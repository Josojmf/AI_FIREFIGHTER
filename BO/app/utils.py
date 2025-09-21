import requests
from functools import wraps
from flask import current_app, flash, redirect, url_for
from flask_login import current_user

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash('Se requieren permisos de administrador', 'error')
            return redirect(url_for('dashboard.index'))
        return f(*args, **kwargs)
    return decorated_function

def api_request(method, endpoint, **kwargs):
    """Helper para hacer requests a la API principal"""
    base_url = current_app.config['API_BASE_URL']
    try:
        response = requests.request(method, f"{base_url}{endpoint}", **kwargs)
        return response
    except requests.RequestException as e:
        current_app.logger.error(f"API request failed: {e}")
        return None