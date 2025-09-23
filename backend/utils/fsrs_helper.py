from fsrs import Scheduler, Card, Rating
from datetime import datetime, timezone
from models.fsrs_card import FSRSCard
from typing import Optional

class FSRSHelper:
    def __init__(self, user_parameters: Optional[dict] = None):
        """Initialize FSRS Scheduler with optional user parameters."""
        self.scheduler = Scheduler(**user_parameters) if user_parameters else Scheduler()

    @staticmethod
    def initialize_card_for_question(user_id: str, question_id: str) -> FSRSCard:
        """Create and save a new FSRSCard for a user/question."""
        card = FSRSCard(user_id=user_id, question_id=question_id)
        card.save()
        return card

    @staticmethod
    def get_due_cards(user_id: str, limit: int = 20):
        """Get due FSRS cards for a user."""
        return FSRSCard.get_due_cards(user_id, limit)

    def review_card(self, card: FSRSCard, rating_value: int, now: Optional[datetime] = None):
        """Review a card using the FSRS scheduler and update the DB card."""
        fsrs_card = card.to_fsrs_card()
        now = now or datetime.now(timezone.utc)
        # Ensure rating_value is a valid Rating
        rating = Rating(rating_value) if not isinstance(rating_value, Rating) else rating_value
        updated_card, review_log = self.scheduler.review_card(fsrs_card, rating, now)
        card.update_from_fsrs_card(updated_card)
        card.save()
        return card, review_log

    def get_retrievability(self, card: FSRSCard, now: Optional[datetime] = None) -> float:
        """Get the retrievability (probability of recall) for a card."""
        now = now or datetime.now(timezone.utc)
        return self.scheduler.get_card_retrievability(card.to_fsrs_card(), now)

# Performance-to-rating conversion

def convert_performance_to_rating(is_correct: bool, response_time: float, difficulty_level: int, user_avg_time: float = 15) -> int:
    """Convert user performance to FSRS rating value (1=Again, 2=Hard, 3=Good, 4=Easy)."""
    if not is_correct:
        return Rating.Again.value
    time_factor = response_time / user_avg_time
    difficulty_multiplier = 1 + (difficulty_level - 2) * 0.2
    adjusted_time_factor = time_factor * difficulty_multiplier
    if adjusted_time_factor <= 0.5:
        return Rating.Easy.value
    elif adjusted_time_factor <= 1.0:
        return Rating.Good.value
    elif adjusted_time_factor <= 1.5:
        return Rating.Hard.value
    else:
        return Rating.Again.value
