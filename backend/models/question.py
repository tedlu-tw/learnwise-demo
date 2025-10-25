from utils.database import get_db
from bson import ObjectId

class Question:
    def __init__(self, id=None, text=None, options=None, correct_answer=None, explanation=None, skill_category=None, difficulty=None, tags=None, sub_topic=None):
        self.id = id
        self.text = text
        self.options = options or []
        self.correct_answer = correct_answer
        self.explanation = explanation
        self.skill_category = skill_category
        self.difficulty = difficulty
        self.tags = tags or []
        self.sub_topic = sub_topic

    @classmethod
    def create_test_question(cls):
        db = get_db()
        q = {
            'text': 'What is 2 + 2?',
            'options': ['3', '4', '5', '6'],
            'correct_answer': 1,
            'explanation': 'Basic addition: 2 + 2 = 4',
            'skill_category': 'arithmetic',
            'difficulty': 1,
            'tags': ['addition'],
            'sub_topic': 'basic'
        }
        result = db.questions.insert_one(q)
        q['_id'] = result.inserted_id
        return cls._from_dict(q)

    @classmethod
    def delete_test_data(cls):
        db = get_db()
        db.questions.delete_many({'text': {'$regex': r'What is 2 \+ 2'}})

    @staticmethod
    def _from_dict(data):
        return Question(
            id=str(data['_id']),
            text=data.get('text'),
            options=data.get('options', []),
            correct_answer=data.get('correct_answer'),
            explanation=data.get('explanation'),
            skill_category=data.get('skill_category'),
            difficulty=data.get('difficulty'),
            tags=data.get('tags', []),
            sub_topic=data.get('sub_topic')
        )

    @staticmethod
    def get_db():
        return get_db()
