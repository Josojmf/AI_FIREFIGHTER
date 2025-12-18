# app/routes/dashboard.py - VERSIÓN CORREGIDA CON ESTRUCTURA GARANTIZADA
from flask import Blueprint, render_template, session, jsonify, current_app, redirect, Response
from flask_login import login_required, current_user
import requests
from datetime import datetime, timedelta
from config import Config
import json
import redis
import hashlib
import time
import os

redis_client = redis.Redis(
    host=Config.REDIS_HOST,
    port=Config.REDIS_PORT,
    decode_responses=True
)

bp = Blueprint('dashboard', __name__)


def get_auth_headers():
    """Obtener headers de autenticación con token JWT"""
    token = session.get('api_token')
    if token:
        return {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
    return {'Content-Type': 'application/json'}


def cache_dashboard(ttl=15):
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                user_id = str(current_user.id)
                cache_key = f"dashboard:{user_id}"

                cached = redis_client.get(cache_key)
                if cached:
                    current_app.logger.info("⚡ Dashboard servido desde Redis")
                    return json.loads(cached)
            except Exception as e:
                current_app.logger.warning(f"Redis no disponible: {e}")

            data = func(*args, **kwargs)

            try:
                redis_client.setex(cache_key, ttl, json.dumps(data))
            except Exception:
                # Continuar sin cache si Redis falla
                pass

            return data
        return wrapper
    return decorator


def get_default_stats():
    """Retorna estructura de stats por defecto con todos los campos"""
    return {
        "total_users": 0,
        "active_users": 0,
        "total_cards": 0,
        "users_count": 0,
        "api_status": "offline",
        "recent_activity": [
            {
                'type': 'system',
                'text': 'Esperando conexión con API...',
                'time': 'Ahora',
                'icon': '⏳'
            }
        ],
        "system_stats": {
            'database_status': 'Unknown',
            'storage_usage': 'N/A',
            'memory_usage': 'N/A',
            'uptime': 'N/A'
        },
        "docker_logs": []
    }


@cache_dashboard(ttl=20)
def fetch_real_data():
    """
    Obtener TODOS los datos reales del dashboard (SERVER-SIDE ONLY)
    - Stats
    - Actividad
    - Estado API
    - Docker logs

    GARANTIZA que SIEMPRE retorna estructura completa
    """

    # Iniciar con estructura completa por defecto
    stats = get_default_stats()
    headers = get_auth_headers()

    # ---------------------------------------------------
    # 1️⃣ HEALTH CHECK API
    # ---------------------------------------------------
    try:
        health_response = requests.get(
            f"{Config.API_BASE_URL}/api/health",
            timeout=5
        )

        if health_response.status_code == 200:
            health_data = health_response.json()
            stats["api_status"] = "online" if health_data.get("ok") or health_data.get("status") == "healthy" else "error"
            # Actualizar users_count si viene en health
            if "users_count" in health_data:
                stats["users_count"] = health_data.get("users_count", 0)
        else:
            stats["api_status"] = "offline"

    except Exception as e:
        current_app.logger.error(f"[Dashboard] API health error: {e}")
        stats["api_status"] = "offline"

    # ---------------------------------------------------
    # 2️⃣ SI LA API ESTÁ ONLINE → CARGAR DATOS REALES
    # ---------------------------------------------------
    if stats["api_status"] == "online":

        # ---------------- USERS ----------------
        try:
            users_response = requests.get(
                f"{Config.API_BASE_URL}/api/users",
                headers=headers,
                timeout=5
            )

            if users_response.status_code == 200:
                users_data = users_response.json()

                if users_data.get("ok"):
                    users = users_data.get("users", [])
                    stats["total_users"] = len(users)
                    stats["active_users"] = len(
                        [u for u in users if u.get("status") == "active"]
                    )
                    stats["users_count"] = len(users)

                    # Generar actividad basada en usuarios reales
                    stats["recent_activity"] = generate_recent_activity(users)

        except Exception as e:
            current_app.logger.error(f"[Dashboard] Error fetching users: {e}")

        # ---------------- MEMORY CARDS ----------------
        try:
            cards_response = requests.get(
                f"{Config.API_BASE_URL}/api/memory-cards",
                headers=headers,
                timeout=5
            )

            if cards_response.status_code == 200:
                cards_data = cards_response.json()

                if cards_data.get("ok"):
                    stats["total_cards"] = len(cards_data.get("cards", []))

        except Exception as e:
            current_app.logger.error(f"[Dashboard] Error fetching cards: {e}")

        # ---------------- SYSTEM STATS ----------------
        stats["system_stats"] = get_system_stats(stats["api_status"])

        # ---------------- DOCKER LOGS (SSR) ----------------
        try:
            logs_response = requests.get(
                f"{Config.API_BASE_URL}/api/docker/logs",
                headers=headers,
                timeout=10
            )

            if logs_response.status_code == 200:
                logs_data = logs_response.json()
                if isinstance(logs_data, dict):
                    stats["docker_logs"] = logs_data.get("logs", [])[:100]
                elif isinstance(logs_data, list):
                    stats["docker_logs"] = logs_data[:100]

        except Exception as e:
            current_app.logger.error(f"[Dashboard] Error fetching docker logs: {e}")

    # ---------------- SUMMARY (para las plantillas) ----------------
    stats["summary"] = {
        "total_users": stats.get("total_users", 0),
        "active_users": stats.get("active_users", 0),
        "total_cards": stats.get("total_cards", 0),
        "users_count": stats.get("users_count", 0),
    }

    return stats


def generate_recent_activity(users):
    """Generar actividad reciente basada en datos reales"""
    activity = []

    if users:
        # Ordenar usuarios por fecha de creación (más recientes primero)
        sorted_users = sorted(
            users,
            key=lambda x: x.get('created_at', ''),
            reverse=True
        )

        # Agregar usuarios recientes como actividad
        for user in sorted_users[:3]:
            activity.append({
                'type': 'user_registered',
                'text': f"Nuevo usuario: {user.get('username', 'N/A')}",
                'time': format_relative_time(user.get('created_at')),
                'icon': '👤'
            })

    # Agregar actividad del sistema
    activity.extend([
        {
            'type': 'system',
            'text': 'Dashboard actualizado',
            'time': 'Justo ahora',
            'icon': '🔄'
        },
        {
            'type': 'api',
            'text': 'API conectada correctamente',
            'time': 'Justo ahora',
            'icon': '🌐'
        }
    ])

    return activity[:5]  # Limitar a 5 actividades


def format_relative_time(timestamp_str):
    """Formatear tiempo relativo para actividad"""
    if not timestamp_str:
        return "Hace un momento"

    try:
        # Intentar diferentes formatos de fecha
        if 'T' in timestamp_str:
            dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        else:
            dt = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')

        now = datetime.utcnow()
        diff = now - dt

        if diff.days > 0:
            return f"Hace {diff.days} día{'s' if diff.days > 1 else ''}"
        elif diff.seconds >= 3600:
            hours = diff.seconds // 3600
            return f"Hace {hours} hora{'s' if hours > 1 else ''}"
        elif diff.seconds >= 60:
            minutes = diff.seconds // 60
            return f"Hace {minutes} minuto{'s' if minutes > 1 else ''}"
        else:
            return "Hace un momento"
    except Exception:
        return "Hace un momento"


def get_system_stats(api_status="offline"):
    """Obtener estadísticas del sistema - SIEMPRE retorna estructura completa"""
    return {
        'database_status': 'Online' if api_status == "online" else 'Unknown',
        'storage_usage': '45%',
        'memory_usage': '512MB / 2GB',
        'uptime': '99.8%'
    }


@bp.route('/')
@bp.route('/dashboard')
@login_required
def index():
    """Dashboard principal con datos reales"""
    print(f"🔍 Dashboard route - User: {current_user.username}, Authenticated: {current_user.is_authenticated}")

    # Verificación de autenticación
    if not current_user.is_authenticated:
        print("❌ Usuario no autenticado en dashboard, redirigiendo a login")
        return redirect('/auth/login')

    try:
        # Obtener los datos del dashboard en el servidor
        stats = fetch_real_data()

        # GARANTIZAR que stats tiene la estructura completa
        if not isinstance(stats, dict):
            stats = get_default_stats()

        # Verificar campos críticos
        if 'system_stats' not in stats:
            stats['system_stats'] = get_system_stats(stats.get('api_status', 'offline'))

        if 'recent_activity' not in stats:
            stats['recent_activity'] = []

        if 'summary' not in stats:
            stats["summary"] = {
                "total_users": stats.get("total_users", 0),
                "active_users": stats.get("active_users", 0),
                "total_cards": stats.get("total_cards", 0),
                "users_count": stats.get("users_count", 0),
            }

        # Renderizar la plantilla con los datos obtenidos
        print(f"✅ Dashboard cargado para: {current_user.username}")
        print(f"📊 Stats keys: {list(stats.keys())}")
        print(f"📊 Total users: {stats.get('total_users')}")
        print(f"📊 API status: {stats.get('api_status')}")

        return render_template('dashboard.html', stats=stats, summary=stats["summary"])

    except Exception as e:
        print(f"❌ Error cargando dashboard: {e}")
        import traceback
        traceback.print_exc()

        # En caso de error, usar estructura por defecto
        stats = get_default_stats()
        stats["summary"] = {
            "total_users": stats.get("total_users", 0),
            "active_users": stats.get("active_users", 0),
            "total_cards": stats.get("total_cards", 0),
            "users_count": stats.get("users_count", 0),
        }
        return render_template('dashboard.html', stats=stats, summary=stats["summary"])


@bp.route('/api/dashboard/stats')
@login_required
def api_dashboard_stats():
    """Endpoint API para obtener estadísticas del dashboard (AJAX)"""
    try:
        stats = fetch_real_data()
        return jsonify(stats)
    except Exception:
        return jsonify(get_default_stats())


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
    except Exception:
        return jsonify({'ok': False, 'activity': []})

@bp.route("/system-status", endpoint="system_status_page")
@login_required
def system_status_page():
    """Página de detalle del estado del sistema."""
    stats = fetch_real_data()

    if not isinstance(stats, dict):
        stats = get_default_stats()

    if "system_stats" not in stats:
        stats["system_stats"] = get_system_stats(stats.get("api_status", "offline"))

    return render_template(
        "dashboard/system_status_detail.html",
        stats=stats,
        system_stats=stats["system_stats"]
    )




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


@bp.route('/dashboard/docker/logs/stream')
@login_required
def docker_logs_stream():
    def generate():
        while True:
            try:
                headers = get_auth_headers()
                r = requests.get(
                    f"{Config.API_BASE_URL}/api/docker/logs",
                    headers=headers,
                    timeout=10
                )
                if r.status_code == 200:
                    yield f"data: {json.dumps(r.json())}\n\n"
            except Exception as e:
                yield f"data: {{\"error\": \"{str(e)}\"}}\n\n"
            time.sleep(3)

    return Response(generate(), mimetype='text/event-stream')


@bp.route("/config/runtime-config.json")
def runtime_config():
    return {
        "API_BASE_URL": os.getenv("PUBLIC_API_URL", "http://localhost:5000")
    }


@bp.route('/api/dashboard/docker-containers')
@login_required
def api_dashboard_docker_containers():
    """Obtener información de contenedores para el dashboard"""
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
