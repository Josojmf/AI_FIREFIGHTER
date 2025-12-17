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

            # ✅ CRÍTICO: GUARDAR DATOS EN SESIÓN ANTES DE login_user
            session['api_token'] = user.token
            session['user_data'] = user.to_dict()
            session['user_id'] = user.id
            session.permanent = True

            print("💾 Datos guardados en sesión:")
            print(f" - user_id: {session.get('user_id')}")
            print(f" - token: {session.get('api_token')[:20] if session.get('api_token') else 'NO'}")
            print(f" - user_data: {'✅' if session.get('user_data') else '❌'}")

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
            return render_template(
                'auth/verify_mfa.html',
                username=session.get('pending_username')
            )

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

    return render_template(
        'auth/verify_mfa.html',
        username=session.get('pending_username'),
        attempts=session.get('mfa_attempts', 0)
    )


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
                user_data['mfa_secret'] = ''
                session['user_data'] = user_data

                # Limpiar sesión temporal
                session.pop('disable_mfa_user_id', None)
                session.pop('disable_mfa_username', None)
                session.pop('disable_mfa_start_time', None)
                session.pop('mfa_verified', None)

                print("🔥 MFA DESHABILITADO - Estado actualizado para usuario:")
                print(f" - current_user.mfa_enabled: {current_user.mfa_enabled}")
                print(f" - session user_data mfa_enabled: {user_data.get('mfa_enabled')}")

                flash('✅ MFA deshabilitado correctamente. Tu cuenta ahora es menos segura.', 'success')
                return redirect('/dashboard')
            else:
                flash('❌ Error al deshabilitar MFA en el servidor', 'error')
        else:
            flash('❌ Código MFA incorrecto', 'error')

    return render_template(
        'auth/verify_mfa_disable.html',
        username=session.get('disable_mfa_username')
    )


@bp.route('/setup-mfa', methods=['GET', 'POST'])
@login_required
def setup_mfa():
    real_user_id = session.get("user_data", {}).get("id")
    print(f"🔐 Setup MFA - User: {current_user.username}, DB_ID: {real_user_id}")
    print(f"📋 Sesión completa: {list(session.keys())}")
    print(f"🔑 Token en sesión: {'SÍ' if session.get('api_token') else 'NO'}")
    print(f"🔑 Token preview: {session.get('api_token')[:30] if session.get('api_token') else 'N/A'}...")
    
    if not real_user_id:
        flash("❌ Error crítico: ID real de usuario no disponible", "error")
        return redirect("/dashboard")

    if request.method == "POST":
        action = request.form.get("action")
        print(f"🔘 Acción POST recibida: {action}")

        if action == "generate":
            print("🔄 Generando código MFA...")
            mfa_data = generate_mfa_secret_api(real_user_id)
            if mfa_data:
                session["mfa_qrcode"] = mfa_data["qrcode"]
                session["manual_entry_key"] = mfa_data["manual_entry_key"]
                session["mfa_secret_temp"] = mfa_data["secret"]
                flash("📱 Código QR generado", "success")
            else:
                flash("❌ Error al generar MFA", "error")

        elif action == "enable":
            mfa_code = request.form.get("mfa_code", "").strip()
            print(f"🔢 Código MFA recibido para activación: {mfa_code}")
            
            # 🔥 CRÍTICO: Verificar Y activar MFA
            print(f"🔄 Verificando código MFA para usuario {real_user_id}...")
            
            # DEBUG: Verificar qué hay en la sesión antes de verificar
            print(f"📋 Estado sesión antes de verificar:")
            print(f"  - api_token: {'SÍ' if session.get('api_token') else 'NO'}")
            print(f"  - user_data: {session.get('user_data', {})}")
            
            if verify_mfa_setup_with_api(real_user_id, mfa_code):
                print("✅ Código MFA verificado correctamente")
                print(f"🚀 Llamando a enable_mfa_for_user({real_user_id})...")
                
                # 🔥 DEBUG: Verificar Config.API_BASE_URL
                print(f"🌐 Config.API_BASE_URL: {Config.API_BASE_URL}")
                
                # 🔥 ACTIVAR MFA en la API
                success = enable_mfa_for_user(real_user_id)
                print(f"📡 Resultado de enable_mfa_for_user: {success}")
                
                if success:
                    print("✅ MFA activado en la API - actualizando estado local")
                    
                    # 🔥 Actualizar estado local
                    current_user.mfa_enabled = True
                    if session.get("user_data"):
                        session["user_data"]["mfa_enabled"] = True
                    
                    # 🔥 Limpiar datos temporales
                    session.pop("mfa_qrcode", None)
                    session.pop("manual_entry_key", None)
                    session.pop("mfa_secret_temp", None)
                    
                    print("✅ Todo actualizado - redirigiendo a dashboard")
                    flash("✅ MFA habilitado correctamente", "success")
                    return redirect("/dashboard")
                else:
                    print("❌ Falló activación MFA en la API")
                    flash("❌ Error al habilitar MFA en el servidor", "error")
            else:
                print("❌ Código MFA incorrecto o verificación falló")
                flash("❌ Código MFA incorrecto", "error")
        else:
            print(f"⚠️  Acción desconocida: {action}")

    # 🔥 IMPORTANTE: Siempre verificar el estado REAL desde la API
    print("🔄 Verificando estado MFA actual desde API...")
    mfa_status = check_user_mfa_status(real_user_id)
    print(f"📊 Estado MFA REAL desde API: {mfa_status}")

    # 🔥 Si hay QR en sesión pero MFA ya está habilitado, limpiar
    if mfa_status.get("mfa_enabled") and session.get("mfa_qrcode"):
        session.pop("mfa_qrcode", None)
        session.pop("manual_entry_key", None)
        session.pop("mfa_secret_temp", None)

    return render_template(
        "auth/setup_mfa.html",
        mfa_enabled=mfa_status.get("mfa_enabled", False),
        qrcode=session.get("mfa_qrcode"),
        manual_entry_key=session.get("manual_entry_key"),
        user_email=current_user.email or current_user.username,
        real_user_id=real_user_id,
    )
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
            timeout=120
        )

        print(f"📡 Respuesta API: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            if data.get('ok'):
                print("✅ MFA secret generado exitosamente para usuario REAL")

                secret = data.get('secret')
                qrcode = data.get('qrcode')              # 👈 NOMBRE QUE DEVUELVE LA API
                manual_entry_key = data.get('manual_entry_key')

                # 👇 GUARDAR EN SESIÓN PARA LA PLANTILLA
                session['mfa_qrcode'] = qrcode
                session['manual_entry_key'] = manual_entry_key

                return {
                    'secret': secret,
                    'qrcode': qrcode,
                    'manual_entry_key': manual_entry_key
                }
            else:
                print(f"❌ API rechazó generación MFA: {data.get('detail', 'Sin detalle')}")
                return None
        else:
            print(f"❌ Error HTTP en API: {response.status_code}")
            try:
                error_data = response.json()
                print(f"  Detalle: {error_data.get('detail', 'Sin detalle')}")
            except Exception:
                print(f"  Respuesta: {response.text[:200]}")
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
        print(f"🔢 Código a verificar: {mfa_code}")
        print(f"🌐 API URL: {api_url}/api/users/{user_id}/mfa/verify-setup")

        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }

        payload = {'code': mfa_code}
        print(f"📦 Payload enviado: {payload}")
        
        response = requests.post(
            f"{api_url}/api/users/{user_id}/mfa/verify-setup",
            headers=headers,
            json=payload,
            timeout=120
        )

        print(f"📡 Verify setup response: {response.status_code}")
        print(f"📄 Respuesta completa: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"📊 Datos parseados: {data}")
            print(f"🔍 Valor de 'ok': {data.get('ok')}")
            print(f"🔍 Tipo de 'ok': {type(data.get('ok'))}")
            return data.get('ok', False)
        else:
            print(f"❌ Error HTTP verificando setup MFA: {response.status_code}")
            print(f"📄 Error response: {response.text}")
            return False

    except Exception as e:
        current_app.logger.error(f"Error verifying MFA setup: {e}")
        print(f"❌ Excepción verificando setup MFA: {e}")
        import traceback
        print(f"📋 Traceback: {traceback.format_exc()}")
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
            timeout=120
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
