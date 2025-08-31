"""
下载器模块
包含各种类型的文件下载器
"""

from .direct_downloader import DirectDownloader
from .platform_downloader import PlatformDownloader

__all__ = ['DirectDownloader', 'PlatformDownloader'] 