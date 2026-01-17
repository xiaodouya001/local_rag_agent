"""
错误处理工具类
统一处理API错误、解析错误信息、过滤敏感信息
"""

import logging
import re

from app.core.utils.common import sanitize_error_message


class ErrorHandler:
    """错误处理工具类"""

    def __init__(self,
                 logger: logging.Logger | None = None,
                 api_key: str | None = None):
        """
        初始化错误处理器

        Args:
            logger: 日志记录器
            api_key: API密钥（用于过滤敏感信息）
        """
        self.logger = logger or logging.getLogger(__name__)
        self.api_key = api_key

    def parse_error(self, error: Exception) -> str:
        """
        解析错误信息，提供友好的提示

        Args:
            error: 异常对象

        Returns:
            友好的错误提示
        """
        error_str = str(error)
        error_str_lower = error_str.lower()

        # 过滤敏感信息
        if self.api_key:
            error_str = sanitize_error_message(error_str, self.api_key)

        # API 余额不足
        if "insufficient balance" in error_str_lower or "402" in error_str:
            return "API 账户余额不足。请前往 DeepSeek 官网充值后重试。"

        # API 密钥错误
        if "401" in error_str or "unauthorized" in error_str_lower or "invalid api key" in error_str_lower:
            return "API 密钥无效或已过期。请检查 .env 文件中的 RAG_LLM_API_KEY 是否正确。"

        # 网络连接问题
        if "timeout" in error_str_lower or "timed out" in error_str_lower or "connection" in error_str_lower:
            return "网络连接超时。请检查网络连接后重试。"

        # 速率限制
        if "rate limit" in error_str_lower or "429" in error_str or "rate_limit" in error_str_lower:
            return "API 请求频率过高（免费版限制约5次/秒）。程序会自动重试，请稍候。"

        # 模型不可用
        if "model" in error_str_lower and ("not found" in error_str_lower or
                                           "unavailable" in error_str_lower):
            return "指定的模型不可用。请检查模型名称是否正确。"

        # 提取错误代码和主要信息
        if "error code:" in error_str:
            code_match = re.search(r'error code:\s*(\d+)', error_str,
                                   re.IGNORECASE)
            message_match = re.search(r"'message':\s*'([^']+)'", error_str)

            if code_match and message_match:
                code = code_match.group(1)
                message = message_match.group(1)
                return f"API 错误 (代码 {code}): {message}"

        # 默认返回原始错误，但截断过长的错误信息
        if len(error_str) > 200:
            return error_str[:200] + "..."

        return error_str

    def classify_error(self, error: Exception) -> str:
        """
        分类错误类型

        Args:
            error: 异常对象

        Returns:
            错误类型：'rate_limit', 'timeout', 'auth', 'balance', 'other'
        """
        error_str = str(error).lower()

        if "429" in str(
                error
        ) or "rate limit" in error_str or "rate_limit" in error_str:
            return "rate_limit"
        elif "timeout" in error_str or "timed out" in error_str:
            return "timeout"
        elif "401" in str(
                error
        ) or "unauthorized" in error_str or "invalid api key" in error_str:
            return "auth"
        elif "402" in str(error) or "insufficient balance" in error_str:
            return "balance"
        else:
            return "other"
