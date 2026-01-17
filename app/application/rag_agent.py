"""
RAG (Retrieval-Augmented Generation) Agent - 重构版本
基于检索增强生成的AI Agent
核心逻辑与UI/业务逻辑分离
"""

import logging
import os
from typing import Any

# 在导入 huggingface_hub 相关模块之前设置环境变量
# 这样可以确保超时配置在模型下载时生效
if 'HF_HUB_DOWNLOAD_TIMEOUT_SECONDS' not in os.environ:
    os.environ['HF_HUB_DOWNLOAD_TIMEOUT_SECONDS'] = '120'
if 'HF_HUB_DOWNLOAD_RETRIES' not in os.environ:
    os.environ['HF_HUB_DOWNLOAD_RETRIES'] = '5'

from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings

from app.core import DocumentLoader
from app.core import LLMWrapper
from app.core import QAChainBuilder
from app.core import Retriever
from app.core import TextSplitter
from app.core import VectorStoreManager
from app.core.utils import ErrorHandler
from app.core.utils import RetryHandler
from app.core.utils.common import validate_api_key
from app.infrastructure import ConfigurationError
from app.infrastructure import ModelLoadError
from app.infrastructure import RAGConfig
from app.infrastructure import VectorStoreError

# LangChainException 不再需要，错误处理由工具类完成




class RAGAgent:
    """RAG Agent主类，负责协调各个核心组件"""

    def __init__(self,
                 persist_directory: str = "./chroma_db",
                 embedding_model: str = "all-MiniLM-L6-v2",
                 llm_model: str = "deepseek-chat",
                 chunk_size: int = 1000,
                 chunk_overlap: int = 200,
                 base_url: str | None = None,
                 api_key: str | None = None,
                 config: RAGConfig | None = None,
                 logger: logging.Logger | None = None):
        """
        初始化RAG Agent

        Args:
            persist_directory: 向量数据库持久化目录
            embedding_model: 嵌入模型名称
            llm_model: 大语言模型名称
            chunk_size: 文档分块大小
            chunk_overlap: 文档分块重叠大小
            base_url: DeepSeek API基础URL
            api_key: DeepSeek API密钥
            config: 配置对象（如果提供，将覆盖其他参数）
            logger: 日志记录器（如果未提供，将使用默认的 logger）

        Raises:
            ConfigurationError: 配置错误
            ModelLoadError: 模型加载失败
        """
        # 初始化 logger
        if logger is None:
            logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.logger = logger

        # 使用配置对象或创建新配置
        if config:
            self.config = config
        else:
            try:
                # 构建配置参数字典（只包含非 None 的值）
                config_kwargs = {}
                if persist_directory:
                    config_kwargs['persist_directory'] = persist_directory
                if embedding_model:
                    config_kwargs['embedding_model'] = embedding_model
                if llm_model:
                    config_kwargs['llm_model'] = llm_model
                if chunk_size:
                    config_kwargs['chunk_size'] = chunk_size
                if chunk_overlap is not None:
                    config_kwargs['chunk_overlap'] = chunk_overlap
                if base_url:
                    config_kwargs['base_url'] = base_url
                if api_key:
                    config_kwargs['api_key'] = api_key

                # 创建配置（自动从环境变量读取，参数会覆盖环境变量）
                self.config = RAGConfig(**config_kwargs)
            except Exception as e:
                # pydantic 可能抛出 ValidationError 或其他异常
                from pydantic import ValidationError
                if isinstance(e, ValidationError):
                    # 提取更友好的错误信息
                    errors = e.errors()
                    error_msg = "; ".join([f"{err['loc']}: {err['msg']}" for err in errors])
                    raise ConfigurationError(f"配置验证失败: {error_msg}") from e
                raise ConfigurationError(str(e)) from e

        # 验证 API 密钥格式
        if not validate_api_key(self.config.api_key):
            raise ConfigurationError("API 密钥格式无效")

        # 初始化嵌入模型
        self.logger.info(f"正在加载嵌入模型: {self.config.embedding_model}")
        try:
            self.embeddings = HuggingFaceEmbeddings(
                model_name=self.config.embedding_model,
                model_kwargs={'device': 'cpu'})
            self.logger.info("嵌入模型加载成功")
        except Exception as e:
            error_msg = f"加载嵌入模型失败: {e}"
            self.logger.error(error_msg, exc_info=True)
            # 提供更友好的错误提示
            error_str_lower = str(e).lower()
            if "timeout" in error_str_lower or "timed out" in error_str_lower:
                error_msg += (
                    "\n提示：模型下载超时，可能是网络连接问题。"
                    "\n建议："
                    "\n1. 检查网络连接，确保可以访问 HuggingFace Hub"
                    "\n2. 如果使用代理，请配置代理设置（设置 HTTP_PROXY/HTTPS_PROXY 环境变量）"
                    "\n3. 可以尝试使用 HuggingFace 镜像站点（设置 HF_ENDPOINT 环境变量）"
                    "\n4. 或者手动下载模型到本地缓存目录（~/.cache/huggingface/hub/）"
                    "\n5. 增加超时时间：设置环境变量 HF_HUB_DOWNLOAD_TIMEOUT_SECONDS=300"
                )
            raise ModelLoadError(error_msg) from e

        # 初始化核心组件
        self._document_loader = DocumentLoader(
            supported_file_types=self.config.supported_file_types,
            logger=self.logger)
        self._text_splitter = TextSplitter(
            chunk_size=self.config.chunk_size,
            chunk_overlap=self.config.chunk_overlap,
            logger=self.logger)
        self._vector_store_manager = VectorStoreManager(
            persist_directory=self.config.persist_directory,
            embeddings=self.embeddings,
            logger=self.logger)
        self._llm_wrapper = LLMWrapper(model=self.config.llm_model,
                                       base_url=self.config.base_url,
                                       api_key=self.config.api_key,
                                       temperature=self.config.temperature,
                                       max_tokens=self.config.max_tokens,
                                       timeout=self.config.timeout,
                                       max_retries=self.config.max_retries,
                                       logger=self.logger)

        # 工具类
        self._error_handler = ErrorHandler(logger=self.logger,
                                           api_key=self.config.api_key)
        self._retry_handler = RetryHandler(
            max_retries=self.config.max_retries,
            retry_wait_base=self.config.retry_wait_base,
            logger=self.logger)

        # 延迟初始化的组件
        self._retriever: Retriever | None = None
        self._qa_chain_builder: QAChainBuilder | None = None

    # 向后兼容的属性
    @property
    def retriever(self):
        """向后兼容：获取检索器（langchain retriever）"""
        if self._retriever is None:
            return None
        return self._retriever._langchain_retriever

    @property
    def qa_chain(self):
        """向后兼容：获取问答链"""
        if self._qa_chain_builder is None:
            return None
        return self._qa_chain_builder.qa_chain

    @property
    def vectorstore(self):
        """向后兼容：获取向量存储"""
        return self._vector_store_manager.vectorstore

    def load_documents(
            self,
            directory: str,
            file_types: list[str] | None = None,
            allow_temp_dir: bool = False) -> list[Document]:
        """
        从目录加载文档

        Args:
            directory: 文档目录路径
            file_types: 支持的文件类型，默认为配置中的值
            allow_temp_dir: 是否允许临时目录（用于文件上传等场景）

        Returns:
            加载的文档列表

        Raises:
            DocumentLoadError: 文档加载失败
        """
        return self._document_loader.load_from_directory(directory, file_types, allow_temp_dir=allow_temp_dir)

    def create_vectorstore(self,
                           documents: list[Document],
                           collection_name: str = "rag_collection") -> None:
        """
        创建向量存储

        Args:
            documents: 文档列表
            collection_name: 集合名称

        Raises:
            VectorStoreError: 向量存储创建失败
        """
        # 分割文档
        text_chunks = self._text_splitter.split_documents(documents)

        # 创建向量存储
        self._vector_store_manager.create(text_chunks, collection_name)

        # 初始化检索器和问答链构建器
        self._initialize_retriever_and_qa_chain(collection_name)

    def load_vectorstore(self, collection_name: str = "rag_collection") -> None:
        """
        加载已存在的向量存储

        Args:
            collection_name: 集合名称

        Raises:
            VectorStoreError: 向量存储加载失败
        """
        self._vector_store_manager.load(collection_name)
        self._initialize_retriever_and_qa_chain(collection_name)

    def add_documents_to_vectorstore(
            self,
            documents: list[Document],
            collection_name: str = "rag_collection",
            incremental: bool = True) -> dict[str, Any]:
        """
        向现有向量存储添加新文档（支持增量添加和去重）

        Args:
            documents: 文档列表
            collection_name: 集合名称
            incremental: 是否启用增量模式（检查新文件，删除旧版本）

        Returns:
            字典，包含添加的文档数量、删除的文档数量等信息

        Raises:
            VectorStoreError: 添加文档失败
            ValueError: 向量存储未初始化
        """
        # 分割文档
        text_chunks = self._text_splitter.split_documents(documents)

        # 添加文档到向量存储（使用增量模式）
        result = self._vector_store_manager.add_documents(
            text_chunks, collection_name, incremental=incremental)

        # 如果检索器和问答链已初始化，需要重新初始化以使用更新后的向量存储
        if self._vector_store_manager.vectorstore is not None:
            self._initialize_retriever_and_qa_chain(collection_name)

        return result

    def _initialize_retriever_and_qa_chain(self, collection_name: str) -> None:
        """初始化检索器和问答链"""
        if self._vector_store_manager.vectorstore is None:
            raise VectorStoreError("向量存储未初始化")

        # 记录向量存储的文档数量
        try:
            collection = self._vector_store_manager.vectorstore._collection
            count = collection.count()
            self.logger.debug(f"重新初始化检索器，当前向量存储包含 {count} 个文档块")
        except Exception:
            pass

        # 创建检索器（使用更新后的向量存储）
        self._retriever = Retriever(
            vectorstore=self._vector_store_manager.vectorstore,
            k=self.config.default_k,
            logger=self.logger)

        # 创建问答链构建器
        self._qa_chain_builder = QAChainBuilder(llm=self._llm_wrapper.llm,
                                                retriever=self._retriever,
                                                logger=self.logger)
        self._qa_chain_builder.build()
        self.logger.info(f"问答链创建完成（检索 k={self.config.default_k} 个文档块）")

    def create_qa_chain(self, k: int | None = None) -> None:
        """
        创建问答链

        Args:
            k: 检索的文档块数量（默认使用配置值）

        Raises:
            ValueError: 向量存储未初始化
        """
        if self._vector_store_manager.vectorstore is None:
            raise ValueError("向量存储未初始化，请先创建或加载向量存储")

        k = k or self.config.default_k

        if self._retriever is None:
            self._retriever = Retriever(
                vectorstore=self._vector_store_manager.vectorstore,
                k=k,
                logger=self.logger)
        else:
            self._retriever.update_k(k)

        if self._qa_chain_builder is None:
            self._qa_chain_builder = QAChainBuilder(llm=self._llm_wrapper.llm,
                                                    retriever=self._retriever,
                                                    logger=self.logger)
        self._qa_chain_builder.build()

    def query(self,
              question: str,
              max_retries: int | None = None) -> dict[str, Any]:
        """
        查询问题（支持自动重试）

        Args:
            question: 用户问题
            max_retries: 最大重试次数（默认使用配置值）

        Returns:
            包含答案和源文档的字典

        Raises:
            ValueError: 问答链未初始化
        """
        if self._qa_chain_builder is None or self._retriever is None:
            raise ValueError("问答链未初始化，请先创建问答链")

        self.logger.info(f"正在处理问题: {question}")

        # 使用重试处理器执行查询
        def _execute_query():
            # 检索相关文档
            source_documents = self._retriever.retrieve(question)

            if not source_documents:
                self.logger.warning(f"检索器没有找到任何相关文档（问题: {question}）")
                return {
                    "answer":
                        "抱歉，我在向量存储中没有找到相关的文档信息。请确保：\n1. 向量存储已正确创建并包含文档\n2. 问题与文档内容相关\n3. 如果是从 FAISS 迁移到 ChromaDB，请删除旧的向量存储并重新创建。",
                    "source_documents": []
                }

            # 获取答案
            answer = self._qa_chain_builder.invoke(question)

            self.logger.info("查询成功")
            return {"answer": answer, "source_documents": source_documents}

        # 使用错误分类器
        def error_classifier(e: Exception) -> str:
            return self._error_handler.classify_error(e)

        # 执行查询（带重试）
        max_retries = max_retries or self.config.max_retries
        original_max_retries = self._retry_handler.max_retries
        self._retry_handler.max_retries = max_retries

        try:
            try:
                return self._retry_handler.retry_with_backoff(
                    _execute_query, error_classifier=error_classifier)
            except Exception as e:
                # 处理不同类型的错误
                error_type = self._error_handler.classify_error(e)
                error_msg = self._error_handler.parse_error(e)

                if error_type == "rate_limit":
                    error_msg = "API请求频率过高。免费版API有速率限制（约5次/秒），请稍后再试。"
                elif error_type == "timeout":
                    error_msg = "API请求超时，请检查网络连接后重试。"
                elif error_type == "auth":
                    error_msg = f"抱歉，认证失败: {error_msg}"
                elif error_type == "balance":
                    error_msg = f"抱歉，账户余额不足: {error_msg}"
                else:
                    error_msg = f"抱歉，处理问题时出现错误: {error_msg}"

                self.logger.error(f"查询失败: {error_msg}", exc_info=True)
                return {"answer": error_msg, "source_documents": []}
        finally:
            self._retry_handler.max_retries = original_max_retries

    def get_similar_documents(self, query: str, k: int = 4) -> list[Document]:
        """
        获取相似文档

        Args:
            query: 查询文本
            k: 返回的文档数量

        Returns:
            相似文档列表

        Raises:
            ValueError: 向量存储未初始化
        """
        if self._vector_store_manager.vectorstore is None:
            raise ValueError("向量存储未初始化")

        return self._vector_store_manager.vectorstore.similarity_search(query,
                                                                        k=k)

    # 向后兼容的方法（用于调试模式）
    def query_with_debug(self,
                         question: str,
                         show_context: bool = True) -> dict[str, Any]:
        """
        查询问题（调试模式，显示检索到的文档和提示内容）

        Args:
            question: 用户问题
            show_context: 是否显示检索到的上下文

        Returns:
            包含答案、源文档和调试信息的字典

        Raises:
            ValueError: 问答链未初始化
        """
        if self._qa_chain_builder is None or self._retriever is None:
            raise ValueError("问答链未初始化，请先创建问答链")

        self.logger.debug(f"调试模式查询: {question}")

        # 检索相关文档
        try:
            source_documents = self._retriever.retrieve(question)

            if show_context:
                for i, doc in enumerate(source_documents, 1):
                    self.logger.info(
                        f"文档块 {i} (长度: {len(doc.page_content)} 字符)")
                    content_preview = (doc.page_content[:300] + "..." if len(
                        doc.page_content) > 300 else doc.page_content)
                    self.logger.debug(f"文档块 {i} 内容预览: {content_preview}")
        except Exception as e:
            error_msg = f"检索失败: {e}"
            self.logger.error(error_msg, exc_info=True)
            return {
                "answer": f"检索失败: {error_msg}",
                "source_documents": [],
                "debug_info": {
                    "error": str(e)
                }
            }

        # 构建提示预览
        context = "\n\n".join(doc.page_content for doc in source_documents)
        self.logger.info(f"提示总长度: {len(context)} 字符")

        # 调用问答链
        try:
            answer = self._qa_chain_builder.invoke(question)
            self.logger.info("DeepSeek API 调用成功")
        except Exception as e:
            error_str = str(e)
            error_msg = self._error_handler.parse_error(e)
            self.logger.error(f"DeepSeek API 调用失败: {error_msg}", exc_info=True)
            return {
                "answer": f"抱歉，处理问题时出现错误: {error_msg}",
                "source_documents": source_documents,
                "debug_info": {
                    "context_length": len(context),
                    "num_documents": len(source_documents),
                    "error": error_str
                }
            }

        return {
            "answer": answer,
            "source_documents": source_documents,
            "debug_info": {
                "context_length": len(context),
                "num_documents": len(source_documents),
                "answer_length": len(answer)
            }
        }
