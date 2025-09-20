from pymongo import MongoClient
from dotenv import load_dotenv
import os

load_dotenv()

username = os.getenv("DB_USERNAME")
password = os.getenv("DB_PASSWORD")
cluster = os.getenv("DB_CLUSTER")

uri = f"mongodb+srv://{username}:{password}@{cluster}.yzzh9ig.mongodb.net/?retryWrites=true&w=majority&appName={cluster}"

client = MongoClient(uri)
db = client["FIREFIGHTER"]
