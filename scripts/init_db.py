from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv(dotenv_path='../.env')

MONGODB_URI = os.environ.get('MONGODB_URI', 'mongodb://localhost:27017/innoserve-dev')
client = MongoClient(MONGODB_URI)
db = client.get_database()

def create_indexes():
    # User related indexes
    db.users.create_index({"email": 1}, unique=True)
    db.users.create_index({"username": 1}, unique=True)
    db.users.create_index({"selected_skills": 1})  # For skill-based filtering
    db.users.create_index({"created_at": -1})  # For user listing
    db.users.create_index([("role", 1), ("created_at", -1)])  # For admin management
    
    # Question related indexes
    db.questions.create_index({"category": 1, "difficulty": 1})  # For filtering by category and difficulty
    db.questions.create_index({"type": 1})  # For filtering by question type
    db.questions.create_index({"tags": 1})  # For tag-based searches
    db.questions.create_index({"category": 1, "sub_topic": 1})  # For hierarchical navigation
    db.questions.create_index([("category", 1), ("sub_topic", 1), ("difficulty", 1)])  # For combined filters
    
    # FSRS card indexes
    db.fsrs_cards.create_index({"user_id": 1, "due_date": 1})  # For retrieving due cards
    db.fsrs_cards.create_index({"user_id": 1, "question_id": 1}, unique=True)  # Unique card per user/question
    db.fsrs_cards.create_index([("user_id", 1), ("state", 1), ("due_date", 1)])  # For review scheduling
    db.fsrs_cards.create_index([("due_date", 1), ("state", 1)])  # For general review querying
    db.fsrs_cards.create_index({"updated_at": -1})  # For sync and maintenance
    
    # Learning session indexes
    db.lesson_sessions.create_index({"session_id": 1}, unique=True)  # Unique session lookup
    db.lesson_sessions.create_index({"user_id": 1, "created_at": -1})  # User's session history
    db.lesson_sessions.create_index([("user_id", 1), ("selected_skills", 1)])  # Skill-based session lookup
    db.lesson_sessions.create_index([("user_id", 1), ("completed", 1)])  # Active/completed sessions
    
    # Session reports/analytics indexes
    db.lesson_reports.create_index({"user_id": 1, "timestamp": -1})  # User's learning history
    db.lesson_reports.create_index({"session_id": 1})  # Session reports
    db.lesson_reports.create_index([("user_id", 1), ("question_id", 1), ("timestamp", -1)])  # Question history
    db.lesson_reports.create_index([("question_id", 1), ("is_correct", 1)])  # Question statistics
    
    print("Indexes created successfully.")

if __name__ == "__main__":
    create_indexes()
