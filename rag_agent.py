"""
RAG (Retrieval-Augmented Generation) Agent
基于检索增强生成的AI智能体
"""

import os
from typing import List, Optional, Dict, Any
from pathlib import Path
import chromadb
from chromadb.config import Settings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader, TextLoader, DirectoryLoader
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_openai import ChatOpenAI
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from dotenv import load_dotenv

load_dotenv()


class RAGAgent:
    """RAG Agent主类，负责文档加载、向量化和检索生成"""
    
    def __init__(
        self,
        persist_directory: str = "./chroma_db",
        embedding_model: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
        llm_model: str = "deepseek-chat",
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        base_url: str = None,
        api_key: str = None
    ):
        """
        初始化RAG Agent
        
        Args:
            persist_directory: 向量数据库持久化目录
            embedding_model: 嵌入模型名称（使用HuggingFace模型）
            llm_model: 大语言模型名称（DeepSeek模型）
            chunk_size: 文档分块大小
            chunk_overlap: 文档分块重叠大小
            base_url: DeepSeek API基础URL
            api_key: DeepSeek API密钥
        """
        self.persist_directory = persist_directory
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        
        # 初始化嵌入模型（使用本地HuggingFace模型）
        print(f"正在加载嵌入模型: {embedding_model}")
        self.embeddings = HuggingFaceEmbeddings(
            model_name=embedding_model,
            model_kwargs={'device': 'cpu'}
        )
        
        # 初始化LLM（DeepSeek）
        base_url = base_url or os.getenv("DEEPSEEK_API_BASE", "https://api.deepseek.com/v1")
        api_key = api_key or os.getenv("DEEPSEEK_API_KEY")
        
        if not api_key:
            raise ValueError("未找到DEEPSEEK_API_KEY，请在.env文件中设置")
        
        print(f"正在初始化DeepSeek LLM: {llm_model}")
        self.llm = ChatOpenAI(
            model=llm_model,
            base_url=base_url,
            api_key=api_key,
            temperature=0.7,
            max_tokens=2000
        )
        
        # 初始化文本分割器
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
        )
        
        # 向量存储
        self.vectorstore: Optional[Chroma] = None
        self.qa_chain: Optional[RetrievalQA] = None
        
    def load_documents(self, directory: str, file_types: List[str] = None) -> List:
        """
        从目录加载文档
        
        Args:
            directory: 文档目录路径
            file_types: 支持的文件类型，默认为['.pdf', '.txt']
            
        Returns:
            加载的文档列表
        """
        if file_types is None:
            file_types = ['.pdf', '.txt']
        
        documents = []
        directory_path = Path(directory)
        
        if not directory_path.exists():
            raise ValueError(f"目录不存在: {directory}")
        
        # 加载PDF文件
        if '.pdf' in file_types:
            pdf_loader = DirectoryLoader(
                directory,
                glob="**/*.pdf",
                loader_cls=PyPDFLoader
            )
            documents.extend(pdf_loader.load())
        
        # 加载TXT文件
        if '.txt' in file_types:
            txt_loader = DirectoryLoader(
                directory,
                glob="**/*.txt",
                loader_cls=TextLoader
            )
            documents.extend(txt_loader.load())
        
        print(f"已加载 {len(documents)} 个文档")
        return documents
    
    def create_vectorstore(self, documents: List, collection_name: str = "rag_collection"):
        """
        创建向量存储
        
        Args:
            documents: 文档列表
            collection_name: 集合名称
        """
        if not documents:
            raise ValueError("文档列表为空")
        
        # 分割文档
        print("正在分割文档...")
        texts = self.text_splitter.split_documents(documents)
        print(f"文档已分割为 {len(texts)} 个块")
        
        # 创建向量存储
        print("正在创建向量存储...")
        self.vectorstore = Chroma.from_documents(
            documents=texts,
            embedding=self.embeddings,
            persist_directory=self.persist_directory,
            collection_name=collection_name
        )
        print(f"向量存储已创建并保存到: {self.persist_directory}")
        
    def load_vectorstore(self, collection_name: str = "rag_collection"):
        """
        加载已存在的向量存储
        
        Args:
            collection_name: 集合名称
        """
        if not os.path.exists(self.persist_directory):
            raise ValueError(f"向量存储目录不存在: {self.persist_directory}")
        
        print(f"正在从 {self.persist_directory} 加载向量存储...")
        self.vectorstore = Chroma(
            persist_directory=self.persist_directory,
            embedding_function=self.embeddings,
            collection_name=collection_name
        )
        print("向量存储加载完成")
    
    def create_qa_chain(self, k: int = 4):
        """
        创建问答链
        
        Args:
            k: 检索的文档块数量
        """
        if self.vectorstore is None:
            raise ValueError("向量存储未初始化，请先创建或加载向量存储")
        
        # 创建检索器
        retriever = self.vectorstore.as_retriever(
            search_type="similarity",
            search_kwargs={"k": k}
        )
        
        # 创建提示模板
        prompt_template = """基于以下上下文信息回答问题。如果你不知道答案，就说不知道，不要编造答案。

上下文信息:
{context}

问题: {question}

请提供详细、准确的回答:"""
        
        PROMPT = PromptTemplate(
            template=prompt_template,
            input_variables=["context", "question"]
        )
        
        # 创建QA链
        self.qa_chain = RetrievalQA.from_chain_type(
            llm=self.llm,
            chain_type="stuff",
            retriever=retriever,
            return_source_documents=True,
            chain_type_kwargs={"prompt": PROMPT}
        )
        print("问答链创建完成")
    
    def query(self, question: str) -> Dict[str, Any]:
        """
        查询问题
        
        Args:
            question: 用户问题
            
        Returns:
            包含答案和源文档的字典
        """
        if self.qa_chain is None:
            raise ValueError("问答链未初始化，请先创建问答链")
        
        print(f"正在处理问题: {question}")
        result = self.qa_chain({"query": question})
        
        return {
            "answer": result["result"],
            "source_documents": result.get("source_documents", [])
        }
    
    def get_similar_documents(self, query: str, k: int = 4) -> List:
        """
        获取相似文档
        
        Args:
            query: 查询文本
            k: 返回的文档数量
            
        Returns:
            相似文档列表
        """
        if self.vectorstore is None:
            raise ValueError("向量存储未初始化")
        
        docs = self.vectorstore.similarity_search(query, k=k)
        return docs
