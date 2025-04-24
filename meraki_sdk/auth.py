# meraki_sdk/auth.py
import os
from dotenv import load_dotenv
from meraki import DashboardAPI
from pathlib import Path

load_dotenv()

def get_dashboard_session():
    """
    Initializes and returns a Meraki Dashboard API session using the API key from .env or environment.
    """
    api_key = os.getenv("MERAKI_API_KEY")
    if not api_key:
        raise ValueError("MERAKI_API_KEY not found in environment variables or .env file.")

    # Ensure Meraki log directory exists
    meraki_log_dir = Path("logs") / "meraki_logs"
    meraki_log_dir.mkdir(parents=True, exist_ok=True)

    dashboard = DashboardAPI(
        api_key=api_key,
        suppress_logging=False,
        log_path=str(meraki_log_dir)  # <--- Redirects Meraki logs
    )
    return dashboard