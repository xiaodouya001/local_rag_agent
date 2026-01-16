# Cursor多角色切换指南

本指南说明如何在Cursor中切换不同的AI角色来适应不同的开发场景。

## 方法1：单文件注释切换（推荐）

### 使用步骤

1. **打开 `.cursorrules` 文件**
2. **找到文件顶部的 "ACTIVE ROLE" 部分**
3. **注释掉当前激活的角色**（在角色定义前添加 `#`）
4. **取消注释想要使用的角色**（删除角色定义前的 `#`）

### 示例

```markdown
# 当前激活的角色
# ============================================================================
# ACTIVE ROLE: Python全栈AI工程师（当前激活）
# ============================================================================
角色定义：20年资深Python全栈AI工程师
...

# 要切换到代码审查专家，这样做：
# ============================================================================
# ACTIVE ROLE: 代码审查专家（当前激活）
# ============================================================================
# 角色定义：资深代码审查专家
# ...
```

### 优缺点

✅ **优点**：
- 所有角色定义在一个文件中，易于管理
- 切换快速，只需注释/取消注释
- 可以随时查看所有可用角色

❌ **缺点**：
- 文件可能较长
- 需要手动注释/取消注释

---

## 方法2：多个.cursorrules文件（按项目切换）

### 使用步骤

1. **创建多个角色文件**：
   ```
   .cursorrules.dev              # 开发角色
   .cursorrules.review           # 代码审查角色
   .cursorrules.architect        # 架构师角色
   .cursorrules.tester           # 测试专家角色
   ```

2. **通过重命名切换**：
   ```bash
   # 切换到代码审查模式
   mv .cursorrules .cursorrules.backup
   mv .cursorrules.review .cursorrules
   
   # 切换回开发模式
   mv .cursorrules .cursorrules.review
   mv .cursorrules.backup .cursorrules
   ```

3. **或在Cursor中直接重命名文件**

### 创建脚本（Windows PowerShell）

创建 `switch-role.ps1`：

```powershell
param(
    [Parameter(Mandatory=$true)]
    [ValidateSet("dev", "review", "architect", "tester", "docs", "devops")]
    [string]$Role
)

$backupFile = ".cursorrules.backup"
$currentFile = ".cursorrules"
$targetFile = ".cursorrules.$Role"

# 备份当前文件
if (Test-Path $currentFile) {
    Copy-Item $currentFile $backupFile -Force
    Write-Host "已备份当前角色配置到 $backupFile" -ForegroundColor Yellow
}

# 切换到目标角色
if (Test-Path $targetFile) {
    Copy-Item $targetFile $currentFile -Force
    Write-Host "已切换到角色: $Role" -ForegroundColor Green
} else {
    Write-Host "错误: 找不到角色文件 $targetFile" -ForegroundColor Red
    Write-Host "可用角色: dev, review, architect, tester, docs, devops"
    exit 1
}
```

使用方式：
```powershell
.\switch-role.ps1 -Role review
```

### 优缺点

✅ **优点**：
- 每个角色独立文件，结构清晰
- 可以针对不同项目使用不同角色
- 便于版本控制和管理

❌ **缺点**：
- 需要管理多个文件
- 切换需要重命名操作

---

## 方法3：子目录级别的.cursorrules

如果你在不同的子项目中工作，可以在每个子目录放置不同的 `.cursorrules` 文件。

### 目录结构

```
project/
├── .cursorrules                    # 根目录角色（默认）
├── frontend/
│   └── .cursorrules               # 前端开发角色
├── backend/
│   └── .cursorrules               # 后端开发角色
└── docs/
    └── .cursorrules               # 文档编写角色
```

Cursor会自动使用当前工作目录或其父目录中的 `.cursorrules` 文件。

### 优缺点

✅ **优点**：
- 根据工作目录自动切换角色
- 适合大型多模块项目

❌ **缺点**：
- 需要在多个目录维护文件
- 需要记住哪个目录用哪个角色

---

## 方法4：使用Cursor的Composer功能

在Cursor的Composer中，可以直接在对话中指定角色：

```
@.cursorrules 使用代码审查专家的角色来审查这段代码...
```

这样可以在不修改配置文件的情况下临时切换角色视角。

---

## 推荐场景

| 场景 | 推荐方法 | 原因 |
|------|---------|------|
| 日常开发 | 方法1（注释切换） | 快速灵活，适合频繁切换 |
| 长期专注某个角色 | 方法2（多文件） | 结构清晰，易于管理 |
| 多模块大型项目 | 方法3（子目录） | 不同模块自动使用不同角色 |
| 临时切换视角 | 方法4（Composer） | 不影响配置文件 |

---

## 可用的角色列表

当前 `.cursorrules` 文件中包含以下角色：

1. **Python全栈AI工程师**（默认）
   - 适用于：日常开发、新功能实现、问题调试

2. **代码审查专家**
   - 适用于：代码审查、重构建议、安全审计

3. **架构师**
   - 适用于：系统设计、技术选型、架构优化

4. **测试专家**
   - 适用于：编写测试用例、测试策略设计

5. **文档工程师**
   - 适用于：编写文档、API文档、用户手册

6. **DevOps工程师**
   - 适用于：部署配置、CI/CD、基础设施

---

## 快速切换脚本

### Windows PowerShell脚本

```powershell
# switch-cursor-role.ps1
param(
    [Parameter(Mandatory=$true)]
    [string]$Role
)

$rulesFile = ".cursorrules"
$content = Get-Content $rulesFile -Raw -Encoding UTF8

# 定义角色标记
$roles = @{
    "dev" = "ACTIVE ROLE: Python全栈AI工程师"
    "review" = "ACTIVE ROLE: 代码审查专家"
    "architect" = "ACTIVE ROLE: 架构师"
    "tester" = "ACTIVE ROLE: 测试专家"
    "docs" = "ACTIVE ROLE: 文档工程师"
    "devops" = "ACTIVE ROLE: DevOps工程师"
}

if (-not $roles.ContainsKey($Role)) {
    Write-Host "错误: 未知角色 '$Role'" -ForegroundColor Red
    Write-Host "可用角色: $($roles.Keys -join ', ')" -ForegroundColor Yellow
    exit 1
}

$targetRole = $roles[$Role]

# 注释掉所有角色
foreach ($roleKey in $roles.Keys) {
    $pattern = "(?s)(# =+\r?\n# ACTIVE ROLE:.*?)(\r?\n# =+\r?\n)"
    $content = $content -replace $pattern, "`$1 (已注释)`$2"
}

# 激活目标角色（简化版，实际需要更复杂的逻辑）
Write-Host "已切换到角色: $Role ($targetRole)" -ForegroundColor Green
Write-Host "注意: 请手动检查 .cursorrules 文件，确保正确的角色已激活" -ForegroundColor Yellow
```

---

## 提示

1. **备份配置**：切换角色前建议备份当前的 `.cursorrules` 文件
2. **验证切换**：切换后可以在Cursor中问一个问题，确认角色已正确切换
3. **混合使用**：可以结合多种方法，例如在子目录使用特定角色，在根目录使用通用角色

---

## 故障排除

### 问题：Cursor没有识别新的角色

**解决方案**：
1. 保存 `.cursorrules` 文件
2. 重启Cursor或重新加载窗口（Ctrl+Shift+P -> Reload Window）
3. 确认文件编码为UTF-8

### 问题：多个.cursorrules文件冲突

**解决方案**：
Cursor使用就近原则，当前工作目录的 `.cursorrules` 优先。确保只在一个位置激活角色。

### 问题：切换后代码风格不一致

**解决方案**：
确保所有角色的基础规范保持一致，只有专业领域的要求不同。
