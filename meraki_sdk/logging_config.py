# meraki_sdk/logging_config.py
import logging
import coloredlogs
import os
from pathlib import Path

def setup_logging(log_name: str = "python_meraki.log"):
    """Configure colorized console logging + persistent file logging."""
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    log_file_path = log_dir / log_name

    # Base config (used by file handler)
    logging.basicConfig(
        level=logging.INFO,
        format='[%(asctime)s] [%(levelname)s] %(name)s: %(message)s',
        handlers=[
            logging.FileHandler(log_file_path),
            logging.StreamHandler()  # Needed for coloredlogs to hook into
        ]
    )

    # Pretty colors for console
    coloredlogs.install(
        level=logging.INFO,
        fmt='[%(asctime)s] [%(levelname)s] %(name)s: %(message)s',
        field_styles={
            'asctime': {'color': 'green'},
            'levelname': {'bold': True, 'color': 'blue'},
            'name': {'color': 'magenta'},
        }
    )