# agents/policy_engine.py
import os
import anthropic
from dotenv import load_dotenv

load_dotenv()
client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

POLICY_TEMPLATES = {
    "DATA_RETENTION": "Define a data retention policy including: how long each data type is stored, when it is automatically deleted, backup schedule, and user-initiated deletion rights.",
    "ACCESS_CONTROL": "Define role-based access control rules including: user roles, what each role can read/write/delete, admin privileges, and API key access levels.",
    "API_USAGE":      "Define API usage policies including: rate limits per endpoint, authentication requirements, allowed HTTP methods, error handling standards, and versioning rules.",
    "PRIVACY":        "Define a privacy policy covering: what personal data is collected, why it is collected, how it is stored, who it is shared with, and user rights (GDPR).",
    "SECURITY":       "Define security standards covering: encryption at rest and in transit, authentication standards, password policies, incident response steps, and vulnerability disclosure."
}


class PolicyEngine:
    def __init__(self, use_case_name="AI Planner App", stack="FastAPI + Supabase"):
        self.use_case_name = use_case_name
        self.stack = stack

    def generate(self, policy_type):
        """
        Generate a policy document for the given type.
        policy_type: DATA_RETENTION | ACCESS_CONTROL | API_USAGE | PRIVACY | SECURITY
        """
        if policy_type not in POLICY_TEMPLATES:
            available = ", ".join(POLICY_TEMPLATES.keys())
            return f"Unknown policy type. Available: {available}"

        prompt = POLICY_TEMPLATES[policy_type]

        system = f"""
        You are a senior software architect writing policies for:
        Product: {self.use_case_name}
        Stack: {self.stack}

        Write clear, numbered policy statements.
        Use plain English — no legal jargon.
        Be specific to this product and stack.
        Format: numbered list, one statement per line.
        """

        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1500,
            system=system,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.content[0].text

    def generate_all(self):
        """Generate all 5 policy documents and return as a dict."""
        results = {}
        for policy_type in POLICY_TEMPLATES:
            print(f"Generating {policy_type}...")
            results[policy_type] = self.generate(policy_type)
        return results
