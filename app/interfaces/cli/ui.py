"""
美观的控制台输出工具
提供颜色、图标和格式化功能
"""


# 尝试导入 colorama，如果没有则使用简单的 ANSI 转义码
try:
    from colorama import Back
    from colorama import Fore
    from colorama import init
    from colorama import Style
    init(autoreset=True)
    HAS_COLORAMA = True
except ImportError:
    HAS_COLORAMA = False

    # 简单的 ANSI 转义码
    class Fore:
        BLACK = '\033[30m'
        RED = '\033[31m'
        GREEN = '\033[32m'
        YELLOW = '\033[33m'
        BLUE = '\033[34m'
        MAGENTA = '\033[35m'
        CYAN = '\033[36m'
        WHITE = '\033[37m'
        RESET = '\033[0m'

    class Style:
        BRIGHT = '\033[1m'
        DIM = '\033[2m'
        RESET_ALL = '\033[0m'

    class Back:
        RESET = '\033[0m'


class ConsoleUI:
    """控制台 UI 工具类"""

    # Unicode 图标
    ICONS = {
        'success': '✓',
        'error': '✗',
        'warning': '⚠',
        'info': 'ℹ',
        'arrow': '→',
        'star': '★',
        'dot': '•',
        'check': '✓',
        'cross': '✗',
        'question': '?',
        'lightning': '⚡',
        'rocket': '🚀',
        'book': '📚',
        'brain': '🧠',
        'gear': '⚙',
        'search': '🔍',
        'sparkles': '✨',
    }

    @staticmethod
    def _get_icon(name: str) -> str:
        """获取图标"""
        return ConsoleUI.ICONS.get(name, '•')

    @staticmethod
    def print_header(text: str,
                     icon: str | None = None,
                     color: str = 'cyan'):
        """打印标题"""
        icon_str = f"{ConsoleUI._get_icon(icon)} " if icon else ""
        color_code = getattr(Fore, color.upper(), Fore.CYAN)
        print(f"\n{color_code}{Style.BRIGHT}{'═' * 70}")
        print(f"{icon_str}{text}")
        print(f"{'═' * 70}{Style.RESET_ALL}\n")

    @staticmethod
    def print_section(text: str,
                      icon: str | None = None,
                      color: str = 'blue'):
        """打印章节标题"""
        icon_str = f"{ConsoleUI._get_icon(icon)} " if icon else ""
        color_code = getattr(Fore, color.upper(), Fore.BLUE)
        print(f"\n{color_code}{Style.BRIGHT}{'─' * 70}")
        print(f"{icon_str}{text}")
        print(f"{'─' * 70}{Style.RESET_ALL}\n")

    @staticmethod
    def print_success(text: str, icon: bool = True):
        """打印成功消息"""
        icon_str = f"{ConsoleUI._get_icon('success')} " if icon else ""
        print(f"{Fore.GREEN}{icon_str}{text}{Style.RESET_ALL}")

    @staticmethod
    def print_error(text: str, icon: bool = True):
        """打印错误消息"""
        icon_str = f"{ConsoleUI._get_icon('error')} " if icon else ""
        print(f"{Fore.RED}{icon_str}{text}{Style.RESET_ALL}")

    @staticmethod
    def print_warning(text: str, icon: bool = True):
        """打印警告消息"""
        icon_str = f"{ConsoleUI._get_icon('warning')} " if icon else ""
        print(f"{Fore.YELLOW}{icon_str}{text}{Style.RESET_ALL}")

    @staticmethod
    def print_info(text: str, icon: bool = True):
        """打印信息消息"""
        icon_str = f"{ConsoleUI._get_icon('info')} " if icon else ""
        print(f"{Fore.CYAN}{icon_str}{text}{Style.RESET_ALL}")

    @staticmethod
    def print_question(text: str):
        """打印问题"""
        print(
            f"\n{Fore.MAGENTA}{Style.BRIGHT}{ConsoleUI._get_icon('question')} {text}{Style.RESET_ALL}"
        )

    @staticmethod
    def print_answer(text: str, indent: int = 2):
        """打印回答"""
        indent_str = " " * indent
        print(f"\n{Fore.WHITE}{Style.BRIGHT}{'─' * 70}")
        print(f"{Fore.GREEN}{Style.BRIGHT}回答:{Style.RESET_ALL}")
        print(f"{Fore.WHITE}{indent_str}{text}")
        print(f"{Fore.WHITE}{'─' * 70}{Style.RESET_ALL}\n")

    @staticmethod
    def print_box(content: str,
                  title: str | None = None,
                  color: str = 'cyan'):
        """打印带边框的文本"""
        lines = content.split('\n')
        max_width = max(len(line) for line in lines) if lines else 0
        max_width = max(max_width, len(title) if title else 0)
        max_width = min(max_width, 68)  # 限制最大宽度

        color_code = getattr(Fore, color.upper(), Fore.CYAN)
        border = '═' * (max_width + 2)

        print(f"\n{color_code}{border}{Style.RESET_ALL}")
        if title:
            print(f"{color_code}│ {title:<{max_width}} │{Style.RESET_ALL}")
            print(f"{color_code}{'─' * (max_width + 2)}{Style.RESET_ALL}")

        for line in lines:
            # 处理过长的行
            if len(line) > max_width:
                words = line.split()
                current_line = ""
                for word in words:
                    if len(current_line + word) <= max_width:
                        current_line += word + " "
                    else:
                        if current_line:
                            print(
                                f"{color_code}│ {current_line.strip():<{max_width}} │{Style.RESET_ALL}"
                            )
                        current_line = word + " "
                if current_line:
                    print(
                        f"{color_code}│ {current_line.strip():<{max_width}} │{Style.RESET_ALL}"
                    )
            else:
                print(f"{color_code}│ {line:<{max_width}} │{Style.RESET_ALL}")

        print(f"{color_code}{border}{Style.RESET_ALL}\n")

    @staticmethod
    def print_step(step_num: int, text: str, icon: str | None = None):
        """打印步骤"""
        icon_str = f"{ConsoleUI._get_icon(icon)} " if icon else ""
        print(
            f"\n{Fore.YELLOW}{Style.BRIGHT}[步骤 {step_num}] {icon_str}{text}{Style.RESET_ALL}"
        )
        print(f"{Fore.YELLOW}{'─' * 70}{Style.RESET_ALL}")

    @staticmethod
    def print_document_block(index: int, content: str, max_length: int = 300):
        """打印文档块"""
        preview = content[:max_length] + ("..."
                                          if len(content) > max_length else "")
        print(f"\n{Fore.CYAN}{Style.BRIGHT}文档块 {index}:{Style.RESET_ALL}")
        print(f"{Fore.WHITE}{Style.DIM}长度: {len(content)} 字符{Style.RESET_ALL}")
        print(f"{Fore.WHITE}{preview}{Style.RESET_ALL}\n")

    @staticmethod
    def print_progress(text: str):
        """打印进度信息"""
        print(f"{Fore.CYAN}{Style.DIM}⏳ {text}...{Style.RESET_ALL}",
              end='',
              flush=True)

    @staticmethod
    def print_progress_done():
        """完成进度"""
        print(f"{Fore.GREEN} ✓{Style.RESET_ALL}")

    @staticmethod
    def print_separator(char: str = '─', length: int = 70):
        """打印分隔线"""
        color = Fore.WHITE + Style.DIM
        print(f"{color}{char * length}{Style.RESET_ALL}")

    @staticmethod
    def print_list(items: list[str],
                   title: str | None = None,
                   icon: str = 'dot'):
        """打印列表"""
        if title:
            ConsoleUI.print_section(title)

        icon_str = ConsoleUI._get_icon(icon)
        for item in items:
            print(f"{Fore.WHITE}  {icon_str} {item}{Style.RESET_ALL}")
        print()

    @staticmethod
    def clear_screen():
        """清屏"""
        import os
        os.system('cls' if os.name == 'nt' else 'clear')

    @staticmethod
    def print_table(headers: list[str],
                    rows: list[list[str]],
                    title: str | None = None):
        """打印表格"""
        if title:
            ConsoleUI.print_section(title)

        # 计算每列的最大宽度
        col_widths = [len(str(h)) for h in headers]
        for row in rows:
            for i, cell in enumerate(row):
                if i < len(col_widths):
                    col_widths[i] = max(col_widths[i], len(str(cell)))

        # 打印表头
        header_line = " │ ".join(
            str(h).ljust(col_widths[i]) for i, h in enumerate(headers))
        print(f"{Fore.CYAN}{Style.BRIGHT}{header_line}{Style.RESET_ALL}")
        print(
            f"{Fore.CYAN}{'─' * (sum(col_widths) + 3 * (len(headers) - 1))}{Style.RESET_ALL}"
        )

        # 打印数据行
        for row in rows:
            row_line = " │ ".join(
                str(cell).ljust(col_widths[i]) for i, cell in enumerate(row))
            print(f"{Fore.WHITE}{row_line}{Style.RESET_ALL}")
        print()


# 创建全局实例
ui = ConsoleUI()
