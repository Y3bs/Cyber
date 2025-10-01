from pymongo import MongoClient
import os
from dotenv import load_dotenv
from pprint import pprint
import json
from datetime import datetime, timezone

load_dotenv()
DB_TOKEN = os.getenv('DB_TOKEN')
db = MongoClient(DB_TOKEN)

def load_services():
    try:
        services = list(db.cyber.services.find({}, {"_id": 0})).sort({"name": 1})  
        if not services:
            return []
        return services
        
    except Exception as e:
        print(f"[Services] Error loading file: {e}")
        return []

def save_service(data):
    try:
        db.cyber.services.insert_one(data)
    except Exception as e:
        print(f"Error Saving Document\nError: {e}")

def update_service(update):
    try:
        service_name = update['name']
        # Only set provided fields except 'name'
        fields_to_set = {k: v for k, v in update.items() if k != "name"}
        if not fields_to_set:
            return {"matched": 0, "modified": 0, "error": "no updatable fields provided"}

        result = db.cyber.services.update_one({"name": service_name}, {"$set": fields_to_set})
        return {"matched": result.matched_count, "modified": result.modified_count}
    except Exception as e:
        print(f"Error updating service\nError: {e}")
        return {"matched": 0, "modified": 0, "error": str(e)}

def delete_service(name):
    try:
        db.cyber.services.delete_one({"name": name})
    except Exception as e:
        print(f"Error deleting service\nError: {e}")


def save_logs():
    try:
        with open('current_day.json','r',encoding='utf-8') as f:
            doc = json.load(f)

        now = datetime.now(timezone.utc)
        doc["date"] = now.strftime("%Y-%m-%d")  # e.g. 2025-09-29
        db.cyber.logs.insert_one(doc)
        default = {
            "pcs": [],
            "services": [],
            "expenses":[],
            "totals": {"pcs": 0, "services": 0,"expenses":0, "all": 0},
            "log_channel_id": None
        }
        with open('current_day.json','w',encoding='utf-8') as f:
            json.dump(default,f,indent=4)
    except Exception as e:
        print(f"Error Saving Logs\nError: {e}")
