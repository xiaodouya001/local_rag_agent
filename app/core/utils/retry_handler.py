"""
重试机制工具类
处理API调用的重试逻辑
"""

import time
import logging
from typing import Callable, TypeVar, Optional, Any
from functools import wraps

T = TypeVar('T')


class RetryHandler:
    """重试处理器"""
    
    def __init__(
        self,
        max_retries: int = 3,
        retry_wait_base: int = 2,
        logger: Optional[logging.Logger] = None
    ):
        """
        初始化重试处理器
        
        Args:
            max_retries: 最大重试次数
            retry_wait_base: 基础等待时间（秒）
            logger: 日志记录器
        """
        self.max_retries = max_retries
        self.retry_wait_base = retry_wait_base
        self.logger = logger or logging.getLogger(__name__)
    
    def retry_with_backoff(
        self,
        func: Callable[..., T],
        error_classifier: Optional[Callable[[Exception], str]] = None,
        *args,
        **kwargs
    ) -> T:
        """
        带指数退避的重试机制
        
        Args:
            func: 要执行的函数
            error_classifier: 错误分类函数，返回 'rate_limit', 'timeout', 'auth', 'balance', 'other'
            *args: 函数位置参数
            **kwargs: 函数关键字参数
            
        Returns:
            函数返回值
            
        Raises:
            最后一次尝试的异常
        """
        last_exception = None
        
        for attempt in range(self.max_retries):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                
                # 如果提供了错误分类器，使用它来判断是否应该重试
                if error_classifier:
                    error_type = error_classifier(e)
                    
                    # 认证错误和余额不足不重试
                    if error_type in ('auth', 'balance'):
                        raise
                    
                    # 速率限制错误，等待后重试
                    if error_type == 'rate_limit':
                        if attempt < self.max_retries - 1:
                            wait_time = (attempt + 1) * self.retry_wait_base
                            self.logger.warning(
                                f"遇到速率限制，等待 {wait_time} 秒后重试... "
                                f"(尝试 {attempt + 1}/{self.max_retries})"
                            )
                            time.sleep(wait_time)
                            continue
                        else:
                            self.logger.error("达到最大重试次数，速率限制错误")
                            raise
                
                # 如果是最后一次尝试，直接抛出异常
                if attempt == self.max_retries - 1:
                    raise
                
                # 其他错误，等待后重试
                wait_time = (attempt + 1) * self.retry_wait_base
                self.logger.warning(
                    f"执行失败，等待 {wait_time} 秒后重试... "
                    f"(尝试 {attempt + 1}/{self.max_retries})"
                )
                time.sleep(wait_time)
        
        # 如果所有重试都失败
        if last_exception:
            raise last_exception
        
        raise RuntimeError("重试机制异常：未捕获到异常但重试失败")
