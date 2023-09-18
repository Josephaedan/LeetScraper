import os
from dotenv import load_dotenv
import time
from pymongo import MongoClient

load_dotenv()

def wait_for_mongodb():
    MONGO_HOST = os.environ.get("MONGO_HOST", "mongodb")
    MONGO_PORT = os.environ.get("MONGO_PORT", 27017)
    db_url = f"mongodb://{MONGO_HOST}:{MONGO_PORT}/"
    print(f"Attempting to connect to MongoDB at {db_url}...")
    
    client = MongoClient(db_url)
    
    while True:
        try:
            # The ismaster command is cheap and does not require auth.
            client.admin.command('ismaster')
            print("MongoDB is ready!")
            return
        except Exception as e:
            print("Waiting for MongoDB...", e)
            time.sleep(5)

if __name__ == "__main__":
    wait_for_mongodb()
