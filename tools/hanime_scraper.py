#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Hanime1 里番/裏番 采集脚本 (Hanime1 Hentai Scraper)
====================================================
从 https://hanime1.me 采集裏番(里番)动漫信息。

采集流程:
1. 进入搜索页 https://hanime1.me/search?genre=裏番 (可分页),
   解析每个视频卡片, 得到 标题、封面图片链接、视频详情页地址。
2. 进入每个视频详情页 https://hanime1.me/watch?v=<id>,
   解析视频播放地址并选取最高画质 (1080p 优先, 没有则 720p, 依次向下),
   以及该视频的标签分类。
3. 结果可输出为 JSON 文件, 也可写入项目的视频数据库 (VideoDatabase)。

依赖: 仅使用 requests + 标准库 (正则解析), 无需额外安装。

使用示例:
    # 采集前 3 页, 打印结果
    python tools/hanime_scraper.py --pages 3

    # 采集并保存为 JSON
    python tools/hanime_scraper.py --pages 3 --output videos.json

    # 采集并写入数据库
    python tools/hanime_scraper.py --pages 3 --save-db

    # 只采集单个视频详情页
    python tools/hanime_scraper.py --watch 407014
"""

import os
import re
import sys
import json
import html
import time
import logging
import argparse
from typing import Dict, List, Any, Optional

import requests

logger = logging.getLogger(__name__)

BASE_URL = "https://hanime1.me"
SEARCH_URL = f"{BASE_URL}/search"
WATCH_URL = f"{BASE_URL}/watch"
DEFAULT_GENRE = "裏番"  # 裏番 / 里番

# 画质从高到低的优先级 (数值越大画质越高)
QUALITY_PRIORITY = [1080, 720, 480, 360, 240]

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    # 站点资源要求 no-referrer, 保持与页面 meta referrer 一致
    "Referer": BASE_URL + "/",
}


# ---------------------------------------------------------------------------
# 解析辅助函数
# ---------------------------------------------------------------------------
def _clean_text(text: str) -> str:
    """去掉 HTML 标签与实体, 归一化空白。"""
    if not text:
        return ""
    text = re.sub(r"<[^>]+>", "", text)
    text = html.unescape(text)
    text = text.replace("\xa0", " ").replace("&nbsp;", " ")
    return text.strip()


# 搜索页中的单个视频卡片:
#   <a ... href="https://hanime1.me/watch?v=407014" >
#       ... <img ... src="https://.../image/cover/407014.jpg?...">
#       ... <div class="home-rows-videos-title">放入他所不知道的秘密</div>
_CARD_RE = re.compile(
    r'<a[^>]+href="https?://hanime1\.me/watch\?v=(?P<vid>\d+)"[^>]*>'
    r'(?P<body>.*?)</a>',
    re.DOTALL,
)
_CARD_IMG_RE = re.compile(
    r'<img[^>]+src="(?P<img>https?://[^"]*?/image/cover/[^"]+)"', re.DOTALL
)
_CARD_TITLE_RE = re.compile(
    r'<div[^>]*class="[^"]*home-rows-videos-title[^"]*"[^>]*>(?P<title>.*?)</div>',
    re.DOTALL,
)


def parse_search(page_html: str) -> List[Dict[str, Any]]:
    """解析搜索列表页, 返回视频卡片列表。

    每个元素包含: video_id, video_title, video_image, watch_url
    """
    results: List[Dict[str, Any]] = []
    seen = set()
    for card in _CARD_RE.finditer(page_html):
        vid = card.group("vid")
        body = card.group("body")

        img_match = _CARD_IMG_RE.search(body)
        title_match = _CARD_TITLE_RE.search(body)
        # 只有带封面(image/cover)且带标题的才是真正的视频卡片,
        # 过滤掉占位/广告卡片。
        if not img_match or not title_match:
            continue

        title = _clean_text(title_match.group("title"))
        if not title:
            continue

        if vid in seen:
            continue
        seen.add(vid)

        results.append(
            {
                "video_id": int(vid),
                "video_title": title,
                "video_image": html.unescape(img_match.group("img")),
                "watch_url": f"{WATCH_URL}?v={vid}",
            }
        )
    return results


# 详情页视频源: <source src="https://.../407014-1080p.mp4?..." type="video/mp4" size="1080">
_SOURCE_RE = re.compile(
    r'<source[^>]+src="(?P<url>https?://[^"]+\.mp4[^"]*)"[^>]*size="(?P<size>\d+)"',
    re.DOTALL,
)
# 兜底: 从 url 文件名中解析画质 (如 407014-1080p.mp4)
_SOURCE_URL_RE = re.compile(r'src="(?P<url>https?://[^"]+\.mp4[^"]*)"')
_QUALITY_FROM_URL_RE = re.compile(r"-(\d+)p\.mp4")

# 标签: <div class="single-video-tag" ...><a ... href="/search?tags%5B%5D=..."> 碧池 &nbsp;<span>(4)</span></a></div>
_TAG_RE = re.compile(
    r'<div[^>]*class="[^"]*single-video-tag[^"]*"[^>]*>\s*'
    r'<a[^>]+href="[^"]*[?&]tags(?:%5B%5D|\[\])=[^"]*"[^>]*>(?P<tag>.*?)</a>',
    re.DOTALL,
)
# 详情页标题
_DETAIL_TITLE_RE = re.compile(
    r'<h3[^>]*id="shareBtn-title"[^>]*>(?P<title>.*?)</h3>', re.DOTALL
)


def _parse_sources(page_html: str) -> List[Dict[str, Any]]:
    """解析详情页所有 mp4 视频源, 返回 [{quality, url}] 列表。"""
    sources: Dict[int, str] = {}

    for m in _SOURCE_RE.finditer(page_html):
        url = html.unescape(m.group("url"))
        quality = int(m.group("size"))
        sources.setdefault(quality, url)

    # 若没有 size 属性, 尝试从文件名推断画质
    if not sources:
        for m in _SOURCE_URL_RE.finditer(page_html):
            url = html.unescape(m.group("url"))
            q = _QUALITY_FROM_URL_RE.search(url)
            if q:
                sources.setdefault(int(q.group(1)), url)

    return [{"quality": q, "url": u} for q, u in sources.items()]


def _pick_best_source(sources: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """按 1080p -> 720p -> 480p ... 的优先级选取最高画质。"""
    if not sources:
        return None
    by_quality = {s["quality"]: s for s in sources}
    for q in QUALITY_PRIORITY:
        if q in by_quality:
            return by_quality[q]
    # 优先级列表之外, 取数值最大的画质
    return max(sources, key=lambda s: s["quality"])


def parse_watch(page_html: str) -> Dict[str, Any]:
    """解析视频详情页, 返回最高画质播放地址与标签等信息。"""
    sources = _parse_sources(page_html)
    best = _pick_best_source(sources)

    tags: List[str] = []
    for m in _TAG_RE.finditer(page_html):
        tag = _clean_text(m.group("tag"))
        # 去掉标签后面的计数, 例如 "碧池 (4)" -> "碧池"
        tag = re.sub(r"\s*\(\d+\)\s*$", "", tag).strip()
        if tag and tag not in tags:
            tags.append(tag)

    title_match = _DETAIL_TITLE_RE.search(page_html)
    title = _clean_text(title_match.group("title")) if title_match else ""

    return {
        "title": title,
        "sources": sorted(sources, key=lambda s: s["quality"], reverse=True),
        "best_quality": best["quality"] if best else None,
        "video_url": best["url"] if best else None,
        "tags": tags,
    }


# ---------------------------------------------------------------------------
# 采集器
# ---------------------------------------------------------------------------
class HanimeScraper:
    def __init__(
        self,
        genre: str = DEFAULT_GENRE,
        delay: float = 1.0,
        timeout: int = 20,
        session: Optional[requests.Session] = None,
    ):
        self.genre = genre
        self.delay = delay
        self.timeout = timeout
        self.session = session or requests.Session()
        self.session.headers.update(DEFAULT_HEADERS)

    def _get(self, url: str, params: Optional[Dict[str, Any]] = None) -> str:
        resp = self.session.get(url, params=params, timeout=self.timeout)
        resp.raise_for_status()
        resp.encoding = resp.apparent_encoding or "utf-8"
        return resp.text

    def fetch_search_page(self, page: int = 1) -> List[Dict[str, Any]]:
        """采集单个搜索列表页。"""
        params = {"genre": self.genre, "page": page}
        logger.info("采集搜索页: genre=%s page=%s", self.genre, page)
        return parse_search(self._get(SEARCH_URL, params=params))

    def fetch_watch(self, video_id: int) -> Dict[str, Any]:
        """采集单个视频详情页。"""
        logger.info("采集详情页: v=%s", video_id)
        return parse_watch(self._get(WATCH_URL, params={"v": video_id}))

    def scrape(
        self, pages: int = 1, with_details: bool = True
    ) -> List[Dict[str, Any]]:
        """采集多页列表, 并可进一步采集每个视频的详情。"""
        collected: List[Dict[str, Any]] = []
        for page in range(1, pages + 1):
            try:
                cards = self.fetch_search_page(page)
            except requests.RequestException as exc:
                logger.error("搜索页采集失败 page=%s: %s", page, exc)
                break

            if not cards:
                logger.info("第 %s 页没有更多视频, 停止。", page)
                break

            for card in cards:
                item = dict(card)
                if with_details:
                    try:
                        detail = self.fetch_watch(card["video_id"])
                        item.update(
                            {
                                "video_url": detail["video_url"],
                                "best_quality": detail["best_quality"],
                                "sources": detail["sources"],
                                "tags": detail["tags"],
                            }
                        )
                        # 详情页标题更完整时优先使用
                        if detail.get("title"):
                            item["detail_title"] = detail["title"]
                    except requests.RequestException as exc:
                        logger.error(
                            "详情页采集失败 v=%s: %s", card["video_id"], exc
                        )
                    if self.delay:
                        time.sleep(self.delay)
                collected.append(item)

            if self.delay:
                time.sleep(self.delay)
        return collected


# ---------------------------------------------------------------------------
# 与数据库集成
# ---------------------------------------------------------------------------
def _to_video_record(item: Dict[str, Any], genre: str) -> Dict[str, Any]:
    """把采集结果转换为 VideoDatabase.insert_video 需要的字段。"""
    tags = item.get("tags") or []
    # video_category 存分类(genre); 标签用逗号拼接一并存入分类字段末尾便于检索。
    category = genre
    if tags:
        category = f"{genre},{','.join(tags)}"
    return {
        "video_id": item["video_id"],
        "video_url": item.get("video_url") or item["watch_url"],
        "video_image": item.get("video_image", ""),
        "video_title": item.get("video_title", ""),
        "video_category": category[:100],
    }


def save_to_database(items: List[Dict[str, Any]], genre: str) -> int:
    """把采集结果写入视频数据库, 返回成功写入的数量。"""
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from video_database import VideoDatabase  # noqa: E402

    records = [
        _to_video_record(it, genre)
        for it in items
        if it.get("video_url")  # 至少要有可播放地址
    ]
    db = VideoDatabase()
    try:
        count = db.insert_videos(records)
    finally:
        db.close()
    logger.info("已写入数据库 %s 条", count)
    return count


# ---------------------------------------------------------------------------
# 命令行入口
# ---------------------------------------------------------------------------
def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Hanime1 裏番/里番 视频采集脚本"
    )
    parser.add_argument(
        "--genre", default=DEFAULT_GENRE, help="搜索分类 (默认: 裏番)"
    )
    parser.add_argument(
        "--pages", type=int, default=1, help="采集的列表页数 (默认: 1)"
    )
    parser.add_argument(
        "--watch",
        type=int,
        default=None,
        help="只采集指定视频 ID 的详情页 (跳过列表采集)",
    )
    parser.add_argument(
        "--no-details",
        action="store_true",
        help="只采集列表(标题/封面), 不进入详情页",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=1.0,
        help="每次请求间隔秒数, 避免请求过快 (默认: 1.0)",
    )
    parser.add_argument("--output", default=None, help="结果保存为 JSON 文件路径")
    parser.add_argument(
        "--save-db", action="store_true", help="把结果写入视频数据库"
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="输出调试日志"
    )
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    args = build_arg_parser().parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )

    scraper = HanimeScraper(genre=args.genre, delay=args.delay)

    if args.watch is not None:
        detail = scraper.fetch_watch(args.watch)
        items = [
            {
                "video_id": args.watch,
                "watch_url": f"{WATCH_URL}?v={args.watch}",
                "video_title": detail.get("title", ""),
                "video_url": detail.get("video_url"),
                "best_quality": detail.get("best_quality"),
                "sources": detail.get("sources"),
                "tags": detail.get("tags"),
            }
        ]
    else:
        items = scraper.scrape(
            pages=args.pages, with_details=not args.no_details
        )

    logger.info("共采集 %s 条", len(items))

    if args.output:
        with open(args.output, "w", encoding="utf-8") as fh:
            json.dump(items, fh, ensure_ascii=False, indent=2)
        logger.info("结果已保存到 %s", args.output)

    if args.save_db:
        save_to_database(items, args.genre)

    if not args.output and not args.save_db:
        print(json.dumps(items, ensure_ascii=False, indent=2))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
