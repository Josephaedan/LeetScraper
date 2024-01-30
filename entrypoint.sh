#!/bin/bash

# Wait for MongoDB to be ready
python wait_for_mongodb.py

# Run the scraper script to populate the database
# python scraper.py

# Start the FastAPI server
uvicorn server:app --host 0.0.0.0 --port 80
