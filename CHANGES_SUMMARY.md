# API接口修改总结

## 修改概述

根据您的要求，我已经完成了以下API接口的修改：

1. ✅ **修改转录接口** - 传入链接，返回处理时间、平台信息、视频信息和四个处理后的文件
2. ✅ **开放健康查询接口** - 提供系统状态检查
3. ✅ **关闭配置文件获取接口** - 移除配置信息暴露
4. ✅ **更新Web端** - 显示API使用方法文档和测试界面

## 具体修改内容

### 1. API接口修改 (`web/api_server.py`)

#### 转录接口 (`POST /api/transcribe`)
- **参数变更**: 从 `input_text` 改为 `video_url`
- **响应结构**: 重新组织为更清晰的格式
- **新增字段**:
  - `processing_time`: 处理完成时间
  - `platform_info`: 平台类型和ID信息
  - `video_info`: 视频标题、时长、大小等
  - `output_files`: 四个输出文件的内容

#### 健康检查接口 (`GET /api/health`)
- **功能**: 检查系统各模块状态和API配置
- **响应**: 包含模块状态、API配置状态、版本信息等

#### 移除的接口
- `GET /api/config` - 配置获取接口已关闭

### 2. 工作流控制器修改 (`modules/workflow/workflow_controller.py`)

- **增强返回信息**: 添加视频标题、时长、大小等信息
- **完善数据结构**: 确保所有必要信息都能正确传递

### 3. Web界面更新

#### 主页 (`/`)
- **API文档**: 完整的接口使用说明
- **测试界面**: 内置的健康检查和转录测试功能
- **响应示例**: 详细的请求和响应示例
- **使用说明**: 支持平台、处理流程、输出文件说明

### 4. 新增文件

#### 启动脚本
- `start_api.py` - Python启动脚本
- `start_api.bat` - Windows批处理启动脚本
- `start_api.sh` - Linux/Mac shell启动脚本

#### 文档和配置
- `API_README.md` - 详细的API使用文档
- `requirements.txt` - Python依赖包列表
- `test_api.py` - API接口测试脚本

## API接口详情

### 转录接口响应格式

```json
{
  "success": true,
  "processing_time": "2024-01-01T12:05:30",
  "platform_info": {
    "type": "bilibili",
    "platform_id": "BV1Dt4y1o7bU"
  },
  "video_info": {
    "title": "视频标题",
    "duration": "00:05:30",
    "size": "50.2 MB",
    "url": "https://www.bilibili.com/video/BV1Dt4y1o7bU"
  },
  "output_files": {
    "transcript": "原始转录文本...",
    "transcript_with_timestamps": "带时间戳转录...",
    "formatted_text": "格式化文本...",
    "result_json": {
      "input_url": "输入URL",
      "platform_type": "平台类型",
      "platform_id": "平台ID",
      "processing_time": "处理时间",
      "text_processing_success": true,
      "message": "处理完成消息"
    }
  }
}
```

### 健康检查接口响应格式

```json
{
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
}
```

## 使用方法

### 启动服务器

#### Windows
```bash
# 双击运行
start_api.bat

# 或命令行运行
python start_api.py
```

#### Linux/Mac
```bash
# 添加执行权限
chmod +x start_api.sh

# 运行
./start_api.sh
```

### 测试接口

#### 健康检查
```bash
curl http://localhost:8000/api/health
```

#### 转录接口
```bash
curl -X POST http://localhost:8000/api/transcribe \
  -H "Content-Type: application/json" \
  -d '{"video_url": "https://www.bilibili.com/video/BV1Dt4y1o7bU"}'
```

### Web界面访问

- **API文档**: http://localhost:8000/
- **健康检查**: http://localhost:8000/api/health
- **转录接口**: POST http://localhost:8000/api/transcribe

## 输出文件

1. **原始转录文本** - 纯文本格式
2. **带时间戳转录** - 包含时间信息
3. **格式化文本** - Markdown格式
4. **完整结果JSON** - 所有处理信息

