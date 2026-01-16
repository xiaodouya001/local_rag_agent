"""
RAG Agent Chainlit Web 应用
基于检索增强生成的AI智能体 - Chainlit 版本（推荐）
"""

import os
import sys
import logging
from pathlib import Path
from typing import Optional

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import chainlit as cl
from app.rag_agent import RAGAgent
from app.config import RAGConfig
from app.exceptions import DocumentLoadError, VectorStoreError
from app.logging_config import setup_logging
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 配置日志（使用统一的日志配置函数）
# 从环境变量读取日志级别，默认为INFO
log_level = os.getenv('LOG_LEVEL', 'INFO')
setup_logging(log_level=log_level, use_json=False)

logger = logging.getLogger(__name__)

# 全局变量存储 RAG Agent（应用级别共享，避免重复初始化）
rag_agent: Optional[RAGAgent] = None
_initialization_lock = False  # 防止并发初始化


async def initialize_rag_agent() -> bool:
    """
    初始化 RAG Agent（可重用的初始化函数）
    
    Returns:
        bool: 初始化是否成功
    """
    global rag_agent, _initialization_lock
    
    # 如果已经初始化，直接返回
    if rag_agent is not None:
        return True
    
    # 如果正在初始化，等待
    if _initialization_lock:
        logger.warning("RAG Agent 正在初始化中，请稍候...")
        return False
    
    try:
        _initialization_lock = True
        logger.info("开始初始化 RAG Agent...")
        
        # 初始化配置和 Agent
        config = RAGConfig.from_env()
        rag_agent = RAGAgent(config=config)
        
        # 检查向量存储是否存在
        docs_dir = "./documents"
        vectorstore_exists = os.path.exists(config.persist_directory)
        
        if not vectorstore_exists:
            # 首次运行，需要创建向量存储
            if not os.path.exists(docs_dir):
                os.makedirs(docs_dir, exist_ok=True)
                logger.warning(f"文档目录不存在，已创建: {docs_dir}")
                return False
            
            # 加载文档并创建向量存储
            try:
                documents = rag_agent.load_documents(docs_dir)
                
                if not documents:
                    logger.warning(f"{docs_dir} 目录中没有找到文档")
                    return False
                
                # 创建向量存储
                rag_agent.create_vectorstore(documents)
                logger.info(f"向量存储创建成功（从 {docs_dir} 加载了 {len(documents)} 个文档）")
            except (DocumentLoadError, VectorStoreError) as e:
                logger.error(f"创建向量存储失败: {e}", exc_info=True)
                return False
        else:
            # 加载已存在的向量存储
            try:
                rag_agent.load_vectorstore()
                
                # 验证向量存储是否有数据
                try:
                    collection = rag_agent.vectorstore._collection
                    count = collection.count()
                    if count == 0:
                        logger.warning("向量存储为空")
                        return False
                    logger.info(f"向量存储加载成功，包含 {count} 个文档块")
                except Exception as e:
                    logger.warning(f"无法验证向量存储数据: {e}")
                
            except VectorStoreError as e:
                logger.error(f"加载向量存储失败: {e}", exc_info=True)
                return False
        
        # 创建问答链
        rag_agent.create_qa_chain()
        logger.info("RAG Agent 初始化成功")
        return True
        
    except Exception as e:
        logger.error(f"初始化 RAG Agent 失败: {e}", exc_info=True)
        return False
    finally:
        _initialization_lock = False


async def handle_file_upload(files):
    """
    处理文件上传的通用函数
    """
    global rag_agent
    
    if not files:
        await cl.Message(
            content="❌ 未选择文件",
            author="System"
        ).send()
        return
    
    try:
        # 创建临时目录保存上传的文件
        import shutil
        temp_dir = Path("./temp_documents")
        temp_dir.mkdir(exist_ok=True)
        
        # 保存上传的文件
        uploaded_files = []
        for file in files:
            # 兼容不同的文件对象类型
            if hasattr(file, 'path'):
                file_path = Path(file.path)
                if file_path.exists():
                    dest_path = temp_dir / file.name
                    shutil.copy2(file_path, dest_path)
                    uploaded_files.append(dest_path)
            elif hasattr(file, 'name') and hasattr(file, 'path'):
                file_path = Path(file.path)
                if file_path.exists():
                    dest_path = temp_dir / file.name
                    shutil.copy2(file_path, dest_path)
                    uploaded_files.append(dest_path)
            else:
                try:
                    file_path = temp_dir / getattr(file, 'name', f'file_{len(uploaded_files)}.txt')
                    if hasattr(file, 'content'):
                        with open(file_path, "wb") as f:
                            f.write(file.content)
                    elif hasattr(file, 'path'):
                        shutil.copy2(file.path, file_path)
                    uploaded_files.append(file_path)
                except Exception as e:
                    logger.warning(f"无法处理文件 {getattr(file, 'name', 'unknown')}: {e}")
                    continue
        
        if not uploaded_files:
            await cl.Message(
                content="❌ 无法处理上传的文件",
                author="System"
            ).send()
            return
        
        # 显示处理进度
        progress_msg = await cl.Message(
            content=f"📤 正在处理 {len(uploaded_files)} 个文件...",
            author="System"
        ).send()
        
        # 确保 Agent 已初始化
        if rag_agent is None:
            progress_msg.content = "🔄 正在初始化 RAG Agent..."
            await progress_msg.update()
            if not await initialize_rag_agent():
                progress_msg.content = "❌ RAG Agent 初始化失败，请刷新页面重试"
                await progress_msg.update()
                return
        
        # 加载文档
        documents = rag_agent.load_documents(str(temp_dir))
        
        if not documents:
            progress_msg.content = "❌ 未找到任何文档"
            await progress_msg.update()
            return
        
        # 创建向量存储
        progress_msg.content = f"📚 正在创建向量存储（已加载 {len(documents)} 个文档）..."
        await progress_msg.update()
        rag_agent.create_vectorstore(documents)
        rag_agent.create_qa_chain()
        
        # 清理临时文件
        shutil.rmtree(temp_dir, ignore_errors=True)
        
        progress_msg.content = f"✅ 成功处理 {len(documents)} 个文档，向量存储已创建！\n\n现在可以开始提问了。"
        await progress_msg.update()
        
    except DocumentLoadError as e:
        logger.error(f"文档加载失败: {e}", exc_info=True)
        await cl.Message(
            content=f"❌ 文档加载失败: {str(e)}",
            author="System"
        ).send()
    except VectorStoreError as e:
        logger.error(f"创建向量存储失败: {e}", exc_info=True)
        await cl.Message(
            content=f"❌ 创建向量存储失败: {str(e)}",
            author="System"
        ).send()
    except Exception as e:
        logger.error(f"处理文档失败: {e}", exc_info=True)
        await cl.Message(
            content=f"❌ 处理文档失败: {str(e)}",
            author="System"
        ).send()


@cl.on_chat_start
async def start():
    """
    聊天开始时初始化 RAG Agent
    使用全局变量缓存，避免重复初始化
    """
    global rag_agent
    
    # 如果 Agent 已经初始化，直接使用（避免重复初始化）
    if rag_agent is not None and rag_agent.qa_chain is not None:
        logger.info("RAG Agent 已存在，复用现有实例")
        await cl.Message(
            content="✅ RAG Agent 已就绪！\n\n你可以开始提问了，我会基于你的文档回答问题。\n\n💡 提示：\n- 直接输入问题开始对话\n- 输入 `/upload` 或拖拽文件上传新文档",
            author="System"
        ).send()
        return
    
    # 尝试初始化（使用统一的初始化函数）
    init_msg = await cl.Message(
        content="🔄 正在初始化 RAG Agent...",
        author="System"
    ).send()
    
    # 使用统一的初始化函数
    success = await initialize_rag_agent()
    
    if success:
        init_msg.content = "✅ RAG Agent 已就绪！\n\n你可以开始提问了，我会基于你的文档回答问题。\n\n💡 提示：\n- 直接输入问题开始对话\n- 输入 `/upload` 或拖拽文件上传新文档"
        await init_msg.update()
    else:
        # 检查具体失败原因，提供更友好的提示
        config = RAGConfig.from_env()
        docs_dir = "./documents"
        vectorstore_exists = os.path.exists(config.persist_directory)
        
        if not vectorstore_exists and not os.path.exists(docs_dir):
            init_msg.content = f"📁 已创建文档目录: {docs_dir}\n\n请将你的文档（PDF或TXT格式）放入 {docs_dir} 目录，然后刷新页面。"
        elif not vectorstore_exists:
            init_msg.content = f"❌ {docs_dir} 目录中没有找到文档\n\n请添加PDF或TXT格式的文档后刷新页面。"
        elif rag_agent is not None:
            # 检查向量存储是否为空
            try:
                collection = rag_agent.vectorstore._collection
                count = collection.count()
                if count == 0:
                    init_msg.content = f"⚠️ 向量存储已加载，但其中没有文档数据（0 个文档块）。\n\n这可能是从 FAISS 迁移到 ChromaDB 导致的。\n\n**解决方案：**\n1. 删除 `chroma_db` 目录中的旧文件（特别是 `index.faiss` 和 `index.pkl`）\n2. 或者直接删除整个 `chroma_db` 目录\n3. 然后刷新页面，系统会自动从 `documents` 目录重新创建向量存储"
                else:
                    init_msg.content = "❌ RAG Agent 初始化失败，请刷新页面重试。"
            except Exception:
                init_msg.content = "❌ RAG Agent 初始化失败，请刷新页面重试。"
        else:
            init_msg.content = "❌ RAG Agent 初始化失败，请刷新页面重试。"
        
        await init_msg.update()


@cl.on_message
async def main(message: cl.Message):
    """
    处理用户消息（包括文件上传）
    """
    global rag_agent
    
    # 检查是否有文件上传和文本内容
    has_files = bool(message.elements)
    has_text = bool(message.content and message.content.strip())
    
    # 如果有文件，先处理文件上传
    if has_files:
        await handle_file_upload(message.elements)
    
    # 处理文本消息（如果有文本内容）
    if has_text:
        # 检查是否是上传命令
        if message.content.strip().lower() in ["/upload", "上传", "upload"]:
            # 如果已经有文件，不需要再请求上传
            if has_files:
                return
            # 请求文件上传
            files = await cl.AskFileMessage(
                content="请上传 PDF 或 TXT 文件（支持多文件）",
                accept=["application/pdf", "text/plain", ".pdf", ".txt"],
                max_files=10,
                max_size_mb=200,
            ).send()
            
            if files:
                await handle_file_upload(files)
            return
        
        # 处理问答（非上传命令的文本消息）
        if rag_agent is None:
            await cl.Message(
                content="❌ RAG Agent 未初始化，请刷新页面重试。",
                author="Assistant"
            ).send()
            return
        
        if rag_agent.qa_chain is None:
            await cl.Message(
                content="❌ 问答链未创建。请先上传文档并创建向量存储。\n\n提示：你可以拖拽文件到聊天窗口或使用 /upload 命令上传文档。",
                author="Assistant"
            ).send()
            return
        
        # 显示加载状态
        msg = cl.Message(content="", author="Assistant")
        await msg.send()
        
        try:
            # 查询问题
            result = rag_agent.query(message.content)
            answer = result["answer"]
            sources = result.get("source_documents", [])
            
            # 构建回复内容
            response_content = answer
            
            # 如果有源文档，添加到回复中
            if sources and len(sources) > 0:
                response_content += f"\n\n---\n\n📚 **参考了 {len(sources)} 个文档块**\n\n"
                for i, doc in enumerate(sources[:3], 1):  # 只显示前3个
                    preview = doc.page_content[:200] + ("..." if len(doc.page_content) > 200 else "")
                    response_content += f"**文档块 {i}** (长度: {len(doc.page_content)} 字符):\n"
                    response_content += f"```\n{preview}\n```\n\n"
            
            # 更新消息内容
            msg.content = response_content
            await msg.update()
            
        except Exception as e:
            logger.error(f"处理问题时出错: {e}", exc_info=True)
            msg.content = f"❌ 处理问题时出错: {str(e)}"
            await msg.update()
