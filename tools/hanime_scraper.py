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

# hanime1.me 的搜索页对分类有两种筛选方式:
#   * 官方「類型 genre」: 只有少数几个 (裏番、泡麵番、Motion Anime、3D、同人 等),
#     形如 /search?genre=裏番
#   * 「標籤 tags[]」: 其余绝大多数分类 (3DCG、2.5D、2D動畫、AI生成、MMD 等),
#     形如 /search?tags[]=3DCG
# 若把标签当作 genre 传, 站点会返回空结果 (导致除裏番/泡麵番外全部采集失败),
# 因此下面列出已知的官方 genre; 不在其中的一律优先按 tags[] 采集。
# 为稳健起见, 采集时会在两种参数间自动回退 (见 fetch_search_page)。
KNOWN_GENRES = {
    "裏番",
    "泡麵番",
    "Motion Anime",
    "3D",
    "同人",
    "同人作品",
    "Cosplay",
}

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


# 搜索页中的单个视频卡片。hanime1.me 有两种列表卡片布局:
#   1) 官方 genre(裏番/泡麵番 等)使用「首页行」布局:
#      <a ... href="https://hanime1.me/watch?v=407014" >
#          ... <img ... src="https://.../image/cover/407014.jpg?...">
#          ... <div class="home-rows-videos-title">放入他所不知道的秘密</div>
#      </a>
#   2) 其余分类(3DCG、Motion Anime、AI生成 等)使用「横向卡片」布局:
#      <a ... href="https://hanime1.me/watch?v=407058" class="video-link">
#          ... <img class="main-thumb" src="https://.../image/thumbnail/407058l.jpg?...">
#          ... <div class="title">褐色むちむち...</div>
#      </a>
# 之前只解析布局 1, 导致除裏番/泡麵番外的分类解析出 0 条卡片而"采集失败";
# 下面的正则同时兼容两种布局(封面 image/cover 或缩略图 image/thumbnail,
# 标题 home-rows-videos-title 或 title)。
_CARD_RE = re.compile(
    r'<a[^>]+href="https?://hanime1\.me/watch\?v=(?P<vid>\d+)"[^>]*>'
    r'(?P<body>.*?)</a>',
    re.DOTALL,
)
_CARD_IMG_RE = re.compile(
    r'<img[^>]+src="(?P<img>https?://[^"]*?/image/(?:cover|thumbnail)/[^"]+)"',
    re.DOTALL,
)
# 布局 1: <div class="home-rows-videos-title">; 布局 2: <div class="title">
_CARD_TITLE_RE = re.compile(
    r'<div[^>]*class="(?:[^"]*\s)?(?:home-rows-videos-title|title)(?:\s[^"]*)?"'
    r'[^>]*>(?P<title>.*?)</div>',
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
        # 只有带封面(image/cover 或 image/thumbnail)且带标题的才是真正的视频卡片,
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
# 详情页封面图片: 优先 og:image, 兜底 poster / image/cover 链接
_OG_IMAGE_RE = re.compile(
    r'<meta[^>]+property="og:image"[^>]+content="(?P<img>https?://[^"]+)"',
    re.DOTALL,
)
_POSTER_RE = re.compile(
    r'poster="(?P<img>https?://[^"]+)"', re.DOTALL
)
_COVER_IMG_RE = re.compile(
    r'(?P<img>https?://[^"\']*?/image/cover/[^"\']+?\.(?:jpg|jpeg|png|webp)[^"\']*)',
    re.DOTALL,
)
# 观看次数与上传日期: "观看次数：228万次&nbsp;&nbsp;2026-07-05"
_VIEWS_RE = re.compile(r"观看次数[：:]\s*([0-9.]+\s*[万亿]?)\s*次?")
_DATE_RE = re.compile(r"(\d{4}-\d{1,2}-\d{1,2})")


def _parse_views(text: str) -> int:
    """把 "228万次" / "1.2亿" / "1234" 之类的观看次数转换为整数。"""
    if not text:
        return 0
    text = text.strip().replace("次", "")
    try:
        if text.endswith("万"):
            return int(float(text[:-1]) * 10_000)
        if text.endswith("亿"):
            return int(float(text[:-1]) * 100_000_000)
        return int(float(text))
    except (ValueError, TypeError):
        return 0


def parse_views_and_date(page_html: str) -> Dict[str, Any]:
    """解析详情页的观看次数与上传日期。

    对应页面片段: 观看次数：228万次&nbsp;&nbsp;2026-07-05
    """
    views_text = ""
    play_count = 0
    upload_date = ""

    # 找到包含“观看次数”的那一段文本再解析, 避免匹配到无关数字
    idx = page_html.find("观看次数")
    if idx != -1:
        segment = _clean_text(page_html[idx: idx + 200])
        vm = _VIEWS_RE.search(segment)
        if vm:
            views_text = vm.group(1).strip()
            play_count = _parse_views(views_text)
        dm = _DATE_RE.search(segment)
        if dm:
            upload_date = dm.group(1)

    return {
        "views_text": views_text,
        "play_count": play_count,
        "upload_date": upload_date,
    }


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


def _parse_watch_image(page_html: str) -> str:
    """从详情页解析封面图片地址 (og:image -> poster -> image/cover 兜底)。"""
    for regex in (_OG_IMAGE_RE, _POSTER_RE, _COVER_IMG_RE):
        m = regex.search(page_html)
        if m:
            return html.unescape(m.group("img"))
    return ""


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

    views = parse_views_and_date(page_html)

    return {
        "title": title,
        "video_image": _parse_watch_image(page_html),
        "sources": sorted(sources, key=lambda s: s["quality"], reverse=True),
        "best_quality": best["quality"] if best else None,
        "video_url": best["url"] if best else None,
        "tags": tags,
        "views_text": views["views_text"],
        "play_count": views["play_count"],
        "upload_date": views["upload_date"],
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
        # 记住首个能返回结果的搜索参数名 ("genre" 或 "tags[]"), 供后续分页复用。
        self._search_key: Optional[str] = None

    def _get(self, url: str, params: Optional[Any] = None) -> str:
        resp = self.session.get(url, params=params, timeout=self.timeout)
        resp.raise_for_status()
        resp.encoding = resp.apparent_encoding or "utf-8"
        return resp.text

    def _search_params(self, key: str, page: int):
        """构造搜索请求参数。

        使用 (key, value) 列表以支持 ``tags[]`` 这类数组式参数名。
        """
        return [(key, self.genre), ("page", page)]

    def _candidate_keys(self):
        """按优先级返回待尝试的搜索参数名。

        已知的官方 genre 先试 ``genre``, 其余分类先试 ``tags[]``;
        无论哪种, 都会把另一种作为回退, 以兼容站点分类归属的变化。
        """
        if self.genre in KNOWN_GENRES:
            return ["genre", "tags[]"]
        return ["tags[]", "genre"]

    def fetch_search_page(self, page: int = 1) -> List[Dict[str, Any]]:
        """采集单个搜索列表页。"""
        logger.info("采集搜索页: genre=%s page=%s", self.genre, page)
        # 已确定有效的参数名, 直接复用 (避免每页重复试探)。
        if self._search_key is not None:
            html_text = self._get(
                SEARCH_URL, params=self._search_params(self._search_key, page)
            )
            return parse_search(html_text)
        # 首次采集: 依次尝试 genre / tags[], 记住第一个有结果的参数名。
        for key in self._candidate_keys():
            cards = parse_search(
                self._get(SEARCH_URL, params=self._search_params(key, page))
            )
            if cards:
                self._search_key = key
                if key != "genre":
                    logger.info("genre=%s 按标签(%s)采集", self.genre, key)
                return cards
        return []

    def fetch_watch(self, video_id: int) -> Dict[str, Any]:
        """采集单个视频详情页。"""
        logger.info("采集详情页: v=%s", video_id)
        return parse_watch(self._get(WATCH_URL, params={"v": video_id}))

    def iter_pages(
        self, pages: int = 1, with_details: bool = True
    ):
        """逐页采集列表, 每采完一页就产出 (page, items)。

        与 :meth:`scrape` 不同, 本方法是生成器: 每页采集完成后立即产出该页结果,
        便于调用方"采集完一页就保存一页"、并实时上报进度, 而不必等待所有页面
        全部采集完成。遇到空页(没有更多视频)或搜索页请求异常时自动停止。
        """
        for page in range(1, pages + 1):
            try:
                cards = self.fetch_search_page(page)
            except requests.RequestException as exc:
                logger.error("搜索页采集失败 page=%s: %s", page, exc)
                break

            if not cards:
                logger.info("第 %s 页没有更多视频, 停止。", page)
                break

            page_items: List[Dict[str, Any]] = []
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
                                "views_text": detail["views_text"],
                                "play_count": detail["play_count"],
                                "upload_date": detail["upload_date"],
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
                page_items.append(item)

            yield page, page_items

            if self.delay:
                time.sleep(self.delay)

    def scrape(
        self, pages: int = 1, with_details: bool = True
    ) -> List[Dict[str, Any]]:
        """采集多页列表, 并可进一步采集每个视频的详情。"""
        collected: List[Dict[str, Any]] = []
        for _page, page_items in self.iter_pages(pages, with_details):
            collected.extend(page_items)
        return collected


# ---------------------------------------------------------------------------
# 与数据库集成
# ---------------------------------------------------------------------------
def _to_video_record(item: Dict[str, Any], genre: str) -> Dict[str, Any]:
    """把采集结果转换为 VideoDatabase.insert_video 需要的字段。"""
    tags = item.get("tags") or []
    return {
        "video_id": item["video_id"],
        "video_url": item.get("video_url") or item["watch_url"],
        "video_image": item.get("video_image", ""),
        "video_title": item.get("video_title", ""),
        # 分类存 genre(裏番); 标签单独存 video_tags 列
        "video_category": genre[:100],
        "video_tags": ",".join(tags),
        # 观看次数 -> play_count(整数), 上传日期 -> upload_time
        "play_count": item.get("play_count", 0) or 0,
        "upload_time": item.get("upload_date", "") or "",
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
                "views_text": detail.get("views_text"),
                "play_count": detail.get("play_count"),
                "upload_date": detail.get("upload_date"),
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
