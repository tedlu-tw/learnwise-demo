import unittest
from datetime import datetime, timezone, timedelta
from utils.fsrs_helper import FSRSHelper
from models.fsrs_card import FSRSCard
from fsrs import Rating, State
from unittest.mock import patch, MagicMock

class TestFSRSHelper(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.test_user_id = 'test_user_123'
        self.test_question_id = 'test_question_456'
        self.helper = FSRSHelper()
        FSRSCard.delete_test_data()

    def tearDown(self):
        """Clean up after each test method."""
        FSRSCard.delete_test_data()

    def test_initialize_with_custom_parameters(self):
        """Test initialization with custom parameters."""
        custom_params = {
            'desired_retention': 0.8,
            'learning_steps': [timedelta(minutes=1)],
            'maximum_interval': 90,
            'enable_fuzzing': False
        }
        helper = FSRSHelper(custom_params)
        self.assertEqual(helper.scheduler.desired_retention, 0.8)
        self.assertEqual(len(helper.scheduler.learning_steps), 1)
        self.assertEqual(helper.scheduler.maximum_interval, 90)
        self.assertFalse(helper.scheduler.enable_fuzzing)

    def test_performance_to_rating_conversion(self):
        """Test converting performance metrics to FSRS rating."""
        # Test incorrect answer
        rating = self.helper.convert_performance_to_rating(
            is_correct=False,
            response_time=10,
            difficulty_level=1
        )
        self.assertEqual(rating, Rating.Again)

        # Test fast, correct answer
        rating = self.helper.convert_performance_to_rating(
            is_correct=True,
            response_time=5,
            difficulty_level=2,
            user_stats={'avg_response_time': 15}
        )
        self.assertEqual(rating, Rating.Easy)

        # Test slow, correct answer
        rating = self.helper.convert_performance_to_rating(
            is_correct=True,
            response_time=30,
            difficulty_level=4,
            user_stats={'avg_response_time': 15}
        )
        self.assertEqual(rating, Rating.Hard)

        # Test consecutive correct answers
        rating = self.helper.convert_performance_to_rating(
            is_correct=True,
            response_time=15,
            difficulty_level=3,
            consecutive_correct=5,
            user_stats={'avg_response_time': 15}
        )
        self.assertEqual(rating, Rating.Good)

    def test_review_card(self):
        """Test reviewing a card with performance data."""
        card = FSRSCard(
            user_id=self.test_user_id,
            question_id=self.test_question_id
        )
        card.save()

        # Test review with performance data
        performance_data = {
            'is_correct': True,
            'response_time': 10,
            'difficulty_level': 2,
            'consecutive_correct': 1
        }
        
        updated_card, review_log = self.helper.review_card(
            card,
            None,  # Rating will be calculated from performance_data
            performance_data
        )
        
        self.assertIsNotNone(updated_card.last_review)
        self.assertGreater(updated_card.reps, 0)
        self.assertGreater(updated_card.due_date, datetime.now(timezone.utc))

    def test_get_next_cards(self):
        """Test getting next cards for review."""
        # Create some test cards
        now = datetime.now(timezone.utc)
        
        # Due card in learning state
        card1 = FSRSCard(
            user_id=self.test_user_id,
            question_id='q1',
            state=State.Learning.value,
            due_date=now - timedelta(minutes=5)
        )
        card1.save()
        
        # Due card in review state
        card2 = FSRSCard(
            user_id=self.test_user_id,
            question_id='q2',
            state=State.Review.value,
            due_date=now - timedelta(hours=1)
        )
        card2.save()
        
        # Not due card
        card3 = FSRSCard(
            user_id=self.test_user_id,
            question_id='q3',
            state=State.Review.value,
            due_date=now + timedelta(days=1)
        )
        card3.save()

        # Test getting all due cards
        cards = FSRSHelper.get_next_cards(
            self.test_user_id,
            limit=10,
            include_learning=True
        )
        self.assertEqual(len(cards), 2)  # Should get card1 and card2

        # Test excluding learning cards
        cards = FSRSHelper.get_next_cards(
            self.test_user_id,
            limit=10,
            include_learning=False
        )
        self.assertEqual(len(cards), 1)  # Should only get card2

    @patch('utils.fsrs_helper.get_db')
    def test_next_cards_with_skills(self, mock_get_db):
        """Test getting next cards filtered by skills."""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        
        # Mock the database queries
        mock_db.fsrs_cards.find.return_value.sort.return_value.limit.return_value = [
            {'question_id': 'q1'},
            {'question_id': 'q2'}
        ]
        
        mock_db.questions.find.return_value = [
            {'_id': 'q1', 'skill_category': 'algebra'},
            {'_id': 'q2', 'skill_category': 'geometry'}
        ]
        
        # Test filtering by skills
        cards = FSRSHelper.get_next_cards(
            self.test_user_id,
            skills=['algebra'],
            limit=10
        )
        self.assertEqual(len(cards), 1)
        self.assertEqual(cards[0]['question_id'], 'q1')

    def test_retrievability(self):
        """Test getting card retrievability."""
        card = FSRSCard(
            user_id=self.test_user_id,
            question_id=self.test_question_id,
            state=State.Review.value,
            stability=5.0,
            difficulty=3.0
        )
        card.save()
        
        retrievability = self.helper.get_retrievability(card)
        self.assertIsInstance(retrievability, float)
        self.assertTrue(0 <= retrievability <= 1)

if __name__ == '__main__':
    unittest.main()
