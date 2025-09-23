from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv(dotenv_path='.env')

MONGODB_URI = os.environ.get('MONGODB_URI', 'mongodb://localhost:27017/innoserve-dev')
client = MongoClient(MONGODB_URI)
db = client['math_learning']

def create_indexes():
    db.users.create_index({"email": 1}, unique=True)
    db.users.create_index({"username": 1}, unique=True)
    db.questions.create_index({"skill_category": 1, "difficulty_level": 1})
    db.questions.create_index({"tags": 1})
    db.questions.create_index({"sub_topic": 1})
    db.fsrs_cards.create_index({"user_id": 1, "due_date": 1})
    db.fsrs_cards.create_index({"user_id": 1, "question_id": 1}, unique=True)
    db.fsrs_cards.create_index({"due_date": 1, "state": 1})
    db.lesson_reports.create_index({"user_id": 1, "timestamp": -1})
    db.lesson_reports.create_index({"session_id": 1})
    db.lesson_reports.create_index({"user_id": 1, "question_id": 1})
    db.lesson_sessions.create_index({"user_id": 1, "start_time": -1})
    db.lesson_sessions.create_index({"user_id": 1, "completed": 1})
    print("Indexes created.")

if __name__ == "__main__":
    create_indexes()
