# agents/scope_guard.py
from config.use_cases import USE_CASES


class ScopeGuard:
    def __init__(self, use_case_key="AI_PLANNER"):
        self.use_case_key = use_case_key
        self.use_case = USE_CASES.get(use_case_key, {})

    def set_use_case(self, key):
        if key in USE_CASES:
            self.use_case_key = key
            self.use_case = USE_CASES[key]
            return f"Use case set to: {USE_CASES[key]['name']}"
        return f"Unknown use case: {key}"

    def check(self, message):
        """
        Returns dict:
          status  : 'in_scope' | 'out_of_scope' | 'needs_clarification'
          reason  : explanation string
          message : original message
        """
        msg_lower = message.lower()

        # Check out of scope first — explicit blocklist takes priority
        out_hits = [
            kw for kw in self.use_case.get("out_of_scope", [])
            if kw.lower() in msg_lower
        ]
        if out_hits:
            return {
                "status": "out_of_scope",
                "reason": (
                    f"This request contains out-of-scope topics: "
                    f"{', '.join(out_hits)}.\n"
                    f"Current use case: {self.use_case.get('name', 'unknown')}.\n"
                    f"Would you like to add this to scope or rephrase your request?"
                ),
                "matched_keywords": out_hits,
                "message": message
            }

        # Check in scope
        in_hits = [
            kw for kw in self.use_case.get("in_scope", [])
            if kw.lower() in msg_lower
        ]
        if in_hits:
            return {
                "status": "in_scope",
                "reason": "Request is within scope.",
                "matched_keywords": in_hits,
                "message": message
            }

        # No keywords matched either list — needs clarification
        return {
            "status": "needs_clarification",
            "reason": (
                f"This request does not clearly match the current use case: "
                f"{self.use_case.get('name', 'unknown')}.\n"
                f"Please clarify how this relates to your project, "
                f"or switch to a different use case."
            ),
            "matched_keywords": [],
            "message": message
        }

    def is_high_risk(self, message):
        """
        Flags messages that should trigger the human approval gate.
        Returns True if approval is needed.
        """
        high_risk_keywords = [
            "change the stack", "switch to", "replace supabase",
            "use aws", "use mongodb", "authentication", "payment",
            "delete all", "drop table", "production database",
            "user passwords", "api keys", "secrets"
        ]
        msg_lower = message.lower()
        return any(kw in msg_lower for kw in high_risk_keywords)
