"""
tests/test_agents.py
---------------------
Basic unit tests for the three agents. Run with: pytest
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd
import pytest

from agents import CGMMealPlannerAgent, GreetingAgent, InterruptAgent
from llm import LLMUnavailableError


@pytest.fixture
def users_df():
    return pd.DataFrame(
        [
            {
                "user_id": "U001",
                "first_name": "Asha",
                "last_name": "Rao",
                "city": "Chennai",
                "dietary_preference": "veg",
                "medical_condition": "Type 2 Diabetes",
                "cgm_reading": 140,
            }
        ]
    )


class FakeLLM:
    """Stand-in LLM that never calls the network."""

    def __init__(self, should_fail=False, response="Fake meal plan text."):
        self.should_fail = should_fail
        self.response = response

    def generate(self, prompt, max_tokens=400, temperature=0.6):
        if self.should_fail:
            raise LLMUnavailableError("simulated failure")
        return self.response


# ---------------- GreetingAgent ----------------

def test_greeting_agent_valid_user(users_df):
    agent = GreetingAgent(users_df)
    result = agent.run("u001")  # lowercase should still match
    assert result["ok"] is True
    assert result["user"]["first_name"] == "Asha"
    assert "Asha" in result["message"]


def test_greeting_agent_invalid_user(users_df):
    agent = GreetingAgent(users_df)
    result = agent.run("U999")
    assert result["ok"] is False
    assert result["user"] is None


def test_greeting_agent_empty_input(users_df):
    agent = GreetingAgent(users_df)
    result = agent.run("")
    assert result["ok"] is False


# ---------------- CGMMealPlannerAgent ----------------

def test_meal_planner_flags_high_glucose(users_df):
    user = users_df.iloc[0].to_dict()
    agent = CGMMealPlannerAgent(FakeLLM())
    result = agent.run(user, 320)
    assert "High" in result["message"]


def test_meal_planner_flags_low_glucose(users_df):
    user = users_df.iloc[0].to_dict()
    agent = CGMMealPlannerAgent(FakeLLM())
    result = agent.run(user, 60)
    assert "Low" in result["message"]


def test_meal_planner_in_range(users_df):
    user = users_df.iloc[0].to_dict()
    agent = CGMMealPlannerAgent(FakeLLM())
    result = agent.run(user, 150)
    assert "In range" in result["message"]


def test_meal_planner_falls_back_when_llm_unavailable(users_df):
    user = users_df.iloc[0].to_dict()
    agent = CGMMealPlannerAgent(FakeLLM(should_fail=True))
    result = agent.run(user, 150)
    assert "fallback" in result["message"].lower()
    assert "Breakfast" in result["message"]


# ---------------- InterruptAgent ----------------

def test_interrupt_agent_answers_and_returns_to_flow():
    agent = InterruptAgent(FakeLLM(response="Paris is the capital of France."))
    answer = agent.run("What is the capital of France?")
    assert "Paris is the capital of France." in answer
    assert "back in the main flow" in answer


def test_interrupt_agent_falls_back_when_llm_unavailable():
    agent = InterruptAgent(FakeLLM(should_fail=True))
    answer = agent.run("What is the capital of France?")
    assert "fallback" in answer.lower()


def test_interrupt_agent_fallback_answers_known_topic():
    agent = InterruptAgent(FakeLLM(should_fail=True))
    answer = agent.run("can he eat sugar?")
    assert "added sugar" in answer.lower()
