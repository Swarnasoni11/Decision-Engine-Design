# main_system.py - Complete Integration

from decision_engine import DecisionEngine
from ai_decision_engine import AIDecisionEngine
from datetime import datetime
import json

class AdaptiveLearningSystem:
    def __init__(self, use_ai=False):
        self.use_ai = use_ai
        if use_ai:
            self.decision_engine = AIDecisionEngine()
        else:
            self.decision_engine = DecisionEngine()
        
        self.question_bank = self.load_question_bank()
        self.session_log = []
        
    def load_question_bank(self):
        """Load your question database"""
        return [
            {
                'id': 1,
                'text': 'What is 2 + 2?',
                'correct_answer': '4',
                'difficulty': 1,
                'topic': 'basic_arithmetic',
                'prerequisites': []
            },
            {
                'id': 2,
                'text': 'What is 10 - 3?',
                'correct_answer': '7',
                'difficulty': 1,
                'topic': 'basic_arithmetic',
                'prerequisites': []
            },
            {
                'id': 3,
                'text': 'What is 15 × 4?',
                'correct_answer': '60',
                'difficulty': 2,
                'topic': 'multiplication',
                'prerequisites': ['basic_arithmetic']
            },
            {
                'id': 4,
                'text': 'What is 144 ÷ 12?',
                'correct_answer': '12',
                'difficulty': 3,
                'topic': 'division',
                'prerequisites': ['multiplication']
            },
            # Add more questions
        ]
    
    def run_session(self):
        """Main loop for running an interactive session"""
        print("=" * 50)
        print("🤖 Adaptive Learning System Started")
        print("Type 'quit' to exit at any time")
        print("=" * 50)
        
        current_question = self.get_starting_question()
        
        while True:
            # Present question
            print(f"\n📝 Question (Difficulty: {current_question['difficulty']}):")
            print(f"{current_question['text']}")
            user_answer = input("\nYour answer: ").strip()
            
            # Check for exit command
            should_end, reason = self.decision_engine.should_stop(user_answer)
            if should_end:
                print(f"\n🛑 Session ending: {reason}")
                self.display_final_report()
                break
            
            # Get decision from engine
            decision = self.decision_engine.get_next_action(
                user_answer, 
                current_question['correct_answer'],
                self.get_questions_by_difficulty()
            )
            
            # Provide feedback
            if decision['is_correct']:
                print("✅ Correct!")
            else:
                print(f"❌ Incorrect. The correct answer is: {current_question['correct_answer']}")
            
            # Show difficulty change
            if decision['difficulty_change'] != 'unchanged':
                print(f"📊 Difficulty: {decision['difficulty_change']}")
            
            # Show current stats
            perf = decision['performance']
            print(f"📈 Stats: {perf['correct']}/{perf['total_questions']} correct "
                  f"({perf['accuracy']}) | Streak: {perf['current_streak']}")
            
            # Log session data
            self.log_interaction(current_question, user_answer, decision)
            
            # Get next question
            if decision['action'] == 'next_question':
                current_question = decision['next_question']
                if not current_question:
                    print("\n✅ No more questions available! Session complete.")
                    break
            else:
                break
    
    def get_starting_question(self):
        """Get first question (difficulty 1)"""
        questions = [q for q in self.question_bank if q['difficulty'] == 1]
        return questions[0] if questions else None
    
    def get_questions_by_difficulty(self):
        """Get all available questions"""
        return self.question_bank
    
    def log_interaction(self, question, user_answer, decision):
        """Log session data for analysis"""
        self.session_log.append({
            'timestamp': datetime.now().isoformat(),
            'question': question,
            'user_answer': user_answer,
            'decision': decision
        })
    
    def display_final_report(self):
        """Display session summary"""
        print("\n" + "=" * 50)
        print("📊 FINAL SESSION REPORT")
        print("=" * 50)
        
        total_questions = len(self.session_log)
        correct_count = sum(1 for log in self.session_log if log['decision']['is_correct'])
        
        print(f"Total Questions: {total_questions}")
        print(f"Correct Answers: {correct_count}")
        print(f"Accuracy: {(correct_count/total_questions*100):.1f}%")
        
        if self.session_log:
            final_perf = self.session_log[-1]['decision']['performance']
            print(f"Final Difficulty Level: {final_perf['difficulty_level']}")
            print(f"Final Streak: {final_perf['current_streak']}")
        
        # Save log to file
        with open(f"session_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json", 'w') as f:
            json.dump(self.session_log, f, indent=2)
        print("\n💾 Session log saved to file")

# Run the system
if __name__ == "__main__":
    # Choose rule-based or AI-based
    system = AdaptiveLearningSystem(use_ai=False)  # Start with rule-based
    system.run_session()