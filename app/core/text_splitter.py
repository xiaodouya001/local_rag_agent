"""
文本分割器
负责将文档分割成小块
"""

import logging
from typing import List, Optional

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

from app.exceptions import VectorStoreError


class TextSplitter:
    """文本分割器"""
    
    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        logger: Optional[logging.Logger] = None
    ):
        """
        初始化文本分割器
        
        Args:
            chunk_size: 文档分块大小
            chunk_overlap: 文档分块重叠大小
            logger: 日志记录器
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.logger = logger or logging.getLogger(__name__)
        
        self._splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
        )
    
    def split_documents(self, documents: List[Document]) -> List[Document]:
        """
        分割文档列表
        
        Args:
            documents: 文档列表
            
        Returns:
            分割后的文档块列表
            
        Raises:
            VectorStoreError: 文档分割失败
        """
        if not documents:
            raise ValueError("文档列表为空")
        
        self.logger.info("正在分割文档...")
        
        try:
            texts = self._splitter.split_documents(documents)
            self.logger.info(f"文档已分割为 {len(texts)} 个块")
            return texts
        except Exception as e:
            error_msg = f"文档分割失败: {e}"
            self.logger.error(error_msg, exc_info=True)
            raise VectorStoreError(error_msg) from e
