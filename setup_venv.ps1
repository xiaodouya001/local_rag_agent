# PowerShell 脚本：使用 Python 3.12 创建虚拟环境

# 设置控制台编码为 UTF-8，解决中文乱码问题
# 必须在脚本开头设置，确保所有输出都使用UTF-8编码
$PSDefaultParameterValues['*:Encoding'] = 'utf8'
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
[Console]::InputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8
# 设置代码页为UTF-8 (65001)
try {
    $null = chcp 65001
} catch {
    # 如果chcp命令失败，继续执行
}

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "RAG Agent - Python 3.12 虚拟环境设置" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 检查 Python 3.12
Write-Host "正在检查 Python 3.12..." -ForegroundColor Yellow

$python312 = $null

# 尝试不同的命令
$commands = @("python3.12", "py -3.12", "python")

foreach ($cmd in $commands) {
    try {
        if ($cmd -eq "py -3.12") {
            $version = & py -3.12 --version 2>&1
        } else {
            $version = & $cmd --version 2>&1
        }
        
        if ($version -match "Python 3\.12") {
            $python312 = $cmd
            Write-Host "[OK] 找到 Python 3.12: $version" -ForegroundColor Green
            break
        }
    } catch {
        continue
    }
}

if (-not $python312) {
    Write-Host "[ERROR] 未找到 Python 3.12" -ForegroundColor Red
    Write-Host ""
    Write-Host "请先安装 Python 3.12:" -ForegroundColor Yellow
    Write-Host "1. 访问 https://www.python.org/downloads/release/python-3120/" -ForegroundColor Yellow
    Write-Host "2. 下载并安装 Python 3.12" -ForegroundColor Yellow
    Write-Host "3. 安装时勾选 'Add Python 3.12 to PATH'" -ForegroundColor Yellow
    Write-Host ""
    exit 1
}

# 初始化变量
$skipVenvCreation = $false

# 删除旧的虚拟环境
if (Test-Path "venv") {
    Write-Host "检测到已存在的虚拟环境..." -ForegroundColor Yellow
    
    # 检查是否有 Python 进程正在使用虚拟环境
    $pythonProcesses = Get-Process python -ErrorAction SilentlyContinue | Where-Object {
        $_.Path -like "*local_rag_agent\venv*"
    }
    
    if ($pythonProcesses) {
        Write-Host "警告: 检测到正在运行的 Python 进程，正在尝试关闭..." -ForegroundColor Yellow
        try {
            $pythonProcesses | Stop-Process -Force -ErrorAction SilentlyContinue
            Start-Sleep -Seconds 2
        } catch {
            Write-Host "无法关闭所有 Python 进程，请手动关闭后再运行此脚本" -ForegroundColor Red
            exit 1
        }
    }
    
    Write-Host "正在删除旧的虚拟环境..." -ForegroundColor Yellow
    
    # 尝试删除，如果失败则重命名或使用现有环境
    try {
        Remove-Item -Recurse -Force venv -ErrorAction Stop
        Write-Host "[OK] 旧虚拟环境已删除" -ForegroundColor Green
    } catch {
        Write-Host "警告: 无法删除虚拟环境（文件可能被占用）" -ForegroundColor Yellow
        Write-Host "尝试重命名为 venv_old..." -ForegroundColor Yellow
        try {
            if (Test-Path "venv_old") {
                Remove-Item -Recurse -Force venv_old -ErrorAction SilentlyContinue
            }
            Rename-Item -Path "venv" -NewName "venv_old" -ErrorAction Stop
            Write-Host "[OK] 虚拟环境已重命名为 venv_old" -ForegroundColor Green
            Write-Host "提示: 可以稍后手动删除 venv_old 目录" -ForegroundColor Cyan
        } catch {
            Write-Host "错误: 无法删除或重命名虚拟环境" -ForegroundColor Red
            Write-Host "将使用现有虚拟环境继续安装依赖" -ForegroundColor Yellow
            $skipVenvCreation = $true
        }
    }
}

# 创建新的虚拟环境（如果之前没有跳过）
if (-not $skipVenvCreation) {
    Write-Host ""
    Write-Host "正在使用 Python 3.12 创建虚拟环境..." -ForegroundColor Yellow
    
    if ($python312 -eq "py -3.12") {
        & py -3.12 -m venv venv
    } else {
        & $python312 -m venv venv
    }
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[ERROR] 创建虚拟环境失败" -ForegroundColor Red
        exit 1
    }
    
    Write-Host "[OK] 虚拟环境创建成功" -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "使用现有虚拟环境..." -ForegroundColor Yellow
}

# 激活虚拟环境
Write-Host ""
Write-Host "正在激活虚拟环境..." -ForegroundColor Yellow
& .\venv\Scripts\Activate.ps1

# 升级 pip
Write-Host ""
Write-Host "正在升级 pip..." -ForegroundColor Yellow
python -m pip install --upgrade pip

# 安装依赖
Write-Host ""
Write-Host "正在安装依赖包（这可能需要几分钟）..." -ForegroundColor Yellow
python -m pip install -r requirements.txt

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "[OK] 设置完成！" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "运行以下命令启动程序:" -ForegroundColor Cyan
    Write-Host "  python main.py" -ForegroundColor White
    Write-Host ""
} else {
    Write-Host ""
    Write-Host "[ERROR] 依赖安装失败，请检查错误信息" -ForegroundColor Red
    exit 1
}
