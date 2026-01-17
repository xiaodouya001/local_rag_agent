"""
测试 RAG 工作流程，展示 DeepSeek API 的作用
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))

from dotenv import load_dotenv
from rag_agent import RAGAgent
from ui import ui

load_dotenv()


def test_rag_workflow():
    """测试 RAG 工作流程"""

    ui.print_header("RAG 工作流程测试", icon='brain')

    # 初始化 RAG Agent
    ui.print_section("初始化 RAG Agent", icon='gear')
    ui.print_progress("正在初始化")
    agent = RAGAgent(persist_directory="./chroma_db",
                     embedding_model="all-MiniLM-L6-v2",
                     llm_model="deepseek-chat")
    ui.print_progress_done()

    # 加载向量存储
    if os.path.exists("./chroma_db"):
        ui.print_progress("正在加载向量存储")
        agent.load_vectorstore()
        ui.print_success("向量存储加载成功")
    else:
        ui.print_info("首次运行，创建向量存储...")
        ui.print_progress("正在加载文档")
        documents = agent.load_documents("./documents")
        ui.print_progress_done()
        ui.print_progress("正在创建向量存储")
        agent.create_vectorstore(documents)
        ui.print_success("向量存储创建成功")

    # 创建问答链
    ui.print_progress("正在创建问答链")
    agent.create_qa_chain(k=4)
    ui.print_success("问答链创建成功")

    # 测试问题
    questions = [
        "什么是RAG", "RAG 有哪些主要特点？", "如果要实现一个 RAG 系统，需要哪些技术组件？",
        "RAG 技术适合解决哪些类型的问题？"
    ]

    for idx, question in enumerate(questions, 1):
        ui.print_header(f"问题 {idx}/{len(questions)}: {question}",
                        icon='question',
                        color='magenta')

        # 1. 显示检索到的文档
        ui.print_step(1, "检索相关文档（本地完成，不使用 DeepSeek API）", icon='search')
        try:
            source_documents = agent.retriever.invoke(question)
            ui.print_success(f"检索到 {len(source_documents)} 个相关文档块")

            for i, doc in enumerate(source_documents, 1):
                ui.print_document_block(i, doc.page_content, max_length=300)
        except Exception as e:
            ui.print_error(f"检索失败: {e}")
            continue

        # 2. 调用 DeepSeek API
        ui.print_step(2, "调用 DeepSeek API 生成回答", icon='lightning')
        ui.print_progress("正在调用 DeepSeek API")
        result = agent.query(question)
        ui.print_progress_done()

        # 3. 显示最终回答
        ui.print_section("最终回答", icon='sparkles')
        ui.print_answer(result['answer'])

        # 4. 对比分析
        ui.print_section("对比分析", icon='brain')
        ui.print_box(source_documents[0].page_content[:200] +
                     "..." if source_documents else "无",
                     title="原始文档（检索到的内容）",
                     color='cyan')
        ui.print_box(result['answer'][:200] +
                     "..." if len(result['answer']) > 200 else result['answer'],
                     title="DeepSeek 生成的回答",
                     color='green')

        # 等待用户输入继续
        if idx < len(questions):
            ui.print_info("按 Enter 继续下一个问题...")
            input()
            ui.print_separator()
            print()


if __name__ == "__main__":
    try:
        test_rag_workflow()
        ui.print_header("测试完成", icon='success', color='green')
    except KeyboardInterrupt:
        ui.print_warning("\n测试已取消")
    except Exception as e:
        ui.print_error(f"\n测试失败: {e}")
        import traceback
        traceback.print_exc()
