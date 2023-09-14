import time
import requests
from bs4 import BeautifulSoup
from pymongo import MongoClient, UpdateOne
import json
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError, BulkWriteError
from dotenv import load_dotenv
import os 

load_dotenv()
MONGO_HOST = os.environ.get('MONGO_HOST', 'localhost')
MONGO_PORT = os.environ.get('MONGO_PORT', '27017')

def parse_questions_xml():
    """Parse the Leetcode questions sitemap XML file and return a list of all question URLs."""
    BASE_URL = "https://leetcode.com/sitemap/sitemap-question-1.xml"
    response = requests.get(BASE_URL).content
    soup = BeautifulSoup(response, "xml")
    urls = soup.find_all("loc")
    return [url.text for url in urls]

def get_questions_to_scrape(urls):
    """Return a list of question URLs to be scraped today. This is defined as all questions that have not been scraped yet, or have been updated more than 7 days ago"""
    # Establish a connection to the MongoDB server
    client = connect_to_mongo(f"mongodb://{MONGO_HOST}:{MONGO_PORT}/")
    print("Successfully connected to MongoDB!")

    # Select the database and collection
    db = client['leetcode_db']
    collection = db['problems']

    # Get all existing question URLs
    existing_urls = [{question["url"]: question["updated_at"]} for question in collection.find({}, {"url": 1, "updated_at": 1, "_id": False})]

    # Get all question URLs that have not been scraped yet, or have been updated more than 7 days ago. Set an upper limit of 500 questions to scrape per day.
    urls_to_scrape = []
    for url in urls:
        if len(urls_to_scrape) >= 500:
            break
        if url not in existing_urls or (url in existing_urls and int(time.time()) - existing_urls[url] > 604800):
            urls_to_scrape.append(url)

    # Close the connection (good practice)
    client.close()

    return urls_to_scrape


def scrape_leetcode_from_urls(urls_to_scrape):
    """Scrape Leetcode for the questions in the list of URLs and return a list of question details."""
    problems = []
    for url in urls_to_scrape:
        # Wait for 0.1 seconds between each request
        time.sleep(0.1)

        response = requests.get(url)
        soup = BeautifulSoup(response.content, "html.parser")

        # # Save the HTML to a file
        # with open('output.html', 'w', encoding='utf-8') as file:
        #     file.write(soup.prettify())

        script_tag = soup.find('script', attrs={'id': '__NEXT_DATA__'})

        # Extract and parse the JSON data
        if script_tag:
            json_data = json.loads(script_tag.string)
            queries = json_data['props']['pageProps']['dehydratedState']['queries']
            details = get_details_from_queries(queries)
            problems.append(details)
            print(f"Successfully scraped {url}!")
        else:
            print("Script tag not found!")

    return problems

def get_details_from_queries(queries: list[dict]):
    question_details = {}

    # Set updated_at timestamp
    question_details["updated_at"] = int(time.time())

    # Extract question details from the first query
    data = queries[0].get("state", {}).get("data", {}).get("question", {})
    question_details["title"] = data.get("title", "")
    question_details["url"] = f"https://leetcode.com/problems/{data.get('titleSlug', '')}"
    question_details["difficulty"] = data.get("difficulty", "")
    question_details["id"] = data.get("questionId", "")
    question_details["paid_only"] = data.get("isPaidOnly", "")
    question_details["category"] = data.get("categoryTitle", "")

    # If question is paid only, return now
    if question_details["paid_only"]:
        return question_details

    # Extract language list from the second query
    languages = queries[1].get("state", {}).get("data", {}).get("languageList", [])
    question_details["languages"] = [lang["name"] for lang in languages]

    # Extract example test cases from the fourth query
    test_cases = queries[3].get("state", {}).get("data", {}).get("question", {}).get("exampleTestcaseList", [])
    question_details["test_cases"] = test_cases

    # Extract content from the seventh query
    question_details["description"] = BeautifulSoup(queries[6].get("state", {}).get("data", {}).get("question", {}).get("content", ""), 'html.parser').text

    # Extract hints from the sixth query
    hints = queries[5].get("state", {}).get("data", {}).get("question", {}).get("hints", [])
    question_details["hints"] = [BeautifulSoup(hint, 'html.parser').text for hint in hints]

    # Extract topic tags from the fifth query
    tags = queries[8].get("state", {}).get("data", {}).get("question", {}).get("topicTags", [])
    question_details["topic_tags"] = [tag["name"] for tag in tags]

    # Extract code snippets from the last query
    code_snippets = queries[-1].get("state", {}).get("data", {}).get("question", {}).get("codeSnippets", [])
    question_details["code_snippets"] = code_snippets

    # Print extracted data
    return question_details

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

def save_to_mongodb(problems):
    try:
        # Establish a connection to the MongoDB server
        client = connect_to_mongo(f"mongodb://{MONGO_HOST}:{MONGO_PORT}/")
        print("Successfully connected to MongoDB!")

        # Select the database and collection
        db = client['leetcode_db']
        collection = db['problems']

        # Create a list of UpdateOne operations
        operations = [
            UpdateOne(
                {'id': problem['id']},  # Filter by problem ID
                {'$set': problem},      # Update or set the problem data
                upsert=True              # Insert a new document if no document matches the filter
            )
            for problem in problems
        ]

        # Execute all operations in a single batch
        collection.bulk_write(operations)
        print("Successfully saved all problems to MongoDB!")

    except ServerSelectionTimeoutError:
        print("Error: Unable to connect to MongoDB server. Connection timed out.")
    except ConnectionFailure:
        print("Error: Failed to connect to MongoDB server.")
    except BulkWriteError:
        print("Error: Some of the problems already exist in the database or other bulk write error occurred.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

    finally:
        # Close the connection (good practice)
        client.close()

if __name__ == "__main__":
    all_questions = parse_questions_xml()
    questions_to_scrape = get_questions_to_scrape(all_questions)
    problems = scrape_leetcode_from_urls(questions_to_scrape)
    save_to_mongodb(problems)
