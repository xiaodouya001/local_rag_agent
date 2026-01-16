"""
RAG Agent 配置管理模块
使用 dataclass 管理配置，支持环境变量和验证
"""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

load_dotenv()


@dataclass
class RAGConfig:
    """RAG Agent 配置类"""
    
    # 向量存储配置
    persist_directory: str = "./chroma_db"
    
    # 模型配置
    embedding_model: str = "all-MiniLM-L6-v2"
    llm_model: str = "deepseek-chat"
    
    # 文档分块配置
    chunk_size: int = 1000
    chunk_overlap: int = 200
    
    # API配置
    base_url: Optional[str] = None
    api_key: Optional[str] = None
    
    # LLM参数
    temperature: float = 0.7
    max_tokens: int = 2000
    timeout: int = 60
    
    # 重试配置
    max_retries: int = 3
    retry_wait_base: int = 2  # 基础等待时间（秒）
    
    # 检索配置
    default_k: int = 4  # 默认检索文档数量
    
    # 支持的文件类型
    supported_file_types: list = field(default_factory=lambda: ['.pdf', '.txt'])
    
    def __post_init__(self):
        """配置验证和规范化"""
        # 验证 chunk_size
        if self.chunk_size <= 0 or self.chunk_size > 10000:
            raise ValueError(
                f"chunk_size 必须在 1-10000 之间，当前值: {self.chunk_size}"
            )
        
        # 验证 chunk_overlap
        if self.chunk_overlap < 0 or self.chunk_overlap >= self.chunk_size:
            raise ValueError(
                f"chunk_overlap 必须小于 chunk_size，当前值: {self.chunk_overlap}"
            )
        
        # 验证 temperature
        if not 0.0 <= self.temperature <= 2.0:
            raise ValueError(
                f"temperature 必须在 0.0-2.0 之间，当前值: {self.temperature}"
            )
        
        # 规范化路径
        self.persist_directory = str(Path(self.persist_directory).resolve())
        
        # 从环境变量加载 API 配置（如果未提供）
        if not self.base_url:
            self.base_url = os.getenv(
                "DEEPSEEK_API_BASE", 
                "https://api.deepseek.com/v1"
            )
        
        if not self.api_key:
            self.api_key = os.getenv("DEEPSEEK_API_KEY")
            if not self.api_key:
                raise ValueError(
                    "未找到 DEEPSEEK_API_KEY，请在 .env 文件中设置或通过参数传入"
                )
        
        # 验证 API 密钥格式（基本检查）
        if len(self.api_key) < 10:
            raise ValueError("API 密钥格式无效（长度过短）")
    
    @classmethod
    def from_env(cls, **overrides) -> 'RAGConfig':
        """
        从环境变量创建配置
        
        Args:
            **overrides: 覆盖默认值的参数
            
        Returns:
            RAGConfig 实例
        """
        return cls(
            persist_directory=overrides.get(
                'persist_directory',
                os.getenv('RAG_PERSIST_DIR', './chroma_db')
            ),
            embedding_model=overrides.get(
                'embedding_model',
                os.getenv('EMBEDDING_MODEL', 'all-MiniLM-L6-v2')
            ),
            llm_model=overrides.get(
                'llm_model',
                os.getenv('LLM_MODEL', 'deepseek-chat')
            ),
            chunk_size=int(overrides.get(
                'chunk_size',
                os.getenv('CHUNK_SIZE', '1000')
            )),
            chunk_overlap=int(overrides.get(
                'chunk_overlap',
                os.getenv('CHUNK_OVERLAP', '200')
            )),
            temperature=float(overrides.get(
                'temperature',
                os.getenv('TEMPERATURE', '0.7')
            )),
            max_tokens=int(overrides.get(
                'max_tokens',
                os.getenv('MAX_TOKENS', '2000')
            )),
            timeout=int(overrides.get(
                'timeout',
                os.getenv('API_TIMEOUT', '60')
            )),
            max_retries=int(overrides.get(
                'max_retries',
                os.getenv('MAX_RETRIES', '3')
            )),
            **{k: v for k, v in overrides.items() 
               if k not in ['persist_directory', 'embedding_model', 'llm_model', 
                           'chunk_size', 'chunk_overlap', 'temperature', 
                           'max_tokens', 'timeout', 'max_retries']}
        )
