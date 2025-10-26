from utils.database import get_db
from bson import ObjectId

class Question:
    def __init__(self, id=None, type=None, text=None, options=None, correct_answer=None, category=None, difficulty=None, tags=None, sub_topic=None):
        self.id = id
        self.type = type or 'single'  # Default to single-choice
        self.text = text
        self.options = options or []
        self.correct_answer = correct_answer if isinstance(correct_answer, list) else [correct_answer] if correct_answer is not None else []
        self.category = category
        self.difficulty = difficulty if isinstance(difficulty, int) and 1 <= difficulty <= 5 else 1
        self.tags = tags or []
        self.sub_topic = sub_topic

    @classmethod
    def create_test_question(cls):
        db = get_db()
        q = {
            'type': 'single',
            'text': 'What is $2 + 2$?',
            'options': ['$3$', '$4$', '$5$', '$6$'],
            'correct_answer': [1],
            'category': '算術',
            'difficulty': 1,
            'tags': ['加法'],
            'sub_topic': '基礎運算'
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
            type=data.get('type', 'single'),
            text=data.get('text'),
            options=data.get('options', []),
            correct_answer=data.get('correct_answer', []),
            category=data.get('category'),
            difficulty=data.get('difficulty', 1),
            tags=data.get('tags', []),
            sub_topic=data.get('sub_topic')
        )

    @staticmethod
    def get_db():
        return get_db()
