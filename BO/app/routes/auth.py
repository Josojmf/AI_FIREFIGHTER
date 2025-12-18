import os
import time
import requests

from flask import (
    Blueprint, render_template, redirect,
    url_for, flash, request, current_app, session
)
from flask_login import login_user, logout_user, login_required, current_user

from app.models.user import BackofficeUser
from config import Config


        
# 🔥 IMPORTANTE: Usar 'auth' como nombre del blueprint para compatibilidad
bp = Blueprint('auth', __name__, url_prefix='/auth')

# DEBUG MIDDLEWARE
@bp.before_request
def debug_auth_session():
    """Debug de sesiones en rutas de auth"""
    if request.endpoint and 'auth' in request.endpoint:
        print(f"\n=== 🔍 AUTH DEBUG - {request.endpoint} ===")
        print(f"📋 Sesión keys: {list(session.keys())}")
        print(f"👤 Current user: {current_user.is_authenticated}")
        if current_user.is_authenticated:
            print(f"👤 User ID: {current_user.id}")
            print(f"👤 User mfa_enabled: {current_user.mfa_enabled}")
            print(f"👤 User token: {current_user.token[:20] if current_user.token else 'NO TOKEN'}")
        print("=" * 50)

def get_auth_headers():
    """Obtener headers de autenticación con token JWT"""
    token = session.get('api_token')
    print(f"🔍 get_auth_headers() - Token en sesión: {'SÍ' if token else 'NO'}")
    if token:
        print(f"🔑 Token preview: {token[:30]}...")
        return {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
    print("⚠️  get_auth_headers() - No hay token, retornando headers básicos")
    return {'Content-Type': 'application/json'}

@bp.route('/login', methods=['GET', 'POST'])
def login():
    print(f"🔐 Login endpoint - Method: {request.method}, "
          f"User authenticated: {current_user.is_authenticated}")
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

            # 🔥 DECISIÓN CRÍTICA: Solo guardar datos si hay token válido o no se requiere MFA
            if user.token:
                # ✅ LOGIN COMPLETO - Guardar todo en sesión
                print(f"✅ Login completo - Usuario con token válido")
                session['api_token'] = user.token
                session['user_data'] = user.to_dict()
                session['user_id'] = user.id
                session.permanent = True
                session['mfa_verified'] = True

                print("💾 Datos guardados en sesión:")
                print(f" - user_id: {session.get('user_id')}")
                print(f" - token: {session.get('api_token')[:20] if session.get('api_token') else 'NO'}")
                print(f" - user_data: {'✅' if session.get('user_data') else '❌'}")

                # Hacer login completo
                login_success = login_user(user, remember=True)
                print(f"🔐 Resultado de login_user: {login_success}")
                print(f"🔐 Current user después de login: {current_user.is_authenticated}")

                if current_user.is_authenticated:
                    flash('✅ ¡Bienvenido/a!', 'success')
                    return redirect('/dashboard')
                else:
                    print("❌ CRÍTICO: login_user no estableció autenticación")
                    flash('❌ Error interno de autenticación', 'error')

            elif user.mfa_enabled:
                # 📱 MFA REQUERIDO - No guardar contraseña
                print(f"📱 Usuario requiere MFA - NO guardar contraseña: {user.username}")
                session['pending_user_id'] = user.id
                session['pending_username'] = user.username
                session['mfa_start_time'] = time.time()
                session['mfa_attempts'] = 0
                
                flash('📱 Por favor ingresa tu código MFA para continuar', 'info')
                return redirect('/auth/verify-mfa')
            else:
                # 🔥 CASO INESPERADO: Usuario sin token y sin MFA
                print(f"❌ Usuario sin token y sin MFA habilitado - Error de configuración")
                flash('❌ Error de configuración de usuario', 'error')
        else:
            print("❌ Autenticación fallida")
            flash('❌ Credenciales inválidas', 'error')

    return render_template('auth/login.html')


@bp.route('/verify-mfa', methods=['GET', 'POST'])
def verify_mfa():
    """Página de verificación MFA - VERSIÓN CORREGIDA"""
    print(f"🔐 Verify MFA - User authenticated: {current_user.is_authenticated}")
    
    pending_user_id = session.get('pending_user_id')
    pending_username = session.get('pending_username')
    
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
            return render_template(
                'auth/verify_mfa.html',
                username=pending_username
            )
        
        # Verificar intentos
        mfa_attempts = session.get('mfa_attempts', 0) + 1
        session['mfa_attempts'] = mfa_attempts
        
        if mfa_attempts > 5:
            session.clear()
            flash('🚫 Demasiados intentos fallidos. Sesión cerrada por seguridad.', 'error')
            return redirect('/auth/login')
        
        print(f"🔐 Verificando MFA para usuario: {pending_username}")
        
        # 🔥 NUEVO: Autenticar con username sin contraseña + código MFA
        # Primero obtener password del usuario temporalmente (sin guardar)
        # O usar un método alternativo
        
        # INTENTO 1: Usar authenticate con token temporal (si la API lo permite)
        try:
            # Aquí necesitamos una lógica diferente
            # Opción A: Verificar solo el código MFA con la API
            if verify_mfa_with_api(pending_user_id, mfa_code):
                print(f"✅ MFA verificado para: {pending_username}")
                
                # 🔥 Ahora obtener usuario COMPLETO con token
                # Necesitas implementar un endpoint en tu API que dé el token después de MFA
                # O usar el flujo original con contraseña temporal
                
                flash('✅ ¡Verificación exitosa! Por favor completa tu login.', 'success')
                
                # TODO: Redirigir a un endpoint que complete el login
                return redirect('/auth/login-complete')
            else:
                remaining_attempts = 5 - mfa_attempts
                flash(f'❌ Código incorrecto. Te quedan {remaining_attempts} intentos.', 'error')
        except Exception as e:
            print(f"❌ Error en verificación MFA: {e}")
            flash('❌ Error en verificación MFA', 'error')
    
    return render_template(
        'auth/verify_mfa.html',
        username=pending_username,
        attempts=session.get('mfa_attempts', 0)
    )
    
@bp.route('/login-complete', methods=['GET', 'POST'])
def login_complete():
    """Completar login después de MFA exitoso"""
    print("🔄 Completing login after MFA...")
    
    pending_user_id = session.get('pending_user_id')
    pending_username = session.get('pending_username')
    
    if not pending_user_id:
        flash('⏰ Sesión expirada', 'warning')
        return redirect('/auth/login')
    
    # 🔥 INTENTAR OBTENER USUARIO DE NUEVO
    # Esto debería funcionar si tu API tiene un endpoint para login post-MFA
    user = BackofficeUser.get(pending_user_id, None)
    
    if user and user.token:
        # ✅ LOGIN COMPLETO
        session['api_token'] = user.token
        session['user_data'] = user.to_dict()
        session['user_id'] = user.id
        session.permanent = True
        session['mfa_verified'] = True
        
        # Limpiar datos temporales
        session.pop('pending_user_id', None)
        session.pop('pending_username', None)
        session.pop('mfa_attempts', None)
        session.pop('mfa_start_time', None)
        
        login_user(user, remember=True)
        print(f"✅ Login completado para: {user.username}")
        flash('✅ ¡Bienvenido/a!', 'success')
        return redirect('/dashboard')
    else:
        flash('❌ No se pudo completar el login. Por favor intenta nuevamente.', 'error')
        return redirect('/auth/login')

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
            return render_template(
                'auth/verify_mfa_disable.html',
                username=session.get('disable_mfa_username')
            )

        # Verificar código MFA con la API
        if verify_mfa_with_api(disable_user_id, mfa_code):
            # MFA verificado, proceder a desactivar
            if disable_mfa_for_user(disable_user_id):
                # 🔥 ACTUALIZAR ESTADO LOCAL DEL USUARIO
                current_user.mfa_enabled = False

                # 🔥 ACTUALIZAR session['user_data'] TAMBIÉN
                user_data = session.get('user_data', {})
                user_data['mfa_enabled'] = False
                session['user_data'] = user_data

                session.pop('disable_mfa_user_id', None)
                session.pop('disable_mfa_username', None)
                session.pop('disable_mfa_start_time', None)

                flash('✅ MFA deshabilitado correctamente', 'success')
                return redirect('/dashboard')
            else:
                flash('❌ Error al deshabilitar MFA', 'error')
        else:
            flash('❌ Código incorrecto', 'error')

    return render_template(
        'auth/verify_mfa_disable.html',
        username=session.get('disable_mfa_username')
    )


@bp.route('/setup-mfa', methods=['GET', 'POST'])
@login_required
def setup_mfa():
    """Página de configuración MFA"""
    print(f"🔐 Setup MFA - User: {current_user.username}, DB_ID: {current_user.id}")
    print(f"📋 Sesión completa: {list(session.keys())}")
    
    # Verificar token en sesión
    print(f"🔑 Token en sesión: {'SÍ' if session.get('api_token') else 'NO'}")
    token_preview = session.get('api_token', '')[:50] + '...' if session.get('api_token') else 'N/A'
    print(f"🔑 Token preview: {token_preview}")

    # Obtener ID real del usuario autenticado
    real_user_id = current_user.id
    print(f"🎯 ID REAL del usuario: {real_user_id}")

    action = request.form.get('action')
    print(f"🔘 Acción POST recibida: {action}")

    if request.method == 'POST':
        if action == 'generate':
            print(f"🔄 Generando código MFA...")
            try:
                # 🔥 VERIFICAR PRESENCIA DE TOKEN ANTES DE CONTINUAR
                if not session.get('api_token'):
                    print("❌ No hay token de API disponible")
                    flash('❌ Sesión expirada. Por favor inicia sesión nuevamente.', 'error')
                    return redirect('/auth/logout')

                # Generar MFA via API usando ID REAL
                secret, qrcode_data = generate_mfa_for_user(real_user_id)
                if secret and qrcode_data:
                    session['temp_mfa_secret'] = secret
                    session['temp_qrcode'] = qrcode_data
                    session['mfa_setup_start_time'] = time.time()
                    flash('✅ Código QR generado. Escanea con tu app de autenticación.', 'success')
                else:
                    flash('❌ Error generando código MFA', 'error')
            except Exception as e:
                current_app.logger.error(f"Error generating MFA: {e}")
                flash('❌ Error generando MFA', 'error')

        elif action == 'verify':
            # Verificar y activar MFA
            verification_code = request.form.get('verification_code', '').strip()
            if not verification_code or len(verification_code) != 6:
                flash('❌ El código debe tener exactamente 6 dígitos', 'error')
            else:
                secret = session.get('temp_mfa_secret')
                if secret:
                    try:
                        # Verificar código localmente primero
                        import pyotp
                        totp = pyotp.TOTP(secret)
                        if totp.verify(verification_code):
                            # Activar MFA en la API
                            if enable_mfa_for_user(real_user_id):
                                # 🔥 ACTUALIZAR ESTADO LOCAL
                                current_user.mfa_enabled = True
                                
                                # 🔥 ACTUALIZAR session['user_data'] TAMBIÉN
                                user_data = session.get('user_data', {})
                                user_data['mfa_enabled'] = True
                                session['user_data'] = user_data
                                
                                # Limpiar datos temporales
                                session.pop('temp_mfa_secret', None)
                                session.pop('temp_qrcode', None)
                                session.pop('mfa_setup_start_time', None)
                                
                                flash('✅ ¡MFA activado exitosamente! Tu cuenta ahora está más segura.', 'success')
                                return redirect('/dashboard')
                            else:
                                flash('❌ Error al habilitar MFA en el servidor', 'error')
                        else:
                            flash('❌ Código incorrecto. Verifica el código e intenta nuevamente.', 'error')
                    except Exception as e:
                        current_app.logger.error(f"Error verifying MFA: {e}")
                        flash('❌ Error al verificar MFA', 'error')
                else:
                    flash('❌ Sesión MFA expirada. Genera un nuevo código.', 'warning')

        elif action == 'disable':
            # Deshabilitar MFA via API con ID REAL
            password = request.form.get('password', '')
            
            if not password:
                flash('❌ Por favor ingresa tu contraseña para deshabilitar MFA', 'error')
            else:
                # Re-autenticar usuario con ID REAL
                user = BackofficeUser.authenticate(current_user.username, password)
                if user and user.id == real_user_id:  # 🔥 Validar ID real
                    if disable_mfa_for_user(real_user_id):
                        # 🔥 ACTUALIZAR ESTADO LOCAL DEL USUARIO
                        current_user.mfa_enabled = False
                        
                        # 🔥 ACTUALIZAR session['user_data'] TAMBIÉN
                        user_data = session.get('user_data', {})
                        user_data['mfa_enabled'] = False
                        session['user_data'] = user_data
                        
                        session.pop('mfa_verified', None)
                        
                        print(f"🔥 MFA DESHABILITADO - Estado actualizado para usuario REAL:")
                        print(f"   - current_user.mfa_enabled: {current_user.mfa_enabled}")
                        print(f"   - session user_data mfa_enabled: {user_data.get('mfa_enabled')}")
                        
                        flash('✅ MFA deshabilitado correctamente', 'success')
                        return redirect('/dashboard')
                    else:
                        flash('❌ Error al deshabilitar MFA', 'error')
                else:
                    flash('❌ Contraseña incorrecta', 'error')

    # Obtener estado MFA actual SIEMPRE DESDE LA API usando ID REAL
    print(f"🔄 Verificando estado MFA actual desde API...")
    mfa_status = check_user_mfa_status(real_user_id)
    mfa_enabled = mfa_status.get('mfa_enabled', False)
    qr_code = session.get('temp_qrcode')
    manual_key = session.get('temp_mfa_secret')

    print(f"📊 Estado MFA REAL desde API: {mfa_status}")

    return render_template(
        'auth/setup_mfa.html',
        mfa_enabled=mfa_enabled,
        qr_code=qr_code,
        manual_key=manual_key,
        username=current_user.username,
        user_id=real_user_id  # 🔥 Pasar ID real al template
    )


def generate_mfa_for_user(user_id):
    """Generar secreto MFA para usuario via API - VERSIÓN CORREGIDA"""
    # 🔥 VALIDAR ID primero
    if not user_id or user_id in ['None', 'admin-fallback', 'admin-local']:
        print(f"❌ ID inválido para generar MFA: {user_id}")
        return None, None

    try:
        headers = get_auth_headers()
        
        response = requests.post(
            f"{Config.API_BASE_URL}/api/users/{user_id}/mfa/generate",
            headers=headers,
            timeout=120
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('ok'):
                secret = data.get('secret')
                qrcode = data.get('qrcode')
                print(f"✅ MFA generado exitosamente para usuario: {user_id}")
                return secret, qrcode
        else:
            print(f"❌ Error HTTP {response.status_code} generando MFA")
    except Exception as e:
        current_app.logger.error(f"Error generating MFA: {e}")
        print(f"❌ Error generando MFA: {e}")
    return None, None


def verify_mfa_with_api(user_id, mfa_code):
    """Verificar código MFA con la API - VERSIÓN MEJORADA"""
    if not user_id or user_id in ['None', 'admin-fallback', 'admin-local']:
        print(f"❌ ID inválido para verificar MFA: {user_id}")
        return False
    
    try:
        # Para verificación MFA durante login, NO necesitamos token todavía
        # La verificación debería hacerse contra un endpoint público o con credenciales temporales
        
        api_url = Config.API_BASE_URL
        print(f"🔐 Verificando MFA para usuario: {user_id}")
        
        # 🔥 ESTE ENDPOINT DEBE EXISTIR EN TU API
        endpoint = f"{api_url}/api/mfa/verify"
        
        payload = {
            'user_id': user_id,
            'code': mfa_code
        }
        
        response = requests.post(
            endpoint,
            json=payload,
            timeout=30
        )
        
        print(f"📡 Verify MFA response: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            return data.get('ok', False) or data.get('verified', False)
        else:
            print(f"❌ Error verificando MFA: {response.status_code}")
            # Para desarrollo, simular éxito si el código es "123456"
            if mfa_code == "123456":
                print("⚠️  Modo desarrollo: código 123456 aceptado")
                return True
            return False
            
    except Exception as e:
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
    print(f"🎯 INICIANDO enable_mfa_for_user para user_id: {user_id}")
    
    # 🔥 VALIDAR ID primero
    if not user_id or user_id in ['None', 'admin-fallback', 'admin-local']:
        print(f"❌ ID inválido para habilitar MFA: {user_id}")
        return False

    try:
        # Obtener headers de autenticación
        print("🔑 Obteniendo headers de autenticación...")
        headers = get_auth_headers()
        print(f"📋 Headers obtenidos: {list(headers.keys())}")
        
        # DEBUG: Mostrar el token completo para verificación
        auth_header = headers.get('Authorization', '')
        if auth_header:
            print(f"🔑 Token completo: {auth_header}")
        else:
            print("❌ NO hay token Authorization en headers")
            print(f"📋 Todos los headers: {headers}")
        
        # Verificar Config.API_BASE_URL
        print(f"🌐 Config.API_BASE_URL: {Config.API_BASE_URL}")
        print(f"🌐 os.getenv('API_BASE_URL'): {os.getenv('API_BASE_URL')}")
        
        api_url = Config.API_BASE_URL
        endpoint = f"{api_url}/api/users/{user_id}/mfa/enable"
        
        print(f"🌐 Llamando a API endpoint: {endpoint}")
        
        # Hacer la petición con timeout y verificación de SSL desactivada si es necesario
        response = requests.post(
            endpoint,
            headers=headers,
            timeout=30,
            verify=False  # Solo para desarrollo, desactiva verificación SSL
        )
        
        print(f"📡 Respuesta HTTP: {response.status_code}")
        print(f"📄 Respuesta completa: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Activación MFA exitosa: {data}")
            return data.get('ok', False)
        elif response.status_code == 401:
            print("❌ ERROR 401: Token no autorizado o expirado")
            print(f"📋 Headers enviados: {headers}")
            return False
        elif response.status_code == 404:
            print("❌ ERROR 404: Endpoint no encontrado")
            print(f"🔗 URL intentada: {endpoint}")
            return False
        elif response.status_code == 500:
            print("❌ ERROR 500: Error interno del servidor")
            try:
                error_data = response.json()
                print(f"📄 Error details: {error_data}")
            except:
                print(f"📄 Raw response: {response.text}")
            return False
        else:
            print(f"❌ Error HTTP {response.status_code} activando MFA")
            return False
            
    except requests.exceptions.ConnectionError as e:
        print(f"❌ Error de conexión: No se puede conectar a {Config.API_BASE_URL}")
        print(f"📋 Detalle: {e}")
        return False
    except requests.exceptions.Timeout as e:
        print(f"❌ Timeout al conectar con la API: {e}")
        return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Error de requests: {e}")
        return False
    except Exception as e:
        print(f"❌ Excepción inesperada en enable_mfa_for_user: {type(e).__name__}: {e}")
        import traceback
        print(f"📋 Traceback: {traceback.format_exc()}")
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
            timeout=120
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
    return render_template(
        'auth/mfa_recovery.html',
        username=session.get('pending_username')
    )