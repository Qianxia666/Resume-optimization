# AI简历优化助手

## 项目简介

AI简历优化助手是一个基于Python Flask构建的Web应用，通过OpenAI API实现简历内容的STAR法则优化。系统会根据用户输入的简历片段，使用人工智能对其进行分析和改写，遵循"情境(Situation)、任务(Task)、行动(Action)、结果(Result)"的STAR法则，帮助求职者创建更专业、更有竞争力的简历。

### 主要特点
- 🚀 基于OpenAI API的简历内容智能优化
- 💼 应用STAR法则重构简历描述
- 🔍 多种API兼容性模式，支持各类OpenAI兼容接口
- 🌐 支持第三方API代理服务
- 📱 响应式设计，适配各种设备屏幕
- 🔧 灵活的部署选项：Python直接运行或Docker容器

## 运行方式

### 方式一：直接运行 Python

#### 1. 安装Python依赖
```bash
pip install -r requirements.txt
```

#### 2. 环境变量配置
创建.env文件并添加以下内容：
```env
OPENAI_API_KEY=sk-your-openai-api-key
OPENAI_API_BASE=https://api.openai.com
DEFAULT_MODEL=gpt-3.5-turbo
FLASK_APP=app.py
PORT=8080
```

#### 3. 运行服务
```bash
python app.py
```
或使用Flask CLI
```bash
flask run --host=0.0.0.0 --port=8080
```

### 方式二：使用 Docker

> ⚠️ **警告**: Docker部署方式尚未经过完整实验验证，请谨慎使用。如遇问题，建议优先使用方式一进行部署。

#### 1. 使用 Docker Compose（推荐）
创建.env文件配置环境变量，然后运行：
```bash
docker-compose up -d
```

#### 2. 手动构建并运行 Docker 镜像
```bash
# 构建镜像
docker build -t resume-optimizer .

# 运行容器
docker run -d -p 8080:8080 \
  -e OPENAI_API_KEY=sk-your-openai-api-key \
  -e OPENAI_API_BASE=https://api.openai.com \
  -e DEFAULT_MODEL=gpt-3.5-turbo \
  --name resume-optimizer resume-optimizer
```

## 使用指南

1. 访问应用：打开浏览器访问 http://localhost:8080
2. 配置API：在"API配置"部分设置您的OpenAI API密钥和相关参数
3. 输入简历内容：在文本框中输入需要优化的简历片段
4. 点击"优化简历"按钮：系统会调用AI进行处理并展示优化结果
5. 使用测试功能：可以通过"测试API连接"按钮验证API配置是否正确

### API配置说明
- **API密钥**：填入您的OpenAI API密钥，格式通常为"sk-..."
- **API地址**：官方为"https://api.openai.com"，国内用户可使用第三方代理
- **模型名称**：如"gpt-3.5-turbo"、"gpt-4"等，或第三方模型名称

系统具有智能检测功能，能自动识别和矫正API地址格式问题，支持多种API路径格式。

## API端点文档

### 1. 优化简历
**请求方式**：POST `/chat`

**请求参数**：
```json
{
  "question": "需要优化的简历文本", 
  "apiKey": "可选-OpenAI API密钥",
  "baseUrl": "可选-API地址",
  "model": "可选-模型名称",
  "systemPrompt": "可选-自定义系统提示词"
}
```

**响应示例**：
```json
{
  "answer": "优化后的简历内容..."
}
```

### 2. 保存配置
**请求方式**：POST `/save_config`

**请求参数**：
```json
{
  "apiKey": "OpenAI API密钥",
  "baseUrl": "API地址",
  "model": "模型名称"
}
```

### 3. 获取配置
**请求方式**：GET `/get_config`

**响应示例**：
```json
{
  "config": {
    "apiKey": "sk_***",
    "baseUrl": "https://api.openai.com",
    "model": "gpt-3.5-turbo"
  }
}
```

### 4. 测试API连接
**请求方式**：POST `/test_api`

**请求参数**：
```json
{
  "apiKey": "OpenAI API密钥",
  "baseUrl": "API地址",
  "testMode": true
}
```

**响应示例**：
```json
{
  "success": true,
  "message": "API连接成功",
  "detectedUrl": "https://api.example.com/v1"
}
```

## 技术实现

- **前端**：HTML、CSS、JavaScript（原生）
- **后端**：Python Flask
- **API集成**：支持OpenAI API 1.x及兼容接口
- **部署选项**：直接Python运行或Docker容器化

## Docker 部署说明

> ⚠️ **警告**: Docker部署方式尚未经过完整实验验证，请谨慎使用。如遇问题，建议优先使用直接Python运行的方式部署应用。

1. 镜像基于Python 3.9构建，使用gunicorn作为生产级WSGI服务器
2. 可以通过环境变量配置OpenAI API密钥和其他参数
3. 容器内服务默认在8080端口运行
4. 支持使用.env文件或环境变量进行配置

## 常见问题与注意事项
1. **API密钥问题**：确保OpenAI API密钥有足够的额度，密钥格式正确
2. **API地址格式**：当使用第三方代理服务时，需要确保地址指向正确的API端点(通常为`/v1/chat/completions`)
3. **响应时间**：API响应时间通常需要10-30秒，取决于网络状况和OpenAI服务负载
4. **模型选择**：生产环境建议固定模型版本，避免API变更带来的兼容性问题
5. **错误处理**：系统内置了完善的错误处理和日志记录，当遇到问题时可查看控制台日志

## 开发与扩展
要添加新功能或修改现有功能，可以关注以下文件：
- `app.py` - 后端Flask应用程序
- `index.html` - 前端界面和交互逻辑
- `Dockerfile` 和 `docker-compose.yml` - 容器化配置

## 许可和致谢
本项目使用OpenAI API进行简历优化，旨在帮助求职者提升简历质量。请确保遵守OpenAI的使用条款和相关法规。
