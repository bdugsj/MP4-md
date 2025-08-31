#!/usr/bin/env python3
"""
视频下载器主模块
协调解析器和下载器完成视频下载
"""

import os
import logging
from typing import Dict, Optional
from dotenv import load_dotenv
import re
import time

# 导入解析器和下载器
from .parsers.bilibili_parser import BilibiliParser
from .parsers.youtube_parser import YouTubeParser
from .parsers.vimeo_parser import VimeoParser
from .parsers.generic_parser import GenericParser
from .downloaders.direct_downloader import DirectDownloader

class VideoDownloader:
    """视频下载器主模块"""
    
    def __init__(self):
        """初始化视频下载器"""
        # 加载配置
        config_path = os.path.join(os.path.dirname(__file__), '..', '..', 'config.env')
        load_dotenv(config_path)
        
        # 设置日志
        log_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'logs')
        os.makedirs(log_dir, exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - VIDEO_DOWNLOADER - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(os.path.join(log_dir, 'video_downloader.log'), encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        
        self.logger = logging.getLogger('VideoDownloader')
        
        # 初始化各个解析器
        self.parsers = {
            "bilibili": BilibiliParser(),
            "youtube": YouTubeParser(),
            "vimeo": VimeoParser(),
            "generic": GenericParser()
        }
        
        # 初始化下载器
        self.downloader = DirectDownloader()
        
        self.logger.info("视频下载器已初始化")
    
    def download_video(self, url: str, platform: str = None) -> Dict:
        """
        下载视频
        :param url: 视频链接
        :param platform: 平台名称（可选，自动检测）
        :return: 下载结果
        """
        try:
            self.logger.info(f"开始下载视频: {url}")
            self.logger.info(f"指定平台: {platform}")
            
            # 如果没有指定平台，自动检测
            if not platform:
                platform = self._detect_platform(url)
                self.logger.info(f"自动检测平台: {platform}")
            
            # 如果是直链，直接下载
            if platform in ["direct_video", "direct_audio"]:
                self.logger.info(f"检测到直链，直接下载: {url}")
                # 从URL中提取文件名
                filename = self._extract_filename_from_url(url)
                download_result = self.downloader.download_file(url, filename)
                
                if download_result.get("success"):
                    return {
                        "success": True,
                        "file_path": download_result["file_path"],
                        "filename": download_result["filename"],
                        "size": download_result["size"],
                        "title": filename,
                        "duration": None,
                        "platform": platform,
                        "url": url
                    }
                else:
                    return download_result
            
            # 获取对应的解析器
            parser = self.parsers.get(platform)
            if not parser:
                return {
                    "success": False,
                    "error": f"不支持的平台: {platform}",
                    "url": url
                }
            
            # 解析链接
            self.logger.info(f"使用{platform}解析器解析链接")
            # 对于B站链接，提取platform_id
            platform_id = None
            if platform == "bilibili" and "bilibili.com/video/" in url:
                platform_id = url.split("/video/")[-1].split("?")[0]
            parse_result = parser.parse_link(url, platform_id)
            
            if not parse_result.get("success"):
                return parse_result
            
            # 获取下载链接
            download_urls = parse_result.get("download_urls", [])
            if not download_urls:
                return {
                    "success": False,
                    "error": "未找到可下载的链接",
                    "url": url
                }
            
            # 选择最佳下载链接
            best_url = self._select_best_download_url(download_urls)
            
            # 下载文件
            filename = self._generate_safe_filename(parse_result.get('title', 'video'))
            download_result = self.downloader.download_file(best_url, filename)
            
            if download_result.get("success"):
                return {
                    "success": True,
                    "file_path": download_result["file_path"],
                    "filename": download_result["filename"],
                    "size": download_result["size"],
                    "title": parse_result.get("title"),
                    "duration": parse_result.get("duration"),
                    "platform": platform,
                    "url": url
                }
            else:
                return download_result
                
        except Exception as e:
            self.logger.error(f"视频下载失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "url": url
            }
    
    def _extract_filename_from_url(self, url: str) -> str:
        """从URL中提取文件名"""
        try:
            # 移除查询参数
            clean_url = url.split('?')[0]
            # 获取路径的最后一部分
            filename = clean_url.split('/')[-1]
            
            # 如果没有扩展名，添加默认扩展名
            if '.' not in filename:
                if 'bilivideo.com' in url:
                    filename += '.mp4'  # B站直链默认是mp4
                else:
                    filename += '.mp4'  # 其他情况默认mp4
            
            # 清理文件名中的特殊字符
            filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
            
            return filename
        except Exception as e:
            self.logger.warning(f"提取文件名失败: {e}")
            return f"video_{int(time.time())}.mp4"
    
    def _generate_safe_filename(self, title: str, extension: str = ".mp4") -> str:
        """生成安全的文件名"""
        try:
            # 清理标题中的特殊字符
            safe_title = re.sub(r'[<>:"/\\|?*]', '_', title)
            # 限制长度
            if len(safe_title) > 100:
                safe_title = safe_title[:100]
            # 添加时间戳确保唯一性
            timestamp = int(time.time())
            return f"{safe_title}_{timestamp}{extension}"
        except Exception as e:
            self.logger.warning(f"生成安全文件名失败: {e}")
            return f"video_{int(time.time())}{extension}"
    
    def _detect_platform(self, url: str) -> str:
        """检测链接平台"""
        for platform, parser in self.parsers.items():
            if parser.validate_url(url):
                return platform
        
        return "generic"
    
    def _select_best_download_url(self, download_urls: list) -> str:
        """选择最佳下载链接"""
        if not download_urls:
            return ""
        
        # 优先选择高质量、小文件的链接
        best_url = download_urls[0]["url"]
        best_score = 0
        
        for url_info in download_urls:
            score = 0
            
            # 质量评分
            quality = url_info.get("quality", "unknown").lower()
            if "1080" in quality or "hd" in quality:
                score += 3
            elif "720" in quality:
                score += 2
            elif "480" in quality:
                score += 1
            
            # 格式评分
            format_type = url_info.get("format", "unknown").lower()
            if format_type in ["mp4", "webm"]:
                score += 2
            elif format_type == "direct":
                score += 1
            
            # 文件大小评分（越小越好）
            size = url_info.get("size", 0)
            if size > 0:
                size_mb = size / (1024 * 1024)
                if size_mb < 100:  # 小于100MB
                    score += 2
                elif size_mb < 500:  # 小于500MB
                    score += 1
            
            if score > best_score:
                best_score = score
                best_url = url_info["url"]
        
        return best_url
    
    def get_download_status(self, url: str) -> Dict:
        """
        获取下载状态
        :param url: 视频链接
        :return: 下载状态
        """
        return self.downloader.get_download_progress(url) 