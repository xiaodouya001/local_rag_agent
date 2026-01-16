#!/bin/bash
# Bash 脚本：使用 Python 3.12 创建虚拟环境

# 设置脚本在出错时退出
set -e

# 设置颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${CYAN}========================================"
echo -e "RAG Agent - Python 3.12 虚拟环境设置"
echo -e "========================================${NC}"
echo ""

# 检查 Python 3.12
echo -e "${YELLOW}正在检查 Python 3.12...${NC}"

python312=""

# 尝试不同的命令
commands=("python3.12" "python3" "python")

for cmd in "${commands[@]}"; do
    if command -v "$cmd" >/dev/null 2>&1; then
        version=$($cmd --version 2>&1)
        if echo "$version" | grep -q "Python 3\.12"; then
            python312="$cmd"
            echo -e "${GREEN}[OK] 找到 Python 3.12: $version${NC}"
            break
        fi
    fi
done

if [ -z "$python312" ]; then
    echo -e "${RED}[ERROR] 未找到 Python 3.12${NC}"
    echo ""
    echo -e "${YELLOW}请先安装 Python 3.12:${NC}"
    echo -e "${YELLOW}1. 访问 https://www.python.org/downloads/release/python-3120/${NC}"
    echo -e "${YELLOW}2. 下载并安装 Python 3.12${NC}"
    echo -e "${YELLOW}3. 确保 Python 3.12 在 PATH 中${NC}"
    echo ""
    exit 1
fi

# 删除旧的虚拟环境
if [ -d "venv" ]; then
    echo -e "${YELLOW}检测到已存在的虚拟环境...${NC}"
    
    # 检查是否有 Python 进程正在使用虚拟环境（仅在 Linux/Mac 上执行）
    if command -v pgrep >/dev/null 2>&1; then
        if pgrep -f "venv/(bin|Scripts)/python" >/dev/null 2>&1; then
            echo -e "${YELLOW}警告: 检测到正在运行的 Python 进程，正在尝试关闭...${NC}"
            pkill -f "venv/(bin|Scripts)/python" || true
            sleep 2
        fi
    fi
    
    echo -e "${YELLOW}正在删除旧的虚拟环境...${NC}"
    
    # 尝试删除，如果失败则重命名
    if rm -rf venv 2>/dev/null; then
        echo -e "${GREEN}[OK] 旧虚拟环境已删除${NC}"
    else
        echo -e "${YELLOW}警告: 无法删除虚拟环境（文件可能被占用）${NC}"
        echo -e "${YELLOW}尝试重命名为 venv_old...${NC}"
        if [ -d "venv_old" ]; then
            rm -rf venv_old
        fi
        if mv venv venv_old 2>/dev/null; then
            echo -e "${GREEN}[OK] 虚拟环境已重命名为 venv_old${NC}"
            echo -e "${CYAN}提示: 可以稍后手动删除 venv_old 目录${NC}"
        else
            echo -e "${RED}错误: 无法删除或重命名虚拟环境${NC}"
            echo -e "${YELLOW}将使用现有虚拟环境继续安装依赖${NC}"
            SKIP_VENV_CREATION=true
        fi
    fi
fi

# 创建新的虚拟环境（如果之前没有跳过）
if [ -z "$SKIP_VENV_CREATION" ]; then
    echo ""
    echo -e "${YELLOW}正在使用 Python 3.12 创建虚拟环境...${NC}"
    
    if $python312 -m venv venv; then
        echo -e "${GREEN}[OK] 虚拟环境创建成功${NC}"
    else
        echo -e "${RED}[ERROR] 创建虚拟环境失败${NC}"
        exit 1
    fi
else
    echo ""
    echo -e "${YELLOW}使用现有虚拟环境...${NC}"
fi

# 确定虚拟环境中 Python 的路径
echo ""
echo -e "${YELLOW}正在定位虚拟环境中的 Python...${NC}"

PYTHON_CMD=""
if [ -f "venv/Scripts/python.exe" ]; then
    # Windows (Git Bash, PowerShell, CMD)
    PYTHON_CMD="./venv/Scripts/python.exe"
elif [ -f "venv/Scripts/python" ]; then
    # Windows (Git Bash) - 有时没有 .exe
    PYTHON_CMD="./venv/Scripts/python"
elif [ -f "venv/bin/python" ]; then
    # Linux/Mac
    PYTHON_CMD="./venv/bin/python"
fi

if [ -z "$PYTHON_CMD" ]; then
    echo -e "${RED}[ERROR] 找不到虚拟环境中的 Python${NC}"
    echo -e "${YELLOW}虚拟环境可能未正确创建，请检查错误信息${NC}"
    exit 1
fi

# 验证 Python 是否可用
if ! $PYTHON_CMD --version >/dev/null 2>&1; then
    echo -e "${RED}[ERROR] 虚拟环境中的 Python 无法执行${NC}"
    exit 1
fi

echo -e "${GREEN}[OK] 找到 Python: $($PYTHON_CMD --version)${NC}"

# 尝试激活虚拟环境（可选，用于设置 PATH 等环境变量）
if [ -f "venv/Scripts/activate" ]; then
    # Windows - 在 Git Bash 中，activate 脚本可能不兼容，但我们仍可以尝试
    # 使用 source 可能在 Git Bash 中失败，但不会影响后续操作
    source venv/Scripts/activate 2>/dev/null || true
elif [ -f "venv/bin/activate" ]; then
    # Linux/Mac
    source venv/bin/activate
fi

# 升级 pip
echo ""
echo -e "${YELLOW}正在升级 pip...${NC}"
$PYTHON_CMD -m pip install --upgrade pip

# 安装依赖
echo ""
echo -e "${YELLOW}正在安装依赖包（这可能需要几分钟）...${NC}"

# 检测操作系统
OS_TYPE="unknown"
if [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "win32" ]] || [[ -n "$WINDIR" ]]; then
    OS_TYPE="windows"
fi

# 安装依赖（根据操作系统使用不同策略）
INSTALL_SUCCESS=false

if [ "$OS_TYPE" == "windows" ]; then
    echo -e "${CYAN}检测到 Windows 系统，优先使用预编译包...${NC}"
    
    # 首先尝试使用 prefer-binary 安装
    echo -e "${YELLOW}尝试使用预编译包安装...${NC}"
    if $PYTHON_CMD -m pip install --prefer-binary -r requirements.txt; then
        INSTALL_SUCCESS=true
    else
        # 如果失败，检查是否是编译错误
        PIP_OUTPUT=$($PYTHON_CMD -m pip install -r requirements.txt 2>&1 || true)
        
        if echo "$PIP_OUTPUT" | grep -qi "Microsoft Visual C\+\+.*required\|failed to build.*chroma-hnswlib\|error: subprocess-exited-with-error.*chroma-hnswlib"; then
            echo ""
            echo -e "${YELLOW}检测到编译错误（chroma-hnswlib），尝试替代方案...${NC}"
            
            # 先安装其他依赖（不包含 ChromaDB）
            echo -e "${YELLOW}安装其他依赖包...${NC}"
            $PYTHON_CMD -m pip install --prefer-binary langchain langchain-community langchain-text-splitters langchain-openai langchain-huggingface sentence-transformers transformers huggingface-hub torch pypdf2 tiktoken python-dotenv colorama chainlit 2>&1 || true
            
            # 尝试安装 ChromaDB（可能失败，但不影响其他功能）
            echo -e "${YELLOW}尝试安装 ChromaDB...${NC}"
            if ! $PYTHON_CMD -m pip install --prefer-binary chromadb langchain-chroma 2>&1; then
                echo ""
                echo -e "${RED}========================================"
                echo -e "ChromaDB 安装失败（需要编译）"
                echo -e "========================================${NC}"
                echo ""
                echo -e "${YELLOW}解决方案：${NC}"
                echo -e "1. 安装 Microsoft Visual C++ Build Tools:"
                echo -e "   https://visualstudio.microsoft.com/visual-cpp-build-tools/"
                echo -e "   下载后安装 'C++ build tools' 工作负载"
                echo ""
                echo -e "2. 安装完成后，重新运行此脚本或执行:"
                echo -e "   $PYTHON_CMD -m pip install chromadb langchain-chroma"
                echo ""
                echo -e "${YELLOW}注意：没有 ChromaDB，向量存储功能将不可用${NC}"
                INSTALL_SUCCESS=false
            else
                INSTALL_SUCCESS=true
            fi
        else
            # 其他类型的错误
            echo ""
            echo -e "${RED}[ERROR] 依赖安装失败${NC}"
            echo "$PIP_OUTPUT"
            exit 1
        fi
    fi
else
    # Linux/Mac 正常安装
    if $PYTHON_CMD -m pip install -r requirements.txt; then
        INSTALL_SUCCESS=true
    else
        echo ""
        echo -e "${RED}[ERROR] 依赖安装失败，请检查错误信息${NC}"
        exit 1
    fi
fi

# 验证关键包是否安装成功
echo ""
echo -e "${YELLOW}验证关键依赖是否安装成功...${NC}"
LANGCHAIN_OK=false
CHROMADB_OK=false

if $PYTHON_CMD -c "import langchain" 2>/dev/null; then
    echo -e "${GREEN}[OK] LangChain 安装成功${NC}"
    LANGCHAIN_OK=true
else
    echo -e "${RED}[ERROR] LangChain 未安装${NC}"
fi

if $PYTHON_CMD -c "import chromadb; import langchain_chroma" 2>/dev/null; then
    echo -e "${GREEN}[OK] ChromaDB 安装成功${NC}"
    CHROMADB_OK=true
else
    echo -e "${YELLOW}[WARNING] ChromaDB 未安装或安装失败${NC}"
    if [ "$OS_TYPE" == "windows" ]; then
        echo -e "${YELLOW}如果后续需要使用向量存储功能，请安装 Visual C++ Build Tools 后重新安装 ChromaDB${NC}"
    fi
fi

if [ "$LANGCHAIN_OK" = true ]; then
    echo ""
    echo -e "${GREEN}========================================"
    if [ "$CHROMADB_OK" = true ]; then
        echo -e "[OK] 设置完成！所有依赖已安装"
    else
        echo -e "[OK] 设置完成！部分依赖未安装（ChromaDB）"
    fi
    echo -e "========================================${NC}"
    echo ""
    echo -e "${CYAN}运行以下命令启动程序:${NC}"
    if [ -f "venv/Scripts/python.exe" ] || [ -f "venv/Scripts/python" ]; then
        echo -e "  ./venv/Scripts/python.exe app/main.py"
        echo -e "  或: source venv/Scripts/activate && python app/main.py"
    else
        echo -e "  ./venv/bin/python app/main.py"
        echo -e "  或: source venv/bin/activate && python app/main.py"
    fi
    echo ""
    echo -e "${CYAN}或启动 Web 界面:${NC}"
    if [ -f "venv/Scripts/python.exe" ] || [ -f "venv/Scripts/python" ]; then
        echo -e "  ./venv/Scripts/python.exe -m chainlit run app/chainlit_app.py"
    else
        echo -e "  ./venv/bin/python -m chainlit run app/chainlit_app.py"
    fi
    echo ""
else
    echo ""
    echo -e "${RED}[ERROR] 核心依赖安装失败，请检查错误信息${NC}"
    exit 1
fi
