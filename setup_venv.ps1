# PowerShell 脚本：使用 Poetry 设置项目环境

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
Write-Host "RAG Agent - Poetry 环境设置" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 检查 Poetry 是否已安装
Write-Host "正在检查 Poetry..." -ForegroundColor Yellow

$poetryInstalled = $false
try {
    $poetryVersion = & poetry --version 2>&1
    if ($LASTEXITCODE -eq 0) {
        $poetryInstalled = $true
        Write-Host "[OK] 找到 Poetry: $poetryVersion" -ForegroundColor Green
    }
} catch {
    $poetryInstalled = $false
}

if (-not $poetryInstalled) {
    Write-Host "[ERROR] 未找到 Poetry" -ForegroundColor Red
    Write-Host ""
    Write-Host "请先安装 Poetry:" -ForegroundColor Yellow
    Write-Host "1. 访问 https://python-poetry.org/docs/#installation" -ForegroundColor Yellow
    Write-Host "2. 或运行以下命令安装:" -ForegroundColor Yellow
    Write-Host "   (Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | python -" -ForegroundColor White
    Write-Host ""
    Write-Host "安装完成后，请重新运行此脚本" -ForegroundColor Yellow
    Write-Host ""
    exit 1
}

# 检查 Python 3.12
Write-Host "正在检查 Python 3.12..." -ForegroundColor Yellow

$python312 = $null
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

# 配置 Poetry 使用项目内的虚拟环境
Write-Host ""
Write-Host "正在配置 Poetry..." -ForegroundColor Yellow
& poetry config virtualenvs.in-project true
# 注意：Poetry 默认使用当前活动的 Python 版本，无需额外配置

# 如果存在旧的 venv 目录，提示用户
if (Test-Path "venv") {
    Write-Host ""
    Write-Host "检测到旧的 venv 目录..." -ForegroundColor Yellow
    Write-Host "Poetry 将使用 .venv 目录管理虚拟环境" -ForegroundColor Cyan
    Write-Host "建议删除旧的 venv 目录以避免混淆" -ForegroundColor Cyan
    Write-Host ""
}

# 安装依赖（包括开发依赖）
# 注意：pyproject.toml 中已设置 package-mode = false，Poetry 不会尝试安装当前项目
Write-Host ""
Write-Host "正在安装项目依赖（这可能需要几分钟）..." -ForegroundColor Yellow
Write-Host "Poetry 会自动创建虚拟环境并安装所有依赖..." -ForegroundColor Cyan
Write-Host ""

& poetry install --with dev

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "[OK] 设置完成！" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "使用以下命令激活 Poetry 虚拟环境:" -ForegroundColor Cyan
    Write-Host "  poetry shell" -ForegroundColor White
    Write-Host ""
    Write-Host "或使用以下命令运行程序:" -ForegroundColor Cyan
    Write-Host "  poetry run python app/main.py" -ForegroundColor White
    Write-Host "  poetry run chainlit run app/chainlit_app.py" -ForegroundColor White
    Write-Host ""
    Write-Host "其他常用 Poetry 命令:" -ForegroundColor Cyan
    Write-Host "  poetry add <package>          # 添加依赖" -ForegroundColor White
    Write-Host "  poetry add --group dev <package>  # 添加开发依赖" -ForegroundColor White
    Write-Host "  poetry update                 # 更新依赖" -ForegroundColor White
    Write-Host "  poetry show                   # 查看已安装的包" -ForegroundColor White
    Write-Host ""
} else {
    Write-Host ""
    Write-Host "[ERROR] 依赖安装失败，请检查错误信息" -ForegroundColor Red
    exit 1
}
