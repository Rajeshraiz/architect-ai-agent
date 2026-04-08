# agents/scrum_master_agent.py
import os
import json
import anthropic
import datetime
from memory.task_store import TaskStore
from dotenv import load_dotenv

load_dotenv()


def get_secret(key):
    try:
        import streamlit as st
        v = st.secrets.get(key)
        if v:
            return v
    except Exception:
        pass
    return os.getenv(key)


SCRUM_MASTER_PROMPT = """
You are ARIA's Scrum Master. You manage software delivery process only.
You do NOT write code or design systems.

When suggesting a task return ONLY valid JSON, nothing else:
{
  "suggestion_type": "task",
  "title": "short task title under 60 chars",
  "description": "what needs to be done and why",
  "assigned_to": "DEVELOPER or ARCHITECT or QA or POLICY or PLANNER",
  "priority": "P1 or P2 or P3",
  "created_by": "SCRUM_MASTER",
  "reason": "one sentence explaining why"
}

If no clear task is implied return ONLY:
{"suggestion_type": "none"}
"""

TASK_GENERATION_PROMPT = """
You are a Senior Scrum Master reading an approved software architecture.
Break it into a structured phased task list.

Rules:
- Group tasks into logical phases (Phase 1 = Foundation, Phase 2 = Core Features, etc.)
- Each task must be actionable and specific
- Assign each to exactly one: DEVELOPER, ARCHITECT, QA, or POLICY
- Estimate realistic hours per task (1-16 hours)
- Identify dependencies where needed
- Keep task titles under 60 characters
- Max 5 phases, max 8 tasks per phase

Return ONLY a valid JSON array. No markdown fences, no explanation:
[
  {
    "phase": "Phase 1 - Foundation",
    "title": "task title here",
    "description": "specific description of what needs to be done",
    "assigned_to": "DEVELOPER",
    "priority": "P1",
    "estimated_hours": 3,
    "depends_on_index": null
  }
]

depends_on_index is the 0-based array index of the task this depends on, or null.
"""


class ScrumMasterAgent:
    def __init__(self):
        self.client = anthropic.Anthropic(
            api_key=get_secret("ANTHROPIC_API_KEY")
        )
        self.task_store = TaskStore()

    def generate_tasks_from_architecture(self, architecture_text, use_case):
        """
        Reads approved architecture and generates structured task batch.
        Returns list of task dicts ready for preview UI.
        """
        try:
            response = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=4000,
                system=TASK_GENERATION_PROMPT,
                messages=[{
                    "role": "user",
                    "content": (
                        f"Use case: {use_case}\n\n"
                        f"Architecture to break down:\n{architecture_text}\n\n"
                        f"Generate task breakdown. Return JSON array only."
                    )
                }]
            )
            text = response.content[0].text.strip()
            # Strip markdown fences if model adds them
            if "```" in text:
                parts = text.split("```")
                for part in parts:
                    part = part.strip()
                    if part.startswith("[") or part.startswith("json\n["):
                        text = part.replace("json\n", "").strip()
                        break
            return json.loads(text)
        except Exception as e:
            print(f"Task generation error: {e}")
            return []

    def scan_for_tasks(self, conversation_history, use_case):
        """
        Proactively scan last messages for implied tasks.
        Only runs every 4 messages to avoid constant interruptions.
        """
        if len(conversation_history) < 4:
            return None
        if len(conversation_history) % 4 != 0:
            return None

        recent = conversation_history[-4:]
        context = "\n".join([
            f"{m['role'].upper()}: {m['content'][:300]}"
            for m in recent
        ])

        try:
            response = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=300,
                system=SCRUM_MASTER_PROMPT,
                messages=[{
                    "role": "user",
                    "content": (
                        f"Review for implied tasks. Use case: {use_case}\n\n"
                        f"Conversation:\n{context}\n\nReturn JSON only."
                    )
                }]
            )
            text = response.content[0].text.strip()
            start = text.find("{")
            end = text.rfind("}") + 1
            if start >= 0 and end > start:
                s = json.loads(text[start:end])
                if s.get("suggestion_type") == "task":
                    return s
        except Exception as e:
            print(f"Scan error: {e}")
        return None

    def create_bug_task(self, test_name, failure_output,
                        use_case, severity="P1"):
        return {
            "suggestion_type": "task",
            "title": f"Fix failing test: {test_name}",
            "description": f"QA found failing test.\nTest: {test_name}\n{failure_output[:400]}",
            "assigned_to": "DEVELOPER",
            "priority": severity,
            "created_by": "QA_RUNNER",
            "reason": "Must fix before PR can merge",
            "use_case": use_case
        }

    def generate_standup(self, use_case):
        tasks = self.task_store.get_tasks(use_case)
        if not tasks:
            return (
                f"# Daily Standup — {use_case}\n\n"
                f"No tasks yet. Approve an architecture to generate tasks."
            )
        done_t  = [t for t in tasks if t["status"] == "done"]
        in_prog = [t for t in tasks if t["status"] == "in_progress"]
        todo    = [t for t in tasks if t["status"] == "todo" and t.get("po_approved")]
        pending = [t for t in tasks if not t.get("po_approved")
                   and t["status"] not in ("rejected","done")]

        today = datetime.datetime.now().strftime("%B %d, %Y")
        lines = [f"# Daily Standup — {use_case}", f"*{today}*", "",
                 "## Done"]
        lines += [f"- {t['title']} ({t.get('assigned_to','')})"
                  for t in done_t[-5:]] or ["- Nothing yet"]
        lines += ["", "## In Progress"]
        lines += [f"- {t['title']} ({t.get('assigned_to','')})"
                  for t in in_prog] or ["- Nothing in progress"]
        lines += ["", "## Blockers"]
        lines += [f"- {t['title']} (awaiting PO approval)"
                  for t in pending] or ["- No blockers"]
        lines += ["", "## Todo Today"]
        lines += [f"- {t['title']} — {t.get('priority','P2')}"
                  for t in todo[:5]] or ["- Board is clear"]
        return "\n".join(lines)