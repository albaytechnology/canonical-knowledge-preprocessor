"""
Structured logging module for CKD Processor.
"""

import logging
import os
import sys
from rich.logging import RichHandler


def setup_logger(name: str = "CKD", log_dir: str = "./knowledge/logs", level: int = logging.INFO) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    if logger.handlers:
        return logger

    # Console handler using Rich
    console_handler = RichHandler(rich_tracebacks=True, show_time=True, show_path=False)
    console_handler.setLevel(level)
    formatter = logging.Formatter("%(message)s")
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler if log_dir exists or can be created
    try:
        os.makedirs(log_dir, exist_ok=True)
        file_path = os.path.join(log_dir, "ckd_pipeline.log")
        file_handler = logging.FileHandler(file_path, encoding="utf-8")
        file_handler.setLevel(level)
        file_formatter = logging.Formatter("%(asctime)s - [%(levelname)s] - %(name)s - %(message)s")
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    except Exception as e:
        sys.stderr.write(f"Warning: Could not create file logger: {e}\n")

    return logger
