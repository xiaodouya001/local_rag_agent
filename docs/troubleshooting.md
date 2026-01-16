# 故障排除与修复指南

本文档包含常见问题的解决方案、已修复的问题说明以及调试技巧。

## 常见问题及解决方案

### 1. PowerShell 中文乱码

**问题**: 运行 `setup_venv.ps1` 时中文显示为乱码

**解决方案**: 
- 脚本已自动设置 UTF-8 编码，包含以下设置：
  ```powershell
  $PSDefaultParameterValues['*:Encoding'] = 'utf8'
  [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
  [Console]::InputEncoding = [System.Text.Encoding]::UTF8
  $OutputEncoding = [System.Text.Encoding]::UTF8
  chcp 65001
  ```
- 如果仍有问题，手动运行：
  ```powershell
  chcp 65001
  [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
  ```

### 2. EOF when reading a line

**问题**: 运行 `main.py` 时出现 `EOFError: EOF when reading a line`

**原因**: 
- 在非交互式环境中运行（如某些 IDE 或自动化脚本）
- 输入流被关闭

**解决方案**:
- 代码已添加交互式环境检测和异常处理
- 程序会自动检测非交互式环境并提前退出
- 确保在交互式终端中运行程序
- 如果使用 IDE，确保配置为交互式运行模式

**实际代码实现**:
```python
# 检查是否在交互式环境中运行
is_interactive = sys.stdin.isatty() and sys.stdout.isatty()

if not is_interactive:
    print("\n警告: 检测到非交互式环境，将跳过交互式问答")
    print("提示: 请在交互式终端中运行此程序")
    return

# 在 input() 调用时添加异常处理
try:
    question = input("请输入你的问题: ").strip()
except (EOFError, OSError):
    print("\n检测到输入流已关闭，退出程序")
    break
```

### 3. Python 控制台中文显示问题

**问题**: Python 程序输出中文为乱码

**解决方案**:
- `main.py` 已自动设置 UTF-8 编码，包含多层错误处理
- Windows 系统可以设置环境变量:
  ```powershell
  $env:PYTHONIOENCODING="utf-8"
  ```

**实际代码实现**:
```python
if sys.platform == 'win32':
    try:
        if hasattr(sys.stdout, 'buffer'):
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        if hasattr(sys.stderr, 'buffer'):
            sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    except (AttributeError, ValueError):
        try:
            if hasattr(sys.stdout, 'reconfigure'):
                sys.stdout.reconfigure(encoding='utf-8', errors='replace')
            if hasattr(sys.stderr, 'reconfigure'):
                sys.stderr.reconfigure(encoding='utf-8', errors='replace')
        except (AttributeError, ValueError):
            os.environ['PYTHONIOENCODING'] = 'utf-8'
```

### 4. 网络连接超时

**问题**: 下载模型时连接 HuggingFace 超时

**解决方案**:
- 检查网络连接
- 使用 VPN 或代理（如果需要）
- 模型会自动重试，请耐心等待
- 首次下载可能需要较长时间（约400MB）

### 5. API 密钥错误

**问题**: `未找到 DEEPSEEK_API_KEY`

**解决方案**:
1. 确保 `.env` 文件存在
2. 检查 `.env` 文件内容：
   ```
   DEEPSEEK_API_KEY=your-api-key-here
   ```
3. 确保 API 密钥正确且有效
4. 获取 API 密钥: https://platform.deepseek.com/

**注意**: 免费版 API 密钥可以使用，但有限制（见下方说明）

### 5.1. 免费版 API 限制问题

**问题**: 遇到 429 错误（速率限制）或 402 错误（余额不足）

**免费版限制**:
- 每日调用次数: 约 500-1000 次/日
- 并发请求: 约 5 次/秒
- 每月 Token 额度: 约 100万-300万 tokens
- 新用户赠送: 约 500万 tokens（30天有效期）

**解决方案**:
1. **429 错误（速率限制）**: 
   - 代码已自动添加重试机制，会自动等待后重试
   - 手动控制请求频率，避免短时间内大量请求
   - 建议每次请求间隔至少 0.2 秒（5次/秒）

2. **402 错误（余额不足）**:
   - 检查 [DeepSeek 控制台](https://platform.deepseek.com/) 查看剩余额度
   - 等待下月额度重置，或升级到付费版

3. **优化使用**:
   - 减少不必要的 API 调用
   - 合理设置 `max_tokens` 参数（已默认设置为 2000）
   - 使用本地嵌入模型（已使用，无需 API）

**代码已优化**:
- ✅ 自动重试机制（最多3次）
- ✅ 速率限制自动处理（429错误）
- ✅ 友好的错误提示

### 6. 文档加载失败

**问题**: `Error loading documents\example.txt`

**解决方案**:
- 检查文件编码是否为 UTF-8
- 确保文件路径正确
- 检查文件权限
- 代码已自动尝试多种编码格式（UTF-8 和 UTF-8-sig）

**实际代码实现**:
```python
# 加载TXT文件时自动尝试多种编码
txt_loader = DirectoryLoader(
    directory,
    glob="**/*.txt",
    loader_cls=TextLoader,
    loader_kwargs={"encoding": "utf-8"}
)
# 如果失败，自动尝试 utf-8-sig 编码
```

### 7. 向量存储加载失败

**问题**: `加载向量存储失败`

**解决方案**:
- 删除 `chroma_db` 目录，重新创建向量存储
- 确保有足够的磁盘空间
- 检查文件权限

### 8. Python 版本问题

**问题**: 使用 Python 3.14 时出现兼容性问题

**解决方案**:
- 使用 Python 3.12（推荐）
- 参考 `INSTALL_PYTHON312.md` 安装 Python 3.12

### 9. 依赖安装失败

**问题**: `pip install` 失败

**解决方案**:
- 确保使用 Python 3.12
- 升级 pip: `python -m pip install --upgrade pip`
- 使用国内镜像（如果需要）:
  ```powershell
  pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
  ```

### 10. 问答链创建失败

**问题**: `创建问答链失败`

**可能原因**:
- 向量存储未正确加载
- LLM 初始化失败
- API 连接问题

**解决方案**:
- 检查向量存储是否存在
- 验证 API 密钥
- 检查网络连接
- 查看详细错误信息

### 11. 查询失败

**问题**: 查询问题时出现错误

**解决方案**:
- 代码已添加异常处理，会返回友好的错误信息
- 检查网络连接
- 验证 API 密钥是否有效
- 查看控制台输出的详细错误信息

**实际代码实现**:
```python
def query(self, question: str) -> Dict[str, Any]:
    try:
        source_documents = self.retriever.get_relevant_documents(question)
        answer = self.qa_chain.invoke(question)
    except Exception as e:
        error_msg = f"查询失败: {str(e)}"
        print(f"错误: {error_msg}")
        return {
            "answer": f"抱歉，处理问题时出现错误: {error_msg}",
            "source_documents": []
        }
```

## 已修复的问题

### 1. ✅ PowerShell 中文乱码问题 (`setup_venv.ps1`)

**修复内容**:
- 在脚本开头添加完善的 UTF-8 编码设置
- 设置 `$PSDefaultParameterValues['*:Encoding'] = 'utf8'`
- 设置 `[Console]::InputEncoding` 和 `[Console]::OutputEncoding`
- 使用 `chcp 65001` 设置代码页，并添加错误处理

### 2. ✅ EOF when reading a line 错误 (`main.py`)

**修复内容**:
- 添加交互式环境检测 (`sys.stdin.isatty()` 和 `sys.stdout.isatty()`)
- 在非交互式环境中提前退出，避免进入输入循环
- 改进 `EOFError` 和 `OSError` 异常处理
- 在 `input()` 调用外层添加异常捕获

### 3. ✅ Python 控制台中文显示问题 (`main.py`)

**修复内容**:
- 改进 UTF-8 编码设置逻辑
- 添加 `errors='replace'` 参数，避免编码错误导致程序崩溃
- 添加多层异常处理，确保在不同 Python 版本中都能正常工作
- 设置环境变量 `PYTHONIOENCODING` 作为后备方案

### 4. ✅ 错误处理改进 (`rag_agent.py`)

**改进内容**:
- LLM 初始化时添加 `timeout=60` 参数
- 嵌入模型加载时提供网络错误提示
- 文档加载时自动尝试多种编码格式（UTF-8 和 UTF-8-sig）
- 查询时添加异常处理，避免程序崩溃

### 5. ✅ 示例代码模型名称统一 (`example.py`)

**修复内容**:
- 统一使用 `all-MiniLM-L6-v2` 模型（与 `main.py` 一致）

## 代码特性说明

### 错误处理机制

1. **LLM 初始化**: 设置 60 秒超时，提供友好的错误提示
2. **嵌入模型加载**: 捕获网络错误，提示用户检查网络连接
3. **文档加载**: 自动尝试 UTF-8 和 UTF-8-sig 编码
4. **查询处理**: 捕获所有异常，返回友好的错误信息而不是崩溃

### 编码处理

1. **PowerShell**: 多层 UTF-8 编码设置，确保中文正常显示
2. **Python**: 兼容不同版本的编码设置方法，使用 `errors='replace'` 避免崩溃
3. **文档**: 支持 UTF-8 和 UTF-8-sig 编码

### 环境检测

1. **交互式环境**: 自动检测是否为交互式终端
2. **非交互式环境**: 提前退出，避免进入输入循环
3. **输入流检测**: 捕获 EOFError 和 OSError，优雅退出

## 调试技巧

1. **启用详细日志**:
   ```python
   import logging
   logging.basicConfig(level=logging.DEBUG)
   ```

2. **测试单个组件**:
   - 测试文档加载: 检查 `documents` 目录
   - 测试向量存储: 检查 `chroma_db` 目录
   - 测试 API: 使用简单的 API 调用测试

3. **检查环境变量**:
   ```powershell
   # PowerShell
   $env:DEEPSEEK_API_KEY
   
   # Python
   import os
   print(os.getenv("DEEPSEEK_API_KEY"))
   ```

4. **验证修复**:
   ```powershell
   # 测试 PowerShell 脚本（检查中文显示）
   .\setup_venv.ps1
   
   # 测试主程序（检查 EOF 处理）
   python main.py
   
   # 测试非交互式环境
   echo "test" | python main.py
   # 应该检测到非交互式环境并提前退出
   ```

## 注意事项

1. **网络连接**: 首次运行需要下载模型，可能需要较长时间（约400MB）
2. **API 密钥**: 必须正确配置 DeepSeek API 密钥
3. **Python 版本**: 建议使用 Python 3.12，避免兼容性问题
4. **磁盘空间**: 确保有足够空间存储模型和向量数据库（至少 1GB）
5. **向量存储**: 使用 FAISS 本地存储，无需额外服务

## 获取帮助

如果以上方案都无法解决问题，请：
1. 检查错误信息的完整输出
2. 确认 Python 版本: `python --version`（应为 3.12.x）
3. 确认依赖已安装: `pip list`
4. 查看项目日志和错误信息
5. 检查 `.env` 文件配置是否正确

## 文件变更清单

- ✅ `setup_venv.ps1` - 改进 UTF-8 编码设置
- ✅ `main.py` - 添加交互式环境检测和改进的 EOF 处理、UTF-8 编码
- ✅ `rag_agent.py` - 改进错误处理和异常捕获、添加超时设置
- ✅ `example.py` - 统一嵌入模型名称

所有问题已修复，代码现在更加健壮和用户友好！