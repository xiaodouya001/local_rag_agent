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
    
    # 检查是否有 Python 进程正在使用虚拟环境
    if pgrep -f "venv/bin/python" >/dev/null 2>&1; then
        echo -e "${YELLOW}警告: 检测到正在运行的 Python 进程，正在尝试关闭...${NC}"
        pkill -f "venv/bin/python" || true
        sleep 2
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

# 激活虚拟环境
echo ""
echo -e "${YELLOW}正在激活虚拟环境...${NC}"
source venv/bin/activate

# 升级 pip
echo ""
echo -e "${YELLOW}正在升级 pip...${NC}"
python -m pip install --upgrade pip

# 安装依赖
echo ""
echo -e "${YELLOW}正在安装依赖包（这可能需要几分钟）...${NC}"
if python -m pip install -r requirements.txt; then
    echo ""
    echo -e "${GREEN}========================================"
    echo -e "[OK] 设置完成！"
    echo -e "========================================${NC}"
    echo ""
    echo -e "${CYAN}运行以下命令启动程序:${NC}"
    echo -e "  python app/main.py"
    echo ""
    echo -e "${CYAN}或启动 Web 界面:${NC}"
    echo -e "  chainlit run app/chainlit_app.py"
    echo ""
else
    echo ""
    echo -e "${RED}[ERROR] 依赖安装失败，请检查错误信息${NC}"
    exit 1
fi
