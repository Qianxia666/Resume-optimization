# 简历优化API服务部署指南

## 项目简介
本项目是基于Vercel Serverless Function构建的简历优化服务，通过OpenAI API实现简历内容的STAR法则优化。

## 部署步骤

### 1. Vercel一键部署
[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https://github.com/Qianxia666/Resume-optimization)

### 2. 环境变量配置
在Vercel项目设置中添加以下环境变量：
```env
OPENAI_API_KEY=sk-your-openai-api-key
OPENAI_API_BASE=https://api.openai.com
DEFAULT_MODEL=gpt-3.5-turbo
```

### 3. 服务部署
```bash
npm install -g vercel
vercel deploy --prod
```

## 接口文档
**请求方式**：POST `/api/chat`

**请求参数**：
```json
{
  "question": "需要优化的简历文本",
  "apiKey": "可选-OpenAI API密钥",
  "model": "可选-模型名称"
}
```

**响应示例**：
```json
{
  "answer": "优化后的简历内容..."
}
```

## 本地开发
1. 安装依赖
```bash
npm install
```

2. 启动开发服务器
```bash
vercel dev
```

## 注意事项
1. 请确保OpenAI API密钥有足够的额度
2. 生产环境建议固定模型版本
3. API响应时间取决于OpenAI服务状态
