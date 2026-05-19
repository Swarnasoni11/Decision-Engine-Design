# test_decision_engine.py

import unittest
from decision_engine import DecisionEngine

class TestDecisionEngine(unittest.TestCase):
    
    def setUp(self):
        self.engine = DecisionEngine()
        self.sample_questions = [
            {'id': 1, 'text': 'Q1', 'correct_answer': 'A', 'difficulty': 1, 'topic': 'math'},
            {'id': 2, 'text': 'Q2', 'correct_answer': 'B', 'difficulty': 2, 'topic': 'science'},
        ]
    
    def test_correct_answer_increases_streak(self):
        self.engine.evaluate_answer("correct", "correct")
        self.assertEqual(self.engine.user_performance['current_streak'], 1)
        self.assertEqual(self.engine.user_performance['correct_answers'], 1)
    
    def test_wrong_answer_resets_streak(self):
        self.engine.evaluate_answer("wrong", "correct")
        self.engine.evaluate_answer("wrong", "correct")
        self.assertEqual(self.engine.user_performance['current_streak'], 0)
    
    def test_difficulty_increases_after_3_correct(self):
        # Simulate 3 correct answers
        for i in range(3):
            self.engine.evaluate_answer("correct", "correct")
        self.engine.update_difficulty()
        self.assertEqual(self.engine.user_performance['difficulty_level'], 2)
    
    def test_difficulty_decreases_after_2_wrong(self):
        self.engine.user_performance['difficulty_level'] = 3
        self.engine.evaluate_answer("wrong", "correct")
        self.engine.evaluate_answer("wrong", "correct")
        self.engine.update_difficulty()
        self.assertEqual(self.engine.user_performance['difficulty_level'], 2)
    
    def test_stop_condition_quit(self):
        should_stop, reason = self.engine.should_stop("quit")
        self.assertTrue(should_stop)
    
    def test_stop_condition_10_correct(self):
        self.engine.user_performance['correct_answers'] = 10
        should_stop, reason = self.engine.should_stop()
        self.assertTrue(should_stop)

if __name__ == "__main__":
    unittest.main()