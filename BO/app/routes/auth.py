import os
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, session
from flask_login import login_user, logout_user, login_required, current_user
from app.models.user import BackofficeUser
from config import Config
import time
import requests

# 🔥 IMPORTANTE: Usar 'auth' como nombre del blueprint para compatibilidad
bp = Blueprint('auth', __name__, url_prefix='/auth')

def get_auth_headers():
    """Obtener headers de autenticación con token JWT"""
    token = session.get('api_token')
    if token:
        return {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
    return {'Content-Type': 'application/json'}

@bp.route('/login', methods=['GET', 'POST'])
def login():
    print(f"🔐 Login endpoint - Method: {request.method}, User authenticated: {current_user.is_authenticated}")
    print(f"📋 Sesión actual al entrar: {dict(session)}")
    
    if current_user.is_authenticated:
        print("✅ Usuario ya autenticado, redirigiendo a dashboard")
        return redirect('/dashboard')
    
    if request.method == 'POST':
        username = (request.form.get('username') or '').strip()
        password = request.form.get('password') or ''
        
        print(f"🔐 Intentando login para usuario: {username}")
        
        # LIMPIAR sesión completamente
        session.clear()

        user = BackofficeUser.authenticate(username, password)
        
        if user:
            print(f"✅ Autenticación exitosa para: {user.username}")
            print(f"📱 MFA habilitado: {user.mfa_enabled}")
            print(f"🔑 Token obtenido: {user.token[:20] if user.token else 'NO TOKEN'}")
            
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
                print(f"📱 Usuario requiere MFA: {user.username}")
                session['pending_user_id'] = user.id
                session['pending_username'] = user.username
                session['mfa_start_time'] = time.time()
                session['mfa_attempts'] = 0
                return redirect('/auth/verify-mfa')
            else:
                # ✅ LOGIN DIRECTO SIN MFA
                print(f"🔓 Login directo SIN MFA para: {user.username}")
                
                # Hacer login - DEBE funcionar porque user_loader tiene los datos
                login_success = login_user(user, remember=True)
                print(f"🔐 Resultado de login_user: {login_success}")
                print(f"🔐 Current user después de login: {current_user.is_authenticated}")
                
                if current_user.is_authenticated:
                    session['mfa_verified'] = True
                    flash('✅ ¡Bienvenido/a!', 'success')
                    return redirect('/dashboard')
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
    print(f"🔐 Verify MFA - User authenticated: {current_user.is_authenticated}")
    
    pending_user_id = session.get('pending_user_id')
    
    if not pending_user_id:
        flash('⏰ Sesión expirada. Por favor inicia sesión nuevamente.', 'warning')
        return redirect('/auth/login')
    
    # Verificar tiempo de sesión (30 minutos)
    if time.time() - session.get('mfa_start_time', 0) > 1800:
        session.clear()
        flash('⏰ Tiempo de sesión agotado. Por favor inicia sesión nuevamente.', 'warning')
        return redirect('/auth/login')
    
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
            return redirect('/auth/login')
        
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
                return redirect('/dashboard')
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

@bp.route('/verify-mfa-disable', methods=['GET', 'POST'])
@login_required
def verify_mfa_disable():
    """Página de verificación MFA para desactivar"""
    print(f"🔐 Verify MFA Disable - User: {current_user.username}")
    
    disable_user_id = session.get('disable_mfa_user_id')
    
    if not disable_user_id:
        flash('⏰ Sesión expirada. Por favor inicia el proceso nuevamente.', 'warning')
        return redirect('/auth/setup-mfa')
    
    # Verificar tiempo de sesión (5 minutos para desactivar)
    if time.time() - session.get('disable_mfa_start_time', 0) > 300:
        session.pop('disable_mfa_user_id', None)
        session.pop('disable_mfa_username', None)
        session.pop('disable_mfa_start_time', None)
        flash('⏰ Tiempo agotado. Por favor inicia el proceso nuevamente.', 'warning')
        return redirect('/auth/setup-mfa')
    
    if request.method == 'POST':
        mfa_code = request.form.get('mfa_code', '').strip().replace(' ', '')
        
        if not mfa_code or len(mfa_code) != 6 or not mfa_code.isdigit():
            flash('❌ El código debe tener exactamente 6 dígitos numéricos', 'error')
            return render_template('auth/verify_mfa_disable.html', username=session.get('disable_mfa_username'))
        
        # Verificar código MFA con la API
        if verify_mfa_with_api(disable_user_id, mfa_code):
            # MFA verificado, proceder a desactivar
            if disable_mfa_for_user(disable_user_id):
                # 🔥 ACTUALIZAR ESTADO LOCAL DEL USUARIO
                current_user.mfa_enabled = False
                
                # 🔥 ACTUALIZAR session['user_data'] TAMBIÉN
                user_data = session.get('user_data', {})
                user_data['mfa_enabled'] = False
                user_data['mfa_secret'] = ''
                session['user_data'] = user_data
                
                # Limpiar sesión temporal
                session.pop('disable_mfa_user_id', None)
                session.pop('disable_mfa_username', None)
                session.pop('disable_mfa_start_time', None)
                session.pop('mfa_verified', None)
                
                print(f"🔥 MFA DESHABILITADO - Estado actualizado para usuario:")
                print(f"   - current_user.mfa_enabled: {current_user.mfa_enabled}")
                print(f"   - session user_data mfa_enabled: {user_data.get('mfa_enabled')}")
                
                flash('✅ MFA deshabilitado correctamente. Tu cuenta ahora es menos segura.', 'success')
                return redirect('/dashboard')
            else:
                flash('❌ Error al deshabilitar MFA en el servidor', 'error')
        else:
            flash('❌ Código MFA incorrecto', 'error')
    
    return render_template('auth/verify_mfa_disable.html', 
                         username=session.get('disable_mfa_username'))

@bp.route('/setup-mfa', methods=['GET', 'POST'])
@login_required
def setup_mfa():
    """Configuración de MFA integrada con API - VERSIÓN CORREGIDA SIN FALLBACKS"""
    print(f"🔐 Setup MFA - User: {current_user.username}, ID: {current_user.id}")
    
    # 🔥 VALIDACIÓN CRÍTICA: Verificar que el ID es REAL
    if not current_user.id or current_user.id in ['None', 'admin-fallback', 'admin-local']:
        print(f"❌ ID ficticio detectado: {current_user.id}")
        flash('❌ Error: ID de usuario no válido para MFA', 'error')
        return redirect('/dashboard')
    
    real_user_id = current_user.id
    print(f"🎯 Usando ID REAL para MFA: {real_user_id}")
    
    # ✅ PROCESAR FORMULARIO
    if request.method == 'POST':
        action = request.form.get('action')
        print(f"🔄 Acción MFA: {action}")
        
        if action == 'generate':
            # Generar nuevo secreto MFA
            mfa_data = generate_mfa_secret_api(real_user_id)
            if mfa_data:
                # Guardar temporalmente en sesión
                session['mfa_qr_code'] = mfa_data['qr_code']
                session['manual_entry_key'] = mfa_data['manual_entry_key']
                flash('📱 Código QR generado. Escanéalo con tu Microsoft Authenticator.', 'success')
            else:
                flash('❌ Error al generar código QR', 'error')
        
        elif action == 'enable':
            # Verificar código y habilitar MFA
            mfa_code = request.form.get('mfa_code', '').strip().replace(' ', '')
            
            if not mfa_code or len(mfa_code) != 6:
                flash('❌ El código debe tener exactamente 6 dígitos', 'error')
            else:
                print(f"🔐 Verificando código MFA para usuario REAL: {real_user_id}")
                try:
                    # El endpoint verify-setup ya habilita MFA si es correcto
                    if verify_mfa_setup_with_api(real_user_id, mfa_code):
                        # ✅ MFA ya fue habilitado por verify-setup, solo actualizar estado local
                        current_user.mfa_enabled = True
                        
                        # 🔥 ACTUALIZAR session['user_data'] TAMBIÉN
                        user_data = session.get('user_data', {})
                        user_data['mfa_enabled'] = True
                        session['user_data'] = user_data
                        
                        # Limpiar datos temporales de sesión
                        session.pop('mfa_qr_code', None)
                        session.pop('manual_entry_key', None)
                        
                        print(f"🔥 MFA HABILITADO - Estado actualizado para usuario REAL:")
                        print(f"   - current_user.mfa_enabled: {current_user.mfa_enabled}")
                        print(f"   - session user_data mfa_enabled: {user_data.get('mfa_enabled')}")
                        
                        flash('✅ ¡MFA habilitado exitosamente! Tu cuenta ahora está más segura.', 'success')
                        return redirect('/dashboard')
                    else:
                        flash('❌ Código incorrecto. Verifica el código e intenta nuevamente.', 'error')
                except Exception as e:
                    current_app.logger.error(f"Error habilitando MFA: {e}")
                    flash('❌ Error al habilitar MFA', 'error')
        
        elif action == 'disable':
            # PASO 1: Verificar solo contraseña para desactivar MFA
            password = request.form.get('password', '')
            
            if not password:
                flash('❌ Por favor ingresa tu contraseña para deshabilitar MFA', 'error')
            else:
                # PASO 1: Verificar solo usuario/contraseña (sin MFA)
                user = BackofficeUser.authenticate(current_user.username, password, mfa_code=None)
                if user and user.id == real_user_id:
                    # Credenciales correctas, ir a pantalla MFA
                    session['disable_mfa_user_id'] = user.id
                    session['disable_mfa_username'] = user.username
                    session['disable_mfa_start_time'] = time.time()
                    print("🔓 Contraseña correcta - redirigiendo a verificar MFA para desactivar")
                    return redirect('/auth/verify-mfa-disable')
                else:
                    flash('❌ Contraseña incorrecta', 'error')
    
    # Obtener estado MFA actual SIEMPRE DESDE LA API usando ID REAL
    mfa_status = check_user_mfa_status(real_user_id)
    mfa_enabled = mfa_status.get('mfa_enabled', False)
    qr_code = session.get('mfa_qr_code') if not mfa_enabled else None
    manual_entry_key = session.get('manual_entry_key') if not mfa_enabled else None
    
    print(f"🔍 Estado MFA actual (usuario REAL {real_user_id}):")
    print(f"   - API mfa_enabled: {mfa_enabled}")
    print(f"   - current_user.mfa_enabled: {current_user.mfa_enabled}")
    print(f"   - session user_data: {session.get('user_data', {}).get('mfa_enabled', 'NO')}")
    print(f"   - ID en sesión: {session.get('user_id')}")
    
    return render_template('auth/setup_mfa.html',
                         mfa_enabled=mfa_enabled,
                         qr_code=qr_code,
                         manual_entry_key=manual_entry_key,
                         user_email=current_user.email or current_user.username,
                         real_user_id=real_user_id)

# FUNCIONES AUXILIARES PARA COMUNICACIÓN CON LA API - VERSIÓN CORREGIDA

def generate_mfa_secret_api(user_id, issuer="FirefighterAI"):
    """Generar secreto MFA a través de la API - VERSIÓN CORREGIDA"""
    try:
        # 🔥 VALIDAR ID primero
        if not user_id or user_id in ['None', 'admin-fallback', 'admin-local']:
            print(f"❌ ID inválido para generar MFA: {user_id}")
            return None
            
        api_url = os.getenv("API_BASE_URL", "http://localhost:5000")  
        token = session.get('api_token')
        
        if not token:
            print("❌ No hay token de API disponible")
            return None
            
        print(f"🔐 Generando MFA secret para usuario REAL: {user_id}")
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
                print("✅ MFA secret generado exitosamente para usuario REAL")
                return {
                    'secret': data.get('secret'),
                    'qr_code': data.get('qr_code'),
                    'manual_entry_key': data.get('manual_entry_key')
                }
            else:
                print(f"❌ API rechazó generación MFA: {data.get('detail', 'Sin detalle')}")
                return None
        else:
            print(f"❌ Error HTTP en API: {response.status_code}")
            try:
                error_data = response.json()
                print(f"   Detalle: {error_data.get('detail', 'Sin detalle')}")
            except:
                print(f"   Respuesta: {response.text[:200]}")
            return None
            
    except Exception as e:
        print(f"❌ Error generando MFA secret: {e}")
        return None

def verify_mfa_setup_with_api(user_id, mfa_code):
    """Verificar código MFA durante setup usando API - VERSIÓN CORREGIDA"""
    # 🔥 VALIDAR ID primero
    if not user_id or user_id in ['None', 'admin-fallback', 'admin-local']:
        print(f"❌ ID inválido para verificar setup MFA: {user_id}")
        return False
        
    try:
        token = session.get('api_token')
        if not token:
            print("❌ No hay token de API disponible para verificar setup MFA")
            return False
            
        api_url = os.getenv("API_BASE_URL", "http://localhost:5000")
        print(f"🔐 Verificando setup MFA para usuario REAL: {user_id}")
        
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        
        payload = {'code': mfa_code}
        
        response = requests.post(
            f"{api_url}/api/users/{user_id}/mfa/verify-setup",
            headers=headers,
            json=payload,
            timeout=5
        )
        
        print(f"📡 Verify setup response: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            return data.get('ok', False)
        else:
            print(f"❌ Error verificando setup MFA: {response.status_code}")
            return False
            
    except Exception as e:
        current_app.logger.error(f"Error verifying MFA setup: {e}")
        print(f"❌ Excepción verificando setup MFA: {e}")
        return False

def verify_mfa_with_api(user_id, mfa_code):
    """Verificar código MFA usando API - VERSIÓN CORREGIDA"""
    # 🔥 VALIDAR ID primero
    if not user_id or user_id in ['None', 'admin-fallback', 'admin-local']:
        print(f"❌ ID inválido para verificar MFA: {user_id}")
        return False
        
    try:
        token = session.get('api_token')
        if not token:
            print("❌ No hay token de API disponible para verificar MFA")
            return False
            
        api_url = os.getenv("API_BASE_URL", "http://localhost:5000")
        print(f"🔐 Verificando MFA para usuario REAL: {user_id}")
        
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        
        payload = {'code': mfa_code}
        
        response = requests.post(
            f"{api_url}/api/users/{user_id}/mfa/verify",
            headers=headers,
            json=payload,
            timeout=5
        )
        
        print(f"📡 Verify MFA response: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            return data.get('ok', False)
        else:
            print(f"❌ Error verificando MFA: {response.status_code}")
            return False
            
    except Exception as e:
        current_app.logger.error(f"Error verifying MFA: {e}")
        print(f"❌ Excepción verificando MFA: {e}")
        return False

def check_user_mfa_status(user_id):
    """Verificar estado MFA del usuario en la API - VERSIÓN CORREGIDA"""
    # 🔥 VALIDAR ID primero
    if not user_id or user_id in ['None', 'admin-fallback', 'admin-local']:
        print(f"❌ ID inválido para verificar estado MFA: {user_id}")
        return {'mfa_enabled': False}
        
    try:
        token = session.get('api_token')
        if not token:
            print("❌ No hay token de API disponible para verificar estado MFA")
            return {'mfa_enabled': False}
            
        api_url = os.getenv("API_BASE_URL", "http://localhost:5000")
        print(f"🔍 Verificando estado MFA para usuario: {user_id}")
        
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        
        response = requests.get(
            f"{api_url}/api/users/{user_id}",
            headers=headers,
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            mfa_status = {'mfa_enabled': data.get('mfa_enabled', False)}
            print(f"📊 Estado MFA desde API: {mfa_status}")
            return mfa_status
        else:
            print(f"❌ Error obteniendo estado MFA: {response.status_code}")
            return {'mfa_enabled': False}
            
    except Exception as e:
        print(f"❌ Error verificando estado MFA: {e}")
        return {'mfa_enabled': False}
def enable_mfa_for_user(user_id):
    """Habilitar MFA para usuario via API - VERSIÓN CORREGIDA"""
    # 🔥 VALIDAR ID primero
    if not user_id or user_id in ['None', 'admin-fallback', 'admin-local']:
        print(f"❌ ID inválido para habilitar MFA: {user_id}")
        return False
        
    try:
        headers = get_auth_headers()
        response = requests.post(
            f"{Config.API_BASE_URL}/api/users/{user_id}/mfa/enable",
            headers=headers,
            timeout=5
        )
        if response.status_code == 200:
            data = response.json()
            return data.get('ok', False)
    except Exception as e:
        current_app.logger.error(f"Error enabling MFA: {e}")
    return False

def disable_mfa_for_user(user_id):
    """Deshabilitar MFA para usuario via API - VERSIÓN CORREGIDA"""
    # 🔥 VALIDAR ID primero
    if not user_id or user_id in ['None', 'admin-fallback', 'admin-local']:
        print(f"❌ ID inválido para deshabilitar MFA: {user_id}")
        return False
        
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

# LAS SIGUIENTES RUTAS NO NECESITAN CAMBIOS (SE MANTIENEN IGUAL):

@bp.route('/logout')
@login_required
def logout():
    print(f"🔐 Logout - Cerrando sesión de: {current_user.username}")
    session.clear()
    logout_user()
    flash('👋 Sesión cerrada correctamente. ¡Vuelve pronto!', 'success')
    return redirect('/auth/login')

@bp.route('/mfa-recovery')
def mfa_recovery():
    """Página de recuperación MFA"""
    pending_user_id = session.get('pending_user_id')
    
    if not pending_user_id:
        flash('Sesión expirada', 'error')
        return redirect('/auth/login')
    
    return render_template('auth/mfa_recovery.html', 
                         username=session.get('pending_username'))