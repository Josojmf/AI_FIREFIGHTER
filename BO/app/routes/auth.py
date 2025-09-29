# app/routes/auth.py (VERSIÓN CORREGIDA - COMPLETA)
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, session
from flask_login import login_user, logout_user, login_required, current_user
from app.models.user import BackofficeUser
import time
import requests
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
    
    if current_user.is_authenticated:
        print("✅ Usuario ya autenticado, redirigiendo a dashboard")
        return redirect(url_for('dashboard.index'))
        
    if request.method == 'POST':
        username = (request.form.get('username') or '').strip()
        password = request.form.get('password') or ''
        
        print(f"🔍 Intentando login para usuario: {username}")
        
        session.clear()

        user = BackofficeUser.authenticate(username, password)
        
        if user:
            print(f"✅ Autenticación exitosa para: {user.username}")
            print(f"🔍 MFA habilitado: {user.mfa_enabled}")
            print(f"🔍 MFA Secret presente: {bool(user.mfa_secret)}")
            
            # ✅ GUARDAR TOKEN DE API EN SESIÓN
            session['api_token'] = user.token
            
            # ✅ DECISIÓN MFA BASADA EN DATOS REALES DE LA API
            if user.mfa_enabled:
                # Usuario tiene MFA habilitado - requerir verificación
                session['pending_user_id'] = user.id
                session['pending_username'] = user.username
                session['mfa_start_time'] = time.time()
                session['mfa_attempts'] = 0
                
                print(f"🔐 Usuario requiere MFA: {user.username}")
                return redirect(url_for('auth.verify_mfa'))
            else:
                # Usuario sin MFA - login directo
                print(f"🔓 Usuario SIN MFA: {user.username} - Login directo")
                login_user(user, remember=True)
                session['user_id'] = user.id
                session['mfa_verified'] = True
                
                print(f"✅ Login directo exitoso para: {user.username}")
                flash('✅ ¡Bienvenido/a!', 'success')
                return redirect(url_for('dashboard.index'))
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
            # ✅ Código correcto
            user = BackofficeUser.get(pending_user_id, session.get('api_token'))
            if user:
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
            # Generar nuevo secreto MFA via API (CON AUTENTICACIÓN)
            try:
                headers = get_auth_headers()
                response = requests.post(
                    f"{Config.API_BASE_URL}/api/users/{current_user.id}/mfa/generate",
                    headers=headers,
                    timeout=10
                )
                if response.status_code == 200:
                    data = response.json()
                    if data.get('ok'):
                        session['mfa_secret'] = data.get('secret')
                        session['mfa_qr_code'] = data.get('qr_code')
                        flash('✅ Secreto MFA generado correctamente. Escanea el código QR.', 'success')
                    else:
                        flash(f'❌ {data.get("detail", "Error al generar el secreto MFA")}', 'error')
                else:
                    flash('❌ Error de conexión con la API', 'error')
            except Exception as e:
                current_app.logger.error(f"Error generando secreto MFA: {e}")
                flash('❌ Error al generar el secreto MFA', 'error')
            return redirect(url_for('auth.setup_mfa'))
        
        elif action == 'enable':
            # Verificar código y habilitar MFA
            mfa_code = request.form.get('mfa_code', '').strip()
            
            if not mfa_code:
                flash('❌ Por favor ingresa el código de verificación', 'error')
            elif not session.get('mfa_secret'):
                flash('❌ Primero debes generar un secreto MFA', 'error')
            else:
                # Verificar código via API (CON AUTENTICACIÓN)
                if verify_mfa_setup(current_user.id, mfa_code, session.get('mfa_secret')):
                    # Habilitar MFA via API (CON AUTENTICACIÓN)
                    if enable_mfa_for_user(current_user.id, session.get('mfa_secret')):
                        # Actualizar estado local del usuario
                        current_user.mfa_enabled = True
                        session['mfa_verified'] = True
                        session.pop('mfa_secret', None)
                        session.pop('mfa_qr_code', None)
                        
                        flash('✅ MFA habilitado correctamente. Tu cuenta ahora está más segura.', 'success')
                        return redirect(url_for('dashboard.index'))
                    else:
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
                        # Actualizar estado local del usuario
                        current_user.mfa_enabled = False
                        session.pop('mfa_verified', None)
                        flash('✅ MFA deshabilitado correctamente', 'success')
                        return redirect(url_for('dashboard.index'))
                    else:
                        flash('❌ Error al deshabilitar MFA', 'error')
                else:
                    flash('❌ Contraseña incorrecta', 'error')
    
    # Obtener estado MFA actual (CON AUTENTICACIÓN)
    mfa_status = check_user_mfa_status(current_user.id)
    mfa_enabled = mfa_status.get('mfa_enabled', False)
    qr_code = session.get('mfa_qr_code') if not mfa_enabled else None
    
    return render_template('auth/setup_mfa.html', 
                         qr_code=qr_code,
                         mfa_enabled=mfa_enabled)

# FUNCIONES AUXILIARES PARA COMUNICACIÓN CON LA API (CON AUTENTICACIÓN)
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