import unittest
from datetime import datetime, timezone, timedelta
from models.fsrs_card import FSRSCard
from fsrs import State
from bson import ObjectId
from utils.database import get_db

class TestFSRSCard(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.test_user_id = 'test_user_123'
        self.test_question_id = 'test_question_456'
        # Clean up any existing test data
        FSRSCard.delete_test_data()
        
    def tearDown(self):
        """Clean up after each test method."""
        FSRSCard.delete_test_data()

    def test_card_creation(self):
        """Test basic card creation and default values."""
        card = FSRSCard(user_id=self.test_user_id, question_id=self.test_question_id)
        
        self.assertIsNone(card.id)
        self.assertEqual(card.user_id, self.test_user_id)
        self.assertEqual(card.question_id, self.test_question_id)
        self.assertEqual(card.state, State.Learning.value)
        self.assertEqual(card.stability, 2.5)
        self.assertEqual(card.difficulty, 2.5)
        self.assertEqual(card.reps, 0)
        self.assertEqual(card.lapses, 0)

    def test_save_and_retrieve(self):
        """Test saving card to database and retrieving it."""
        card = FSRSCard(user_id=self.test_user_id, question_id=self.test_question_id)
        card.save()
        
        # Test retrieval by ID
        retrieved_card = FSRSCard.get_by_id(str(card.id))
        self.assertIsNotNone(retrieved_card)
        self.assertEqual(retrieved_card.user_id, self.test_user_id)
        
        # Test retrieval by user and question
        retrieved_card = FSRSCard.get_by_user_and_question(self.test_user_id, self.test_question_id)
        self.assertIsNotNone(retrieved_card)
        self.assertEqual(retrieved_card.id, card.id)

    def test_card_properties(self):
        """Test the new card properties."""
        now = datetime.now(timezone.utc)
        future = now + timedelta(days=5)
        
        card = FSRSCard(
            user_id=self.test_user_id,
            question_id=self.test_question_id,
            due_date=future,
            state=State.Review.value
        )
        
        # Test state_name property
        self.assertEqual(card.state_name, 'Review')
        
        # Test is_due property
        self.assertFalse(card.is_due)
        card.due_date = now - timedelta(days=1)
        self.assertTrue(card.is_due)
        
        # Test days_until_due property
        card.due_date = future
        self.assertAlmostEqual(card.days_until_due, 5.0, places=1)

    def test_reset_state(self):
        """Test resetting card state."""
        card = FSRSCard(
            user_id=self.test_user_id,
            question_id=self.test_question_id,
            state=State.Review.value,
            stability=5.0,
            difficulty=4.0,
            reps=10,
            lapses=2
        )
        card.save()
        
        card.reset_state()
        
        self.assertEqual(card.state, State.Learning.value)
        self.assertEqual(card.stability, 2.5)
        self.assertEqual(card.difficulty, 2.5)
        self.assertEqual(card.elapsed_days, 0)
        self.assertEqual(card.scheduled_days, 0)
        
        # Verify changes were saved to database
        retrieved_card = FSRSCard.get_by_id(str(card.id))
        self.assertEqual(retrieved_card.state, State.Learning.value)

    def test_user_stats(self):
        """Test user statistics calculation."""
        # Create cards in different states
        states = [State.Learning, State.Review, State.Relearning]
        for i, state in enumerate(states):
            card = FSRSCard(
                user_id=self.test_user_id,
                question_id=f'question_{i}',
                state=state.value,
                reps=5,
                lapses=1,
                stability=3.0,
                difficulty=2.0
            )
            card.save()
        
        stats = FSRSCard.get_user_stats(self.test_user_id)
        
        self.assertEqual(stats['total_cards'], 3)
        self.assertEqual(stats['total_reps'], 15)  # 5 reps × 3 cards
        self.assertEqual(stats['total_lapses'], 3)  # 1 lapse × 3 cards
        self.assertAlmostEqual(stats['retention_rate'], 0.8)  # (15-3)/15
        
        # Check state-specific stats
        states_data = {state['state']: state for state in stats['states']}
        for state in states:
            state_stats = states_data[state.value]
            self.assertEqual(state_stats['count'], 1)
            self.assertEqual(state_stats['avg_stability'], 3.0)
            self.assertEqual(state_stats['avg_difficulty'], 2.0)

    def test_due_cards(self):
        """Test retrieving due cards."""
        now = datetime.now(timezone.utc)
        
        # Create some due and not due cards
        due_card = FSRSCard(
            user_id=self.test_user_id,
            question_id='due_q1',
            due_date=now - timedelta(hours=1)
        )
        due_card.save()
        
        not_due_card = FSRSCard(
            user_id=self.test_user_id,
            question_id='not_due_q1',
            due_date=now + timedelta(days=1)
        )
        not_due_card.save()
        
        due_cards = FSRSCard.get_due_cards(self.test_user_id)
        self.assertEqual(len(due_cards), 1)
        self.assertEqual(due_cards[0].question_id, 'due_q1')

    def test_fsrs_conversion(self):
        """Test conversion between FSRSCard and FSRS Card objects."""
        card = FSRSCard(
            user_id=self.test_user_id,
            question_id=self.test_question_id,
            state=State.Review.value,
            stability=4.0,
            difficulty=3.0,
            due_date=datetime.now(timezone.utc)
        )
        
        # Convert to FSRS Card
        fsrs_card = card.to_fsrs_card()
        self.assertEqual(fsrs_card.state, State.Review)
        self.assertEqual(fsrs_card.stability, 4.0)
        self.assertEqual(fsrs_card.difficulty, 3.0)
        
        # Update from FSRS Card
        fsrs_card.stability = 5.0
        fsrs_card.difficulty = 3.5
        fsrs_card.state = State.Relearning
        
        card.update_from_fsrs_card(fsrs_card)
        self.assertEqual(card.stability, 5.0)
        self.assertEqual(card.difficulty, 3.5)
        self.assertEqual(card.state, State.Relearning.value)

if __name__ == '__main__':
    unittest.main()
