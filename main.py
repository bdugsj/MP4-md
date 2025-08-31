#!/usr/bin/env python3
"""
视频转录项目主入口
协调各个模块完成视频转录的完整流程
"""

import os
import sys
import logging
from pathlib import Path
from dotenv import load_dotenv

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 导入各个模块
from modules.link_classifier import LinkClassifier
from modules.preprocessing.video_downloader import VideoDownloader
from modules.preprocessing.audio_processor import AudioProcessor
from modules.transcription.audio_transcriber import AudioTranscriber
from modules.text_processing.text_processor import TextProcessor
from modules.workflow.workflow_controller import WorkflowController
from web.api_server import VideoTranscriptionAPI

# 确保日志目录存在
log_dir = project_root / 'logs'
log_dir.mkdir(exist_ok=True)

# 初始化日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - MAIN - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_dir / 'main.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger('Main')

def main():
    """主函数"""
    try:
        # 加载环境变量
        config_path = project_root / 'config.env'
        if not config_path.exists():
            logger.error(f"配置文件不存在: {config_path}")
            return
        
        load_dotenv(config_path)
        logger.info("环境变量加载完成")
        
        # 检查必要的环境变量
        required_vars = ['OPENAI_API_KEY', 'OPENAI_BASE_URL']
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        if missing_vars:
            logger.error(f"缺少必要的环境变量: {missing_vars}")
            return
        
        # 启动API服务器
        port = int(os.getenv('WEB_PORT', 8000))
        logger.info(f"启动API服务器，端口: {port}")
        
        api_server = VideoTranscriptionAPI()
        api_server.run(host='0.0.0.0', port=port, debug=False)
        
    except KeyboardInterrupt:
        logger.info("程序被用户中断")
    except Exception as e:
        logger.error(f"程序运行出错: {e}")
        raise

if __name__ == "__main__":
    main() 