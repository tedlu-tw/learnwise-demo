"""
FSRS Card Schema (MongoDB: fsrs_cards collection):
- _id: ObjectId
- user_id: ObjectId (refers to users._id)
- question_id: ObjectId (refers to questions._id)
- due_date: datetime (next review due)
- stability: float (FSRS stability)
- difficulty: float (FSRS difficulty)
- elapsed_days: int (days since last review)
- scheduled_days: int (days scheduled for next review)
- reps: int (number of successful reviews)
- lapses: int (number of failed reviews)
- state: int (FSRS state: New, Learning, Review, Relearning)
- step: Optional[int] (learning/relearning step; 0+ for Learning/Relearning, None for Review)
- last_review: datetime (last review timestamp)
- created_at: datetime
- updated_at: datetime
"""

from datetime import datetime, timezone, timedelta
from typing import List, Optional, Tuple
from utils.database import get_db
from fsrs import Card, State, Rating
from bson import ObjectId
from bson.errors import InvalidId
import logging

logger = logging.getLogger(__name__)

# Normalize string/ObjectId values; keep strings that aren't valid ObjectIds
def _normalize_id(value):
    if isinstance(value, ObjectId):
        return value
    if isinstance(value, str):
        try:
            return ObjectId(value)
        except InvalidId:
            return value
    return value

class FSRSCard:
    def __init__(self, user_id=None, question_id=None, due_date=None, stability=None,
                 difficulty=None, elapsed_days=None, scheduled_days=None, reps=None,
                 lapses=None, step: Optional[int] = None, state=None, last_review=None, _id=None):
        self._id = _id
        self.user_id = user_id
        self.question_id = question_id
        self.due_date = due_date or datetime.now(timezone.utc)
        self.stability = stability if stability is not None else 2.5
        self.difficulty = difficulty if difficulty is not None else 2.5
        self.elapsed_days = elapsed_days or 0
        self.scheduled_days = scheduled_days or 0
        self.reps = reps or 0
        self.lapses = lapses or 0
        # Default to Learning state for new cards
        self.state = state if state is not None else State.Learning.value
        # Ensure a valid step for Learning/Relearning states, None for Review
        if step is None:
            if self.state in (State.Learning.value, State.Relearning.value):
                self.step = 0
            else:
                self.step = None
        else:
            self.step = step
        self.last_review = last_review
        self.created_at = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)

    @property
    def id(self):
        return self._id

    @property
    def days_until_due(self) -> float:
        """Calculate days until the next review is due"""
        if not self.due_date:
            return 0.0
        now = datetime.now(timezone.utc)
        delta = self.due_date - now
        return delta.total_seconds() / (24 * 3600)  # Convert seconds to days

    @property
    def is_due(self) -> bool:
        """Whether the card is currently due for review"""
        if not self.due_date:
            return False
        return self.due_date <= datetime.now(timezone.utc)

    @property
    def state_name(self) -> str:
        """Get a human-readable name for the card's state"""
        state_map = {
            State.Learning.value: 'Learning',
            State.Review.value: 'Review',
            State.Relearning.value: 'Relearning'
        }
        return state_map.get(self.state, 'New')  # Default to 'New' for unrecognized states

    def _default_step_for_state(self, state_val: int) -> Optional[int]:
        return 0 if state_val in (State.Learning.value, State.Relearning.value) else None

    def save(self):
        db = get_db()
        self.updated_at = datetime.now(timezone.utc)
        card_data = {
            'user_id': _normalize_id(self.user_id),
            'question_id': _normalize_id(self.question_id),
            'due_date': self.due_date,
            'stability': self.stability,
            'difficulty': self.difficulty,
            'elapsed_days': self.elapsed_days,
            'scheduled_days': self.scheduled_days,
            'reps': self.reps,
            'lapses': self.lapses,
            'state': self.state,
            'step': self.step,
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
        self.state = fsrs_card.state.value
        self.last_review = getattr(fsrs_card, "last_review", None)
        # Ensure step is persisted; default appropriately if missing
        self.step = getattr(fsrs_card, "step", self._default_step_for_state(self.state))
        # Remove legacy/undocumented FSRS fields for future compatibility

    def to_fsrs_card(self) -> Card:
        # Guarantee a valid step for Learning/Relearning
        step_val = self.step if self.step is not None else self._default_step_for_state(self.state)
        # Try with step and last_review
        try:
            return Card(
                due=self.due_date,
                stability=self.stability,
                difficulty=self.difficulty,
                state=State(self.state),
                last_review=self.last_review,
                step=step_val
            )
        except TypeError:
            # Fallback for fsrs.Card versions without `step`
            try:
                return Card(
                    due=self.due_date,
                    stability=self.stability,
                    difficulty=self.difficulty,
                    state=State(self.state),
                    last_review=self.last_review
                )
            except TypeError:
                # Fallback for fsrs.Card versions without `last_review` as well
                return Card(
                    due=self.due_date,
                    stability=self.stability,
                    difficulty=self.difficulty,
                    state=State(self.state)
                )

    def reset_state(self):
        """Reset the card back to Learning with default parameters and persist it."""
        self.state = State.Learning.value
        self.stability = 2.5
        self.difficulty = 2.5
        self.elapsed_days = 0
        self.scheduled_days = 0
        # Ensure step is valid for Learning
        self.step = self._default_step_for_state(self.state)
        self.save()

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
            'user_id': _normalize_id(user_id),
            'question_id': _normalize_id(question_id)
        })
        if card_data:
            return cls._from_dict(card_data)
        return None

    @classmethod
    def get_due_cards(cls, user_id: str, limit: int = 20) -> List['FSRSCard']:
        db = get_db()
        now = datetime.now(timezone.utc)
        cursor = db.fsrs_cards.find({
            'user_id': _normalize_id(user_id),
            'due_date': {'$lte': now}
        }).sort('due_date', 1).limit(limit)
        return [cls._from_dict(card_data) for card_data in cursor]

    @classmethod
    def get_new_cards(cls, user_id: str, limit: int = 10) -> List['FSRSCard']:
        """Get cards that are in the Learning state and haven't been reviewed yet"""
        db = get_db()
        cursor = db.fsrs_cards.find({
            'user_id': _normalize_id(user_id),
            'state': State.Learning.value,
            'last_review': None  # Cards that haven't been reviewed yet
        }).limit(limit)
        return [cls._from_dict(card_data) for card_data in cursor]

    @classmethod
    def get_cards_by_state(cls, user_id: str, state: int, limit: int = 50) -> List['FSRSCard']:
        db = get_db()
        cursor = db.fsrs_cards.find({
            'user_id': _normalize_id(user_id),
            'state': state
        }).limit(limit)
        return [cls._from_dict(card_data) for card_data in cursor]

    @classmethod
    def delete_test_data(cls):
        db = get_db()
        db.fsrs_cards.delete_many({'user_id': {'$regex': 'test_'}})

    @classmethod
    def _from_dict(cls, card_data: dict) -> 'FSRSCard':
        stability = card_data.get('stability', 2.5)
        if not stability or stability == 0.0:
            stability = 2.5
        difficulty = card_data.get('difficulty', 2.5)
        if not difficulty or difficulty == 0.0:
            difficulty = 2.5
        # Ensure due_date and last_review are always UTC-aware datetimes
        due_date = card_data.get('due_date')
        if due_date and due_date.tzinfo is None:
            from datetime import timezone
            due_date = due_date.replace(tzinfo=timezone.utc)
        last_review = card_data.get('last_review')
        if last_review and last_review.tzinfo is None:
            from datetime import timezone
            last_review = last_review.replace(tzinfo=timezone.utc)
        state_val = card_data['state']
        step_val = card_data.get('step')
        if step_val is None:
            step_val = 0 if state_val in (State.Learning.value, State.Relearning.value) else None
        return cls(
            _id=card_data['_id'],
            user_id=str(card_data['user_id']),
            question_id=str(card_data['question_id']),
            due_date=due_date,
            stability=stability,
            difficulty=difficulty,
            elapsed_days=card_data.get('elapsed_days', 0),
            scheduled_days=card_data.get('scheduled_days', 0),
            reps=card_data.get('reps', 0),
            lapses=card_data.get('lapses', 0),
            step=step_val,
            state=state_val,
            last_review=last_review
        )

    @staticmethod
    def convert_difficulty_to_fsrs(db_difficulty: int) -> float:
        """
        Convert database difficulty (1-5) to FSRS difficulty scale
        1 = Very Easy   -> 1.5
        2 = Easy        -> 2.0
        3 = Medium      -> 2.5
        4 = Hard        -> 3.0
        5 = Very Hard   -> 3.5
        """
        return 1.5 + (db_difficulty - 1) * 0.5

    @staticmethod
    def convert_difficulty_to_db(fsrs_difficulty: float) -> int:
        """Convert FSRS difficulty back to database scale (1-5)"""
        db_difficulty = round(((fsrs_difficulty - 1.5) / 0.5) + 1)
        return max(1, min(5, db_difficulty))  # Clamp between 1-5

    def initialize_from_question(self, question_data: dict):
        """Initialize card difficulty from question data"""
        if 'difficulty' in question_data:
            self.difficulty = self.convert_difficulty_to_fsrs(question_data['difficulty'])
        return self

    @classmethod
    def get_cards_with_context(cls, user_id: str, limit: int = 20) -> List[tuple['FSRSCard', dict]]:
        """Get due cards along with their question data"""
        db = get_db()
        now = datetime.now(timezone.utc)
        
        # First get the due cards
        cursor = db.fsrs_cards.find({
            'user_id': _normalize_id(user_id),
            'due_date': {'$lte': now}
        }).sort('due_date', 1).limit(limit)
        
        cards = [cls._from_dict(card_data) for card_data in cursor]
        
        # Batch fetch questions
        obj_ids = []
        for card in cards:
            try:
                obj_ids.append(ObjectId(card.question_id))
            except (InvalidId, TypeError):
                continue
        questions = {
            str(q['_id']): q 
            for q in db.questions.find({'_id': {'$in': obj_ids}})
        }
        
        return [(card, questions.get(card.question_id, {})) for card in cards]

    @classmethod
    def get_user_stats(cls, user_id: str) -> dict:
        """Aggregate basic study stats for a user."""
        db = get_db()
        match_stage = {'$match': {'user_id': _normalize_id(user_id)}}
        total_pipeline = [
            match_stage,
            {'$group': {
                '_id': None,
                'total_cards': {'$sum': 1},
                'total_reps': {'$sum': {'$ifNull': ['$reps', 0]}},
                'total_lapses': {'$sum': {'$ifNull': ['$lapses', 0]}}
            }}
        ]
        totals = list(db.fsrs_cards.aggregate(total_pipeline))
        totals_doc = totals[0] if totals else {'total_cards': 0, 'total_reps': 0, 'total_lapses': 0}
        states_pipeline = [
            match_stage,
            {'$group': {
                '_id': '$state',
                'count': {'$sum': 1},
                'avg_stability': {'$avg': {'$ifNull': ['$stability', 0]}},
                'avg_difficulty': {'$avg': {'$ifNull': ['$difficulty', 0]}}
            }}
        ]
        states = []
        for s in db.fsrs_cards.aggregate(states_pipeline):
            states.append({
                'state': s['_id'],
                'count': s['count'],
                'avg_stability': float(s.get('avg_stability') or 0.0),
                'avg_difficulty': float(s.get('avg_difficulty') or 0.0)
            })
        total_reps = int(totals_doc.get('total_reps', 0) or 0)
        total_lapses = int(totals_doc.get('total_lapses', 0) or 0)
        retention = (total_reps - total_lapses) / total_reps if total_reps > 0 else 0.0
        return {
            'total_cards': int(totals_doc.get('total_cards', 0) or 0),
            'total_reps': total_reps,
            'total_lapses': total_lapses,
            'retention_rate': round(retention, 2),
            'states': states
        }

    def calculate_performance_rating(
        self,
        is_correct: bool,
        response_time: float,
        question_difficulty: int,
        consecutive_correct: int = 0
    ) -> Rating:
        """
        Calculate FSRS rating based on performance metrics.
        Falls back to Again on incorrect answers, and adjusts by time, difficulty, and consistency.
        """
        if not is_correct:
            return Rating.Again

        expected_time = {
            1: 10,
            2: 20,
            3: 30,
            4: 45,
            5: 60
        }.get(question_difficulty, 30)

        # Avoid division by zero and negatives
        expected_time = max(expected_time, 1)
        rt = max(response_time, 0.0)
        time_factor = rt / expected_time

        difficulty_multiplier = 1 + (question_difficulty - 3) * 0.2
        consistency_bonus = min(max(consecutive_correct, 0) * 0.1, 0.3)

        final_score = time_factor * difficulty_multiplier * (1 - consistency_bonus)

        if final_score <= 0.6:
            return Rating.Easy
        elif final_score <= 1.0:
            return Rating.Good
        elif final_score <= 1.5:
            return Rating.Hard
        return Rating.Again
