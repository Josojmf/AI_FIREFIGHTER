from flask_login import UserMixin
from config import Config
import requests
import jwt
from datetime import datetime


class BackofficeUser(UserMixin):
    def __init__(self, id, username, email, role, mfa_enabled=False, token=None):
        # 🔴 ID SIEMPRE STRING para Flask-Login
        self.id = str(id)
        self.username = username
        self.email = email
        self.role = role
        self.mfa_enabled = mfa_enabled
        self.token = token

    def get_id(self):
        # 🔴 Flask-Login guarda esto en la cookie
        return str(self.id)

    @staticmethod
    def authenticate(username, password, mfa_code=None):
        """Autenticar usuario, con MFA opcional para casos especiales"""
        try:
            print(f"🔍 Intentando login en: {Config.API_BASE_URL}/api/auth/login")
            print(f"🔍 MFA code proporcionado: {'Sí' if mfa_code else 'No'}")

            # Construir payload base
            payload = {"username": username, "password": password}

            # Solo incluir MFA si se proporciona
            if mfa_code:
                payload["mfa_token"] = mfa_code
                print("🔐 Enviando código MFA con login")
            else:
                print("🔓 Login solo con usuario/contraseña (sin MFA)")

            response = requests.post(
            f"{Config.API_BASE_URL}/api/auth/login",
            json=payload,
            timeout=10
          )

            print(f"📡 Respuesta API: {response.status_code}")

            if response.status_code == 200:
                data = response.json()
                print(f"📋 Datos recibidos: {list(data.keys())}")
                
                # 🔥 VERIFICAR SI LA API REQUIERE MFA
                if data.get("requires_mfa") and not mfa_code:
                    print(f"📱 MFA requerido para: {username}")
                    # Retornar objeto especial indicando que se requiere MFA
                    # pero SIN token porque aún no está completamente autenticado
                    user_data = data.get("user", {})
                    if not user_data and "username" in data:
                        user_data = data
                    
                    return BackofficeUser(
                        id=data.get("user_id") or username,  # ID temporal
                        username=user_data.get("username") or username,
                        email=user_data.get("email") or "",
                        role=user_data.get("role", "user"),
                        mfa_enabled=True,  # 🔥 Marca que requiere MFA
                        token=None  # 🔥 SIN TOKEN hasta completar MFA
                    )
                
                # ✅ LOGIN COMPLETO (con token)
                if (data.get("ok") and not data.get("requires_mfa")) or "access_token" in data or "token" in data:
                    # Intentar diferentes estructuras de respuesta
                    user_data = data.get("user", {})
                    if not user_data and "username" in data:
                        user_data = data
                    
                    access_token = data.get("access_token") or data.get("token")
                    
                    if not access_token:
                        print(f"❌ Login sin token recibido")
                        return None
                    
                    print(f"✅ Login exitoso para {username}")

                    # 🔥 Extraer user_id REAL del JWT
                    user_id = user_data.get("id")
                    if not user_id and access_token:
                        try:
                            decoded_token = jwt.decode(access_token, options={"verify_signature": False})
                            user_id = decoded_token.get("user_id") or decoded_token.get("username")
                            print(f"🎯 User ID extraído del JWT: {user_id}")
                        except Exception as e:
                            print(f"⚠️ No se pudo decodificar JWT: {e}")
                            user_id = username

                    # Si aún no hay ID, usar username
                    if not user_id:
                        user_id = username

                    return BackofficeUser(
                        id=str(user_id),
                        username=user_data.get("username") or username,
                        email=user_data.get("email") or "",
                        role=user_data.get("role", "user"),
                        mfa_enabled=user_data.get("mfa_enabled", False),
                        token=access_token
                    )
                else:
                    print(f"❌ Login rechazado: {data.get('detail', 'Sin detalle')}")
                    return None
            elif response.status_code == 401:
                print("❌ Credenciales inválidas")
                return None
            else:
                print(f"❌ Error HTTP: {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"  Detalle: {error_data}")
                except Exception:
                    print(f"  Respuesta: {response.text[:200]}")
                return None

        except Exception as e:
            print(f"❌ Error en authenticate: {e}")
            return None

    @staticmethod
    def get(user_id, token=None):
        """Obtener datos del usuario desde la API usando ID"""
        try:
            # 🔥 VALIDAR ID primero
            if not user_id or user_id in ["None", "admin-fallback", "admin-local"]:
                print(f"❌ ID inválido para get: {user_id}")
                return None

            headers = {}
            if token:
                headers["Authorization"] = f"Bearer {token}"

            print(f"🔍 Obteniendo datos para usuario ID: {user_id}")

            response = requests.get(
                f"{Config.API_BASE_URL}/api/users/{user_id}",
                headers=headers,
                timeout=5
            )

            print(f"📡 Get user response: {response.status_code}")

            if response.status_code == 200:
                user_data = response.json()
                print(f"✅ Datos de usuario obtenidos para ID: {user_id}")

                return BackofficeUser(
                    id=str(user_id),  # ID REAL
                    username=user_data["username"],
                    email=user_data["email"],
                    role=user_data["role"],
                    mfa_enabled=user_data.get("mfa_enabled", False),
                    token=token
                )
            else:
                print(f"❌ Error obteniendo usuario {user_id}: {response.status_code}")
                return None

        except Exception as e:
            print(f"❌ Error en get user: {e}")
            return None

    # [El resto del archivo se mantiene igual...]
    
    @staticmethod
    def get_user_progress(user_id, token=None):
        """Obtener el progreso de aprendizaje del usuario desde la API"""
        try:
            print(f"🔍 Obteniendo progreso para usuario ID: {user_id}")

            headers = {}
            if token:
                headers["Authorization"] = f"Bearer {token}"
                headers["Content-Type"] = "application/json"

            # Primero obtener información básica del usuario
            try:
                user_response = requests.get(
                    f"{Config.API_BASE_URL}/api/users/{user_id}",
                    headers=headers,
                    timeout=5
                )

                if user_response.status_code == 200:
                    user_data = user_response.json()
                    has_leitner_progress = user_data.get("has_leitner_progress", False)

                    if not has_leitner_progress:
                        print(f"ℹ️ Usuario {user_id} no tiene progreso Leitner registrado")
                        return {
                            "ok": False,
                            "message": "Usuario sin progreso registrado",
                            "progress": {},
                            "stats": {
                                "total_cards": 0,
                                "reviewed_cards": 0,
                                "mastered_cards": 0,
                                "review_percentage": 0
                            }
                        }
                else:
                    print(f"⚠️ No se pudo obtener datos del usuario: {user_response.status_code}")
            except Exception as e:
                print(f"⚠️ Error obteniendo datos usuario: {e}")

            # Intentar varios endpoints posibles de progreso
            endpoints = [
                f"{Config.API_BASE_URL}/api/users/{user_id}/progress",
                f"{Config.API_BASE_URL}/api/users/{user_id}/leitner-progress",
                f"{Config.API_BASE_URL}/api/progress/{user_id}",
                f"{Config.API_BASE_URL}/api/leitner/{user_id}/stats"
            ]

            for endpoint in endpoints:
                try:
                    print(f"🌐 Probando endpoint: {endpoint}")
                    response = requests.get(endpoint, headers=headers, timeout=5)

                    if response.status_code == 200:
                        progress_data = response.json()
                        print(f"✅ Progreso obtenido de {endpoint}")
                        return progress_data
                    elif response.status_code == 404:
                        print(f"ℹ️ Endpoint no encontrado: {endpoint}")
                    else:
                        print(f"⚠️ Error {response.status_code} en {endpoint}")
                except requests.exceptions.RequestException as e:
                    print(f"⚠️ Error de conexión con {endpoint}: {e}")
                    continue

            # Si llegamos aquí, ningún endpoint funcionó
            print("ℹ️ No se encontró endpoint de progreso funcionando")

            # Datos simulados para desarrollo
            return {
                "ok": True,
                "message": "Datos de demostración (endpoint no disponible)",
                "progress": {
                    "boxes": [15, 25, 12, 6, 2],
                    "next_review": "2025-12-05",
                    "streak_days": 3,
                    "last_study": "2025-12-04T14:30:00"
                },
                "stats": {
                    "total_cards": 80,
                    "reviewed_cards": 60,
                    "mastered_cards": 32,
                    "review_percentage": 75.0,
                    "average_score": 82.5
                }
            }

        except Exception as e:
            print(f"❌ Error inesperado obteniendo progreso: {e}")
            return {
                "ok": False,
                "message": f"Error: {str(e)}",
                "progress": {},
                "stats": {
                    "total_cards": 0,
                    "reviewed_cards": 0,
                    "mastered_cards": 0,
                    "review_percentage": 0
                }
            }

    def to_dict(self):
        """Convertir a diccionario para sesión"""
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "role": self.role,
            "mfa_enabled": self.mfa_enabled,
            "token": self.token
        }

    @staticmethod
    def from_dict(data):
        """Crear instancia desde diccionario de sesión"""
        if not data:
            return None

        # 🔥 VALIDAR ID antes de crear usuario
        user_id = data.get("id")
        if not user_id or user_id in ["None", "admin-fallback", "admin-local"]:
            print(f"❌ ID inválido en from_dict: {user_id}")
            return None

        return BackofficeUser(
            id=str(user_id),
            username=data.get("username"),
            email=data.get("email"),
            role=data.get("role"),
            mfa_enabled=data.get("mfa_enabled", False),
            token=data.get("token")
        )

    def __repr__(self):
        return f"<BackofficeUser {self.username}>"