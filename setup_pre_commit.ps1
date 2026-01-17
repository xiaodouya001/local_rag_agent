# Pre-commit 安装脚本 (PowerShell)
# 用于快速设置 pre-commit hooks
# 编码: UTF-8 with BOM

# 设置控制台编码为 UTF-8（解决中文乱码问题）
# 兼容 PowerShell 5.1 和 PowerShell Core
if ($PSVersionTable.PSVersion.Major -ge 6) {
    # PowerShell Core (6+)
    [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
    [Console]::InputEncoding = [System.Text.Encoding]::UTF8
} else {
    # Windows PowerShell 5.1 - 使用代码页 65001 (UTF-8)
    $OutputEncoding = New-Object System.Text.UTF8Encoding $false
    try {
        chcp 65001 | Out-Null
        [Console]::OutputEncoding = [System.Text.Encoding]::GetEncoding(65001)
        [Console]::InputEncoding = [System.Text.Encoding]::GetEncoding(65001)
    } catch {
        # 如果设置失败，使用默认编码
        [Console]::OutputEncoding = [System.Text.Encoding]::Default
    }
}

# 设置环境变量
$env:PYTHONIOENCODING = 'utf-8'
$PSDefaultParameterValues['*:Encoding'] = 'utf8'

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Pre-commit Hooks 安装脚本" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 检查是否已安装 pre-commit
Write-Host "检查 pre-commit 安装状态..." -ForegroundColor Yellow
try {
    # 使用 2>&1 捕获所有输出，包括错误
    $versionOutput = pre-commit --version 2>&1 | Out-String
    if ($LASTEXITCODE -eq 0 -and $versionOutput -and $versionOutput.Trim()) {
        Write-Host "[OK] pre-commit 已安装: $($versionOutput.Trim())" -ForegroundColor Green
    } else {
        throw "pre-commit not found"
    }
} catch {
    Write-Host "[X] pre-commit 未安装，正在安装..." -ForegroundColor Red
    pip install pre-commit
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[X] 安装失败，请手动运行: pip install pre-commit" -ForegroundColor Red
        Write-Host "提示: 确保已激活虚拟环境或 pip 在 PATH 中" -ForegroundColor Gray
        exit 1
    }
    Write-Host "[OK] pre-commit 安装成功" -ForegroundColor Green
}

Write-Host ""

# 安装 Git hooks
Write-Host "安装 Git hooks..." -ForegroundColor Yellow
pre-commit install
if ($LASTEXITCODE -eq 0) {
    Write-Host "[OK] Git hooks 安装成功" -ForegroundColor Green
} else {
    Write-Host "[X] Git hooks 安装失败" -ForegroundColor Red
    exit 1
}

Write-Host ""

# 询问是否运行所有文件的检查
$response = Read-Host "是否现在运行 pre-commit 检查所有文件? (y/n)"
if ($response -eq "y" -or $response -eq "Y") {
    Write-Host ""
    Write-Host "运行 pre-commit 检查所有文件..." -ForegroundColor Yellow
    Write-Host "注意: 这可能需要几分钟时间，请耐心等待..." -ForegroundColor Gray
    Write-Host ""

    # 运行 pre-commit 检查
    pre-commit run --all-files

    # 检查退出码
    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "[OK] 所有检查通过" -ForegroundColor Green
    } else {
        Write-Host ""
        Write-Host "[WARNING] 部分检查失败，请查看上面的错误信息" -ForegroundColor Yellow
        Write-Host "提示: 某些检查会自动修复问题，请重新运行: pre-commit run --all-files" -ForegroundColor Gray
    }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "安装完成！" -ForegroundColor Green
Write-Host ""
Write-Host "使用说明:" -ForegroundColor Cyan
Write-Host "  - 正常提交代码时，hooks 会自动运行" -ForegroundColor White
Write-Host "  - 手动运行检查: pre-commit run --all-files" -ForegroundColor White
Write-Host "  - 更新 hooks: pre-commit autoupdate" -ForegroundColor White
Write-Host "  - 查看文档: docs/pre-commit-guide.md" -ForegroundColor White
Write-Host "========================================" -ForegroundColor Cyan
