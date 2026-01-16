"""
RAG Agent 主程序入口
"""

import os
import sys
from rag_agent import RAGAgent
from dotenv import load_dotenv

load_dotenv()


def check_api_key():
    """检查DeepSeek API密钥"""
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        print("错误: 未找到 DEEPSEEK_API_KEY")
        print("请在 .env 文件中设置你的 DeepSeek API 密钥")
        print("或者设置环境变量: $env:DEEPSEEK_API_KEY='your-api-key' (PowerShell)")
        print("                      export DEEPSEEK_API_KEY='your-api-key' (Linux/Mac)")
        return False
    return True


def main():
    """主函数"""
    print("=" * 60)
    print("RAG Agent - 基于检索增强生成的AI智能体")
    print("=" * 60)
    
    # 检查API密钥
    if not check_api_key():
        sys.exit(1)
    
    # 初始化RAG Agent
    agent = RAGAgent(
        persist_directory="./chroma_db",
        embedding_model="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
        llm_model="deepseek-chat"
    )
    
    # 检查是否已有向量存储
    docs_dir = "./documents"
    vectorstore_exists = os.path.exists("./chroma_db")
    
    if not vectorstore_exists:
        print("\n首次运行，需要创建向量存储")
        
        # 检查文档目录
        if not os.path.exists(docs_dir):
            print(f"\n创建文档目录: {docs_dir}")
            os.makedirs(docs_dir, exist_ok=True)
            print(f"请将你的文档（PDF或TXT格式）放入 {docs_dir} 目录")
            print("然后重新运行此程序")
            return
        
        # 加载文档
        try:
            documents = agent.load_documents(docs_dir)
            if not documents:
                print(f"\n{docs_dir} 目录中没有找到文档")
                print("请添加PDF或TXT格式的文档后重新运行")
                return
            
            # 创建向量存储
            agent.create_vectorstore(documents)
        except Exception as e:
            print(f"错误: {e}")
            return
    else:
        print("\n检测到已存在的向量存储，正在加载...")
        try:
            agent.load_vectorstore()
        except Exception as e:
            print(f"加载向量存储失败: {e}")
            return
    
    # 创建问答链
    try:
        agent.create_qa_chain(k=4)
    except Exception as e:
        print(f"创建问答链失败: {e}")
        return
    
    # 交互式问答
    print("\n" + "=" * 60)
    print("RAG Agent 已就绪！")
    print("输入 'quit' 或 'exit' 退出")
    print("=" * 60 + "\n")
    
    while True:
        try:
            question = input("请输入你的问题: ").strip()
            
            if question.lower() in ['quit', 'exit', '退出']:
                print("再见！")
                break
            
            if not question:
                continue
            
            # 查询
            result = agent.query(question)
            
            # 显示结果
            print("\n" + "-" * 60)
            print("回答:")
            print(result["answer"])
            print("-" * 60)
            
            # 显示源文档
            if result["source_documents"]:
                print(f"\n参考了 {len(result['source_documents'])} 个文档块")
                print("-" * 60)
            
            print("\n")
            
        except KeyboardInterrupt:
            print("\n\n再见！")
            break
        except Exception as e:
            print(f"错误: {e}\n")


if __name__ == "__main__":
    main()
