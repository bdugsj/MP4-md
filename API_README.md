# 视频转录系统 API 接口文档

## 概述

本系统提供视频转录API接口，支持B站、YouTube、Vimeo等平台的视频转录处理。用户可以通过API接口传入视频链接，系统将返回处理时间、平台信息、视频信息和四个处理后的文件。

## 接口列表

### 1. 健康检查接口

**接口地址:** `GET /api/health`

**功能描述:** 检查系统各个模块的运行状态和API配置情况

**请求参数:** 无

**响应示例:**
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

### 2. 视频转录接口

**接口地址:** `POST /api/transcribe`

**功能描述:** 传入视频链接，返回处理时间、平台信息、视频信息和四个处理后的文件

**请求参数:**
```json
{
  "video_url": "https://www.bilibili.com/video/BV1Dt4y1o7bU"
}
```

**参数说明:**
- `video_url` (必填): 视频链接，支持B站、YouTube、Vimeo等平台

**响应字段:**
- `success`: 处理是否成功
- `processing_time`: 处理完成时间
- `platform_info`: 平台信息（类型、ID等）
- `video_info`: 视频信息（标题、时长、大小等）
- `output_files`: 四个输出文件的信息

**响应示例:**
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
    "transcript": "转录文本内容...",
    "transcript_with_timestamps": "带时间戳的转录文本...",
    "formatted_text": "格式化后的文本...",
    "result_json": {
      "input_url": "https://www.bilibili.com/video/BV1Dt4y1o7bU",
      "platform_type": "bilibili",
      "platform_id": "BV1Dt4y1o7bU",
      "processing_time": "2024-01-01T12:05:30",
      "text_processing_success": true,
      "text_processing_error": null,
      "message": "视频转录处理完成 - 文本格式化完成"
    }
  }
}
```

## 支持的平台

### B站 (bilibili.com)
- 支持视频、番剧、课程等
- 链接格式: `https://www.bilibili.com/video/BV1Dt4y1o7bU`

## 待支持的平台

### YouTube
- 支持各种视频格式
- 链接格式: `https://www.youtube.com/watch?v=dQw4w9WgXcQ`

### Vimeo
- 支持高清视频
- 链接格式: `https://vimeo.com/123456789`

### 抖音/快手
- 支持短视频
- 链接格式: `https://www.douyin.com/video/123456789`

### 直链视频
- 支持MP4、AVI、MOV、MKV等格式
- 直接提供视频文件链接

## 处理流程

1. **链接分类识别** - 自动识别视频平台和类型
2. **视频下载** - 下载视频文件到本地
3. **音频提取** - 从视频中提取音频
4. **语音转录** - 使用Whisper API进行语音转文字
5. **文本处理** - 对转录文本进行格式化和优化
6. **结果输出** - 生成四个输出文件

## 输出文件说明

### 1. 原始转录文本 (transcript)
- 格式: 纯文本 (.txt)
- 内容: 直接从音频转录得到的文本内容
- 用途: 基础转录结果，包含所有识别到的文字

### 2. 带时间戳转录 (transcript_with_timestamps)
- 格式: 纯文本 (.txt)
- 内容: 包含时间信息的转录文本
- 用途: 需要时间轴信息的应用场景

### 3. 格式化文本 (formatted_text)
- 格式: Markdown (.md)
- 内容: 经过格式化和优化的文本
- 用途: 可直接用于文档、报告等

### 4. 完整结果JSON (result_json)
- 格式: JSON (.json)
- 内容: 包含所有处理信息的完整结果
- 用途: 程序化处理和分析

## 使用方法

### 启动服务器
```bash
cd web
python api_server.py
```

### 测试健康检查
```bash
curl http://localhost:8000/api/health
```

### 测试转录接口
```bash
curl -X POST http://localhost:8000/api/transcribe \
  -H "Content-Type: application/json" \
  -d '{"video_url": "https://www.bilibili.com/video/BV1Dt4y1o7bU"}'
```

### Python示例
```python
import requests

# 健康检查
response = requests.get('http://localhost:8000/api/health')
print(response.json())

# 视频转录
payload = {
    "video_url": "https://www.bilibili.com/video/BV1Dt4y1o7bU"
}
response = requests.post(
    'http://localhost:8000/api/transcribe',
    json=payload,
    headers={'Content-Type': 'application/json'}
)
result = response.json()
print(result)
```

## 错误处理

### 常见错误码
- `400 Bad Request`: 请求参数错误（如缺少video_url）
- `500 Internal Server Error`: 服务器内部错误

### 错误响应格式
```json
{
  "success": false,
  "error": "错误描述",
  "video_url": "原始请求的URL",
  "processing_time": "处理时间"
}
```

## 注意事项

1. **API密钥配置**: 确保在`config.env`中正确配置了OpenAI API密钥
2. **网络环境**: 某些平台可能需要特定的网络环境才能访问
3. **文件大小**: 大文件处理时间较长，请耐心等待
4. **并发限制**: 建议控制并发请求数量，避免系统过载

## 更新日志

### v1.0.0 (当前版本)
- ✅ 修改转录接口，接收video_url参数
- ✅ 返回处理时间、平台信息、视频信息
- ✅ 提供四个输出文件
- ✅ 添加健康检查接口
- ✅ 关闭配置获取接口
- ✅ 更新Web端API文档
