"""
Configuración robusta con validaciones y fallbacks
"""
import os
import sys
from dotenv import load_dotenv
from pathlib import Path

# 🔥 Cargar variables de entorno con múltiples ubicaciones
env_locations = [
    Path(__file__).parent / ".env",
    Path(__file__).parent.parent / ".env",
    Path.home() / ".firefighter-backoffice.env",
    "/etc/firefighter/backoffice.env",
]

env_loaded = False
for env_path in env_locations:
    try:
        if env_path.exists():  # <-- AHORA ES Path object, funciona correctamente
            load_dotenv(env_path)
            print(f"✅ Cargado .env desde: {env_path}")
            env_loaded = True
            break
    except Exception as e:
        print(f"⚠️  Error cargando {env_path}: {e}")

if not env_loaded:
    print("⚠️  No se encontró archivo .env, usando variables de entorno del sistema")

class Config:
    """
    Configuración principal con validaciones robustas
    """
    
    # =========================================================
    # 🌍 ENTORNO Y MODO
    # =========================================================
    ENVIRONMENT = os.getenv("ENVIRONMENT", "development").lower()
    DOCKER = os.getenv("DOCKER_ENV", "true").lower() in ("true", "1", "t", "yes")
    DEBUG = os.getenv("DEBUG", "true").lower() in ("true", "1", "t", "yes")
    
    # Validar entorno
    if ENVIRONMENT not in ["development", "testing", "staging", "production"]:
        print(f"⚠️  Entorno inválido: {ENVIRONMENT}, usando 'production'")
        ENVIRONMENT = "production"
    
    # =========================================================
    # 🔐 SEGURIDAD - CLAVES CRÍTICAS
    # =========================================================
    # Secret Key para Flask (sesiones, CSRF, etc.)
    SECRET_KEY = os.getenv(
        "BACKOFFICE_SECRET_KEY",
        os.getenv("SECRET_KEY", "firefighter-super-secret-key-2024-backoffice")
    )
    
    # JWT Secret para comunicación con Backend API
    JWT_SECRET = os.getenv(
        "JWT_SECRET",
        os.getenv("BACKEND_JWT_SECRET", "firefighter-jwt-secret-2024")
    )
    
    JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
    JWT_TOKEN_LOCATION = ["headers", "cookies"]
    JWT_COOKIE_SECURE = False  # Cambiar a True en producción con HTTPS
    
    # =========================================================
    # 🍪 CONFIGURACIÓN DE COOKIES Y SESIONES
    # =========================================================
    SESSION_COOKIE_NAME = os.getenv("SESSION_COOKIE_NAME", "backoffice_session")
    SESSION_COOKIE_PATH = os.getenv("SESSION_COOKIE_PATH", "/")
    SESSION_COOKIE_HTTPONLY = os.getenv("SESSION_COOKIE_HTTPONLY", "true").lower() in ("true", "1", "t")
    SESSION_COOKIE_SECURE = os.getenv("SESSION_COOKIE_SECURE", "false").lower() in ("true", "1", "t")
    SESSION_COOKIE_SAMESITE = os.getenv("SESSION_COOKIE_SAMESITE", "Lax")
    SESSION_COOKIE_DOMAIN = os.getenv("SESSION_COOKIE_DOMAIN", None)
    SESSION_COOKIE_MAX_AGE = int(os.getenv("SESSION_COOKIE_MAX_AGE", "28800"))  # 8 horas
    
    PERMANENT_SESSION_LIFETIME = SESSION_COOKIE_MAX_AGE
    SESSION_PROTECTION = os.getenv("SESSION_PROTECTION", "basic")
    SESSION_REFRESH_EACH_REQUEST = os.getenv("SESSION_REFRESH_EACH_REQUEST", "true").lower() in ("true", "1", "t")
    
    # =========================================================
    # 👤 ADMINISTRACIÓN Y AUTENTICACIÓN
    # =========================================================
    ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
    ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", os.getenv("ADMIN_PASSWORD_HASH", "admin123"))
    
    # MFA Configuration
    MFA_ISSUER = os.getenv("MFA_ISSUER", "FirefighterAI-BackOffice")
    MFA_VALID_WINDOW = int(os.getenv("MFA_VALID_WINDOW", "1"))
    
    # =========================================================
    # 🌐 API CONFIGURATION - URLs CRÍTICAS
    # =========================================================
    # URL para comunicación interna (Docker network)
    API_INTERNAL_URL = os.getenv(
    "API_INTERNAL_URL",
    "http://backend:5000" if DOCKER else "http://localhost:5000"
    )
    
    # URL para el navegador (pública)
    PUBLIC_HOST = os.getenv("PUBLIC_HOST", "localhost")
    API_PUBLIC_URL = os.getenv(
        "API_PUBLIC_URL",
        f"http://{PUBLIC_HOST}:5000"
    )
    
    # URL base usada por la aplicación (puede ser dinámica)
    API_BASE_URL = os.getenv("API_BASE_URL", API_INTERNAL_URL)
    
    # Timeout para requests a la API
    API_TIMEOUT = int(os.getenv("API_TIMEOUT", "30"))
    API_RETRY_ATTEMPTS = int(os.getenv("API_RETRY_ATTEMPTS", "3"))
    
    # =========================================================
    # 🔴 REDIS - SESSIONS Y CACHE
    # =========================================================
    REDIS_HOST = os.getenv("REDIS_HOST", "redis" if DOCKER else "localhost")
    REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_DB = int(os.getenv("REDIS_DB", "0"))
    REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", None)
    REDIS_SOCKET_TIMEOUT = float(os.getenv("REDIS_SOCKET_TIMEOUT", "5.0"))
    
    USE_REDIS_SESSIONS = os.getenv("USE_REDIS_SESSIONS", "true").lower() in ("true", "1", "t")
    
    # =========================================================
    # 📊 LOGGING Y MONITORING
    # =========================================================
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
    
    # Validar log level
    VALID_LOG_LEVELS = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    if LOG_LEVEL not in VALID_LOG_LEVELS:
        print(f"⚠️  Nivel de log inválido: {LOG_LEVEL}, usando INFO")
        LOG_LEVEL = "INFO"
    
    LOG_FORMAT = os.getenv("LOG_FORMAT", "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    LOG_DATE_FORMAT = os.getenv("LOG_DATE_FORMAT", "%Y-%m-%d %H:%M:%S")
    
    # Sentry para producción
    SENTRY_DSN = os.getenv("SENTRY_DSN", None)
    
    # =========================================================
    # 🔧 OTRAS CONFIGURACIONES
    # =========================================================
    # CORS
    ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*").split(",")
    
    # Rate limiting
    RATE_LIMIT_ENABLED = os.getenv("RATE_LIMIT_ENABLED", "true").lower() in ("true", "1", "t")
    RATE_LIMIT_DEFAULT = os.getenv("RATE_LIMIT_DEFAULT", "200 per hour")
    
    # Uploads
    MAX_CONTENT_LENGTH = int(os.getenv("MAX_CONTENT_LENGTH", "16777216"))  # 16MB
    UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", "/tmp/uploads")
    
    # Database (si se usa localmente)
    DATABASE_URL = os.getenv("DATABASE_URL", None)
    
    # =========================================================
    # ✅ VALIDACIÓN DE CONFIGURACIÓN
    # =========================================================
    @classmethod
    def validate(cls):
        """Validar configuración completa"""
        errors = []
        warnings = []
        
        print("🔍 Validando configuración...")
        
        # Validaciones CRÍTICAS (bloqueantes)
        if not cls.SECRET_KEY or cls.SECRET_KEY == "firefighter-super-secret-key-2024-backoffice":
            errors.append("❌ SECRET_KEY: Usando valor por defecto. Configurar BACKOFFICE_SECRET_KEY")
        
        if not cls.JWT_SECRET or cls.JWT_SECRET == "firefighter-jwt-secret-2024":
            errors.append("❌ JWT_SECRET: Usando valor por defecto. Configurar JWT_SECRET")
        
        if not cls.API_INTERNAL_URL:
            errors.append("❌ API_INTERNAL_URL: No configurada")
        
        # Validaciones de PRODUCCIÓN
        if cls.ENVIRONMENT == "production":
            if cls.DEBUG:
                errors.append("❌ DEBUG: No debe estar activado en producción")
            
            if not cls.SESSION_COOKIE_SECURE:
                warnings.append("⚠️  SESSION_COOKIE_SECURE: Debería ser True en producción con HTTPS")
            
            if cls.ADMIN_PASSWORD == "admin123":
                warnings.append("⚠️  ADMIN_PASSWORD: Usando contraseña por defecto en producción")
            
            if not cls.SENTRY_DSN:
                warnings.append("⚠️  SENTRY_DSN: No configurado. Recomendado para producción")
        
        # Validaciones de REDIS
        if cls.USE_REDIS_SESSIONS:
            if cls.REDIS_HOST in ["localhost", "127.0.0.1"] and cls.DOCKER:
                warnings.append("⚠️  REDIS_HOST: Usando localhost en Docker. Debería ser 'redis'")
        
        # Reportar
        if errors:
            print("\n🚨 ERRORES CRÍTICOS:")
            for error in errors:
                print(f"   {error}")
        
        if warnings:
            print("\n⚠️  ADVERTENCIAS:")
            for warning in warnings:
                print(f"   {warning}")
        
        if not errors and not warnings:
            print("✅ Configuración validada correctamente")
        elif errors:
            print(f"\n💀 {len(errors)} error(es) crítico(s) encontrado(s)")
        
        return len(errors) == 0
    
    # =========================================================
    # 🪵 LOGGING DE CONFIGURACIÓN
    # =========================================================
    @classmethod
    def log_config(cls):
        """Mostrar configuración actual (segura)"""
        import socket
        
        print("=" * 70)
        print("🚀 FIREFIGHTER BACKOFFICE - CONFIGURACIÓN")
        print("=" * 70)
        
        # Información básica
        print(f"🌍 Environment:     {cls.ENVIRONMENT}")
        print(f"🐋 Docker Mode:     {cls.DOCKER}")
        print(f"🐛 Debug:           {cls.DEBUG}")
        print(f"📊 Log Level:       {cls.LOG_LEVEL}")
        
        # URLs
        print(f"🌐 API Internal:    {cls.API_INTERNAL_URL}")
        print(f"🌐 API Public:      {cls.API_PUBLIC_URL}")
        
        # Seguridad (valores ocultos)
        print(f"🔐 Secret Key:      {'***' + cls.SECRET_KEY[-4:] if cls.SECRET_KEY else '❌ No configurado'}")
        print(f"🔑 JWT Secret:      {'***' + cls.JWT_SECRET[-4:] if cls.JWT_SECRET else '❌ No configurado'}")
        
        # Cookies
        print(f"🍪 Cookie Name:     {cls.SESSION_COOKIE_NAME}")
        print(f"🔒 Secure Cookies:  {cls.SESSION_COOKIE_SECURE}")
        print(f"🔄 Refresh Session: {cls.SESSION_REFRESH_EACH_REQUEST}")
        
        # Redis
        print(f"📡 Redis Sessions:  {cls.USE_REDIS_SESSIONS}")
        if cls.USE_REDIS_SESSIONS:
            print(f"   ├─ Host:        {cls.REDIS_HOST}")
            print(f"   ├─ Port:        {cls.REDIS_PORT}")
            print(f"   └─ DB:          {cls.REDIS_DB}")
        
        # Admin
        admin_pass_length = len(cls.ADMIN_PASSWORD) if cls.ADMIN_PASSWORD else 0
        print(f"👤 Admin User:      {cls.ADMIN_USERNAME}")
        print(f"🔑 Admin Pass:      {'*' * min(8, admin_pass_length)}... ({admin_pass_length} chars)")
        
        # Sistema
        try:
            hostname = socket.gethostname()
            ip = socket.gethostbyname(hostname)
            print(f"🖥️  Hostname:        {hostname}")
            print(f"📍 IP Address:      {ip}")
        except:
            pass
        
        print("=" * 70)
        
        # Validar
        is_valid = cls.validate()
        print("=" * 70)
        
        return is_valid


# Validar al importar
Config.log_config()

# En producción, solo warning, no salir
if Config.ENVIRONMENT == "production" and not Config.validate():
    print("⚠️  ADVERTENCIAS EN PRODUCCIÓN - Continuando con precaución")
    # No sys.exit() - Continuar con advertencias