# agents/approval_gate.py
from memory.task_store import TaskStore

task_store = TaskStore()


class ApprovalGate:
    """
    Handles all PO approval flows:
      - Task creation approval
      - PR creation approval
      - Test execution approval
      - Scope change approval
    """

    @staticmethod
    def needs_approval(request_type, content):
        """
        Determine if a request needs PO approval.
        Returns True for anything that creates, changes or runs.
        """
        always_approve = [
            "task_creation",
            "pr_creation",
            "test_execution",
            "scope_change",
            "code_deployment",
            "bug_fix_assignment"
        ]
        return request_type in always_approve

    @staticmethod
    def format_approval_card(request_type, details):
        """
        Format a pending approval for display in the UI.
        Returns a dict the UI renders as an approval card.
        """
        titles = {
            "task_creation":     "Task creation approval",
            "pr_creation":       "GitHub PR approval",
            "test_execution":    "Test execution approval",
            "scope_change":      "Scope change approval",
            "bug_fix_assignment":"Bug fix assignment approval"
        }
        return {
            "type": "approval_required",
            "request_type": request_type,
            "title": titles.get(request_type, "Approval required"),
            "details": details,
            "pending": True
        }

    @staticmethod
    def approve_task(task_suggestion, use_case):
        """
        Called when PO clicks Approve on a task suggestion.
        Saves to Supabase and returns the created task.
        """
        task = task_store.create_task(
            use_case=use_case,
            title=task_suggestion.get("title", "Untitled task"),
            description=task_suggestion.get("description", ""),
            assigned_to=task_suggestion.get("assigned_to", ""),
            created_by=task_suggestion.get("created_by", "SCRUM_MASTER"),
            priority=task_suggestion.get("priority", "P2")
        )
        if task:
            task_store.approve_task(task["id"], approved=True,
                                    decision="Approved by Product Owner")
        return task

    @staticmethod
    def reject_task(task_suggestion):
        """Called when PO clicks Reject — no database write."""
        return {
            "rejected": True,
            "title": task_suggestion.get("title"),
            "reason": "Rejected by Product Owner"
        }
