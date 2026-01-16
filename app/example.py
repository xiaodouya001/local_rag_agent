"""
RAG Agent 使用示例
"""

import os
import sys
import logging
from pathlib import Path

# 处理直接运行时的导入路径问题
if __name__ == "__main__":
    # 添加项目根目录到路径
    project_root = Path(__file__).parent.parent
    sys.path.insert(0, str(project_root))
    from app.rag_agent import RAGAgent
    from app.config import RAGConfig
    from app.logging_config import setup_logging
else:
    # 作为模块导入时使用相对导入
    from .rag_agent import RAGAgent
    from .config import RAGConfig
    from .logging_config import setup_logging

from dotenv import load_dotenv

# 配置日志（使用统一的日志配置函数）
# 从环境变量读取日志级别，默认为INFO
log_level = os.getenv('LOG_LEVEL', 'INFO')
setup_logging(log_level=log_level, use_json=False)

logger = logging.getLogger(__name__)

load_dotenv()


def example_usage() -> None:
    """使用示例"""
    
    # 1. 初始化RAG Agent（使用配置对象）
    logger.info("初始化 RAG Agent")
    try:
        config = RAGConfig.from_env(
            persist_directory="./chroma_db",
            embedding_model="all-MiniLM-L6-v2",
            llm_model="deepseek-chat",
            chunk_size=1000,
            chunk_overlap=200
        )
        agent = RAGAgent(config=config)
        logger.info("RAG Agent 初始化成功")
    except Exception as e:
        logger.error(f"初始化失败: {e}", exc_info=True)
        return
    
    # 2. 加载文档（首次运行）
    documents_dir = "./documents"
    if os.path.exists(documents_dir):
        try:
            documents = agent.load_documents(documents_dir)
            
            # 3. 创建向量存储
            agent.create_vectorstore(documents, collection_name="my_documents")
            logger.info("向量存储创建成功")
        except Exception as e:
            logger.error(f"创建向量存储失败: {e}", exc_info=True)
            return
    else:
        # 如果向量存储已存在，直接加载
        try:
            agent.load_vectorstore(collection_name="my_documents")
            logger.info("向量存储加载成功")
        except Exception as e:
            logger.error(f"加载向量存储失败: {e}", exc_info=True)
            return
    
    # 4. 创建问答链
    try:
        agent.create_qa_chain(k=4)
        logger.info("问答链创建成功")
    except Exception as e:
        logger.error(f"创建问答链失败: {e}", exc_info=True)
        return
    
    # 5. 查询问题
    questions = [
        "文档的主要内容是什么？",
        "有哪些关键概念？",
        "请总结一下文档的要点"
    ]
    
    for question in questions:
        logger.info(f"问题: {question}")
        try:
            result = agent.query(question)
            logger.info(f"回答: {result['answer']}")
            logger.info(f"参考了 {len(result['source_documents'])} 个文档块")
            logger.info(f"成功处理问题: {question}")
        except Exception as e:
            logger.error(f"处理问题失败: {e}", exc_info=True)
    
    # 6. 获取相似文档
    logger.info("查找相似文档")
    try:
        similar_docs = agent.get_similar_documents("机器学习", k=2)
        for i, doc in enumerate(similar_docs, 1):
            logger.info(f"文档 {i}:")
            logger.debug(f"文档 {i} 内容预览: {doc.page_content[:200]}...")
        logger.info("成功获取相似文档")
    except Exception as e:
        logger.error(f"获取相似文档失败: {e}", exc_info=True)


if __name__ == "__main__":
    example_usage()
