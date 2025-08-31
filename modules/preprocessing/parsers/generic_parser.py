#!/usr/bin/env python3
"""
通用解析器
处理未知类型的链接或直链
"""

import os
import re
from typing import Dict
from .base_parser import BaseParser

class GenericParser(BaseParser):
    """通用解析器"""
    
    def __init__(self):
        """初始化通用解析器"""
        super().__init__("generic")
    
    def parse_link(self, url: str, platform_id: str = None) -> Dict:
        """
        解析通用链接
        :param url: 链接URL
        :param platform_id: 平台ID（可选）
        :return: 解析结果
        """
        try:
            self.logger.info(f"开始解析通用链接: {url}")
            
            # 检查是否为直链
            if self._is_direct_link(url):
                return {
                    "success": True,
                    "url": url,
                    "platform_id": platform_id,
                    "title": self._extract_filename(url),
                    "duration": 0,
                    "thumbnail": "",
                    "download_urls": [{"url": url, "format": "direct", "quality": "unknown", "size": 0}],
                    "platform": "direct"
                }
            
            # 尝试识别平台
            platform = self._identify_platform(url)
            if platform != "unknown":
                return {
                    "success": False,
                    "error": f"链接类型为{platform}，请使用对应的专用解析器",
                    "url": url,
                    "suggested_parser": f"{platform}_parser"
                }
            
            return {
                "success": False,
                "error": "无法识别的链接类型",
                "url": url
            }
            
        except Exception as e:
            self.logger.error(f"通用链接解析失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "url": url
            }
    
    def get_video_info(self, url: str, platform_id: str = None) -> Dict:
        """
        获取通用链接信息
        :param url: 链接URL
        :param platform_id: 平台ID（可选）
        :return: 链接信息
        """
        try:
            if self._is_direct_link(url):
                return {
                    "success": True,
                    "title": self._extract_filename(url),
                    "duration": 0,
                    "thumbnail": "",
                    "formats": [{"url": url, "format": "direct"}],
                    "platform": "direct"
                }
            
            return {
                "success": False,
                "error": "无法获取非直链的信息",
                "url": url
            }
                
        except Exception as e:
            self.logger.error(f"获取通用链接信息失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "url": url
            }
    
    def _is_direct_link(self, url: str) -> bool:
        """检查是否为直链"""
        # 检查是否为媒体文件直链
        media_extensions = r'\.(mp4|avi|mov|mkv|wmv|flv|webm|m4v|mp3|wav|m4a|aac|flac|ogg)(\?.*)?$'
        return bool(re.search(media_extensions, url, re.IGNORECASE))
    
    def _extract_filename(self, url: str) -> str:
        """从URL中提取文件名"""
        # 移除查询参数
        clean_url = url.split('?')[0]
        # 获取文件名
        filename = clean_url.split('/')[-1]
        return filename if filename else "unknown_file"
    
    def _identify_platform(self, url: str) -> str:
        """识别链接平台"""
        platform_patterns = {
            "bilibili": r'bilibili\.com|b23\.tv',
            "youtube": r'youtube\.com|youtu\.be',
            "vimeo": r'vimeo\.com',
            "douyin": r'douyin\.com',
            "kuaishou": r'kuaishou\.com'
        }
        
        for platform, pattern in platform_patterns.items():
            if re.search(pattern, url, re.IGNORECASE):
                return platform
        
        return "unknown" 