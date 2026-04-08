# agents/base_agent.py
import os
import anthropic
from dotenv import load_dotenv

load_dotenv()


def get_secret(key):
    """Read from Streamlit secrets first, fall back to .env"""
    try:
        import streamlit as st
        val = st.secrets.get(key)
        if val:
            return val
    except Exception:
        pass
    return os.getenv(key)


class BaseAgent:
    """
    Base class for all 5 specialist agents.
    Each specialist inherits this and sets MODE_PROMPT.
    Orchestrator calls run() on whichever specialist is active.
    """
    MODE = "BASE"
    MODE_PROMPT = ""

    def __init__(self):
        self.client = anthropic.Anthropic(
            api_key=get_secret("ANTHROPIC_API_KEY")
        )

    def get_system_prompt(self, context=""):
        from prompts.master_prompt import MASTER_PROMPT
        from prompts.tone_rules import TONE_RULES
        return f"{MASTER_PROMPT}\n{TONE_RULES}\n{self.MODE_PROMPT}\n{context}"

    def run(self, user_message, history, context=""):
        """
        Called by Orchestrator with full conversation history.
        Returns specialist response string.
        """
        response = self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4000,
            system=self.get_system_prompt(context),
            messages=history
        )
        return response.content[0].text
