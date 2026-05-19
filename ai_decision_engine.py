# ai_decision_engine.py - ML-Enhanced Version

import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
import json

class AIDecisionEngine:
    def __init__(self):
        self.user_performance = {
            'correct_answers': [],
            'response_times': [],
            'difficulty_levels': [],
            'topics_attempted': [],
            'confidence_scores': []
        }
        
        # ML Models
        self.difficulty_predictor = RandomForestClassifier(n_estimators=100)
        self.question_selector = None
        self.scaler = StandardScaler()
        self.is_trained = False
        
        # Knowledge graph for topic relationships
        self.knowledge_graph = self.build_knowledge_graph()
        
    def build_knowledge_graph(self):
        """Build topic relationship graph (simplified)"""
        return {
            'mathematics': {
                'prerequisites': ['basic_arithmetic'],
                'related_topics': ['physics', 'statistics'],
                'difficulty_weight': 0.8
            },
            'programming': {
                'prerequisites': ['logic', 'algorithms'],
                'related_topics': ['data_structures', 'software_design'],
                'difficulty_weight': 0.9
            }
            # Add more topics as needed
        }
    
    def extract_features(self, user_history):
        """Extract features for ML model"""
        if len(user_history['correct_answers']) < 3:
            return None
        
        features = {
            'accuracy_recent': np.mean(user_history['correct_answers'][-5:]),
            'avg_response_time': np.mean(user_history['response_times'][-5:]),
            'current_difficulty': user_history['difficulty_levels'][-1] if user_history['difficulty_levels'] else 1,
            'streak_length': self.get_current_streak(user_history['correct_answers']),
            'topic_mastery_score': self.calculate_topic_mastery(user_history),
            'fatigue_index': len(user_history['correct_answers']) / 20,  # Increases with session length
            'variation_in_performance': np.std(user_history['correct_answers'][-10:]) if len(user_history['correct_answers']) >= 10 else 0
        }
        
        return np.array([list(features.values())])
    
    def get_current_streak(self, answers):
        """Calculate current streak of correct answers"""
        streak = 0
        for answer in reversed(answers):
            if answer == 1:
                streak += 1
            else:
                break
        return streak
    
    def calculate_topic_mastery(self, history):
        """Calculate mastery score for each topic"""
        if not history['topics_attempted']:
            return 0
        
        topic_scores = {}
        for i, topic in enumerate(history['topics_attempted']):
            if topic not in topic_scores:
                topic_scores[topic] = []
            topic_scores[topic].append(history['correct_answers'][i])
        
        # Average mastery across topics
        mastery = np.mean([np.mean(scores) for scores in topic_scores.values()])
        return mastery
    
    def train_difficulty_model(self, training_data):
        """Train ML model to predict optimal difficulty"""
        # training_data format: list of (features, optimal_difficulty)
        X = []
        y = []
        
        for features, optimal_diff in training_data:
            X.append(features)
            y.append(optimal_diff)
        
        X = np.array(X)
        X_scaled = self.scaler.fit_transform(X)
        
        self.difficulty_predictor.fit(X_scaled, y)
        self.is_trained = True
        
    def predict_optimal_difficulty(self, user_history):
        """Predict the optimal difficulty level for next question"""
        features = self.extract_features(user_history)
        
        if features is None or not self.is_trained:
            # Fallback to rule-based logic
            return self.fallback_difficulty_logic(user_history)
        
        features_scaled = self.scaler.transform(features)
        predicted_diff = self.difficulty_predictor.predict(features_scaled)[0]
        
        # Ensure difficulty is within bounds
        return max(1, min(5, int(predicted_diff)))
    
    def fallback_difficulty_logic(self, user_history):
        """Rule-based fallback when ML model isn't ready"""
        if len(user_history['correct_answers']) < 3:
            return 1
        
        recent_accuracy = np.mean(user_history['correct_answers'][-3:])
        
        if recent_accuracy >= 0.8:
            return min(5, (user_history['difficulty_levels'][-1] if user_history['difficulty_levels'] else 1) + 1)
        elif recent_accuracy <= 0.3:
            return max(1, (user_history['difficulty_levels'][-1] if user_history['difficulty_levels'] else 1) - 1)
        else:
            return user_history['difficulty_levels'][-1] if user_history['difficulty_levels'] else 1
    
    def select_next_question_ai(self, available_questions, user_history):
        """AI-based question selection using contextual bandits"""
        
        # Score each question based on multiple factors
        scored_questions = []
        
        for question in available_questions:
            score = self.calculate_question_score(question, user_history)
            scored_questions.append((score, question))
        
        # Sort by score and return best question
        scored_questions.sort(key=lambda x: x[0], reverse=True)
        
        # Add exploration (epsilon-greedy) to avoid getting stuck
        if np.random.random() < 0.1:  # 10% exploration rate
            return np.random.choice(available_questions)
        
        return scored_questions[0][1]
    
    def calculate_question_score(self, question, user_history):
        """Calculate score for a question (higher = better to ask next)"""
        score = 0
        
        # Factor 1: Difficulty match (40% weight)
        optimal_diff = self.predict_optimal_difficulty(user_history)
        diff_match = 1 - abs(question['difficulty'] - optimal_diff) / 5
        score += diff_match * 0.4
        
        # Factor 2: Topic weakness (30% weight)
        topic_mastery = self.get_topic_mastery_for_user(question['topic'], user_history)
        topic_need = 1 - topic_mastery  # Lower mastery = higher need
        score += topic_need * 0.3
        
        # Factor 3: Question freshness (20% weight)
        times_asked = user_history.get('questions_asked', {}).get(question['id'], 0)
        freshness = 1 / (times_asked + 1)
        score += freshness * 0.2
        
        # Factor 4: Prerequisite satisfaction (10% weight)
        prereq_satisfied = self.check_prerequisites(question, user_history)
        score += (1 if prereq_satisfied else 0) * 0.1
        
        return score
    
    def get_topic_mastery_for_user(self, topic, user_history):
        """Get user's mastery level for a specific topic"""
        if 'topic_performance' not in user_history:
            return 0
        
        topic_perf = user_history['topic_performance'].get(topic, [])
        if not topic_perf:
            return 0
        
        return np.mean(topic_perf)
    
    def check_prerequisites(self, question, user_history):
        """Check if user has mastered prerequisites for a question"""
        if 'prerequisites' not in question:
            return True
        
        for prereq_topic in question['prerequisites']:
            mastery = self.get_topic_mastery_for_user(prereq_topic, user_history)
            if mastery < 0.6:  # Need 60% mastery
                return False
        
        return True
    
    def adaptive_stopping_condition(self, user_history):
        """AI-based dynamic stopping condition"""
        
        # Factor 1: Learning progress
        if len(user_history['correct_answers']) >= 10:
            recent_accuracy = np.mean(user_history['correct_answers'][-5:])
            if recent_accuracy >= 0.85:
                return True, "Achieved mastery level"
        
        # Factor 2: Fatigue detection
        if len(user_history['response_times']) >= 8:
            recent_times = user_history['response_times'][-5:]
            if len(recent_times) >= 3:
                avg_recent = np.mean(recent_times)
                avg_previous = np.mean(user_history['response_times'][-10:-5]) if len(user_history['response_times']) >= 10 else avg_recent
                
                # If response time increased by >50%, user might be fatigued
                if avg_recent > avg_previous * 1.5:
                    return True, "User showing signs of fatigue"
        
        # Factor 3: Plateau detection (no improvement)
        if len(user_history['correct_answers']) >= 15:
            first_half = np.mean(user_history['correct_answers'][:7])
            second_half = np.mean(user_history['correct_answers'][7:14])
            
            if abs(second_half - first_half) < 0.05:  # No improvement
                return True, "Learning plateau detected - time for a break"
        
        return False, None