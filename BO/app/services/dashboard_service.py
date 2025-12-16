import requests
from datetime import datetime

API_BASE = "http://backend:5000/api"  # nombre del servicio docker

def get_dashboard_stats():
    try:
        r = requests.get(f"{API_BASE}/dashboard/stats", timeout=3)
        r.raise_for_status()
        data = r.json()
    except Exception as e:
        data = {
            "ok": False,
            "total_users": 0,
            "active_users": 0,
            "total_cards": 0,
            "api_status": "offline",
            "recent_activity": []
        }

    return data
