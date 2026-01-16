"""
LLM包装器
封装LLM的初始化和调用
"""

import logging
from typing import Optional

from langchain_openai import ChatOpenAI

from app.exceptions import ModelLoadError


class LLMWrapper:
    """LLM包装器"""
    
    def __init__(
        self,
        model: str,
        base_url: str,
        api_key: str,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        timeout: int = 60,
        max_retries: int = 3,
        logger: Optional[logging.Logger] = None
    ):
        """
        初始化LLM包装器
        
        Args:
            model: 模型名称
            base_url: API基础URL
            api_key: API密钥
            temperature: 温度参数
            max_tokens: 最大token数
            timeout: 超时时间（秒）
            max_retries: 最大重试次数
            logger: 日志记录器
            
        Raises:
            ModelLoadError: LLM初始化失败
        """
        self.model = model
        self.base_url = base_url
        self.api_key = api_key
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.timeout = timeout
        self.max_retries = max_retries
        self.logger = logger or logging.getLogger(__name__)
        
        self._llm: Optional[ChatOpenAI] = None
        self._initialize()
    
    def _initialize(self) -> None:
        """初始化LLM"""
        self.logger.info(f"正在初始化LLM: {self.model}")
        
        try:
            self._llm = ChatOpenAI(
                model=self.model,
                base_url=self.base_url,
                api_key=self.api_key,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                timeout=self.timeout,
                max_retries=self.max_retries
            )
            self.logger.info("LLM初始化成功")
        except Exception as e:
            error_msg = f"初始化LLM失败: {e}"
            self.logger.error(error_msg, exc_info=True)
            raise ModelLoadError(error_msg) from e
    
    @property
    def llm(self) -> ChatOpenAI:
        """获取LLM实例"""
        if self._llm is None:
            raise ModelLoadError("LLM未初始化")
        return self._llm
    
    def invoke(self, prompt: str) -> str:
        """
        调用LLM生成回答
        
        Args:
            prompt: 提示文本
            
        Returns:
            LLM生成的回答
        """
        return self.llm.invoke(prompt).content
