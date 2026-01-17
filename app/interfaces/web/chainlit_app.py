"""
RAG Agent Chainlit Web 应用
基于检索增强生成的AI Agent - Chainlit 版本（推荐）
"""

import asyncio
import logging
import os
from pathlib import Path
import sys

# 添加项目根目录到路径
# 在导入 app 模块之前，需要先手动查找项目根目录
_current_file = Path(__file__).resolve()

# 向上查找包含 pyproject.toml 的目录
project_root = None
for parent in [(_current_file.parent if _current_file.is_file() else _current_file)] + list(_current_file.parents):
    if (parent / "pyproject.toml").exists():
        project_root = parent.resolve()
        break

# 如果找不到，尝试从当前工作目录查找
if project_root is None:
    cwd = Path.cwd()
    if (cwd / "pyproject.toml").exists():
        project_root = cwd.resolve()
    else:
        for parent in cwd.parents:
            if (parent / "pyproject.toml").exists():
                project_root = parent.resolve()
                break

# 如果还是找不到，抛出错误
if project_root is None:
    raise RuntimeError(
        "无法找到项目根目录（包含 pyproject.toml 的目录）。"
        "请确保在项目目录中运行，或检查目录结构是否正确。"
    )

# 确保项目根目录在 sys.path 中
project_root_str = str(project_root)
if project_root_str not in sys.path:
    sys.path.insert(0, project_root_str)

# 必须在 sys.path 设置后才能导入 app 模块
import chainlit as cl  # noqa: E402
from dotenv import load_dotenv  # noqa: E402

from app.application import RAGAgent  # noqa: E402
from app.infrastructure import DocumentLoadError  # noqa: E402
from app.infrastructure import RAGConfig
from app.infrastructure import setup_logging
from app.infrastructure import VectorStoreError

# 加载环境变量
load_dotenv()

# 配置日志（使用统一的日志配置函数）
# 从环境变量读取日志级别，默认为INFO
log_level = os.getenv('LOG_LEVEL', 'INFO')
setup_logging(log_level=log_level, use_json=False)

logger = logging.getLogger(__name__)

# 全局变量存储 RAG Agent（应用级别共享，避免重复初始化）
rag_agent: RAGAgent | None = None
_initialization_lock = False
_startup_complete = False
_startup_failed = False
_startup_task = None


async def startup_initialization():
    """
    启动时预初始化 RAG Agent（后台任务）
    在服务器启动时自动运行，避免用户首次访问时等待
    """
    global _startup_complete, _startup_failed
    
    logger.info("")
    logger.info("=" * 60)
    logger.info("🚀 开始启动 RAG Agent 后台服务...")
    logger.info("=" * 60)
    
    # 等待一小段时间，确保服务器基本启动
    await asyncio.sleep(0.5)
    
    # 执行初始化
    success = await initialize_rag_agent()
    
    if success:
        # Banner 已移至 PowerShell 启动脚本，此处不再显示
        _startup_complete = True
    else:
        logger.error("=" * 60)
        logger.error("❌ RAG Agent 启动失败，但服务器将继续运行")
        logger.error("   用户首次访问时将尝试重新初始化")
        logger.error("=" * 60)
        _startup_failed = True


# 使用Chainlit的启动机制
# 注意：由于Chainlit的事件循环机制，我们在on_chat_start时进行初始化
# 但为了更好的用户体验，我们会在首次访问时立即初始化
# Banner 显示已移至 PowerShell 启动脚本（start_chainlit.ps1）


async def initialize_rag_agent() -> bool:
    """
    初始化 RAG Agent（可重用的初始化函数）

    Returns:
        bool: 初始化是否成功
    """
    global rag_agent, _initialization_lock, _startup_complete

    # 如果已经初始化，直接返回
    if rag_agent is not None and _startup_complete:
        return True

    # 如果正在初始化，等待
    if _initialization_lock:
        logger.warning("RAG Agent 正在初始化中，请稍候...")
        return False

    try:
        _initialization_lock = True
        logger.info("=" * 60)
        logger.info("🔄 开始初始化 RAG Agent...")
        logger.info("=" * 60)

        # 初始化配置和 Agent（自动从环境变量读取）
        logger.info("📋 步骤 1/5: 加载配置...")
        config = RAGConfig()
        logger.info(f"   ✓ 配置加载完成 (模型: {config.llm_model}, 嵌入模型: {config.embedding_model})")
        
        logger.info("📦 步骤 2/5: 创建 RAG Agent 实例...")
        rag_agent = RAGAgent(config=config)
        logger.info("   ✓ RAG Agent 实例创建成功")

        # 检查向量存储是否存在
        docs_dir = "./documents"
        vectorstore_exists = os.path.exists(config.persist_directory)
        logger.info(f"📂 步骤 3/5: 检查向量存储 (目录: {config.persist_directory})...")

        if not vectorstore_exists:
            # 首次运行，需要创建向量存储
            logger.info("   ℹ️  向量存储不存在，需要创建")
            if not os.path.exists(docs_dir):
                os.makedirs(docs_dir, exist_ok=True)
                logger.warning(f"   ⚠️  文档目录不存在，已创建: {docs_dir}")
                return False

            # 加载文档并创建向量存储
            try:
                logger.info(f"   📄 正在从 {docs_dir} 加载文档...")
                documents = rag_agent.load_documents(docs_dir)

                if not documents:
                    logger.warning(f"   ⚠️  {docs_dir} 目录中没有找到文档")
                    return False

                logger.info(f"   ✓ 成功加载 {len(documents)} 个文档")
                logger.info("   🗄️  正在创建向量存储...")
                # 创建向量存储
                rag_agent.create_vectorstore(documents)
                logger.info(f"   ✓ 向量存储创建成功（从 {docs_dir} 加载了 {len(documents)} 个文档）")
            except (DocumentLoadError, VectorStoreError) as e:
                logger.error(f"   ❌ 创建向量存储失败: {e}", exc_info=True)
                return False
        else:
            # 加载已存在的向量存储
            try:
                logger.info("   ℹ️  向量存储已存在，正在加载...")
                rag_agent.load_vectorstore()

                # 验证向量存储是否有数据
                try:
                    collection = rag_agent.vectorstore._collection
                    count = collection.count()
                    if count == 0:
                        logger.warning("   ⚠️  向量存储为空")
                        return False
                    logger.info(f"   ✓ 向量存储加载成功，包含 {count} 个文档块")
                except Exception as e:
                    logger.warning(f"   ⚠️  无法验证向量存储数据: {e}")

                # 检查 documents 目录是否有新文档需要添加（增量模式）
                if os.path.exists(docs_dir):
                    try:
                        all_documents = rag_agent.load_documents(docs_dir)
                        if all_documents:
                            logger.info(f"   📄 检测到 {len(all_documents)} 个文档，正在检查新文件...")
                            # 使用增量模式，只添加新文件或更新的文件
                            result = rag_agent.add_documents_to_vectorstore(
                                all_documents, incremental=True)

                            if result['added_files'] > 0 or result['updated_files'] > 0:
                                logger.info(
                                    f"   ✓ 增量更新完成: "
                                    f"新增 {result['added_files']} 个文件, "
                                    f"更新 {result['updated_files']} 个文件, "
                                    f"添加 {result['added_chunks']} 个文档块, "
                                    f"删除 {result['deleted_chunks']} 个旧文档块")
                            else:
                                logger.info("   ℹ️  没有新文档或更新的文档需要添加")
                    except DocumentLoadError as e:
                        logger.warning(f"   ⚠️  加载新文档时出错: {e}")
                    except VectorStoreError as e:
                        logger.error(f"   ❌ 添加新文档到向量存储失败: {e}", exc_info=True)

            except VectorStoreError as e:
                logger.error(f"   ❌ 加载向量存储失败: {e}", exc_info=True)
                return False

        # 创建问答链
        logger.info("🔗 步骤 4/5: 创建问答链...")
        rag_agent.create_qa_chain()
        logger.info("   ✓ 问答链创建成功")
        
        logger.info("✅ 步骤 5/5: RAG Agent 初始化完成！")
        logger.info("=" * 60)
        _startup_complete = True
        return True

    except Exception as e:
        logger.error(f"❌ 初始化 RAG Agent 失败: {e}", exc_info=True)
        logger.error("=" * 60)
        global _startup_failed
        _startup_failed = True
        return False
    finally:
        _initialization_lock = False


async def handle_file_upload(files):
    """
    处理文件上传

    Args:
        files: 上传的文件列表
    """
    global rag_agent
    import shutil
    import tempfile

    try:
        if not files:
            await cl.Message(content="❌ 未选择文件", author="System").send()
            return

        # 创建临时目录存储上传的文件
        temp_dir = tempfile.mkdtemp()
        uploaded_files = []

        for file in files:
            # 保存文件到临时目录
            file_path = os.path.join(temp_dir, file.name)
            with open(file_path, "wb") as f:
                content = file.read()
                f.write(content)
            uploaded_files.append(file.name)
            logger.info(f"已保存上传的文件: {file.name} ({len(content)} 字节)")

        # 显示处理进度
        progress_msg = await cl.Message(
            content=f"📤 正在处理 {len(uploaded_files)} 个文件...",
            author="System").send()

        # 确保 Agent 已初始化
        if rag_agent is None:
            progress_msg.content = "🔄 正在初始化 RAG Agent..."
            await progress_msg.update()
            if not await initialize_rag_agent():
                progress_msg.content = "❌ RAG Agent 初始化失败，请刷新页面重试"
                await progress_msg.update()
                return

        # 加载文档（允许临时目录）
        documents = rag_agent.load_documents(str(temp_dir), allow_temp_dir=True)

        if not documents:
            progress_msg.content = "❌ 未找到任何文档"
            await progress_msg.update()
            return

        # 检查向量存储是否已存在
        if rag_agent.vectorstore is not None:
            # 向现有向量存储添加新文档（使用增量模式，自动去重）
            progress_msg.content = f"📚 正在检查并添加新文档（已加载 {len(documents)} 个文档）..."
            await progress_msg.update()
            # add_documents_to_vectorstore 内部会重新初始化检索器和问答链
            result = rag_agent.add_documents_to_vectorstore(documents, incremental=True)

            if result['added_files'] > 0 or result['updated_files'] > 0:
                progress_msg.content = (
                    f"✅ 成功处理文档！\n\n"
                    f"新增文件: {result['added_files']} 个\n"
                    f"更新文件: {result['updated_files']} 个\n"
                    f"添加文档块: {result['added_chunks']} 个\n"
                    f"删除旧文档块: {result['deleted_chunks']} 个\n\n"
                    f"现在可以开始提问了。"
                )
            else:
                progress_msg.content = (
                    "ℹ️ 所有文档已存在且未更新，无需重复添加。\n\n"
                    "现在可以开始提问了。"
                )
        else:
            # 创建新的向量存储
            progress_msg.content = f"📚 正在创建向量存储（已加载 {len(documents)} 个文档）..."
            await progress_msg.update()
            rag_agent.create_vectorstore(documents)
            # 创建向量存储后需要创建问答链
            rag_agent.create_qa_chain()
            progress_msg.content = f"✅ 成功处理 {len(documents)} 个文档！\n\n现在可以开始提问了。"

        # 清理临时文件
        shutil.rmtree(temp_dir, ignore_errors=True)

        progress_msg.content = f"✅ 成功处理 {len(documents)} 个文档！\n\n现在可以开始提问了。"
        await progress_msg.update()

    except DocumentLoadError as e:
        logger.error(f"文档加载失败: {e}", exc_info=True)
        await cl.Message(content=f"❌ 文档加载失败: {str(e)}", author="System").send()
    except VectorStoreError as e:
        logger.error(f"创建向量存储失败: {e}", exc_info=True)
        await cl.Message(content=f"❌ 创建向量存储失败: {str(e)}",
                         author="System").send()
    except Exception as e:
        logger.error(f"处理文档失败: {e}", exc_info=True)
        await cl.Message(content=f"❌ 处理文档失败: {str(e)}", author="System").send()


@cl.on_message
async def main(message: cl.Message):
    """处理用户消息"""
    global rag_agent

    # 检查消息是否包含文件附件
    if message.elements:
        # 处理文件上传
        files = []
        for element in message.elements:
            if hasattr(element, 'path') and element.path:
                # 读取文件内容
                try:
                    with open(element.path, "rb") as f:
                        file_content = f.read()
                    # 创建一个简单的文件对象
                    class FileObj:
                        def __init__(self, name, content):
                            self.name = name
                            self._content = content
                        def read(self):
                            return self._content
                    files.append(FileObj(element.name or element.path, file_content))
                except Exception as e:
                    logger.error(f"读取文件失败: {e}", exc_info=True)

        if files:
            await handle_file_upload(files)
            return

    # 确保 Agent 已初始化
    if rag_agent is None and not await initialize_rag_agent():
        await cl.Message(
            content=
            "❌ RAG Agent 初始化失败。请检查：\n1. 向量存储是否存在\n2. 文档目录是否有文档\n3. 查看日志获取详细信息",
            author="System").send()
        return

    # 处理查询
    try:
        result = rag_agent.query(message.content)
        answer = result.get("answer", "抱歉，无法生成答案")
        source_docs = result.get("source_documents", [])

        # 构建回复消息
        response = f"{answer}\n\n"
        if source_docs:
            response += f"📚 参考了 {len(source_docs)} 个文档块"

        await cl.Message(content=response, author="Assistant").send()

    except Exception as e:
        logger.error(f"处理消息失败: {e}", exc_info=True)
        await cl.Message(content=f"❌ 处理消息时出错: {str(e)}",
                         author="System").send()


@cl.on_chat_start
async def start():
    """
    聊天开始时初始化 RAG Agent
    使用全局变量缓存，避免重复初始化
    """
    global rag_agent, _startup_complete, _startup_failed, _startup_task

    # 如果 Agent 已经初始化，直接使用（避免重复初始化）
    if rag_agent is not None and rag_agent.qa_chain is not None and _startup_complete:
        logger.info("RAG Agent 已存在，复用现有实例")
        await cl.Message(
            content=
            "✅ RAG Agent 已就绪！\n\n你可以开始提问了，我会基于你的文档回答问题。\n\n💡 提示：\n- 直接输入问题开始对话\n- 拖拽文件上传新文档",
            author="System").send()
        return

    # 如果后台初始化任务还在运行，等待它完成
    if not _startup_complete and not _startup_failed:
        # 启动后台初始化任务（如果还没启动）
        if _startup_task is None:
            _startup_task = asyncio.create_task(startup_initialization())
        
        # 等待初始化完成（最多等待30秒）
        for _ in range(60):  # 30秒 = 60 * 0.5秒
            await asyncio.sleep(0.5)
            if _startup_complete:
                break
            if _startup_failed:
                break

    # 如果后台初始化失败或未完成，尝试在前台初始化
    if not _startup_complete:
        # 尝试初始化（使用统一的初始化函数）
        init_msg = await cl.Message(content="🔄 正在初始化 RAG Agent...",
                                    author="System").send()

        # 使用统一的初始化函数
        success = await initialize_rag_agent()

        if success:
            init_msg.content = "✅ RAG Agent 已就绪！\n\n你可以开始提问了，我会基于你的文档回答问题。\n\n💡 提示：\n- 直接输入问题开始对话\n- 拖拽文件上传新文档"
            await init_msg.update()
        else:
            # 检查具体失败原因，提供更友好的提示
            config = RAGConfig()  # 自动从环境变量读取
            docs_dir = "./documents"
            vectorstore_exists = os.path.exists(config.persist_directory)

            if not vectorstore_exists:
                if not os.path.exists(docs_dir):
                    init_msg.content = f"❌ 文档目录不存在: {docs_dir}\n\n请创建目录并添加文档后刷新页面。"
                else:
                    init_msg.content = f"❌ 向量存储未创建\n\n请在 {docs_dir} 目录中添加 PDF 或 TXT 格式的文档，然后刷新页面。"
            else:
                init_msg.content = "❌ 向量存储加载失败\n\n请检查日志获取详细信息，或删除向量存储目录后重新创建。"
            await init_msg.update()
    else:
        # 后台初始化成功，直接显示就绪消息
        await cl.Message(
            content=
            "✅ RAG Agent 已就绪！\n\n你可以开始提问了，我会基于你的文档回答问题。\n\n💡 提示：\n- 直接输入问题开始对话\n- 拖拽文件上传新文档",
            author="System").send()
