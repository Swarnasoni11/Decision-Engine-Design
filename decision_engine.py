# decision_engine.py - Rule-Based Version

class DecisionEngine:
    def __init__(self):
        self.user_performance = {
            'correct_answers': 0,
            'wrong_answers': 0,
            'current_streak': 0,
            'difficulty_level': 1,  # 1-5 scale
            'question_history': [],
            'topic_mastery': {}  # track per-topic performance
        }
        
        # Define difficulty thresholds
        self.difficulty_thresholds = {
            1: {'name': 'Beginner', 'points_needed': 0},
            2: {'name': 'Easy', 'points_needed': 3},
            3: {'name': 'Intermediate', 'points_needed': 6},
            4: {'name': 'Advanced', 'points_needed': 9},
            5: {'name': 'Expert', 'points_needed': 12}
        }
        
    def evaluate_answer(self, user_answer, correct_answer):
        """Evaluate if answer is correct and update performance"""
        is_correct = self.check_correctness(user_answer, correct_answer)
        
        # Update performance metrics
        if is_correct:
            self.user_performance['correct_answers'] += 1
            self.user_performance['current_streak'] += 1
        else:
            self.user_performance['wrong_answers'] += 1
            self.user_performance['current_streak'] = 0
            
        # Record history
        self.user_performance['question_history'].append({
            'answer': user_answer,
            'is_correct': is_correct,
            'timestamp': datetime.now()
        })
        
        return is_correct
    
    def check_correctness(self, user_answer, correct_answer):
        """Check if answer is correct (with fuzzy matching)"""
        # Simple exact match (you can enhance this)
        return user_answer.strip().lower() == correct_answer.strip().lower()
    
    def decide_next_question(self, available_questions):
        """Decide which question to ask next"""
        
        # Filter questions by current difficulty
        suitable_questions = [
            q for q in available_questions 
            if q['difficulty'] == self.user_performance['difficulty_level']
        ]
        
        # Prioritize topics with low mastery
        if self.user_performance['topic_mastery']:
            weak_topics = sorted(
                self.user_performance['topic_mastery'].items(),
                key=lambda x: x[1]
            )
            for topic, mastery in weak_topics:
                topic_questions = [q for q in suitable_questions if q['topic'] == topic]
                if topic_questions:
                    return topic_questions[0]
        
        # Return random question from suitable ones
        return suitable_questions[0] if suitable_questions else None
    
    def update_difficulty(self):
        """Decide if difficulty should increase or decrease"""
        
        # Difficulty increase logic
        if self.user_performance['current_streak'] >= 3:
            if self.user_performance['difficulty_level'] < 5:
                self.user_performance['difficulty_level'] += 1
                print(f"🎉 Difficulty increased to level {self.user_performance['difficulty_level']}")
                return "increased"
        
        # Difficulty decrease logic
        elif self.user_performance['wrong_answers'] >= 2:
            # Check consecutive wrong answers
            last_two = self.user_performance['question_history'][-2:]
            if len(last_two) == 2 and not last_two[0]['is_correct'] and not last_two[1]['is_correct']:
                if self.user_performance['difficulty_level'] > 1:
                    self.user_performance['difficulty_level'] -= 1
                    print(f"📉 Difficulty decreased to level {self.user_performance['difficulty_level']}")
                    return "decreased"
        
        return "unchanged"
    
    def should_stop(self, user_input=None):
        """Determine if conversation/session should end"""
        
        # Check for explicit stop command
        if user_input and user_input.lower() in ['quit', 'exit', 'stop', 'end']:
            return True, "User requested to stop"
        
        # Check performance-based stopping
        if self.user_performance['correct_answers'] >= 10:
            return True, "Achieved target of 10 correct answers"
        
        # Check if user is struggling too much
        if self.user_performance['wrong_answers'] >= 5 and \
           self.user_performance['correct_answers'] == 0:
            return True, "User needs remedial training first"
        
        # Check session length
        if len(self.user_performance['question_history']) >= 20:
            return True, "Maximum session length reached"
        
        return False, None
    
    def get_next_action(self, user_answer, correct_answer, available_questions):
        """Main decision method - coordinates everything"""
        
        # Step 1: Evaluate answer
        is_correct = self.evaluate_answer(user_answer, correct_answer)
        
        # Step 2: Update difficulty level
        difficulty_change = self.update_difficulty()
        
        # Step 3: Check if we should stop
        should_end, reason = self.should_stop()
        
        if should_end:
            return {
                'action': 'stop',
                'reason': reason,
                'performance_summary': self.get_performance_summary()
            }
        
        # Step 4: Decide next question
        next_question = self.decide_next_question(available_questions)
        
        # Step 5: Update topic mastery
        self.update_topic_mastery(correct_answer)
        
        return {
            'action': 'next_question',
            'is_correct': is_correct,
            'difficulty_change': difficulty_change,
            'next_question': next_question,
            'current_difficulty': self.user_performance['difficulty_level'],
            'performance': self.get_performance_summary()
        }
    
    def update_topic_mastery(self, question_topic):
        """Track mastery per topic"""
        if question_topic not in self.user_performance['topic_mastery']:
            self.user_performance['topic_mastery'][question_topic] = 0
        
        # Simple mastery scoring (can be more sophisticated)
        recent_correct = sum(1 for q in self.user_performance['question_history'][-5:] 
                            if q['is_correct'])
        mastery_score = recent_correct / min(5, len(self.user_performance['question_history']))
        self.user_performance['topic_mastery'][question_topic] = mastery_score
    
    def get_performance_summary(self):
        """Generate performance summary"""
        total = self.user_performance['correct_answers'] + self.user_performance['wrong_answers']
        accuracy = (self.user_performance['correct_answers'] / total * 100) if total > 0 else 0
        
        return {
            'correct': self.user_performance['correct_answers'],
            'wrong': self.user_performance['wrong_answers'],
            'accuracy': f"{accuracy:.1f}%",
            'current_streak': self.user_performance['current_streak'],
            'difficulty_level': self.user_performance['difficulty_level'],
            'total_questions': total
        }