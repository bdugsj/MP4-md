#!/usr/bin/env python3
"""
链接分类器
识别用户输入中的链接类型，并决定使用哪个解析器
"""

import os
import re
import logging
from typing import Dict, Optional, Tuple
from dotenv import load_dotenv

class LinkClassifier:
    """链接分类器"""
    
    def __init__(self):
        """初始化链接分类器"""
        # 加载配置
        config_path = os.path.join(os.path.dirname(__file__), '..', '..', 'config.env')
        load_dotenv(config_path)
        
        # 设置日志
        log_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'logs')
        os.makedirs(log_dir, exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - LINK_CLASSIFIER - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(os.path.join(log_dir, 'link_classifier.log'), encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        
        self.logger = logging.getLogger('LinkClassifier')
        
        # 定义链接模式
        self.link_patterns = {
            "bilibili": [
                r'https?://(?:www\.)?bilibili\.com/video/([A-Za-z0-9]+)',
                r'https?://b23\.tv/([A-Za-z0-9]+)',
                r'https?://(?:www\.)?bilibili\.com/bangumi/play/([A-Za-z0-9]+)',
                r'https?://(?:www\.)?bilibili\.com/medialist/play/([A-Za-z0-9]+)',
                r'https?://(?:www\.)?bilibili\.com/cheese/play/([A-Za-z0-9]+)'
            ],
            "youtube": [
                r'https?://(?:www\.)?youtube\.com/watch\?v=([A-Za-z0-9_-]+)',
                r'https?://youtu\.be/([A-Za-z0-9_-]+)',
                r'https?://(?:www\.)?youtube\.com/embed/([A-Za-z0-9_-]+)'
            ],
            "vimeo": [
                r'https?://(?:www\.)?vimeo\.com/(\d+)',
                r'https?://player\.vimeo\.com/video/(\d+)'
            ],
            "douyin": [
                r'https?://(?:www\.)?douyin\.com/video/([A-Za-z0-9]+)',
                r'https?://v\.douyin\.com/([A-Za-z0-9]+)'
            ],
            "kuaishou": [
                r'https?://(?:www\.)?kuaishou\.com/short-video/([A-Za-z0-9]+)',
                r'https?://v\.kuaishou\.com/([A-Za-z0-9]+)'
            ],
            "direct_video": [
                # 视频文件扩展名
                r'.*\.(mp4|avi|mov|mkv|wmv|flv|webm|m4v)(\?.*)?$',
                # B站视频直链（CDN域名）
                r'https?://[^/]*bilivideo\.com/.*\.(mp4|flv|m4v)(\?.*)?$',
                # 其他常见视频CDN域名
                r'https?://[^/]*\.(cdn|media|video|stream)\.com/.*\.(mp4|avi|mov|mkv|wmv|flv|webm|m4v)(\?.*)?$',
                # 包含视频关键词的直链
                r'https?://[^/]*\.(mp4|avi|mov|mkv|wmv|flv|webm|m4v)(\?.*)?$'
            ],
            "direct_audio": [
                # 音频文件扩展名
                r'.*\.(mp3|wav|m4a|aac|flac|ogg)(\?.*)?$',
                # 包含音频关键词的直链
                r'https?://[^/]*\.(mp3|wav|m4a|aac|flac|ogg)(\?.*)?$'
            ]
        }
        
        self.logger.info("链接分类器已初始化")
    
    def classify_link(self, input_text: str) -> Dict:
        """
        分类输入文本中的链接
        :param input_text: 输入的文本
        :return: 分类结果
        """
        try:
            self.logger.info(f"开始分类链接: {input_text}")
            
            # 查找所有链接
            links = self._extract_links(input_text)
            self.logger.info(f"提取到 {len(links)} 个链接: {links}")
            
            if not links:
                return {
                    "success": False,
                    "error": "未找到任何链接",
                    "links": [],
                    "primary_link": None
                }
            
            # 分类每个链接
            classified_links = []
            for link in links:
                link_type, platform_id = self._identify_link_type(link)
                self.logger.info(f"链接 {link} 分类为: {link_type}, 平台ID: {platform_id}")
                classified_links.append({
                    "url": link,
                    "type": link_type,
                    "platform_id": platform_id,
                    "parser": self._get_parser_name(link_type)
                })
            
            # 确定主要链接（优先级：直链 > 平台链接）
            primary_link = self._select_primary_link(classified_links)
            self.logger.info(f"选择主要链接: {primary_link}")
            
            return {
                "success": True,
                "links": classified_links,
                "primary_link": primary_link,
                "total_links": len(links)
            }
            
        except Exception as e:
            self.logger.error(f"链接分类失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "links": [],
                "primary_link": None
            }
    
    def _extract_links(self, text: str) -> list:
        """提取文本中的所有链接"""
        # 简单的URL提取正则表达式
        url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
        return re.findall(url_pattern, text)
    
    def _identify_link_type(self, url: str) -> Tuple[str, Optional[str]]:
        """识别单个链接的类型"""
        for link_type, patterns in self.link_patterns.items():
            for pattern in patterns:
                match = re.match(pattern, url)
                if match:
                    platform_id = match.group(1) if len(match.groups()) > 0 else None
                    return link_type, platform_id
        
        # 如果没有匹配到任何模式，默认为未知类型
        return "unknown", None
    
    def _get_parser_name(self, link_type: str) -> str:
        """根据链接类型获取对应的解析器名称"""
        parser_mapping = {
            "bilibili": "bilibili_parser",
            "youtube": "youtube_parser", 
            "vimeo": "vimeo_parser",
            "douyin": "douyin_parser",
            "kuaishou": "kuaishou_parser",
            "direct_video": "direct_downloader",
            "direct_audio": "direct_downloader",
            "unknown": "generic_parser"
        }
        return parser_mapping.get(link_type, "generic_parser")
    
    def _select_primary_link(self, classified_links: list) -> Optional[dict]:
        """选择主要链接"""
        if not classified_links:
            return None
        
        # 优先级：直链 > 平台链接 > 未知
        # 直链优先级更高，因为可以直接下载，不需要解析
        priority_order = ["direct_video", "direct_audio", "bilibili", "youtube", "vimeo", "douyin", "kuaishou", "unknown"]
        
        for priority_type in priority_order:
            for link in classified_links:
                if link["type"] == priority_type:
                    return link
        
        return classified_links[0]  # 如果没有找到优先级链接，返回第一个 