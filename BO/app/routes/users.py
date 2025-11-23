# app/routes/users.py - VERSIÓN CON PROGRESO
from flask import Blueprint, render_template, request, flash, redirect, url_for, session
from flask_login import login_required, current_user
import requests
from config import Config
from app.models.user import BackofficeUser

bp = Blueprint('users', __name__, url_prefix='/users')

def get_auth_headers():
    """Obtener headers de autenticación con token JWT"""
    token = session.get('api_token')
    if token:
        return {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
    return {'Content-Type': 'application/json'}

@bp.route('/')
@login_required
def user_list():
    try:
        headers = get_auth_headers()
        print(f"🔍 Obteniendo usuarios con headers: {headers}")
        
        response = requests.get(
            f"{Config.API_BASE_URL}/api/users", 
            headers=headers,
            timeout=10
        )
        
        print(f"📡 Respuesta API /api/users: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"📋 Datos usuarios recibidos: {data}")
            if data.get('ok'):
                users = data.get('users', [])
                print(f"✅ Usuarios obtenidos: {len(users)}")
                
                # 📊 Agregar información de progreso básico a cada usuario
                for user in users:
                    # Agregar estadísticas básicas visuales
                    user['progress_summary'] = {
                        'has_leitner': user.get('has_leitner_progress', False),
                        'has_backoffice': user.get('has_backoffice_cards', False),
                        'activity_level': 'alta' if user.get('has_leitner_progress') else 'baja'
                    }
                
                return render_template('users/list.html', users=users)
            else:
                print(f"❌ API error: {data.get('detail', 'Unknown error')}")
                flash(f'Error en la API: {data.get("detail", "Error desconocido")}', 'error')
        elif response.status_code == 401:
            print("❌ Error 401: Token inválido o expirado")
            flash('❌ Sesión expirada. Por favor inicia sesión nuevamente.', 'error')
            return redirect(url_for('auth.login'))
        else:
            print(f"❌ Error HTTP {response.status_code}: {response.text}")
            flash(f'Error al obtener usuarios: {response.status_code}', 'error')
        
        return render_template('users/list.html', users=[])
    
    except requests.RequestException as e:
        print(f"❌ Error de conexión con la API: {e}")
        flash('Error de conexión con la API', 'error')
        return render_template('users/list.html', users=[])

@bp.route('/<user_id>')
@login_required
def user_detail(user_id):
    try:
        headers = get_auth_headers()
        token = session.get('api_token')
        
        print(f"🔍 Obteniendo detalles de usuario {user_id}")
        
        # Obtener información básica del usuario
        response = requests.get(
            f"{Config.API_BASE_URL}/api/users/{user_id}",
            headers=headers,
            timeout=5
        )
        
        print(f"📡 Respuesta API /api/users/{user_id}: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get('ok'):
                user = data.get('user', {})
                print(f"✅ Usuario obtenido: {user.get('username')}")
                
                # 📊 Obtener progreso detallado del usuario
                progress_data = BackofficeUser.get_user_progress(user_id, token)
                
                return render_template('users/detail.html', 
                                     user=user, 
                                     progress=progress_data)
            else:
                print(f"❌ API error: {data.get('detail', 'Unknown error')}")
        elif response.status_code == 401:
            print("❌ Error 401: Token inválido o expirado")
            flash('❌ Sesión expirada. Por favor inicia sesión nuevamente.', 'error')
            return redirect(url_for('auth.login'))
        elif response.status_code == 404:
            flash('Usuario no encontrado', 'error')
        else:
            flash(f'Error: {response.status_code}', 'error')
        
        return redirect(url_for('users.user_list'))
    
    except requests.RequestException as e:
        print(f"❌ Error de conexión: {e}")
        flash('Error de conexión', 'error')
        return redirect(url_for('users.user_list'))

@bp.route('/<user_id>/progress')
@login_required
def user_progress(user_id):
    """Vista específica para el progreso detallado del usuario"""
    try:
        token = session.get('api_token')
        headers = get_auth_headers()
        
        # Obtener información básica del usuario
        user_response = requests.get(
            f"{Config.API_BASE_URL}/api/users/{user_id}",
            headers=headers,
            timeout=5
        )
        
        if user_response.status_code != 200:
            flash('Usuario no encontrado', 'error')
            return redirect(url_for('users.user_list'))
        
        user_data = user_response.json()
        user = user_data.get('user', {})
        
        # 📊 Obtener progreso detallado
        progress_data = BackofficeUser.get_user_progress(user_id, token)
        
        if not progress_data:
            flash('No se pudo obtener el progreso del usuario', 'warning')
            return redirect(url_for('users.user_detail', user_id=user_id))
        
        return render_template('users/progress.html', 
                             user=user, 
                             progress=progress_data)
        
    except Exception as e:
        print(f"❌ Error obteniendo progreso: {e}")
        flash('Error obteniendo progreso del usuario', 'error')
        return redirect(url_for('users.user_list'))

@bp.route('/<user_id>/toggle-status', methods=['POST'])
@login_required
def toggle_user_status(user_id):
    try:
        headers = get_auth_headers()
        
        # Primero obtener el usuario actual
        response = requests.get(
            f"{Config.API_BASE_URL}/api/users/{user_id}",
            headers=headers,
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('ok'):
                current_status = data['user'].get('status', 'active')
                new_status = 'inactive' if current_status == 'active' else 'active'
                
                print(f"🔄 Cambiando estado de usuario {user_id} de {current_status} a {new_status}")
                
                # Actualizar estado
                update_response = requests.patch(
                    f"{Config.API_BASE_URL}/api/users/{user_id}",
                    headers=headers,
                    json={"status": new_status},
                    timeout=5
                )
                
                if update_response.status_code == 200:
                    update_data = update_response.json()
                    if update_data.get('ok'):
                        flash(f'✅ Estado actualizado a {new_status}', 'success')
                    else:
                        flash(f'❌ Error API: {update_data.get("detail", "Error desconocido")}', 'error')
                elif update_response.status_code == 401:
                    flash('❌ Sesión expirada. Por favor inicia sesión nuevamente.', 'error')
                    return redirect(url_for('auth.login'))
                else:
                    flash('❌ Error al actualizar', 'error')
        elif response.status_code == 401:
            flash('❌ Sesión expirada. Por favor inicia sesión nuevamente.', 'error')
            return redirect(url_for('auth.login'))
        
        return redirect(url_for('users.user_detail', user_id=user_id))
    
    except requests.RequestException as e:
        print(f"❌ Error de conexión: {e}")
        flash('Error de conexión', 'error')
        return redirect(url_for('users.user_list'))

# Endpoint temporal para debug
@bp.route('/debug-token')
@login_required
def debug_token():
    """Endpoint temporal para debug del token"""
    token = session.get('api_token')
    return {
        'token_present': bool(token),
        'token_preview': token[:50] + '...' if token else None,
        'current_user': current_user.username,
        'session_keys': list(session.keys())
    }