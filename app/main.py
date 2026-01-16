"""
RAG Agent 主程序入口
"""

import os
import sys
import io
import logging
from pathlib import Path

# 处理直接运行时的导入路径问题
if __name__ == "__main__":
    # 添加项目根目录到路径
    project_root = Path(__file__).parent.parent
    sys.path.insert(0, str(project_root))
    from app.rag_agent import RAGAgent
    from app.config import RAGConfig
    from app.exceptions import ConfigurationError, DocumentLoadError, VectorStoreError
    from app.ui import ui
    from app.logging_config import setup_logging
else:
    # 作为模块导入时使用相对导入
    from .rag_agent import RAGAgent
    from .config import RAGConfig
    from .exceptions import ConfigurationError, DocumentLoadError, VectorStoreError
    from .ui import ui
    from .logging_config import setup_logging

from dotenv import load_dotenv

# 设置标准输出编码为 UTF-8，解决中文显示问题
if sys.platform == 'win32':
    try:
        # Windows 系统设置控制台编码
        if hasattr(sys.stdout, 'buffer'):
            sys.stdout = io.TextIOWrapper(
                sys.stdout.buffer, 
                encoding='utf-8', 
                errors='replace'
            )
        if hasattr(sys.stderr, 'buffer'):
            sys.stderr = io.TextIOWrapper(
                sys.stderr.buffer, 
                encoding='utf-8', 
                errors='replace'
            )
    except (AttributeError, ValueError):
        # 如果已经是 TextIOWrapper 或设置失败，尝试重新配置
        try:
            if hasattr(sys.stdout, 'reconfigure'):
                sys.stdout.reconfigure(encoding='utf-8', errors='replace')
            if hasattr(sys.stderr, 'reconfigure'):
                sys.stderr.reconfigure(encoding='utf-8', errors='replace')
        except (AttributeError, ValueError):
            # 如果都失败了，至少尝试设置环境变量
            os.environ['PYTHONIOENCODING'] = 'utf-8'

load_dotenv()

# 配置日志（使用统一的日志配置函数）
# 从环境变量读取日志级别，默认为INFO
log_level = os.getenv('LOG_LEVEL', 'INFO')
setup_logging(log_level=log_level, use_json=False)

logger = logging.getLogger(__name__)


def check_api_key() -> bool:
    """
    检查DeepSeek API密钥
    
    Returns:
        是否找到有效的API密钥
    """
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        ui.print_error("未找到 DEEPSEEK_API_KEY")
        ui.print_info("请在 .env 文件中设置你的 DeepSeek API 密钥")
        ui.print_info("或者设置环境变量:")
        ui.print_info("  PowerShell: $env:DEEPSEEK_API_KEY='your-api-key'")
        logger.error("未找到 DEEPSEEK_API_KEY")
        return False
    return True


def main() -> None:
    """主函数"""
    ui.print_header("RAG Agent - 基于检索增强生成的AI智能体", icon='rocket')
    
    # 检查API密钥
    if not check_api_key():
        sys.exit(1)
    
    # 初始化RAG Agent
    try:
        ui.print_progress("正在初始化 RAG Agent")
        config = RAGConfig.from_env()
        agent = RAGAgent(config=config)
        ui.print_progress_done()
        logger.info("RAG Agent 初始化成功")
    except ConfigurationError as e:
        ui.print_error(f"配置错误: {e}")
        logger.error(f"配置错误: {e}", exc_info=True)
        sys.exit(1)
    except Exception as e:
        ui.print_error(f"初始化失败: {e}")
        logger.error(f"初始化失败: {e}", exc_info=True)
        sys.exit(1)
    
    # 检查是否已有向量存储
    docs_dir = "./documents"
    vectorstore_exists = os.path.exists("./chroma_db")
    
    if not vectorstore_exists:
        ui.print_section("首次运行，需要创建向量存储", icon='gear')
        
        # 检查文档目录
        if not os.path.exists(docs_dir):
            ui.print_info(f"创建文档目录: {docs_dir}")
            os.makedirs(docs_dir, exist_ok=True)
            ui.print_warning(f"请将你的文档（PDF或TXT格式）放入 {docs_dir} 目录")
            ui.print_info("然后重新运行此程序")
            logger.warning(f"文档目录不存在，已创建: {docs_dir}")
            return
        
        # 加载文档
        try:
            ui.print_progress("正在加载文档")
            documents = agent.load_documents(docs_dir)
            ui.print_progress_done()
            ui.print_success(f"已加载 {len(documents)} 个文档")
            
            if not documents:
                ui.print_error(f"{docs_dir} 目录中没有找到文档")
                ui.print_info("请添加PDF或TXT格式的文档后重新运行")
                logger.warning(f"{docs_dir} 目录中没有找到文档")
                return
            
            # 创建向量存储
            ui.print_progress("正在创建向量存储")
            agent.create_vectorstore(documents)
            ui.print_success("向量存储创建成功")
        except DocumentLoadError as e:
            ui.print_error(f"文档加载失败: {e}")
            logger.error(f"文档加载失败: {e}", exc_info=True)
            return
        except VectorStoreError as e:
            ui.print_error(f"创建向量存储失败: {e}")
            logger.error(f"创建向量存储失败: {e}", exc_info=True)
            return
        except Exception as e:
            ui.print_error(f"创建向量存储失败: {e}")
            logger.error(f"创建向量存储失败: {e}", exc_info=True)
            return
    else:
        ui.print_section("检测到已存在的向量存储，正在加载...", icon='book')
        try:
            ui.print_progress("正在加载向量存储")
            agent.load_vectorstore()
            ui.print_success("向量存储加载成功")
        except VectorStoreError as e:
            ui.print_error(f"加载向量存储失败: {e}")
            logger.error(f"加载向量存储失败: {e}", exc_info=True)
            return
        except Exception as e:
            ui.print_error(f"加载向量存储失败: {e}")
            logger.error(f"加载向量存储失败: {e}", exc_info=True)
            return
    
    # 创建问答链
    try:
        ui.print_progress("正在创建问答链")
        agent.create_qa_chain()
        ui.print_success("问答链创建成功")
    except Exception as e:
        ui.print_error(f"创建问答链失败: {e}")
        logger.error(f"创建问答链失败: {e}", exc_info=True)
        return
    
    # 检查是否在交互式环境中运行
    is_interactive = sys.stdin.isatty() and sys.stdout.isatty()
    
    if not is_interactive:
        ui.print_warning("检测到非交互式环境，将跳过交互式问答")
        ui.print_info("提示: 请在交互式终端中运行此程序")
        logger.warning("检测到非交互式环境")
        return
    
    # 交互式问答
    ui.print_header("RAG Agent 已就绪！", icon='sparkles', color='green')
    ui.print_info("输入 'quit' 或 'exit' 退出")
    ui.print_separator()
    logger.info("RAG Agent 已就绪，进入交互式问答模式")
    
    while True:
        try:
            # 使用 try-except 确保在非交互式环境中也能正常退出
            try:
                ui.print_question("请输入你的问题")
                question = input("→ ").strip()
            except (EOFError, OSError):
                # EOFError: 输入流关闭（非交互式环境或管道输入）
                # OSError: 输入设备不可用
                ui.print_warning("检测到输入流已关闭，退出程序")
                logger.info("输入流已关闭，退出程序")
                break
            
            if question.lower() in ['quit', 'exit', '退出']:
                ui.print_success("再见！")
                logger.info("用户退出程序")
                break
            
            if not question:
                continue
            
            # 查询
            ui.print_progress("正在处理问题")
            result = agent.query(question)
            ui.print_progress_done()
            
            # 显示结果
            ui.print_answer(result["answer"])
            
            # 显示源文档
            if result["source_documents"]:
                ui.print_info(f"参考了 {len(result['source_documents'])} 个文档块")
                ui.print_separator()
            
        except KeyboardInterrupt:
            # 用户按 Ctrl+C
            ui.print_warning("\n程序已中断，再见！")
            logger.info("用户中断程序")
            break
        except Exception as e:
            ui.print_error(f"处理问题时出错: {e}")
            logger.error(f"处理问题时出错: {e}", exc_info=True)
            # 继续循环，不退出程序


if __name__ == "__main__":
    main()
