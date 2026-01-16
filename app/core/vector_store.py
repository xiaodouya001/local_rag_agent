"""
向量存储管理器
负责创建、加载和管理向量存储
"""

import logging
from typing import Optional, List
from pathlib import Path

try:
    from langchain_chroma import Chroma
except ImportError:
    from langchain_community.vectorstores import Chroma

from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings

from app.exceptions import VectorStoreError


class VectorStoreManager:
    """向量存储管理器"""
    
    def __init__(
        self,
        persist_directory: str,
        embeddings: Embeddings,
        logger: Optional[logging.Logger] = None
    ):
        """
        初始化向量存储管理器
        
        Args:
            persist_directory: 持久化目录
            embeddings: 嵌入模型
            logger: 日志记录器
        """
        self.persist_directory = Path(persist_directory)
        self.embeddings = embeddings
        self.logger = logger or logging.getLogger(__name__)
        self._vectorstore: Optional[Chroma] = None
    
    @property
    def vectorstore(self) -> Optional[Chroma]:
        """获取向量存储实例"""
        return self._vectorstore
    
    def create(
        self,
        documents: List[Document],
        collection_name: str = "rag_collection"
    ) -> None:
        """
        创建向量存储
        
        Args:
            documents: 文档列表（应该是已经分割后的文档块）
            collection_name: 集合名称
            
        Raises:
            VectorStoreError: 向量存储创建失败
            ValueError: 文档列表为空
        """
        if not documents:
            raise ValueError("文档列表为空")
        
        self.logger.info("正在创建向量存储...")
        
        try:
            # 确保目录存在
            self.persist_directory.mkdir(parents=True, exist_ok=True)
            
            # 使用 ChromaDB 创建向量存储
            self._vectorstore = Chroma.from_documents(
                documents=documents,
                embedding=self.embeddings,
                persist_directory=str(self.persist_directory),
                collection_name=collection_name
            )
            
            self.logger.info(f"向量存储已创建并保存到: {self.persist_directory}")
        except Exception as e:
            error_msg = f"创建向量存储失败: {e}"
            self.logger.error(error_msg, exc_info=True)
            raise VectorStoreError(error_msg) from e
    
    def load(self, collection_name: str = "rag_collection") -> None:
        """
        加载已存在的向量存储
        
        Args:
            collection_name: 集合名称
            
        Raises:
            VectorStoreError: 向量存储加载失败
            ValueError: 向量存储目录不存在
        """
        if not self.persist_directory.exists():
            raise ValueError(f"向量存储目录不存在: {self.persist_directory}")
        
        # 检查是否有旧的 FAISS 文件
        faiss_files = list(self.persist_directory.glob("*.faiss")) + list(self.persist_directory.glob("*.pkl"))
        if faiss_files:
            self.logger.warning(
                f"检测到旧的 FAISS 文件: {faiss_files}。"
                "这些文件与 ChromaDB 不兼容，建议删除后重新创建向量存储。"
            )
        
        self.logger.info(f"正在从 {self.persist_directory} 加载向量存储（collection: {collection_name}）...")
        
        try:
            # 使用 ChromaDB 加载向量存储
            self._vectorstore = Chroma(
                persist_directory=str(self.persist_directory),
                embedding_function=self.embeddings,
                collection_name=collection_name
            )
            
            # 验证向量存储是否有数据
            try:
                collection = self._vectorstore._collection
                count = collection.count()
                self.logger.info(f"向量存储加载完成，包含 {count} 个文档块")
                
                if count == 0:
                    self.logger.warning("向量存储为空！请重新创建向量存储。")
            except Exception as e:
                self.logger.warning(f"无法获取向量存储统计信息: {e}")
                self.logger.info("向量存储加载完成（无法验证数据）")
                
        except Exception as e:
            error_msg = f"加载向量存储失败: {e}"
            self.logger.error(error_msg, exc_info=True)
            raise VectorStoreError(error_msg) from e
    
    def exists(self) -> bool:
        """检查向量存储是否存在"""
        return self.persist_directory.exists() and self._vectorstore is not None
    
    def get_document_count(self) -> Optional[int]:
        """
        获取文档数量
        
        Returns:
            文档数量，如果无法获取则返回 None
        """
        if not self._vectorstore:
            return None
        
        try:
            collection = self._vectorstore._collection
            return collection.count()
        except Exception:
            return None
