# RAG Agent - 基于检索增强生成的AI智能体

一个功能完整的RAG (Retrieval-Augmented Generation) Agent实现，支持文档加载、向量化存储、语义检索和智能问答。

## 功能特性

- 📚 **多格式文档支持**: 支持PDF和TXT格式文档
- 🔍 **智能检索**: 基于向量相似度的语义检索
- 💬 **智能问答**: 基于检索内容的上下文感知问答
- 💾 **持久化存储**: 向量数据库持久化，无需重复处理文档
- 🎯 **可配置**: 支持自定义模型、分块大小等参数

## 系统要求

- **Python 3.12** （推荐，Python 3.14 有兼容性问题）
- Windows 10/11 或 Linux/Mac
- 至少 4GB 可用磁盘空间（用于模型和依赖）

## 安装步骤

### 1. 安装 Python 3.12

如果还没有安装 Python 3.12，请参考 [INSTALL_PYTHON312.md](INSTALL_PYTHON312.md)

**快速安装：**
- 访问：https://www.python.org/downloads/release/python-3120/
- 下载 Windows installer (64-bit)
- **重要：安装时勾选 "Add Python 3.12 to PATH"**

### 2. 创建虚拟环境并安装依赖

**自动设置（推荐）：**
```powershell
.\setup_venv.ps1
```

**手动设置：**
```powershell
# 创建虚拟环境
python3.12 -m venv venv
# 或
py -3.12 -m venv venv

# 激活虚拟环境
.\venv\Scripts\Activate.ps1

# 安装依赖
pip install -r requirements.txt
```

### 3. 配置DeepSeek API密钥

创建 `.env` 文件并添加你的DeepSeek API密钥：

```env
DEEPSEEK_API_KEY=your-api-key-here
```

或者设置环境变量：

```bash
# Windows PowerShell
$env:DEEPSEEK_API_KEY="your-api-key-here"

# Linux/Mac
export DEEPSEEK_API_KEY="your-api-key-here"
```

**注意**: 
- 嵌入模型使用本地HuggingFace模型，无需API密钥
- LLM使用DeepSeek API，需要配置API密钥
- 获取DeepSeek API密钥: https://platform.deepseek.com/

## 使用方法

### 方法1: 使用主程序（推荐）

1. 将你的文档放入 `documents` 目录（支持PDF和TXT格式）

2. 运行主程序：

```bash
python main.py
```

3. 程序会自动：
   - 首次运行：加载文档、创建向量存储
   - 后续运行：直接加载已存在的向量存储

4. 在交互式界面中输入问题，输入 `quit` 或 `exit` 退出

### 方法2: 使用示例代码

```bash
python example.py
```

### 方法3: 在代码中使用

```python
from rag_agent import RAGAgent

# 初始化Agent
agent = RAGAgent()

# 加载文档并创建向量存储
documents = agent.load_documents("./documents")
agent.create_vectorstore(documents)

# 创建问答链
agent.create_qa_chain(k=4)

# 查询
result = agent.query("你的问题")
print(result["answer"])
```

## 项目结构

```
local_rag_agent/
├── rag_agent.py          # RAG Agent核心类
├── main.py               # 主程序入口
├── example.py            # 使用示例
├── requirements.txt      # 依赖包列表
├── README.md            # 项目说明
├── .env                 # 环境变量配置（需自行创建）
├── documents/           # 文档目录（需自行创建并放入文档）
└── chroma_db/           # 向量数据库存储目录（自动创建）
```

## 配置选项

在初始化 `RAGAgent` 时可以自定义以下参数：

- `persist_directory`: 向量数据库存储路径（默认: `./chroma_db`）
- `embedding_model`: 嵌入模型名称（默认: `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`，本地模型）
- `llm_model`: 大语言模型名称（默认: `deepseek-chat`）
- `chunk_size`: 文档分块大小（默认: 1000）
- `chunk_overlap`: 文档分块重叠大小（默认: 200）
- `base_url`: DeepSeek API基础URL（默认: `https://api.deepseek.com/v1`）
- `api_key`: DeepSeek API密钥（从环境变量读取）

## 示例问题

- "文档的主要内容是什么？"
- "有哪些关键概念？"
- "请总结一下文档的要点"
- "文档中提到了哪些方法？"

## 技术栈

- **LangChain**: 用于构建RAG应用框架
- **FAISS**: 向量数据库（本地存储）
- **DeepSeek**: 大语言模型（LLM）
- **HuggingFace Sentence Transformers**: 本地嵌入模型（无需API）
- **PyTorch**: 深度学习框架

## 注意事项

1. 首次运行需要下载嵌入模型，可能需要一些时间（约400MB）
2. 确保有足够的磁盘空间存储向量数据库和模型
3. 嵌入模型使用本地HuggingFace模型，完全免费
4. LLM使用DeepSeek API，**免费版可用**，但有限制（见下方说明）
5. 建议将敏感文档放在本地，不要上传到云端
6. 获取DeepSeek API密钥: https://platform.deepseek.com/

## DeepSeek API 免费版说明

**✅ 免费版可以使用！** 但需要注意以下限制：

### 免费版限制（参考，以官方最新政策为准）

- **每日调用次数**: 约 500-1000 次/日
- **并发请求限制**: 约 5 次/秒（QPS）
- **Token 额度**: 每月约 100万-300万 tokens
- **新用户赠送**: 注册即得约 500万 tokens，有效期 30 天
- **单次请求最大 tokens**: 约 4096 tokens（输入+输出）

### 使用建议

1. **速率限制处理**: 代码已自动添加重试机制，遇到 429 错误时会自动等待并重试
2. **控制使用频率**: 避免短时间内大量请求，建议间隔 0.2 秒以上（5次/秒）
3. **监控使用量**: 定期前往 [DeepSeek 控制台](https://platform.deepseek.com/) 查看使用情况
4. **账户验证**: 某些功能可能需要验证手机/邮箱才能使用

### 常见错误处理

- **429 错误（速率限制）**: 程序会自动重试，请耐心等待
- **401 错误（API密钥无效）**: 检查 `.env` 文件中的密钥是否正确
- **402 错误（余额不足）**: 免费额度用完后需要充值或等待下月重置

### 升级到付费版

如果免费版限制不够用，可以前往 [DeepSeek 官网](https://platform.deepseek.com/) 升级到付费版，获得更高的调用限制和更好的服务。

## 常见问题

**Q: 如何添加新的文档？**  
A: 将新文档放入 `documents` 目录，删除 `chroma_db` 目录，然后重新运行程序。

**Q: 支持哪些文档格式？**  
A: 目前支持PDF和TXT格式，可以轻松扩展支持其他格式。

**Q: 如何更换LLM模型？**  
A: 在初始化 `RAGAgent` 时修改 `llm_model` 参数。

## 许可证

MIT License

## 贡献

欢迎提交Issue和Pull Request！
