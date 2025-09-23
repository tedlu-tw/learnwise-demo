from datetime import datetime, timezone, timedelta
from typing import List, Optional
from utils.database import get_db
from fsrs import Card, State
from bson import ObjectId
import logging

logger = logging.getLogger(__name__)

class FSRSCard:
    def __init__(self, user_id=None, question_id=None, due_date=None, stability=None,
                 difficulty=None, elapsed_days=None, scheduled_days=None, reps=None,
                 lapses=None, state=None, last_review=None, _id=None):
        self._id = _id
        self.user_id = user_id
        self.question_id = question_id
        self.due_date = due_date or datetime.now(timezone.utc)
        self.stability = stability or 0.0
        self.difficulty = difficulty or 0.0
        self.elapsed_days = elapsed_days or 0
        self.scheduled_days = scheduled_days or 0
        self.reps = reps or 0
        self.lapses = lapses or 0
        self.state = state or State.New.value
        self.last_review = last_review
        self.created_at = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)

    @property
    def id(self):
        return self._id

    def save(self):
        db = get_db()
        self.updated_at = datetime.now(timezone.utc)
        card_data = {
            'user_id': ObjectId(self.user_id),
            'question_id': ObjectId(self.question_id),
            'due_date': self.due_date,
            'stability': self.stability,
            'difficulty': self.difficulty,
            'elapsed_days': self.elapsed_days,
            'scheduled_days': self.scheduled_days,
            'reps': self.reps,
            'lapses': self.lapses,
            'state': self.state,
            'last_review': self.last_review,
            'updated_at': self.updated_at
        }
        if self._id:
            db.fsrs_cards.update_one({'_id': self._id}, {'$set': card_data})
        else:
            card_data['created_at'] = self.created_at
            result = db.fsrs_cards.insert_one(card_data)
            self._id = result.inserted_id
        logger.debug(f"Saved FSRS card: {self._id}")

    def update_from_fsrs_card(self, fsrs_card: Card):
        self.due_date = fsrs_card.due
        self.stability = fsrs_card.stability
        self.difficulty = fsrs_card.difficulty
        self.elapsed_days = fsrs_card.elapsed_days
        self.scheduled_days = fsrs_card.scheduled_days
        self.reps = fsrs_card.reps
        self.lapses = fsrs_card.lapses
        self.state = fsrs_card.state.value
        self.last_review = fsrs_card.last_review

    def to_fsrs_card(self) -> Card:
        return Card(
            due=self.due_date,
            stability=self.stability,
            difficulty=self.difficulty,
            elapsed_days=self.elapsed_days,
            scheduled_days=self.scheduled_days,
            reps=self.reps,
            lapses=self.lapses,
            state=State(self.state),
            last_review=self.last_review
        )

    @classmethod
    def get_by_id(cls, card_id: str) -> Optional['FSRSCard']:
        db = get_db()
        card_data = db.fsrs_cards.find_one({'_id': ObjectId(card_id)})
        if card_data:
            return cls._from_dict(card_data)
        return None

    @classmethod
    def get_by_user_and_question(cls, user_id: str, question_id: str) -> Optional['FSRSCard']:
        db = get_db()
        card_data = db.fsrs_cards.find_one({
            'user_id': ObjectId(user_id),
            'question_id': ObjectId(question_id)
        })
        if card_data:
            return cls._from_dict(card_data)
        return None

    @classmethod
    def get_due_cards(cls, user_id: str, limit: int = 20) -> List['FSRSCard']:
        db = get_db()
        now = datetime.now(timezone.utc)
        cursor = db.fsrs_cards.find({
            'user_id': ObjectId(user_id),
            'due_date': {'$lte': now}
        }).sort('due_date', 1).limit(limit)
        return [cls._from_dict(card_data) for card_data in cursor]

    @classmethod
    def get_new_cards(cls, user_id: str, limit: int = 10) -> List['FSRSCard']:
        db = get_db()
        cursor = db.fsrs_cards.find({
            'user_id': ObjectId(user_id),
            'state': State.New.value
        }).limit(limit)
        return [cls._from_dict(card_data) for card_data in cursor]

    @classmethod
    def get_cards_by_state(cls, user_id: str, state: int, limit: int = 50) -> List['FSRSCard']:
        db = get_db()
        cursor = db.fsrs_cards.find({
            'user_id': ObjectId(user_id),
            'state': state
        }).limit(limit)
        return [cls._from_dict(card_data) for card_data in cursor]

    @classmethod
    def delete_test_data(cls):
        db = get_db()
        db.fsrs_cards.delete_many({'user_id': {'$regex': 'test_'}})

    @classmethod
    def _from_dict(cls, card_data: dict) -> 'FSRSCard':
        return cls(
            _id=card_data['_id'],
            user_id=str(card_data['user_id']),
            question_id=str(card_data['question_id']),
            due_date=card_data['due_date'],
            stability=card_data['stability'],
            difficulty=card_data['difficulty'],
            elapsed_days=card_data['elapsed_days'],
            scheduled_days=card_data['scheduled_days'],
            reps=card_data['reps'],
            lapses=card_data['lapses'],
            state=card_data['state'],
            last_review=card_data.get('last_review')
        )
