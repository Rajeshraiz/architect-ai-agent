# memory/persistent.py
import os
from supabase import create_client
from dotenv import load_dotenv
import streamlit as st

load_dotenv()


class PersistentMemory:
    def __init__(self, session_id):
        self.session_id = session_id
        def get_secret(key):
            try:
                return st.secrets[key]
            except Exception:
                return os.getenv(key)
        self.client = create_client(
            get_secret("SUPABASE_URL"),
            get_secret("SUPABASE_KEY")
        )

    def save_message(self, role, content, mode="ARCHITECT"):
        """Save a single message to Supabase."""
        try:
            self.client.table("sessions").insert({
                "session_id": self.session_id,
                "role": role,
                "content": content,
                "mode": mode
            }).execute()
        except Exception as e:
            print(f"Warning: Could not save message to Supabase: {e}")

    def load_history(self):
        """Load full conversation history for this session."""
        try:
            result = (
                self.client.table("sessions")
                .select("role, content")
                .eq("session_id", self.session_id)
                .order("created_at")
                .execute()
            )
            return [
                {"role": r["role"], "content": r["content"]}
                for r in result.data
            ]
        except Exception as e:
            print(f"Warning: Could not load history from Supabase: {e}")
            return []

    def clear_session(self):
        """Delete all messages for this session."""
        try:
            self.client.table("sessions") \
                .delete() \
                .eq("session_id", self.session_id) \
                .execute()
        except Exception as e:
            print(f"Warning: Could not clear session: {e}")

    def list_sessions(self):
        """List all unique session IDs in the database."""
        try:
            result = (
                self.client.table("sessions")
                .select("session_id, created_at")
                .order("created_at", desc=True)
                .execute()
            )
            seen = set()
            sessions = []
            for r in result.data:
                if r["session_id"] not in seen:
                    seen.add(r["session_id"])
                    sessions.append(r["session_id"])
            return sessions
        except Exception as e:
            print(f"Warning: Could not list sessions: {e}")
            return []
