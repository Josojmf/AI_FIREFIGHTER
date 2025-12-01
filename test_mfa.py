# cleanup_mfa.py
from pymongo import MongoClient
from bson import ObjectId

# Conectar a MongoDB
client = MongoClient("mongodb+srv://joso:XyGItdDKpWkfJfjT@cluster0.yzzh9ig.mongodb.net/")
db = client["FIREFIGHTER"]
users = db["users"]

# Limpiar el secreto MFA del usuario admin
result = users.update_one(
    {"_id": "44ef090f-c7b9-401f-9e75-ec24a68e3113"},
    {"$set": {"mfa_secret": "", "mfa_enabled": False}}
)

print(f"✅ Secreto MFA limpiado: {result.modified_count} documentos actualizados")