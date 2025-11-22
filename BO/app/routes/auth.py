# app/routes/auth.py - VERSIÓN COMPLETA CON MFA INTEGRADO
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, session
from flask_login import login_user, logout_user, login_required, current_user
from app.models.user import BackofficeUser
import time
import requests
import pyotp
import qrcode
import io
import base64
from config import Config

bp = Blueprint('auth', __name__, url_prefix='/auth')

def get_auth_headers():
    """Obtener headers de autenticación con token JWT"""
    token = session.get('api_token')
    if token:
        return {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
    return {'Content-Type': 'application/json'}

@bp.route('/login', methods=['GET', 'POST'])
def login():
    print(f"🔍 Login endpoint - Method: {request.method}, User authenticated: {current_user.is_authenticated}")
    print(f"📋 Sesión actual al entrar: {dict(session)}")
    
    if current_user.is_authenticated:
        print("✅ Usuario ya autenticado, redirigiendo a dashboard")
        return redirect(url_for('dashboard.index'))
        
    if request.method == 'POST':
        username = (request.form.get('username') or '').strip()
        password = request.form.get('password') or ''
        
        print(f"🔍 Intentando login para usuario: {username}")
        
        # LIMPIAR sesión completamente
        session.clear()

        user = BackofficeUser.authenticate(username, password)
        
        if user:
            print(f"✅ Autenticación exitosa para: {user.username}")
            print(f"🔍 MFA habilitado: {user.mfa_enabled}")
            print(f"🔍 Token obtenido: {user.token[:20] if user.token else 'NO TOKEN'}")
            
            # ✅ CRÍTICO: GUARDAR DATOS EN SESIÓN ANTES DE login_user
            session['api_token'] = user.token
            session['user_data'] = user.to_dict()
            session['user_id'] = user.id
            session.permanent = True
            
            print(f"💾 Datos guardados en sesión:")
            print(f"   - user_id: {session.get('user_id')}")
            print(f"   - token: {session.get('api_token')[:20] if session.get('api_token') else 'NO'}")
            print(f"   - user_data: {'✅' if session.get('user_data') else '❌'}")
            
            # ✅ DECISIÓN MFA
            if user.mfa_enabled:
                print(f"🔐 Usuario requiere MFA: {user.username}")
                session['pending_user_id'] = user.id
                session['pending_username'] = user.username
                session['mfa_start_time'] = time.time()
                session['mfa_attempts'] = 0
                return redirect(url_for('auth.verify_mfa'))
            else:
                # ✅ LOGIN DIRECTO SIN MFA
                print(f"🔓 Login directo SIN MFA para: {user.username}")
                
                # Hacer login - DEBE funcionar porque user_loader tiene los datos
                login_success = login_user(user, remember=True)
                print(f"🔍 Resultado de login_user: {login_success}")
                print(f"🔍 Current user después de login: {current_user.is_authenticated}")
                
                if current_user.is_authenticated:
                    session['mfa_verified'] = True
                    flash('✅ ¡Bienvenido/a!', 'success')
                    return redirect(url_for('dashboard.index'))
                else:
                    print("❌ CRÍTICO: login_user no estableció autenticación")
                    flash('❌ Error interno de autenticación', 'error')
        else:
            print("❌ Autenticación fallida")
            flash('❌ Credenciales inválidas', 'error')
    
    return render_template('auth/login.html')

@bp.route('/verify-mfa', methods=['GET', 'POST'])
def verify_mfa():
    """Página de verificación MFA"""
    print(f"🔍 Verify MFA - User authenticated: {current_user.is_authenticated}")
    
    pending_user_id = session.get('pending_user_id')
    
    if not pending_user_id:
        flash('⏰ Sesión expirada. Por favor inicia sesión nuevamente.', 'warning')
        return redirect(url_for('auth.login'))
    
    # Verificar tiempo de sesión (30 minutos)
    if time.time() - session.get('mfa_start_time', 0) > 1800:
        session.clear()
        flash('⏰ Tiempo de sesión agotado. Por favor inicia sesión nuevamente.', 'warning')
        return redirect(url_for('auth.login'))
    
    if request.method == 'POST':
        mfa_code = request.form.get('mfa_code', '').strip().replace(' ', '')
        
        if not mfa_code or len(mfa_code) != 6 or not mfa_code.isdigit():
            flash('❌ El código debe tener exactamente 6 dígitos numéricos', 'error')
            return render_template('auth/verify_mfa.html', username=session.get('pending_username'))
        
        # Verificar intentos
        mfa_attempts = session.get('mfa_attempts', 0) + 1
        session['mfa_attempts'] = mfa_attempts
        
        if mfa_attempts > 5:
            session.clear()
            flash('🚫 Demasiados intentos fallidos. Sesión cerrada por seguridad.', 'error')
            return redirect(url_for('auth.login'))
        
        # Verificar código MFA con la API (CON AUTENTICACIÓN)
        if verify_mfa_with_api(pending_user_id, mfa_code):
            # ✅ Código correcto - Cargar usuario y hacer login
            user = BackofficeUser.get(pending_user_id, session.get('api_token'))
            if user:
                # Actualizar token en sesión
                session['api_token'] = user.token
                session['user_data'] = user.to_dict()
                session.permanent = True
                
                login_user(user, remember=True)
                session['user_id'] = user.id
                session['mfa_verified'] = True
                session.pop('pending_user_id', None)
                session.pop('pending_username', None)
                session.pop('mfa_attempts', None)
                session.pop('mfa_start_time', None)
                
                print(f"✅ MFA verificado exitosamente para: {user.username}")
                flash('✅ ¡Verificación exitosa! Bienvenido/a.', 'success')
                return redirect(url_for('dashboard.index'))
            else:
                flash('❌ Error al cargar usuario después de MFA', 'error')
        else:
            # Código incorrecto
            remaining_attempts = 5 - mfa_attempts
            if remaining_attempts > 0:
                flash(f'❌ Código incorrecto. Te quedan {remaining_attempts} intentos.', 'error')
            else:
                flash('❌ Código incorrecto. Último intento.', 'error')
    
    return render_template('auth/verify_mfa.html', 
                         username=session.get('pending_username'),
                         attempts=session.get('mfa_attempts', 0))

@bp.route('/setup-mfa', methods=['GET', 'POST'])
@login_required
def setup_mfa():
    """Configuración de MFA integrada con API"""
    print(f"🔍 Setup MFA - User: {current_user.username}")
    
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'generate':
            # Generar secreto MFA vía API
            print(f"🔐 Generando secreto MFA para usuario: {current_user.id}")
            mfa_data = generate_mfa_secret_api(current_user.id)
            
            if mfa_data:
                # Guardar datos en sesión
                session['mfa_secret'] = mfa_data['secret']
                session['mfa_qr_code'] = mfa_data['qr_code']
                session['manual_entry_key'] = mfa_data['manual_entry_key']
                
                print(f"✅ QR code generado y guardado en sesión")
                print(f"🔑 Secret: {mfa_data['secret']}")
                flash('✅ Código QR generado correctamente', 'success')
            else:
                print(f"❌ Error generando QR code")
                flash('❌ Error generando código QR. Intenta nuevamente.', 'error')
            
            return redirect(url_for('auth.setup_mfa'))
        
        elif action == 'enable':
            # Verificar código y habilitar MFA
            mfa_code = request.form.get('mfa_code', '').strip()
            
            if not mfa_code:
                flash('❌ Por favor ingresa el código de verificación', 'error')
            elif not session.get('mfa_secret'):
                flash('❌ Primero debes generar un secreto MFA', 'error')
            else:
                # Verificar código localmente primero
                secret = session.get('mfa_secret')
                totp = pyotp.TOTP(secret)
                
                if totp.verify(mfa_code, valid_window=2):  # Permitir ventana de tiempo
                    # Habilitar MFA via API
                    try:
                        if enable_mfa_for_user(current_user.id, secret):
                            # 🔥 CRÍTICO: ACTUALIZAR ESTADO LOCAL DEL USUARIO
                            current_user.mfa_enabled = True
                            
                            # 🔥 ACTUALIZAR session['user_data'] TAMBIÉN
                            user_data = session.get('user_data', {})
                            user_data['mfa_enabled'] = True
                            user_data['mfa_secret'] = secret
                            session['user_data'] = user_data
                            
                            session['mfa_verified'] = True
                            session.pop('mfa_secret', None)
                            session.pop('mfa_qr_code', None)
                            session.pop('manual_entry_key', None)
                            
                            print(f"🔥 MFA HABILITADO - Estado actualizado:")
                            print(f"   - current_user.mfa_enabled: {current_user.mfa_enabled}")
                            print(f"   - session user_data mfa_enabled: {user_data.get('mfa_enabled')}")
                            
                            flash('✅ MFA habilitado correctamente. Tu cuenta ahora está más segura.', 'success')
                            return redirect(url_for('dashboard.index'))
                        else:
                            flash('❌ Error al habilitar MFA en el servidor', 'error')
                    except Exception as e:
                        current_app.logger.error(f"Error habilitando MFA: {e}")
                        flash('❌ Error al habilitar MFA', 'error')
                else:
                    flash('❌ Código incorrecto. Verifica el código e intenta nuevamente.', 'error')
        
        elif action == 'disable':
            # Deshabilitar MFA via API
            password = request.form.get('password', '')
            
            if not password:
                flash('❌ Por favor ingresa tu contraseña para deshabilitar MFA', 'error')
            else:
                # Re-autenticar usuario
                user = BackofficeUser.authenticate(current_user.username, password)
                if user and user.id == current_user.id:
                    if disable_mfa_for_user(current_user.id):
                        # 🔥 ACTUALIZAR ESTADO LOCAL DEL USUARIO
                        current_user.mfa_enabled = False
                        
                        # 🔥 ACTUALIZAR session['user_data'] TAMBIÉN
                        user_data = session.get('user_data', {})
                        user_data['mfa_enabled'] = False
                        user_data['mfa_secret'] = ''
                        session['user_data'] = user_data
                        
                        session.pop('mfa_verified', None)
                        
                        print(f"🔥 MFA DESHABILITADO - Estado actualizado:")
                        print(f"   - current_user.mfa_enabled: {current_user.mfa_enabled}")
                        print(f"   - session user_data mfa_enabled: {user_data.get('mfa_enabled')}")
                        
                        flash('✅ MFA deshabilitado correctamente', 'success')
                        return redirect(url_for('dashboard.index'))
                    else:
                        flash('❌ Error al deshabilitar MFA', 'error')
                else:
                    flash('❌ Contraseña incorrecta', 'error')
    
    # Obtener estado MFA actual SIEMPRE DESDE LA API
    mfa_status = check_user_mfa_status(current_user.id)
    mfa_enabled = mfa_status.get('mfa_enabled', False)
    qr_code = session.get('mfa_qr_code') if not mfa_enabled else None
    manual_entry_key = session.get('manual_entry_key') if not mfa_enabled else None
    
    # 🔥 DEBUG: Mostrar estado actual
    print(f"🔍 Estado MFA actual:")
    print(f"   - API mfa_enabled: {mfa_enabled}")
    print(f"   - current_user.mfa_enabled: {current_user.mfa_enabled}")
    print(f"   - session user_data: {session.get('user_data', {}).get('mfa_enabled')}")
    
    return render_template('auth/setup_mfa.html', 
                         qr_code=qr_code,
                         mfa_enabled=mfa_enabled,
                         manual_entry_key=manual_entry_key,
                         user_email=current_user.email or current_user.username)

# FUNCIONES AUXILIARES PARA COMUNICACIÓN CON LA API

def generate_mfa_secret_api(user_id, issuer="OnFire"):
    """Generar secreto MFA a través de la API"""
    try:
        api_url = current_app.config['API_BASE_URL']
        token = session.get('api_token')
        
        if not token:
            print("❌ No hay token de API disponible")
            return None
            
        print(f"🔐 Generando MFA secret para usuario: {user_id}")
        print(f"🌐 API URL: {api_url}/api/users/{user_id}/mfa/generate")
        
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        
        payload = {'issuer': issuer}
        
        response = requests.post(
            f"{api_url}/api/users/{user_id}/mfa/generate",
            headers=headers,
            json=payload,
            timeout=10
        )
        
        print(f"📡 Respuesta API: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get('ok'):
                print("✅ MFA secret generado exitosamente")
                return {
                    'secret': data.get('secret'),
                    'qr_code': data.get('qr_code'),
                    'manual_entry_key': data.get('manual_entry_key')
                }
            else:
                print(f"❌ Error en respuesta API: {data.get('detail')}")
                return None
        else:
            print(f"❌ Error HTTP: {response.status_code}")
            try:
                error_data = response.json()
                print(f"❌ Detalle del error: {error_data.get('detail')}")
            except:
                print(f"❌ Respuesta no JSON: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Error generando MFA secret: {e}")
        import traceback
        traceback.print_exc()
        return None

def check_user_mfa_status(user_id):
    """Verificar estado MFA del usuario via API"""
    try:
        headers = get_auth_headers()
        response = requests.get(
            f"{Config.API_BASE_URL}/api/users/{user_id}",
            headers=headers,
            timeout=5
        )
        if response.status_code == 200:
            data = response.json()
            if data.get('ok'):
                user_data = data.get('user', {})
                return {
                    'mfa_enabled': user_data.get('mfa_enabled', False),
                    'mfa_secret': user_data.get('mfa_secret', '')
                }
    except Exception as e:
        current_app.logger.error(f"Error checking MFA status: {e}")
    return {'mfa_enabled': False, 'mfa_secret': ''}

def verify_mfa_with_api(user_id, mfa_code):
    """Verificar código MFA via API"""
    try:
        headers = get_auth_headers()
        response = requests.post(
            f"{Config.API_BASE_URL}/api/users/{user_id}/mfa/verify",
            headers=headers,
            json={'code': mfa_code},
            timeout=5
        )
        if response.status_code == 200:
            data = response.json()
            return data.get('valid', False)
        elif response.status_code == 401:
            current_app.logger.error("Error 401: Token inválido o expirado")
    except Exception as e:
        current_app.logger.error(f"Error verifying MFA code: {e}")
    return False

def verify_mfa_setup(user_id, mfa_code, secret):
    """Verificar código durante setup MFA"""
    try:
        headers = get_auth_headers()
        response = requests.post(
            f"{Config.API_BASE_URL}/api/users/{user_id}/mfa/verify-setup",
            headers=headers,
            json={'code': mfa_code, 'secret': secret},
            timeout=5
        )
        if response.status_code == 200:
            data = response.json()
            return data.get('valid', False)
    except Exception as e:
        current_app.logger.error(f"Error verifying MFA setup: {e}")
    
    # Fallback: verificar localmente
    try:
        totp = pyotp.TOTP(secret)
        return totp.verify(mfa_code, valid_window=2)
    except Exception as e:
        current_app.logger.error(f"Error en verificación local: {e}")
        return False

def enable_mfa_for_user(user_id, secret):
    """Habilitar MFA para usuario via API"""
    try:
        headers = get_auth_headers()
        response = requests.post(
            f"{Config.API_BASE_URL}/api/users/{user_id}/mfa/enable",
            headers=headers,
            json={'secret': secret},
            timeout=5
        )
        if response.status_code == 200:
            data = response.json()
            return data.get('ok', False)
    except Exception as e:
        current_app.logger.error(f"Error enabling MFA: {e}")
    return False

def disable_mfa_for_user(user_id):
    """Deshabilitar MFA para usuario via API"""
    try:
        headers = get_auth_headers()
        response = requests.post(
            f"{Config.API_BASE_URL}/api/users/{user_id}/mfa/disable",
            headers=headers,
            timeout=5
        )
        if response.status_code == 200:
            data = response.json()
            return data.get('ok', False)
    except Exception as e:
        current_app.logger.error(f"Error disabling MFA: {e}")
    return False

@bp.route('/logout')
@login_required
def logout():
    print(f"🔍 Logout - Cerrando sesión de: {current_user.username}")
    session.clear()
    logout_user()
    flash('👋 Sesión cerrada correctamente. ¡Vuelve pronto!', 'success')
    return redirect(url_for('auth.login'))

@bp.route('/mfa-recovery')
def mfa_recovery():
    """Página de recuperación MFA"""
    pending_user_id = session.get('pending_user_id')
    
    if not pending_user_id:
        flash('Sesión expirada', 'error')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/mfa_recovery.html', 
                         username=session.get('pending_username'))

@bp.route('/clear-session')
def clear_session():
    """Ruta temporal para limpiar sesiones - SOLO DESARROLLO"""
    session.clear()
    flash('🧹 Sesión limpiada correctamente', 'info')
    return redirect(url_for('auth.login'))

@bp.route('/debug-session')
def debug_session():
    """Endpoint de diagnóstico"""
    info = {
        'session': dict(session),
        'current_user': {
            'is_authenticated': current_user.is_authenticated,
            'id': getattr(current_user, 'id', None),
            'username': getattr(current_user, 'username', None),
            'mfa_enabled': getattr(current_user, 'mfa_enabled', None)
        } if current_user else None,
        'cookies': dict(request.cookies)
    }
    return info