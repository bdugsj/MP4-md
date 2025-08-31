#!/usr/bin/env python3
"""
文本处理器
处理转录文本的纠正、格式化和总结
"""

import os
import time
import logging
import requests
import json
from typing import Dict, Optional
from dotenv import load_dotenv

class TextProcessor:
    """文本处理器"""
    
    def __init__(self):
        """初始化文本处理器"""
        # 加载配置
        config_path = os.path.join(os.path.dirname(__file__), '..', '..', 'config.env')
        load_dotenv(config_path)
        
        # 设置日志
        log_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'logs')
        os.makedirs(log_dir, exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - TEXT_PROCESSER - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(os.path.join(log_dir, 'text_processor.log'), encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        
        self.logger = logging.getLogger('TextProcessor')
        
        # 从环境变量读取配置
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.openai_base_url = os.getenv("OPENAI_BASE_URL")
        self.gpt_model = os.getenv("GPT_MODEL", "gpt-4o")
        self.max_retries = int(os.getenv("GPT_MAX_RETRIES", "3"))
        self.retry_delay = int(os.getenv("GPT_RETRY_DELAY", "2"))
        self.timeout = int(os.getenv("GPT_TIMEOUT", "60"))
        
        # 特殊错误类型的重试策略配置
        self.gpt_502_retry_multiplier = int(os.getenv("GPT_502_RETRY_MULTIPLIER", "3"))
        self.gpt_503_retry_multiplier = int(os.getenv("GPT_503_RETRY_MULTIPLIER", "2"))
        self.gpt_502_base_delay = int(os.getenv("GPT_502_BASE_DELAY", "5"))
        self.gpt_503_base_delay = int(os.getenv("GPT_503_BASE_DELAY", "10"))
        
        # 检查配置
        self._validate_config()
        
        self.logger.info("文本处理器已初始化")
    
    def _validate_config(self):
        """验证配置"""
        if not self.openai_api_key:
            self.logger.warning("未设置OPENAI_API_KEY，GPT功能将不可用")
        if not self.openai_base_url:
            self.logger.warning("未设置OPENAI_BASE_URL，GPT功能将不可用")
    
    def process_text(self, text: str, task: str = "format") -> Dict:
        """
        处理文本
        :param text: 输入文本
        :param task: 处理任务类型 (correct, format, summarize)
        :return: 处理结果
        """
        try:
            self.logger.info(f"开始处理文本，任务类型: {task}")
            
            # 检查OpenAI配置
            if not self.openai_api_key or not self.openai_base_url:
                return {
                    "success": False,
                    "error": "OpenAI API配置不完整，请检查OPENAI_API_KEY和OPENAI_BASE_URL",
                    "text": text[:100] + "..." if len(text) > 100 else text
                }
            
            # 根据任务类型处理文本
            if task == "correct":
                return self._correct_text(text)
            elif task == "format":
                return self._format_text(text)
            elif task == "summarize":
                return self._summarize_text(text)
            else:
                return {
                    "success": False,
                    "error": f"不支持的任务类型: {task}",
                    "text": text[:100] + "..." if len(text) > 100 else text
                }
            
        except Exception as e:
            self.logger.error(f"文本处理失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "text": text[:100] + "..." if len(text) > 100 else text
            }
    
    def _correct_text(self, text: str) -> Dict:
        """纠正文本"""
        self.logger.info("开始纠正文本")
        
        prompt = f"""请纠正以下转录文本中的错误，包括：
1. 语法错误
2. 标点符号错误
3. 明显的听写错误
4. 保持原意不变

转录文本：
{text}

请返回纠正后的文本："""
        
        gpt_result = self._call_gpt_api(prompt, "text_correction")
        
        if gpt_result.get("success"):
            return {
                "success": True,
                "original_text": text,
                "corrected_text": gpt_result["content"],
                "task": "correct",
                "message": "文本纠正完成"
            }
        else:
            # 如果GPT API失败，返回错误信息
            return {
                "success": False,
                "error": gpt_result.get("error", "GPT API调用失败"),
                "original_text": text,
                "task": "correct"
            }
    
    def _format_text(self, text: str) -> Dict:
        """格式化文本"""
        self.logger.info("开始格式化文本")
        
        prompt = f"""请将以下转录文本格式化为Markdown格式，要求：
1. 添加适当的标题和段落
2. 使用Markdown语法美化
3. 保持内容完整性
4. 添加适当的强调和列表

转录文本：
{text}

请返回格式化后的Markdown文本："""
        
        gpt_result = self._call_gpt_api(prompt, "text_formatting")
        
        if gpt_result.get("success"):
            return {
                "success": True,
                "original_text": text,
                "formatted_text": gpt_result["content"],
                "task": "format",
                "message": "文本格式化完成"
            }
        else:
            # 如果GPT API失败，返回错误信息
            return {
                "success": False,
                "error": gpt_result.get("error", "GPT API调用失败"),
                "original_text": text,
                "task": "format"
            }
    
    def _summarize_text(self, text: str) -> Dict:
        """总结文本"""
        self.logger.info("开始总结文本")
        
        prompt = f"""请总结以下转录文本的主要内容，要求：
1. 提取关键信息
2. 概括主要观点
3. 保持客观准确
4. 总结长度适中

转录文本：
{text}

请返回文本总结："""
        
        gpt_result = self._call_gpt_api(prompt, "text_summarization")
        
        if gpt_result.get("success"):
            return {
                "success": True,
                "original_text": text,
                "summary": gpt_result["content"],
                "task": "summarize",
                "message": "文本总结完成"
            }
        else:
            # 如果GPT API失败，返回错误信息
            return {
                "success": False,
                "error": gpt_result.get("error", "GPT API调用失败"),
                "original_text": text,
                "task": "summarize"
            }
    
    def _call_gpt_api(self, prompt: str, task_type: str) -> Dict:
        """
        调用GPT API
        :param prompt: 提示词
        :param task_type: 任务类型
        :return: API调用结果
        """
        for attempt in range(self.max_retries):
            try:
                self.logger.info(f"调用GPT API (尝试 {attempt + 1}/{self.max_retries})")
                
                # 构建API请求
                url = f"{self.openai_base_url}/chat/completions"
                headers = {
                    "Authorization": f"Bearer {self.openai_api_key}",
                    "Content-Type": "application/json"
                }
                
                data = {
                    "model": self.gpt_model,
                    "messages": [
                        {
                            "role": "system",
                            "content": f"你是一个专业的文本处理助手，专门负责{task_type}任务。请根据用户的要求完成任务，返回准确、有用的结果。"
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    "max_tokens": 2000,
                    "temperature": 0.3,
                    "response_format": {"type": "text"}
                }
                
                # 发送请求
                response = requests.post(
                    url,
                    headers=headers,
                    json=data,
                    timeout=self.timeout
                )
                
                # 检查响应
                if response.status_code == 200:
                    result = response.json()
                    content = result.get('choices', [{}])[0].get('message', {}).get('content', '')
                    
                    if content:
                        self.logger.info("GPT API调用成功")
                        return {
                            "success": True,
                            "content": content,
                            "model": self.gpt_model,
                            "task_type": task_type
                        }
                    else:
                        self.logger.warning("GPT API返回空内容")
                        if attempt < self.max_retries - 1:
                            time.sleep(self.retry_delay)
                            continue
                        else:
                            return {
                                "success": False,
                                "error": "GPT API返回空内容"
                            }
                
                elif response.status_code == 401:
                    error_msg = "OpenAI API密钥无效或已过期"
                    self.logger.error(f"认证失败: {error_msg}")
                    return {
                        "success": False,
                        "error": error_msg
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
                            "error": error_msg
                        }
                
                elif response.status_code == 502:
                    error_msg = "OpenAI服务器网关错误，服务器可能暂时不可用"
                    self.logger.warning(f"网关错误 (尝试 {attempt + 1}/{self.max_retries}): {error_msg}")
                    
                    if attempt < self.max_retries - 1:
                        # 502错误使用更长的重试间隔
                        wait_time = self.retry_delay * (self.gpt_502_retry_multiplier ** attempt) + self.gpt_502_base_delay
                        self.logger.info(f"等待 {wait_time} 秒后重试 (502错误特殊处理)")
                        time.sleep(wait_time)
                        continue
                    else:
                        return {
                            "success": False,
                            "error": f"{error_msg}，建议稍后重试或检查网络连接"
                        }
                
                elif response.status_code == 503:
                    error_msg = "OpenAI服务暂时不可用，服务器可能正在维护"
                    self.logger.warning(f"服务不可用 (尝试 {attempt + 1}/{self.max_retries}): {error_msg}")
                    
                    if attempt < self.max_retries - 1:
                        wait_time = self.retry_delay * (self.gpt_503_retry_multiplier ** attempt) + self.gpt_503_base_delay
                        self.logger.info(f"等待 {wait_time} 秒后重试 (503错误特殊处理)")
                        time.sleep(wait_time)
                        continue
                    else:
                        return {
                            "success": False,
                            "error": f"{error_msg}，建议稍后重试"
                        }
                
                elif response.status_code == 400:
                    error_msg = f"请求参数错误: {response.text}"
                    self.logger.error(f"参数错误: {error_msg}")
                    return {
                        "success": False,
                        "error": error_msg
                    }
                
                else:
                    error_msg = f"GPT API请求失败，状态码: {response.status_code}"
                    self.logger.warning(f"API错误: {error_msg}")
                    
                    if attempt < self.max_retries - 1:
                        time.sleep(self.retry_delay)
                        continue
                    else:
                        return {
                            "success": False,
                            "error": error_msg
                        }
                
            except requests.exceptions.Timeout:
                error_msg = "GPT API请求超时"
                self.logger.warning(f"请求超时 (尝试 {attempt + 1}/{self.max_retries})")
                
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                    continue
                else:
                    return {
                        "success": False,
                        "error": error_msg
                    }
            
            except requests.exceptions.RequestException as e:
                error_msg = f"GPT API请求异常: {e}"
                self.logger.warning(f"请求异常 (尝试 {attempt + 1}/{self.max_retries}): {e}")
                
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                    continue
                else:
                    return {
                        "success": False,
                        "error": error_msg
                    }
            
            except Exception as e:
                error_msg = f"GPT API调用异常: {e}"
                self.logger.error(f"API异常: {e}")
                return {
                    "success": False,
                    "error": error_msg
                }
        
        return {
            "success": False,
            "error": f"GPT API调用失败，已重试{self.max_retries}次"
        } 