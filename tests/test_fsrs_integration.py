import unittest
from datetime import datetime, timezone, timedelta
from backend.app import create_app
from backend.utils.fsrs_helper import FSRSHelper
from backend.models.user import User
from backend.models.question import Question
from backend.models.fsrs_card import FSRSCard

class TestFSRSIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_app()
        cls.app.config['TESTING'] = True
        cls.client = cls.app.test_client()
        cls.fsrs_helper = FSRSHelper()
    def setUp(self):
        self.test_user = User.create_test_user()
        self.test_question = Question.create_test_question()
    def tearDown(self):
        User.delete_test_data()
        Question.delete_test_data()
        FSRSCard.delete_test_data()
    def test_new_card_creation(self):
        card = self.fsrs_helper.initialize_card_for_question(
            str(self.test_user.id), str(self.test_question.id))
        self.assertIsNotNone(card)
        self.assertEqual(card.user_id, str(self.test_user.id))
        self.assertEqual(card.question_id, str(self.test_question.id))
        self.assertEqual(card.reps, 0)
    def test_card_review_cycle(self):
        card = self.fsrs_helper.initialize_card_for_question(
            str(self.test_user.id), str(self.test_question.id))
        updated_card, review_log = self.fsrs_helper.review_card(card, 3)
        self.assertEqual(updated_card.reps, 1)
        self.assertGreater(updated_card.stability, card.stability)
        self.assertIsNotNone(review_log)
        incorrect_card, incorrect_log = self.fsrs_helper.review_card(updated_card, 1)
        self.assertEqual(incorrect_card.lapses, 1)
    def test_due_cards_selection(self):
        card1 = self.fsrs_helper.initialize_card_for_question(
            str(self.test_user.id), str(self.test_question.id))
        card1.due_date = datetime.now(timezone.utc) - timedelta(hours=1)
        card1.save()
        due_cards = self.fsrs_helper.get_due_cards(str(self.test_user.id))
        self.assertGreater(len(due_cards), 0)
        self.assertIn(card1.id, [card.id for card in due_cards])

if __name__ == '__main__':
    unittest.main()
