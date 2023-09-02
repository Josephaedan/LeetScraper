import os
from dotenv import load_dotenv
import time
from pymongo import MongoClient

load_dotenv()

def wait_for_mongodb():
    mongo_host = os.environ.get("MONGO_HOST", "mongodb")
    mongo_port = os.environ.get("MONGO_PORT", 27017)
    print(f"Attempting to connect to MongoDB at {mongo_host}:{mongo_port}...")
    client = MongoClient(host=mongo_host, port=int(mongo_port))
    
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
