# memory/task_store.py
import os
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


class TaskStore:
    def __init__(self):
        self._client = None

    def _get_client(self):
        if self._client is None:
            try:
                from supabase import create_client
                url = get_secret("SUPABASE_URL")
                key = get_secret("SUPABASE_KEY")
                if url and key:
                    self._client = create_client(url, key)
            except Exception as e:
                print(f"Supabase connect error: {e}")
        return self._client

    # ── Single task ──────────────────────────────────────────────

    def create_task(self, use_case, title, description="",
                    assigned_to="", created_by="", priority="P2",
                    phase="Phase 1", estimated_hours=0,
                    architecture_id=None):
        try:
            client = self._get_client()
            if client:
                payload = {
                    "use_case": use_case,
                    "title": title,
                    "description": description,
                    "assigned_to": assigned_to,
                    "created_by": created_by,
                    "priority": priority,
                    "status": "todo",
                    "po_approved": False,
                    "phase": phase,
                    "estimated_hours": estimated_hours,
                }
                if architecture_id:
                    payload["architecture_id"] = architecture_id
                result = client.table("tasks").insert(payload).execute()
                return result.data[0] if result.data else None
        except Exception as e:
            print(f"Create task error: {e}")
        return None

    def batch_create_tasks(self, task_list, use_case, architecture_id=None):
        """
        Create multiple tasks from Scrum Master generation.
        task_list is the JSON array from generate_tasks_from_architecture().
        Returns list of created task dicts.
        """
        created = []
        id_map = {}  # index → created task id for depends_on

        for i, t in enumerate(task_list):
            depends_on = None
            dep_idx = t.get("depends_on_index")
            if dep_idx is not None and dep_idx in id_map:
                depends_on = id_map[dep_idx]

            try:
                client = self._get_client()
                if client:
                    payload = {
                        "use_case": use_case,
                        "title": t.get("title", "Untitled task"),
                        "description": t.get("description", ""),
                        "assigned_to": t.get("assigned_to", "DEVELOPER"),
                        "created_by": "SCRUM_MASTER",
                        "priority": t.get("priority", "P2"),
                        "status": "todo",
                        "po_approved": True,  # batch approved by PO
                        "phase": t.get("phase", "Phase 1"),
                        "estimated_hours": t.get("estimated_hours", 0),
                    }
                    if architecture_id:
                        payload["architecture_id"] = architecture_id
                    if depends_on:
                        payload["depends_on"] = depends_on

                    result = client.table("tasks").insert(payload).execute()
                    if result.data:
                        task = result.data[0]
                        id_map[i] = task["id"]
                        created.append(task)
            except Exception as e:
                print(f"Batch create error on task {i}: {e}")

        return created

    # ── Fetch ─────────────────────────────────────────────────────

    def get_tasks(self, use_case):
        try:
            client = self._get_client()
            if client:
                result = (
                    client.table("tasks")
                    .select("*")
                    .eq("use_case", use_case)
                    .order("created_at")
                    .execute()
                )
                return result.data or []
        except Exception as e:
            print(f"Get tasks error: {e}")
        return []

    def get_tasks_by_phase(self, use_case):
        """
        Returns tasks grouped by phase.
        { "Phase 1 - Foundation": [task, ...], ... }
        """
        tasks = self.get_tasks(use_case)
        phases = {}
        for t in tasks:
            phase = t.get("phase") or "Phase 1"
            if phase not in phases:
                phases[phase] = []
            phases[phase].append(t)
        return phases

    # ── Update ────────────────────────────────────────────────────

    def update_status(self, task_id, status):
        try:
            client = self._get_client()
            if client:
                client.table("tasks") \
                    .update({"status": status}) \
                    .eq("id", task_id) \
                    .execute()
                return True
        except Exception as e:
            print(f"Update status error: {e}")
        return False

    def update_status_by_pr_title(self, pr_title, status, pr_url=""):
        """
        Called by webhook server when PR is opened or merged.
        Matches task by title contained in PR title.
        PR title format: [ARIA] {task_title}
        """
        try:
            client = self._get_client()
            if client:
                # Extract task title from PR title
                clean_title = pr_title.replace("[ARIA]", "").strip()
                result = (
                    client.table("tasks")
                    .select("*")
                    .ilike("title", f"%{clean_title[:40]}%")
                    .execute()
                )
                if result.data:
                    task_id = result.data[0]["id"]
                    update = {"status": status}
                    if pr_url:
                        update["github_pr_url"] = pr_url
                    client.table("tasks") \
                        .update(update) \
                        .eq("id", task_id) \
                        .execute()
                    return True
        except Exception as e:
            print(f"PR title match error: {e}")
        return False

    def approve_task(self, task_id, approved=True, decision=""):
        try:
            client = self._get_client()
            if client:
                client.table("tasks") \
                    .update({
                        "po_approved": approved,
                        "po_decision": decision,
                        "status": "todo" if approved else "rejected"
                    }) \
                    .eq("id", task_id) \
                    .execute()
                return True
        except Exception as e:
            print(f"Approve task error: {e}")
        return False

    def update_pr_url(self, task_id, pr_url):
        try:
            client = self._get_client()
            if client:
                client.table("tasks") \
                    .update({"github_pr_url": pr_url,
                             "status": "in_progress"}) \
                    .eq("id", task_id) \
                    .execute()
                return True
        except Exception as e:
            print(f"Update PR URL error: {e}")
        return False

    def all_phase_tasks_done(self, use_case, phase):
        """Check if all tasks in a phase are done — triggers next phase."""
        try:
            tasks = self.get_tasks(use_case)
            phase_tasks = [t for t in tasks if t.get("phase") == phase
                           and t.get("po_approved")]
            if not phase_tasks:
                return False
            return all(t["status"] == "done" for t in phase_tasks)
        except Exception as e:
            print(f"Phase check error: {e}")
        return False

    def delete_task(self, task_id):
        try:
            client = self._get_client()
            if client:
                client.table("tasks") \
                    .delete() \
                    .eq("id", task_id) \
                    .execute()
                return True
        except Exception as e:
            print(f"Delete task error: {e}")
        return False

    # ── Architecture store ────────────────────────────────────────

    def save_architecture(self, use_case, content):
        """Save approved architecture to Supabase."""
        try:
            client = self._get_client()
            if client:
                result = client.table("architectures").insert({
                    "use_case": use_case,
                    "content": content,
                    "status": "approved"
                }).execute()
                return result.data[0] if result.data else None
        except Exception as e:
            print(f"Save architecture error: {e}")
        return None

    def get_latest_architecture(self, use_case):
        """Get most recent approved architecture for a use case."""
        try:
            client = self._get_client()
            if client:
                result = (
                    client.table("architectures")
                    .select("*")
                    .eq("use_case", use_case)
                    .eq("status", "approved")
                    .order("created_at", desc=True)
                    .limit(1)
                    .execute()
                )
                return result.data[0] if result.data else None
        except Exception as e:
            print(f"Get architecture error: {e}")
        return None