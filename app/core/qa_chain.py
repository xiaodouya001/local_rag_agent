"""
问答链构建器
负责构建RAG问答链
"""

import logging
from typing import Optional, List

from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain_core.documents import Document
from langchain_core.language_models import BaseChatModel

from app.core.retriever import Retriever


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
        prompt_template: Optional[str] = None,
        logger: Optional[logging.Logger] = None,
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

        self._qa_chain = None

    def build(self) -> None:
        """构建问答链"""
        # 创建提示模板
        prompt = PromptTemplate(
            template=self.prompt_template, input_variables=["context", "question"]
        )

        # 格式化文档的函数
        def format_docs(docs: List[Document]) -> str:
            if not docs:
                self.logger.warning("检索器返回了空的文档列表！")
                return "没有找到相关的上下文信息。"
            return "\n\n".join(doc.page_content for doc in docs)

        # 创建QA链
        self._qa_chain = (
            {
                "context": self.retriever._langchain_retriever | format_docs,
                "question": RunnablePassthrough(),
            }
            | prompt
            | self.llm
            | StrOutputParser()
        )

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
