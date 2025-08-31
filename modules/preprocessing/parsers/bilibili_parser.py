#!/usr/bin/env python3
"""
B站视频解析器
解析B站视频链接，获取视频信息和下载链接
"""

import os
import re
import time
import requests
import logging
from typing import Dict, Optional, List
from dotenv import load_dotenv
from .base_parser import BaseParser

class BilibiliParser(BaseParser):
    """B站视频解析器"""
    
    def __init__(self):
        """初始化B站解析器"""
        super().__init__("bilibili")
        
        # B站API配置
        self.api_url = os.getenv("BILIBILI_API_URL", "https://api.cenguigui.cn/api/bilibili/api.php")
        self.max_retries = int(os.getenv("BILIBILI_MAX_RETRIES", "3"))
        self.retry_delay = int(os.getenv("BILIBILI_RETRY_DELAY", "2"))
        
        # 请求头配置
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Referer': 'https://www.bilibili.com/',
        }
        
        self.logger.info("B站解析器已初始化")
    
    def validate_url(self, url: str) -> bool:
        """
        验证B站链接是否有效
        :param url: 视频链接
        :return: 是否有效
        """
        bilibili_patterns = [
            r'https?://(?:www\.)?bilibili\.com/video/([A-Za-z0-9]+)',
            r'https?://b23\.tv/([A-Za-z0-9]+)',
            r'https?://(?:www\.)?bilibili\.com/bangumi/play/([A-Za-z0-9]+)',
            r'https?://(?:www\.)?bilibili\.com/medialist/play/([A-Za-z0-9]+)',
            r'https?://(?:www\.)?bilibili\.com/cheese/play/([A-Za-z0-9]+)'
        ]
        
        for pattern in bilibili_patterns:
            if re.match(pattern, url):
                return True
        return False
    
    def parse_link(self, url: str, platform_id: str = None) -> Dict:
        """
        解析B站视频链接
        :param url: 视频链接
        :param platform_id: 平台ID（可选）
        :return: 解析结果
        """
        try:
            self.logger.info(f"开始解析B站链接: {url}")
            
            # 验证链接
            if not self.validate_url(url):
                return {
                    "success": False,
                    "error": "无效的B站链接",
                    "url": url
                }
            
            # 提取视频ID
            video_id = self._extract_video_id(url)
            if not video_id:
                return {
                    "success": False,
                    "error": "无法提取视频ID",
                    "url": url
                }
            
            self.logger.info(f"提取到视频ID: {video_id}")
            
            # 调用API解析
            api_result = self._call_bilibili_api(url)
            if not api_result.get("success"):
                return api_result
            
            # 处理API返回结果
            video_info = api_result["data"]
            
            # 构建下载链接列表
            download_urls = self._build_download_urls(video_info)
            
            return {
                "success": True,
                "title": video_info.get("title", "未知标题"),
                "duration": video_info.get("duration", 0),
                "duration_format": video_info.get("durationFormat", "00:00:00"),
                "description": video_info.get("desc", ""),
                "thumbnail": video_info.get("imgurl", ""),
                "uploader": video_info.get("user", {}).get("name", "未知用户"),
                "uploader_avatar": video_info.get("user", {}).get("user_img", ""),
                "download_urls": download_urls,
                "platform": "bilibili",
                "video_id": video_id,
                "url": url
            }
            
        except Exception as e:
            self.logger.error(f"B站链接解析失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "url": url
            }
    
    def _extract_video_id(self, url: str) -> Optional[str]:
        """
        从URL中提取视频ID
        :param url: 视频链接
        :return: 视频ID
        """
        try:
            # 处理不同的B站链接格式
            if "b23.tv" in url:
                # 短链接需要先解析
                return self._resolve_short_url(url)
            elif "bilibili.com/video/" in url:
                # 标准视频链接
                match = re.search(r'/video/([A-Za-z0-9]+)', url)
                return match.group(1) if match else None
            elif "bilibili.com/bangumi/play/" in url:
                # 番剧链接
                match = re.search(r'/bangumi/play/([A-Za-z0-9]+)', url)
                return match.group(1) if match else None
            elif "bilibili.com/medialist/play/" in url:
                # 视频列表链接
                match = re.search(r'/medialist/play/([A-Za-z0-9]+)', url)
                return match.group(1) if match else None
            elif "bilibili.com/cheese/play/" in url:
                # 课程链接
                match = re.search(r'/cheese/play/([A-Za-z0-9]+)', url)
                return match.group(1) if match else None
            
            return None
            
        except Exception as e:
            self.logger.error(f"提取视频ID失败: {e}")
            return None
    
    def _resolve_short_url(self, short_url: str) -> Optional[str]:
        """
        解析B站短链接
        :param short_url: 短链接
        :return: 视频ID
        """
        try:
            response = requests.get(short_url, headers=self.headers, allow_redirects=False)
            if response.status_code == 302:
                location = response.headers.get('Location', '')
                # 从重定向URL中提取视频ID
                match = re.search(r'/video/([A-Za-z0-9]+)', location)
                return match.group(1) if match else None
            return None
        except Exception as e:
            self.logger.error(f"解析短链接失败: {e}")
            return None
    
    def _call_bilibili_api(self, url: str) -> Dict:
        """
        调用B站解析API
        :param url: 视频链接
        :return: API返回结果
        """
        for attempt in range(self.max_retries):
            try:
                self.logger.info(f"调用B站API (尝试 {attempt + 1}/{self.max_retries})")
                
                # 构建请求参数
                params = {
                    'url': url
                }
                
                # 发送请求
                response = requests.get(
                    self.api_url,
                    params=params,
                    headers=self.headers,
                    timeout=30
                )
                response.raise_for_status()
                
                # 解析JSON响应
                result = response.json()
                
                # 检查API返回状态
                if result.get("code") == 1:
                    self.logger.info("B站API调用成功")
                    return {
                        "success": True,
                        "data": result
                    }
                else:
                    error_msg = result.get("msg", "未知错误")
                    self.logger.warning(f"B站API返回错误: {error_msg}")
                    
                    # 如果是最后一次尝试，返回错误
                    if attempt == self.max_retries - 1:
                        return {
                            "success": False,
                            "error": f"B站API错误: {error_msg}",
                            "url": url
                        }
                    
                    # 等待后重试
                    time.sleep(self.retry_delay)
                    continue
                
            except requests.exceptions.RequestException as e:
                self.logger.warning(f"B站API请求失败 (尝试 {attempt + 1}/{self.max_retries}): {e}")
                
                if attempt == self.max_retries - 1:
                    return {
                        "success": False,
                        "error": f"B站API请求失败: {e}",
                        "url": url
                    }
                
                time.sleep(self.retry_delay)
                continue
                
            except Exception as e:
                self.logger.error(f"B站API调用异常: {e}")
                return {
                    "success": False,
                    "error": str(e),
                    "url": url
                }
        
        return {
            "success": False,
            "error": f"B站API调用失败，已重试{self.max_retries}次",
            "url": url
        }
    
    def _build_download_urls(self, video_info: Dict) -> List[Dict]:
        """
        构建下载链接列表
        :param video_info: 视频信息
        :return: 下载链接列表
        """
        download_urls = []
        
        try:
            # 从API返回结果中提取下载链接
            if "data" in video_info and isinstance(video_info["data"], list):
                for item in video_info["data"]:
                    if "video_url" in item and item["video_url"]:
                        download_urls.append({
                            "url": item["video_url"],
                            "quality": item.get("accept", ["未知质量"])[0] if item.get("accept") else "未知质量",
                            "format": "mp4",
                            "size": 0,  # API没有提供文件大小信息
                            "title": item.get("title", "未知标题")
                        })
            
            # 如果没有找到下载链接，尝试从其他字段获取
            if not download_urls and "video_url" in video_info:
                download_urls.append({
                    "url": video_info["video_url"],
                    "quality": "标准质量",
                    "format": "mp4",
                    "size": 0,
                    "title": video_info.get("title", "未知标题")
                })
            
            self.logger.info(f"构建了 {len(download_urls)} 个下载链接")
            
        except Exception as e:
            self.logger.error(f"构建下载链接失败: {e}")
        
        return download_urls
    
    def get_video_info(self, url: str) -> Dict:
        """
        获取视频信息（不包含下载链接）
        :param url: 视频链接
        :return: 视频信息
        """
        try:
            # 先解析链接
            parse_result = self.parse_link(url)
            if not parse_result.get("success"):
                return parse_result
            
            # 移除下载链接信息
            info = parse_result.copy()
            info.pop("download_urls", None)
            
            return info
            
        except Exception as e:
            self.logger.error(f"获取视频信息失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "url": url
            } 