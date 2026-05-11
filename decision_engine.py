"""
decision_engine.py
Task 6 — Decision Engine Design for Adaptive Interview System

Architecture:
  - Rule-based layer  : difficulty escalation / de-escalation, stopping conditions
  - AI-based layer    : LLM scores free-text answers (correctness + depth + clarity)
  - SessionState      : tracks all context between questions
"""

import json
import random
import logging
from dataclasses import dataclass, field
from typing import Literal

import anthropic  # pip install anthropic

# ─── Logging setup ─────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("DecisionEngine")

Difficulty = Literal["easy", "medium", "hard"]

DIFFICULTY_ORDER = {"easy": 0, "medium": 1, "hard": 2}


# ─── Data Models ───────────────────────────────────────────────────────────────

@dataclass
class Question:
    id: str
    topic: str
    text: str
    difficulty: Difficulty
    ideal_answer: str = ""          # used as reference for AI scoring


@dataclass
class AnswerEval:
    """Structured result from AI scorer."""
    correctness: float              # 0.0 – 1.0
    depth: float                    # 0.0 – 1.0
    clarity: float                  # 0.0 – 1.0
    overall: float                  # weighted average
    reason: str                     # short LLM explanation


@dataclass
class SessionState:
    questions_asked: list[Question] = field(default_factory=list)
    evaluations: list[AnswerEval]   = field(default_factory=list)
    current_difficulty: Difficulty  = "easy"
    streak: int      = 0            # consecutive correct (score >= threshold)
    fail_streak: int = 0            # consecutive incorrect
    hard_correct: int = 0           # correct answers specifically at hard level
    decision_log: list[str] = field(default_factory=list)

    def log(self, msg: str, level: str = "info"):
        self.decision_log.append(f"[{level.upper()}] {msg}")
        getattr(logger, level)(msg)


# ─── AI Scorer ─────────────────────────────────────────────────────────────────

class AIScorer:
    """
    Uses Claude to score a candidate's free-text answer on three axes:
      - correctness : factually accurate?
      - depth       : does it go beyond surface level?
      - clarity     : is it well-explained?
    Returns a normalized AnswerEval.
    """

    SCORE_WEIGHTS = {"correctness": 0.5, "depth": 0.3, "clarity": 0.2}

    def __init__(self, model: str = "claude-sonnet-4-20250514"):
        self.client = anthropic.Anthropic()   # reads ANTHROPIC_API_KEY from env
        self.model = model

    def score(self, question: Question, candidate_answer: str) -> AnswerEval:
        prompt = f"""You are an expert technical interviewer evaluating a candidate's answer.

Question: {question.text}
Ideal answer (reference only): {question.ideal_answer or "Not provided"}
Candidate answer: {candidate_answer}

Score the candidate on THREE dimensions, each from 0.0 to 1.0:
  - correctness : Is the answer factually accurate?
  - depth       : Does it show deep understanding beyond surface facts?
  - clarity     : Is the explanation clear and well-structured?

Respond ONLY with a valid JSON object, no extra text:
{{
  "correctness": <float 0.0-1.0>,
  "depth": <float 0.0-1.0>,
  "clarity": <float 0.0-1.0>,
  "reason": "<one sentence explanation>"
}}"""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=300,
                messages=[{"role": "user", "content": prompt}]
            )
            raw = response.content[0].text.strip()
            data = json.loads(raw)

            c = float(data["correctness"])
            d = float(data["depth"])
            cl = float(data["clarity"])
            overall = (
                c  * self.SCORE_WEIGHTS["correctness"] +
                d  * self.SCORE_WEIGHTS["depth"] +
                cl * self.SCORE_WEIGHTS["clarity"]
            )

            return AnswerEval(
                correctness=round(c, 2),
                depth=round(d, 2),
                clarity=round(cl, 2),
                overall=round(overall, 2),
                reason=data.get("reason", "")
            )

        except (json.JSONDecodeError, KeyError, anthropic.APIError) as e:
            logger.warning(f"AI scorer fallback due to error: {e}")
            # Graceful fallback — don't crash the session
            return AnswerEval(0.5, 0.5, 0.5, 0.5, "Scoring unavailable — default applied")


# ─── Decision Engine ───────────────────────────────────────────────────────────

class DecisionEngine:
    """
    All 'thinking logic' lives here.
    Three responsibilities:
      1. next_question      — select question based on current state
      2. update_difficulty  — rule-based escalation / de-escalation
      3. should_stop        — multi-condition stopping logic
    """

    # ── Tunable rules ──
    CORRECT_THRESHOLD = 0.6     # overall score >= this → "correct"
    STREAK_UP         = 2       # consecutive correct → harder
    STREAK_DOWN       = 2       # consecutive wrong   → easier
    MAX_QUESTIONS     = 10      # hard cap
    MASTERY_HARD      = 3       # correct at hard → mastery → stop
    GIVE_UP_EASY      = 3       # wrong at easy   → struggling → stop

    def __init__(self, question_bank: list[Question]):
        self.bank = question_bank
        self._used_ids: set[str] = set()

    # ── 1. Next Question ──────────────────────────────────────────────────────

    def next_question(self, state: SessionState) -> Question | None:
        """
        Rule: prefer unseen questions at current difficulty.
        Fallback: if exhausted, reset seen set and resample.
        """
        pool = [
            q for q in self.bank
            if q.difficulty == state.current_difficulty
            and q.id not in self._used_ids
        ]

        if not pool:
            state.log("Question pool exhausted — resetting seen IDs", "warning")
            self._used_ids = {
                q.id for q in self.bank
                if q.difficulty != state.current_difficulty
            }
            pool = [q for q in self.bank if q.difficulty == state.current_difficulty]

        if not pool:
            return None

        chosen = random.choice(pool)
        self._used_ids.add(chosen.id)
        state.log(f"Selected Q '{chosen.id}' [{chosen.difficulty}] — topic: {chosen.topic}")
        return chosen

    # ── 2. Difficulty Update ──────────────────────────────────────────────────

    def update_difficulty(self, state: SessionState, eval_result: AnswerEval) -> None:
        """
        Rule-based difficulty adjustment after each answer.
        Updates state in-place.
        """
        was_correct = eval_result.overall >= self.CORRECT_THRESHOLD

        if was_correct:
            state.streak += 1
            state.fail_streak = 0
            if state.current_difficulty == "hard":
                state.hard_correct += 1
        else:
            state.fail_streak += 1
            state.streak = 0

        old = state.current_difficulty

        # Escalate
        if state.streak >= self.STREAK_UP:
            if old == "easy":
                state.current_difficulty = "medium"
            elif old == "medium":
                state.current_difficulty = "hard"
            state.streak = 0
            state.fail_streak = 0

        # De-escalate
        elif state.fail_streak >= self.STREAK_DOWN:
            if old == "hard":
                state.current_difficulty = "medium"
            elif old == "medium":
                state.current_difficulty = "easy"
            state.streak = 0
            state.fail_streak = 0

        if state.current_difficulty != old:
            direction = "↑ increased" if (
                DIFFICULTY_ORDER[state.current_difficulty] > DIFFICULTY_ORDER[old]
            ) else "↓ decreased"
            state.log(f"Difficulty {direction}: {old} → {state.current_difficulty}")
        else:
            state.log(
                f"Difficulty unchanged [{old}] | streak={state.streak} fail_streak={state.fail_streak}"
            )

    # ── 3. Stopping Condition ─────────────────────────────────────────────────

    def should_stop(self, state: SessionState) -> tuple[bool, str]:
        """
        Checks multiple stopping rules in priority order.
        Returns (stop: bool, reason: str).
        """
        n = len(state.questions_asked)

        if n >= self.MAX_QUESTIONS:
            return True, f"Max questions reached ({self.MAX_QUESTIONS})"

        if state.hard_correct >= self.MASTERY_HARD:
            return True, f"Mastery detected — {self.MASTERY_HARD} correct at hard level"

        if (state.fail_streak >= self.GIVE_UP_EASY
                and state.current_difficulty == "easy"):
            return True, f"Candidate struggling — {self.GIVE_UP_EASY} consecutive wrong at easy"

        return False, ""


# ─── Session Runner ────────────────────────────────────────────────────────────

def run_session(engine: DecisionEngine, scorer: AIScorer):
    state = SessionState()
    print("\n" + "="*50)
    print("  Adaptive Interview Session — Decision Engine")
    print("="*50 + "\n")

    while True:
        stop, reason = engine.should_stop(state)
        if stop:
            print(f"\n{'─'*50}")
            print(f"  Session ended: {reason}")
            break

        q = engine.next_question(state)
        if q is None:
            print("No more questions available.")
            break

        state.questions_asked.append(q)
        n = len(state.questions_asked)
        diff_label = state.current_difficulty.upper()

        print(f"\nQ{n} [{diff_label}] ({q.topic})")
        print(f"  {q.text}")
        answer = input("  Your answer: ").strip()

        if not answer:
            answer = "I don't know"

        print("  Scoring your answer...")
        eval_result = scorer.score(q, answer)
        state.evaluations.append(eval_result)

        correct_str = "✓ Correct" if eval_result.overall >= engine.CORRECT_THRESHOLD else "✗ Incorrect"
        print(f"  Overall: {eval_result.overall:.2f} ({correct_str})")
        print(f"  Correctness={eval_result.correctness:.2f}  "
              f"Depth={eval_result.depth:.2f}  "
              f"Clarity={eval_result.clarity:.2f}")
        print(f"  Feedback: {eval_result.reason}")

        engine.update_difficulty(state, eval_result)

    # ── Final Summary ──
    print("\n" + "="*50)
    print("  RESULTS")
    print("="*50)
    if state.evaluations:
        avg = sum(e.overall for e in state.evaluations) / len(state.evaluations)
        avg_c = sum(e.correctness for e in state.evaluations) / len(state.evaluations)
        avg_d = sum(e.depth for e in state.evaluations) / len(state.evaluations)
        avg_cl = sum(e.clarity for e in state.evaluations) / len(state.evaluations)
        print(f"  Questions answered : {len(state.questions_asked)}")
        print(f"  Avg overall score  : {avg:.2f}")
        print(f"  Avg correctness    : {avg_c:.2f}")
        print(f"  Avg depth          : {avg_d:.2f}")
        print(f"  Avg clarity        : {avg_cl:.2f}")
        print(f"  Final difficulty   : {state.current_difficulty}")
        print(f"\n  Decision log ({len(state.decision_log)} entries):")
        for entry in state.decision_log:
            print(f"    {entry}")
    print("="*50 + "\n")


# ─── Sample Question Bank + Entry Point ───────────────────────────────────────

SAMPLE_BANK = [
    Question("e1", "ML Basics",    "What is supervised learning?",              "easy",
             "Learning from labeled input-output pairs to predict outputs on new data."),
    Question("e2", "ML Basics",    "What is the difference between a parameter and a hyperparameter?", "easy",
             "Parameters are learned during training; hyperparameters are set before training."),
    Question("e3", "Python",       "What does a list comprehension do in Python?","easy",
             "Creates a new list by applying an expression to each element of an iterable."),
    Question("m1", "ML Concepts",  "Explain overfitting and two ways to prevent it.", "medium",
             "Overfitting = model memorizes training data. Prevent with regularization and dropout."),
    Question("m2", "Deep Learning","What is backpropagation?",                  "medium",
             "Algorithm to compute gradients of the loss w.r.t. weights using the chain rule."),
    Question("m3", "ML Concepts",  "Why do we need cross-validation?",          "medium",
             "To get an unbiased estimate of model performance on unseen data."),
    Question("h1", "ML Theory",    "Explain the bias-variance tradeoff.",        "hard",
             "High bias = underfitting; high variance = overfitting. Must balance both."),
    Question("h2", "Optimization", "Why does SGD generalize better than full-batch GD?", "hard",
             "Noise in SGD acts as regularization, helping escape sharp minima."),
    Question("h3", "Deep Learning","What problem does attention solve in Transformers?", "hard",
             "Captures long-range dependencies without the vanishing gradient of RNNs."),
]

if __name__ == "__main__":
    engine = DecisionEngine(SAMPLE_BANK)
    scorer = AIScorer()
    run_session(engine, scorer)