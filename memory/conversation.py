class ConversationMemory:
    def __init__(self):
        self.history = []
        self.project_context = {}

    def add_message(self, role, content):
        self.history.append({
            "role": role,
            "content": content
        })

    def get_history(self):
        return self.history

    def set_context(self, key, value):
        self.project_context[key] = value

    def get_context_summary(self):
        if not self.project_context:
            return ""
        lines = ["PROJECT CONTEXT (remember these decisions):"]
        for k, v in self.project_context.items():
            lines.append(f"  {k}: {v}")
        return "\n".join(lines)

    def clear(self):
        self.history = []
        self.project_context = {}

    def message_count(self):
        return len(self.history)
