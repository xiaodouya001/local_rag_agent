# Cursor角色切换脚本
# 使用方法: .\switch_role.ps1 <角色名称>
# 可用角色: dev, review, architect, tester, docs, devops, prompt
#
# 功能说明：
# - 自动备份当前的 .cursorrules 文件
# - 从 cursor-roles/ 目录读取角色文件并复制为 .cursorrules
# - 显示切换结果和提示信息

param(
    [Parameter(Mandatory=$true, Position=0)]
    [ValidateSet("dev", "review", "architect", "tester", "docs", "devops", "prompt")]
    [string]$Role
)

$currentFile = ".cursorrules"
$backupFile = ".cursorrules.backup"
$rolesDir = "cursor-roles"
$targetFile = Join-Path $rolesDir "$Role.md"

# 角色名称映射
$roleNames = @{
    "dev" = "Python全栈AI工程师"
    "review" = "代码审查专家"
    "architect" = "架构师"
    "tester" = "测试专家"
    "docs" = "文档工程师"
    "devops" = "DevOps工程师"
    "prompt" = "资深 Prompt 开发专家"
}

$targetRoleName = $roleNames[$Role]

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Cursor角色切换工具" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 检查角色目录是否存在
if (-not (Test-Path $rolesDir)) {
    Write-Host "错误: 找不到角色目录 $rolesDir" -ForegroundColor Red
    Write-Host "请确保在项目根目录运行此脚本" -ForegroundColor Yellow
    exit 1
}

# 检查目标角色文件是否存在
if (-not (Test-Path $targetFile)) {
    Write-Host "错误: 找不到角色文件 $targetFile" -ForegroundColor Red
    Write-Host ""
    Write-Host "可用角色文件:" -ForegroundColor Yellow
    Get-ChildItem -Path $rolesDir -Filter "*.md" | ForEach-Object {
        $roleKey = $_.BaseName
        if ($roleNames.ContainsKey($roleKey)) {
            Write-Host "  $roleKey - $($roleNames[$roleKey])" -ForegroundColor White
        }
    }
    Write-Host ""
    exit 1
}

# 备份当前文件（如果存在）
if (Test-Path $currentFile) {
    Copy-Item $currentFile $backupFile -Force | Out-Null
    Write-Host "✓ 已备份当前配置到 $backupFile" -ForegroundColor Gray
} else {
    Write-Host "⚠ 当前 .cursorrules 文件不存在，跳过备份" -ForegroundColor Yellow
}

# 复制目标角色文件为 .cursorrules
try {
    Copy-Item $targetFile $currentFile -Force
    Write-Host "✓ 已切换到角色: $targetRoleName" -ForegroundColor Green
    Write-Host ""
    Write-Host "下一步操作:" -ForegroundColor Yellow
    Write-Host "  1. 保存文件（如果已打开）" -ForegroundColor White
    Write-Host "  2. 在Cursor中按 Ctrl+Shift+P，输入 'Reload Window' 重新加载窗口" -ForegroundColor White
    Write-Host "  3. 或者在Cursor中问一个问题验证角色是否切换成功" -ForegroundColor White
    Write-Host ""
    Write-Host "验证命令: 在Cursor中问 '请介绍一下你的角色'" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "备份文件: $backupFile" -ForegroundColor Gray
    Write-Host "如需恢复，请运行: Copy-Item $backupFile $currentFile -Force" -ForegroundColor Gray
    Write-Host ""
} catch {
    Write-Host "错误: 切换失败 - $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}
