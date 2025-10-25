from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv(dotenv_path='.env')

MONGODB_URI = os.environ.get('MONGODB_URI', 'mongodb://localhost:27017/math_learning')
client = MongoClient(MONGODB_URI)
db = client['math_learning']

print('Total questions:', db.questions.count_documents({}))
print('Questions by skill:')
for skill in ['arithmetic', 'algebra', 'calculus', 'geometry']:
    count = db.questions.count_documents({'skill_category': skill})
    print(f'{skill}: {count}')

print('\nSample questions:')
for q in db.questions.find().limit(3):
    print(f"- {q.get('text', q.get('question_text', 'No text'))[:50]}... (skill: {q.get('skill_category')})")
