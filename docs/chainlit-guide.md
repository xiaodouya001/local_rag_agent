# Chainlit 使用指南

## 为什么选择 Chainlit？

Chainlit 是专为 LLM 聊天应用设计的框架，相比 Streamlit 有以下优势：

✅ **界面更美观**：类似 ChatGPT 的现代化界面，开箱即用  
✅ **专为聊天设计**：内置消息历史、流式输出、文件上传等功能  
✅ **更好的用户体验**：支持多轮对话、消息编辑、代码高亮等  
✅ **易于集成**：与 LangChain 无缝集成  
✅ **生产就绪**：支持认证、持久化、多用户等企业级功能  

## 安装

```powershell
pip install chainlit
```

或者安装所有依赖：

```powershell
pip install -r requirements.txt
```

## 使用方法

### 1. 启动 Chainlit 应用

```powershell
chainlit run app/chainlit_app.py
```

应用会自动在浏览器中打开，默认地址：`http://localhost:8000`

### 2. 上传文档

- 点击界面上的文件上传按钮
- 选择 PDF 或 TXT 文件（支持多文件）
- 等待处理完成

### 3. 开始对话

- 在输入框中输入问题
- 按 Enter 或点击发送按钮
- AI 会基于你的文档回答问题

## 功能特点

### ✨ 现代化界面

- 类似 ChatGPT 的聊天界面
- 支持深色/浅色主题切换
- 流畅的动画效果

### 💬 聊天功能

- 多轮对话支持
- 消息历史记录
- 流式输出（打字效果）
- 消息编辑和删除

### 📚 文档管理

- 拖拽上传文件
- 支持 PDF、TXT 等多种格式
- 显示参考的文档块

### 🔧 高级功能

- 代码高亮
- Markdown 渲染
- 文件下载
- 用户认证（可选）

## 与 Streamlit 对比

| 特性 | Streamlit | Chainlit |
|------|-----------|----------|
| 界面美观度 | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| 聊天体验 | ⭐⭐ | ⭐⭐⭐⭐⭐ |
| 易用性 | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| 自定义能力 | ⭐⭐⭐ | ⭐⭐⭐⭐ |
| 生产就绪 | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |

## 配置选项

Chainlit 支持通过 `.chainlit` 目录下的配置文件进行自定义：

### 创建配置文件

在项目根目录创建 `.chainlit/config.toml`：

```toml
[project]
name = "RAG Agent"
description = "基于检索增强生成的AI智能体"

[UI]
# 主题设置
theme = "light"  # 或 "dark"

# 显示设置
show_readme_as_default = false
hide_cot = false
```

### 自定义欢迎消息

创建 `.chainlit/welcome.md`：

```markdown
# 欢迎使用 RAG Agent

这是一个基于检索增强生成的AI智能问答助手。

## 功能特点

- 📚 支持 PDF 和 TXT 文档上传
- 🔍 基于向量相似度的智能检索
- 💬 基于文档内容的上下文感知问答
- 📊 显示参考的文档来源

## 使用步骤

1. 上传你的文档（PDF 或 TXT 格式）
2. 等待文档处理完成
3. 开始提问！
```

## 部署

### 本地运行

```powershell
chainlit run app/chainlit_app.py
```

### 生产环境部署

Chainlit 支持多种部署方式：

1. **Docker 部署**

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["chainlit", "run", "app/chainlit_app.py", "--port", "8000"]
```

2. **使用 Gunicorn**

```powershell
pip install gunicorn
gunicorn -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000 app.chainlit_app:app
```

3. **云平台部署**
   - Railway
   - Render
   - Fly.io
   - AWS/GCP/Azure

## 常见问题

### Q: Chainlit 支持哪些文件格式？

A: 支持 PDF、TXT、Markdown、代码文件等多种格式。

### Q: 如何自定义界面主题？

A: 在 `.chainlit/config.toml` 中设置 `theme = "dark"` 或 `theme = "light"`。

## 更多资源

- [Chainlit 官方文档](https://docs.chainlit.io/)
- [Chainlit GitHub](https://github.com/Chainlit/chainlit)
- [示例项目](https://github.com/Chainlit/chainlit/tree/main/examples)
