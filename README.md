# Adaptive AI Quiz & Decision Engine

An intelligent AI-powered assessment system that dynamically adjusts question difficulty, evaluates user responses, and determines the next question using a Decision Engine. This project demonstrates how AI can be used to create adaptive learning and interview platforms.

---

## Project Overview

Traditional quiz systems ask fixed questions regardless of user performance. This project introduces a Decision Engine that continuously analyzes user responses and adapts the assessment process in real time.

The system:

- Evaluates user answers
- Tracks performance metrics
- Adjusts question difficulty
- Selects the next appropriate question
- Stops assessment based on predefined conditions

---

## Objectives

- Build an adaptive assessment platform
- Design a rule-based and AI-based decision engine
- Implement intelligent answer evaluation
- Create a scalable architecture for future AI integration
- Store and analyze user performance data

---

## Features

### Adaptive Question Selection
Questions are selected dynamically based on user performance.

### Difficulty Adjustment
Difficulty increases or decreases according to accuracy and consistency.

### Answer Evaluation
Supports:
- Keyword Matching
- Semantic Similarity (NLP-Based)

### Decision Engine
Makes intelligent decisions regarding:
- Next Question
- Difficulty Level
- Session Termination

### Performance Tracking
Tracks:
- Score
- Accuracy
- Correct Streak
- Questions Attempted

### Database Integration
Stores:
- Question Bank
- User Responses
- Assessment Results

---

## System Architecture

```text
User
 ↓
Frontend (Streamlit)
 ↓
Answer Evaluation Module
 ↓
Decision Engine
 ↓
Question Selector
 ↓
Database
 ↓
Analytics & Reports
```

---

## Project Structure

```text
adaptive-ai-quiz/
│
├── data/
│   ├── questions.csv
│
├── models/
│   ├── decision_model.pkl
│
├── database/
│   ├── schema.sql
│
├── app/
│   ├── app.py
│   ├── evaluation.py
│   ├── decision_engine.py
│   ├── question_selector.py
│
├── requirements.txt
│
└── README.md
```

---

## Technologies Used

| Category | Technology |
|-----------|------------|
| Programming | Python |
| Frontend | Streamlit |
| Backend | Flask / FastAPI |
| Database | PostgreSQL / SQLite |
| Machine Learning | Scikit-Learn |
| NLP | Sentence Transformers |
| Data Handling | Pandas |
| Visualization | Matplotlib |

---

## Decision Engine Logic

The Decision Engine controls the adaptive behavior of the system.

### Difficulty Rules

```python
if correct_streak >= 3:
    difficulty = "Hard"

elif score >= 5:
    difficulty = "Medium"

else:
    difficulty = "Easy"
```

### Next Question Selection

```text
Select Question
    ↓
Match Difficulty
    ↓
Choose Unattempted Question
    ↓
Present to User
```

### Stopping Conditions

- Maximum questions reached
- Time limit exceeded
- Assessment completed
- User exits session

---

## Evaluation Methods

### Method 1: Keyword Matching

Simple answer verification using text comparison.

### Method 2: Semantic Similarity

Uses Sentence Transformers to compare meaning rather than exact wording.

Example:

```python
similarity_score = cosine_similarity(
    user_embedding,
    answer_embedding
)
```

---

## Database Design

### Questions Table

| Column | Type |
|----------|----------|
| id | Integer |
| question | Text |
| answer | Text |
| difficulty | Text |
| topic | Text |

### User Results Table

| Column | Type |
|----------|----------|
| user_id | Integer |
| score | Integer |
| difficulty | Text |
| accuracy | Float |
| questions_attempted | Integer |

---

## Future AI Enhancements

- GPT-based answer evaluation
- Personalized learning paths
- Reinforcement Learning decision engine
- Voice-based assessments
- Interview simulation mode
- Real-time analytics dashboard

---

## Sample Workflow

```text
Start Assessment
        ↓
Ask Question
        ↓
Receive Answer
        ↓
Evaluate Answer
        ↓
Update Score
        ↓
Decision Engine
        ↓
Adjust Difficulty
        ↓
Select Next Question
        ↓
Continue / Stop
```

---

## Installation

Clone repository:

```bash
git clone https://github.com/yourusername/adaptive-ai-quiz.git
```

Navigate to project:

```bash
cd adaptive-ai-quiz
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Run application:

```bash
streamlit run app.py
```

---

## Requirements

```text
streamlit
pandas
numpy
scikit-learn
sentence-transformers
matplotlib
psycopg2
```

---

## Learning Outcomes

Through this project you will learn:

- Decision Engine Design
- Adaptive Learning Systems
- Machine Learning Integration
- NLP-based Evaluation
- Database Modeling
- AI Product Development
- Full-Stack AI Application Design

---

## Author

**Swarna Soni**

AI/ML Enthusiast | Python Developer | Machine Learning Learner

---


---

If you find this project useful, consider giving it a star on GitHub.
