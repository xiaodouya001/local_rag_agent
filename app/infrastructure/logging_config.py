"""
RAG Agent 统一日志配置模块
提供统一的日志配置函数，避免代码重复
"""

import gzip
import json
import logging
from logging.handlers import TimedRotatingFileHandler
import os
from pathlib import Path


class JSONFormatter(logging.Formatter):
    """JSON格式化器（用于生产环境，便于日志聚合和分析）"""

    def __init__(self, datefmt: str | None = None):
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
    with open(source, 'rb') as f_in, gzip.open(dest, 'wb') as f_out:
        f_out.writelines(f_in)
    os.remove(source)


def setup_logging(log_level: str = "INFO",
                  use_json: bool = False,
                  log_dir: Path | None = None,
                  log_file_name: str = "rag_agent.log") -> None:
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
        from app.core.utils.common import find_project_root
        project_root = find_project_root(__file__)
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
        delay=False)

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
            datefmt='%Y-%m-%d %H:%M:%S')

    file_handler.setFormatter(formatter)

    # 控制台处理器：只显示WARNING级别及以上的日志，避免与UI重复
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.WARNING)
    console_handler.setFormatter(
        logging.Formatter('%(levelname)s - %(message)s'))

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

    # 检查是否启用 SDK 原始 debug 日志
    enable_sdk_debug = os.getenv('ENABLE_SDK_DEBUG', 'false').lower() == 'true'
    if enable_sdk_debug:
        # 启用 OpenAI/DeepSeek SDK 和 HTTP 客户端的 debug 日志
        logging.getLogger('openai').setLevel(logging.DEBUG)
        logging.getLogger('httpx').setLevel(logging.DEBUG)
        logging.getLogger('httpcore').setLevel(logging.DEBUG)
        # 将 SDK 日志也输出到 api_debug.log
        setup_sdk_debug_logger(log_dir)
    else:
        # 默认情况下降低这些库的日志级别
        logging.getLogger('openai').setLevel(logging.WARNING)
        logging.getLogger('httpx').setLevel(logging.WARNING)
        logging.getLogger('httpcore').setLevel(logging.WARNING)
        logging.getLogger('langchain').setLevel(logging.WARNING)


def setup_api_logger(log_dir: Path | None = None,
                     log_file_name: str = "api_debug.log") -> logging.Logger:
    """
    创建独立的API调试日志记录器

    用于记录详细的API请求和响应信息，与应用日志分离

    Args:
        log_dir: 日志目录路径，默认为项目根目录下的logs目录
        log_file_name: API日志文件名，默认api_debug.log

    Returns:
        配置好的API日志记录器

    Example:
        >>> api_logger = setup_api_logger()
        >>> api_logger.debug("API请求详情...")
    """
    # 确定日志目录
    if log_dir is None:
        from app.core.utils.common import find_project_root
        project_root = find_project_root(__file__)
        log_dir = project_root / "logs"
    else:
        log_dir = Path(log_dir)

    # 创建日志目录
    log_dir.mkdir(parents=True, exist_ok=True)

    # 创建API专用的日志记录器
    api_logger = logging.getLogger('rag_agent.api_debug')
    api_logger.setLevel(logging.DEBUG)

    # 避免重复添加handler
    if api_logger.handlers:
        return api_logger

    # 文件处理器：使用 TimedRotatingFileHandler 按天轮转并压缩
    api_log_file = log_dir / log_file_name
    api_file_handler = TimedRotatingFileHandler(
        filename=str(api_log_file),
        when='midnight',
        interval=1,
        backupCount=30,
        encoding='utf-8',
        delay=False)

    api_file_handler.setLevel(logging.DEBUG)

    # 设置压缩函数
    api_file_handler.rotator = _rotator
    api_file_handler.namer = _namer

    # 使用可读格式
    api_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S')

    api_file_handler.setFormatter(api_formatter)

    # 只添加到API日志记录器，不影响其他日志
    api_logger.addHandler(api_file_handler)
    api_logger.propagate = False  # 不传播到根日志记录器

    return api_logger


def setup_sdk_debug_logger(log_dir: Path | None = None,
                           log_file_name: str = "api_debug.log") -> None:
    """
    配置 SDK（OpenAI/DeepSeek）的原始 debug 日志输出到文件

    将 openai、httpx、httpcore 等底层库的日志也输出到 api_debug.log

    Args:
        log_dir: 日志目录路径，默认为项目根目录下的logs目录
        log_file_name: 日志文件名，默认api_debug.log（与API日志共用）

    Example:
        >>> setup_sdk_debug_logger()
        >>> # 现在 openai、httpx 等库的 DEBUG 日志会输出到 api_debug.log
    """
    # 确定日志目录
    if log_dir is None:
        from app.core.utils.common import find_project_root
        project_root = find_project_root(__file__)
        log_dir = project_root / "logs"
    else:
        log_dir = Path(log_dir)

    # 创建日志目录
    log_dir.mkdir(parents=True, exist_ok=True)

    # 获取或创建 API 日志文件处理器（复用 api_debug.log）
    api_log_file = log_dir / log_file_name

    # 为 SDK 相关的日志记录器添加文件处理器
    sdk_loggers = ['openai', 'httpx', 'httpcore']

    for logger_name in sdk_loggers:
        sdk_logger = logging.getLogger(logger_name)

        # 检查是否已经添加了文件处理器
        has_file_handler = any(
            isinstance(h, TimedRotatingFileHandler) and
            h.baseFilename == str(api_log_file)
            for h in sdk_logger.handlers
        )

        if not has_file_handler:
            # 创建文件处理器
            sdk_file_handler = TimedRotatingFileHandler(
                filename=str(api_log_file),
                when='midnight',
                interval=1,
                backupCount=30,
                encoding='utf-8',
                delay=False)

            sdk_file_handler.setLevel(logging.DEBUG)

            # 设置压缩函数
            sdk_file_handler.rotator = _rotator
            sdk_file_handler.namer = _namer

            # 使用可读格式，标记为 SDK 日志（添加 [SDK] 前缀以便区分）
            sdk_formatter = logging.Formatter(
                '%(asctime)s - %(levelname)s - [SDK:%(name)s] - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S')

            sdk_file_handler.setFormatter(sdk_formatter)
            sdk_logger.addHandler(sdk_file_handler)
            sdk_logger.setLevel(logging.DEBUG)
            sdk_logger.propagate = False  # 不传播到根日志记录器
