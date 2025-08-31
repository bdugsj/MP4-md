#!/usr/bin/env python3
"""
解析器基类
定义所有平台解析器的通用接口
"""

import os
import logging
from abc import ABC, abstractmethod
from typing import Dict, Optional
from dotenv import load_dotenv

class BaseParser(ABC):
    """解析器基类"""
    
    def __init__(self, platform_name: str):
        """
        初始化解析器
        :param platform_name: 平台名称
        """
        # 加载配置
        config_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'config.env')
        load_dotenv(config_path)
        
        # 设置日志
        log_dir = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'logs')
        os.makedirs(log_dir, exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format=f'%(asctime)s - {platform_name.upper()}_PARSER - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(os.path.join(log_dir, f'{platform_name}_parser.log'), encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        
        self.logger = logging.getLogger(f'{platform_name}_parser')
        self.platform_name = platform_name
        
        self.logger.info(f"{platform_name}解析器已初始化")
    
    @abstractmethod
    def parse_link(self, url: str, platform_id: str) -> Dict:
        """
        解析链接
        :param url: 原始链接
        :param platform_id: 平台ID
        :return: 解析结果
        """
        pass
    
    @abstractmethod
    def get_video_info(self, url: str, platform_id: str) -> Dict:
        """
        获取视频信息
        :param url: 原始链接
        :param platform_id: 平台ID
        :return: 视频信息
        """
        pass
    
    def validate_url(self, url: str) -> bool:
        """
        验证URL格式
        :param url: 要验证的URL
        :return: 是否有效
        """
        return url.startswith('http') and self.platform_name in url.lower()
    
    def get_download_urls(self, url: str, platform_id: str) -> Dict:
        """
        获取下载链接
        :param url: 原始链接
        :param platform_id: 平台ID
        :return: 下载链接列表
        """
        try:
            video_info = self.get_video_info(url, platform_id)
            if not video_info.get("success"):
                return video_info
            
            # 提取下载链接
            download_urls = []
            if "formats" in video_info:
                for format_info in video_info["formats"]:
                    if "url" in format_info:
                        download_urls.append({
                            "url": format_info["url"],
                            "format": format_info.get("format", "unknown"),
                            "quality": format_info.get("quality", "unknown"),
                            "size": format_info.get("filesize", 0)
                        })
            
            return {
                "success": True,
                "download_urls": download_urls,
                "title": video_info.get("title"),
                "duration": video_info.get("duration"),
                "thumbnail": video_info.get("thumbnail")
            }
            
        except Exception as e:
            self.logger.error(f"获取下载链接失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "download_urls": []
            } 