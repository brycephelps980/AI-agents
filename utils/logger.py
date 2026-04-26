import sys
from pathlib import Path
from loguru import logger


def setup_logger(log_dir: str = "logs", level: str = "INFO") -> None:
    logger.remove()
    logger.add(sys.stdout, level=level, colorize=True,
               format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan> - {message}")
    Path(log_dir).mkdir(exist_ok=True)
    logger.add(
        f"{log_dir}/agents_{{time:YYYY-MM-DD}}.log",
        rotation="00:00",
        retention="30 days",
        level="DEBUG",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name} - {message}",
    )
    logger.add(
        f"{log_dir}/safety_{{time:YYYY-MM-DD}}.log",
        rotation="00:00",
        retention="30 days",
        level="WARNING",
        filter=lambda r: "safety" in r["name"].lower() or r["level"].no >= 30,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name} - {message}",
    )


setup_logger()
