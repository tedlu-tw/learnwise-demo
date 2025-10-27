from utils.database import get_db
from bson import ObjectId
import datetime
from utils.security import PasswordManager
import logging

logger = logging.getLogger(__name__)

class User:
    def __init__(self, id=None, username=None, email=None, password_hash=None, role='user', last_login=None, selected_skills=None, total_questions_answered=0, seen_question_ids=None, correct_answers=0):
        self.id = id
        self.username = username
        self.email = email
        self.password_hash = password_hash
        self.role = role
        self.last_login = last_login
        self.selected_skills = selected_skills or []
        self.total_questions_answered = total_questions_answered
        self.seen_question_ids = seen_question_ids or []
        self.correct_answers = correct_answers or 0

    @classmethod
    def find_by_email(cls, email):
        db = get_db()
        try:
            data = db.users.find_one({'email': email})
            if data:
                logger.info(f"Found user with email {email}")
                return cls._from_dict(data)
            logger.warning(f"No user found with email {email}")
            return None
        except Exception as e:
            logger.error(f"Error finding user by email {email}: {str(e)}")
            return None

    @classmethod
    def find_by_username(cls, username):
        db = get_db()
        data = db.users.find_one({'username': username})
        if data:
            return cls._from_dict(data)
        return None

    @classmethod
    def get_by_id(cls, user_id):
        db = get_db()
        data = db.users.find_one({'_id': ObjectId(user_id)})
        if data:
            return cls._from_dict(data)
        return None

    @classmethod
    def create_user(cls, username, email, password):
        db = get_db()
        password_hash = PasswordManager.hash_password(password)
        user = {
            'username': username,
            'email': email,
            'password_hash': password_hash,
            'role': 'user',
            'created_at': datetime.datetime.utcnow(),
            'selected_skills': [],
            'total_questions_answered': 0
        }
        result = db.users.insert_one(user)
        user['_id'] = result.inserted_id
        return cls._from_dict(user)

    def check_password(self, password):
        return PasswordManager.verify_password(password, self.password_hash)

    def update_last_login(self):
        db = get_db()
        self.last_login = datetime.datetime.utcnow()
        db.users.update_one({'_id': ObjectId(self.id)}, {'$set': {'last_login': self.last_login}})

    @classmethod
    def create_test_user(cls):
        return cls.create_user(f"test_{ObjectId()}", f"test_{ObjectId()}@example.com", "testpass")

    @classmethod
    def delete_test_data(cls):
        db = get_db()
        db.users.delete_many({'username': {'$regex': 'test_'}})

    def mark_question_seen(self, question_id):
        """Mark a question as seen only if it's correctly answered."""
        db = get_db()
        db.users.update_one(
            {'_id': ObjectId(self.id)},
            {'$addToSet': {'seen_question_ids': ObjectId(question_id)}}
        )
        self.seen_question_ids.append(str(question_id))
        
    def reset_question_tracking(self):
        """Reset question tracking for this user."""
        db = get_db()
        db.users.update_one(
            {'_id': ObjectId(self.id)},
            {
                '$set': {
                    'seen_question_ids': [],
                    'total_questions_answered': 0,
                    'correct_answers': 0
                }
            }
        )
        self.seen_question_ids = []
        self.total_questions_answered = 0
        self.correct_answers = 0

    def get_question_stats(self):
        """Get question tracking stats for this user."""
        return {
            'total_questions': self.total_questions_answered,
            'correct_questions': self.correct_answers,
            'seen_questions': len(self.seen_question_ids),
            'accuracy': round((self.correct_answers / self.total_questions_answered * 100), 2) if self.total_questions_answered > 0 else 0
        }

    def get_completion_status(self):
        """Check completion status for questions in user's selected skills."""
        db = get_db()
        # Get total questions in user's selected skills
        total_questions = db.questions.count_documents({
            'category': {'$in': [s.lower() for s in self.selected_skills]}
        })
        # Get correctly answered questions (seen questions are only those answered correctly)
        completed_questions = len(self.seen_question_ids)
        
        return {
            'total_available': total_questions,
            'completed': completed_questions,
            'completion_rate': round((completed_questions / total_questions * 100), 2) if total_questions > 0 else 0
        }

    @staticmethod
    def _from_dict(data):
        return User(
            id=str(data['_id']),
            username=data.get('username'),
            email=data.get('email'),
            password_hash=data.get('password_hash'),
            role=data.get('role', 'user'),
            last_login=data.get('last_login'),
            selected_skills=data.get('selected_skills', []),
            total_questions_answered=data.get('total_questions_answered', 0),
            seen_question_ids=data.get('seen_question_ids', []),
            correct_answers=data.get('correct_answers', 0)
        )

    @staticmethod
    def get_db():
        return get_db()
