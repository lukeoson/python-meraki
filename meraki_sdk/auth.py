# meraki_sdk/auth.py

import os
from dotenv import load_dotenv
from meraki import DashboardAPI

load_dotenv()  # ⬅️ Load variables from .env

def get_dashboard_session():
    """
    Initializes and returns a Meraki Dashboard API session using the API key from .env or environment.
    """
    api_key = os.getenv("MERAKI_API_KEY")
    if not api_key:
        raise ValueError("MERAKI_API_KEY not found in environment variables or .env file.")

    dashboard = DashboardAPI(
        api_key=api_key,
        suppress_logging=False
    )
    return dashboard