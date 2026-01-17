"""
RAG Agent 通用工具函数
提供路径验证、错误信息清理、API 密钥验证、项目根目录查找等功能
"""

from pathlib import Path
import re


def find_project_root(start_path: Path | str | None = None) -> Path:
    """
    查找项目根目录（包含 pyproject.toml 的目录）

    查找策略（按优先级）：
    1. 从 start_path 向上查找包含 pyproject.toml 的目录
    2. 从当前工作目录查找
    3. 如果都找不到，抛出 RuntimeError

    Args:
        start_path: 起始路径（文件或目录），如果为 None 则使用当前文件位置

    Returns:
        项目根目录的 Path 对象

    Raises:
        RuntimeError: 如果无法找到项目根目录
    """
    # 确定起始路径
    if start_path is None:
        # 尝试从调用者的文件位置获取
        import inspect
        frame = inspect.currentframe()
        if frame and frame.f_back:
            caller_file = frame.f_back.f_globals.get('__file__')
            if caller_file:
                start_path = Path(caller_file).resolve()
            else:
                start_path = Path.cwd()
        else:
            start_path = Path.cwd()
    else:
        start_path = Path(start_path).resolve()

    # 如果是文件，使用其父目录
    search_path = start_path.parent if start_path.is_file() else start_path

    # 从起始路径向上查找包含 pyproject.toml 的目录
    for parent in [search_path] + list(search_path.parents):
        if (parent / "pyproject.toml").exists():
            return parent.resolve()

    # 如果找不到，尝试从当前工作目录查找
    cwd = Path.cwd()
    if (cwd / "pyproject.toml").exists():
        return cwd.resolve()

    # 从当前工作目录向上查找
    for parent in cwd.parents:
        if (parent / "pyproject.toml").exists():
            return parent.resolve()

    # 如果都找不到，抛出错误
    raise RuntimeError(
        "无法找到项目根目录（包含 pyproject.toml 的目录）。"
        "请确保在项目目录中运行，或检查目录结构是否正确。"
    )


def sanitize_path(path: str, base_dir: Path | None = None) -> Path:
    """
    规范化并验证路径，防止路径遍历攻击

    Args:
        path: 输入路径
        base_dir: 基础目录，用于限制路径范围

    Returns:
        规范化后的 Path 对象

    Raises:
        ValueError: 如果路径无效或超出允许范围
    """
    # 规范化路径
    resolved_path = Path(path).resolve()

    # 如果指定了基础目录，确保路径在基础目录内
    if base_dir:
        base_dir = Path(base_dir).resolve()
        try:
            resolved_path.relative_to(base_dir)
        except ValueError as err:
            raise ValueError(
                f"路径 {resolved_path} 不在允许的目录 {base_dir} 内"
            ) from err

    return resolved_path


def sanitize_error_message(error_str: str,
                           api_key: str | None = None) -> str:
    """
    清理错误信息，移除敏感信息

    Args:
        error_str: 原始错误信息
        api_key: API密钥（用于过滤）

    Returns:
        清理后的错误信息
    """
    # 移除 API 密钥（如果存在）
    if api_key:
        error_str = error_str.replace(api_key, "***REDACTED***")
        # 移除可能的密钥片段
        api_key_pattern = re.compile(r'sk-[a-zA-Z0-9]{20,}', re.IGNORECASE)
        error_str = api_key_pattern.sub("***REDACTED***", error_str)

    # 移除可能的文件路径（保留文件名）
    path_pattern = re.compile(r'[A-Z]:\\[^\s]+|/[^\s]+')
    error_str = path_pattern.sub(
        lambda m: Path(m.group()).name
        if Path(m.group()).exists() else m.group(), error_str)

    return error_str


def validate_api_key(api_key: str) -> bool:
    """
    验证 API 密钥格式（基本检查）

    Args:
        api_key: API 密钥

    Returns:
        是否通过基本格式验证
    """
    if not api_key or len(api_key) < 10:
        return False

    # DeepSeek API 密钥通常以 sk- 开头
    if api_key.startswith('sk-'):
        return len(api_key) >= 20

    return True
