# memory/persistent.py
import os
from dotenv import load_dotenv

load_dotenv()


def get_secret(key):
    """Read from Streamlit secrets first, fall back to .env"""
    try:
        import streamlit as st
        val = st.secrets.get(key)
        if val:
            return val
    except Exception:
        pass
    return os.getenv(key)


class PersistentMemory:
    def __init__(self, session_id):
        self.session_id = session_id
        self._client = None

    def _get_client(self):
        """Lazy initialisation — only connect when first needed"""
        if self._client is None:
            from supabase import create_client
            url = get_secret("SUPABASE_URL")
            key = get_secret("SUPABASE_KEY")
            if url and key:
                self._client = create_client(url, key)
        return self._client

    def save_message(self, role, content, mode="ARCHITECT"):
        try:
            client = self._get_client()
            if client:
                client.table("sessions").insert({
                    "session_id": self.session_id,
                    "role": role,
                    "content": content,
                    "mode": mode
                }).execute()
        except Exception as e:
            print(f"Warning: Could not save to Supabase: {e}")

    def load_history(self):
        try:
            client = self._get_client()
            if client:
                result = (
                    client.table("sessions")
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
            print(f"Warning: Could not load from Supabase: {e}")
        return []

    def clear_session(self):
        try:
            client = self._get_client()
            if client:
                client.table("sessions") \
                    .delete() \
                    .eq("session_id", self.session_id) \
                    .execute()
        except Exception as e:
            print(f"Warning: Could not clear session: {e}")

    def list_sessions(self):
        try:
            client = self._get_client()
            if client:
                result = (
                    client.table("sessions")
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