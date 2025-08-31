# 视频转录系统

## 快速启动

### 1. 安装依赖
```bash
pip install -r requirements.txt
```

### 2. 配置环境变量
复制 `config.env.example` 为 `config.env` 并填入你的API密钥：
```bash
cp config.env.example config.env
# 编辑 config.env 文件，填入你的 OpenAI API 密钥
```

### 3. 启动服务器
```bash
python main.py
```

服务器将在 `http://localhost:8000` 启动

## 功能特性

- 🎬 支持B站、YouTube、Vimeo等平台视频转录
- 🎵 自动音频提取和语音识别
- 📝 智能文本处理和格式化
- 🌐 提供Web界面和RESTful API
- 📱 支持多种输出格式

## 使用说明

1. 打开浏览器访问 `http://localhost:8000`
2. 在转录功能页面输入视频链接
3. 点击"开始转录"按钮
4. 等待处理完成，下载转录结果

## API接口

- `GET /api/health` - 健康检查
- `POST /api/transcribe` - 视频转录

详细API文档请访问Web界面的"API文档"标签页。 