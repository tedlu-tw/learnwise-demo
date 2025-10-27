from fsrs import Scheduler, Card, Rating, State
from datetime import datetime, timezone, timedelta
from models.fsrs_card import FSRSCard
from typing import Optional, List, Dict, Union, Tuple
from bson.objectid import ObjectId
from utils.database import get_db
import logging

logger = logging.getLogger(__name__)

class FSRSHelper:
    def __init__(self, user_parameters: Optional[dict] = None):
        """Initialize FSRS Scheduler with math-optimized parameters."""
        default_params = {
            'desired_retention': 0.85,  # Slightly lower for math learning
            'learning_steps': [
                timedelta(minutes=5),
                timedelta(minutes=30),
                timedelta(hours=4)
            ],
            'relearning_steps': [
                timedelta(minutes=10),
                timedelta(hours=1)
            ],
            'maximum_interval': 180,  # 6 months max for math topics
            'enable_fuzzing': True    # Add some randomness to intervals
        }
        
        # Update with user parameters if provided
        if user_parameters:
            # Adjust based on user level
            if 'user_level' in user_parameters:
                level = user_parameters['user_level']
                if level == 'beginner':
                    default_params['desired_retention'] = 0.90
                    default_params['learning_steps'].append(timedelta(hours=8))
                elif level == 'advanced':
                    default_params['desired_retention'] = 0.80
                    default_params['learning_steps'] = default_params['learning_steps'][:2]
            
            # Override with any explicit parameters
            default_params.update(user_parameters)
        
        self.scheduler = Scheduler(**default_params)

    @staticmethod
    def ensure_card(user_id: str, question_id: str, is_new: bool = True) -> FSRSCard:
        """Ensure an FSRSCard exists for a user/question, create if missing."""
        card = FSRSCard.get_by_user_and_question(user_id, question_id)
        if not card:
            card = FSRSCard(user_id=user_id, question_id=question_id)
            # For new cards, we start in Learning state
            # For review cards, we'll let FSRS handle the state transitions
            card.save()
        return card

    @staticmethod
    def update_card(user_id: str, question_id: str, rating: Rating) -> FSRSCard:
        """Update FSRS card state based on user rating."""
        card = FSRSHelper.ensure_card(user_id, question_id)
        helper = FSRSHelper()
        # Let FSRS handle the state transitions based on the rating
        updated_card, _ = helper.review_card(card, rating)
        return updated_card

    @staticmethod
    def get_due_cards(user_id: str, skills=None, limit: int = 20):
        """Get due FSRS cards for a user, optionally filtered by skills."""
        cards = FSRSCard.get_due_cards(user_id, limit=limit)
        if skills:
            db = get_db()
            skill_set = set([s.lower() for s in skills])
            filtered = []
            for card in cards:
                q = db.questions.find_one({'_id': ObjectId(card.question_id)})
                if q and q.get('skill_category', '').lower() in skill_set:
                    filtered.append({'question_id': card.question_id})
            return filtered
        return [{'question_id': card.question_id} for card in cards]

    def review_card(
        self,
        card: FSRSCard,
        rating_value: Optional[Union[int, Rating]] = None,
        performance_data: Optional[dict] = None,
        question_data: Optional[dict] = None,
        now: Optional[datetime] = None
    ) -> Tuple[FSRSCard, dict]:
        """
        Review a card with enhanced performance tracking
        
        Args:
            card: The FSRSCard to review
            rating_value: Optional explicit rating (1-4)
            performance_data: Dict with keys:
                - is_correct: bool
                - response_time: float (seconds)
                - consecutive_correct: int (optional)
            question_data: Question details including difficulty
            now: Override current time (for testing)
        """
        now = now or datetime.now(timezone.utc)
        
        # If we have performance data, calculate rating
        if performance_data and not rating_value:
            # Get question difficulty from question data or default to medium (3)
            question_difficulty = question_data.get('difficulty', 3) if question_data else 3
            
            rating_value = card.calculate_performance_rating(
                is_correct=performance_data['is_correct'],
                response_time=performance_data['response_time'],
                question_difficulty=question_difficulty,
                consecutive_correct=performance_data.get('consecutive_correct', 0)
            )
        
        # Ensure rating is proper type
        rating = rating_value if isinstance(rating_value, Rating) else Rating(rating_value)
        
        # Convert to FSRS Card and review
        fsrs_card = card.to_fsrs_card()
        updated_card, review_log = self.scheduler.review_card(fsrs_card, rating, now)
        
        # Update card with new FSRS state
        card.update_from_fsrs_card(updated_card)
        
        # Update additional metrics
        card.reps += 1
        if rating == Rating.Again:
            card.lapses += 1
        
        # Update timing metrics
        card.last_review = now
        if card.last_review:
            card.elapsed_days = (now - card.last_review).days
        card.scheduled_days = (card.due_date - now).days
        
        # Save changes
        card.save()
        
        logger.debug(
            f"Reviewed card {card.id}: rating={rating.name}, "
            f"next_review={card.due_date}, state={card.state_name}"
        )
        
        return card, review_log

    @staticmethod
    def get_next_cards(
        user_id: str,
        skills: Optional[List[str]] = None,
        limit: int = 20,
        include_learning: bool = True
    ) -> List[dict]:
        """Get next cards to review with smart selection"""
        cards_with_context = FSRSCard.get_cards_with_context(
            user_id=user_id,
            limit=limit * 2  # Get extra for filtering
        )
        
        if skills:
            # Filter by skills
            skill_set = {s.lower() for s in skills}
            cards_with_context = [
                (card, q) for card, q in cards_with_context
                if q.get('skill_category', '').lower() in skill_set
            ]
        
        # Filter by state if needed
        if not include_learning:
            cards_with_context = [
                (card, q) for card, q in cards_with_context
                if card.state == State.Review.value
            ]
        
        # Take only what we need
        cards_with_context = cards_with_context[:limit]
        
        return [
            {
                'question_id': card.question_id,
                'due_in_days': card.days_until_due,
                'state': card.state_name,
                'difficulty': q.get('difficulty', 3)
            }
            for card, q in cards_with_context
        ]
