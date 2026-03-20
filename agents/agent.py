# agents/agent.py
import os
import anthropic
from dotenv import load_dotenv
from agents.modes import MODES
from prompts.master_prompt import MASTER_PROMPT
from memory.conversation import ConversationMemory
import streamlit as st

load_dotenv()

def get_api_key():
    try:
        return st.secrets["ANTHROPIC_API_KEY"]
    except Exception:
        return os.getenv("ANTHROPIC_API_KEY")

client = anthropic.Anthropic(api_key=get_api_key())

class ArchitectAgent:
    def __init__(self):
        self.memory = ConversationMemory()
        self.current_mode = "ARCHITECT"

    def set_mode(self, mode):
        mode = mode.upper()
        if mode in MODES:
            self.current_mode = mode
            return f"Switched to {mode} mode"
        return f"Unknown mode: {mode}. Available: {', '.join(MODES.keys())}"

    def set_context(self, key, value):
        self.memory.set_context(key, value)
        return f"Context saved: {key} = {value}"

    def build_system_prompt(self):
        context = self.memory.get_context_summary()
        mode_prompt = MODES[self.current_mode]
        return f"{MASTER_PROMPT}\n{mode_prompt}\n{context}"

    def chat(self, user_message):
        self.memory.add_message("user", user_message)

        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4000,
            system=self.build_system_prompt(),
            messages=self.memory.get_history()
        )

        reply = response.content[0].text
        self.memory.add_message("assistant", reply)
        return reply

    def reset(self):
        self.memory.clear()
        self.current_mode = "ARCHITECT"
        return "Memory cleared. Starting fresh."
