#!/usr/bin/env python3
"""
YouTube视频解析器
解析YouTube视频链接，获取视频信息和下载链接
"""

import os
from typing import Dict
from .base_parser import BaseParser

class YouTubeParser(BaseParser):
    """YouTube视频解析器"""
    
    def __init__(self):
        """初始化YouTube解析器"""
        super().__init__("youtube")
        
        # 从环境变量读取配置
        self.use_yt_dlp = os.getenv("USE_YT_DLP", "false").lower() == "true"
        
        if self.use_yt_dlp:
            try:
                import yt_dlp
                self.yt_dlp = yt_dlp
                self.logger.info("yt-dlp已加载")
            except ImportError:
                self.logger.warning("yt-dlp未安装，将使用基础解析")
                self.yt_dlp = None
        else:
            self.yt_dlp = None
    
    def parse_link(self, url: str, platform_id: str) -> Dict:
        """
        解析YouTube链接
        :param url: YouTube视频链接
        :param platform_id: 视频ID
        :return: 解析结果
        """
        try:
            self.logger.info(f"开始解析YouTube链接: {url}")
            
            # 验证URL
            if not self.validate_url(url):
                return {
                    "success": False,
                    "error": "无效的YouTube链接",
                    "url": url
                }
            
            # 获取视频信息
            video_info = self.get_video_info(url, platform_id)
            if not video_info.get("success"):
                return video_info
            
            # 获取下载链接
            download_info = self.get_download_urls(url, platform_id)
            if not download_info.get("success"):
                return download_info
            
            return {
                "success": True,
                "url": url,
                "platform_id": platform_id,
                "title": video_info.get("title"),
                "duration": video_info.get("duration"),
                "thumbnail": video_info.get("thumbnail"),
                "download_urls": download_info.get("download_urls", []),
                "platform": "youtube"
            }
            
        except Exception as e:
            self.logger.error(f"YouTube链接解析失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "url": url
            }
    
    def get_video_info(self, url: str, platform_id: str) -> Dict:
        """
        获取YouTube视频信息
        :param url: YouTube视频链接
        :param platform_id: 视频ID
        :return: 视频信息
        """
        try:
            if self.yt_dlp:
                # 使用yt-dlp获取信息
                ydl_opts = {
                    'quiet': True,
                    'no_warnings': True,
                    'extract_flat': False
                }
                
                with self.yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=False)
                    
                    return {
                        "success": True,
                        "title": info.get("title", ""),
                        "duration": info.get("duration", 0),
                        "thumbnail": info.get("thumbnail", ""),
                        "formats": info.get("formats", []),
                        "platform": "youtube"
                    }
            else:
                # 基础解析（需要实现）
                return {
                    "success": False,
                    "error": "YouTube解析功能需要安装yt-dlp或实现基础解析",
                    "url": url
                }
                
        except Exception as e:
            self.logger.error(f"获取YouTube视频信息失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "url": url
            } 