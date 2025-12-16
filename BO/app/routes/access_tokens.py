# app/routes/access_tokens.py - Sistema de gestión de tokens de acceso CON DEBUG MEJORADO
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
    print(f"🔐 DEBUG get_auth_headers - Token en sesión: {'✅' if token else '❌'}")
    if token:
        print(f"🔐 DEBUG Token preview: {token[:30]}...")
        headers = {
            'Authorization': f'Bearer {token}', 
            'Content-Type': 'application/json'
        }
        print(f"🔐 DEBUG Headers preparados: {headers}")
        return headers
    
    print("🔐 DEBUG No hay token en sesión")
    return {'Content-Type': 'application/json'}

def generate_token(length=64):
    """Generar token seguro de acceso"""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))


@bp.route('/handle_action', methods=['POST'])
@login_required
def handle_action():
    """
    Endpoint unificado para acciones sobre tokens desde la tabla:
    - revoke
    - reactivate
    - reset
    - delete
    Recibe: action, token_id
    Devuelve JSON para el fetch del frontend.
    """
    action = request.form.get('action')
    token_id = request.form.get('token_id')

    if not action or not token_id:
        return jsonify({
            'success': False,
            'message': 'Acción o token_id no proporcionados'
        }), 400

    # Mapear acciones a URLs internas del propio blueprint
    try:
        if action == 'revoke':
            return _proxy_action(
                f"{Config.API_BASE_URL}/api/access_tokens/{token_id}/revoke",
                json_payload={
                    'revoked_by': current_user.username,
                    'revoked_at': datetime.now(timezone.utc).isoformat()
                },
                success_message='Token revocado exitosamente'
            )
        elif action == 'reactivate':
            return _proxy_action(
                f"{Config.API_BASE_URL}/api/access_tokens/{token_id}/reactivate",
                json_payload={
                    'reactivated_by': current_user.username,
                    'reactivated_at': datetime.now(timezone.utc).isoformat()
                },
                success_message='Token reactivado exitosamente'
            )
        elif action == 'reset':
            return _proxy_action(
                f"{Config.API_BASE_URL}/api/access_tokens/{token_id}/reset_uses",
                json_payload={
                    'reset_by': current_user.username,
                    'reset_at': datetime.now(timezone.utc).isoformat()
                },
                success_message='Contador de usos reiniciado exitosamente'
            )
        elif action == 'delete':
            # DELETE no lleva body JSON
            return _proxy_action(
                f"{Config.API_BASE_URL}/api/access_tokens/{token_id}",
                method='DELETE',
                success_message='Token eliminado permanentemente'
            )
        else:
            return jsonify({
                'success': False,
                'message': 'Acción no soportada'
            }), 400

    except Exception as e:
        print(f"❌ Error en handle_action: {e}")
        return jsonify({
            'success': False,
            'message': 'Error interno al procesar la acción'
        }), 500


def _proxy_action(api_url, json_payload=None, method='PATCH', success_message='Acción realizada correctamente'):
    """
    Helper para llamar a la API y devolver un JSON homogéneo al frontend.
    """
    headers = get_auth_headers()
    try:
        if method == 'DELETE':
            resp = requests.delete(api_url, headers=headers, timeout=10)
        else:
            resp = requests.patch(api_url, headers=headers, json=json_payload, timeout=10)

        if resp.status_code == 200:
            data = resp.json()
            if data.get('ok'):
                return jsonify({'success': True, 'message': success_message})
            else:
                return jsonify({
                    'success': False,
                    'message': data.get('message', 'Error en la API')
                }), 400
        else:
            return jsonify({
                'success': False,
                'message': f'Error del servidor: {resp.status_code}'
            }), 500

    except requests.RequestException as e:
        print(f"❌ Error de conexión en _proxy_action: {e}")
        return jsonify({
            'success': False,
            'message': 'Error de conexión con el servidor'
        }), 500


@bp.route('/')
@login_required
def token_list():
    """Lista todos los tokens de acceso"""
    print("🔑 DEBUG token_list - Iniciando obtención de tokens")
    print(f"🔑 DEBUG Usuario autenticado: {current_user.username}")
    
    try:
        headers = get_auth_headers()
        api_url = f"{Config.API_BASE_URL}/api/access_tokens"
        
        print(f"🌐 DEBUG Llamando a API:")
        print(f"🌐 DEBUG URL: {api_url}")
        print(f"🌐 DEBUG Headers: {headers}")
        print(f"🌐 DEBUG API_BASE_URL config: {Config.API_BASE_URL}")
        
        response = requests.get(
            api_url, 
            headers=headers,
            timeout=10
        )
        
        print(f"📡 DEBUG Respuesta recibida:")
        print(f"📡 DEBUG Status Code: {response.status_code}")
        print(f"📡 DEBUG Response Headers: {dict(response.headers)}")
        print(f"📡 DEBUG Response Text: {response.text[:500]}...")
        
        if response.status_code == 200:
            data = response.json()
            print(f"📋 DEBUG JSON parseado: {data}")
            
            if data.get('ok'):
                tokens = data.get('tokens', [])
                print(f"✅ DEBUG Tokens obtenidos: {len(tokens)}")
                for token in tokens:
                    print(f"   - {token.get('name')}: {token.get('token', '')[:10]}...")
                return render_template('access_tokens/list.html', tokens=tokens)
            else:
                error_msg = data.get('message', 'Error al obtener tokens')
                print(f"❌ DEBUG Error en respuesta JSON: {error_msg}")
                flash(error_msg, 'error')
        else:
            error_msg = f'Error del servidor: {response.status_code} - {response.text}'
            print(f"❌ DEBUG Error HTTP: {error_msg}")
            flash(error_msg, 'error')
    
    except requests.RequestException as e:
        print(f"❌ DEBUG Error de conexión: {e}")
        flash(f'Error de conexión con el servidor: {str(e)}', 'error')
    except Exception as e:
        print(f"❌ DEBUG Error inesperado: {e}")
        import traceback
        traceback.print_exc()
        flash(f'Error interno del sistema: {str(e)}', 'error')
    
    # Fallback con lista vacía
    print("🔄 DEBUG Usando fallback - lista vacía de tokens")
    return render_template('access_tokens/list.html', tokens=[])

@bp.route('/debug-session')
@login_required
def debug_session():
    """Endpoint para debuggear la sesión"""
    debug_info = {
        'session_keys': list(session.keys()),
        'has_api_token': 'api_token' in session,
        'api_token_preview': session.get('api_token', '')[:50] + '...' if session.get('api_token') else None,
        'user_authenticated': current_user.is_authenticated,
        'user_id': current_user.get_id(),
        'username': current_user.username if current_user.is_authenticated else None,
        'config_api_url': Config.API_BASE_URL,
        'config_backoffice_url': Config.BACKOFFICE_API_BASE_URL
    }
    return jsonify(debug_info)

@bp.route('/test-api-connection')
@login_required
def test_api_connection():
    """Endpoint para testear la conexión a la API"""
    try:
        headers = get_auth_headers()
        test_url = f"{Config.API_BASE_URL}/health"
        
        print(f"🧪 TEST Conectando a: {test_url}")
        response = requests.get(test_url, timeout=5)
        
        result = {
            'test_url': test_url,
            'status_code': response.status_code,
            'response': response.text,
            'headers_sent': headers
        }
        
        print(f"🧪 TEST Resultado: {result}")
        return jsonify(result)
        
    except Exception as e:
        print(f"🧪 TEST Error: {e}")
        return jsonify({'error': str(e)}), 500


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
        
        # Fecha de expiración
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
        
        # Añadir email del destinatario si se proporciona
        if recipient_email:
            token_data['recipient_email'] = recipient_email
        
        headers = get_auth_headers()
        response = requests.post(
            f"{Config.API_BASE_URL}/api/access_tokens", 
            headers=headers,
            json=token_data,
            timeout=30
        )
        
        # ✅ CORRECCIÓN CLAVE: aceptar 200 y 201
        if response.status_code in (200, 201):
            data = response.json()
            if data.get('ok'):
                email_info = data.get('email_info')

                if email_info and email_info.get('sent'):
                    flash(
                        f'Token "{name}" creado y enviado por email a {recipient_email}',
                        'success'
                    )
                elif email_info and not email_info.get('sent'):
                    flash(
                        f'Token "{name}" creado pero error al enviar email: {email_info.get("error")}',
                        'warning'
                    )
                else:
                    flash(f'Token "{name}" creado exitosamente', 'success')

                return redirect(url_for('access_tokens.token_list'))
            else:
                flash(data.get('message', 'Error al crear token'), 'error')
        else:
            flash(f'Error del servidor: {response.status_code}', 'error')
    
    except ValueError:
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
    print(f"🔧 DEBUG edit_token - Iniciando edición para token_id: {token_id}")
    
    if request.method == 'GET':
        print(f"📝 DEBUG GET edit - Obteniendo datos del token {token_id}")
        try:
            headers = get_auth_headers()
            api_url = f"{Config.API_BASE_URL}/api/access_tokens/{token_id}"
            print(f"🌐 DEBUG GET edit - Llamando a: {api_url}")
            
            response = requests.get(api_url, headers=headers, timeout=10)
            print(f"📡 DEBUG GET edit - Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"📋 DEBUG GET edit - Respuesta: {data}")
                
                if data.get('ok'):
                    token = data.get('token')
                    print(f"✅ DEBUG GET edit - Token obtenido: {token.get('name') if token else 'None'}")
                    return render_template('access_tokens/edit.html', token=token)
                else:
                    error_msg = data.get('message', 'Token no encontrado')
                    print(f"❌ DEBUG GET edit - Error en data: {error_msg}")
                    flash(error_msg, 'error')
            else:
                error_msg = f'Error del servidor: {response.status_code}'
                print(f"❌ DEBUG GET edit - Error HTTP: {error_msg}")
                flash(error_msg, 'error')
        
        except requests.RequestException as e:
            print(f"❌ DEBUG GET edit - Error de conexión: {e}")
            flash('Error de conexión con el servidor', 'error')
        except Exception as e:
            print(f"❌ DEBUG GET edit - Error inesperado: {e}")
            flash('Error interno del sistema', 'error')
        
        print("🔄 DEBUG GET edit - Redirigiendo a lista de tokens")
        return redirect(url_for('access_tokens.token_list'))
    
    # POST - Actualizar token
    print(f"📝 DEBUG POST edit - Actualizando token {token_id}")
    try:
        # Validar datos del formulario
        name = (request.form.get('name') or '').strip()
        description = (request.form.get('description') or '').strip()
        max_uses = int(request.form.get('max_uses', 1))
        status = request.form.get('status', 'active')
        
        print(f"📋 DEBUG POST edit - Datos recibidos: name={name}, max_uses={max_uses}, status={status}")
        
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
        api_url = f"{Config.API_BASE_URL}/api/access_tokens/{token_id}"
        print(f"🌐 DEBUG POST edit - Actualizando en: {api_url}")
        print(f"📦 DEBUG POST edit - Datos a enviar: {update_data}")
        
        response = requests.put(api_url, headers=headers, json=update_data, timeout=10)
        print(f"📡 DEBUG POST edit - Status Code: {response.status_code}")
        print(f"📡 DEBUG POST edit - Respuesta: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get('ok'):
                flash(f'Token "{name}" actualizado exitosamente', 'success')
            else:
                flash(data.get('message', 'Error al actualizar token'), 'error')
        else:
            flash(f'Error del servidor: {response.status_code}', 'error')
    
    except ValueError as e:
        print(f"❌ DEBUG POST edit - Error de valor: {e}")
        flash('Por favor, verifica que todos los números sean válidos', 'error')
    except requests.RequestException as e:
        print(f"❌ DEBUG POST edit - Error de conexión: {e}")
        flash('Error de conexión con el servidor', 'error')
    except Exception as e:
        print(f"❌ DEBUG POST edit - Error inesperado: {e}")
        flash('Error interno del sistema', 'error')
    
    print("🔄 DEBUG POST edit - Redirigiendo a lista de tokens")
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

@bp.route('/public-debug')
def public_debug():
    """Endpoint público para debug (sin autenticación)"""
    debug_info = {
        'session_keys': list(session.keys()),
        'has_api_token': 'api_token' in session,
        'api_token_preview': session.get('api_token', '')[:50] + '...' if session.get('api_token') else None,
        'user_authenticated': current_user.is_authenticated,
        'config_api_url': Config.API_BASE_URL,
        'config_backoffice_url': Config.BACKOFFICE_API_BASE_URL
    }
    return jsonify(debug_info)

@bp.route('/public-test-api')
def public_test_api():
    """Endpoint público para testear API (sin autenticación)"""
    try:
        test_url = f"{Config.API_BASE_URL}/health"
        response = requests.get(test_url, timeout=5)
        
        result = {
            'test_url': test_url,
            'status_code': response.status_code,
            'response': response.text
        }
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/debug-test')
@login_required  
def debug_test():
    """Endpoint de debug simple con autenticación"""
    try:
        headers = get_auth_headers()
        response = requests.get(f"{Config.API_BASE_URL}/api/access_tokens", headers=headers, timeout=10)
        
        result = {
            'status_code': response.status_code,
            'response_ok': response.ok,
            'data': response.json() if response.status_code == 200 else {'error': response.text}
        }
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

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