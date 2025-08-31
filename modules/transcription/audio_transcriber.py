#!/usr/bin/env python3
"""
音频转录器
使用OpenAI Whisper API转录音频文件
"""

import os
import time
import logging
import requests
from typing import Dict, Optional
from dotenv import load_dotenv

class AudioTranscriber:
    """音频转录器"""
    
    def __init__(self):
        """初始化音频转录器"""
        # 加载配置
        config_path = os.path.join(os.path.dirname(__file__), '..', '..', 'config.env')
        load_dotenv(config_path)
        
        # 设置日志
        log_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'logs')
        os.makedirs(log_dir, exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - AUDIO_TRANSCRIBER - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(os.path.join(log_dir, 'audio_transcriber.log'), encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        
        self.logger = logging.getLogger('AudioTranscriber')
        
        # 从环境变量读取配置
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.openai_base_url = os.getenv("OPENAI_BASE_URL")
        self.whisper_model = os.getenv("WHISPER_MODEL", "whisper-1")
        self.max_retries = int(os.getenv("WHISPER_MAX_RETRIES", "3"))
        self.retry_delay = int(os.getenv("WHISPER_RETRY_DELAY", "2"))
        self.timeout = int(os.getenv("WHISPER_TIMEOUT", "300"))
        
        # 检查配置
        self._validate_config()
        
        self.logger.info("音频转录器已初始化")
    
    def _format_timestamp(self, seconds: float) -> str:
        """
        格式化时间戳
        :param seconds: 秒数
        :return: 格式化的时间字符串 (MM:SS)
        """
        minutes = int(seconds // 60)
        remaining_seconds = int(seconds % 60)
        return f"{minutes:02d}:{remaining_seconds:02d}"
    
    def _validate_config(self):
        """验证配置"""
        if not self.openai_api_key:
            self.logger.warning("未设置OPENAI_API_KEY，转录功能将不可用")
        if not self.openai_base_url:
            self.logger.warning("未设置OPENAI_BASE_URL，转录功能将不可用")
    
    def transcribe_audio(self, audio_path: str) -> Dict:
        """
        转录音频文件
        :param audio_path: 音频文件路径
        :return: 转录结果
        """
        try:
            self.logger.info(f"开始转录音频: {audio_path}")
            
            if not os.path.exists(audio_path):
                return {
                    "success": False,
                    "error": "音频文件不存在",
                    "audio_path": audio_path
                }
            
            file_size = os.path.getsize(audio_path)
            if file_size == 0:
                return {
                    "success": False,
                    "error": "音频文件大小为0",
                    "audio_path": audio_path
                }
            
            if not self.openai_api_key or not self.openai_base_url:
                return {
                    "success": False,
                    "error": "OpenAI API配置不完整，请检查OPENAI_API_KEY和OPENAI_BASE_URL",
                    "audio_path": audio_path
                }
            
            # 只使用真实的Whisper API
            transcript_result = self._transcribe_with_whisper(audio_path)
            
            if transcript_result.get("success"):
                return transcript_result
            else:
                # 如果转录失败，返回错误信息
                return transcript_result
            
        except Exception as e:
            self.logger.error(f"音频转录失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "audio_path": audio_path
            }
    
    def _transcribe_with_whisper(self, audio_path: str) -> Dict:
        """
        使用OpenAI Whisper API转录音频
        :param audio_path: 音频文件路径
        :return: 转录结果
        """
        for attempt in range(self.max_retries):
            try:
                self.logger.info(f"调用Whisper API (尝试 {attempt + 1}/{self.max_retries})")
                
                # 构建API请求
                url = f"{self.openai_base_url}/audio/transcriptions"
                headers = {
                    "Authorization": f"Bearer {self.openai_api_key}"
                }
                
                # 准备文件数据
                with open(audio_path, 'rb') as audio_file:
                    files = {
                        'file': (os.path.basename(audio_path), audio_file, 'audio/wav')
                    }
                    data = {
                        'model': self.whisper_model,
                        'response_format': 'verbose_json',
                        'language': 'zh',  # 支持中文
                        'timestamp_granularities': ['word', 'segment']
                    }
                    
                    # 发送请求
                    response = requests.post(
                        url,
                        headers=headers,
                        files=files,
                        data=data,
                        timeout=self.timeout
                    )
                
                # 检查响应
                if response.status_code == 200:
                    result = response.json()
                    
                    # 添加调试日志
                    self.logger.info(f"Whisper API响应结构: {list(result.keys())}")
                    if 'segments' in result:
                        self.logger.info(f"找到segments数据，数量: {len(result['segments'])}")
                        if len(result['segments']) > 0:
                            self.logger.info(f"第一个segment示例: {result['segments'][0]}")
                    else:
                        self.logger.info("未找到segments数据，使用纯文本模式")
                    
                    # 处理verbose_json格式的响应
                    if 'segments' in result:
                        # 构建带时间戳的转录文本
                        transcript_with_timestamps = []
                        plain_transcript = []
                        
                        for segment in result['segments']:
                            start_time = segment.get('start', 0)
                            end_time = segment.get('end', 0)
                            text = segment.get('text', '').strip()
                            
                            if text:
                                # 格式化时间戳
                                start_str = self._format_timestamp(start_time)
                                end_str = self._format_timestamp(end_time)
                                
                                # 带时间戳的文本
                                timestamped_text = f"[{start_str} - {end_str}] {text}"
                                transcript_with_timestamps.append(timestamped_text)
                                
                                # 纯文本
                                plain_transcript.append(text)
                        
                        # 合并文本
                        transcript_with_timestamps = '\n'.join(transcript_with_timestamps)
                        plain_transcript = ' '.join(plain_transcript)
                        
                        self.logger.info("Whisper API转录成功（带时间戳）")
                        
                        # 添加详细的调试日志
                        self.logger.info(f"纯文本转录长度: {len(plain_transcript)}")
                        self.logger.info(f"带时间戳转录长度: {len(transcript_with_timestamps)}")
                        self.logger.info(f"第一个带时间戳文本示例: {transcript_with_timestamps[0] if transcript_with_timestamps else 'None'}")
                        
                        return {
                            "success": True,
                            "audio_path": audio_path,
                            "transcript": plain_transcript,  # 纯文本版本
                            "transcript_with_timestamps": transcript_with_timestamps,  # 带时间戳版本
                            "segments": result.get('segments', []),  # 原始分段数据
                            "model": self.whisper_model,
                            "language": "zh",
                            "message": "转录完成（含时间戳）"
                        }
                    else:
                        # 兼容旧格式
                        transcript = result.get('text', '')
                        
                        if transcript:
                            self.logger.info("Whisper API转录成功（纯文本）")
                            return {
                                "success": True,
                                "audio_path": audio_path,
                                "transcript": transcript,
                                "model": self.whisper_model,
                                "language": "zh",
                                "message": "转录完成"
                            }
                        else:
                            self.logger.warning("Whisper API返回空转录结果")
                            if attempt < self.max_retries - 1:
                                time.sleep(self.retry_delay)
                                continue
                            else:
                                return {
                                    "success": False,
                                    "error": "Whisper API返回空转录结果",
                                    "audio_path": audio_path
                                }
                
                elif response.status_code == 401:
                    error_msg = "OpenAI API密钥无效或已过期"
                    self.logger.error(f"认证失败: {error_msg}")
                    return {
                        "success": False,
                        "error": error_msg,
                        "audio_path": audio_path
                    }
                
                elif response.status_code == 429:
                    error_msg = "API请求频率过高，请稍后重试"
                    self.logger.warning(f"频率限制: {error_msg}")
                    if attempt < self.max_retries - 1:
                        wait_time = self.retry_delay * (2 ** attempt)  # 指数退避
                        self.logger.info(f"等待 {wait_time} 秒后重试")
                        time.sleep(wait_time)
                        continue
                    else:
                        return {
                            "success": False,
                            "error": error_msg,
                            "audio_path": audio_path
                        }
                
                elif response.status_code == 400:
                    error_msg = f"请求参数错误: {response.text}"
                    self.logger.error(f"参数错误: {error_msg}")
                    return {
                        "success": False,
                        "error": error_msg,
                        "audio_path": audio_path
                    }
                
                else:
                    error_msg = f"Whisper API请求失败，状态码: {response.status_code}"
                    self.logger.warning(f"API错误: {error_msg}")
                    
                    if attempt < self.max_retries - 1:
                        time.sleep(self.retry_delay)
                        continue
                    else:
                        return {
                            "success": False,
                            "error": error_msg,
                            "audio_path": audio_path
                        }
                
            except requests.exceptions.Timeout:
                error_msg = "Whisper API请求超时"
                self.logger.warning(f"请求超时 (尝试 {attempt + 1}/{self.max_retries})")
                
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                    continue
                else:
                    return {
                        "success": False,
                        "error": error_msg,
                        "audio_path": audio_path
                    }
            
            except requests.exceptions.RequestException as e:
                error_msg = f"Whisper API请求异常: {e}"
                self.logger.warning(f"请求异常 (尝试 {attempt + 1}/{self.max_retries}): {e}")
                
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                    continue
                else:
                    return {
                        "success": False,
                        "error": error_msg,
                        "audio_path": audio_path
                    }
            
            except Exception as e:
                error_msg = f"Whisper API调用异常: {e}"
                self.logger.error(f"API异常: {e}")
                return {
                    "success": False,
                    "error": error_msg,
                    "audio_path": audio_path
                }
        
        return {
            "success": False,
            "error": f"Whisper API调用失败，已重试{self.max_retries}次",
            "audio_path": audio_path
        }
    
    def get_transcription_status(self, audio_path: str) -> Dict:
        """
        获取转录状态
        :param audio_path: 音频文件路径
        :return: 转录状态
        """
        try:
            if not os.path.exists(audio_path):
                return {
                    "success": False,
                    "error": "音频文件不存在",
                    "status": "not_found"
                }
            
            # 检查是否有对应的转录文件
            transcript_path = audio_path.replace('.wav', '_transcript.txt')
            if os.path.exists(transcript_path):
                return {
                    "success": True,
                    "status": "completed",
                    "transcript_file": transcript_path,
                    "message": "转录已完成"
                }
            else:
                return {
                    "success": True,
                    "status": "pending",
                    "message": "转录待处理"
                }
                
        except Exception as e:
            self.logger.error(f"获取转录状态失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "status": "error"
            } 