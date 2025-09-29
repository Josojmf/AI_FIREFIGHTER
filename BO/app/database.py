# app/database.py
from pymongo import MongoClient
from flask import current_app

# Cache de cliente/colección
_mongo_client = None
_final_coll = None

def get_final_collection():
    """Obtiene (y cachea) la colección FIREFIGHTER.Final"""
    global _mongo_client, _final_coll
    if _final_coll is not None:
        return _final_coll

    cfg = current_app.config
    mongo_uri = cfg.get('MONGO_URI')
    db_name = cfg.get('DB_NAME', 'FIREFIGHTER')

    if not mongo_uri:
        user = cfg.get('MONGO_USER', '')
        pwd = cfg.get('MONGO_PASS', '')
        cluster = cfg.get('MONGO_CLUSTER', '')
        if not cluster:
            raise RuntimeError("MongoDB mal configurado: MONGO_CLUSTER vacío")
        mongo_uri = f"mongodb+srv://{user}:{pwd}@{cluster}/{db_name}?retryWrites=true&w=majority"

    try:
        host_part = mongo_uri.split('@', 1)[1].split('/', 1)[0] if '@' in mongo_uri else mongo_uri
        current_app.logger.info(f"[Mongo] Conectando a host: {host_part}")
    except Exception:
        pass

    _mongo_client = MongoClient(mongo_uri)
    _final_coll = _mongo_client[db_name]['Adm_Users']
    return _final_coll

def get_database():
    """Obtiene la instancia de la base de datos"""
    return get_final_collection().database

def get_client():
    """Obtiene el cliente MongoDB"""
    if _mongo_client is None:
        get_final_collection()  # Esto inicializará el cliente
    return _mongo_client