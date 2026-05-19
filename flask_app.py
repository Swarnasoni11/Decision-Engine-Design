from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from decision_engine import DecisionEngine
import json

app = Flask(__name__)
CORS(app)

# Store sessions in memory (use Redis/DB in production)
sessions = {}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/start_session', methods=['POST'])
def start_session():
    session_id = request.json.get('session_id', 'default')
    sessions[session_id] = {
        'engine': DecisionEngine(),
        'current_question': None,
        'history': []
    }
    
    # Get first question
    question = get_starting_question()
    sessions[session_id]['current_question'] = question
    
    return jsonify({
        'success': True,
        'question': question,
        'performance': sessions[session_id]['engine'].get_performance_summary()
    })

@app.route('/api/submit_answer', methods=['POST'])
def submit_answer():
    data = request.json
    session_id = data.get('session_id', 'default')
    user_answer = data.get('answer')
    current_question = data.get('question')
    
    if session_id not in sessions:
        return jsonify({'error': 'Session not found'}, 404)
    
    session = sessions[session_id]
    engine = session['engine']
    
    # Get available questions
    available_questions = get_questions_by_difficulty(
        engine.user_performance['difficulty_level']
    )
    
    # Process decision
    decision = engine.get_next_action(
        user_answer,
        current_question['correct_answer'],
        available_questions
    )
    
    # Update session
    session['history'].append({
        'question': current_question,
        'answer': user_answer,
        'decision': decision
    })
    
    if decision['next_question']:
        session['current_question'] = decision['next_question']
    
    return jsonify({
        'success': True,
        'decision': decision,
        'next_question': decision['next_question'],
        'performance': engine.get_performance_summary(),
        'session_active': decision['action'] != 'stop'
    })

def get_starting_question():
    questions = [q for q in QUESTION_BANK if q['difficulty'] == 1]
    return questions[0] if questions else None

def get_questions_by_difficulty(difficulty):
    return [q for q in QUESTION_BANK if q['difficulty'] == difficulty]

# Same QUESTION_BANK as before
QUESTION_BANK = [
    {
        'id': 1,
        'text': 'What is 2 + 2?',
        'correct_answer': '4',
        'difficulty': 1,
        'topic': 'basic_arithmetic',
        'explanation': '2 + 2 equals 4. This is basic addition!'
    },
    # Add more questions...
]

if __name__ == '__main__':
    app.run(debug=True, port=5000)