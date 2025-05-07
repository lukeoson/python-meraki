# utils/logging_config.py
import logging
import coloredlogs
import os
from pathlib import Path

def setup_logging(log_name: str = "python_meraki.log"):
    """Configure colorized console logging + persistent file logging."""
    base_log_dir = Path("logs")
    custom_log_dir = base_log_dir / "custom_logs"
    custom_log_dir.mkdir(parents=True, exist_ok=True)

    log_file_path = custom_log_dir / log_name

    logging.basicConfig(
        level=logging.INFO,
        format='[%(asctime)s] [%(levelname)s] %(name)s: %(message)s',
        handlers=[
            logging.FileHandler(log_file_path, mode='a'),
            logging.StreamHandler()
        ]
    )

    coloredlogs.install(
        level=logging.INFO,
        fmt='[%(asctime)s] [%(levelname)s] %(name)s: %(message)s',
        field_styles={
            'asctime': {'color': 'green'},
            'levelname': {'bold': True, 'color': 'blue'},
            'name': {'color': 'magenta'},
        }
    )