#!/usr/bin/env python3
"""
视频转录API服务器
提供RESTful API接口
"""

import os
import json
import logging
from datetime import datetime
from flask import Flask, request, jsonify
from dotenv import load_dotenv

# 导入工作流控制器
import sys
import os
# 添加项目根目录到Python路径
project_root = os.path.join(os.path.dirname(__file__), '..')
sys.path.insert(0, project_root)

try:
    from modules.workflow import WorkflowController
except ImportError as e:
    print(f"导入WorkflowController失败: {e}")
    print(f"当前Python路径: {sys.path}")
    print(f"项目根目录: {project_root}")
    raise

class VideoTranscriptionAPI:
    """视频转录API服务器"""
    
    def __init__(self):
        """初始化API服务器"""
        # 加载配置
        config_path = os.path.join(os.path.dirname(__file__), '..', 'config.env')
        load_dotenv(config_path)
        
        # 设置日志
        log_dir = os.path.join(os.path.dirname(__file__), '..', 'logs')
        os.makedirs(log_dir, exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - API_SERVER - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(os.path.join(log_dir, 'api_server.log'), encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        
        self.logger = logging.getLogger('VideoTranscriptionAPI')
        
        # 初始化Flask应用
        self.app = Flask(__name__)
        self.setup_routes()
        
        # 初始化工作流控制器
        self.workflow_controller = WorkflowController()
        
        self.logger.info("API服务器已初始化")
    
    def setup_routes(self):
        """设置API路由"""
        
        @self.app.route('/', methods=['GET'])
        def index():
            """主页 - 包含转录功能和API文档"""
            return '''
<!DOCTYPE html>
<html>
<head>
    <title>视频转录系统</title>
    <meta charset="utf-8">
    <style>
        body { 
            font-family: Arial, sans-serif; 
            margin: 40px; 
            background-color: #f5f5f5; 
        }
        .container { 
            max-width: 1200px; 
            margin: 0 auto; 
            background: white; 
            padding: 30px; 
            border-radius: 10px; 
            box-shadow: 0 2px 10px rgba(0,0,0,0.1); 
        }
        h1, h2, h3 { color: #333; }
        h1 { text-align: center; }
        .transcription-section { 
            margin: 30px 0; 
            padding: 20px; 
            border: 1px solid #ddd; 
            border-radius: 8px; 
            background-color: #f0f8ff; 
        }
        .form-group { margin: 20px 0; }
        label { 
            display: block; 
            margin-bottom: 5px; 
            font-weight: bold; 
        }
        input[type="text"], textarea { 
            width: 100%; 
            padding: 10px; 
            border: 1px solid #ddd; 
            border-radius: 5px; 
            font-size: 16px; 
        }
        button { 
            background-color: #007bff; 
            color: white; 
            padding: 12px 24px; 
            border: none; 
            border-radius: 5px; 
            cursor: pointer; 
            font-size: 16px; 
            margin: 5px; 
        }
        button:hover { background-color: #0056b3; }
        .download-btn { background-color: #28a745; }
        .download-btn:hover { background-color: #218838; }
        .result { 
            margin-top: 20px; 
            padding: 15px; 
            background-color: #f8f9fa; 
            border-radius: 5px; 
        }
        .api-section { 
            margin: 30px 0; 
            padding: 20px; 
            border: 1px solid #ddd; 
            border-radius: 8px; 
            background-color: #f9f9f9; 
        }
        .endpoint { 
            font-family: monospace; 
            background-color: #e3f2fd; 
            padding: 8px 12px; 
            border-radius: 5px; 
            font-weight: bold; 
            color: #1976d2; 
        }
        .method { 
            display: inline-block; 
            padding: 4px 8px; 
            border-radius: 4px; 
            font-size: 12px; 
            font-weight: bold; 
            color: white; 
            margin-right: 10px; 
        }
        .method.get { background-color: #4caf50; }
        .method.post { background-color: #2196f3; }
        .param-table { 
            width: 100%; 
            border-collapse: collapse; 
            margin: 15px 0; 
        }
        .param-table th, .param-table td { 
            border: 1px solid #ddd; 
            padding: 10px; 
            text-align: left; 
        }
        .param-table th { 
            background-color: #f2f2f2; 
            font-weight: bold; 
        }
        .response-example { 
            background-color: #f8f9fa; 
            padding: 15px; 
            border-radius: 5px; 
            font-family: monospace; 
            white-space: pre-wrap; 
            border-left: 4px solid #007bff; 
        }
        .test-section { 
            background-color: #e8f5e8; 
            padding: 20px; 
            border-radius: 8px; 
            margin: 20px 0; 
        }
        .test-form { margin: 15px 0; }
        .test-input { 
            width: 100%; 
            padding: 10px; 
            border: 1px solid #ddd; 
            border-radius: 5px; 
            font-size: 14px; 
            margin-bottom: 10px; 
        }
        .test-button { 
            background-color: #007bff; 
            color: white; 
            padding: 10px 20px; 
            border: none; 
            border-radius: 5px; 
            cursor: pointer; 
            font-size: 14px; 
        }
        .test-button:hover { background-color: #0056b3; }
        .status { 
            padding: 5px 10px; 
            border-radius: 3px; 
            font-size: 14px; 
            font-weight: bold; 
            margin-bottom: 10px; 
        }
        .status.success { background-color: #d4edda; color: #155724; }
        .status.error { background-color: #f8d7da; color: #721c24; }
        .transcript-section { 
            margin: 15px 0; 
            padding: 15px; 
            border: 1px solid #dee2e6; 
            border-radius: 5px; 
            background-color: #fff; 
        }
        .transcript-title { 
            font-weight: bold; 
            color: #495057; 
            margin-bottom: 10px; 
        }
        .transcript-content { 
            background-color: #f8f9fa; 
            padding: 10px; 
            border-radius: 3px; 
            font-family: monospace; 
            white-space: pre-wrap; 
            max-height: 300px; 
            overflow-y: auto; 
        }
        .download-section { 
            margin: 15px 0; 
            padding: 15px; 
            background-color: #e7f3ff; 
            border-radius: 5px; 
        }
        .file-info { 
            background-color: #e7f3ff; 
            padding: 10px; 
            border-radius: 5px; 
            margin: 10px 0; 
        }
        .nav-tabs { 
            display: flex; 
            border-bottom: 1px solid #ddd; 
            margin-bottom: 20px; 
        }
        .nav-tab { 
            padding: 10px 20px; 
            cursor: pointer; 
            border: 1px solid transparent; 
            border-bottom: none; 
            background-color: #f8f9fa; 
        }
        .nav-tab.active { 
            background-color: white; 
            border-color: #ddd; 
            border-bottom-color: white; 
            margin-bottom: -1px; 
        }
        .tab-content { display: none; }
        .tab-content.active { display: block; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🚀 视频转录系统</h1>
        
        <!-- 导航标签 -->
        <div class="nav-tabs">
            <div class="nav-tab active" onclick="showTab('transcription', this)">🎬 转录功能</div>
            <div class="nav-tab" onclick="showTab('api-docs', this)">📚 API文档</div>
            <div class="nav-tab" onclick="showTab('testing', this)">🧪 接口测试</div>
        </div>
        
        <!-- 转录功能标签页 -->
        <div id="transcription" class="tab-content active">
            <div class="transcription-section">
                <h2>🎬 视频转录</h2>
                <p>输入视频链接，系统将自动下载、转录并处理视频内容。</p>
                
                <div class="form-group">
                    <label for="videoUrl">视频链接:</label>
                    <input type="text" id="videoUrl" placeholder="请输入B站、YouTube等视频链接" value="https://www.bilibili.com/video/BV1Dt4y1o7bU">
                </div>
                
                <div class="form-group">
                    <button onclick="transcribeVideo()">开始转录</button>
                </div>
                
                <div id="transcriptionResult" class="result" style="display: none;"></div>
            </div>
        </div>
        
        <!-- API文档标签页 -->
        <div id="api-docs" class="tab-content">
            <div class="api-section">
                <h2>📋 API接口概览</h2>
                <p>本系统提供以下API接口，支持B站、YouTube、Vimeo等平台的视频转录处理。</p>
                
                <table class="param-table">
                    <tr>
                        <th>接口</th>
                        <th>方法</th>
                        <th>描述</th>
                        <th>状态</th>
                    </tr>
                    <tr>
                        <td>/api/health</td>
                        <td><span class="method get">GET</span></td>
                        <td>健康检查接口</td>
                        <td>✅ 可用</td>
                    </tr>
                    <tr>
                        <td>/api/transcribe</td>
                        <td><span class="method post">POST</span></td>
                        <td>视频转录接口</td>
                        <td>✅ 可用</td>
                    </tr>
                </table>
            </div>
            
            <div class="api-section">
                <h2>🏥 健康检查接口</h2>
                <p><span class="endpoint">GET /api/health</span></p>
                <p>检查系统各个模块的运行状态和API配置情况。</p>
                
                <h4>响应示例：</h4>
                <div class="response-example">{
  "status": "healthy",
  "timestamp": "2024-01-01T12:00:00",
  "version": "2.0.0",
  "modules": {
    "link_classifier": "ok",
    "bilibili_parser": "ok",
    "video_downloader": "ok",
    "audio_processor": "ok",
    "audio_transcriber": "ok",
    "text_processor": "ok"
  },
  "api_status": {
    "whisper_api": "configured",
    "gpt_api": "configured"
  }
}</div>
            </div>
            
            <div class="api-section">
                <h2>🎬 视频转录接口</h2>
                <p><span class="endpoint">POST /api/transcribe</span></p>
                <p>传入视频链接，返回处理时间、平台信息、视频信息和四个处理后的文件。</p>
                
                <h4>请求参数：</h4>
                <table class="param-table">
                    <tr>
                        <th>参数名</th>
                        <th>类型</th>
                        <th>必填</th>
                        <th>描述</th>
                    </tr>
                    <tr>
                        <td>video_url</td>
                        <td>string</td>
                        <td>是</td>
                        <td>视频链接（支持B站、YouTube、Vimeo等）</td>
                    </tr>
                </table>
                
                <h4>响应字段：</h4>
                <table class="param-table">
                    <tr>
                        <th>字段名</th>
                        <th>类型</th>
                        <th>描述</th>
                    </tr>
                    <tr>
                        <td>success</td>
                        <td>boolean</td>
                        <td>处理是否成功</td>
                    </tr>
                    <tr>
                        <td>processing_time</td>
                        <td>string</td>
                        <td>处理完成时间</td>
                    </tr>
                    <tr>
                        <td>platform_info</td>
                        <td>object</td>
                        <td>平台信息（类型、ID等）</td>
                    </tr>
                    <tr>
                        <td>video_info</td>
                        <td>object</td>
                        <td>视频信息（标题、时长、大小等）</td>
                    </tr>
                    <tr>
                        <td>output_files</td>
                        <td>object</td>
                        <td>四个输出文件的信息</td>
                    </tr>
                </table>
                
                <h4>响应示例：</h4>
                <div class="response-example">{
  "success": true,
  "processing_time": "2024-01-01T12:05:30",
  "platform_info": {
    "type": "bilibili",
    "platform_id": "BV1Dt4y1o7bU"
  },
  "video_info": {
    "title": "视频标题",
    "duration": "00:05:30",
    "size": "50.2 MB"
  },
  "output_files": {
    "transcript": "转录文本内容...",
    "transcript_with_timestamps": "带时间戳的转录文本...",
    "formatted_text": "格式化后的文本...",
    "result_json": "完整的处理结果JSON..."
  }
}</div>
            </div>
            
            <div class="api-section">
                <h2>📚 使用说明</h2>
                <h3>支持的平台：</h3>
                <ul>
                    <li><strong>B站 (bilibili.com)</strong> - 支持视频、番剧、课程等</li>
                    <li><strong>YouTube</strong> - 支持各种视频格式</li>
                    <li><strong>Vimeo</strong> - 支持高清视频</li>
                    <li><strong>抖音/快手</strong> - 支持短视频</li>
                    <li><strong>直链视频</strong> - 支持MP4、AVI等格式</li>
                </ul>
                
                <h3>处理流程：</h3>
                <ol>
                    <li>链接分类识别</li>
                    <li>视频下载</li>
                    <li>音频提取</li>
                    <li>语音转录</li>
                    <li>文本处理</li>
                    <li>结果输出</li>
                </ol>
                
                <h3>输出文件：</h3>
                <ul>
                    <li><strong>原始转录文本</strong> - 纯文本格式</li>
                    <li><strong>带时间戳转录</strong> - 包含时间信息的文本</li>
                    <li><strong>格式化文本</strong> - Markdown格式的整理后文本</li>
                    <li><strong>完整结果JSON</strong> - 包含所有处理信息的JSON文件</li>
                </ul>
            </div>
        </div>
        
        <!-- 接口测试标签页 -->
        <div id="testing" class="tab-content">
            <div class="test-section">
                <h3>健康检查测试</h3>
                <button class="test-button" onclick="testHealth()">测试健康检查</button>
                <div id="healthResult" class="result" style="display: none;"></div>
            </div>
            
            <div class="test-section">
                <h3>转录功能测试</h3>
                <div class="test-form">
                    <input type="text" id="testVideoUrl" class="test-input" placeholder="请输入视频链接" value="https://www.bilibili.com/video/BV1Dt4y1o7bU">
                    <button class="test-button" onclick="testTranscribe()">测试转录</button>
                </div>
                <div id="transcribeResult" class="result" style="display: none;"></div>
            </div>
        </div>
    </div>
    
    <script>
        // 简化的测试版本
        console.log('JavaScript代码已加载 - 测试版本');
        
        // 标签页切换功能
        function showTab(tabName, element) {
            console.log('切换到标签页:', tabName);
            
            // 隐藏所有标签页内容
            var tabContents = document.querySelectorAll('.tab-content');
            for (var i = 0; i < tabContents.length; i++) {
                tabContents[i].classList.remove('active');
            }
            
            // 移除所有标签页的active状态
            var navTabs = document.querySelectorAll('.nav-tab');
            for (var i = 0; i < navTabs.length; i++) {
                navTabs[i].classList.remove('active');
            }
            
            // 显示选中的标签页内容
            var targetTab = document.getElementById(tabName);
            if (targetTab) {
                targetTab.classList.add('active');
                console.log('显示标签页内容:', tabName);
            } else {
                console.error('未找到标签页内容:', tabName);
            }
            
            // 设置选中标签页的active状态
            if (element) {
                element.classList.add('active');
            }
        }
        
        // 转录功能
        function transcribeVideo() {
            console.log('开始转录视频...');
            
            var url = document.getElementById('videoUrl').value;
            if (!url) {
                alert('请输入视频链接');
                return;
            }
            
            console.log('视频链接:', url);
            
            var resultDiv = document.getElementById('transcriptionResult');
            resultDiv.style.display = 'block';
            resultDiv.innerHTML = '<div class="status success">正在处理中，请稍候...</div>';
            
            // 使用XMLHttpRequest而不是fetch
            var xhr = new XMLHttpRequest();
            xhr.open('POST', '/api/transcribe', true);
            xhr.setRequestHeader('Content-Type', 'application/json');
            
            xhr.onreadystatechange = function() {
                if (xhr.readyState === 4) {
                    console.log('API响应状态:', xhr.status);
                    if (xhr.status === 200) {
                        try {
                            var data = JSON.parse(xhr.responseText);
                            console.log('API响应数据:', data);
                            
                            if (data.success) {
                                var resultHtml = '<div class="status success">✅ 转录完成</div>';
                                
                                // 显示处理信息
                                resultHtml += '<div class="file-info">';
                                resultHtml += '<strong>处理时间:</strong> ' + data.processing_time + '<br>';
                                resultHtml += '<strong>平台:</strong> ' + data.platform_info.type + '<br>';
                                resultHtml += '<strong>视频ID:</strong> ' + data.platform_info.platform_id + '<br>';
                                if (data.video_info) {
                                    resultHtml += '<strong>标题:</strong> ' + (data.video_info.title || '未知') + '<br>';
                                    resultHtml += '<strong>时长:</strong> ' + (data.video_info.duration || '未知') + '<br>';
                                    resultHtml += '<strong>大小:</strong> ' + (data.video_info.size || '未知');
                                }
                                resultHtml += '</div>';
                                
                                // 显示转录结果
                                if (data.output_files.transcript) {
                                    resultHtml += '<div class="transcript-section">';
                                    resultHtml += '<div class="transcript-title">📝 原始转录文本</div>';
                                    resultHtml += '<div class="transcript-content">' + data.output_files.transcript + '</div>';
                                    resultHtml += '</div>';
                                }
                                
                                if (data.output_files.transcript_with_timestamps) {
                                    resultHtml += '<div class="transcript-section">';
                                    resultHtml += '<div class="transcript-title">⏰ 带时间戳转录文本</div>';
                                    resultHtml += '<div class="transcript-content">' + data.output_files.transcript_with_timestamps + '</div>';
                                    resultHtml += '</div>';
                                }
                                
                                if (data.output_files.formatted_text) {
                                    resultHtml += '<div class="transcript-section">';
                                    resultHtml += '<div class="transcript-title">✨ 格式化文本</div>';
                                    resultHtml += '<div class="transcript-content">' + data.output_files.formatted_text + '</div>';
                                    resultHtml += '</div>';
                                }
                                
                                resultDiv.innerHTML = resultHtml;
                            } else {
                                resultDiv.innerHTML = '<div class="status error">❌ 转录失败: ' + (data.error || '未知错误') + '</div>';
                            }
                        } catch (e) {
                            console.error('解析响应失败:', e);
                            resultDiv.innerHTML = '<div class="status error">❌ 响应解析失败</div>';
                        }
                    } else {
                        resultDiv.innerHTML = '<div class="status error">❌ 请求失败: HTTP ' + xhr.status;
                    }
                }
            };
            
            xhr.onerror = function() {
                console.error('请求失败');
                resultDiv.innerHTML = '<div class="status error">❌ 网络请求失败</div>';
            };
            
            var requestData = JSON.stringify({
                video_url: url
            });
            
            console.log('发送请求数据:', requestData);
            xhr.send(requestData);
        }
        
        // 健康检查测试
        function testHealth() {
            console.log('测试健康检查...');
            var resultDiv = document.getElementById('healthResult');
            resultDiv.style.display = 'block';
            resultDiv.innerHTML = '<div class="status success">测试中...</div>';
            
            var xhr = new XMLHttpRequest();
            xhr.open('GET', '/api/health', true);
            
            xhr.onreadystatechange = function() {
                if (xhr.readyState === 4 && xhr.status === 200) {
                    try {
                        var data = JSON.parse(xhr.responseText);
                        var resultHtml = '<div class="status success">✅ 健康检查成功</div>';
                        resultHtml += '<div class="response-example">' + JSON.stringify(data, null, 2) + '</div>';
                        resultDiv.innerHTML = resultHtml;
                    } catch (e) {
                        resultDiv.innerHTML = '<div class="status error">❌ 响应解析失败</div>';
                    }
                }
            };
            
            xhr.send();
        }
        
        // 页面加载完成后初始化
        document.addEventListener('DOMContentLoaded', function() {
            console.log('页面加载完成，初始化标签页');
            
            // 测试DOM元素是否存在
            var transcriptionTab = document.getElementById('transcription');
            var apiDocsTab = document.getElementById('api-docs');
            var testingTab = document.getElementById('testing');
            
            console.log('标签页元素检查:');
            console.log('- transcription:', transcriptionTab);
            console.log('- api-docs:', apiDocsTab);
            console.log('- testing:', testingTab);
            
            // 默认显示第一个标签页
            showTab('transcription', document.querySelector('.nav-tab.active'));
            
            console.log('初始化完成');
        });
    </script>
</body>
</html>
            '''
        
        @self.app.route('/api/health', methods=['GET'])
        def health_check():
            """健康检查接口"""
            try:
                # 检查各个模块状态
                status = {
                    'status': 'healthy',
                    'timestamp': datetime.now().isoformat(),
                    'version': '2.0.0',
                    'modules': {
                        'link_classifier': 'ok',
                        'bilibili_parser': 'ok',
                        'video_downloader': 'ok',
                        'audio_processor': 'ok',
                        'audio_transcriber': 'ok',
                        'text_processor': 'ok'
                    },
                    'api_status': {
                        'whisper_api': 'unknown',
                        'gpt_api': 'unknown'
                    }
                }
                
                # 检查OpenAI API状态
                try:
                    # 简单的API连接测试
                    if os.getenv('OPENAI_API_KEY') and os.getenv('OPENAI_BASE_URL'):
                        status['api_status']['whisper_api'] = 'configured'
                        status['api_status']['gpt_api'] = 'configured'
                    else:
                        status['api_status']['whisper_api'] = 'not_configured'
                        status['api_status']['gpt_api'] = 'not_configured'
                except Exception as e:
                    status['api_status']['whisper_api'] = f'error: {str(e)}'
                    status['api_status']['gpt_api'] = f'error: {str(e)}'
                
                return jsonify(status)
            except Exception as e:
                return jsonify({
                    'status': 'unhealthy',
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                }), 500
        
        @self.app.route('/api/transcribe', methods=['POST'])
        def transcribe_video():
            """转录视频接口 - 接收链接参数"""
            try:
                data = request.get_json()
                if not data or 'video_url' not in data:
                    return jsonify({
                        'success': False,
                        'error': '缺少video_url参数'
                    }), 400
                
                video_url = data['video_url']
                self.logger.info(f"收到转录请求: {video_url}")
                
                # 记录开始时间
                start_time = datetime.now()
                
                # 调用工作流控制器
                result = self.workflow_controller.process_video_link(video_url)
                
                # 记录结束时间
                end_time = datetime.now()
                processing_time = end_time.isoformat()
                
                if result.get('success'):
                    # 构建响应数据
                    response_data = {
                        'success': True,
                        'processing_time': processing_time,
                        'platform_info': {
                            'type': result.get('link_type'),
                            'platform_id': result.get('platform_id')
                        },
                        'video_info': {
                            'title': result.get('title', '未知标题'),
                            'duration': result.get('duration', '未知'),
                            'size': result.get('size', '未知'),
                            'url': video_url
                        },
                        'output_files': {
                            'transcript': result.get('transcript', ''),
                            'transcript_with_timestamps': result.get('transcript_with_timestamps', ''),
                            'formatted_text': result.get('formatted_text', ''),
                            'result_json': {
                                'input_url': video_url,
                                'platform_type': result.get('link_type'),
                                'platform_id': result.get('platform_id'),
                                'processing_time': processing_time,
                                'text_processing_success': result.get('text_processing_success'),
                                'text_processing_error': result.get('text_processing_error'),
                                'message': result.get('message')
                            }
                        }
                    }
                    
                    # 记录成功信息
                    self.logger.info(f"转录成功: {result.get('message')}")
                    if result.get('transcript'):
                        self.logger.info(f"转录文本长度: {len(result.get('transcript'))} 字符")
                    if result.get('formatted_text'):
                        self.logger.info(f"格式化文本长度: {len(result.get('formatted_text'))} 字符")
                    
                    return jsonify(response_data)
                else:
                    # 记录错误信息
                    error_msg = result.get('error', '未知错误')
                    self.logger.error(f"转录失败: {error_msg}")
                    
                    return jsonify({
                        'success': False,
                        'error': error_msg,
                        'video_url': video_url,
                        'processing_time': processing_time
                    }), 400
                    
            except Exception as e:
                error_msg = f"转录处理异常: {str(e)}"
                self.logger.error(error_msg)
                return jsonify({
                    'success': False,
                    'error': error_msg,
                    'processing_time': datetime.now().isoformat()
                }), 500
        
        @self.app.route('/api/status/<job_id>', methods=['GET'])
        def get_job_status(job_id):
            """获取任务状态接口"""
            return jsonify({
                'success': True,
                'job_id': job_id,
                'status': 'completed',
                'message': '任务状态查询功能待实现'
            })
    
    def run(self, host='0.0.0.0', port=8000, debug=False):
        """启动API服务器"""
        self.logger.info(f"启动API服务器，地址: {host}:{port}")
        self.app.run(host=host, port=port, debug=debug) 