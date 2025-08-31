#!/usr/bin/env python3
"""
工作流控制器
协调整个视频转录处理流程
"""

import os
import logging
import json
from datetime import datetime
from typing import Dict, Optional
from dotenv import load_dotenv

# 导入各个模块
from ..link_classifier import LinkClassifier
from ..preprocessing.video_downloader import VideoDownloader
from ..preprocessing.audio_processor import AudioProcessor
from ..transcription.audio_transcriber import AudioTranscriber
from ..text_processing.text_processor import TextProcessor

class WorkflowController:
    """工作流控制器"""
    
    def __init__(self):
        """初始化工作流控制器"""
        # 加载配置
        config_path = os.path.join(os.path.dirname(__file__), '..', '..', 'config.env')
        load_dotenv(config_path)
        
        # 设置日志
        log_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'logs')
        os.makedirs(log_dir, exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - WORKFLOW_CONTROLLER - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(os.path.join(log_dir, 'workflow_controller.log'), encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        
        self.logger = logging.getLogger('WorkflowController')
        
        # 初始化各个模块
        self.link_classifier = LinkClassifier()
        self.video_downloader = VideoDownloader()
        self.audio_processor = AudioProcessor()
        self.audio_transcriber = AudioTranscriber()
        self.text_processor = TextProcessor()
        
        self.logger.info("工作流控制器已初始化")
    
    def _save_transcription_result(self, result: Dict) -> Dict:
        """
        保存转录结果到output目录
        :param result: 转录结果
        :return: 包含保存路径的结果
        """
        try:
            # 创建输出目录
            output_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'output')
            transcriptions_dir = os.path.join(output_dir, 'transcriptions')
            processed_dir = os.path.join(output_dir, 'processed')
            
            os.makedirs(transcriptions_dir, exist_ok=True)
            os.makedirs(processed_dir, exist_ok=True)
            
            # 生成时间戳
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # 保存原始转录文本
            if result.get('transcript'):
                transcript_filename = f"transcript_{result.get('platform_id', 'unknown')}_{timestamp}.txt"
                transcript_path = os.path.join(transcriptions_dir, transcript_filename)
                
                with open(transcript_path, 'w', encoding='utf-8') as f:
                    f.write(result['transcript'])
                
                result['transcript_file'] = transcript_path
                self.logger.info(f"转录文本已保存: {transcript_path}")
            
            # 保存带时间戳的转录文本
            if result.get('transcript_with_timestamps'):
                timestamped_filename = f"transcript_with_timestamps_{result.get('platform_id', 'unknown')}_{timestamp}.txt"
                timestamped_path = os.path.join(transcriptions_dir, timestamped_filename)
                
                with open(timestamped_path, 'w', encoding='utf-8') as f:
                    f.write(result['transcript_with_timestamps'])
                
                result['transcript_with_timestamps_file'] = timestamped_path
                self.logger.info(f"带时间戳转录文本已保存: {timestamped_path}")
            
            # 保存格式化文本
            if result.get('formatted_text'):
                formatted_filename = f"processed_transcript_{result.get('platform_id', 'unknown')}_{timestamp}.md"
                formatted_path = os.path.join(processed_dir, formatted_filename)
                
                with open(formatted_path, 'w', encoding='utf-8') as f:
                    f.write(result['formatted_text'])
                
                result['formatted_file'] = formatted_path
                self.logger.info(f"格式化文本已保存: {formatted_path}")
            
            # 保存完整结果JSON
            json_filename = f"transcription_result_{result.get('platform_id', 'unknown')}_{timestamp}.json"
            json_path = os.path.join(processed_dir, json_filename)
            
            # 移除文件路径等敏感信息
            json_result = result.copy()
            if 'video_path' in json_result:
                json_result['video_path'] = os.path.basename(json_result['video_path'])
            if 'audio_path' in json_result:
                json_result['audio_path'] = os.path.basename(json_result['audio_path'])
            
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(json_result, f, ensure_ascii=False, indent=2)
            
            result['result_file'] = json_path
            self.logger.info(f"完整结果已保存: {json_path}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"保存转录结果失败: {e}")
            return result
    
    def process_video_link(self, input_text: str) -> Dict:
        """
        处理视频链接的完整流程
        :param input_text: 输入文本（包含链接）
        :return: 处理结果
        """
        try:
            self.logger.info(f"开始处理视频链接: {input_text}")
            
            # 步骤1: 链接分类
            self.logger.info("步骤1: 链接分类")
            classification_result = self.link_classifier.classify_link(input_text)
            if not classification_result.get("success"):
                return classification_result
            
            primary_link = classification_result.get("primary_link")
            if not primary_link:
                return {
                    "success": False,
                    "error": "未找到主要链接",
                    "input_text": input_text
                }
            
            # 步骤2: 视频下载
            self.logger.info("步骤2: 视频下载")
            download_result = self.video_downloader.download_video(
                primary_link["url"], 
                primary_link["type"]
            )
            if not download_result.get("success"):
                return download_result
            
            video_path = download_result["file_path"]
            
            # 步骤3: 音频提取
            self.logger.info("步骤3: 音频提取")
            audio_result = self.audio_processor.extract_audio_from_video(video_path)
            if not audio_result.get("success"):
                return audio_result
            
            audio_path = audio_result["audio_path"]
            
            # 步骤4: 音频转录
            self.logger.info("步骤4: 音频转录")
            transcription_result = self.audio_transcriber.transcribe_audio(audio_path)
            if not transcription_result.get("success"):
                return transcription_result
            
            transcript = transcription_result["transcript"]
            
            # 提取带时间戳的转录结果（如果存在）
            transcript_with_timestamps = transcription_result.get("transcript_with_timestamps")
            
            # 添加调试日志
            self.logger.info(f"转录结果字段: {list(transcription_result.keys())}")
            self.logger.info(f"transcript_with_timestamps存在: {transcript_with_timestamps is not None}")
            if transcript_with_timestamps:
                self.logger.info(f"transcript_with_timestamps长度: {len(transcript_with_timestamps)}")
                self.logger.info(f"transcript_with_timestamps前100字符: {transcript_with_timestamps[:100]}")
            
            # 步骤5: 文本处理
            self.logger.info("步骤5: 文本处理")
            text_result = self.text_processor.process_text(transcript, "format")
            
            # 即使文本处理失败，也要返回转录结果
            if text_result.get("success"):
                formatted_text = text_result["formatted_text"]
                text_message = "文本格式化完成"
            else:
                formatted_text = transcript  # 使用原始转录文本
                text_message = f"文本格式化失败: {text_result.get('error', '未知错误')}"
            
            # 返回完整结果，包含视频信息
            result = {
                "success": True,
                "input_text": input_text,
                "link_type": primary_link["type"],
                "platform_id": primary_link["platform_id"],
                "video_path": video_path,
                "audio_path": audio_path,
                "transcript": transcript,
                "transcript_with_timestamps": transcript_with_timestamps,
                "formatted_text": formatted_text,
                "text_processing_success": text_result.get("success", False),
                "text_processing_error": text_result.get("error") if not text_result.get("success") else None,
                "message": f"视频转录处理完成 - {text_message}",
                # 添加视频信息
                "title": download_result.get("title", "未知标题"),
                "duration": download_result.get("duration", "未知"),
                "size": download_result.get("size", "未知"),
                "platform": download_result.get("platform", primary_link["type"]),
                "url": primary_link["url"]
            }
            
            # 保存结果到output目录
            final_result = self._save_transcription_result(result)
            return final_result
            
        except Exception as e:
            self.logger.error(f"工作流处理失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "input_text": input_text
            }
    
    def get_workflow_status(self) -> Dict:
        """获取工作流状态"""
        return {
            "success": True,
            "modules": {
                "link_classifier": "已初始化",
                "video_downloader": "已初始化",
                "audio_processor": "已初始化",
                "audio_transcriber": "已初始化",
                "text_processor": "已初始化"
            },
            "message": "所有模块已就绪"
        } 