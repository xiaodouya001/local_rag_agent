"""
问答链构建器
负责构建RAG问答链
"""

import logging
import os

from langchain_core.documents import Document
from langchain_core.language_models import BaseChatModel
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnableLambda
from langchain_core.runnables import RunnablePassthrough

from app.core.retriever import Retriever
from app.infrastructure.logging_config import setup_api_logger


class QAChainBuilder:
    """问答链构建器"""

    DEFAULT_PROMPT_TEMPLATE = """基于以下上下文信息回答问题。如果你不知道答案，就说不知道，不要编造答案。

上下文信息:
{context}

问题: {question}

请提供详细、准确的回答:"""

    def __init__(
        self,
        llm: BaseChatModel,
        retriever: Retriever,
        prompt_template: str | None = None,
        logger: logging.Logger | None = None,
    ):
        """
        初始化问答链构建器

        Args:
            llm: 语言模型实例
            retriever: 检索器实例
            prompt_template: 提示模板（如果未提供则使用默认模板）
            logger: 日志记录器
        """
        self.llm = llm
        self.retriever = retriever
        self.prompt_template = prompt_template or self.DEFAULT_PROMPT_TEMPLATE
        self.logger = logger or logging.getLogger(__name__)

        # 检查是否启用详细日志（通过环境变量或日志级别）
        self.enable_debug_log = (
            os.getenv('ENABLE_API_DEBUG', 'false').lower() == 'true' or
            self.logger.level <= logging.DEBUG
        )

        # 创建独立的API日志记录器（用于记录详细的API请求/响应）
        self.api_logger = setup_api_logger() if self.enable_debug_log else None

        self._qa_chain = None

    def build(self) -> None:
        """构建问答链"""
        # 创建提示模板
        prompt = PromptTemplate(template=self.prompt_template,
                                input_variables=["context", "question"])

        # 格式化文档的函数（带日志记录）
        def format_docs(docs: list[Document]) -> str:
            if not docs:
                self.logger.warning("检索器返回了空的文档列表！")
                return "没有找到相关的上下文信息。"

            # 记录检索到的文档块
            if self.enable_debug_log:
                self.logger.debug("=" * 80)
                self.logger.debug("📚 检索到的文档块:")
                self.logger.debug("=" * 80)
                for i, doc in enumerate(docs, 1):
                    source = doc.metadata.get('source', 'unknown')
                    page = doc.metadata.get('page', 'N/A')
                    self.logger.debug(f"\n[文档块 {i}]")
                    self.logger.debug(f"  来源: {source} (页码: {page})")
                    self.logger.debug(f"  长度: {len(doc.page_content)} 字符")
                    # 只显示前500字符，避免日志过长
                    preview = doc.page_content[:500]
                    if len(doc.page_content) > 500:
                        preview += f"... (共 {len(doc.page_content)} 字符)"
                    self.logger.debug(f"  内容: {preview}")

            context = "\n\n".join(doc.page_content for doc in docs)

            if self.enable_debug_log:
                self.logger.debug(f"\n上下文总长度: {len(context)} 字符")
                self.logger.debug("=" * 80)

            return context

        # 创建用于记录完整 prompt 的包装器
        def log_full_prompt(input_dict: dict) -> dict:
            """记录完整的 prompt（在格式化之前）"""
            if self.enable_debug_log and self.api_logger:
                context = input_dict.get('context', '')
                question = input_dict.get('question', '')
                full_prompt = self.prompt_template.format(context=context, question=question)

                self.api_logger.debug("=" * 80)
                self.api_logger.debug("📤 [应用层] 发送给 DeepSeek API 的完整请求 (REQUEST):")
                self.api_logger.debug("=" * 80)
                self.api_logger.debug(full_prompt)
                self.api_logger.debug("=" * 80)
                self.api_logger.debug("请求统计:")
                self.api_logger.debug(f"  - 问题: {question}")
                self.api_logger.debug(f"  - 问题长度: {len(question)} 字符")
                self.api_logger.debug(f"  - 上下文长度: {len(context)} 字符")
                self.api_logger.debug(f"  - 总请求长度: {len(full_prompt)} 字符")
                self.api_logger.debug("=" * 80)

            return input_dict

        # 创建用于记录响应的包装器
        def log_response(response: str) -> str:
            """记录 API 响应"""
            if self.enable_debug_log and self.api_logger:
                self.api_logger.debug("=" * 80)
                self.api_logger.debug("📥 [应用层] DeepSeek API 响应 (RESPONSE):")
                self.api_logger.debug("=" * 80)
                self.api_logger.debug(response)
                self.api_logger.debug("=" * 80)
                self.api_logger.debug(f"响应长度: {len(response)} 字符")
                self.api_logger.debug("=" * 80)

            return response

        # 创建QA链（添加日志记录包装器）
        # 注意：需要在 prompt 格式化之前记录，所以使用 RunnableLambda
        self._qa_chain = ({
            "context": self.retriever._langchain_retriever | format_docs,
            "question": RunnablePassthrough(),
        } | RunnableLambda(log_full_prompt) | prompt | self.llm | StrOutputParser() | RunnableLambda(log_response))

        self.logger.info(f"问答链创建完成（检索 k={self.retriever.k} 个文档块）")

    @property
    def qa_chain(self):
        """获取问答链"""
        if self._qa_chain is None:
            self.build()
        return self._qa_chain

    def invoke(self, question: str) -> str:
        """
        调用问答链

        Args:
            question: 用户问题

        Returns:
            生成的回答
        """
        return self.qa_chain.invoke(question)
