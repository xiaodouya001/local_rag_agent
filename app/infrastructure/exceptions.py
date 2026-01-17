"""
RAG Agent 自定义异常类
"""


class RAGAgentError(Exception):
    """RAG Agent 基础异常类"""
    pass


class ConfigurationError(RAGAgentError):
    """配置错误"""
    pass


class DocumentLoadError(RAGAgentError):
    """文档加载错误"""
    pass


class VectorStoreError(RAGAgentError):
    """向量存储错误"""
    pass


class APIError(RAGAgentError):
    """API调用错误"""
    pass


class RateLimitError(APIError):
    """API速率限制错误"""
    pass


class AuthenticationError(APIError):
    """API认证错误"""
    pass


class InsufficientBalanceError(APIError):
    """API余额不足错误"""
    pass


class TimeoutError(APIError):
    """API超时错误"""
    pass


class ModelLoadError(RAGAgentError):
    """模型加载错误"""
    pass
