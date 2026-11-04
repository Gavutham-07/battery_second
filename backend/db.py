import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "revolt_db")

client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)

db = client[MONGO_DB_NAME]

batteries_collection = db["batteries"]
tests_collection = db["tests"]
reports_collection = db["reports"]
exchanges_collection = db["exchanges"]
inventory_collection = db["inventory"]


def test_connection():
    try:
        client.admin.command("ping")
        return True
    except Exception as e:
        print(f"MongoDB connection failed: {e}")
        return False


def init_indexes():
    try:
        batteries_collection.create_index("battery_id", unique=True)
        tests_collection.create_index([("battery_id", 1), ("sec", 1)])
        tests_collection.create_index("mode")
        reports_collection.create_index([("battery_id", 1), ("created_at", -1)])
        exchanges_collection.create_index("transaction_id", unique=True)
        exchanges_collection.create_index("battery_id")
        inventory_collection.create_index("battery_id", unique=True)
        return True
    except Exception as e:
        print(f"Index initialization warning: {e}")
        return False
