import time
from fastapi import FastAPI, HTTPException
from pymongo import MongoClient
from fastapi.responses import RedirectResponse
from pymongo.errors import ConnectionFailure
from dotenv import load_dotenv
import os

load_dotenv()
MONGO_HOST = os.environ.get('MONGO_HOST', 'localhost')
MONGO_PORT = os.environ.get('MONGO_PORT', '27017')

app = FastAPI()

def connect_to_mongo(db_url, retries=5, delay=5):
    print(f"Connecting to MongoDB at {db_url}...")
    client = MongoClient(db_url)
    for _ in range(retries):
        try:
            client.admin.command('ismaster')
            return client
        except ConnectionFailure:
            print(f"Failed to connect to MongoDB. Retrying in {delay} seconds...")
            time.sleep(delay)
    raise ConnectionError("Could not connect to MongoDB after multiple retries.")

# Establish a connection to the MongoDB server
client = connect_to_mongo(f"mongodb://{MONGO_HOST}:{MONGO_PORT}/")
print("Successfully connected to MongoDB!")
db = client['leetcode_db']
collection = db['problems']

@app.get("/", include_in_schema=False)
async def root():
    return RedirectResponse(url="/docs")

@app.get("/questions/")
async def get_all_questions():
    questions = list(collection.find({}))
    for question in questions:
        question["_id"] = str(question["_id"])  # Convert ObjectID to string
    return {"questions": questions}

@app.get("/questions/{question_id}")
async def get_one_question(question_id: str):
    question = collection.find_one({"id": question_id})
    if question:
        question["_id"] = str(question["_id"])
        return {"question": question}
    else:
        raise HTTPException(status_code=404, detail="Question not found")
