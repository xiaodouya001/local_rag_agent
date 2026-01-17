"""
向量存储管理器
负责创建、加载和管理向量存储
"""

import logging
from pathlib import Path

try:
    from langchain_chroma import Chroma
except ImportError:
    from langchain_community.vectorstores import Chroma

from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings

from app.infrastructure import VectorStoreError


class VectorStoreManager:
    """向量存储管理器"""

    def __init__(self,
                 persist_directory: str,
                 embeddings: Embeddings,
                 logger: logging.Logger | None = None):
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
        self._vectorstore: Chroma | None = None

    @property
    def vectorstore(self) -> Chroma | None:
        """获取向量存储实例"""
        return self._vectorstore

    def create(self,
               documents: list[Document],
               collection_name: str = "rag_collection") -> None:
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
                collection_name=collection_name)

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
        faiss_files = list(self.persist_directory.glob("*.faiss")) + list(
            self.persist_directory.glob("*.pkl"))
        if faiss_files:
            self.logger.warning(f"检测到旧的 FAISS 文件: {faiss_files}。"
                                "这些文件与 ChromaDB 不兼容，建议删除后重新创建向量存储。")

        self.logger.info(
            f"正在从 {self.persist_directory} 加载向量存储（collection: {collection_name}）..."
        )

        try:
            # 使用 ChromaDB 加载向量存储
            self._vectorstore = Chroma(persist_directory=str(
                self.persist_directory),
                                       embedding_function=self.embeddings,
                                       collection_name=collection_name)

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

    def get_existing_files(self) -> dict[str, dict]:
        """
        获取向量存储中已存在的文件信息

        Returns:
            字典，key 为文件名，value 为文件信息（包含 file_hash, modified_time 等）
        """
        if self._vectorstore is None:
            return {}

        try:
            collection = self._vectorstore._collection
            # 获取所有文档的 metadata
            results = collection.get(include=['metadatas'])

            if not results or 'metadatas' not in results:
                return {}

            existing_files = {}
            metadatas = results.get('metadatas', [])
            ids = results.get('ids', [])

            for idx, metadata in enumerate(metadatas):
                if not metadata:
                    continue

                filename = metadata.get('filename')
                if not filename:
                    # 如果没有 filename，尝试从 source 提取
                    source = metadata.get('source', '')
                    if source:
                        filename = Path(source).name

                if filename:
                    file_hash = metadata.get('file_hash', '')
                    modified_time = metadata.get('modified_time', 0)

                    # 如果已存在同名文件，保留最新的（modified_time 更大的）
                    if filename not in existing_files:
                        existing_files[filename] = {
                            'file_hash': file_hash,
                            'modified_time': modified_time,
                            'source': metadata.get('source', ''),
                            'ids': [ids[idx]] if idx < len(ids) else []
                        }
                    else:
                        # 比较修改时间，保留更新的
                        if modified_time > existing_files[filename]['modified_time']:
                            existing_files[filename] = {
                                'file_hash': file_hash,
                                'modified_time': modified_time,
                                'source': metadata.get('source', ''),
                                'ids': [ids[idx]] if idx < len(ids) else []
                            }
                        else:
                            # 保留旧的，但添加当前 id 到列表
                            if idx < len(ids):
                                existing_files[filename]['ids'].append(ids[idx])

            return existing_files
        except Exception as e:
            self.logger.warning(f"获取已存在文件信息失败: {e}")
            return {}

    def delete_documents_by_filename(self, filename: str) -> int:
        """
        根据文件名删除向量存储中的文档

        Args:
            filename: 文件名

        Returns:
            删除的文档块数量
        """
        if self._vectorstore is None:
            return 0

        try:
            collection = self._vectorstore._collection

            # 获取所有文档的 ids 和 metadatas
            results = collection.get(include=['metadatas'])

            if not results or 'metadatas' not in results:
                return 0

            ids_to_delete = []
            metadatas = results.get('metadatas', [])
            ids = results.get('ids', [])

            for idx, metadata in enumerate(metadatas):
                if not metadata:
                    continue

                doc_filename = metadata.get('filename')
                if not doc_filename:
                    # 如果没有 filename，尝试从 source 提取
                    source = metadata.get('source', '')
                    if source:
                        doc_filename = Path(source).name

                if doc_filename == filename and idx < len(ids):
                    ids_to_delete.append(ids[idx])

            if ids_to_delete:
                collection.delete(ids=ids_to_delete)
                self.logger.info(f"删除了 {len(ids_to_delete)} 个文档块（文件: {filename}）")
                return len(ids_to_delete)

            return 0
        except Exception as e:
            self.logger.warning(f"删除文档失败（文件: {filename}）: {e}")
            return 0

    def add_documents(self,
                      documents: list[Document],
                      collection_name: str = "rag_collection",
                      incremental: bool = True) -> dict[str, int]:
        """
        向现有向量存储添加新文档（支持增量添加和去重）

        Args:
            documents: 文档列表（应该是已经分割后的文档块）
            collection_name: 集合名称
            incremental: 是否启用增量模式（检查新文件，删除旧版本）

        Returns:
            字典，包含添加的文档数量、删除的文档数量等信息

        Raises:
            VectorStoreError: 添加文档失败
            ValueError: 文档列表为空或向量存储未初始化
        """
        if not documents:
            raise ValueError("文档列表为空")

        # 如果向量存储未加载，先加载它
        if self._vectorstore is None:
            self.logger.info("向量存储未加载，正在加载...")
            self.load(collection_name)

        if self._vectorstore is None:
            raise VectorStoreError("无法加载向量存储")

        result = {
            'added_files': 0,
            'updated_files': 0,
            'deleted_chunks': 0,
            'added_chunks': 0
        }

        try:
            if incremental:
                # 获取已存在的文件信息
                existing_files = self.get_existing_files()

                # 按文件名分组新文档
                new_docs_by_file: dict[str, list[Document]] = {}
                for doc in documents:
                    filename = doc.metadata.get('filename', '')
                    if not filename:
                        # 如果没有 filename，尝试从 source 提取
                        source = doc.metadata.get('source', '')
                        if source:
                            filename = Path(source).name

                    if filename:
                        if filename not in new_docs_by_file:
                            new_docs_by_file[filename] = []
                        new_docs_by_file[filename].append(doc)

                # 处理每个文件
                docs_to_add = []
                for filename, file_docs in new_docs_by_file.items():
                    if not file_docs:
                        continue

                    # 获取文件的 metadata（使用第一个文档的 metadata）
                    file_metadata = file_docs[0].metadata
                    file_hash = file_metadata.get('file_hash', '')
                    modified_time = file_metadata.get('modified_time', 0)

                    if filename in existing_files:
                        # 文件已存在，检查是否需要更新
                        existing_info = existing_files[filename]
                        existing_hash = existing_info.get('file_hash', '')
                        existing_time = existing_info.get('modified_time', 0)

                        # 如果文件已更新（hash 不同或修改时间更新），删除旧版本
                        if file_hash != existing_hash or modified_time > existing_time:
                            deleted_count = self.delete_documents_by_filename(filename)
                            result['deleted_chunks'] += deleted_count
                            result['updated_files'] += 1
                            self.logger.info(f"文件已更新: {filename} (旧版本已删除)")
                            docs_to_add.extend(file_docs)
                        else:
                            # 文件未更新，跳过
                            self.logger.debug(f"文件未更新，跳过: {filename}")
                    else:
                        # 新文件
                        result['added_files'] += 1
                        self.logger.info(f"新文件: {filename}")
                        docs_to_add.extend(file_docs)

                if not docs_to_add:
                    self.logger.info("没有新文档或更新的文档需要添加")
                    return result

                documents = docs_to_add
            else:
                # 非增量模式，直接添加所有文档
                result['added_files'] = len({doc.metadata.get('filename', '') for doc in documents})

            self.logger.info(f"正在向向量存储添加 {len(documents)} 个文档块...")

            # 使用 add_documents 方法添加新文档
            self._vectorstore.add_documents(documents)
            result['added_chunks'] = len(documents)

            # 记录添加的文档文件名
            if documents:
                filenames = set()
                for doc in documents:
                    filename = doc.metadata.get('filename', '')
                    if not filename:
                        source = doc.metadata.get('source', '')
                        if source:
                            filename = Path(source).name
                    if filename:
                        filenames.add(filename)

                if filenames:
                    self.logger.info(f"添加的文档文件: {', '.join(sorted(filenames))}")

            # 获取更新后的文档数量
            try:
                collection = self._vectorstore._collection
                count = collection.count()
                self.logger.info(
                    f"成功添加文档，向量存储现在包含 {count} 个文档块")
            except Exception as e:
                self.logger.warning(f"无法获取向量存储统计信息: {e}")
                self.logger.info("文档添加完成（无法验证数据）")

        except Exception as e:
            error_msg = f"添加文档到向量存储失败: {e}"
            self.logger.error(error_msg, exc_info=True)
            raise VectorStoreError(error_msg) from e

        return result

    def exists(self) -> bool:
        """检查向量存储是否存在"""
        return self.persist_directory.exists() and self._vectorstore is not None

    def get_document_count(self) -> int | None:
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
