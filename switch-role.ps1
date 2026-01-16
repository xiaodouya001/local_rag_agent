# Cursor角色切换脚本
# 使用方法: .\switch-role.ps1 -Role <角色名称>
# 可用角色: dev, review, architect, tester, docs, devops

param(
    [Parameter(Mandatory=$true)]
    [ValidateSet("dev", "review", "architect", "tester", "docs", "devops")]
    [string]$Role
)

$rulesFile = ".cursorrules"

if (-not (Test-Path $rulesFile)) {
    Write-Host "错误: 找不到 .cursorrules 文件" -ForegroundColor Red
    exit 1
}

$backupFile = ".cursorrules.backup"

# 创建备份
Copy-Item $rulesFile $backupFile -Force | Out-Null
Write-Host "已备份当前配置到 $backupFile" -ForegroundColor Gray

# 角色名称映射
$roleNames = @{
    "dev" = "Python全栈AI工程师"
    "review" = "代码审查专家"
    "architect" = "架构师"
    "tester" = "测试专家"
    "docs" = "文档工程师"
    "devops" = "DevOps工程师"
}

$targetRoleName = $roleNames[$Role]

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  切换到角色: $targetRoleName" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "提示:" -ForegroundColor Yellow
Write-Host "  1. 请打开 .cursorrules 文件" -ForegroundColor White
Write-Host "  2. 注释掉当前的 'ACTIVE ROLE' 部分" -ForegroundColor White
Write-Host "  3. 取消注释 '$targetRoleName' 对应的角色定义" -ForegroundColor White
Write-Host "  4. 保存文件后，Cursor会自动识别新角色" -ForegroundColor White
Write-Host ""
Write-Host "详细说明请查看: docs/CURSOR_ROLES_GUIDE.md" -ForegroundColor Gray
Write-Host ""

# 如果文件存在，尝试自动切换（基础版本）
$content = Get-Content $rulesFile -Raw -Encoding UTF8
$originalContent = $content

# 简单的提示：在文件中查找角色定义位置
if ($content -match "# 角色定义：") {
    Write-Host "✓ 已在 .cursorrules 文件中找到角色定义" -ForegroundColor Green
    Write-Host ""
    Write-Host "请手动编辑文件，将以下内容：" -ForegroundColor Yellow
    Write-Host "  # ACTIVE ROLE: Python全栈AI工程师（当前激活）" -ForegroundColor White
    Write-Host "修改为：" -ForegroundColor Yellow
    Write-Host "  # ACTIVE ROLE: $targetRoleName（当前激活）" -ForegroundColor Green
} else {
    Write-Host "⚠ 未能在文件中找到标准角色标记" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "备份文件: $backupFile" -ForegroundColor Gray
Write-Host "如需恢复，请运行: Copy-Item $backupFile $rulesFile -Force" -ForegroundColor Gray
