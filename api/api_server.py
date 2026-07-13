#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
视频API服务器 (Video API Server)
================================
基于Flask的REST API服务器，连接视频数据库

启动方式:
    python api_server.py                    # 开发模式
    python api_server.py --production       # 生产模式

API端点:
    GET  /api/videos                - 获取视频列表 (支持分页)
    GET  /api/videos/<id>           - 获取单个视频
    GET  /api/videos/search         - 搜索视频
    GET  /api/videos/category       - 按分类获取视频
    GET  /api/videos/category/tags  - 获取分类下的视频标签
    GET  /api/videos/top            - 获取热门视频
    POST /api/videos/<id>/play      - 增加播放次数
    GET  /api/categories            - 获取所有分类
    GET  /api/statistics            - 获取统计信息

作者: Auto-generated
日期: 2026-01-30
"""
from __future__ import annotations

import os
import sys
import uuid
import json
import logging
import time
from datetime import datetime
from functools import wraps
from contextlib import contextmanager
from typing import Any, Callable, cast, Dict, Generator, List, Optional, Tuple, TypeVar

import requests as http_requests
from flask import (
    Flask, jsonify, request, Response, g, send_from_directory, stream_with_context
)
from werkzeug.utils import secure_filename
from flask_cors import CORS

# 导入视频数据库模块 (在同一目录或父目录中)
try:
    from video_database import VideoDatabase
except ImportError:
    # 如果同目录找不到,尝试父目录 (本地开发环境)
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, repo_root)
    tools_path = os.path.join(repo_root, "tools")
    if tools_path not in sys.path:
        sys.path.insert(0, tools_path)
    try:
        from video_database import VideoDatabase
    except ImportError:
        print("错误: 无法导入 video_database 模块")
        print("请确保 video_database.py 在正确的位置")
        sys.exit(1)

# 导入 Hanime1 采集器 (可选, 缺失时相关接口会返回明确错误)
try:
    import hanime_scraper  # type: ignore
except ImportError:
    hanime_scraper = None  # type: ignore

# Type variable for decorated functions
F = TypeVar('F', bound=Callable[..., Any])

# 配置日志 (Configure logging)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger: logging.Logger = logging.getLogger(__name__)

# 创建Flask应用 (Create Flask app)
app: Flask = Flask(__name__)

# 配置CORS - 允许跨域请求
# 在部署的app或H5中，origin可能来自多种来源（Capacitor、WebView、不同域名等）
# 因此需要允许所有来源以确保图片和API请求能正常加载
CORS(app, resources={
    r"/api/*": {
        "origins": "*",
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})

# ==================== 图片上传配置 (Image Upload Config) ====================
# 允许上传的图片扩展名 (Allowed image file extensions)
ALLOWED_IMAGE_EXTENSIONS: set = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'bmp'}
# 单个上传文件的最大大小 (Maximum upload size per request: 10MB)
MAX_UPLOAD_BYTES: int = 10 * 1024 * 1024
# 限制请求体大小，防止过大的上传 (Limit request body size to guard uploads)
app.config['MAX_CONTENT_LENGTH'] = MAX_UPLOAD_BYTES


def get_upload_dir() -> str:
    """
    获取图片上传目录 (Get the image upload directory)

    优先级 (Priority):
        1. UPLOAD_DIR 环境变量 (if set and non-empty)
        2. /app/data/uploads (Docker环境，持久化卷)
        3. <api目录>/data/uploads (本地开发)
    目录不存在时会自动创建 (Created automatically if missing).
    """
    upload_dir = os.environ.get('UPLOAD_DIR', '').strip()
    if not upload_dir:
        if os.path.isdir('/app/data'):
            upload_dir = '/app/data/uploads'
        else:
            upload_dir = os.path.join(
                os.path.dirname(os.path.abspath(__file__)), 'data', 'uploads'
            )
    os.makedirs(upload_dir, exist_ok=True)
    return upload_dir


# 请求计时中间件 (Request timing middleware)
@app.before_request
def before_request() -> None:
    """记录请求开始时间 (Record request start time)"""
    g.start_time = time.time()


@app.after_request
def after_request(response: Response) -> Response:
    """记录请求处理时间 (Log request processing time)"""
    if hasattr(g, 'start_time'):
        elapsed = time.time() - g.start_time
        # 记录慢请求 (超过1秒) (Log slow requests over 1 second)
        if elapsed > 1.0:
            logger.warning(
                f"Slow request: {request.method} {request.path} "
                f"took {elapsed:.3f}s"
            )
    return response


@contextmanager
def get_db() -> Generator[VideoDatabase, None, None]:
    """
    获取数据库连接 (Get database connection)
    每个请求创建新连接，解决SQLite线程问题
    Creates a new connection per request to solve SQLite threading issues
    """
    use_mysql: bool = os.environ.get('USE_MYSQL', 'true').lower() == 'true'
    db: VideoDatabase = VideoDatabase(use_mysql=use_mysql, verbose=False)
    try:
        yield db
    finally:
        db.close()


def api_response(
    data: Optional[Any] = None,
    message: str = "success",
    code: int = 200,
    total: Optional[int] = None
) -> Tuple[Response, int]:
    """
    统一API响应格式 (Unified API response format)

    Args:
        data: Response data
        message: Response message
        code: HTTP status code
        total: 数据总量, 用于分页 (Total count for pagination, optional)

    Returns:
        Tuple of (JSON response, status code)
    """
    response: Dict[str, Any] = {
        "code": code,
        "message": message,
        "data": data
    }
    if total is not None:
        response["total"] = total
    return jsonify(response), code


def handle_errors(f: F) -> F:
    """
    错误处理装饰器 (Error handling decorator)
    Wraps route handlers to provide consistent error handling
    """
    @wraps(f)
    def decorated_function(*args: Any, **kwargs: Any) -> Tuple[Response, int]:
        try:
            return f(*args, **kwargs)
        except ValueError as e:
            logger.warning(f"参数错误 (Parameter error): {e}")
            return api_response(message=str(e), code=400)
        except Exception as e:
            logger.error(f"服务器错误 (Server error): {e}", exc_info=True)
            return api_response(message="服务器内部错误", code=500)
    return cast(F, decorated_function)


# ==================== API路由 (API Routes) ====================

@app.route('/api/health', methods=['GET'])
def health_check() -> Tuple[Response, int]:
    """健康检查端点 (Health check endpoint)"""
    return api_response(data={"status": "healthy"})


@app.route('/api/videos', methods=['GET'])
@handle_errors
def get_videos() -> Tuple[Response, int]:
    """
    获取视频列表 (Get video list)

    Query参数 (Query parameters):
        limit: 返回数量 (默认20, 最大100) / Return count (default 20, max 100)
        offset: 偏移量 (默认0) / Offset (default 0)
    """
    limit: int = max(1, min(int(request.args.get('limit', 20)), 100))
    offset: int = max(0, int(request.args.get('offset', 0)))

    with get_db() as db:
        videos: List[Dict[str, Any]] = db.get_all_videos(limit=limit, offset=offset)
        total: int = db.count_all_videos()

    return api_response(data=videos, total=total)


@app.route('/api/videos/search', methods=['GET'])
@handle_errors
def search_videos() -> Tuple[Response, int]:
    """
    搜索视频 (Search videos)

    Query参数 (Query parameters):
        keyword: 搜索关键词 (必需) / Search keyword (required)
        limit: 返回数量 (默认20, 最大100) / Return count (default 20, max 100)
        offset: 偏移量 (默认0) / Offset (default 0)
    """
    keyword: str = request.args.get('keyword', '').strip()
    if not keyword:
        return api_response(message="请提供搜索关键词", code=400)

    limit: int = max(1, min(int(request.args.get('limit', 20)), 100))
    offset: int = max(0, int(request.args.get('offset', 0)))

    with get_db() as db:
        videos: List[Dict[str, Any]] = db.search_videos(keyword, limit=limit, offset=offset)
        total: int = db.count_search_videos(keyword)

    return api_response(data=videos, total=total)


@app.route('/api/videos/<int:video_id>', methods=['GET'])
@handle_errors
def get_video(video_id: int) -> Tuple[Response, int]:
    """获取单个视频详情 (Get single video details)"""
    with get_db() as db:
        video: Optional[Dict[str, Any]] = db.get_video(video_id)

    if video:
        return api_response(data=video)
    else:
        return api_response(message="视频不存在", code=404)


@app.route('/api/videos/category', methods=['GET'])
@handle_errors
def get_videos_by_category() -> Tuple[Response, int]:
    """
    按分类获取视频 (Get videos by category)

    Query参数 (Query parameters):
        category: 分类名称 (必需) / Category name (required)
        limit: 返回数量 (默认20, 最大100) / Return count (default 20, max 100)
        offset: 偏移量 (默认0) / Offset (default 0)
        tag: 单个标签过滤 (可选, 向后兼容) / Single tag filter (optional)
        tags: 多个标签, 逗号分隔 (可选) / Multiple tags, comma-separated (optional)
        broad: 广泛配对开关, 1/true 时任意匹配, 否则全部匹配 / Broad match toggle
    """
    category: str = request.args.get('category', '').strip()
    if not category:
        return api_response(message="请提供分类名称", code=400)

    limit: int = max(1, min(int(request.args.get('limit', 20)), 100))
    offset: int = max(0, int(request.args.get('offset', 0)))
    tag: str = request.args.get('tag', '').strip()
    # 多标签筛选 (参考 dyb 的标签筛选): tags 以逗号分隔, broad 为广泛配对(任意匹配)
    raw_tags: str = request.args.get('tags', '')
    tags: List[str] = [t.strip() for t in raw_tags.split(',') if t.strip()]
    match_any: bool = str(request.args.get('broad', '')).strip().lower() in (
        '1', 'true', 'yes', 'on')

    with get_db() as db:
        videos: List[Dict[str, Any]] = db.get_videos_by_category(
            category, limit=limit, offset=offset, tag=tag or None,
            tags=tags or None, match_any=match_any)
        total: int = db.count_videos_by_category(
            category, tag=tag or None, tags=tags or None, match_any=match_any)

    return api_response(data=videos, total=total)


@app.route('/api/videos/category/tags', methods=['GET'])
@handle_errors
def get_category_tags() -> Tuple[Response, int]:
    """
    获取指定分类下的视频标签 (Get video tags available within a category)

    Query参数 (Query parameters):
        category: 分类名称 (必需) / Category name (required)
        limit: 返回标签数量 (默认60, 最大200) / Tag count (default 60, max 200)
    """
    category: str = request.args.get('category', '').strip()
    if not category:
        return api_response(message="请提供分类名称", code=400)

    limit: int = max(1, min(int(request.args.get('limit', 60)), 200))

    with get_db() as db:
        tags: List[Dict[str, Any]] = db.get_category_tags(category, limit=limit)

    return api_response(data=tags)


@app.route('/api/videos/top', methods=['GET'])
@handle_errors
def get_top_videos() -> Tuple[Response, int]:
    """
    获取热门视频 (Get top videos by play count)

    Query参数 (Query parameters):
        limit: 返回数量 (默认10) / Return count (default 10)
    """
    limit: int = max(1, min(int(request.args.get('limit', 10)), 50))

    with get_db() as db:
        videos: List[Dict[str, Any]] = db.get_top_videos(limit=limit)

    return api_response(data=videos)


@app.route('/api/videos/<int:video_id>/play', methods=['POST'])
@handle_errors
def update_play_count(video_id: int) -> Tuple[Response, int]:
    """增加视频播放次数 (Increment video play count)"""
    with get_db() as db:
        success: bool = db.update_play_count(video_id)

    if success:
        return api_response(message="播放次数已更新")
    else:
        return api_response(message="视频不存在", code=404)


@app.route('/api/videos/random', methods=['GET'])
@handle_errors
def get_random_videos() -> Tuple[Response, int]:
    """
    获取随机视频推荐 (Get random video recommendations)

    Query参数 (Query parameters):
        limit: 返回数量 (默认10, 最大50) / Return count (default 10, max 50)
        category: 可选分类过滤 / Optional category filter
    """
    limit: int = max(1, min(int(request.args.get('limit', 10)), 50))
    category: str = request.args.get('category', '').strip()

    with get_db() as db:
        if category:
            videos: List[Dict[str, Any]] = db.get_videos_by_category(
                category, limit=limit * 2, offset=0
            )
        else:
            videos = db.get_all_videos(limit=limit * 2, offset=0)

    # Shuffle and return random subset
    import random
    random.shuffle(videos)
    return api_response(data=videos[:limit])


@app.route('/api/videos/related/<int:video_id>', methods=['GET'])
@handle_errors
def get_related_videos(video_id: int) -> Tuple[Response, int]:
    """
    获取相关视频 (Get related videos based on category)

    Query参数 (Query parameters):
        limit: 返回数量 (默认6, 最大20) / Return count (default 6, max 20)
    """
    limit: int = max(1, min(int(request.args.get('limit', 6)), 20))

    with get_db() as db:
        # Get the current video to find its category
        video: Optional[Dict[str, Any]] = db.get_video(video_id)
        if not video:
            return api_response(message="视频不存在", code=404)

        # Get videos from the same category
        category = video.get('video_category', '')
        if category:
            related: List[Dict[str, Any]] = db.get_videos_by_category(
                category, limit=limit + 1, offset=0
            )
            # Filter out the current video
            related = [v for v in related if v.get('video_id') != video_id][:limit]
        else:
            related = []

    return api_response(data=related)


@app.route('/api/categories', methods=['GET'])
@handle_errors
def get_categories() -> Tuple[Response, int]:
    """获取所有视频分类 (Get all video categories)"""
    with get_db() as db:
        categories: List[Dict[str, Any]] = db.get_categories()

    return api_response(data=categories)


@app.route('/api/statistics', methods=['GET'])
@handle_errors
def get_statistics() -> Tuple[Response, int]:
    """获取数据库统计信息 (Get database statistics)"""
    with get_db() as db:
        stats: Dict[str, Any] = db.get_statistics()

    return api_response(data=stats)


# ==================== 导航分类管理API (Navigation Categories API) ====================

# 默认导航分类配置 (Default navigation categories)
DEFAULT_NAV_CATEGORIES: List[Dict[str, Any]] = [
    {
        'key': 'recommend',
        'label': '推荐',
        'subcategories': ['热门推荐', '动作电影', '喜剧片', '科幻大片', '爱情电影', '恐怖惊悚', '纪录片', '动漫']
    },
    {
        'key': 'japan',
        'label': '日本',
        'subcategories': ['日本AV', '无码高清', '制服诱惑', '人妻系列', '女优精选', '素人企划', '动漫资源', '经典作品']
    },
    {
        'key': 'domestic',
        'label': '国产',
        'subcategories': ['国产自拍', '网红主播', '偷拍私拍', '情侣实录', '素人投稿', '制服诱惑', '熟女人妻', '精品短视频']
    },
    {
        'key': 'anime',
        'label': '动漫',
        'subcategories': ['里番动漫', '3D动画', '同人作品', '触手系列', 'NTR剧情', '巨乳萝莉', '校园爱情', '经典番剧']
    },
    {
        'key': 'welfare',
        'label': '福利',
        'subcategories': ['写真福利', '丝袜美腿', '性感模特', '大尺度写真', '韩国女团', '日本偶像', '网红热舞', 'ASMR']
    }
]


@app.route('/api/nav-categories', methods=['GET'])
@handle_errors
def get_nav_categories() -> Tuple[Response, int]:
    """
    获取导航分类配置 (Get navigation categories)
    如果数据库中没有配置，返回默认配置
    """
    with get_db() as db:
        categories: List[Dict[str, Any]] = db.get_nav_categories()

    # 如果没有配置，返回默认配置
    if not categories:
        categories = DEFAULT_NAV_CATEGORIES

    return api_response(data=categories)


@app.route('/api/nav-categories', methods=['POST'])
@handle_errors
def save_nav_categories() -> Tuple[Response, int]:
    """
    保存导航分类配置 (Save navigation categories)
    所有用户共享此配置
    """
    data = request.get_json()
    if not data or not isinstance(data, list):
        return api_response(message="请提供有效的分类配置列表", code=400)

    # 验证数据格式
    for cat in data:
        if not isinstance(cat, dict):
            return api_response(message="分类格式无效", code=400)
        if not cat.get('key') or not cat.get('label'):
            return api_response(message="每个分类必须包含 key 和 label", code=400)

    with get_db() as db:
        success: bool = db.save_nav_categories(data)

    if success:
        return api_response(message="导航分类配置已保存")
    else:
        return api_response(message="保存失败", code=500)


@app.route('/api/nav-categories/reset', methods=['POST'])
@handle_errors
def reset_nav_categories() -> Tuple[Response, int]:
    """
    重置导航分类为默认配置 (Reset navigation categories to default)
    """
    with get_db() as db:
        success: bool = db.save_nav_categories(DEFAULT_NAV_CATEGORIES)

    if success:
        return api_response(data=DEFAULT_NAV_CATEGORIES, message="已恢复默认配置")
    else:
        return api_response(message="重置失败", code=500)


@app.route('/api/carousel', methods=['GET'])
@handle_errors
def get_carousel() -> Tuple[Response, int]:
    """
    获取首页轮播图视频 (Get home carousel videos)

    仅返回管理员在后台手动选择的视频。
    如果未配置，返回空列表，前端将隐藏轮播图，
    这样新增视频只会显示在其所属分类，而不会自动出现在轮播图。
    """
    with get_db() as db:
        videos: List[Dict[str, Any]] = db.get_carousel_videos()

    return api_response(data=videos)


@app.route('/api/admin/carousel', methods=['POST'])
@handle_errors
def save_carousel() -> Tuple[Response, int]:
    """
    保存首页轮播图配置 (Save home carousel items)

    支持三种请求体格式 (Request body):
        1. 新版混合条目: { "items": [
               { "item_type": "video", "video_id": 1 },
               { "item_type": "image", "image_url": "https://...",
                 "title": "标题", "link_url": "https://..." }
           ] }
        2. 旧版仅视频: { "video_ids": [1, 2, 3] }
        3. 直接传视频ID数组: [1, 2, 3]
    """
    data = request.get_json()

    items = None
    video_ids = None

    if isinstance(data, dict):
        items = data.get('items')
        video_ids = data.get('video_ids')
    elif isinstance(data, list):
        video_ids = data

    # 新版混合条目格式 (New mixed items format)
    if isinstance(items, list):
        normalized_items: List[Dict[str, Any]] = []
        for item in items:
            if not isinstance(item, dict):
                return api_response(message="轮播图条目格式无效", code=400)
            item_type = (item.get('item_type') or 'video')
            if item_type == 'image':
                image_url = (item.get('image_url') or '').strip()
                if not image_url:
                    return api_response(message="图片轮播图条目缺少图片地址", code=400)
                normalized_items.append({
                    'item_type': 'image',
                    'image_url': image_url,
                    'title': item.get('title') or '',
                    'link_url': item.get('link_url') or ''
                })
            else:
                try:
                    normalized_items.append({
                        'item_type': 'video',
                        'video_id': int(item.get('video_id'))
                    })
                except (TypeError, ValueError):
                    return api_response(message="视频ID必须为整数", code=400)

        with get_db() as db:
            success = db.save_carousel_items(normalized_items)

        if success:
            return api_response(message="轮播图配置已保存")
        return api_response(message="保存失败", code=500)

    # 旧版仅视频格式 (Legacy video-only format)
    if not isinstance(video_ids, list):
        return api_response(message="请提供有效的轮播图条目列表", code=400)

    # 验证每个ID都是整数 (Validate every id is an integer)
    try:
        normalized_ids: List[int] = [int(vid) for vid in video_ids]
    except (TypeError, ValueError):
        return api_response(message="视频ID必须为整数", code=400)

    with get_db() as db:
        success = db.save_carousel_videos(normalized_ids)

    if success:
        return api_response(message="轮播图配置已保存")
    else:
        return api_response(message="保存失败", code=500)


# ==================== 图片上传API (Image Upload API) ====================

@app.route('/api/admin/upload-image', methods=['POST'])
@handle_errors
def upload_image() -> Tuple[Response, int]:
    """
    上传图片 (Upload an image file)

    接收 multipart/form-data，字段名为 ``file``。
    保存到上传目录并返回可访问的绝对URL，供轮播图等使用。

    Returns:
        { "url": "http://host/api/uploads/<name>", "filename": "<name>" }
    """
    if 'file' not in request.files:
        return api_response(message="未找到上传文件", code=400)

    file = request.files['file']
    if not file or not file.filename:
        return api_response(message="未选择文件", code=400)

    # 校验扩展名 (Validate the file extension)
    ext = ''
    if '.' in file.filename:
        ext = file.filename.rsplit('.', 1)[1].lower()
    if ext not in ALLOWED_IMAGE_EXTENSIONS:
        return api_response(
            message="仅支持 png/jpg/jpeg/gif/webp/bmp 图片", code=400
        )

    # 校验MIME类型 (Validate the reported MIME type)
    if file.mimetype and not file.mimetype.startswith('image/'):
        return api_response(message="文件类型必须为图片", code=400)

    # 使用随机文件名，避免路径穿越与覆盖 (Random name avoids traversal/overwrite)
    filename = f"{uuid.uuid4().hex}.{ext}"
    # secure_filename 作为额外防护 (secure_filename as an extra safeguard)
    filename = secure_filename(filename)

    upload_dir = get_upload_dir()
    filepath = os.path.join(upload_dir, filename)
    file.save(filepath)

    url = request.host_url.rstrip('/') + '/api/uploads/' + filename
    return api_response(
        data={'url': url, 'filename': filename}, message="上传成功"
    )


@app.route('/api/uploads/<path:filename>', methods=['GET'])
def serve_upload(filename: str) -> Response:
    """
    提供已上传的图片 (Serve an uploaded image)

    使用 send_from_directory 防止路径穿越 (Prevents path traversal).
    """
    upload_dir = get_upload_dir()
    return send_from_directory(upload_dir, filename)


# ==================== 视频管理API (Video Management API) ====================

@app.route('/api/admin/category-stats', methods=['GET'])
@handle_errors
def get_category_stats() -> Tuple[Response, int]:
    """
    获取各分类视频统计 (Get video count statistics by category)
    返回每个分类的视频数量
    """
    with get_db() as db:
        stats: List[Dict[str, Any]] = db.get_category_stats()

    return api_response(data=stats)


@app.route('/api/admin/category-videos', methods=['GET'])
@handle_errors
def get_category_videos_admin() -> Tuple[Response, int]:
    """
    获取指定分类的视频列表 (Get videos in a specific category for admin)
    用于后台查看分类内的视频

    Query参数:
        category: 分类名称 (必需)
        limit: 返回数量 (默认50, 最大200)
        offset: 偏移量 (默认0)
    """
    category: str = request.args.get('category', '').strip()
    if not category:
        return api_response(message="请提供分类名称", code=400)

    limit: int = max(1, min(int(request.args.get('limit', 50)), 200))
    offset: int = max(0, int(request.args.get('offset', 0)))

    with get_db() as db:
        videos: List[Dict[str, Any]] = db.get_videos_by_category(category, limit=limit, offset=offset)
        total: int = db.count_videos_by_category(category)

    return api_response(data=videos, total=total)


@app.route('/api/admin/duplicates', methods=['GET'])
@handle_errors
def get_duplicate_videos() -> Tuple[Response, int]:
    """
    检测重复视频 (Detect duplicate videos)
    根据标题或图片URL查找重复的视频

    Query参数:
        type: 检测类型 ('title' 或 'image', 默认 'title')
    """
    check_type: str = request.args.get('type', 'title').strip().lower()
    if check_type not in ['title', 'image']:
        check_type = 'title'

    with get_db() as db:
        duplicates: List[Dict[str, Any]] = db.find_duplicates(check_type)

    return api_response(data=duplicates)


@app.route('/api/admin/videos', methods=['POST'])
@handle_errors
def add_video() -> Tuple[Response, int]:
    """
    添加新视频 (Add a new video)
    """
    data = request.get_json()
    if not data:
        return api_response(message="请提供视频数据", code=400)

    required_fields = ['video_url', 'video_title']
    for field in required_fields:
        if not data.get(field):
            return api_response(message=f"缺少必需字段: {field}", code=400)

    with get_db() as db:
        # Generate a new video_id if not provided
        if not data.get('video_id'):
            data['video_id'] = db.get_next_video_id()

        success: bool = db.insert_video(data)

    if success:
        return api_response(message="视频添加成功", data={'video_id': data['video_id']})
    else:
        return api_response(message="添加失败", code=500)


@app.route('/api/admin/videos/<int:video_id>', methods=['DELETE'])
@handle_errors
def delete_video(video_id: int) -> Tuple[Response, int]:
    """
    删除视频 (Delete a video)
    """
    with get_db() as db:
        success: bool = db.delete_video(video_id)

    if success:
        return api_response(message="视频删除成功")
    else:
        return api_response(message="视频不存在或删除失败", code=404)


@app.route('/api/admin/videos/<int:video_id>', methods=['PUT'])
@handle_errors
def update_video(video_id: int) -> Tuple[Response, int]:
    """
    更新视频 (Update a video)
    """
    data = request.get_json()
    if not data:
        return api_response(message="请提供视频数据", code=400)

    with get_db() as db:
        # Check if video exists
        existing_video: Optional[Dict[str, Any]] = db.get_video(video_id)
        if not existing_video:
            return api_response(message="视频不存在", code=404)

        success: bool = db.update_video(video_id, data)

    if success:
        return api_response(message="视频更新成功")
    else:
        return api_response(message="更新失败", code=500)


@app.route('/api/admin/videos/batch-delete', methods=['POST'])
@handle_errors
def batch_delete_videos() -> Tuple[Response, int]:
    """
    批量删除视频 (Batch delete videos)

    Request Body:
        video_ids: 要删除的视频ID列表 (必需)
    """
    data = request.get_json() or {}
    video_ids = data.get('video_ids')
    if not isinstance(video_ids, list) or not video_ids:
        return api_response(message="请提供要删除的视频ID列表", code=400)

    # 限制单次批量删除数量, 避免超大请求
    if len(video_ids) > 1000:
        return api_response(message="单次最多删除1000个视频", code=400)

    with get_db() as db:
        deleted_count: int = db.delete_videos(video_ids)

    return api_response(
        data={'deleted_count': deleted_count, 'requested_count': len(video_ids)},
        message=f"成功删除 {deleted_count} 个视频"
    )


@app.route('/api/admin/collection-status', methods=['GET'])
@handle_errors
def get_collection_status() -> Tuple[Response, int]:
    """
    获取采集状态 (Get collection status)
    检查是否有新视频可以采集，以及已采集的视频统计

    Query参数:
        hours: 检查多少小时内的更新 (默认24)
    """
    hours: int = max(1, min(int(request.args.get('hours', 24)), 168))  # Max 7 days

    with get_db() as db:
        status: Dict[str, Any] = db.get_collection_status(hours)

    return api_response(data=status)


@app.route('/api/admin/check-new-videos', methods=['POST'])
@handle_errors
def check_new_videos() -> Tuple[Response, int]:
    """
    检查新视频 (Check for new videos from source)
    从采集源检查是否有新的视频可以采集
    """
    # 采集API配置 - 使用环境变量或默认值
    api_url = os.environ.get('COLLECTOR_API_URL', 'https://api.sq03.shop/api.php/provide/vod/')
    hours: int = max(1, min(int(request.args.get('hours', 24)), 168))

    try:
        # 请求最近更新的视频 (使用较短超时避免阻塞)
        params = {'ac': 'detail', 'h': hours, 'pg': 1}
        response = http_requests.get(api_url, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()

        total_available = data.get('total', 0)
        source_videos = data.get('list', [])

        # 检查哪些视频已经在数据库中
        with get_db() as db:
            existing_ids = set()
            for video in source_videos:
                vod_id = video.get('vod_id')
                if vod_id and db.get_video(vod_id):
                    existing_ids.add(vod_id)

            new_videos = [v for v in source_videos if v.get('vod_id') not in existing_ids]
            already_collected = [v for v in source_videos if v.get('vod_id') in existing_ids]

        result = {
            'total_available': total_available,
            'checked_count': len(source_videos),
            'new_count': len(new_videos),
            'already_collected_count': len(already_collected),
            'new_videos': [{
                'vod_id': v.get('vod_id'),
                'vod_name': v.get('vod_name'),
                'vod_pic': v.get('vod_pic'),
                'type_name': v.get('type_name'),
                'vod_time': v.get('vod_time')
            } for v in new_videos[:20]],  # Only return first 20
            'checked_at': datetime.now().isoformat()
        }

        return api_response(data=result)

    except http_requests.RequestException as e:
        logger.error(f"检查新视频失败: {e}")
        return api_response(message="检查失败: 采集源请求异常", code=500)
    except Exception as e:
        logger.error(f"检查新视频失败: {e}")
        return api_response(message="检查失败", code=500)


@app.route('/api/admin/collect-videos', methods=['POST'])
@handle_errors
def collect_videos() -> Tuple[Response, int]:
    """
    后台采集视频 (Background video collection)
    从采集源采集视频并保存到数据库

    Request Body:
        type_id: 分类ID筛选 (可选)
        hours: 获取多少小时内更新的视频 (可选, 默认24)
        max_pages: 最大采集页数 (可选, 默认1)
        skip_duplicates: 是否跳过已存在的视频 (可选, 默认true)
    """
    # 获取请求参数
    data = request.get_json() or {}
    type_id = data.get('type_id')
    hours: int = max(1, min(int(data.get('hours', 24)), 168))
    max_pages: int = max(1, min(int(data.get('max_pages', 1)), 50))
    skip_duplicates: bool = data.get('skip_duplicates', True)

    # 采集API配置
    api_url = os.environ.get('COLLECTOR_API_URL', 'https://api.sq03.shop/api.php/provide/vod/')

    # 域名替换配置 (Domain replacement configuration)
    domain_replacements = {
        'vip.sq03.shop': 'd34zpx35a2d8cd.cloudfront.net'
    }

    def process_play_url(play_url: str) -> str:
        """处理播放URL，替换指定域名"""
        if not play_url:
            return play_url
        for old_domain, new_domain in domain_replacements.items():
            play_url = play_url.replace(old_domain, new_domain)
        return play_url

    def is_valid_video(video: dict) -> bool:
        """检查视频是否有效（图片URL不能以.txt结尾）"""
        vod_pic = video.get('vod_pic', '')
        if vod_pic and vod_pic.lower().endswith('.txt'):
            return False
        return True

    collected_videos = []
    skipped_count = 0
    duplicate_count = 0
    pages_processed = 0

    try:
        with get_db() as db:
            # 遍历采集页面
            for page in range(1, max_pages + 1):
                params = {'ac': 'detail', 'pg': page}
                if type_id:
                    params['t'] = type_id
                if hours:
                    params['h'] = hours

                response = http_requests.get(api_url, params=params, timeout=30)
                response.raise_for_status()
                page_data = response.json()

                source_videos = page_data.get('list', [])
                if not source_videos:
                    break
                
                pages_processed += 1

                for video in source_videos:
                    # 验证视频有效性
                    if not is_valid_video(video):
                        skipped_count += 1
                        continue

                    vod_id = video.get('vod_id')
                    if not vod_id:
                        skipped_count += 1
                        continue

                    # 检查重复
                    if skip_duplicates and db.get_video(vod_id):
                        duplicate_count += 1
                        continue

                    # 处理播放URL
                    vod_play_url = process_play_url(video.get('vod_play_url', ''))

                    # 映射字段并插入数据库
                    db_video = {
                        'video_id': vod_id,
                        'video_url': vod_play_url,
                        'video_image': video.get('vod_pic', ''),
                        'video_title': video.get('vod_name', ''),
                        'video_category': video.get('type_name', ''),
                        'play_count': video.get('vod_hits', 0),
                        'upload_time': video.get('vod_time', ''),
                        'video_duration': video.get('vod_duration', video.get('vod_remarks', '')),
                        'video_coins': 0
                    }

                    if db.insert_video(db_video):
                        collected_videos.append({
                            'video_id': vod_id,
                            'video_title': video.get('vod_name', ''),
                            'video_category': video.get('type_name', '')
                        })

        result = {
            'collected_count': len(collected_videos),
            'skipped_count': skipped_count,
            'duplicate_count': duplicate_count,
            'pages_processed': pages_processed,
            'type_id': type_id,
            'hours': hours,
            'collected_at': datetime.now().isoformat(),
            'collected_videos': collected_videos[:50]  # Return first 50 for preview
        }

        if len(collected_videos) > 0:
            return api_response(data=result, message=f"成功采集 {len(collected_videos)} 个视频")
        else:
            return api_response(data=result, message="没有新视频可采集")

    except http_requests.RequestException as e:
        logger.error(f"采集视频失败: {e}")
        return api_response(message="采集失败: 采集源请求异常", code=500)
    except Exception as e:
        logger.error(f"采集视频失败: {e}")
        return api_response(message="采集失败", code=500)


@app.route('/api/admin/get-source-categories', methods=['GET'])
@handle_errors
def get_source_categories() -> Tuple[Response, int]:
    """
    获取采集源分类列表 (Get source categories)
    从采集源API获取可用的视频分类
    """
    api_url = os.environ.get('COLLECTOR_API_URL', 'https://api.sq03.shop/api.php/provide/vod/')

    try:
        params = {'ac': 'list'}
        response = http_requests.get(api_url, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()

        categories = data.get('class', [])
        return api_response(data=categories)

    except http_requests.RequestException as e:
        logger.error(f"获取分类失败: {e}")
        return api_response(message="获取分类失败: 采集源请求异常", code=500)
    except Exception as e:
        logger.error(f"获取分类失败: {e}")
        return api_response(message="获取分类失败", code=500)


def _media_update_with_backup(existing: Dict[str, Any], new_url: str,
                              new_image: str) -> Dict[str, Any]:
    """构建"更新链接/图片"的字段字典, 并在链接变化时保留旧链接为备用地址。

    采集源 (如 hanime) 的播放地址在白天/夜间可能不同, 因此当新采集到的
    video_url 与现有地址不同时, 把旧地址存入 video_url_backup, 播放失败时前端
    可自动切换到备用地址重试。

    Args:
        existing: 数据库中已存在的视频记录
        new_url: 新采集到的视频播放地址
        new_image: 新采集到的封面图片地址

    Returns:
        传给 db.update_video 的更新字段字典
    """
    updates: Dict[str, Any] = {}
    old_url = (existing.get('video_url') or '').strip()
    new_url = (new_url or '').strip()
    # 仅当地址确实发生变化(或原本为空)时才更新, 便于"更新全部"准确统计未变化数量
    if new_url and new_url != old_url:
        updates['video_url'] = new_url
        # 旧地址存在且不同才存为备用地址, 供播放失败时自动切换
        if old_url:
            updates['video_url_backup'] = old_url
    # 图片地址存在且发生变化时才更新, 避免用空值覆盖已有封面
    new_image = (new_image or '').strip()
    if new_image and new_image != (existing.get('video_image') or '').strip():
        updates['video_image'] = new_image
    return updates


def _hanime_parse_params(data: Dict[str, Any]) -> Dict[str, Any]:
    """解析 hanime 采集请求参数, 供普通与流式采集端点复用。"""
    genre = (data.get('genre') or hanime_scraper.DEFAULT_GENRE).strip()
    # 入库分类默认归到前端「里番动漫」子分类, 与搜索 genre 解耦
    category = (data.get('category') or '里番动漫').strip() or '里番动漫'
    collect_all: bool = bool(data.get('collect_all', False))
    # 采集全部时给一个较大的上限, iter_pages() 在遇到空页时会自动停止
    if collect_all:
        max_pages = 1000
    else:
        max_pages = max(1, min(int(data.get('max_pages', 1)), 20))
    skip_duplicates: bool = data.get('skip_duplicates', True)
    delay: float = max(0.0, min(float(data.get('delay', 1.0)), 10.0))
    return {
        'genre': genre,
        'category': category,
        'collect_all': collect_all,
        'max_pages': max_pages,
        'skip_duplicates': skip_duplicates,
        'delay': delay,
    }


def _hanime_preview(item: Dict[str, Any]) -> Dict[str, Any]:
    """生成用于前端预览的精简视频信息。"""
    return {
        'video_id': item.get('video_id'),
        'video_title': item.get('video_title', ''),
        'best_quality': item.get('best_quality'),
        'tags': item.get('tags', []),
        'play_count': item.get('play_count', 0),
        'upload_date': item.get('upload_date', ''),
    }


def _save_hanime_item(
    db: VideoDatabase,
    item: Dict[str, Any],
    genre: str,
    category: str,
    skip_duplicates: bool,
    stats: Dict[str, int],
    collected_videos: List[Dict[str, Any]],
) -> None:
    """处理并保存单个 hanime 采集条目, 就地累加统计数据。

    去重以「名称(标题)」为准: 若已存在同名视频, 只替换图片/视频链接,
    不新增重复的视频数据; 否则按 video_id 兜底判重后新增。
    """
    video_id = item.get('video_id')
    # 没有可播放地址的条目视为无效, 跳过
    if not video_id or not item.get('video_url'):
        stats['skipped'] += 1
        return

    record = hanime_scraper._to_video_record(item, genre)
    # 采集的视频统一归到目标分类(里番动漫)
    record['video_category'] = category

    title = (record.get('video_title') or '').strip()
    existing = db.get_video_by_title(title) if title else None
    if existing is None:
        existing = db.get_video(video_id)

    if existing:
        if skip_duplicates:
            # 只替换链接(图片链接与视频链接), 保留其余数据与采集时间;
            # 链接变化时把旧地址存为备用地址, 供播放失败时自动切换。
            updates = _media_update_with_backup(
                existing, record['video_url'], record['video_image']
            )
            if updates and db.update_video(existing['video_id'], updates):
                stats['updated'] += 1
            stats['duplicate'] += 1
            return
        # 未开启去重时, 按主键覆盖(可能重置采集时间)
        if db.insert_video(record):
            collected_videos.append(_hanime_preview(item))
        return

    if db.insert_video(record):
        collected_videos.append(_hanime_preview(item))


@app.route('/api/admin/collect-hanime', methods=['POST'])
@handle_errors
def collect_hanime() -> Tuple[Response, int]:
    """
    Hanime1 裏番/里番 采集 (Hanime1 hentai collection)

    使用 tools/hanime_scraper.py 从 hanime1.me 采集视频, 解析最高画质播放地址、
    标签、观看次数与上传日期, 并保存到数据库。

    Request Body:
        genre: 采集分类 (可选, 默认: 裏番) —— hanime 搜索用的类型
        category: 入库分类 (可选, 默认: 里番动漫) —— 保存到数据库/前端展示的分类
        max_pages: 采集列表页数 (可选, 默认1, 最大20)
        collect_all: 采集全部页 (可选, 默认false) —— 一直翻页直到没有更多视频
        skip_duplicates: 重复名称的视频是否只替换链接不新增 (可选, 默认true)
        delay: 每次请求间隔秒数 (可选, 默认1.0)
    """
    if hanime_scraper is None:
        return api_response(message="采集模块 hanime_scraper 未安装", code=500)

    params = _hanime_parse_params(request.get_json() or {})
    genre = params['genre']
    category = params['category']
    collect_all = params['collect_all']
    max_pages = params['max_pages']
    skip_duplicates = params['skip_duplicates']
    delay = params['delay']

    collected_videos: List[Dict[str, Any]] = []
    stats: Dict[str, int] = {'skipped': 0, 'duplicate': 0, 'updated': 0}
    pages_processed = 0
    total_items = 0

    try:
        scraper = hanime_scraper.HanimeScraper(genre=genre, delay=delay)
        # 逐页采集: 每采完一页就立即入库, 避免整批采集(尤其"采集全部")
        # 中途失败时前面已采集的数据丢失。
        for page, page_items in scraper.iter_pages(
            pages=max_pages, with_details=True
        ):
            total_items += len(page_items)
            with get_db() as db:
                for item in page_items:
                    _save_hanime_item(
                        db, item, genre, category,
                        skip_duplicates, stats, collected_videos,
                    )
            pages_processed = page

        updated_count = stats['updated']
        result = {
            'collected_count': len(collected_videos),
            'updated_count': updated_count,
            'skipped_count': stats['skipped'],
            'duplicate_count': stats['duplicate'],
            'pages_processed': pages_processed,
            'collect_all': collect_all,
            'total_items': total_items,
            'genre': genre,
            'category': category,
            'collected_at': datetime.now().isoformat(),
            'collected_videos': collected_videos[:50],
        }

        if collected_videos or updated_count:
            parts = []
            if collected_videos:
                parts.append(f"新增 {len(collected_videos)} 个")
            if updated_count:
                parts.append(f"更新链接 {updated_count} 个")
            return api_response(
                data=result,
                message="采集完成: " + ", ".join(parts)
            )
        return api_response(data=result, message="没有新视频可采集")

    except http_requests.RequestException as e:
        logger.error(f"Hanime采集失败: {e}")
        return api_response(message="采集失败: 采集源请求异常", code=500)
    except Exception as e:
        logger.error(f"Hanime采集失败: {e}")
        return api_response(message="采集失败", code=500)


def _sse_event(event: str, payload: Dict[str, Any]) -> str:
    """构造一条 Server-Sent Events 消息。"""
    return f"event: {event}\ndata: {json.dumps(payload, ensure_ascii=False)}\n\n"


@app.route('/api/admin/collect-hanime-stream', methods=['POST'])
@handle_errors
def collect_hanime_stream() -> Response:
    """
    Hanime1 采集(流式) —— 采集完一页保存一页, 并实时上报进度。

    与 /api/admin/collect-hanime 相同的请求参数, 但以 Server-Sent Events (SSE)
    的形式逐页返回进度: 每采完一页立即入库并推送一条 `progress` 事件
    (含当前页、总页数、剩余页数与累计统计), 全部完成后推送一条 `done` 事件
    (含最终结果), 出错时推送 `error` 事件。
    """
    if hanime_scraper is None:
        return api_response(message="采集模块 hanime_scraper 未安装", code=500)[0]

    params = _hanime_parse_params(request.get_json() or {})
    genre = params['genre']
    category = params['category']
    collect_all = params['collect_all']
    max_pages = params['max_pages']
    skip_duplicates = params['skip_duplicates']
    delay = params['delay']
    # 用于进度展示的目标页数: 采集全部时未知(None)
    target_pages: Optional[int] = None if collect_all else max_pages

    def generate() -> Generator[str, None, None]:
        collected_videos: List[Dict[str, Any]] = []
        stats: Dict[str, int] = {'skipped': 0, 'duplicate': 0, 'updated': 0}
        pages_processed = 0
        total_items = 0

        yield _sse_event('start', {
            'collect_all': collect_all,
            'total_pages': target_pages,
        })

        try:
            scraper = hanime_scraper.HanimeScraper(genre=genre, delay=delay)
            for page, page_items in scraper.iter_pages(
                pages=max_pages, with_details=True
            ):
                total_items += len(page_items)
                with get_db() as db:
                    for item in page_items:
                        _save_hanime_item(
                            db, item, genre, category,
                            skip_duplicates, stats, collected_videos,
                        )
                pages_processed = page

                remaining = (
                    None if target_pages is None
                    else max(0, target_pages - page)
                )
                yield _sse_event('progress', {
                    'page': page,
                    'total_pages': target_pages,
                    'remaining_pages': remaining,
                    'collected_count': len(collected_videos),
                    'updated_count': stats['updated'],
                    'skipped_count': stats['skipped'],
                    'duplicate_count': stats['duplicate'],
                    'total_items': total_items,
                    'collect_all': collect_all,
                })

            result = {
                'collected_count': len(collected_videos),
                'updated_count': stats['updated'],
                'skipped_count': stats['skipped'],
                'duplicate_count': stats['duplicate'],
                'pages_processed': pages_processed,
                'collect_all': collect_all,
                'total_items': total_items,
                'genre': genre,
                'category': category,
                'collected_at': datetime.now().isoformat(),
                'collected_videos': collected_videos[:50],
            }
            yield _sse_event('done', result)

        except http_requests.RequestException as e:
            logger.error(f"Hanime采集失败: {e}")
            yield _sse_event('error', {'message': '采集失败: 采集源请求异常'})
        except Exception as e:
            logger.error(f"Hanime采集失败: {e}")
            yield _sse_event('error', {'message': '采集失败'})

    headers = {
        'Content-Type': 'text/event-stream; charset=utf-8',
        'Cache-Control': 'no-cache',
        # 关闭 nginx 反向代理的响应缓冲, 否则进度事件会被缓存到最后才一次性下发
        'X-Accel-Buffering': 'no',
        'Connection': 'keep-alive',
    }
    return Response(stream_with_context(generate()), headers=headers)


@app.route('/api/admin/refresh-hanime-media', methods=['POST'])
@handle_errors
def refresh_hanime_media() -> Tuple[Response, int]:
    """
    更新全部裏番视频的图片与播放地址 (Refresh all hanime videos' image & url)

    遍历数据库中指定分类的所有视频, 逐个重新访问 hanime 详情页, 抓取最新的
    播放地址与封面图片并更新。若播放地址发生变化, 旧地址会被保存为备用地址
    (video_url_backup), 播放失败时前端可自动切换到备用地址重试。

    Request Body:
        category: 要刷新的入库分类 (可选, 默认: 里番动漫)
        delay: 每次请求间隔秒数 (可选, 默认1.0)
        limit: 最多刷新多少个视频 (可选, 0 或不填表示全部)
    """
    if hanime_scraper is None:
        return api_response(message="采集模块 hanime_scraper 未安装", code=500)

    data = request.get_json() or {}
    category = (data.get('category') or '里番动漫').strip() or '里番动漫'
    delay: float = max(0.0, min(float(data.get('delay', 1.0)), 10.0))
    limit: int = max(0, int(data.get('limit', 0)))

    updated_count = 0
    unchanged_count = 0
    failed_count = 0
    checked_count = 0

    try:
        scraper = hanime_scraper.HanimeScraper(delay=delay)

        with get_db() as db:
            videos = db.get_videos_by_category(category)
            if limit:
                videos = videos[:limit]

            for video in videos:
                video_id = video.get('video_id')
                if not video_id:
                    continue
                checked_count += 1
                try:
                    detail = scraper.fetch_watch(int(video_id))
                except http_requests.RequestException as e:
                    logger.warning(f"刷新详情页失败 v={video_id}: {e}")
                    failed_count += 1
                    if delay:
                        time.sleep(delay)
                    continue

                new_url = detail.get('video_url') or ''
                new_image = detail.get('video_image') or ''
                # 没解析到播放地址视为失败, 保留原数据不动
                if not new_url:
                    failed_count += 1
                    if delay:
                        time.sleep(delay)
                    continue

                updates = _media_update_with_backup(video, new_url, new_image)
                if updates:
                    if db.update_video(video_id, updates):
                        updated_count += 1
                    else:
                        failed_count += 1
                else:
                    unchanged_count += 1

                if delay:
                    time.sleep(delay)

        result = {
            'category': category,
            'checked_count': checked_count,
            'updated_count': updated_count,
            'unchanged_count': unchanged_count,
            'failed_count': failed_count,
            'refreshed_at': datetime.now().isoformat(),
        }

        if checked_count == 0:
            return api_response(data=result, message="该分类下没有视频")
        return api_response(
            data=result,
            message=f"更新完成: 刷新 {updated_count} 个, 未变化 {unchanged_count} 个, 失败 {failed_count} 个"
        )

    except http_requests.RequestException as e:
        logger.error(f"刷新Hanime媒体失败: {e}")
        return api_response(message="更新失败: 采集源请求异常", code=500)
    except Exception as e:
        logger.error(f"刷新Hanime媒体失败: {e}")
        return api_response(message="更新失败", code=500)


# ==================== 错误处理 (Error Handlers) ====================

@app.errorhandler(404)
def not_found(e: Exception) -> Tuple[Response, int]:
    """404 错误处理 (404 error handler)"""
    return api_response(message="接口不存在", code=404)


@app.errorhandler(405)
def method_not_allowed(e: Exception) -> Tuple[Response, int]:
    """405 错误处理 (405 error handler)"""
    return api_response(message="方法不允许", code=405)


@app.errorhandler(413)
def payload_too_large(e: Exception) -> Tuple[Response, int]:
    """413 错误处理 (413 error handler - upload too large)"""
    return api_response(message="上传文件过大（最大10MB）", code=413)


@app.errorhandler(500)
def internal_error(e: Exception) -> Tuple[Response, int]:
    """500 错误处理 (500 error handler)"""
    return api_response(message="服务器内部错误", code=500)


# ==================== 主程序入口 (Main Entry Point) ====================

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='视频API服务器 (Video API Server)')
    parser.add_argument('--host', type=str, default='0.0.0.0',
                        help='监听地址 / Listen address (默认: 0.0.0.0)')
    parser.add_argument('--port', type=int, default=5000,
                        help='监听端口 / Listen port (默认: 5000)')
    parser.add_argument('--production', action='store_true',
                        help='生产模式 / Production mode (关闭调试)')
    parser.add_argument('--sqlite', action='store_true',
                        help='使用SQLite而非MySQL / Use SQLite instead of MySQL')

    args = parser.parse_args()

    # 设置环境变量 (Set environment variables)
    if args.sqlite:
        os.environ['USE_MYSQL'] = 'false'

    debug: bool = not args.production

    print("\n" + "=" * 60)
    print("🚀 视频API服务器 (Video API Server)")
    print("=" * 60)
    print(f"📡 地址 (Address): http://{args.host}:{args.port}")
    print(f"🔧 模式 (Mode): {'生产 (Production)' if args.production else '开发 (Development)'}")
    print(f"📦 数据库 (Database): {'SQLite' if args.sqlite else 'MySQL'}")
    print("=" * 60 + "\n")

    app.run(
        host=args.host,
        port=args.port,
        debug=debug,
        threaded=True
    )
