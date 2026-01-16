"""
RAG Agent 统一日志配置模块
提供统一的日志配置函数，避免代码重复
"""

import os
import gzip
import json
import logging
from pathlib import Path
from logging.handlers import TimedRotatingFileHandler
from typing import Optional


class JSONFormatter(logging.Formatter):
    """JSON格式化器（用于生产环境，便于日志聚合和分析）"""
    
    def __init__(self, datefmt: Optional[str] = None):
        super().__init__(datefmt=datefmt)
        self.datefmt = datefmt or '%Y-%m-%d %H:%M:%S'
    
    def format(self, record: logging.LogRecord) -> str:
        """
        格式化日志记录为JSON格式
        
        Args:
            record: 日志记录
            
        Returns:
            JSON格式的日志字符串
        """
        log_data = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        
        # 添加异常信息（如果有）
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        # 添加模块和行号信息
        if record.pathname:
            log_data["module"] = record.pathname
        if record.lineno:
            log_data["line"] = record.lineno
        
        return json.dumps(log_data, ensure_ascii=False)


def _namer(name: str) -> str:
    """
    压缩轮转后的日志文件命名函数
    
    Args:
        name: 日志文件名
        
    Returns:
        压缩后的文件名
    """
    return name + ".gz"


def _rotator(source: str, dest: str) -> None:
    """
    轮转时压缩日志文件
    
    Args:
        source: 源文件路径
        dest: 目标文件路径
    """
    with open(source, 'rb') as f_in:
        with gzip.open(dest, 'wb') as f_out:
            f_out.writelines(f_in)
    os.remove(source)


def setup_logging(
    log_level: str = "INFO",
    use_json: bool = False,
    log_dir: Optional[Path] = None,
    log_file_name: str = "rag_agent.log"
) -> None:
    """
    统一的日志配置函数
    
    Args:
        log_level: 日志级别（DEBUG/INFO/WARNING/ERROR/CRITICAL），默认INFO
        use_json: 是否使用JSON格式（生产环境推荐），默认False
        log_dir: 日志目录路径，默认为项目根目录下的logs目录
        log_file_name: 日志文件名，默认rag_agent.log
        
    Example:
        >>> # 基本使用（开发环境）
        >>> setup_logging()
        
        >>> # 生产环境使用JSON格式
        >>> setup_logging(log_level="INFO", use_json=True)
        
        >>> # 自定义日志目录
        >>> setup_logging(log_dir=Path("./custom_logs"))
    """
    # 确定日志目录
    if log_dir is None:
        # 默认使用项目根目录下的logs目录
        project_root = Path(__file__).parent.parent
        log_dir = project_root / "logs"
    else:
        log_dir = Path(log_dir)
    
    # 创建日志目录
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # 文件处理器：使用 TimedRotatingFileHandler 按天轮转并压缩
    log_file = log_dir / log_file_name
    file_handler = TimedRotatingFileHandler(
        filename=str(log_file),
        when='midnight',  # 每天午夜轮转
        interval=1,  # 每1天
        backupCount=30,  # 保留30天的日志
        encoding='utf-8',
        delay=False
    )
    
    # 设置日志级别
    file_handler.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    
    # 设置压缩函数
    file_handler.rotator = _rotator
    file_handler.namer = _namer
    
    # 选择格式化器
    if use_json:
        # 生产环境：使用JSON格式
        formatter = JSONFormatter(datefmt='%Y-%m-%d %H:%M:%S')
    else:
        # 开发环境：使用可读格式
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(name)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    
    file_handler.setFormatter(formatter)
    
    # 控制台处理器：只显示WARNING级别及以上的日志，避免与UI重复
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.WARNING)
    console_handler.setFormatter(
        logging.Formatter('%(levelname)s - %(message)s')
    )
    
    # 配置根日志
    root_level = getattr(logging, log_level.upper(), logging.INFO)
    logging.basicConfig(
        level=root_level,
        handlers=[file_handler, console_handler],
        force=True  # 强制重新配置，避免重复配置问题
    )
    
    # 降低第三方库的日志级别，减少噪音
    logging.getLogger('sentence_transformers').setLevel(logging.WARNING)
    logging.getLogger('transformers').setLevel(logging.WARNING)
    logging.getLogger('chromadb').setLevel(logging.WARNING)
    logging.getLogger('langchain').setLevel(logging.WARNING)
