#!/usr/bin/env python3
"""
直链下载器
下载直链的音频或视频文件
"""

import os
import time
import requests
import logging
from pathlib import Path
from typing import Dict, Optional
from dotenv import load_dotenv

class DirectDownloader:
    """直链下载器"""
    
    def __init__(self):
        """初始化直链下载器"""
        # 加载配置
        config_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'config.env')
        load_dotenv(config_path)
        
        # 设置日志
        log_dir = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'logs')
        os.makedirs(log_dir, exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - DIRECT_DOWNLOADER - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(os.path.join(log_dir, 'direct_downloader.log'), encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        
        self.logger = logging.getLogger('DirectDownloader')
        
        # 从环境变量读取配置
        self.download_dir = os.getenv("DOWNLOAD_DIR", "./downloads")
        self.max_file_size = int(os.getenv("MAX_FILE_SIZE_MB", "1000")) * 1024 * 1024  # 转换为字节
        self.timeout = int(os.getenv("DOWNLOAD_TIMEOUT", "300"))
        
        # 确保下载目录存在
        os.makedirs(self.download_dir, exist_ok=True)
        
        self.logger.info("直链下载器已初始化")
    
    def download_file(self, url: str, filename: str = None) -> Dict:
        """
        下载文件
        :param url: 文件URL
        :param filename: 保存的文件名（可选）
        :return: 下载结果
        """
        max_retries = 3
        retry_delay = 2  # 秒
        
        for attempt in range(max_retries):
            try:
                self.logger.info(f"开始下载 (尝试 {attempt + 1}/{max_retries}): {url}")
                
                # 如果没有指定文件名，从URL中提取
                if not filename:
                    filename = self._extract_filename(url)
                
                # 构建完整的文件路径
                file_path = os.path.join(self.download_dir, filename)
                
                # 检查文件是否已存在
                if os.path.exists(file_path):
                    self.logger.info(f"文件已存在: {file_path}")
                    return {
                        "success": True,
                        "file_path": file_path,
                        "filename": filename,
                        "size": os.path.getsize(file_path),
                        "message": "文件已存在"
                    }
                
                # 设置请求头，模拟浏览器访问
                headers = self._get_download_headers(url)
                
                # 如果是重试，尝试不同的请求头策略
                if attempt > 0:
                    headers = self._get_retry_headers(url, attempt)
                
                # 开始下载
                response = requests.get(url, stream=True, timeout=self.timeout, headers=headers)
                response.raise_for_status()
                
                # 检查文件大小
                content_length = response.headers.get('content-length')
                if content_length:
                    file_size = int(content_length)
                    if file_size > self.max_file_size:
                        return {
                            "success": False,
                            "error": f"文件大小超过限制: {file_size / (1024*1024):.2f}MB > {self.max_file_size / (1024*1024):.2f}MB",
                            "url": url
                        }
                
                # 下载文件
                with open(file_path, 'wb') as f:
                    downloaded_size = 0
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            downloaded_size += len(chunk)
                            
                            # 检查下载大小是否超过限制
                            if downloaded_size > self.max_file_size:
                                f.close()
                                os.remove(file_path)  # 删除部分下载的文件
                                return {
                                    "success": False,
                                    "error": f"下载大小超过限制: {downloaded_size / (1024*1024):.2f}MB > {self.max_file_size / (1024*1024):.2f}MB",
                                    "url": url
                                }
                
                # 验证下载的文件
                if os.path.exists(file_path):
                    actual_size = os.path.getsize(file_path)
                    if actual_size == 0:
                        os.remove(file_path)
                        return {
                            "success": False,
                            "error": "下载的文件大小为0，可能下载失败",
                            "url": url
                        }
                    
                    self.logger.info(f"下载完成: {file_path}, 大小: {actual_size / (1024*1024):.2f}MB")
                    
                    return {
                        "success": True,
                        "file_path": file_path,
                        "filename": filename,
                        "size": actual_size,
                        "message": "下载完成"
                    }
                else:
                    return {
                        "success": False,
                        "error": "文件下载后不存在",
                        "url": url
                    }
                    
            except requests.exceptions.HTTPError as e:
                error_msg = f"HTTP错误: {e}"
                if e.response.status_code == 403:
                    error_msg = "访问被拒绝(403)，可能是链接过期或需要特殊请求头"
                    if attempt < max_retries - 1:
                        self.logger.warning(f"403错误，将在{retry_delay}秒后重试 (尝试 {attempt + 1}/{max_retries})")
                        time.sleep(retry_delay)
                        continue
                elif e.response.status_code == 404:
                    error_msg = "文件不存在(404)，链接可能已失效"
                elif e.response.status_code == 429:
                    error_msg = "请求过于频繁(429)，请稍后重试"
                    if attempt < max_retries - 1:
                        self.logger.warning(f"429错误，将在{retry_delay * 2}秒后重试 (尝试 {attempt + 1}/{max_retries})")
                        time.sleep(retry_delay * 2)
                        continue
                
                self.logger.error(f"下载失败: {error_msg}")
                return {
                    "success": False,
                    "error": error_msg,
                    "url": url
                }
            except requests.exceptions.Timeout as e:
                if attempt < max_retries - 1:
                    self.logger.warning(f"下载超时，将在{retry_delay}秒后重试 (尝试 {attempt + 1}/{max_retries})")
                    time.sleep(retry_delay)
                    continue
                else:
                    self.logger.error(f"下载超时: {e}")
                    return {
                        "success": False,
                        "error": f"下载超时: {e}",
                        "url": url
                    }
            except requests.exceptions.ConnectionError as e:
                if attempt < max_retries - 1:
                    self.logger.warning(f"连接错误，将在{retry_delay}秒后重试 (尝试 {attempt + 1}/{max_retries})")
                    time.sleep(retry_delay)
                    continue
                else:
                    self.logger.error(f"连接错误: {e}")
                    return {
                        "success": False,
                        "error": f"连接错误: {e}",
                        "url": url
                    }
            except Exception as e:
                self.logger.error(f"下载失败: {e}")
                return {
                    "success": False,
                    "error": str(e),
                    "url": url
                }
        
        return {
            "success": False,
            "error": f"下载失败，已重试{max_retries}次",
            "url": url
        }
    
    def _get_download_headers(self, url: str) -> dict:
        """获取下载请求头"""
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': '*/*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        
        # 针对B站直链的特殊处理
        if 'bilivideo.com' in url:
            headers.update({
                'Referer': 'https://www.bilibili.com/',
                'Origin': 'https://www.bilibili.com',
                'Sec-Fetch-Dest': 'video',
                'Sec-Fetch-Mode': 'cors',
                'Sec-Fetch-Site': 'cross-site',
            })
        
        # 针对其他视频CDN的特殊处理
        elif any(cdn in url for cdn in ['.cdn.com', '.media.com', '.video.com', '.stream.com']):
            headers.update({
                'Referer': 'https://www.google.com/',
                'Sec-Fetch-Dest': 'video',
                'Sec-Fetch-Mode': 'cors',
                'Sec-Fetch-Site': 'cross-site',
            })
        
        return headers
    
    def _get_retry_headers(self, url: str, attempt: int) -> dict:
        """获取重试请求头"""
        # 基础请求头
        headers = self._get_download_headers(url)
        
        # 根据重试次数调整策略
        if attempt == 1:
            # 第一次重试：尝试不同的User-Agent
            headers['User-Agent'] = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        elif attempt == 2:
            # 第二次重试：尝试移动端User-Agent
            headers['User-Agent'] = 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.3 Mobile/15E148 Safari/604.1'
        
        # 针对B站直链的特殊重试策略
        if 'bilivideo.com' in url:
            if attempt == 1:
                # 尝试不同的Referer
                headers['Referer'] = 'https://www.bilibili.com/video/'
            elif attempt == 2:
                # 尝试更通用的Referer
                headers['Referer'] = 'https://www.bilibili.com/'
                headers.pop('Origin', None)  # 移除Origin头
        
        return headers
    
    def _extract_filename(self, url: str) -> str:
        """从URL中提取文件名"""
        # 移除查询参数
        clean_url = url.split('?')[0]
        # 获取文件名
        filename = clean_url.split('/')[-1]
        
        # 如果没有文件名或文件名无效，生成一个
        if not filename or '.' not in filename:
            import time
            filename = f"download_{int(time.time())}.mp4"
        
        return filename
    
    def get_download_progress(self, url: str) -> Dict:
        """
        获取下载进度（用于大文件下载）
        :param url: 文件URL
        :return: 下载进度信息
        """
        # 这里可以实现断点续传和进度跟踪
        # 目前返回基础信息
        return {
            "success": True,
            "url": url,
            "status": "not_started",
            "progress": 0,
            "message": "下载进度跟踪功能待实现"
        } 