# Pre-commit Hooks 使用指南

## 📋 简介

Pre-commit hooks 是在提交代码到 Git 之前自动运行的检查工具，确保代码质量和一致性。

## 🚀 快速开始

### 1. 安装 pre-commit

```bash
# 使用 pip 安装
pip install pre-commit

# 或添加到 requirements.txt 后安装
pip install -r requirements.txt
```

### 2. 安装 Git hooks

```bash
# 在项目根目录运行
pre-commit install
```

这会在 `.git/hooks/pre-commit` 中安装 hooks，每次 `git commit` 时自动运行。

### 3. 手动运行所有检查

```bash
# 检查所有文件（包括未暂存的）
pre-commit run --all-files

# 只检查暂存的文件（默认行为）
pre-commit run

# 只运行特定的 hook
pre-commit run yapf --all-files  # 只格式化代码
pre-commit run ruff-check --all-files  # 只检查代码
pre-commit run isort --all-files  # 只排序导入
```

**替代方案**：如果不想使用 pre-commit，也可以直接使用工具：
```bash
# 使用项目配置文件格式化
yapf -ir --style=.style.yapf app test

# 或使用 Google 风格
yapf -ir --style=google app test
```

## 🔧 配置说明

配置文件：`.pre-commit-config.yaml`

### 包含的检查工具

1. **通用文件检查** (`pre-commit-hooks`)
   - 文件末尾换行符
   - 尾随空白
   - 合并冲突标记
   - 私密信息检测
   - YAML/JSON 语法检查
   - 大文件检查

2. **代码格式化** (`yapf`)
   - 使用 Google Style 格式化 Python 代码
   - 配置文件：`.style.yapf`

3. **代码检查** (`ruff`)
   - 快速且功能强大的 Python linter
   - 替代 flake8 + pylint
   - 配置文件：`.ruff.toml`

4. **导入排序** (`isort`)
   - 自动排序和格式化 import 语句
   - 使用 Google 风格配置

5. **Markdown 检查** (`markdownlint`)
   - 检查 Markdown 文件格式

## 📝 使用场景

### 日常开发

```bash
# 正常提交，hooks 会自动运行
git add .
git commit -m "feat: 添加新功能"

# 如果检查失败，修复后重新提交
# hooks 会自动修复一些简单问题（如格式化）
```

### 跳过 hooks（不推荐）

```bash
# 紧急情况下可以跳过（不推荐）
git commit --no-verify -m "紧急修复"
```

### 更新 hooks

```bash
# 更新到最新版本
pre-commit autoupdate
```

### 卸载 hooks

```bash
# 移除 Git hooks
pre-commit uninstall
```

## ⚙️ 自定义配置

### 修改检查规则

编辑 `.pre-commit-config.yaml`：

```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.1.15
    hooks:
      - id: ruff
        args: [--fix, --select=E,W,F]  # 只检查特定规则
```

### 排除特定文件

在 `.pre-commit-config.yaml` 中使用 `exclude`：

```yaml
- id: yapf
  exclude: ^(test/|.*test.*\.py)$  # 排除测试文件
```

### 添加新的 hooks

在 `.pre-commit-config.yaml` 的 `repos` 部分添加：

```yaml
repos:
  - repo: https://github.com/your-repo/your-hook
    rev: v1.0.0
    hooks:
      - id: your-hook-id
```

## 🐛 常见问题

### 1. yapf 版本错误：`error: pathspec 'v0.40.2' did not match any file(s) known to git`

**原因**：`pre-commit/mirrors-yapf` 仓库已归档，且没有该版本标签。

**解决方案**：
- 配置文件已更新为使用官方 `google/yapf` 仓库
- 如果仍有问题，运行 `pre-commit clean` 清理缓存后重新安装：
  ```bash
  pre-commit clean
  pre-commit install
  pre-commit run --all-files
  ```

### 2. hooks 运行太慢

**解决方案**：
- 只检查暂存的文件（默认行为）
- 使用 `ruff` 替代 `flake8`（更快）
- 排除不需要检查的目录

### 3. 某些检查总是失败

**解决方案**：
- 查看错误信息，修复代码问题
- 如果规则不适合项目，在配置中禁用该规则
- 使用 `--no-verify` 临时跳过（不推荐）

### 4. 格式化工具修改了代码

**解决方案**：
- 这是正常行为，格式化工具会自动修复代码风格
- 重新暂存修改后的文件：`git add .`
- 然后重新提交：`git commit`

### 5. 在 CI/CD 中运行

```yaml
# .github/workflows/pre-commit.yml
name: Pre-commit
on: [push, pull_request]
jobs:
  pre-commit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.12'
      - uses: pre-commit/action@v3.0.0
```

## 📚 相关资源

- [Pre-commit 官方文档](https://pre-commit.com/)
- [YAPF 文档](https://github.com/google/yapf)
- [Ruff 文档](https://docs.astral.sh/ruff/)
- [isort 文档](https://pycqa.github.io/isort/)

## 💡 最佳实践

1. **团队协作**：所有团队成员都应该安装并启用 pre-commit hooks
2. **CI/CD 集成**：在 CI/CD 流水线中也运行 pre-commit 检查
3. **定期更新**：使用 `pre-commit autoupdate` 保持工具最新
4. **不要跳过**：除非紧急情况，不要使用 `--no-verify`
5. **配置版本化**：将 `.pre-commit-config.yaml` 提交到版本控制

## 🔄 工作流程示例

```bash
# 1. 编写代码
vim app/main.py

# 2. 暂存文件
git add app/main.py

# 3. 提交（hooks 自动运行）
git commit -m "feat: 更新主程序"
# → yapf 自动格式化代码
# → ruff 检查代码问题
# → isort 排序导入
# → 其他检查...

# 4. 如果检查失败，修复后重新暂存和提交
git add app/main.py
git commit -m "feat: 更新主程序"
```

---

**提示**：首次运行 `pre-commit install` 后，建议运行 `pre-commit run --all-files` 检查所有现有文件。
