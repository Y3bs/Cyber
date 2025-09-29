from pymongo import MongoClient
import os
from dotenv import load_dotenv
from pprint import pprint

load_dotenv()
DB_TOKEN = os.getenv('DB_TOKEN')
db = MongoClient(DB_TOKEN)

pprint(list(db.cyber.services.find({},{"_id": 0})))