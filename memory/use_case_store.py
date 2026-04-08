# memory/use_case_store.py
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


class UseCaseStore:
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

    def get_all(self):
        """Return all active use cases as list of dicts."""
        try:
            client = self._get_client()
            if client:
                result = (
                    client.table("use_cases")
                    .select("*")
                    .eq("active", True)
                    .order("created_at")
                    .execute()
                )
                return result.data or []
        except Exception as e:
            print(f"Get use cases error: {e}")
        return []

    def get_by_key(self, key):
        """Return a single use case by its key."""
        try:
            client = self._get_client()
            if client:
                result = (
                    client.table("use_cases")
                    .select("*")
                    .eq("key", key)
                    .limit(1)
                    .execute()
                )
                return result.data[0] if result.data else None
        except Exception as e:
            print(f"Get use case error: {e}")
        return None

    def create(self, key, name, description="", github_repo="",
               stack_frontend="", stack_backend="", stack_database="",
               stack_ai="", stack_hosting="", stack_auth="",
               in_scope="", out_of_scope=""):
        """Create a new use case."""
        try:
            client = self._get_client()
            if client:
                result = client.table("use_cases").insert({
                    "key": key.upper().replace(" ", "_"),
                    "name": name,
                    "description": description,
                    "github_repo": github_repo,
                    "stack_frontend": stack_frontend,
                    "stack_backend": stack_backend,
                    "stack_database": stack_database,
                    "stack_ai": stack_ai,
                    "stack_hosting": stack_hosting,
                    "stack_auth": stack_auth,
                    "in_scope": in_scope,
                    "out_of_scope": out_of_scope,
                    "active": True,
                    "repo_created": False
                }).execute()
                return result.data[0] if result.data else None
        except Exception as e:
            print(f"Create use case error: {e}")
        return None

    def update(self, key, **kwargs):
        """Update fields on an existing use case."""
        try:
            client = self._get_client()
            if client:
                client.table("use_cases") \
                    .update(kwargs) \
                    .eq("key", key) \
                    .execute()
                return True
        except Exception as e:
            print(f"Update use case error: {e}")
        return False

    def deactivate(self, key):
        """Soft delete — sets active=false."""
        return self.update(key, active=False)

    def mark_repo_created(self, key):
        return self.update(key, repo_created=True)

    def get_stack_string(self, key):
        """Return formatted stack string for use in agent prompts."""
        uc = self.get_by_key(key)
        if not uc:
            return "FastAPI + React Native + Supabase + Claude API"
        parts = []
        for field in ["stack_backend", "stack_frontend", "stack_database",
                      "stack_ai", "stack_hosting", "stack_auth"]:
            val = uc.get(field, "")
            if val:
                parts.append(val)
        return " + ".join(parts) if parts else "FastAPI + Supabase + Claude API"

    def get_scope_keywords(self, key):
        """Return in_scope and out_of_scope as lists."""
        uc = self.get_by_key(key)
        if not uc:
            return [], []
        in_scope = [k.strip() for k in uc.get("in_scope","").split(",") if k.strip()]
        out_scope = [k.strip() for k in uc.get("out_of_scope","").split(",") if k.strip()]
        return in_scope, out_scope

    def to_dropdown_options(self):
        """Return dict suitable for st.selectbox: {key: name}"""
        use_cases = self.get_all()
        return {uc["key"]: uc["name"] for uc in use_cases}