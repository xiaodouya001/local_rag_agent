"""
文本分割器
负责将文档分割成小块
"""

from collections import defaultdict
import logging

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.infrastructure import VectorStoreError


class TextSplitter:
    """文本分割器"""

    def __init__(self,
                 chunk_size: int = 1000,
                 chunk_overlap: int = 200,
                 logger: logging.Logger | None = None):
        """
        初始化文本分割器

        Args:
            chunk_size: 文档分块大小（字符数）
            chunk_overlap: 文档分块重叠大小（字符数）
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

    def split_documents(self, documents: list[Document]) -> list[Document]:
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
            # 按源文件分组，以便统计每个文件被分割成了多少块
            source_chunks = defaultdict(list)

            texts = self._splitter.split_documents(documents)

            # 统计每个源文件的块数
            for chunk in texts:
                source = chunk.metadata.get('source', 'unknown')
                source_chunks[source].append(chunk)

            # 输出详细的统计信息
            self.logger.info(f"文档已分割为 {len(texts)} 个块（来自 {len(documents)} 个原始文档）")
            self.logger.info(f"分块配置：chunk_size={self.chunk_size}, chunk_overlap={self.chunk_overlap}")

            # 显示每个文件的块数统计
            if len(source_chunks) > 0:
                self.logger.info("每个文件的块数统计：")
                for source, chunks in sorted(source_chunks.items()):
                    # 提取文件名（去掉路径）
                    filename = source.split('/')[-1] if '/' in source else source.split('\\')[-1]
                    self.logger.info(f"  - {filename}: {len(chunks)} 个块")

            return texts
        except Exception as e:
            error_msg = f"文档分割失败: {e}"
            self.logger.error(error_msg, exc_info=True)
            raise VectorStoreError(error_msg) from e
