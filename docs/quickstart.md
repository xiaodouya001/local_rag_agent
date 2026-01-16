# 快速开始指南

## 使用 Python 3.12 运行 RAG Agent

### 步骤 1: 安装 Python 3.12

如果还没有安装 Python 3.12：

1. 访问：https://www.python.org/downloads/release/python-3120/
2. 下载 "Windows installer (64-bit)"
3. 运行安装程序
4. **重要：勾选 "Add Python 3.12 to PATH"** ✅
5. 点击 "Install Now"

详细安装说明请参考：[install-python312.md](install-python312.md)

### 步骤 2: 运行自动设置脚本

打开 PowerShell，在项目目录下运行：

```powershell
.\setup_venv.ps1
```

这个脚本会自动：
- ✅ 检测 Python 3.12
- ✅ 创建虚拟环境
- ✅ 安装所有依赖
- ✅ 准备运行环境

### 步骤 3: 配置 API 密钥

确保 `.env` 文件存在并包含你的 DeepSeek API 密钥：

```env
DEEPSEEK_API_KEY=your-api-key-here
```

如果还没有 `.env` 文件，可以复制示例：
```powershell
copy env_example.txt .env
```

然后编辑 `.env` 文件，填入你的 API 密钥。

### 步骤 4: 添加文档（可选）

将你的文档放入 `documents` 目录：
- 支持 PDF 格式（`.pdf`）
- 支持文本格式（`.txt`）

示例文档已包含在 `documents/example.txt`

### 步骤 5: 运行程序

```powershell
# 确保虚拟环境已激活
.\venv\Scripts\Activate.ps1

# 运行程序
python main.py
```

## 手动设置（如果自动脚本失败）

```powershell
# 1. 创建虚拟环境
py -3.12 -m venv venv
# 或
python3.12 -m venv venv

# 2. 激活虚拟环境
.\venv\Scripts\Activate.ps1

# 3. 升级 pip
python -m pip install --upgrade pip

# 4. 安装依赖
python -m pip install -r requirements.txt

# 5. 运行程序
python main.py
```

## 验证 Python 3.12 安装

运行以下命令检查：

```powershell
# 方法 1
python3.12 --version

# 方法 2（使用 Python Launcher）
py -3.12 --version

# 方法 3（列出所有已安装版本）
py -0
```

应该看到：`Python 3.12.x`

## 常见问题

### Q: PowerShell 执行策略错误？

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Q: 找不到 python3.12 命令？

使用 Python Launcher：
```powershell
py -3.12 -m venv venv
```

### Q: 安装依赖时出错？

确保使用 Python 3.12，不要使用 Python 3.14。

## 下一步

安装完成后，运行：
```powershell
python main.py
```

程序会：
1. 加载嵌入模型（首次运行会下载，约400MB）
2. 初始化 DeepSeek LLM
3. 加载或创建向量存储
4. 进入交互式问答界面

输入问题后按回车，输入 `quit` 或 `exit` 退出。
