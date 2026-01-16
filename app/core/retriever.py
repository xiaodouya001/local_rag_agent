"""
检索器
负责从向量存储中检索相关文档
"""

import logging
from typing import List, Optional

from langchain_core.documents import Document
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from langchain_core.vectorstores import VectorStore
else:
    # 运行时使用Any类型，避免导入问题
    from typing import Any as VectorStore

from app.exceptions import VectorStoreError


class Retriever:
    """检索器"""
    
    def __init__(
        self,
        vectorstore,  # VectorStore类型，但使用动态类型避免导入问题
        k: int = 4,
        logger: Optional[logging.Logger] = None
    ):
        """
        初始化检索器
        
        Args:
            vectorstore: 向量存储实例
            k: 检索的文档块数量
            logger: 日志记录器
        """
        if vectorstore is None:
            raise ValueError("向量存储未初始化")
        
        self.vectorstore = vectorstore
        self.k = k
        self.logger = logger or logging.getLogger(__name__)
        
        # 创建检索器
        self._langchain_retriever = self.vectorstore.as_retriever(
            search_type="similarity",
            search_kwargs={"k": k}
        )
    
    def retrieve(self, query: str) -> List[Document]:
        """
        检索相关文档
        
        Args:
            query: 查询文本
            
        Returns:
            相关文档列表
        """
        try:
            documents = self._langchain_retriever.invoke(query)
            
            if not documents:
                self.logger.warning(f"检索器没有找到任何相关文档（问题: {query}）")
            else:
                self.logger.info(f"检索到 {len(documents)} 个相关文档块")
            
            return documents
        except Exception as e:
            error_msg = f"检索失败: {e}"
            self.logger.error(error_msg, exc_info=True)
            raise VectorStoreError(error_msg) from e
    
    def similarity_search(self, query: str, k: Optional[int] = None) -> List[Document]:
        """
        相似度搜索
        
        Args:
            query: 查询文本
            k: 返回的文档数量（如果未提供则使用默认值）
            
        Returns:
            相似文档列表
        """
        k = k or self.k
        return self.vectorstore.similarity_search(query, k=k)
    
    def update_k(self, k: int) -> None:
        """
        更新检索数量
        
        Args:
            k: 新的检索数量
        """
        self.k = k
        self._langchain_retriever = self.vectorstore.as_retriever(
            search_type="similarity",
            search_kwargs={"k": k}
        )
