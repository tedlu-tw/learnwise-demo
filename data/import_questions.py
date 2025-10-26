from pymongo import MongoClient
import json
import os
from dotenv import load_dotenv

# Load environment variables from project root
load_dotenv(dotenv_path='../.env')

# Use the same database configuration across the project
MONGODB_URI = os.environ.get('MONGODB_URI', 'mongodb://localhost:27017/innoserve-dev')
client = MongoClient(MONGODB_URI)
db = client['learnwise-demo']

def import_questions():
    try:
        # Read the combined questions file
        with open('combined_questions.json', 'r', encoding='utf-8') as f:
            questions = json.load(f)
        
        if not questions:
            print("No questions found in the combined file")
            return
        
        # Insert questions into the database
        result = db.questions.insert_many(questions)
        print(f"Successfully imported {len(result.inserted_ids)} questions into the database")
        
    except FileNotFoundError:
        print("combined_questions.json not found. Please run concat_json.py first")
    except json.JSONDecodeError as e:
        print(f"Error reading JSON file: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    import_questions()
