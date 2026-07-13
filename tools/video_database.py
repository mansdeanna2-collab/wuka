#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
视频数据库模块 (Video Database Module)
======================================
基于MySQL的视频信息存储系统

数据表结构:
- video_id: 视频ID (主键)
- video_url: 视频链接
- video_image: 视频图片/封面
- video_title: 视频标题
- video_category: 视频分类
- play_count: 播放数
- upload_time: 上传时间
- video_duration: 视频时长
- video_coins: 视频金币

MySQL连接配置通过环境变量设置:
- MYSQL_HOST: 数据库主机
- MYSQL_PORT: 数据库端口
- MYSQL_DATABASE: 数据库名
- MYSQL_USER: 用户名
- MYSQL_PASSWORD: 密码

SQLite配置:
- SQLITE_DB_PATH: SQLite数据库文件路径 (默认: /app/data/videos.db)

使用方法:
    from video_database import VideoDatabase

    db = VideoDatabase()
    db.insert_video({
        'video_id': 1,
        'video_url': 'https://example.com/video.mp4',
        'video_image': 'https://example.com/cover.jpg',
        'video_title': '示例视频',
        'video_category': '电影',
        'play_count': 1000,
        'upload_time': '2026-01-30 10:00:00',
        'video_duration': '01:30:00',
        'video_coins': 0
    })

作者: Auto-generated
日期: 2026-01-30
"""

import os
import re
import json
import logging
import sqlite3
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple

# 配置日志
logger = logging.getLogger(__name__)

# MySQL连接配置 - 从环境变量获取
MYSQL_CONFIG = {
    'host': os.environ.get('MYSQL_HOST', 'localhost'),
    'port': int(os.environ.get('MYSQL_PORT', '3306')),
    'database': os.environ.get('MYSQL_DATABASE', 'videos'),
    'user': os.environ.get('MYSQL_USER', 'root'),
    'password': os.environ.get('MYSQL_PASSWORD', ''),
    'charset': 'utf8mb4'
}

# 尝试导入MySQL连接器
try:
    import pymysql
    MYSQL_AVAILABLE = True
except ImportError:
    MYSQL_AVAILABLE = False
    logger.warning("pymysql 未安装，将使用SQLite作为备用数据库")


class VideoDatabase:
    """
    视频数据库管理类

    支持MySQL和SQLite两种数据库后端。
    注意：建议使用上下文管理器 (with语句) 来确保数据库连接正确关闭，
    或手动调用 close() 方法。
    """

    # 前端/后台视频列表排序: 优先按视频上架日期(upload_time, 即详情页显示的日期)倒序,
    # 缺失上架日期的视频回退到采集时间(created_at)倒序, 最后用 video_id 保证稳定排序。
    # upload_time 存储格式为 'YYYY-MM-DD' 字符串, 可按字典序倒序得到最新日期在前。
    _VIDEO_ORDER_BY = (
        "(upload_time IS NULL OR upload_time = '') , "
        "upload_time DESC, created_at DESC, video_id DESC"
    )

    @staticmethod
    def _get_default_db_path():
        """
        获取默认数据库路径

        优先级:
        1. SQLITE_DB_PATH 环境变量 (如果设置且非空)
        2. /app/data/videos.db (Docker环境，当目录存在时)
        3. data/videos.db (本地开发)
        """
        env_path = os.environ.get('SQLITE_DB_PATH', '').strip()
        if env_path:
            return env_path
        # Docker环境优先使用绝对路径
        if os.path.isdir('/app/data'):
            return '/app/data/videos.db'
        # 本地开发使用相对路径
        return 'data/videos.db'

    def __init__(self, use_mysql: bool = True, db_path: Optional[str] = None,
                 mysql_config: Optional[Dict[str, Any]] = None, verbose: bool = True):
        """
        初始化数据库连接

        Args:
            use_mysql: 是否使用MySQL，默认True。如果pymysql未安装，自动降级到SQLite
            db_path: SQLite数据库文件路径。默认路径取决于环境:
                     - SQLITE_DB_PATH环境变量 (如果设置)
                     - Docker环境: /app/data/videos.db
                     - 本地开发: data/videos.db
            mysql_config: MySQL连接配置，默认使用全局配置
            verbose: 是否输出日志信息，默认True
        """
        self.db_path = db_path or self._get_default_db_path()
        self.verbose = verbose
        self.connection = None
        self.use_mysql = use_mysql and MYSQL_AVAILABLE
        self.mysql_config = mysql_config or MYSQL_CONFIG
        self._init_database()

    def _init_database(self) -> None:
        """初始化数据库，创建表结构"""
        if self.use_mysql:
            self._init_mysql()
        else:
            self._init_sqlite()

    def _init_mysql(self) -> None:
        """初始化MySQL数据库"""
        try:
            self.connection = pymysql.connect(
                host=self.mysql_config['host'],
                port=self.mysql_config['port'],
                user=self.mysql_config['user'],
                password=self.mysql_config['password'],
                database=self.mysql_config['database'],
                charset=self.mysql_config.get('charset', 'utf8mb4'),
                cursorclass=pymysql.cursors.DictCursor
            )

            cursor = self.connection.cursor()

            # 创建视频表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS videos (
                    video_id INT PRIMARY KEY,
                    video_url TEXT NOT NULL,
                    video_url_backup TEXT,
                    video_image TEXT,
                    video_title VARCHAR(500) NOT NULL,
                    video_category VARCHAR(100),
                    video_tags TEXT,
                    play_count INT DEFAULT 0,
                    upload_time VARCHAR(50),
                    video_duration VARCHAR(50),
                    video_coins INT DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
            ''')

            # 兼容旧表结构: 补齐 video_tags 列
            self._migrate_videos_mysql(cursor)

            # 创建索引以提高查询效率
            try:
                cursor.execute('CREATE INDEX idx_video_category ON videos(video_category)')
            except pymysql.err.OperationalError:
                pass  # 索引已存在

            try:
                cursor.execute('CREATE INDEX idx_video_upload_time ON videos(upload_time)')
            except pymysql.err.OperationalError:
                pass

            try:
                cursor.execute('CREATE INDEX idx_video_play_count ON videos(play_count)')
            except pymysql.err.OperationalError:
                pass

            try:
                cursor.execute('CREATE INDEX idx_video_created_at ON videos(created_at)')
            except pymysql.err.OperationalError:
                pass

            # 创建导航分类配置表 (Create nav_categories table for global admin settings)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS nav_categories (
                    id INT PRIMARY KEY AUTO_INCREMENT,
                    category_key VARCHAR(100) UNIQUE NOT NULL,
                    label VARCHAR(100) NOT NULL,
                    subcategories TEXT,
                    sort_order INT DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
            ''')

            # 创建轮播图配置表 (Create carousel_items table for admin-managed home carousel)
            # 轮播图支持两种条目：已有视频(item_type='video')与独立图片(item_type='image')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS carousel_items (
                    id INT PRIMARY KEY AUTO_INCREMENT,
                    item_type VARCHAR(20) DEFAULT 'video',
                    video_id INT NULL,
                    image_url TEXT,
                    title VARCHAR(500),
                    link_url TEXT,
                    sort_order INT DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
            ''')

            # 兼容旧表结构：补齐独立图片所需的列，并允许 video_id 为空
            self._migrate_carousel_items_mysql(cursor)

            self.connection.commit()
            self._log(f"✅ MySQL数据库初始化完成: {self.mysql_config['database']}")
        except Exception as e:
            logger.error(f"MySQL连接失败: {e}")
            self._log(f"⚠️ MySQL连接失败，降级到SQLite: {e}")
            # 关闭可能已建立的 MySQL 连接，避免降级到 SQLite 时泄漏连接
            if self.connection is not None:
                try:
                    self.connection.close()
                except Exception:
                    pass
                self.connection = None
            self.use_mysql = False
            self._init_sqlite()

    def _init_sqlite(self) -> None:
        """初始化SQLite数据库"""
        # 确保父目录存在
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
            self._log(f"📂 创建数据库目录: {db_dir}")

        self.connection = sqlite3.connect(self.db_path)
        self.connection.row_factory = sqlite3.Row

        cursor = self.connection.cursor()

        # 创建视频表 (使用video_coins代替video_price)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS videos (
                video_id INTEGER PRIMARY KEY,
                video_url TEXT NOT NULL,
                video_url_backup TEXT,
                video_image TEXT,
                video_title TEXT NOT NULL,
                video_category TEXT,
                video_tags TEXT,
                play_count INTEGER DEFAULT 0,
                upload_time TEXT,
                video_duration TEXT,
                video_coins INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # 兼容旧表结构: 补齐 video_tags 列
        self._migrate_videos_sqlite(cursor)

        # 创建索引以提高查询效率
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_video_category
            ON videos(video_category)
        ''')

        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_video_upload_time
            ON videos(upload_time)
        ''')

        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_video_play_count
            ON videos(play_count)
        ''')

        # 采集时间索引: 前端按采集时间(created_at)倒序展示最新视频
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_video_created_at
            ON videos(created_at)
        ''')

        # 创建导航分类配置表 (Create nav_categories table for global admin settings)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS nav_categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category_key TEXT UNIQUE NOT NULL,
                label TEXT NOT NULL,
                subcategories TEXT,
                sort_order INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # 创建轮播图配置表 (Create carousel_items table for admin-managed home carousel)
        # 轮播图内容由管理员在后台手动选择，不再自动展示新增视频。
        # 支持两种条目：已有视频(item_type='video')与独立图片(item_type='image')。
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS carousel_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_type TEXT DEFAULT 'video',
                video_id INTEGER,
                image_url TEXT,
                title TEXT,
                link_url TEXT,
                sort_order INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # 兼容旧表结构：补齐独立图片所需的列
        self._migrate_carousel_items_sqlite(cursor)

        self.connection.commit()
        self._log(f"✅ 数据库初始化完成: {self.db_path}")

    def _migrate_videos_mysql(self, cursor) -> None:
        """为旧版 MySQL videos 表补齐新增的列 (如 video_tags, video_url_backup)"""
        column_defs = {
            'video_tags': "ALTER TABLE videos ADD COLUMN video_tags TEXT",
            'video_url_backup': "ALTER TABLE videos ADD COLUMN video_url_backup TEXT",
        }
        for sql in column_defs.values():
            try:
                cursor.execute(sql)
            except Exception:
                # 列已存在
                pass

    def _migrate_videos_sqlite(self, cursor) -> None:
        """为旧版 SQLite videos 表补齐新增的列 (如 video_tags, video_url_backup)"""
        cursor.execute('PRAGMA table_info(videos)')
        existing = {row[1] for row in cursor.fetchall()}
        if 'video_tags' not in existing:
            try:
                cursor.execute('ALTER TABLE videos ADD COLUMN video_tags TEXT')
            except Exception:
                pass
        if 'video_url_backup' not in existing:
            try:
                cursor.execute('ALTER TABLE videos ADD COLUMN video_url_backup TEXT')
            except Exception:
                pass

    def _migrate_carousel_items_mysql(self, cursor) -> None:
        """为旧版 MySQL carousel_items 表补齐独立图片所需的列并放宽 video_id 约束"""
        column_defs = {
            'item_type': "ALTER TABLE carousel_items ADD COLUMN item_type VARCHAR(20) DEFAULT 'video'",
            'image_url': "ALTER TABLE carousel_items ADD COLUMN image_url TEXT",
            'title': "ALTER TABLE carousel_items ADD COLUMN title VARCHAR(500)",
            'link_url': "ALTER TABLE carousel_items ADD COLUMN link_url TEXT",
        }
        for sql in column_defs.values():
            try:
                cursor.execute(sql)
            except Exception:
                # 列已存在
                pass
        # 允许 video_id 为空（独立图片没有关联视频）
        try:
            cursor.execute('ALTER TABLE carousel_items MODIFY COLUMN video_id INT NULL')
        except Exception:
            pass

    def _migrate_carousel_items_sqlite(self, cursor) -> None:
        """为旧版 SQLite carousel_items 表补齐独立图片所需的列"""
        cursor.execute('PRAGMA table_info(carousel_items)')
        info = cursor.fetchall()
        existing = {row[1] for row in info}
        # 旧表将 video_id 定义为 NOT NULL，SQLite 无法直接放宽该约束，
        # 独立图片条目需要 video_id 为空，因此重建表并迁移数据。
        video_id_not_null = any(row[1] == 'video_id' and row[3] == 1 for row in info)
        if video_id_not_null:
            cursor.execute('ALTER TABLE carousel_items RENAME TO carousel_items_old')
            cursor.execute('''
                CREATE TABLE carousel_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    item_type TEXT DEFAULT 'video',
                    video_id INTEGER,
                    image_url TEXT,
                    title TEXT,
                    link_url TEXT,
                    sort_order INTEGER DEFAULT 0,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            cursor.execute('''
                INSERT INTO carousel_items (item_type, video_id, sort_order, created_at)
                SELECT 'video', video_id, sort_order, created_at FROM carousel_items_old
            ''')
            cursor.execute('DROP TABLE carousel_items_old')
            return

        column_defs = {
            'item_type': "ALTER TABLE carousel_items ADD COLUMN item_type TEXT DEFAULT 'video'",
            'image_url': "ALTER TABLE carousel_items ADD COLUMN image_url TEXT",
            'title': "ALTER TABLE carousel_items ADD COLUMN title TEXT",
            'link_url': "ALTER TABLE carousel_items ADD COLUMN link_url TEXT",
        }
        for column, sql in column_defs.items():
            if column not in existing:
                try:
                    cursor.execute(sql)
                except Exception:
                    pass

    def _log(self, message: str) -> None:
        """输出日志信息"""
        if self.verbose:
            print(message)
        logger.info(message)

    def insert_video(self, video_data: Dict[str, Any]) -> bool:
        """
        插入单个视频记录

        Args:
            video_data: 视频数据字典，包含以下字段:
                - video_id: 视频ID (必需)
                - video_url: 视频链接 (必需)
                - video_image: 视频图片
                - video_title: 视频标题 (必需)
                - video_category: 视频分类
                - video_tags: 视频标签 (逗号分隔)
                - play_count: 播放数
                - upload_time: 上传时间
                - video_duration: 视频时长
                - video_coins: 视频金币

        Returns:
            插入成功返回True，失败返回False
        """
        required_fields = ['video_id', 'video_url', 'video_title']
        for field in required_fields:
            if field not in video_data or video_data[field] is None:
                self._log(f"❌ 缺少必需字段: {field}")
                return False

        try:
            cursor = self.connection.cursor()

            if self.use_mysql:
                # MySQL使用 REPLACE INTO
                cursor.execute('''
                    REPLACE INTO videos
                    (video_id, video_url, video_url_backup, video_image, video_title, video_category,
                     video_tags, play_count, upload_time, video_duration, video_coins)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ''', (
                    video_data.get('video_id'),
                    video_data.get('video_url'),
                    video_data.get('video_url_backup', ''),
                    video_data.get('video_image', ''),
                    video_data.get('video_title'),
                    video_data.get('video_category', ''),
                    video_data.get('video_tags', ''),
                    video_data.get('play_count', 0),
                    video_data.get('upload_time', ''),
                    video_data.get('video_duration', ''),
                    video_data.get('video_coins', 0)
                ))
            else:
                # SQLite使用 INSERT OR REPLACE
                cursor.execute('''
                    INSERT OR REPLACE INTO videos
                    (video_id, video_url, video_url_backup, video_image, video_title, video_category,
                     video_tags, play_count, upload_time, video_duration, video_coins, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    video_data.get('video_id'),
                    video_data.get('video_url'),
                    video_data.get('video_url_backup', ''),
                    video_data.get('video_image', ''),
                    video_data.get('video_title'),
                    video_data.get('video_category', ''),
                    video_data.get('video_tags', ''),
                    video_data.get('play_count', 0),
                    video_data.get('upload_time', ''),
                    video_data.get('video_duration', ''),
                    video_data.get('video_coins', 0),
                    datetime.now().isoformat()
                ))

            self.connection.commit()
            return True
        except Exception as e:
            logger.error(f"插入视频失败: {e}")
            self._log(f"❌ 插入视频失败: {e}")
            return False

    def insert_videos(self, videos: List[Dict[str, Any]]) -> int:
        """
        批量插入视频记录

        Args:
            videos: 视频数据列表

        Returns:
            成功插入的视频数量
        """
        success_count = 0
        for video in videos:
            if self.insert_video(video):
                success_count += 1

        self._log(f"✅ 批量插入完成: 成功 {success_count}/{len(videos)} 个")
        return success_count

    def get_video(self, video_id: int) -> Optional[Dict[str, Any]]:
        """
        根据ID获取视频信息

        Args:
            video_id: 视频ID

        Returns:
            视频数据字典，如果不存在返回None
        """
        cursor = self.connection.cursor()
        placeholder = '%s' if self.use_mysql else '?'
        cursor.execute(f'SELECT * FROM videos WHERE video_id = {placeholder}', (video_id,))
        row = cursor.fetchone()

        if row:
            return dict(row) if isinstance(row, dict) else dict(row)
        return None

    def get_video_by_title(self, title: str) -> Optional[Dict[str, Any]]:
        """
        根据标题(名称)获取视频信息

        用于采集去重: 相同名称的视频被视为同一条内容, 仅替换其图片/视频链接,
        而不新增重复记录。若存在多条同名记录, 返回最早采集的一条(created_at 最小),
        以保持展示的稳定性。

        Args:
            title: 视频标题

        Returns:
            视频数据字典，如果不存在返回None
        """
        if not title:
            return None

        cursor = self.connection.cursor()
        placeholder = '%s' if self.use_mysql else '?'
        cursor.execute(
            f'SELECT * FROM videos WHERE video_title = {placeholder} '
            f'ORDER BY created_at ASC, video_id ASC LIMIT 1',
            (title,)
        )
        row = cursor.fetchone()

        if row:
            return dict(row) if isinstance(row, dict) else dict(row)
        return None

    def get_all_videos(self, limit: Optional[int] = None,
                       offset: int = 0) -> List[Dict[str, Any]]:
        """
        获取所有视频

        Args:
            limit: 限制返回数量
            offset: 偏移量

        Returns:
            视频列表
        """
        cursor = self.connection.cursor()
        placeholder = '%s' if self.use_mysql else '?'

        if limit:
            cursor.execute(
                f'SELECT * FROM videos ORDER BY {self._VIDEO_ORDER_BY} LIMIT {placeholder} OFFSET {placeholder}',
                (limit, offset)
            )
        else:
            cursor.execute(f'SELECT * FROM videos ORDER BY {self._VIDEO_ORDER_BY}')

        rows = cursor.fetchall()
        return [dict(row) if isinstance(row, dict) else dict(row) for row in rows]

    def count_all_videos(self) -> int:
        """获取视频总数 (Get total number of videos)"""
        cursor = self.connection.cursor()
        cursor.execute('SELECT COUNT(*) as cnt FROM videos')
        row = cursor.fetchone()
        return int(row['cnt'] if isinstance(row, dict) else row[0])

    def _tag_filter_clause(self, tag: str) -> Tuple[str, str]:
        """
        构建按标签过滤的 SQL 片段 (Build a SQL fragment for filtering by an exact tag)

        video_tags 以逗号分隔存储 (如 "碧池,巨乳"), 为避免子串误匹配,
        使用逗号边界匹配: 在两侧补上逗号后用 LIKE '%,tag,%' 精确匹配单个标签。

        Args:
            tag: 标签名称

        Returns:
            (SQL条件片段, LIKE匹配参数)
        """
        placeholder = '%s' if self.use_mysql else '?'
        # 逗号拼接: MySQL 用 CONCAT, SQLite 用 || 运算符
        if self.use_mysql:
            wrapped = "CONCAT(',', COALESCE(video_tags, ''), ',')"
        else:
            wrapped = "(',' || COALESCE(video_tags, '') || ',')"
        clause = f"{wrapped} LIKE {placeholder}"
        return clause, f"%,{tag},%"

    def get_videos_by_category(self, category: str,
                               limit: Optional[int] = None,
                               offset: int = 0,
                               tag: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        按分类获取视频

        Args:
            category: 视频分类
            limit: 限制返回数量
            offset: 偏移量
            tag: 可选的视频标签, 仅返回包含该标签的视频

        Returns:
            视频列表
        """
        cursor = self.connection.cursor()
        placeholder = '%s' if self.use_mysql else '?'

        where = f'video_category = {placeholder}'
        params: List[Any] = [category]
        tag = (tag or '').strip()
        if tag:
            clause, like_param = self._tag_filter_clause(tag)
            where += f' AND {clause}'
            params.append(like_param)

        if limit:
            cursor.execute(
                f'SELECT * FROM videos WHERE {where} ORDER BY {self._VIDEO_ORDER_BY} LIMIT {placeholder} OFFSET {placeholder}',
                (*params, limit, offset)
            )
        else:
            cursor.execute(
                f'SELECT * FROM videos WHERE {where} ORDER BY {self._VIDEO_ORDER_BY}',
                tuple(params)
            )

        rows = cursor.fetchall()
        return [dict(row) if isinstance(row, dict) else dict(row) for row in rows]

    def count_videos_by_category(self, category: str,
                                 tag: Optional[str] = None) -> int:
        """获取指定分类的视频总数 (Get total number of videos in a category)

        Args:
            category: 视频分类
            tag: 可选的视频标签, 仅统计包含该标签的视频
        """
        cursor = self.connection.cursor()
        placeholder = '%s' if self.use_mysql else '?'

        where = f'video_category = {placeholder}'
        params: List[Any] = [category]
        tag = (tag or '').strip()
        if tag:
            clause, like_param = self._tag_filter_clause(tag)
            where += f' AND {clause}'
            params.append(like_param)

        cursor.execute(
            f'SELECT COUNT(*) as cnt FROM videos WHERE {where}',
            tuple(params)
        )
        row = cursor.fetchone()
        return int(row['cnt'] if isinstance(row, dict) else row[0])

    def get_category_tags(self, category: str,
                          limit: int = 60) -> List[Dict[str, Any]]:
        """
        获取指定分类下的视频标签及其数量 (按出现频率降序)

        Args:
            category: 视频分类
            limit: 最多返回的标签数量

        Returns:
            标签列表, 每项为 {"tag": 标签名, "count": 视频数}
        """
        cursor = self.connection.cursor()
        placeholder = '%s' if self.use_mysql else '?'
        cursor.execute(
            f"SELECT video_tags FROM videos WHERE video_category = {placeholder} "
            f"AND video_tags IS NOT NULL AND video_tags != ''",
            (category,)
        )
        rows = cursor.fetchall()

        counts: Dict[str, int] = {}
        for row in rows:
            raw = row['video_tags'] if isinstance(row, dict) else row[0]
            if not raw:
                continue
            for tag in str(raw).split(','):
                tag = tag.strip()
                if not tag:
                    continue
                counts[tag] = counts.get(tag, 0) + 1

        ordered = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
        if limit and limit > 0:
            ordered = ordered[:limit]
        return [{"tag": tag, "count": cnt} for tag, cnt in ordered]

    def search_videos(self, keyword: str,
                      limit: Optional[int] = None,
                      offset: int = 0) -> List[Dict[str, Any]]:
        """
        搜索视频标题

        Args:
            keyword: 搜索关键词
            limit: 限制返回数量
            offset: 偏移量

        Returns:
            匹配的视频列表
        """
        cursor = self.connection.cursor()
        search_pattern = f"%{keyword}%"
        placeholder = '%s' if self.use_mysql else '?'

        if limit:
            cursor.execute(
                f'SELECT * FROM videos WHERE video_title LIKE {placeholder} ORDER BY play_count DESC LIMIT {placeholder} OFFSET {placeholder}',
                (search_pattern, limit, offset)
            )
        else:
            cursor.execute(
                f'SELECT * FROM videos WHERE video_title LIKE {placeholder} ORDER BY play_count DESC',
                (search_pattern,)
            )

        rows = cursor.fetchall()
        return [dict(row) if isinstance(row, dict) else dict(row) for row in rows]

    def count_search_videos(self, keyword: str) -> int:
        """获取搜索结果的视频总数 (Get total number of videos matching a keyword)"""
        cursor = self.connection.cursor()
        search_pattern = f"%{keyword}%"
        placeholder = '%s' if self.use_mysql else '?'
        cursor.execute(
            f'SELECT COUNT(*) as cnt FROM videos WHERE video_title LIKE {placeholder}',
            (search_pattern,)
        )
        row = cursor.fetchone()
        return int(row['cnt'] if isinstance(row, dict) else row[0])

    def get_top_videos(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        获取播放量最高的视频

        优先返回有播放量的视频 (play_count > 0)，按播放量降序排列。
        如果没有任何视频有播放量（例如刚添加的新视频播放量都为0），
        则回退到返回最新上传的视频，确保前端轮播图始终有内容展示，
        不会因为播放量都为0而完全不显示。

        Args:
            limit: 返回数量

        Returns:
            视频列表
        """
        cursor = self.connection.cursor()
        placeholder = '%s' if self.use_mysql else '?'
        cursor.execute(
            f'SELECT * FROM videos WHERE play_count > 0 ORDER BY play_count DESC LIMIT {placeholder}',
            (limit,)
        )
        rows = cursor.fetchall()
        videos = [dict(row) if isinstance(row, dict) else dict(row) for row in rows]

        # Fallback: if no videos have play counts yet, show the most recent
        # videos so the carousel still displays content instead of being empty.
        if not videos:
            cursor.execute(
                f'SELECT * FROM videos ORDER BY created_at DESC, video_id DESC LIMIT {placeholder}',
                (limit,)
            )
            rows = cursor.fetchall()
            videos = [dict(row) if isinstance(row, dict) else dict(row) for row in rows]

        return videos

    def update_video(self, video_id: int,
                     updates: Dict[str, Any]) -> bool:
        """
        更新视频信息

        Args:
            video_id: 视频ID
            updates: 要更新的字段和值

        Returns:
            更新成功返回True，失败返回False
        """
        if not updates:
            return False

        # 构建更新SQL
        # 注意：字段名来自 allowed_fields 白名单，防止SQL注入
        allowed_fields = [
            'video_url', 'video_url_backup', 'video_image', 'video_title', 'video_category',
            'video_tags', 'play_count', 'upload_time', 'video_duration',
            'video_coins'
        ]

        placeholder = '%s' if self.use_mysql else '?'
        set_clauses = []
        values = []

        for field, value in updates.items():
            if field in allowed_fields:
                set_clauses.append(f"{field} = {placeholder}")
                values.append(value)

        if not set_clauses:
            return False

        if not self.use_mysql:
            set_clauses.append(f"updated_at = {placeholder}")
            values.append(datetime.now().isoformat())

        values.append(video_id)

        try:
            cursor = self.connection.cursor()
            sql = f"UPDATE videos SET {', '.join(set_clauses)} WHERE video_id = {placeholder}"
            cursor.execute(sql, values)
            self.connection.commit()
            return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"更新视频失败: {e}")
            self._log(f"❌ 更新视频失败: {e}")
            return False

    def update_play_count(self, video_id: int,
                          increment: int = 1) -> bool:
        """
        增加视频播放数

        Args:
            video_id: 视频ID
            increment: 增加的数量，默认为1

        Returns:
            更新成功返回True
        """
        try:
            cursor = self.connection.cursor()
            placeholder = '%s' if self.use_mysql else '?'

            if self.use_mysql:
                cursor.execute(
                    f'UPDATE videos SET play_count = play_count + {placeholder} WHERE video_id = {placeholder}',
                    (increment, video_id)
                )
            else:
                cursor.execute(
                    f'UPDATE videos SET play_count = play_count + {placeholder}, updated_at = {placeholder} WHERE video_id = {placeholder}',
                    (increment, datetime.now().isoformat(), video_id)
                )
            self.connection.commit()
            return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"更新播放数失败: {e}")
            self._log(f"❌ 更新播放数失败: {e}")
            return False

    def delete_video(self, video_id: int) -> bool:
        """
        删除视频

        Args:
            video_id: 视频ID

        Returns:
            删除成功返回True
        """
        try:
            cursor = self.connection.cursor()
            placeholder = '%s' if self.use_mysql else '?'
            cursor.execute(f'DELETE FROM videos WHERE video_id = {placeholder}', (video_id,))
            self.connection.commit()
            return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"删除视频失败: {e}")
            self._log(f"❌ 删除视频失败: {e}")
            return False

    def delete_videos(self, video_ids: List[int]) -> int:
        """
        批量删除视频

        Args:
            video_ids: 视频ID列表

        Returns:
            成功删除的视频数量
        """
        # 归一化为去重后的整数列表, 过滤无效值
        ids: List[int] = []
        seen = set()
        for vid in video_ids or []:
            try:
                iv = int(vid)
            except (TypeError, ValueError):
                continue
            if iv not in seen:
                seen.add(iv)
                ids.append(iv)

        if not ids:
            return 0

        try:
            cursor = self.connection.cursor()
            placeholder = '%s' if self.use_mysql else '?'
            placeholders = ', '.join([placeholder] * len(ids))
            cursor.execute(
                f'DELETE FROM videos WHERE video_id IN ({placeholders})',
                ids
            )
            self.connection.commit()
            return cursor.rowcount
        except Exception as e:
            logger.error(f"批量删除视频失败: {e}")
            self._log(f"❌ 批量删除视频失败: {e}")
            return 0

    def get_categories(self) -> List[Dict[str, Any]]:
        """
        获取所有分类及其视频数量

        Returns:
            分类列表，包含分类名和视频数量
        """
        cursor = self.connection.cursor()
        cursor.execute('''
            SELECT video_category, COUNT(*) as video_count
            FROM videos
            GROUP BY video_category
            ORDER BY video_count DESC
        ''')
        rows = cursor.fetchall()
        return [dict(row) if isinstance(row, dict) else dict(row) for row in rows]

    def get_statistics(self) -> Dict[str, Any]:
        """
        获取数据库统计信息

        Returns:
            统计信息字典
        """
        cursor = self.connection.cursor()

        # 总视频数
        cursor.execute('SELECT COUNT(*) as cnt FROM videos')
        row = cursor.fetchone()
        total_videos = row['cnt'] if isinstance(row, dict) else row[0]

        # 总播放数
        cursor.execute('SELECT COALESCE(SUM(play_count), 0) as total FROM videos')
        row = cursor.fetchone()
        total_plays = row['total'] if isinstance(row, dict) else row[0]

        # 分类数
        cursor.execute('SELECT COUNT(DISTINCT video_category) as cnt FROM videos')
        row = cursor.fetchone()
        category_count = row['cnt'] if isinstance(row, dict) else row[0]

        # 平均播放数
        avg_plays = total_plays / total_videos if total_videos > 0 else 0

        return {
            'total_videos': total_videos,
            'total_plays': total_plays,
            'category_count': category_count,
            'total_categories': category_count,  # Alias for frontend compatibility
            'average_plays': round(avg_plays, 2)
        }

    # ==================== 导航分类管理 (Navigation Categories Management) ====================

    def get_nav_categories(self) -> List[Dict[str, Any]]:
        """
        获取所有导航分类配置 (Get all navigation categories)

        Returns:
            导航分类列表
        """
        cursor = self.connection.cursor()
        cursor.execute('''
            SELECT category_key, label, subcategories, sort_order
            FROM nav_categories
            ORDER BY sort_order ASC, id ASC
        ''')
        rows = cursor.fetchall()

        result = []
        for row in rows:
            row_dict = dict(row)
            # Parse subcategories from JSON string
            subcategories_str = row_dict.get('subcategories', '[]')
            try:
                subcategories = json.loads(subcategories_str) if subcategories_str else []
            except (json.JSONDecodeError, TypeError):
                subcategories = []

            result.append({
                'key': row_dict['category_key'],
                'label': row_dict['label'],
                'subcategories': subcategories
            })

        return result

    def save_nav_categories(self, categories: List[Dict[str, Any]]) -> bool:
        """
        保存导航分类配置 (Save navigation categories - replaces all)

        Args:
            categories: 导航分类列表 [{ key, label, subcategories }]

        Returns:
            成功返回True，失败返回False
        """
        try:
            cursor = self.connection.cursor()
            placeholder = '%s' if self.use_mysql else '?'

            # 删除所有现有分类 (Delete all existing categories)
            cursor.execute('DELETE FROM nav_categories')

            # 插入新的分类 (Insert new categories)
            for i, cat in enumerate(categories):
                subcategories_json = json.dumps(cat.get('subcategories', []), ensure_ascii=False)
                cursor.execute(
                    f'''INSERT INTO nav_categories (category_key, label, subcategories, sort_order)
                    VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder})''',
                    (cat['key'], cat['label'], subcategories_json, i))

            self.connection.commit()
            self._log(f"✅ 保存了 {len(categories)} 个导航分类")
            return True
        except Exception as e:
            logger.error(f"保存导航分类失败: {e}")
            return False

    # ==================== 轮播图管理 (Carousel Management) ====================

    def get_carousel_videos(self) -> List[Dict[str, Any]]:
        """
        获取首页轮播图条目列表 (Get home carousel items)

        返回管理员在后台手动配置的轮播图条目，按配置顺序排列。支持两种条目：
          - 视频条目 (item_type='video')：JOIN videos 表获取完整视频信息，
            已删除的视频会自动被排除。
          - 独立图片条目 (item_type='image')：直接使用配置的图片地址，
            与视频管理无关。
        如果管理员未配置轮播图，返回空列表（前端会显示占位样式）。

        Returns:
            条目列表，每个条目包含 item_type / video_id / video_image /
            video_title / video_category / link_url 等字段。
        """
        cursor = self.connection.cursor()
        cursor.execute('''
            SELECT c.id, c.item_type, c.video_id, c.image_url, c.title, c.link_url,
                   c.sort_order,
                   v.video_url, v.video_image, v.video_title, v.video_category
            FROM carousel_items c
            LEFT JOIN videos v ON c.video_id = v.video_id
            ORDER BY c.sort_order ASC, c.id ASC
        ''')
        rows = cursor.fetchall()

        items: List[Dict[str, Any]] = []
        for row in rows:
            row = dict(row)
            item_type = row.get('item_type') or 'video'
            if item_type == 'image':
                # 独立图片条目：必须配置了图片地址才展示
                if not row.get('image_url'):
                    continue
                items.append({
                    'item_type': 'image',
                    'video_id': None,
                    'video_image': row.get('image_url'),
                    'video_title': row.get('title') or '',
                    'video_category': '',
                    'link_url': row.get('link_url') or ''
                })
            else:
                # 视频条目：关联视频被删除时(LEFT JOIN 结果为空)自动跳过
                if not row.get('video_id') or row.get('video_url') is None:
                    continue
                items.append({
                    'item_type': 'video',
                    'video_id': row.get('video_id'),
                    'video_url': row.get('video_url'),
                    'video_image': row.get('video_image'),
                    'video_title': row.get('video_title') or '',
                    'video_category': row.get('video_category') or '',
                    'link_url': ''
                })
        return items

    def save_carousel_videos(self, video_ids: List[int]) -> bool:
        """
        保存首页轮播图配置（仅视频，向后兼容）

        Args:
            video_ids: 视频ID列表，按展示顺序排列

        Returns:
            成功返回True，失败返回False
        """
        items = [{'item_type': 'video', 'video_id': vid} for vid in video_ids]
        return self.save_carousel_items(items)

    def save_carousel_items(self, items: List[Dict[str, Any]]) -> bool:
        """
        保存首页轮播图配置 (Save carousel items - replaces all)

        Args:
            items: 轮播图条目列表，按展示顺序排列。每个条目为字典：
                - 视频条目: {'item_type': 'video', 'video_id': 1}
                - 图片条目: {'item_type': 'image', 'image_url': '...',
                            'title': '...', 'link_url': '...'}

        Returns:
            成功返回True，失败返回False
        """
        try:
            cursor = self.connection.cursor()
            placeholder = '%s' if self.use_mysql else '?'

            # 删除所有现有轮播图配置 (Delete all existing carousel items)
            cursor.execute('DELETE FROM carousel_items')

            # 按顺序插入新的轮播图条目 (Insert new carousel items in order)
            insert_sql = (
                'INSERT INTO carousel_items '
                '(item_type, video_id, image_url, title, link_url, sort_order) '
                f'VALUES ({placeholder}, {placeholder}, {placeholder}, '
                f'{placeholder}, {placeholder}, {placeholder})'
            )
            for i, item in enumerate(items):
                item_type = (item.get('item_type') or 'video').strip()
                if item_type == 'image':
                    image_url = (item.get('image_url') or '').strip()
                    if not image_url:
                        # 图片条目必须有图片地址，否则跳过
                        continue
                    cursor.execute(insert_sql, (
                        'image',
                        None,
                        image_url,
                        (item.get('title') or '').strip(),
                        (item.get('link_url') or '').strip(),
                        i
                    ))
                else:
                    video_id = item.get('video_id')
                    if video_id is None:
                        continue
                    cursor.execute(insert_sql, (
                        'video',
                        int(video_id),
                        None,
                        None,
                        None,
                        i
                    ))

            self.connection.commit()
            self._log(f"✅ 保存了 {len(items)} 个轮播图条目")
            return True
        except Exception as e:
            logger.error(f"保存轮播图配置失败: {e}")
            return False

    # ==================== 视频管理功能 (Video Management Features) ====================

    def get_category_stats(self) -> List[Dict[str, Any]]:
        """
        获取各分类视频统计 (Get video count statistics by category)

        Returns:
            分类统计列表，包含分类名、视频数量和示例图片
        """
        cursor = self.connection.cursor()
        
        if self.use_mysql:
            # MySQL: Use a subquery with ROW_NUMBER() or a correlated subquery
            # This approach uses a LEFT JOIN with a derived table that finds the latest video per category
            cursor.execute('''
                SELECT 
                    c.video_category,
                    c.video_count,
                    v.video_image as sample_image
                FROM (
                    SELECT video_category, COUNT(*) as video_count
                    FROM videos
                    WHERE video_category IS NOT NULL AND video_category != ''
                    GROUP BY video_category
                ) c
                LEFT JOIN videos v ON v.video_id = (
                    SELECT v2.video_id 
                    FROM videos v2 
                    WHERE v2.video_category = c.video_category 
                    AND v2.video_image IS NOT NULL 
                    AND v2.video_image != ''
                    ORDER BY v2.upload_time DESC 
                    LIMIT 1
                )
                ORDER BY c.video_count DESC
            ''')
        else:
            # SQLite: Similar approach with correlated subquery
            cursor.execute('''
                SELECT 
                    c.video_category,
                    c.video_count,
                    (
                        SELECT v.video_image 
                        FROM videos v 
                        WHERE v.video_category = c.video_category 
                        AND v.video_image IS NOT NULL 
                        AND v.video_image != ''
                        ORDER BY v.upload_time DESC 
                        LIMIT 1
                    ) as sample_image
                FROM (
                    SELECT video_category, COUNT(*) as video_count
                    FROM videos
                    WHERE video_category IS NOT NULL AND video_category != ''
                    GROUP BY video_category
                ) c
                ORDER BY c.video_count DESC
            ''')
        
        rows = cursor.fetchall()
        
        result = []
        for row in rows:
            row_dict = dict(row) if isinstance(row, dict) else dict(row)
            result.append({
                'video_category': row_dict['video_category'],
                'video_count': row_dict['video_count'],
                'sample_image': row_dict.get('sample_image') or ''
            })
        
        return result

    # SQL expression for normalizing video titles (removing spaces and common separators)
    # Used in find_duplicates to identify similar titles like "海绵宝宝" and "海绵宝 宝"
    TITLE_NORMALIZE_SQL = "REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(video_title, ' ', ''), '　', ''), '-', ''), '_', ''), '.', '')"

    def find_duplicates(self, check_type: str = 'title') -> List[Dict[str, Any]]:
        """
        查找重复视频 (Find duplicate videos by title or image)
        
        对于标题查重，会移除空格和特殊字符进行比较，
        例如 "海绵宝宝" 和 "海绵宝 宝" 会被识别为重复。

        Args:
            check_type: 'title' 按标题查找 (忽略空格), 'image' 按图片URL查找

        Returns:
            重复视频列表，每组包含重复的视频信息
        """
        cursor = self.connection.cursor()

        if check_type == 'title':
            # 查找标题重复的视频 (忽略空格和常见分隔符)
            # 使用 TITLE_NORMALIZE_SQL 移除空格、全角空格、以及常见的分隔符后进行比较
            # 这样 "海绵宝宝" 和 "海绵宝 宝" 会被识别为相同标题
            cursor.execute(f'''
                SELECT 
                    {self.TITLE_NORMALIZE_SQL} as normalized_title,
                    COUNT(*) as duplicate_count
                FROM videos
                WHERE video_title IS NOT NULL AND video_title != ''
                GROUP BY normalized_title
                HAVING COUNT(*) > 1
                ORDER BY duplicate_count DESC
                LIMIT 100
            ''')
            duplicate_groups = cursor.fetchall()

            result = []
            placeholder = '%s' if self.use_mysql else '?'
            
            for group in duplicate_groups:
                group_dict = dict(group) if isinstance(group, dict) else dict(group)
                normalized_title = group_dict['normalized_title']

                # 使用相同的规范化方式查找所有匹配的视频
                cursor.execute(
                    f'''SELECT video_id, video_title, video_image, video_category, upload_time 
                        FROM videos 
                        WHERE {self.TITLE_NORMALIZE_SQL} = {placeholder}''',
                    (normalized_title,)
                )
                videos = cursor.fetchall()
                
                # 使用第一个视频的原始标题作为显示值
                video_list = [dict(v) if isinstance(v, dict) else dict(v) for v in videos]
                display_title = video_list[0]['video_title'] if video_list else normalized_title
                
                result.append({
                    'duplicate_value': display_title,
                    'duplicate_type': 'title',
                    'count': group_dict['duplicate_count'],
                    'videos': video_list
                })

            return result

        else:  # check_type == 'image'
            # 查找图片URL重复的视频
            cursor.execute('''
                SELECT video_image, COUNT(*) as duplicate_count
                FROM videos
                WHERE video_image IS NOT NULL AND video_image != ''
                GROUP BY video_image
                HAVING COUNT(*) > 1
                ORDER BY duplicate_count DESC
                LIMIT 100
            ''')
            duplicate_groups = cursor.fetchall()

            result = []
            for group in duplicate_groups:
                group_dict = dict(group) if isinstance(group, dict) else dict(group)
                image = group_dict['video_image']
                placeholder = '%s' if self.use_mysql else '?'

                cursor.execute(
                    f'SELECT video_id, video_title, video_image, video_category, upload_time FROM videos WHERE video_image = {placeholder}',
                    (image,)
                )
                videos = cursor.fetchall()
                result.append({
                    'duplicate_value': image,
                    'duplicate_type': 'image',
                    'count': group_dict['duplicate_count'],
                    'videos': [dict(v) if isinstance(v, dict) else dict(v) for v in videos]
                })

            return result

    def get_next_video_id(self) -> int:
        """
        获取下一个可用的视频ID (Get next available video ID)
        
        使用时间戳和随机数组合生成唯一ID，避免并发竞争条件

        Returns:
            下一个视频ID (基于时间戳)
        """
        import random
        from datetime import datetime
        
        # 使用时间戳 + 随机数生成唯一ID
        # 格式: YYMMDDHHMM + 4位随机数 = 14位数字
        timestamp = datetime.now().strftime('%y%m%d%H%M')
        random_suffix = random.randint(1000, 9999)
        video_id = int(f"{timestamp}{random_suffix}")
        
        return video_id

    def get_collection_status(self, hours: int = 24) -> Dict[str, Any]:
        """
        获取采集状态统计 (Get collection status statistics)

        Args:
            hours: 统计多少小时内的采集数据

        Returns:
            采集状态统计信息
        """
        cursor = self.connection.cursor()

        # 总视频数
        cursor.execute('SELECT COUNT(*) as cnt FROM videos')
        row = cursor.fetchone()
        total_videos = row['cnt'] if isinstance(row, dict) else row[0]

        # 分类统计
        cursor.execute('''
            SELECT COUNT(DISTINCT video_category) as cnt FROM videos
            WHERE video_category IS NOT NULL AND video_category != ''
        ''')
        row = cursor.fetchone()
        total_categories = row['cnt'] if isinstance(row, dict) else row[0]

        # 最新采集时间 (基于created_at或upload_time)
        cursor.execute('''
            SELECT MAX(created_at) as latest FROM videos
        ''')
        row = cursor.fetchone()
        latest_collection = row['latest'] if isinstance(row, dict) else row[0]

        # 按分类统计视频数量
        category_stats = self.get_category_stats()

        return {
            'total_videos': total_videos,
            'total_categories': total_categories,
            'latest_collection_time': latest_collection,
            'category_breakdown': category_stats[:10],  # Top 10 categories
            'hours_checked': hours
        }

    def close(self) -> None:
        """关闭数据库连接"""
        if self.connection:
            self.connection.close()
            self.connection = None
            self._log("📁 数据库连接已关闭")

    def __del__(self):
        """析构函数，确保连接被关闭"""
        self.close()

    def __enter__(self):
        """支持with语句"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """退出时自动关闭连接"""
        self.close()


def import_from_collector(collector_data: List[Dict[str, Any]],
                          db: VideoDatabase) -> int:
    """
    从采集器数据导入到数据库

    Args:
        collector_data: 采集器收集的视频数据列表
        db: 数据库实例

    Returns:
        成功导入的数量
    """
    videos_to_insert = []
    skipped_count = 0

    for video in collector_data:
        # 验证必需字段
        vod_id = video.get('vod_id')
        vod_name = video.get('vod_name', '')
        vod_play_url = video.get('vod_play_url', '')

        if not vod_id or not vod_name:
            skipped_count += 1
            logger.warning(f"跳过无效视频记录: 缺少必需字段 (vod_id={vod_id}, vod_name={vod_name})")
            continue

        # 映射采集器字段到数据库字段
        db_video = {
            'video_id': vod_id,
            'video_url': vod_play_url,
            'video_image': video.get('vod_pic', ''),
            'video_title': vod_name,
            'video_category': video.get('type_name', ''),
            'play_count': video.get('vod_hits', 0),
            'upload_time': video.get('vod_time', ''),
            'video_duration': video.get('vod_duration', video.get('vod_remarks', '')),
            'video_coins': 0  # 默认金币为0
        }
        videos_to_insert.append(db_video)

    if skipped_count > 0:
        logger.info(f"跳过 {skipped_count} 个无效视频记录")

    return db.insert_videos(videos_to_insert)


def parse_spjs_file(file_path: str) -> List[Dict[str, Any]]:
    """
    解析sp.js文件，提取视频数据

    sp.js文件格式通常为JavaScript变量赋值，包含视频数组
    例如: var videoList = [{...}, {...}];

    Args:
        file_path: sp.js文件路径

    Returns:
        视频数据列表
    """
    if not os.path.exists(file_path):
        logger.error(f"文件不存在: {file_path}")
        print(f"❌ 文件不存在: {file_path}")
        return []

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 尝试提取JSON数组
        # 方法1: 查找 var xxx = [...] 或 let xxx = [...] 或 const xxx = [...]
        array_match = re.search(r'(?:var|let|const)\s+\w+\s*=\s*(\[[\s\S]*?\]);?\s*$', content, re.MULTILINE)
        if array_match:
            json_str = array_match.group(1)
            # 清理JavaScript特有的语法
            json_str = re.sub(r',\s*([}\]])', r'\1', json_str)  # 移除尾随逗号
            videos = json.loads(json_str)
            print(f"✅ 从sp.js解析到 {len(videos)} 个视频 (变量赋值格式)")
            return videos

        # 方法2: 直接尝试作为JSON解析
        try:
            videos = json.loads(content)
            if isinstance(videos, list):
                print(f"✅ 从sp.js解析到 {len(videos)} 个视频 (JSON数组格式)")
                return videos
            elif isinstance(videos, dict) and 'data' in videos:
                videos = videos['data']
                print(f"✅ 从sp.js解析到 {len(videos)} 个视频 (JSON对象格式)")
                return videos if isinstance(videos, list) else []
        except json.JSONDecodeError:
            pass

        # 方法3: 查找JSON数组部分
        bracket_match = re.search(r'\[[\s\S]*\]', content)
        if bracket_match:
            json_str = bracket_match.group(0)
            json_str = re.sub(r',\s*([}\]])', r'\1', json_str)
            videos = json.loads(json_str)
            print(f"✅ 从sp.js解析到 {len(videos)} 个视频 (提取JSON数组)")
            return videos

        print("❌ 无法解析sp.js文件格式")
        return []

    except json.JSONDecodeError as e:
        logger.error(f"JSON解析失败: {e}")
        print(f"❌ JSON解析失败: {e}")
        return []
    except Exception as e:
        logger.error(f"读取文件失败: {e}")
        print(f"❌ 读取文件失败: {e}")
        return []


def import_from_spjs(file_path: str, db: VideoDatabase) -> int:
    """
    从sp.js文件导入视频数据到数据库

    Args:
        file_path: sp.js文件路径
        db: 数据库实例

    Returns:
        成功导入的数量
    """
    videos = parse_spjs_file(file_path)

    if not videos:
        print("⚠️ 没有找到可导入的视频数据")
        return 0

    videos_to_insert = []
    skipped_count = 0

    def get_first_value(*keys, default=None, source=None):
        """从字典中获取第一个存在的键值"""
        for key in keys:
            val = source.get(key)
            if val is not None:
                return val
        return default

    for video in videos:
        # 尝试多种字段名映射
        video_id = get_first_value('video_id', 'vod_id', 'id', source=video)
        video_title = get_first_value('video_title', 'vod_name', 'title', 'name', source=video)
        video_url = get_first_value('video_url', 'vod_play_url', 'url', 'play_url', default='', source=video)

        if not video_id or not video_title:
            skipped_count += 1
            continue

        db_video = {
            'video_id': video_id,
            'video_url': video_url,
            'video_image': get_first_value('video_image', 'vod_pic', 'pic', 'thumb', default='', source=video),
            'video_title': video_title,
            'video_category': get_first_value('video_category', 'type_name', 'category', default='', source=video),
            'play_count': get_first_value('play_count', 'vod_hits', 'hits', default=0, source=video),
            'upload_time': get_first_value('upload_time', 'vod_time', 'time', default='', source=video),
            'video_duration': get_first_value('video_duration', 'vod_duration', 'duration', 'vod_remarks', default='', source=video),
            'video_coins': get_first_value('video_coins', 'coins', 'gold', default=0, source=video)
        }
        videos_to_insert.append(db_video)

    if skipped_count > 0:
        print(f"⏭️ 跳过 {skipped_count} 个无效视频记录")

    return db.insert_videos(videos_to_insert)


# 命令行测试
if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='视频数据库管理工具 - 支持MySQL和SQLite')
    parser.add_argument('--mysql', action='store_true', default=True,
                        help='使用MySQL数据库 (默认)')
    parser.add_argument('--sqlite', action='store_true',
                        help='使用SQLite数据库')
    parser.add_argument('--db', type=str, default='videos.db',
                        help='SQLite数据库文件路径')
    parser.add_argument('--import-spjs', type=str, default=None, metavar='FILE',
                        help='从sp.js文件导入视频数据')
    parser.add_argument('--stats', action='store_true',
                        help='显示统计信息')
    parser.add_argument('--categories', action='store_true',
                        help='显示所有分类')
    parser.add_argument('--list', type=int, default=None,
                        help='列出指定数量的视频')
    parser.add_argument('--search', type=str, default=None,
                        help='搜索视频标题')
    parser.add_argument('--top', type=int, default=None,
                        help='显示播放量最高的N个视频')

    args = parser.parse_args()

    # 确定使用MySQL还是SQLite
    use_mysql = not args.sqlite

    print("\n" + "=" * 60)
    print("🎬 视频数据库管理工具 v2.0")
    print("=" * 60)

    if use_mysql and MYSQL_AVAILABLE:
        print("📡 数据库类型: MySQL")
        print(f"   主机: {MYSQL_CONFIG['host']}:{MYSQL_CONFIG['port']}")
        print(f"   数据库: {MYSQL_CONFIG['database']}")
    else:
        print(f"📡 数据库类型: SQLite ({args.db})")

    with VideoDatabase(use_mysql=use_mysql, db_path=args.db) as db:
        # 导入sp.js文件
        if args.import_spjs:
            print(f"\n📥 正在从 {args.import_spjs} 导入视频数据...")
            count = import_from_spjs(args.import_spjs, db)
            print(f"✅ 成功导入 {count} 个视频到数据库")

        if args.stats:
            stats = db.get_statistics()
            print("\n📊 数据库统计信息:")
            print(f"  总视频数: {stats['total_videos']}")
            print(f"  总播放数: {stats['total_plays']}")
            print(f"  分类数量: {stats['category_count']}")
            print(f"  平均播放: {stats['average_plays']}")

        if args.categories:
            categories = db.get_categories()
            print("\n📂 视频分类:")
            for cat in categories:
                print(f"  - {cat['video_category']}: {cat['video_count']} 个视频")

        if args.list:
            videos = db.get_all_videos(limit=args.list)
            print(f"\n📺 视频列表 (共 {len(videos)} 个):")
            for v in videos:
                print(f"  [{v['video_id']}] {v['video_title']} - {v['video_category']}")

        if args.search:
            results = db.search_videos(args.search)
            print(f"\n🔍 搜索 '{args.search}' 结果 (共 {len(results)} 个):")
            for v in results:
                print(f"  [{v['video_id']}] {v['video_title']}")

        if args.top:
            top_videos = db.get_top_videos(limit=args.top)
            print(f"\n🔥 播放量TOP{args.top}:")
            for i, v in enumerate(top_videos, 1):
                print(f"  {i}. [{v['play_count']}播放] {v['video_title']}")
