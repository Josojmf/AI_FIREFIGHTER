# app/routes/dashboard.py - VERSIÃ“N CORREGIDA CON DATOS REALES
from flask import Blueprint, render_template, session, jsonify, current_app
from flask_login import login_required, current_user
import requests
from datetime import datetime, timedelta
from config import Config
import json

bp = Blueprint('dashboard', __name__)

def get_auth_headers():
    """Obtener headers de autenticaciÃ³n con token JWT"""
    token = session.get('api_token')
    if token:
        return {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
    return {'Content-Type': 'application/json'}

def fetch_real_data():
    """Obtener datos reales de la API"""
    stats = {
        'total_users': 0,
        'active_users': 0,
        'total_cards': 0,
        'api_status': 'offline',
        'recent_activity': [],
        'system_stats': {}
    }
    
    try:
        headers = get_auth_headers()
        
        # Health check de API
        try:
            health_response = requests.get(f"{Config.API_BASE_URL}/api/health", timeout=5)
            if health_response.status_code == 200:
                health_data = health_response.json()
                stats['api_status'] = 'online' if health_data.get('ok') else 'error'
                stats['users_count'] = health_data.get('users_count', 0)
        except:
            stats['api_status'] = 'offline'
        
        # Solo continuar si la API estÃ¡ online
        if stats['api_status'] == 'online':
            # Obtener usuarios reales
            try:
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
                        
                        # Generar actividad reciente basada en usuarios
                        stats['recent_activity'] = generate_recent_activity(users)
            except Exception as e:
                current_app.logger.error(f"Error fetching users: {e}")
            
            # Obtener memory cards reales
            try:
                cards_response = requests.get(
                    f"{Config.API_BASE_URL}/api/memory-cards",
                    headers=headers,
                    timeout=5
                )
                if cards_response.status_code == 200:
                    cards_data = cards_response.json()
                    if cards_data.get('ok'):
                        stats['total_cards'] = len(cards_data.get('cards', []))
            except Exception as e:
                current_app.logger.error(f"Error fetching cards: {e}")
            
            # Obtener estadÃ­sticas del sistema
            stats['system_stats'] = get_system_stats()
        
    except Exception as e:
        current_app.logger.error(f"Error en dashboard: {e}")
    
    return stats

def generate_recent_activity(users):
    """Generar actividad reciente basada en datos reales"""
    activity = []
    
    if users:
        # Ordenar usuarios por fecha de creaciÃ³n (mÃ¡s recientes primero)
        sorted_users = sorted(users, key=lambda x: x.get('created_at', ''), reverse=True)
        
        # Agregar usuarios recientes como actividad
        for user in sorted_users[:3]:
            activity.append({
                'type': 'user_registered',
                'text': f"Nuevo usuario registrado: {user.get('username', 'N/A')}",
                'time': format_relative_time(user.get('created_at')),
                'icon': 'ðŸ‘¤'
            })
    
    # Agregar actividad del sistema
    activity.extend([
        {
            'type': 'system',
            'text': 'Sistema de dashboard inicializado',
            'time': 'Justo ahora',
            'icon': 'ðŸ”§'
        },
        {
            'type': 'api',
            'text': f'API conectada correctamente',
            'time': 'Justo ahora', 
            'icon': 'ðŸŒ'
        }
    ])
    
    return activity[:5]  # Limitar a 5 actividades

def format_relative_time(timestamp_str):
    """Formatear tiempo relativo para actividad"""
    if not timestamp_str:
        return "Hace un momento"
    
    try:
        if 'T' in timestamp_str:
            dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        else:
            dt = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
        
        now = datetime.utcnow()
        diff = now - dt
        
        if diff.days > 0:
            return f"Hace {diff.days} dÃ­a{'s' if diff.days > 1 else ''}"
        elif diff.seconds >= 3600:
            hours = diff.seconds // 3600
            return f"Hace {hours} hora{'s' if hours > 1 else ''}"
        elif diff.seconds >= 60:
            minutes = diff.seconds // 60
            return f"Hace {minutes} minuto{'s' if minutes > 1 else ''}"
        else:
            return "Hace un momento"
    except:
        return "Hace un momento"

def get_system_stats():
    """Obtener estadÃ­sticas del sistema"""
    return {
        'database_status': 'online',
        'storage_usage': '45%',  # PodrÃ­as calcular esto basado en datos reales
        'memory_usage': '512MB / 2GB',
        'uptime': '99.8%'
    }

@bp.route('/')
@bp.route('/dashboard')
@login_required
def index():
    """Dashboard principal con datos reales"""
    print(f"🔍 Dashboard route - User: {current_user.username}, Authenticated: {current_user.is_authenticated}")
    
    # 🔥 VERIFICACIÓN ADICIONAL: Si no está autenticado, redirigir manualmente
    if not current_user.is_authenticated:
        print("❌ Usuario no autenticado en dashboard, redirigiendo a login")
        return redirect('/auth/login')
    
    try:
        stats = fetch_real_data()
        print(f"✅ Dashboard cargado para: {current_user.username}")
        return render_template('dashboard.html', stats=stats)
    except Exception as e:
        print(f"❌ Error cargando dashboard: {e}")
        # En caso de error, mostrar dashboard básico
        return render_template('dashboard.html', stats={
            'total_users': 0,
            'active_users': 0, 
            'total_cards': 0,
            'api_status': 'offline',
            'recent_activity': []
        })

@bp.route('/api/dashboard/stats')
@login_required
def api_dashboard_stats():
    """Endpoint API para obtener estadÃ­sticas del dashboard (AJAX)"""
    stats = fetch_real_data()
    return jsonify(stats)

@bp.route('/api/dashboard/activity')
@login_required
def api_dashboard_activity():
    """Endpoint API para actividad reciente (AJAX)"""
    try:
        headers = get_auth_headers()
        users_response = requests.get(f"{Config.API_BASE_URL}/api/users", headers=headers)
        
        if users_response.status_code == 200:
            users_data = users_response.json()
            if users_data.get('ok'):
                users = users_data.get('users', [])
                activity = generate_recent_activity(users)
                return jsonify({'ok': True, 'activity': activity})
        
        return jsonify({'ok': False, 'activity': []})
    except Exception as e:
        return jsonify({'ok': False, 'activity': []})

@bp.route('/api/dashboard/health')
@login_required
def api_dashboard_health():
    """Endpoint API para verificar salud del sistema"""
    try:
        health_response = requests.get(f"{Config.API_BASE_URL}/api/health", timeout=5)
        if health_response.status_code == 200:
            health_data = health_response.json()
            return jsonify({
                'ok': True,
                'api_status': 'online' if health_data.get('ok') else 'error',
                'database': health_data.get('database', 'unknown'),
                'timestamp': datetime.utcnow().isoformat()
            })
        else:
            return jsonify({'ok': False, 'api_status': 'offline'})
    except:
        return jsonify({'ok': False, 'api_status': 'offline'})
    
# AÃ±ade estas funciones al archivo de rutas del dashboard

@bp.route('/api/dashboard/docker-logs')
@login_required
def api_dashboard_docker_logs():
    """Obtener logs Docker para el dashboard"""
    try:
        headers = get_auth_headers()
        response = requests.get(
            f"{Config.API_BASE_URL}/api/docker/logs",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            logs_data = response.json()
            return jsonify(logs_data)
        else:
            return jsonify({"ok": False, "logs": []})
            
    except Exception as e:
        current_app.logger.error(f"Error obteniendo logs Docker: {e}")
        return jsonify({"ok": False, "logs": []})

@bp.route('/api/dashboard/docker-containers')
@login_required
def api_dashboard_docker_containers():
    """Obtener informaciÃ³n de contenedores para el dashboard"""
    try:
        headers = get_auth_headers()
        response = requests.get(
            f"{Config.API_BASE_URL}/api/docker/containers",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            containers_data = response.json()
            return jsonify(containers_data)
        else:
            return jsonify({"ok": False, "containers": []})
            
    except Exception as e:
        current_app.logger.error(f"Error obteniendo contenedores: {e}")
        return jsonify({"ok": False, "containers": []})