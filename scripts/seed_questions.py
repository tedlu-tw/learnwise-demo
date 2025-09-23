from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv(dotenv_path='.env')

MONGODB_URI = os.environ.get('MONGODB_URI', 'mongodb://localhost:27017/math_learning')
client = MongoClient(MONGODB_URI)
db = client['math_learning']

sample_questions = [
    {
        'text': 'What is 2 + 2?',
        'options': ['3', '4', '5', '6'],
        'correct_answer': 1,
        'explanation': 'Basic addition: 2 + 2 = 4',
        'skill_category': 'arithmetic',
        'difficulty': 1,
        'tags': ['addition'],
        'sub_topic': 'basic'
    },
    {
        'text': 'Solve for x: 2x = 10',
        'options': ['2', '5', '10', '8'],
        'correct_answer': 1,
        'explanation': '2x=10 => x=5',
        'skill_category': 'algebra',
        'difficulty': 2,
        'tags': ['equation'],
        'sub_topic': 'linear'
    }
]

def seed():
    db.questions.insert_many(sample_questions)
    print("Sample questions seeded.")

if __name__ == "__main__":
    seed()
