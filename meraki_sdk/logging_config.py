# meraki_sdk/logging_config.py
import logging
import coloredlogs

def setup_logging():
    """Configure consistent, colorized logging across the project."""
    log_level = logging.INFO
    field_styles = {
        'asctime': {'color': 'green'},
        'levelname': {'bold': True, 'color': 'blue'},
        'name': {'color': 'magenta'},
    }
    coloredlogs.install(
        level=log_level,
        fmt='[%(asctime)s] [%(levelname)s] %(name)s: %(message)s',
        field_styles=field_styles
    )