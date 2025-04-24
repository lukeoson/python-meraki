# meraki_sdk/logging_config.py
import logging
import coloredlogs
import os

def setup_logging():
    """Configure colorized console logging + persistent file logging."""
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)
    log_file_path = os.path.join(log_dir, "python_meraki.log")

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