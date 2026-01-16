# Python 3.12 安装指南

## Windows 安装步骤

### 方法 1: 从官网下载（推荐）

1. **访问 Python 官网**
   - 打开浏览器，访问：https://www.python.org/downloads/release/python-3120/
   - 或直接访问：https://www.python.org/downloads/

2. **下载 Python 3.12**
   - 找到 "Python 3.12.0" 或更高版本
   - 点击 "Windows installer (64-bit)" 下载
   - 文件大小约 25MB

3. **运行安装程序**
   - 双击下载的 `.exe` 文件
   - **重要：勾选 "Add Python 3.12 to PATH"** ✅
   - 选择 "Install Now" 或 "Customize installation"
   - 等待安装完成

4. **验证安装**
   - 打开 PowerShell 或命令提示符
   - 运行：`python --version` 或 `python3.12 --version`
   - 应该显示：`Python 3.12.x`

### 方法 2: 使用 Microsoft Store

1. 打开 Microsoft Store
2. 搜索 "Python 3.12"
3. 点击安装

### 方法 3: 使用 Chocolatey（如果已安装）

```powershell
choco install python312
```

## 安装后设置

安装完成后，运行以下命令设置项目：

```powershell
# 运行自动设置脚本
.\setup_venv.ps1
```

或者手动设置：

```powershell
# 1. 创建虚拟环境
python3.12 -m venv venv
# 或
py -3.12 -m venv venv

# 2. 激活虚拟环境
.\venv\Scripts\Activate.ps1

# 3. 升级 pip
python -m pip install --upgrade pip

# 4. 安装依赖
python -m pip install -r requirements.txt

# 5. 运行程序
python main.py
```

## 常见问题

### Q: 安装后仍然找不到 python3.12 命令？

A: 尝试使用 Python Launcher：
```powershell
py -3.12 --version
```

### Q: PowerShell 执行策略错误？

A: 运行以下命令：
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Q: 如何检查已安装的 Python 版本？

A: 运行：
```powershell
py -0  # 列出所有已安装的 Python 版本
```

### Q: 需要卸载旧版本吗？

A: 不需要，可以同时安装多个 Python 版本。使用 `py -3.12` 来指定版本。

## 验证安装

安装完成后，运行：

```powershell
python3.12 --version
# 或
py -3.12 --version
```

应该看到类似输出：
```
Python 3.12.0
```

## 下一步

安装 Python 3.12 后，运行：
```powershell
.\setup_venv.ps1
```

这将自动：
- 检测 Python 3.12
- 创建虚拟环境
- 安装所有依赖
- 准备运行程序
