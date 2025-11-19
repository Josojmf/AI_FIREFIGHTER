# app/routes/dashboard.py - VERSIÓN CORREGIDA
from flask import Blueprint, render_template, session
from flask_login import login_required
import requests
from config import Config

bp = Blueprint('dashboard', __name__)

def get_auth_headers():
    """Obtener headers de autenticación con token JWT"""
    token = session.get('api_token')
    if token:
        return {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
    return {'Content-Type': 'application/json'}

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
        headers = get_auth_headers()
        
        # Health check
        health_response = requests.get(f"{Config.API_BASE_URL}/api/health", timeout=5)
        if health_response.status_code == 200:
            health_data = health_response.json()
            stats['api_status'] = 'online' if health_data.get('ok') else 'error'
        
        # Obtener usuarios
        users_response = requests.get(
            f"{Config.API_BASE_URL}/api/users", 
            headers=headers,
            timeout=5
        )
        if users_response.status_code == 200:
            users_data = users_response.json()
            if users_data.get('ok'):
                users = users_data.get('users', [])
                stats['total_users'] = len(users)
                stats['active_users'] = len([u for u in users if u.get('status') == 'active'])
        
        # Obtener memory cards
        cards_response = requests.get(
            f"{Config.API_BASE_URL}/api/memory-cards",
            headers=headers,
            timeout=5
        )
        if cards_response.status_code == 200:
            cards_data = cards_response.json()
            if cards_data.get('ok'):
                stats['total_cards'] = len(cards_data.get('cards', []))
        
    except requests.RequestException as e:
        print(f"❌ Error en dashboard: {e}")
        stats['api_status'] = 'offline'
    
    return render_template('dashboard.html', stats=stats)