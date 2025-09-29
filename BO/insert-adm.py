import bcrypt
from pymongo import MongoClient

MONGO_USER="joso"
MONGO_PASS="XyGItdDKpWkfJfjT"
MONGO_CLUSTER="cluster0.yzzh9ig.mongodb.net"
DB_NAME="FIREFIGHTER"

uri = f"mongodb+srv://{MONGO_USER}:{MONGO_PASS}@{MONGO_CLUSTER}/{DB_NAME}?retryWrites=true&w=majority"
client = MongoClient(uri)
coll = client[DB_NAME]["Final"]

email = "admin@admin.com"
username = "admin"
plain_pw = "admin"

# generar hash bcrypt
salt = bcrypt.gensalt(rounds=12)
hashed = bcrypt.hashpw(plain_pw.encode("utf-8"), salt).decode("utf-8")

doc = {
    "email": email,
    "username": username,
    "password_hash": hashed,
    "role": "admin",
    "mfa_enabled": False,
    "mfa_secret": None
}

res = coll.find_one_and_update(
    {"email": email},
    {"$set": doc},
    upsert=True,
    return_document=True
)

print("Usuario insertado/actualizado:", res)
