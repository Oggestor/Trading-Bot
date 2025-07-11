from datetime import datetime
from managers import dbManager
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from pymongo import MongoClient
import os
import dotenv

# Connect to MongoDB
#client = MongoClient("mongodb://localhost:27017/")

# Get all database names
dotenv.load_dotenv()
CONNECTION_STRING = os.getenv('DB_CONNECTION')
client = MongoClient(CONNECTION_STRING, server_api=ServerApi('1'))

databases = client.list_database_names()

for db_name in databases:
    db = client[db_name]
    collections = db.list_collection_names()
    for collection_name in collections:    
        db = client[db_name]
        collection = db[collection_name]
        print(f"Processing {db_name}.{collection_name}")
        
        # Convert timestamp string to ISODate        
        try:
            result = collection.update_many(
                {},
                [{"$set": {"timestamp": {"$toDate": "$timestamp"}}}]
            )
            
            print(f"Updated {"result.modified_count"} documents in {db_name}.{collection_name}")
        except Exception as e:
            print(f"Error processing {db_name}.{collection_name}: {e}")
