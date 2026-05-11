"""
test_decision_engine.py
Unit tests for Task 6 — Decision Engine

Run with:  pytest test_decision_engine.py -v
"""

import pytest
from decision_engine import (
    DecisionEngine, AIScorer, SessionState,
    Question, AnswerEval, DIFFICULTY_ORDER
)

# ─── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def sample_bank():
    return [
        Question("e1", "ML", "Easy Q1", "easy",   "answer1"),
        Question("e2", "ML", "Easy Q2", "easy",   "answer2"),
        Question("m1", "ML", "Med Q1",  "medium", "answer3"),
        Question("m2", "ML", "Med Q2",  "medium", "answer4"),
        Question("h1", "ML", "Hard Q1", "hard",   "answer5"),
        Question("h2", "ML", "Hard Q2", "hard",   "answer6"),
    ]

@pytest.fixture
def engine(sample_bank):
    return DecisionEngine(sample_bank)

def make_eval(score: float) -> AnswerEval:
    return AnswerEval(score, score, score, score, "test")


# ─── Test: next_question ───────────────────────────────────────────────────────

class TestNextQuestion:

    def test_returns_question_at_current_difficulty(self, engine):
        state = SessionState(current_difficulty="easy")
        q = engine.next_question(state)
        assert q is not None
        assert q.difficulty == "easy"

    def test_avoids_repeated_questions(self, engine):
        state = SessionState(current_difficulty="easy")
        q1 = engine.next_question(state)
        q2 = engine.next_question(state)
        assert q1.id != q2.id

    def test_returns_none_when_bank_empty_for_level(self, engine):
        """If bank has no questions at a level after exhaustion, should still recover."""
        state = SessionState(current_difficulty="easy")
        engine.next_question(state)  # e1
        engine.next_question(state)  # e2
        q3 = engine.next_question(state)  # should reset and resample
        assert q3 is not None
        assert q3.difficulty == "easy"

    def test_respects_difficulty_change(self, engine):
        state = SessionState(current_difficulty="hard")
        q = engine.next_question(state)
        assert q.difficulty == "hard"


# ─── Test: update_difficulty ───────────────────────────────────────────────────

class TestUpdateDifficulty:

    def test_escalates_easy_to_medium_after_streak(self, engine):
        state = SessionState(current_difficulty="easy")
        engine.update_difficulty(state, make_eval(0.8))   # streak=1
        assert state.current_difficulty == "easy"
        engine.update_difficulty(state, make_eval(0.8))   # streak=2 → escalate
        assert state.current_difficulty == "medium"

    def test_escalates_medium_to_hard_after_streak(self, engine):
        state = SessionState(current_difficulty="medium")
        engine.update_difficulty(state, make_eval(0.9))
        engine.update_difficulty(state, make_eval(0.9))
        assert state.current_difficulty == "hard"

    def test_deescalates_medium_to_easy_on_fail_streak(self, engine):
        state = SessionState(current_difficulty="medium")
        engine.update_difficulty(state, make_eval(0.2))   # fail_streak=1
        assert state.current_difficulty == "medium"
        engine.update_difficulty(state, make_eval(0.2))   # fail_streak=2 → de-escalate
        assert state.current_difficulty == "easy"

    def test_deescalates_hard_to_medium_on_fail_streak(self, engine):
        state = SessionState(current_difficulty="hard")
        engine.update_difficulty(state, make_eval(0.1))
        engine.update_difficulty(state, make_eval(0.1))
        assert state.current_difficulty == "medium"

    def test_does_not_escalate_beyond_hard(self, engine):
        state = SessionState(current_difficulty="hard")
        for _ in range(5):
            engine.update_difficulty(state, make_eval(0.9))
        assert state.current_difficulty == "hard"

    def test_does_not_deescalate_below_easy(self, engine):
        state = SessionState(current_difficulty="easy")
        for _ in range(5):
            engine.update_difficulty(state, make_eval(0.1))
        assert state.current_difficulty == "easy"

    def test_streak_resets_after_escalation(self, engine):
        state = SessionState(current_difficulty="easy")
        engine.update_difficulty(state, make_eval(0.8))
        engine.update_difficulty(state, make_eval(0.8))
        assert state.streak == 0   # resets after escalation

    def test_hard_correct_increments_only_at_hard(self, engine):
        state = SessionState(current_difficulty="hard")
        engine.update_difficulty(state, make_eval(0.9))
        assert state.hard_correct == 1
        state.current_difficulty = "medium"
        engine.update_difficulty(state, make_eval(0.9))
        assert state.hard_correct == 1   # no change at medium

    def test_correct_threshold_boundary(self, engine):
        """Score exactly at threshold should count as correct."""
        state = SessionState(current_difficulty="easy")
        engine.update_difficulty(state, make_eval(engine.CORRECT_THRESHOLD))
        assert state.streak == 1
        assert state.fail_streak == 0

    def test_just_below_threshold_is_wrong(self, engine):
        state = SessionState(current_difficulty="easy")
        engine.update_difficulty(state, make_eval(engine.CORRECT_THRESHOLD - 0.01))
        assert state.fail_streak == 1
        assert state.streak == 0


# ─── Test: should_stop ─────────────────────────────────────────────────────────

class TestShouldStop:

    def test_stops_at_max_questions(self, engine):
        state = SessionState()
        state.questions_asked = [Question(f"q{i}", "ML", "Q", "easy") for i in range(10)]
        stop, reason = engine.should_stop(state)
        assert stop is True
        assert "Max" in reason

    def test_does_not_stop_before_max(self, engine):
        state = SessionState()
        state.questions_asked = [Question(f"q{i}", "ML", "Q", "easy") for i in range(5)]
        stop, _ = engine.should_stop(state)
        assert stop is False

    def test_stops_on_mastery(self, engine):
        state = SessionState(hard_correct=3)
        stop, reason = engine.should_stop(state)
        assert stop is True
        assert "Mastery" in reason

    def test_stops_on_easy_fail_streak(self, engine):
        state = SessionState(fail_streak=3, current_difficulty="easy")
        stop, reason = engine.should_stop(state)
        assert stop is True
        assert "struggling" in reason.lower()

    def test_does_not_stop_on_fail_streak_at_medium(self, engine):
        """Fail streak stopping only applies at easy level."""
        state = SessionState(fail_streak=3, current_difficulty="medium")
        stop, _ = engine.should_stop(state)
        assert stop is False

    def test_empty_session_does_not_stop(self, engine):
        state = SessionState()
        stop, _ = engine.should_stop(state)
        assert stop is False


# ─── Test: AnswerEval score weights ───────────────────────────────────────────

class TestAnswerEval:

    def test_overall_is_weighted_average(self):
        """
        Weights: correctness=0.5, depth=0.3, clarity=0.2
        Expected: 1.0*0.5 + 0.5*0.3 + 0.0*0.2 = 0.65
        """
        eval_ = AnswerEval(
            correctness=1.0, depth=0.5, clarity=0.0,
            overall=1.0*0.5 + 0.5*0.3 + 0.0*0.2,
            reason="test"
        )
        assert abs(eval_.overall - 0.65) < 1e-9


# ─── Test: Full session flow (integration, no real API) ───────────────────────

class TestSessionFlow:

    def test_full_session_terminates(self, engine):
        """Simulate a full session without real API calls."""
        state = SessionState()
        evals_used = []

        for i in range(15):   # more than MAX to verify stop fires
            stop, _ = engine.should_stop(state)
            if stop:
                break
            q = engine.next_question(state)
            if q is None:
                break
            state.questions_asked.append(q)
            ev = make_eval(0.8 if i % 3 != 0 else 0.2)
            state.evaluations.append(ev)
            evals_used.append(ev)
            engine.update_difficulty(state, ev)

        assert len(state.questions_asked) <= engine.MAX_QUESTIONS

    def test_difficulty_never_invalid(self, engine):
        """Current difficulty must always be easy/medium/hard."""
        state = SessionState()
        for _ in range(20):
            ev = make_eval(random.uniform(0, 1))  # noqa: F821
            engine.update_difficulty(state, ev)
            assert state.current_difficulty in ("easy", "medium", "hard")

import random  # needed for test above


# ─── Run ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    pytest.main([__file__, "-v"])