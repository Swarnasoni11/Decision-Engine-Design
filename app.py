import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import random

# Page config
st.set_page_config(
    page_title="AI Learning Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .stButton > button {
        width: 100%;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        padding: 10px;
        font-size: 16px;
    }
    .stButton > button:hover {
        transform: translateY(-2px);
        transition: all 0.3s;
    }
    .css-1y4p8pa {
        padding: 2rem;
        border-radius: 1rem;
        background: linear-gradient(135deg, #667eea15 0%, #764ba215 100%);
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'session_active' not in st.session_state:
    st.session_state.session_active = False
    st.session_state.current_question = None
    st.session_state.question_number = 0
    st.session_state.correct_count = 0
    st.session_state.wrong_count = 0
    st.session_state.current_streak = 0
    st.session_state.difficulty_level = 1
    st.session_state.history = []
    st.session_state.answer_submitted = False
    st.session_state.feedback_shown = False
    st.session_state.user_answer = ""
    st.session_state.session_complete = False

# Comprehensive question bank
QUESTION_BANK = [
    # Difficulty 1 - Beginner
    {'id': 1, 'text': 'What is 2 + 2?', 'correct_answer': '4', 'difficulty': 1, 'topic': 'Basic Addition', 'explanation': '2 + 2 equals 4. This is basic addition!'},
    {'id': 2, 'text': 'What is 10 - 3?', 'correct_answer': '7', 'difficulty': 1, 'topic': 'Basic Subtraction', 'explanation': '10 minus 3 equals 7. Subtraction means taking away.'},
    {'id': 3, 'text': 'What is 5 × 2?', 'correct_answer': '10', 'difficulty': 1, 'topic': 'Basic Multiplication', 'explanation': '5 multiplied by 2 equals 10.'},
    {'id': 4, 'text': 'What is 8 ÷ 2?', 'correct_answer': '4', 'difficulty': 1, 'topic': 'Basic Division', 'explanation': '8 divided by 2 equals 4.'},
    
    # Difficulty 2 - Easy
    {'id': 5, 'text': 'What is 15 × 4?', 'correct_answer': '60', 'difficulty': 2, 'topic': 'Multiplication', 'explanation': '15 × 4 = 60. Multiply 15 by 4 to get 60.'},
    {'id': 6, 'text': 'What is 100 - 37?', 'correct_answer': '63', 'difficulty': 2, 'topic': 'Subtraction', 'explanation': '100 - 37 = 63. Subtract 37 from 100.'},
    {'id': 7, 'text': 'Solve: 8 × (3 + 2)', 'correct_answer': '40', 'difficulty': 2, 'topic': 'Order of Operations', 'explanation': 'First parentheses: 3+2=5, then multiply: 8×5=40'},
    
    # Difficulty 3 - Intermediate
    {'id': 8, 'text': 'What is 144 ÷ 12?', 'correct_answer': '12', 'difficulty': 3, 'topic': 'Division', 'explanation': '144 ÷ 12 = 12. 12 × 12 = 144.'},
    {'id': 9, 'text': 'What is 25% of 80?', 'correct_answer': '20', 'difficulty': 3, 'topic': 'Percentages', 'explanation': '25% means 25/100 = 0.25, so 0.25 × 80 = 20'},
    
    # Difficulty 4 - Advanced
    {'id': 10, 'text': 'What is √144?', 'correct_answer': '12', 'difficulty': 4, 'topic': 'Square Roots', 'explanation': 'Square root of 144 is 12 because 12 × 12 = 144'},
    
    # Difficulty 5 - Expert
    {'id': 11, 'text': 'What is 3² × 2³?', 'correct_answer': '72', 'difficulty': 5, 'topic': 'Exponents', 'explanation': '3² = 9, 2³ = 8, 9 × 8 = 72'}
]

def get_questions_by_difficulty(difficulty):
    """Get questions for current difficulty level"""
    return [q for q in QUESTION_BANK if q['difficulty'] == difficulty]

def get_next_question():
    """Get next question based on difficulty and history"""
    available = get_questions_by_difficulty(st.session_state.difficulty_level)
    
    # Filter out already answered questions
    answered_ids = [h['question_id'] for h in st.session_state.history]
    available = [q for q in available if q['id'] not in answered_ids]
    
    if available:
        return random.choice(available)
    
    # If no questions at current difficulty, move up
    if st.session_state.difficulty_level < 5:
        st.session_state.difficulty_level += 1
        return get_next_question()
    
    return None

def update_difficulty(is_correct):
    """Update difficulty based on performance"""
    if is_correct:
        st.session_state.current_streak += 1
        st.session_state.correct_count += 1
        
        # Increase difficulty after 3 correct in a row
        if st.session_state.current_streak >= 3 and st.session_state.difficulty_level < 5:
            st.session_state.difficulty_level += 1
            st.session_state.current_streak = 0
            return "increased"
    else:
        st.session_state.current_streak = 0
        st.session_state.wrong_count += 1
        
        # Decrease difficulty after 2 wrong in a row
        if len(st.session_state.history) >= 2:
            last_two = st.session_state.history[-2:]
            if not last_two[0]['was_correct'] and not last_two[1]['was_correct']:
                if st.session_state.difficulty_level > 1:
                    st.session_state.difficulty_level -= 1
                    return "decreased"
    return "unchanged"

def process_answer():
    """Process the user's answer"""
    if not st.session_state.user_answer:
        st.warning("Please enter an answer!")
        return False
    
    current_q = st.session_state.current_question
    
    # Check if answer is correct (case-insensitive)
    is_correct = st.session_state.user_answer.strip().lower() == current_q['correct_answer'].lower()
    
    # Update difficulty
    diff_change = update_difficulty(is_correct)
    
    # Save to history
    st.session_state.history.append({
        'question_id': current_q['id'],
        'question_text': current_q['text'],
        'user_answer': st.session_state.user_answer,
        'correct_answer': current_q['correct_answer'],
        'was_correct': is_correct,
        'difficulty': current_q['difficulty'],
        'topic': current_q['topic'],
        'timestamp': datetime.now()
    })
    
    # Store feedback
    st.session_state.feedback = {
        'is_correct': is_correct,
        'explanation': current_q['explanation'],
        'correct_answer': current_q['correct_answer'],
        'difficulty_change': diff_change
    }
    
    # Get next question
    next_q = get_next_question()
    
    if next_q is None:
        st.session_state.session_complete = True
        st.session_state.session_active = False
    else:
        st.session_state.current_question = next_q
    
    st.session_state.answer_submitted = True
    st.session_state.user_answer = ""  # Reset answer
    
    return True

def start_new_session():
    """Start a fresh session"""
    st.session_state.session_active = True
    st.session_state.session_complete = False
    st.session_state.question_number = 0
    st.session_state.correct_count = 0
    st.session_state.wrong_count = 0
    st.session_state.current_streak = 0
    st.session_state.difficulty_level = 1
    st.session_state.history = []
    st.session_state.answer_submitted = False
    st.session_state.feedback_shown = False
    st.session_state.user_answer = ""
    
    # Get first question
    first_question = get_questions_by_difficulty(1)[0]
    st.session_state.current_question = first_question

def reset_for_next_question():
    """Reset flags for next question"""
    st.session_state.answer_submitted = False
    st.session_state.feedback_shown = False

# Main UI
st.title("🤖 AI Learning Assistant")
st.markdown("*Adaptive Learning System with Intelligent Decision Engine*")

# Sidebar with stats
with st.sidebar:
    st.markdown("## 📊 Performance Dashboard")
    
    if st.session_state.session_active and not st.session_state.session_complete:
        total_questions = len(st.session_state.history)
        accuracy = (st.session_state.correct_count / total_questions * 100) if total_questions > 0 else 0
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("✅ Correct", st.session_state.correct_count)
            st.metric("🔥 Streak", st.session_state.current_streak)
        with col2:
            st.metric("❌ Wrong", st.session_state.wrong_count)
            st.metric("⭐ Difficulty", f"Lvl {st.session_state.difficulty_level}")
        
        st.progress(accuracy/100, text=f"🎯 Accuracy: {accuracy:.1f}%")
        
        # Topic mastery
        if st.session_state.history:
            st.markdown("### 📚 Topic Performance")
            topics = {}
            for h in st.session_state.history:
                if h['topic'] not in topics:
                    topics[h['topic']] = {'correct': 0, 'total': 0}
                topics[h['topic']]['total'] += 1
                if h['was_correct']:
                    topics[h['topic']]['correct'] += 1
            
            for topic, stats in topics.items():
                mastery = (stats['correct'] / stats['total'] * 100)
                st.text(f"{topic}: {mastery:.0f}%")
                st.progress(mastery/100)
        
        # Recent history
        if st.session_state.history:
            st.markdown("### 📝 Recent Answers")
            recent = st.session_state.history[-5:]
            for item in reversed(recent):
                icon = "✅" if item['was_correct'] else "❌"
                st.text(f"{icon} {item['question_text'][:30]}...")
    
    elif st.session_state.session_complete:
        st.success("🎉 Session Complete!")
        total = len(st.session_state.history)
        accuracy = (st.session_state.correct_count / total * 100) if total > 0 else 0
        st.metric("Final Accuracy", f"{accuracy:.1f}%")
        st.metric("Questions Attempted", total)
        st.metric("Highest Difficulty", f"Lvl {st.session_state.difficulty_level}")

# Main content area
if not st.session_state.session_active and not st.session_state.session_complete:
    # Welcome screen
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("""
        ### 🎓 Welcome to AI Learning Assistant!
        
        This intelligent system adapts to your learning pace:
        
        - 📈 **Smart Difficulty** - Questions adjust based on your performance
        - 🎯 **Focused Learning** - Concentrates on topics you find challenging
        - ⚡ **Real-time Feedback** - Instant explanations for every answer
        - 🔥 **Streak System** - Stay motivated with correct answer streaks
        
        **Ready to begin your learning journey?**
        """)
        
        if st.button("🚀 Start New Session", use_container_width=True):
            start_new_session()
            st.rerun()

elif st.session_state.session_active:
    # Active quiz session
    if not st.session_state.answer_submitted:
        # Show question
        current_q = st.session_state.current_question
        
        # Question card
        with st.container():
            st.markdown("---")
            col1, col2, col3 = st.columns([1, 3, 1])
            with col2:
                st.markdown(f"""
                <div style='text-align: center; padding: 2rem; background: linear-gradient(135deg, #667eea15 0%, #764ba215 100%); border-radius: 1rem;'>
                    <h3>Question {len(st.session_state.history) + 1}</h3>
                    <h2 style='margin: 2rem 0;'>{current_q['text']}</h2>
                    <div>
                        <span style='background: #{["28a745", "17a2b8", "ffc107", "fd7e14", "dc3545"][current_q['difficulty']-1]}; 
                                     color: white; padding: 0.3rem 1rem; border-radius: 20px; margin: 0 0.5rem;'>
                            Difficulty: {'⭐' * current_q['difficulty']}
                        </span>
                        <span style='background: #6c757d; color: white; padding: 0.3rem 1rem; border-radius: 20px;'>
                            Topic: {current_q['topic']}
                        </span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                st.markdown("<br>", unsafe_allow_html=True)
                
                # Answer input
                user_answer = st.text_input("**Your Answer:**", key="answer", 
                                           placeholder="Type your answer here...")
                
                col_a, col_b, col_c = st.columns([1, 2, 1])
                with col_b:
                    if st.button("📝 Submit Answer", use_container_width=True):
                        st.session_state.user_answer = user_answer
                        if process_answer():
                            st.rerun()
    
    else:
        # Show feedback
        feedback = st.session_state.feedback
        
        if feedback['is_correct']:
            st.success(f"""
            ### ✅ Correct!
            
            {feedback['explanation']}
            """)
        else:
            st.error(f"""
            ### ❌ Incorrect
            
            **Correct answer:** {feedback['correct_answer']}
            
            {feedback['explanation']}
            """)
        
        # Show difficulty change
        if feedback['difficulty_change'] == 'increased':
            st.balloons()
            st.info(f"🎉 Great job! Difficulty increased to Level {st.session_state.difficulty_level}")
        elif feedback['difficulty_change'] == 'decreased':
            st.warning(f"📚 Difficulty decreased to Level {st.session_state.difficulty_level} for better learning")
        
        # Performance preview
        total = len(st.session_state.history)
        accuracy = (st.session_state.correct_count / total * 100)
        st.markdown(f"""
        <div style='background: #f0f2f6; padding: 1rem; border-radius: 0.5rem; margin: 1rem 0;'>
            <strong>📊 Current Performance:</strong> {st.session_state.correct_count}/{total} correct ({accuracy:.0f}%) | 
            🔥 Streak: {st.session_state.current_streak} | ⭐ Difficulty: Level {st.session_state.difficulty_level}
        </div>
        """, unsafe_allow_html=True)
        
        # Next question button
        if st.button("➡️ Next Question", use_container_width=True):
            reset_for_next_question()
            st.rerun()

elif st.session_state.session_complete:
    # Completion screen
    st.markdown("## 🎉 Congratulations! Session Complete!")
    
    total = len(st.session_state.history)
    accuracy = (st.session_state.correct_count / total * 100) if total > 0 else 0
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Questions", total)
    with col2:
        st.metric("Correct Answers", st.session_state.correct_count)
    with col3:
        st.metric("Accuracy", f"{accuracy:.1f}%")
    with col4:
        st.metric("Max Difficulty", f"Level {st.session_state.difficulty_level}")
    
    # Progress chart
    if st.session_state.history:
        df = pd.DataFrame(st.session_state.history)
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=list(range(1, len(df)+1)),
            y=[1 if x else 0 for x in df['was_correct']],
            mode='lines+markers',
            name='Performance',
            line=dict(color='green', width=2),
            marker=dict(size=10, color=['green' if x else 'red' for x in df['was_correct']])
        ))
        fig.update_layout(
            title="Your Learning Journey",
            xaxis_title="Question Number",
            yaxis_title="Result (1=Correct, 0=Wrong)",
            height=300
        )
        st.plotly_chart(fig, use_container_width=True)
    
    if st.button("🔄 Start New Session", use_container_width=True):
        start_new_session()
        st.rerun()

# Footer
st.markdown("---")
st.markdown("<p style='text-align: center; color: #666;'>🤖 AI Learning Assistant | Powered by Adaptive Decision Engine</p>", unsafe_allow_html=True)