# API/database.py
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo import ASCENDING
from pymongo.errors import ConnectionFailure
from typing import Optional
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

# Configuración de MongoDB
MONGO_USER = os.getenv("MONGO_USER", "joso")
MONGO_PASS = os.getenv("MONGO_PASS", "XyGItdDKpWkfJfjT")
MONGO_CLUSTER = os.getenv("MONGO_CLUSTER", "cluster0.yzzh9ig.mongodb.net")
DB_NAME = os.getenv("DB_NAME", "FIREFIGHTER")
DB_TIMEOUT_MS = 30000

def get_mongo_uri():
    """Construir URI de MongoDB"""
    if MONGO_USER and MONGO_PASS:
        return f"mongodb+srv://{MONGO_USER}:{MONGO_PASS}@{MONGO_CLUSTER}/?retryWrites=true&w=majority&appName=FirefighterAPI"
    return "mongodb://localhost:27017"


class Database:
    """Gestor de conexión MongoDB con Motor (async)"""
    
    client: Optional[AsyncIOMotorClient] = None
    db: Optional[AsyncIOMotorDatabase] = None
    
    # Collections
    users = None
    admin_users = None
    resets = None
    access_tokens = None
    memory_cards = None
    
    @classmethod
    async def connect_db(cls):
        """Conectar a MongoDB con retry logic"""
        try:
            print("📡 Conectando a MongoDB...")
            
            cls.client = AsyncIOMotorClient(
                get_mongo_uri(),
                serverSelectionTimeoutMS=DB_TIMEOUT_MS,
                connectTimeoutMS=20000,
                socketTimeoutMS=20000,
                maxPoolSize=50,
                minPoolSize=10,
                retryWrites=True,
                retryReads=True,
                maxIdleTimeMS=45000,
                waitQueueTimeoutMS=10000
            )
            
            # Test connection
            await cls.client.admin.command('ping')
            
            cls.db = cls.client[DB_NAME]
            
            # Inicializar colecciones
            cls.users = cls.db["users"]
            cls.admin_users = cls.db["Adm_Users"]
            cls.resets = cls.db["password_resets"]
            cls.access_tokens = cls.db["access_tokens"]
            cls.memory_cards = cls.db["memory_cards"]
            
            # Crear índices
            await cls._create_indexes()
            
            print("✅ Conectado a MongoDB Atlas correctamente")
            print(f"📊 Base de datos: {DB_NAME}")
            print(f"🔗 Cluster: {MONGO_CLUSTER}")
            
        except ConnectionFailure as e:
            print(f"❌ Error conectando a MongoDB: {e}")
            print("💡 Verifica tus credenciales en el archivo .env")
            print("💡 Asegúrate de que tu IP esté en la whitelist de MongoDB Atlas")
            raise
    
    @classmethod
    async def _create_indexes(cls):
        """Crear índices de MongoDB"""
        if not cls.db:
            return
        
        try:
            # Índices de usuarios
            await cls.users.create_index([("username", ASCENDING)], unique=True)
            await cls.users.create_index([("email", ASCENDING)], unique=True)
            
            # TTL para tokens de reseteo
            await cls.resets.create_index("expiresAt", expireAfterSeconds=0)
            
            # Índices de access tokens
            await cls.access_tokens.create_index([("token", ASCENDING)], unique=True, name="token_unique_idx")
            await cls.access_tokens.create_index("status")
            
            # Índices de memory cards
            await cls.memory_cards.create_index("category")
            await cls.memory_cards.create_index("difficulty")
            await cls.memory_cards.create_index("created_by")
            
            print("✅ Índices de MongoDB creados")
        except Exception as e:
            print(f"⚠️  Advertencia creando índices: {e}")
    
    @classmethod
    async def close_db(cls):
        """Cerrar conexión a MongoDB"""
        if cls.client:
            cls.client.close()
            print("🔌 Conexión a MongoDB cerrada")
    
    @classmethod
    def get_db(cls) -> AsyncIOMotorDatabase:
        """Obtener instancia de base de datos"""
        if not cls.db:
            raise RuntimeError("Database not initialized. Call connect_db first.")
        return cls.db


# Dependency para FastAPI
async def get_database() -> AsyncIOMotorDatabase:
    """Dependency injection para obtener DB en endpoints"""
    return Database.get_db()