"""
RAG Agent 应用包
"""

__version__ = "1.2.0"

# 向后兼容导入（推荐使用新的导入路径）
from app.application import RAGAgent
from app.infrastructure import ConfigurationError
from app.infrastructure import DocumentLoadError
from app.infrastructure import RAGConfig
from app.infrastructure import setup_logging
from app.infrastructure import VectorStoreError

__all__ = [
    'RAGAgent',
    'RAGConfig',
    'ConfigurationError',
    'DocumentLoadError',
    'VectorStoreError',
    'setup_logging',
]
