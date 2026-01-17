# .env 文件最佳实践

## 位置

### ✅ 推荐：项目根目录

`.env` 文件应该放在**项目根目录**（与 `pyproject.toml`、`README.md` 同级）：

```
local_rag_agent/
├── .env                    # ✅ 放在这里
├── .env.example            # ✅ 示例文件也放在这里
├── .gitignore
├── pyproject.toml
├── README.md
├── app/
│   └── ...
└── ...
```

### 为什么放在根目录？

1. **`pydantic-settings` 的行为**：
   - `env_file=".env"` 使用相对路径时，从**当前工作目录**查找
   - 运行脚本时，工作目录通常是项目根目录

2. **`load_dotenv()` 的行为**：
   - 默认调用 `find_dotenv()`，从脚本所在目录**向上查找**
   - 最终会在项目根目录找到 `.env` 文件

3. **行业标准**：
   - 符合 12-factor app 原则
   - 大多数 Python 项目都遵循此约定
   - 便于团队协作和 CI/CD 配置

## 配置说明

### 当前配置

```python
# app/infrastructure/config.py
model_config = SettingsConfigDict(
    env_file=".env",  # 相对路径，从项目根目录查找
    env_file_encoding="utf-8",
)
```

### 查找顺序

1. **`pydantic-settings`**：
   - 从当前工作目录查找 `.env` 文件
   - 如果不存在，静默忽略，继续从系统环境变量读取

2. **`load_dotenv()`**：
   - 从脚本所在目录向上查找 `.env` 文件
   - 如果不存在，静默失败，不影响程序运行

## 使用方式

### 开发环境

```bash
# 1. 复制示例文件
cp .env.example .env

# 2. 编辑 .env 文件
# RAG_LLM_API_KEY=your-actual-api-key
```

### 生产环境

**选项 1：使用 `.env` 文件**
```bash
# 在服务器上创建 .env 文件
nano .env
```

**选项 2：使用系统环境变量**
```bash
# 设置系统环境变量
export RAG_LLM_API_KEY=your-api-key
# 不需要 .env 文件
```

## 文件管理

### `.env` 文件
- ✅ **不提交**到版本控制（已在 `.gitignore` 中）
- ✅ 包含敏感信息（API 密钥等）
- ✅ 每个开发者/环境可以有不同的配置

### `.env.example` 文件
- ✅ **提交**到版本控制
- ✅ 作为配置模板
- ✅ 不包含敏感信息

## 总结

- **位置**：项目根目录（`local_rag_agent/.env`）
- **必需性**：可选，但推荐使用
- **安全性**：已在 `.gitignore` 中，不会被提交
- **灵活性**：支持 `.env` 文件或系统环境变量
