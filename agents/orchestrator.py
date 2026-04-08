# agents/orchestrator.py
import os
from memory.conversation import ConversationMemory
from dotenv import load_dotenv

load_dotenv()


class Orchestrator:
    """
    Routes every user message to the correct specialist agent.
    Holds shared conversation memory and project context.
    Lazy-loads specialists — only imports when first needed.
    Scrum Master scanning is handled by app.py — not here.
    """

    def __init__(self):
        self.memory = ConversationMemory()
        self.current_mode = "ARCHITECT"
        self._specialists = {}

    def _get_specialist(self, mode):
        """Lazy load specialist — only import when first needed"""
        if mode not in self._specialists:
            if mode == "ARCHITECT":
                from agents.architect_agent import ArchitectAgent
                self._specialists[mode] = ArchitectAgent()
            elif mode == "DEVELOPER":
                from agents.developer_agent import DeveloperAgent
                self._specialists[mode] = DeveloperAgent()
            elif mode == "PLANNER":
                from agents.planner_agent import PlannerAgent
                self._specialists[mode] = PlannerAgent()
            elif mode == "QA":
                from agents.qa_agent import QAAgent
                self._specialists[mode] = QAAgent()
            elif mode == "POLICY":
                from agents.policy_agent import PolicyAgent
                self._specialists[mode] = PolicyAgent()
        return self._specialists.get(mode)

    def set_mode(self, mode):
        mode = mode.upper()
        valid = ["ARCHITECT", "DEVELOPER", "PLANNER", "QA", "POLICY"]
        if mode in valid:
            self.current_mode = mode
            return f"Switched to {mode} mode"
        return f"Unknown mode: {mode}. Available: {', '.join(valid)}"

    def set_context(self, key, value):
        self.memory.set_context(key, value)
        return f"Context saved: {key} = {value}"

    def chat(self, user_message):
        """
        Main entry point from app.py.
        1. Add user message to memory
        2. Route to correct specialist
        3. Return response
        Note: Scrum Master task scanning is done in app.py after this returns.
        """
        self.memory.add_message("user", user_message)
        history = self.memory.get_history()
        context = self.memory.get_context_summary()

        specialist = self._get_specialist(self.current_mode)
        if not specialist:
            return f"Error: could not load specialist for {self.current_mode}"

        reply = specialist.run(user_message, history, context)
        self.memory.add_message("assistant", reply)
        return reply

    def reset(self):
        self.memory.clear()
        self.current_mode = "ARCHITECT"
        self._specialists = {}
        return "Memory cleared. Starting fresh."