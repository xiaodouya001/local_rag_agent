"""
RAG Agent 使用示例
"""

import os
from rag_agent import RAGAgent
from dotenv import load_dotenv

load_dotenv()


def example_usage():
    """使用示例"""
    
    # 1. 初始化RAG Agent
    agent = RAGAgent(
        persist_directory="./chroma_db",
        embedding_model="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
        llm_model="deepseek-chat",
        chunk_size=1000,
        chunk_overlap=200
    )
    
    # 2. 加载文档（首次运行）
    documents_dir = "./documents"
    if os.path.exists(documents_dir):
        documents = agent.load_documents(documents_dir)
        
        # 3. 创建向量存储
        agent.create_vectorstore(documents, collection_name="my_documents")
    else:
        # 如果向量存储已存在，直接加载
        agent.load_vectorstore(collection_name="my_documents")
    
    # 4. 创建问答链
    agent.create_qa_chain(k=4)
    
    # 5. 查询问题
    questions = [
        "文档的主要内容是什么？",
        "有哪些关键概念？",
        "请总结一下文档的要点"
    ]
    
    for question in questions:
        print(f"\n问题: {question}")
        result = agent.query(question)
        print(f"回答: {result['answer']}")
        print(f"参考了 {len(result['source_documents'])} 个文档块")
        print("-" * 60)
    
    # 6. 获取相似文档
    print("\n查找相似文档:")
    similar_docs = agent.get_similar_documents("机器学习", k=2)
    for i, doc in enumerate(similar_docs, 1):
        print(f"\n文档 {i}:")
        print(doc.page_content[:200] + "...")


if __name__ == "__main__":
    example_usage()
