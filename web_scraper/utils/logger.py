"""
Loguru 日志配置模块
提供统一的日志配置和中文化输出
"""
from loguru import logger
import sys
from typing import Optional

def setup_logger(
    level: str = "INFO",
    log_file: Optional[str] = None,
    rotation: str = "10 MB",
    retention: str = "7 days"
) -> None:
    """
    配置 Loguru 日志器
    
    Args:
        level: 日志级别 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: 日志文件路径，如果为 None 则只输出到控制台
        rotation: 日志轮转大小
        retention: 日志保留时间
    """
    # 移除默认处理器
    logger.remove()
    
    # 添加控制台处理器
    logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level=level,
        colorize=True
    )
    
    # 如果指定了日志文件，添加文件处理器
    if log_file:
        logger.add(
            log_file,
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
            level=level,
            rotation=rotation,
            retention=retention,
            encoding="utf-8"
        )

# 提供便捷的日志方法
def log_info(message: str) -> None:
    """记录信息日志"""
    logger.info(message)

def log_error(message: str) -> None:
    """记录错误日志"""
    logger.error(message)

def log_warning(message: str) -> None:
    """记录警告日志"""
    logger.warning(message)

def log_debug(message: str) -> None:
    """记录调试日志"""
    logger.debug(message)

def log_success(message: str) -> None:
    """记录成功日志"""
    logger.success(message)

def log_critical(message: str) -> None:
    """记录严重错误日志"""
    logger.critical(message)

# 初始化日志配置
setup_logger()

# 导出 logger 实例供直接使用
__all__ = ["logger", "setup_logger", "log_info", "log_error", "log_warning", "log_debug", "log_success", "log_critical"]