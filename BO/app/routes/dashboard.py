from flask import Blueprint, render_template
from flask_login import login_required
import requests
from config import Config

bp = Blueprint('dashboard', __name__)

@bp.route('/')
@bp.route('/dashboard')
@login_required
def index():
    # Obtener estadísticas de la API
    stats = {
        'total_users': 0,
        'active_users': 0,
        'total_cards': 0,
        'api_status': 'offline'
    }
    
    try:
        # Health check
        health_response = requests.get(f"{Config.API_BASE_URL}/api/health", timeout=5)
        if health_response.status_code == 200:
            health_data = health_response.json()
            stats['api_status'] = 'online' if health_data['ok'] else 'error'
            stats['total_users'] = health_data.get('users_count', 0)
        
        # Obtener usuarios
        users_response = requests.get(f"{Config.API_BASE_URL}/api/users", timeout=5)
        if users_response.status_code == 200:
            users_data = users_response.json()
            if users_data['ok']:
                stats['active_users'] = len([u for u in users_data['users'] if u.get('status') == 'active'])
        
    except requests.RequestException:
        stats['api_status'] = 'offline'
    
    return render_template('dashboard.html', stats=stats)