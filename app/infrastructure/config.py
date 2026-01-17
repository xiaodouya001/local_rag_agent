"""
RAG Agent 配置管理模块
使用 pydantic-settings 管理配置，支持环境变量和验证
遵循行业最佳实践：统一配置读取、类型验证、环境变量前缀
"""

from pathlib import Path

from pydantic import Field
from pydantic import field_validator
from pydantic_settings import BaseSettings
from pydantic_settings import SettingsConfigDict


class RAGConfig(BaseSettings):
    """
    RAG Agent 配置类

    使用 pydantic-settings 自动从环境变量读取配置
    所有环境变量使用 RAG_ 前缀，并在其后添加具体类别名称
    格式：RAG_{类别}_{配置项}

    配置类别：
    - LLM_*：LLM API 和参数相关（如 RAG_LLM_API_KEY、RAG_LLM_TEMPERATURE）
    - EMBEDDING_*：嵌入模型相关（如 RAG_EMBEDDING_MODEL）
    - DOCUMENT_*：文档处理相关（如 RAG_DOCUMENT_CHUNK_SIZE）
    - RETRIEVER_*：检索器相关（如 RAG_RETRIEVER_DEFAULT_K）
    - VECTORSTORE_*：向量存储相关（如 RAG_VECTORSTORE_PERSIST_DIRECTORY）

    配置优先级（从高到低）：
    1. 代码中直接传入的参数
    2. 环境变量（.env 文件或系统环境变量）
    3. 默认值（代码中定义）

    Example:
        >>> # 从环境变量创建（推荐）
        >>> config = RAGConfig()
        >>>
        >>> # 覆盖特定配置
        >>> config = RAGConfig(api_key="custom-key")
        >>>
        >>> # 从 .env 文件自动读取（如果存在）
    """

    model_config = SettingsConfigDict(
        env_prefix="RAG_",  # 保留用于兼容性（实际使用 validation_alias 指定完整名称）
        env_file=".env",  # 自动从 .env 文件读取
        env_file_encoding="utf-8",
        case_sensitive=False,  # 环境变量不区分大小写
        extra="ignore",  # 忽略未定义的字段
    )

    # ============================================================================
    # 向量存储配置
    # ============================================================================
    persist_directory: str = Field(
        default="./chroma_db",
        validation_alias="RAG_VECTORSTORE_PERSIST_DIRECTORY",
        description="向量数据库持久化目录路径")

    # ============================================================================
    # 模型配置
    # ============================================================================
    embedding_model: str = Field(
        default="all-MiniLM-L6-v2",
        validation_alias="RAG_EMBEDDING_MODEL",
        description="嵌入模型名称（HuggingFace）")

    llm_model: str = Field(
        default="deepseek-chat",
        validation_alias="RAG_LLM_MODEL",
        description="大语言模型名称")

    # ============================================================================
    # 文档分块配置
    # ============================================================================
    chunk_size: int = Field(
        default=1000,
        validation_alias="RAG_DOCUMENT_CHUNK_SIZE",
        ge=1,
        le=10000,
        description="文档分块大小（字符数）")

    chunk_overlap: int = Field(
        default=200,
        validation_alias="RAG_DOCUMENT_CHUNK_OVERLAP",
        ge=0,
        description="文档分块重叠大小（字符数）")

    # ============================================================================
    # LLM API 配置
    # ============================================================================
    base_url: str = Field(
        default="https://api.deepseek.com/v1",
        validation_alias="RAG_LLM_API_BASE",
        description="DeepSeek API 基础 URL")

    api_key: str = Field(
        ...,
        validation_alias="RAG_LLM_API_KEY",
        min_length=10,
        description="DeepSeek API 密钥（必填，通过环境变量 RAG_LLM_API_KEY 设置）")

    # ============================================================================
    # LLM 参数
    # ============================================================================
    temperature: float = Field(
        default=0.7,
        validation_alias="RAG_LLM_TEMPERATURE",
        ge=0.0,
        le=2.0,
        description="LLM 温度参数（控制随机性）")

    max_tokens: int = Field(
        default=2000,
        validation_alias="RAG_LLM_MAX_TOKENS",
        ge=1,
        description="LLM 最大生成 token 数")

    timeout: int = Field(
        default=60,
        validation_alias="RAG_LLM_TIMEOUT",
        ge=1,
        description="LLM API 请求超时时间（秒）")

    # ============================================================================
    # LLM 重试配置
    # ============================================================================
    max_retries: int = Field(
        default=3,
        validation_alias="RAG_LLM_MAX_RETRIES",
        ge=0,
        description="LLM API 请求最大重试次数")

    retry_wait_base: int = Field(
        default=2,
        validation_alias="RAG_LLM_RETRY_WAIT_BASE",
        ge=0,
        description="LLM API 重试基础等待时间（秒）")

    # ============================================================================
    # 检索配置
    # ============================================================================
    default_k: int = Field(
        default=10,
        validation_alias="RAG_RETRIEVER_DEFAULT_K",
        ge=1,
        description="默认检索文档块数量")

    # ============================================================================
    # 文件类型配置
    # ============================================================================
    supported_file_types: list[str] = Field(
        default_factory=lambda: ['.pdf', '.txt'],
        validation_alias="RAG_DOCUMENT_SUPPORTED_FILE_TYPES",
        description="支持的文件类型列表")

    # ============================================================================
    # 验证器
    # ============================================================================
    @field_validator('chunk_overlap')
    @classmethod
    def validate_chunk_overlap(cls, v: int, info) -> int:
        """验证 chunk_overlap 必须小于 chunk_size"""
        if 'chunk_size' in info.data and v >= info.data['chunk_size']:
            raise ValueError(
                f"chunk_overlap ({v}) 必须小于 chunk_size ({info.data['chunk_size']})")
        return v

    @field_validator('persist_directory')
    @classmethod
    def normalize_persist_directory(cls, v: str) -> str:
        """规范化持久化目录路径"""
        return str(Path(v).resolve())

    # ============================================================================
    # 属性方法
    # ============================================================================
    @property
    def persist_directory_resolved(self) -> Path:
        """获取解析后的持久化目录路径（Path 对象）"""
        return Path(self.persist_directory).resolve()

    def model_post_init(self, __context) -> None:
        """
        配置初始化后的处理

        在 pydantic 验证完成后执行，用于额外的验证和规范化
        """
        # 验证 chunk_overlap < chunk_size（如果两者都已设置）
        if self.chunk_overlap >= self.chunk_size:
            raise ValueError(
                f"chunk_overlap ({self.chunk_overlap}) 必须小于 chunk_size ({self.chunk_size})")

    # ============================================================================
    # 便捷方法
    # ============================================================================
    @classmethod
    def from_env(cls, **overrides) -> 'RAGConfig':
        """
        从环境变量创建配置（便捷方法）

        注意：直接实例化 RAGConfig() 即可自动从环境变量读取
        此方法提供与直接实例化相同的功能，可用于代码可读性

        Args:
            **overrides: 覆盖默认值的参数

        Returns:
            RAGConfig 实例

        Example:
            >>> # 方式1：直接实例化（推荐）
            >>> config = RAGConfig()
            >>>
            >>> # 方式2：使用 from_env（功能相同）
            >>> config = RAGConfig.from_env(api_key="custom-key")
        """
        return cls(**overrides)
