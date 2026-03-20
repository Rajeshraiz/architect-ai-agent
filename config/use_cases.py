# config/use_cases.py
# Add a new entry here for every use case you build.
# The scope guard reads in_scope and out_of_scope keyword lists.
# Keep keywords lowercase — matching is case-insensitive.

USE_CASES = {
    "AI_PLANNER": {
        "name": "AI Planner App",
        "description": "Cross-platform AI-driven task planner for Android, iOS and Windows",
        "stack": "FastAPI + React Native + Supabase + Claude API",
        "in_scope": [
            # Core features
            "task", "tasks", "planner", "planning", "schedule", "scheduling",
            "priority", "prioritize", "prioritisation", "deadline", "due date",
            "reminder", "notification", "calendar", "sync", "synchronise",
            # AI features
            "ai suggestion", "ai prioritiz", "smart schedule", "auto schedule",
            "rank", "ranking", "workload", "effort estimate",
            # Auth
            "login", "logout", "register", "authentication", "google sso",
            "user account", "password", "session", "token",
            # Team
            "team", "share", "collaborate", "assign", "member",
            # Technical
            "api", "endpoint", "database", "schema", "model", "fastapi",
            "react native", "supabase", "backend", "frontend", "mobile",
            "android", "ios", "windows", "cross-platform",
            # General
            "design", "architect", "build", "test", "policy", "plan", "code"
        ],
        "out_of_scope": [
            # Explicitly excluded features
            "payment", "billing", "stripe", "invoice", "subscription", "checkout",
            "voice input", "voice command", "speech recognition",
            "offline mode", "local storage", "no internet",
            "admin dashboard", "admin panel", "user management portal",
            "habit tracking", "habit suggestion", "behavioral insight",
            "file attachment", "upload file", "attach file",
            "outlook", "apple calendar", "ical",
            "native ios", "swift", "kotlin", "native android",
            # Infrastructure out of scope
            "aws", "azure", "kubernetes", "docker swarm", "terraform",
            "microservices", "kafka", "rabbitmq",
        ]
    },

    # ── Template for your next use case ──────────────────────────
    # "MY_NEXT_APP": {
    #     "name": "My Next App",
    #     "description": "One sentence description",
    #     "stack": "Your tech stack",
    #     "in_scope": [
    #         "keyword1", "keyword2", ...
    #     ],
    #     "out_of_scope": [
    #         "keyword1", "keyword2", ...
    #     ]
    # },
}
