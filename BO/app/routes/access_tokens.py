# app/routes/access_tokens.py - Sistema de gestión de tokens de acceso
from flask import Blueprint, render_template, redirect, url_for, flash, request, session, jsonify, current_app
from flask_login import login_required, current_user
from datetime import datetime, timedelta, timezone
from config import Config
import requests
import secrets
import string

bp = Blueprint('access_tokens', __name__, url_prefix='/access_tokens')

def get_auth_headers():
    """Obtener headers de autenticación con token JWT"""
    token = session.get('api_token')
    if token:
        return {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
    return {'Content-Type': 'application/json'}

def generate_token(length=64):
    """Generar token seguro de acceso"""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))

@bp.route('/')
@login_required
def token_list():
    """Lista todos los tokens de acceso"""
    print("🔑 Accediendo a lista de tokens")
    
    try:
        headers = get_auth_headers()
        response = requests.get(
            f"{Config.API_BASE_URL}/api/access_tokens", 
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('ok'):
                tokens = data.get('tokens', [])
                print(f"✅ Tokens obtenidos: {len(tokens)}")
                return render_template('access_tokens/list.html', tokens=tokens)
            else:
                flash(data.get('message', 'Error al obtener tokens'), 'error')
        else:
            flash(f'Error del servidor: {response.status_code}', 'error')
    
    except requests.RequestException as e:
        print(f"❌ Error de conexión: {e}")
        flash('Error de conexión con el servidor', 'error')
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        flash('Error interno del sistema', 'error')
    
    # Fallback con lista vacía
    return render_template('access_tokens/list.html', tokens=[])

@bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_token():
    """Crear nuevo token de acceso con envío de email opcional"""
    if request.method == 'GET':
        return render_template('access_tokens/create.html')
    
    try:
        # Validar datos del formulario
        name = (request.form.get('name') or '').strip()
        description = (request.form.get('description') or '').strip()
        recipient_email = (request.form.get('recipient_email') or '').strip()
        max_uses = int(request.form.get('max_uses', 1))
        expires_days = int(request.form.get('expires_days', 30))
        user_type = request.form.get('user_type', 'student')
        
        # Validaciones
        if not name:
            flash('El nombre del token es obligatorio', 'error')
            return render_template('access_tokens/create.html')
        
        if max_uses < 1 or max_uses > 1000:
            flash('Los usos máximos deben estar entre 1 y 1000', 'error')
            return render_template('access_tokens/create.html')
        
        if expires_days < 1 or expires_days > 365:
            flash('Los días de expiración deben estar entre 1 y 365', 'error')
            return render_template('access_tokens/create.html')
        
        # Validar email si se proporciona (OPCIONAL)
        if recipient_email and '@' not in recipient_email:
            flash('Por favor ingresa un email válido', 'error')
            return render_template('access_tokens/create.html')
        
        # Generar token único
        token_value = generate_token()
        
        # CORRECCIÓN: Usar timezone.utc correctamente
        expiration_date = datetime.now(timezone.utc) + timedelta(days=expires_days)
        
        # Preparar datos para la API
        token_data = {
            'name': name,
            'description': description,
            'token': token_value,
            'max_uses': max_uses,
            'user_type': user_type,
            'status': 'active',
            'created_by': current_user.username,
            'expires_at': expiration_date.isoformat()
        }
        
        # Añadir email del destinatario si se proporciona (OPCIONAL)
        if recipient_email:
            token_data['recipient_email'] = recipient_email
        
        headers = get_auth_headers()
        response = requests.post(
            f"{Config.API_BASE_URL}/api/access_tokens", 
            headers=headers,
            json=token_data,
            timeout=30  # Aumentado timeout
        )
        
        if response.status_code == 201:
            data = response.json()
            if data.get('ok'):
                # Verificar si se envió email
                email_info = data.get('email_info')
                if email_info and email_info.get('sent'):
                    flash(f'Token "{name}" creado y enviado por email a {recipient_email}', 'success')
                elif email_info and not email_info.get('sent'):
                    flash(f'Token "{name}" creado pero error al enviar email: {email_info.get("error")}', 'warning')
                else:
                    flash(f'Token "{name}" creado exitosamente', 'success')
                return redirect(url_for('access_tokens.token_list'))
            else:
                flash(data.get('message', 'Error al crear token'), 'error')
        else:
            flash(f'Error del servidor: {response.status_code}', 'error')
    
    except ValueError as e:
        flash('Por favor, verifica que todos los números sean válidos', 'error')
    except requests.RequestException as e:
        print(f"❌ Error de conexión: {e}")
        flash('Error de conexión con el servidor', 'error')
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        flash('Error interno del sistema', 'error')
    
    return render_template('access_tokens/create.html')

@bp.route('/edit/<token_id>', methods=['GET', 'POST'])
@login_required
def edit_token(token_id):
    """Editar token existente"""
    
    if request.method == 'GET':
        try:
            headers = get_auth_headers()
            response = requests.get(
                f"{Config.API_BASE_URL}/api/access_tokens/{token_id}", 
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('ok'):
                    token = data.get('token')
                    return render_template('access_tokens/edit.html', token=token)
                else:
                    flash(data.get('message', 'Token no encontrado'), 'error')
            else:
                flash(f'Error del servidor: {response.status_code}', 'error')
        
        except requests.RequestException as e:
            print(f"❌ Error de conexión: {e}")
            flash('Error de conexión con el servidor', 'error')
        
        return redirect(url_for('access_tokens.token_list'))
    
    # POST - Actualizar token
    try:
        # Validar datos del formulario
        name = (request.form.get('name') or '').strip()
        description = (request.form.get('description') or '').strip()
        max_uses = int(request.form.get('max_uses', 1))
        status = request.form.get('status', 'active')
        
        # Validaciones
        if not name:
            flash('El nombre del token es obligatorio', 'error')
            return redirect(url_for('access_tokens.edit_token', token_id=token_id))
        
        if max_uses < 1 or max_uses > 1000:
            flash('Los usos máximos deben estar entre 1 y 1000', 'error')
            return redirect(url_for('access_tokens.edit_token', token_id=token_id))
        
        # Preparar datos para actualizar
        update_data = {
            'name': name,
            'description': description,
            'max_uses': max_uses,
            'status': status,
            'updated_by': current_user.username,
            'updated_at': datetime.now(timezone.utc).isoformat()
        }
        
        headers = get_auth_headers()
        response = requests.put(
            f"{Config.API_BASE_URL}/api/access_tokens/{token_id}", 
            headers=headers,
            json=update_data,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('ok'):
                flash(f'Token "{name}" actualizado exitosamente', 'success')
            else:
                flash(data.get('message', 'Error al actualizar token'), 'error')
        else:
            flash(f'Error del servidor: {response.status_code}', 'error')
    
    except ValueError as e:
        flash('Por favor, verifica que todos los números sean válidos', 'error')
    except requests.RequestException as e:
        print(f"❌ Error de conexión: {e}")
        flash('Error de conexión con el servidor', 'error')
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        flash('Error interno del sistema', 'error')
    
    return redirect(url_for('access_tokens.token_list'))

@bp.route('/delete/<token_id>', methods=['POST'])
@login_required
def delete_token(token_id):
    """Eliminar token permanentemente"""
    try:
        headers = get_auth_headers()
        response = requests.delete(
            f"{Config.API_BASE_URL}/api/access_tokens/{token_id}", 
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('ok'):
                flash('Token eliminado permanentemente', 'success')
            else:
                flash(data.get('message', 'Error al eliminar token'), 'error')
        else:
            flash(f'Error del servidor: {response.status_code}', 'error')
    
    except requests.RequestException as e:
        print(f"❌ Error de conexión: {e}")
        flash('Error de conexión con el servidor', 'error')
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        flash('Error interno del sistema', 'error')
    
    return redirect(url_for('access_tokens.token_list'))

@bp.route('/revoke/<token_id>', methods=['POST'])
@login_required
def revoke_token(token_id):
    """Revocar token (cambiar status a revoked)"""
    try:
        headers = get_auth_headers()
        response = requests.patch(
            f"{Config.API_BASE_URL}/api/access_tokens/{token_id}/revoke", 
            headers=headers,
            json={'revoked_by': current_user.username, 'revoked_at': datetime.now(timezone.utc).isoformat()},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('ok'):
                flash('Token revocado exitosamente', 'success')
            else:
                flash(data.get('message', 'Error al revocar token'), 'error')
        else:
            flash(f'Error del servidor: {response.status_code}', 'error')
    
    except requests.RequestException as e:
        print(f"❌ Error de conexión: {e}")
        flash('Error de conexión con el servidor', 'error')
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        flash('Error interno del sistema', 'error')
    
    return redirect(url_for('access_tokens.token_list'))

@bp.route('/reactivate/<token_id>', methods=['POST'])
@login_required
def reactivate_token(token_id):
    """Reactivar token revocado"""
    try:
        headers = get_auth_headers()
        response = requests.patch(
            f"{Config.API_BASE_URL}/api/access_tokens/{token_id}/reactivate", 
            headers=headers,
            json={'reactivated_by': current_user.username, 'reactivated_at': datetime.now(timezone.utc).isoformat()},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('ok'):
                flash('Token reactivado exitosamente', 'success')
            else:
                flash(data.get('message', 'Error al reactivar token'), 'error')
        else:
            flash(f'Error del servidor: {response.status_code}', 'error')
    
    except requests.RequestException as e:
        print(f"❌ Error de conexión: {e}")
        flash('Error de conexión con el servidor', 'error')
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        flash('Error interno del sistema', 'error')
    
    return redirect(url_for('access_tokens.token_list'))

@bp.route('/reset_uses/<token_id>', methods=['POST'])
@login_required
def reset_uses(token_id):
    """Reiniciar contador de usos a 0"""
    try:
        headers = get_auth_headers()
        response = requests.patch(
            f"{Config.API_BASE_URL}/api/access_tokens/{token_id}/reset_uses", 
            headers=headers,
            json={'reset_by': current_user.username, 'reset_at': datetime.now(timezone.utc).isoformat()},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('ok'):
                flash('Contador de usos reiniciado exitosamente', 'success')
            else:
                flash(data.get('message', 'Error al reiniciar usos'), 'error')
        else:
            flash(f'Error del servidor: {response.status_code}', 'error')
    
    except requests.RequestException as e:
        print(f"❌ Error de conexión: {e}")
        flash('Error de conexión con el servidor', 'error')
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        flash('Error interno del sistema', 'error')
    
    return redirect(url_for('access_tokens.token_list'))

@bp.route('/api/stats')
@login_required
def token_stats():
    """API endpoint para estadísticas de tokens en tiempo real"""
    try:
        headers = get_auth_headers()
        response = requests.get(
            f"{Config.API_BASE_URL}/api/access_tokens/stats", 
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('ok'):
                return jsonify(data.get('stats', {}))
        
        return jsonify({'error': 'No se pudieron obtener estadísticas'}), 500
    
    except Exception as e:
        print(f"❌ Error al obtener estadísticas: {e}")
        return jsonify({'error': 'Error interno del servidor'}), 500