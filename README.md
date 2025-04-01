# 简历优化助手部署指南

## 项目概述
本项目是基于Vercel Serverless Function构建的简历优化服务，通过OpenAI API实现智能简历优化功能。

## 前置要求
- Vercel 账号
- OpenAI API Key（获取地址：https://platform.openai.com/api-keys）

## 部署步骤

### 1. 克隆仓库
```bash
git clone https://github.com/your-repo-url.git
cd your-repo-directory
```

### 2. 安装Vercel CLI并登录
```bash
npm install -g vercel
vercel login
```

### 3. 设置环境变量
在项目根目录创建`.env`文件：
```env
OPENAI_API_KEY=sk-your-api-key-here
OPENAI_API_BASE=https://api.openai.com/v1
DEFAULT_MODEL=gpt-3.5-turbo
```

### 4. 部署到Vercel
```bash
vercel deploy --prod
```

## 接口调用
前端HTML示例：
```html
<script>
async function getOptimizedResume(text) {
  const response = await fetch('/api/chat', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
      question: text,
      apiKey: 'your-api-key' // 可选，优先使用环境变量
    })
  });
  return await response.json();
}
</script>
```

## 配置说明
- `vercel.json`: 已配置路由规则，所有/api请求指向api目录
- `api/chat.js`: 核心服务端逻辑处理文件
- `index.html`: 前端示例页面

## 注意事项
1. 建议在Vercel控制台设置环境变量（更安全）
2. 可修改api/chat.js中的systemMessage来调整优化策略
3. 免费版Vercel有10秒超时限制，建议控制简历内容长度
