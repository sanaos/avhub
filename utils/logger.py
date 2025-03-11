import logging
from omegaconf import DictConfig

def setup_logger(cfg: DictConfig):
    logger = logging.getLogger(__name__)
    if not logger.hasHandlers():  # 检查是否已经有处理器
        logger.setLevel(getattr(logging, cfg.logging.level.upper()))

        # 创建文件处理器和流处理器
        file_handler = logging.FileHandler(cfg.logging.log_file)
        stream_handler = logging.StreamHandler()

        # 设置日志格式
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        stream_handler.setFormatter(formatter)

        # 添加处理器到日志器
        logger.addHandler(file_handler)
        logger.addHandler(stream_handler)

    return logger



