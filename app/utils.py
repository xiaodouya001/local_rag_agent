"""
RAG Agent 工具函数
"""

import re
from pathlib import Path
from typing import Optional


def sanitize_path(path: str, base_dir: Optional[Path] = None) -> Path:
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
        except ValueError:
            raise ValueError(
                f"路径 {resolved_path} 不在允许的目录 {base_dir} 内"
            )
    
    return resolved_path


def sanitize_error_message(error_str: str, api_key: Optional[str] = None) -> str:
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
        api_key_pattern = re.compile(
            r'sk-[a-zA-Z0-9]{20,}', 
            re.IGNORECASE
        )
        error_str = api_key_pattern.sub("***REDACTED***", error_str)
    
    # 移除可能的文件路径（保留文件名）
    path_pattern = re.compile(r'[A-Z]:\\[^\s]+|/[^\s]+')
    error_str = path_pattern.sub(
        lambda m: Path(m.group()).name if Path(m.group()).exists() else m.group(),
        error_str
    )
    
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
