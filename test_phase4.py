# test_phase4.py
from agents.scope_guard import ScopeGuard

guard = ScopeGuard("AI_PLANNER")

print("=" * 60)
print("PHASE 4 TEST — Scope Guard")
print("=" * 60)

IN_SCOPE_TESTS = [
    "Design a task creation API endpoint",
    "Write the AI priority ranking logic in Python",
    "Break down the calendar sync feature into tasks",
    "Write test cases for the login authentication flow",
    "Define a data retention policy for user tasks",
]

OUT_OF_SCOPE_TESTS = [
    "Add a payment system with Stripe integration",
    "Build a voice input feature for the app",
    "Create an admin dashboard for user management",
    "Add offline mode with local storage",
    "Integrate with Outlook calendar",
]

print("\n--- IN SCOPE TESTS ---")
all_passed = True
for prompt in IN_SCOPE_TESTS:
    result = guard.check(prompt)
    status = result["status"]
    passed = status == "in_scope"
    if not passed:
        all_passed = False
    icon = "✓" if passed else "✗"
    print(f"[IN SCOPE  {icon}] '{prompt[:55]}'")
    if not passed:
        print(f"           → Got: {status} | {result['reason'][:80]}")

print("\n--- OUT OF SCOPE TESTS ---")
for prompt in OUT_OF_SCOPE_TESTS:
    result = guard.check(prompt)
    status = result["status"]
    passed = status == "out_of_scope"
    if not passed:
        all_passed = False
    icon = "✓" if passed else "✗"
    print(f"[OUT SCOPE {icon}] '{prompt[:55]}'")
    if not passed:
        print(f"           → Got: {status} | {result['reason'][:80]}")

print("\n" + "=" * 60)
if all_passed:
    print("All 10 tests passed. Phase 4 scope guard working!")
else:
    print("Some tests failed — paste output above to Claude for fix.")
print("=" * 60)
