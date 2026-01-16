"""
RAG (Retrieval-Augmented Generation) Agent
基于检索增强生成的AI智能体
"""

import os
import pickle
import re
import time
from typing import List, Optional, Dict, Any
from pathlib import Path
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader, TextLoader, DirectoryLoader
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from dotenv import load_dotenv

# 尝试导入 UI 模块，如果失败则使用简单的 print
try:
    from ui import ui
    HAS_UI = True
except ImportError:
    HAS_UI = False
    # 创建一个简单的 UI 占位符
    class SimpleUI:
        @staticmethod
        def print_step(num, text, icon=None):
            print(f"\n[步骤 {num}] {text}")
            print("-" * 70)
        @staticmethod
        def print_document_block(index, content, max_length=300):
            preview = content[:max_length] + ("..." if len(content) > max_length else "")
            print(f"\n文档块 {index}:")
            print(f"长度: {len(content)} 字符")
            print(preview)
        @staticmethod
        def print_box(content, title=None, color='cyan'):
            if title:
                print(f"\n{title}:")
            print(content)
    ui = SimpleUI()

load_dotenv()


class RAGAgent:
    """RAG Agent主类，负责文档加载、向量化和检索生成"""
    
    def __init__(
        self,
        persist_directory: str = "./chroma_db",
        embedding_model: str = "all-MiniLM-L6-v2",
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
        print("提示: 首次运行需要下载模型，可能需要一些时间...")
        try:
            self.embeddings = HuggingFaceEmbeddings(
                model_name=embedding_model,
                model_kwargs={'device': 'cpu'}
            )
        except Exception as e:
            print(f"加载嵌入模型失败: {e}")
            print("提示: 可能是网络连接问题，请检查网络或稍后重试")
            raise
        
        # 初始化LLM（DeepSeek）
        base_url = base_url or os.getenv("DEEPSEEK_API_BASE", "https://api.deepseek.com/v1")
        api_key = api_key or os.getenv("DEEPSEEK_API_KEY")
        
        if not api_key:
            raise ValueError("未找到DEEPSEEK_API_KEY，请在.env文件中设置")
        
        print(f"正在初始化DeepSeek LLM: {llm_model}")
        print("提示: 免费版API有速率限制，如遇到429错误请稍后重试")
        try:
            self.llm = ChatOpenAI(
                model=llm_model,
                base_url=base_url,
                api_key=api_key,
                temperature=0.7,
                max_tokens=2000,
                timeout=60,  # 设置超时时间
                max_retries=3  # 添加重试机制
            )
        except Exception as e:
            print(f"初始化LLM失败: {e}")
            print("提示: 请检查 API 密钥和网络连接")
            print("注意: 免费版API可能需要验证账户，请前往 https://platform.deepseek.com/ 检查账户状态")
            raise
        
        # 初始化文本分割器
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
        )
        
        # 向量存储
        self.vectorstore: Optional[FAISS] = None
        self.qa_chain = None
        self.retriever = None
        
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
                loader_cls=TextLoader,
                loader_kwargs={"encoding": "utf-8"}
            )
            try:
                documents.extend(txt_loader.load())
            except Exception as e:
                print(f"警告: 加载TXT文件时出错: {e}")
                # 尝试使用其他编码
                try:
                    txt_loader_utf8 = DirectoryLoader(
                        directory,
                        glob="**/*.txt",
                        loader_cls=TextLoader,
                        loader_kwargs={"encoding": "utf-8-sig"}
                    )
                    documents.extend(txt_loader_utf8.load())
                except Exception as e2:
                    print(f"错误: 无法加载TXT文件: {e2}")
        
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
        self.vectorstore = FAISS.from_documents(
            documents=texts,
            embedding=self.embeddings
        )
        # 保存向量存储
        self.vectorstore.save_local(self.persist_directory)
        print(f"向量存储已创建并保存到: {self.persist_directory}")
        
    def load_vectorstore(self, collection_name: str = "rag_collection"):
        """
        加载已存在的向量存储
        
        Args:
            collection_name: 集合名称（保留参数以兼容旧代码）
        """
        if not os.path.exists(self.persist_directory):
            raise ValueError(f"向量存储目录不存在: {self.persist_directory}")
        
        print(f"正在从 {self.persist_directory} 加载向量存储...")
        self.vectorstore = FAISS.load_local(
            self.persist_directory,
            self.embeddings,
            allow_dangerous_deserialization=True
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
        
        # 创建QA链（使用新版本API）
        def format_docs(docs):
            return "\n\n".join(doc.page_content for doc in docs)
        
        self.retriever = retriever
        self.qa_chain = (
            {"context": retriever | format_docs, "question": RunnablePassthrough()}
            | PROMPT
            | self.llm
            | StrOutputParser()
        )
        print("问答链创建完成")
    
    def query(self, question: str, max_retries: int = 3) -> Dict[str, Any]:
        """
        查询问题（支持自动重试，适用于免费版API的速率限制）
        
        Args:
            question: 用户问题
            max_retries: 最大重试次数（默认3次）
            
        Returns:
            包含答案和源文档的字典
        """
        if self.qa_chain is None or self.retriever is None:
            raise ValueError("问答链未初始化，请先创建问答链")
        
        print(f"正在处理问题: {question}")
        
        # 重试机制，特别处理速率限制错误
        for attempt in range(max_retries):
            try:
                # 获取相关文档（使用新版本API）
                source_documents = self.retriever.invoke(question)
                # 获取答案
                answer = self.qa_chain.invoke(question)
                
                return {
                    "answer": answer,
                    "source_documents": source_documents
                }
                
            except Exception as e:
                error_str = str(e)
                error_msg = self._parse_error_message(error_str)
                
                # 如果是速率限制错误（429），等待后重试
                if "429" in error_str or "rate limit" in error_str.lower():
                    if attempt < max_retries - 1:
                        wait_time = (attempt + 1) * 2  # 递增等待时间：2秒、4秒、6秒
                        print(f"遇到速率限制，等待 {wait_time} 秒后重试... (尝试 {attempt + 1}/{max_retries})")
                        time.sleep(wait_time)
                        continue
                    else:
                        print(f"错误: {error_msg}")
                        return {
                            "answer": f"抱歉，API请求频率过高。免费版API有速率限制（约5次/秒），请稍后再试。\n\n详细错误: {error_msg}",
                            "source_documents": []
                        }
                else:
                    # 其他错误，不重试
                    print(f"错误: {error_msg}")
                    return {
                        "answer": f"抱歉，处理问题时出现错误: {error_msg}",
                        "source_documents": []
                    }
        
        # 如果所有重试都失败了
        return {
            "answer": "抱歉，多次重试后仍然失败，请检查网络连接和API密钥状态。",
            "source_documents": []
        }
    
    def _parse_error_message(self, error_str: str) -> str:
        """
        解析错误信息，提供更友好的提示
        
        Args:
            error_str: 原始错误信息
            
        Returns:
            友好的错误提示
        """
        error_str_lower = error_str.lower()
        
        # API 余额不足
        if "insufficient balance" in error_str_lower or "402" in error_str:
            return "API 账户余额不足。请前往 DeepSeek 官网充值后重试。"
        
        # API 密钥错误
        if "401" in error_str or "unauthorized" in error_str_lower or "invalid api key" in error_str_lower:
            return "API 密钥无效或已过期。请检查 .env 文件中的 DEEPSEEK_API_KEY 是否正确。"
        
        # 网络连接问题
        if "timeout" in error_str_lower or "connection" in error_str_lower:
            return "网络连接超时。请检查网络连接后重试。"
        
        # 速率限制
        if "rate limit" in error_str_lower or "429" in error_str:
            return "API 请求频率过高（免费版限制约5次/秒）。程序会自动重试，请稍候。"
        
        # 模型不可用
        if "model" in error_str_lower and ("not found" in error_str_lower or "unavailable" in error_str_lower):
            return "指定的模型不可用。请检查模型名称是否正确。"
        
        # 其他错误，返回原始错误信息但更简洁
        if "error code:" in error_str:
            # 提取错误代码和主要信息
            import re
            code_match = re.search(r'error code:\s*(\d+)', error_str, re.IGNORECASE)
            message_match = re.search(r"'message':\s*'([^']+)'", error_str)
            
            if code_match and message_match:
                code = code_match.group(1)
                message = message_match.group(1)
                return f"API 错误 (代码 {code}): {message}"
        
        # 默认返回原始错误，但截断过长的错误信息
        if len(error_str) > 200:
            return error_str[:200] + "..."
        
        return error_str
    
    def query_with_debug(self, question: str, show_context: bool = True) -> Dict[str, Any]:
        """
        查询问题（调试模式，显示检索到的文档和提示内容）
        
        Args:
            question: 用户问题
            show_context: 是否显示检索到的上下文
            
        Returns:
            包含答案、源文档和调试信息的字典
        """
        if self.qa_chain is None or self.retriever is None:
            raise ValueError("问答链未初始化，请先创建问答链")
        
        print(f"\n{'='*60}")
        print(f"问题: {question}")
        print(f"{'='*60}\n")
        
        # 步骤 1: 检索相关文档
        print("【步骤 1】检索相关文档（本地完成，不使用 DeepSeek API）:")
        print("-" * 60)
        source_documents = self.retriever.invoke(question)
        print(f"检索到 {len(source_documents)} 个相关文档块\n")
        
        if show_context:
            for i, doc in enumerate(source_documents, 1):
                print(f"文档块 {i} (长度: {len(doc.page_content)} 字符):")
                content_preview = doc.page_content[:300] + ("..." if len(doc.page_content) > 300 else "")
                print(f"  {content_preview}\n")
        
        # 步骤 2: 构建提示
        print("\n【步骤 2】构建发送给 DeepSeek API 的提示:")
        print("-" * 60)
        context = "\n\n".join(doc.page_content for doc in source_documents)
        prompt_preview = f"""基于以下上下文信息回答问题。如果你不知道答案，就说不知道，不要编造答案。

上下文信息:
{context[:500]}{'...' if len(context) > 500 else ''}

问题: {question}

请提供详细、准确的回答:"""
        print(prompt_preview)
        print(f"\n提示总长度: {len(context)} 字符")
        
        # 步骤 3: 调用 DeepSeek API
        print("\n【步骤 3】调用 DeepSeek API 生成回答:")
        print("-" * 60)
        print("正在调用 DeepSeek API...")
        
        try:
            answer = self.qa_chain.invoke(question)
            if HAS_UI:
                ui.print_progress_done()
                ui.print_success("DeepSeek API 调用成功")
            else:
                print("✓ DeepSeek API 调用成功\n")
        except Exception as e:
            error_str = str(e)
            error_msg = self._parse_error_message(error_str)
            if HAS_UI:
                ui.print_error(f"DeepSeek API 调用失败: {error_msg}")
            else:
                print(f"✗ DeepSeek API 调用失败: {error_msg}\n")
            return {
                "answer": f"抱歉，处理问题时出现错误: {error_msg}",
                "source_documents": source_documents,
                "debug_info": {
                    "context_length": len(context),
                    "num_documents": len(source_documents),
                    "error": error_str
                }
            }
        
        # 步骤 4: 对比分析
        if HAS_UI:
            ui.print_section("对比分析", icon='brain')
            if source_documents:
                ui.print_box(
                    source_documents[0].page_content[:200] + "..." if len(source_documents[0].page_content) > 200 else source_documents[0].page_content,
                    title="原始文档内容（检索到的）",
                    color='cyan'
                )
            ui.print_box(
                answer[:200] + "..." if len(answer) > 200 else answer,
                title="DeepSeek 生成的回答",
                color='green'
            )
            
            # 计算相似度（简单对比）
            if source_documents:
                original_text = source_documents[0].page_content.lower()
                answer_lower = answer.lower()
                # 简单的关键词重叠分析
                original_words = set(original_text.split())
                answer_words = set(answer_lower.split())
                common_words = original_words & answer_words
                similarity = len(common_words) / max(len(original_words), len(answer_words)) * 100
                ui.print_info(f"关键词重叠度: {similarity:.1f}%")
                ui.print_info("（这只是一个简单的指标，DeepSeek 会重新组织和表述内容）")
        else:
            print("【步骤 4】对比分析:")
            print("-" * 60)
            print("原始文档内容（检索到的）:")
            if source_documents:
                original_preview = source_documents[0].page_content[:200]
                print(f"  {original_preview}...")
            print()
            print("DeepSeek 生成的回答:")
            print(f"  {answer[:200]}...")
            print()
            
            # 计算相似度（简单对比）
            if source_documents:
                original_text = source_documents[0].page_content.lower()
                answer_lower = answer.lower()
                # 简单的关键词重叠分析
                original_words = set(original_text.split())
                answer_words = set(answer_lower.split())
                common_words = original_words & answer_words
                similarity = len(common_words) / max(len(original_words), len(answer_words)) * 100
                print(f"关键词重叠度: {similarity:.1f}%")
                print("（这只是一个简单的指标，DeepSeek 会重新组织和表述内容）")
        
        return {
            "answer": answer,
            "source_documents": source_documents,
            "debug_info": {
                "context_length": len(context),
                "num_documents": len(source_documents),
                "answer_length": len(answer)
            }
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
