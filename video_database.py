#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
视频数据库模块 (Video Database Module)
======================================
基于SQLite的视频信息存储系统

数据表结构:
- video_id: 视频ID (主键)
- video_url: 视频链接
- video_image: 视频图片/封面
- video_title: 视频标题
- video_category: 视频分类
- play_count: 播放数
- upload_time: 上传时间
- video_duration: 视频时长
- video_price: 视频价格

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
        'video_price': 0.00
    })

作者: Auto-generated
日期: 2026-01-30
"""

import sqlite3
import os
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any, Union

# 配置日志
logger = logging.getLogger(__name__)


class VideoDatabase:
    """
    视频数据库管理类
    
    注意：建议使用上下文管理器 (with语句) 来确保数据库连接正确关闭，
    或手动调用 close() 方法。
    """
    
    DEFAULT_DB_NAME = "videos.db"
    
    def __init__(self, db_path: Optional[str] = None, verbose: bool = True):
        """
        初始化数据库连接
        
        Args:
            db_path: 数据库文件路径，默认为当前目录下的 videos.db
            verbose: 是否输出日志信息，默认True
        """
        self.db_path = db_path or self.DEFAULT_DB_NAME
        self.verbose = verbose
        self.connection: Optional[sqlite3.Connection] = None
        self._init_database()
    
    def _init_database(self) -> None:
        """初始化数据库，创建表结构"""
        self.connection = sqlite3.connect(self.db_path)
        self.connection.row_factory = sqlite3.Row  # 支持通过列名访问
        
        cursor = self.connection.cursor()
        
        # 创建视频表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS videos (
                video_id INTEGER PRIMARY KEY,
                video_url TEXT NOT NULL,
                video_image TEXT,
                video_title TEXT NOT NULL,
                video_category TEXT,
                play_count INTEGER DEFAULT 0,
                upload_time TEXT,
                video_duration TEXT,
                video_price REAL DEFAULT 0.0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
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
        
        self.connection.commit()
        self._log(f"✅ 数据库初始化完成: {self.db_path}")
    
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
                - play_count: 播放数
                - upload_time: 上传时间
                - video_duration: 视频时长
                - video_price: 视频价格
                
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
            # 使用 INSERT OR REPLACE 实现更新或插入功能
            # 注意：这会替换整行数据，包括 created_at 时间戳
            cursor.execute('''
                INSERT OR REPLACE INTO videos 
                (video_id, video_url, video_image, video_title, video_category, 
                 play_count, upload_time, video_duration, video_price, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                video_data.get('video_id'),
                video_data.get('video_url'),
                video_data.get('video_image', ''),
                video_data.get('video_title'),
                video_data.get('video_category', ''),
                video_data.get('play_count', 0),
                video_data.get('upload_time', ''),
                video_data.get('video_duration', ''),
                video_data.get('video_price', 0.0),
                datetime.now().isoformat()
            ))
            self.connection.commit()
            return True
        except sqlite3.Error as e:
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
        cursor.execute('SELECT * FROM videos WHERE video_id = ?', (video_id,))
        row = cursor.fetchone()
        
        if row:
            return dict(row)
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
        
        if limit:
            cursor.execute(
                'SELECT * FROM videos ORDER BY upload_time DESC LIMIT ? OFFSET ?',
                (limit, offset)
            )
        else:
            cursor.execute('SELECT * FROM videos ORDER BY upload_time DESC')
        
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    
    def get_videos_by_category(self, category: str, 
                               limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        按分类获取视频
        
        Args:
            category: 视频分类
            limit: 限制返回数量
            
        Returns:
            视频列表
        """
        cursor = self.connection.cursor()
        
        if limit:
            cursor.execute(
                'SELECT * FROM videos WHERE video_category = ? ORDER BY upload_time DESC LIMIT ?',
                (category, limit)
            )
        else:
            cursor.execute(
                'SELECT * FROM videos WHERE video_category = ? ORDER BY upload_time DESC',
                (category,)
            )
        
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    
    def search_videos(self, keyword: str, 
                      limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        搜索视频标题
        
        Args:
            keyword: 搜索关键词
            limit: 限制返回数量
            
        Returns:
            匹配的视频列表
        """
        cursor = self.connection.cursor()
        search_pattern = f"%{keyword}%"
        
        if limit:
            cursor.execute(
                'SELECT * FROM videos WHERE video_title LIKE ? ORDER BY play_count DESC LIMIT ?',
                (search_pattern, limit)
            )
        else:
            cursor.execute(
                'SELECT * FROM videos WHERE video_title LIKE ? ORDER BY play_count DESC',
                (search_pattern,)
            )
        
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    
    def get_top_videos(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        获取播放量最高的视频
        
        Args:
            limit: 返回数量
            
        Returns:
            视频列表
        """
        cursor = self.connection.cursor()
        cursor.execute(
            'SELECT * FROM videos ORDER BY play_count DESC LIMIT ?',
            (limit,)
        )
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    
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
            'video_url', 'video_image', 'video_title', 'video_category',
            'play_count', 'upload_time', 'video_duration', 'video_price'
        ]
        
        set_clauses = []
        values = []
        
        for field, value in updates.items():
            if field in allowed_fields:
                set_clauses.append(f"{field} = ?")
                values.append(value)
        
        if not set_clauses:
            return False
        
        set_clauses.append("updated_at = ?")
        values.append(datetime.now().isoformat())
        values.append(video_id)
        
        try:
            cursor = self.connection.cursor()
            sql = f"UPDATE videos SET {', '.join(set_clauses)} WHERE video_id = ?"
            cursor.execute(sql, values)
            self.connection.commit()
            return cursor.rowcount > 0
        except sqlite3.Error as e:
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
            cursor.execute(
                'UPDATE videos SET play_count = play_count + ?, updated_at = ? WHERE video_id = ?',
                (increment, datetime.now().isoformat(), video_id)
            )
            self.connection.commit()
            return cursor.rowcount > 0
        except sqlite3.Error as e:
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
            cursor.execute('DELETE FROM videos WHERE video_id = ?', (video_id,))
            self.connection.commit()
            return cursor.rowcount > 0
        except sqlite3.Error as e:
            logger.error(f"删除视频失败: {e}")
            self._log(f"❌ 删除视频失败: {e}")
            return False
    
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
        return [dict(row) for row in rows]
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        获取数据库统计信息
        
        Returns:
            统计信息字典
        """
        cursor = self.connection.cursor()
        
        # 总视频数
        cursor.execute('SELECT COUNT(*) FROM videos')
        total_videos = cursor.fetchone()[0]
        
        # 总播放数
        cursor.execute('SELECT SUM(play_count) FROM videos')
        total_plays = cursor.fetchone()[0] or 0
        
        # 分类数
        cursor.execute('SELECT COUNT(DISTINCT video_category) FROM videos')
        category_count = cursor.fetchone()[0]
        
        # 平均播放数
        avg_plays = total_plays / total_videos if total_videos > 0 else 0
        
        return {
            'total_videos': total_videos,
            'total_plays': total_plays,
            'category_count': category_count,
            'average_plays': round(avg_plays, 2)
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
            'video_price': 0.0  # 默认价格为0
        }
        videos_to_insert.append(db_video)
    
    if skipped_count > 0:
        logger.info(f"跳过 {skipped_count} 个无效视频记录")
    
    return db.insert_videos(videos_to_insert)


# 命令行测试
if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='视频数据库管理工具')
    parser.add_argument('--db', type=str, default='videos.db', 
                        help='数据库文件路径')
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
    
    with VideoDatabase(args.db) as db:
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
