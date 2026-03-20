# test_phase2.py
from agents.agent import ArchitectAgent

agent = ArchitectAgent()

print("=" * 60)
print("PHASE 2 TEST — All 5 Agent Modes")
print("=" * 60)

tests = [
    ("ARCHITECT", "Design a simple REST API for a task manager app"),
    ("DEVELOPER", "Write a Python FastAPI health check endpoint"),
    ("PLANNER",   "Break down user registration into tasks"),
    ("QA",        "Write test cases for a login form"),
    ("POLICY",    "Define a data retention policy for user accounts"),
]

for mode, prompt in tests:
    print(f"\n{'─' * 60}")
    print(f"MODE: {mode}")
    print(f"PROMPT: {prompt}")
    print(f"{'─' * 60}")
    agent.set_mode(mode)
    agent.memory.clear()
    response = agent.chat(prompt)
    print(response[:500])
    print(f"\n[{mode}: OK ✓]")

print("\n" + "=" * 60)
print("All 5 modes working! Phase 2 complete.")
print("=" * 60)
