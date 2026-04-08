# webhook_server.py
# Deploy this to Railway — NOT Streamlit Cloud
# This is a separate FastAPI app that receives GitHub PR events
# and updates the Supabase task table automatically

import os
import hmac
import hashlib
from fastapi import FastAPI, Request, HTTPException
from supabase import create_client

app = FastAPI(title="ARIA Webhook Server")

# ─── Supabase client ────────────────────────────────────────────
def get_supabase():
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    if not url or not key:
        raise RuntimeError("SUPABASE_URL and SUPABASE_KEY must be set")
    return create_client(url, key)


# ─── GitHub signature verification ──────────────────────────────
def verify_signature(payload_body: bytes, signature: str) -> bool:
    """Verify the webhook came from GitHub."""
    secret = os.getenv("GITHUB_WEBHOOK_SECRET", "")
    if not secret:
        return True  # Skip verification if no secret set
    expected = "sha256=" + hmac.new(
        secret.encode(), payload_body, hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature or "")


# ─── Task lookup and update ──────────────────────────────────────
def update_task_by_pr_title(pr_title: str, status: str, pr_url: str = ""):
    """
    Find a task matching the PR title and update its status.
    PR title format from ARIA: [ARIA] {task_title}
    """
    try:
        supabase = get_supabase()
        # Extract task title — remove [ARIA] prefix
        clean = pr_title.replace("[ARIA]", "").strip()
        if not clean:
            return False

        # Search for matching task (first 40 chars)
        result = (
            supabase.table("tasks")
            .select("id, title, status")
            .ilike("title", f"%{clean[:40]}%")
            .execute()
        )

        if not result.data:
            print(f"No task found matching: {clean[:40]}")
            return False

        task_id = result.data[0]["id"]
        update_payload = {"status": status}
        if pr_url:
            update_payload["github_pr_url"] = pr_url

        supabase.table("tasks") \
            .update(update_payload) \
            .eq("id", task_id) \
            .execute()

        print(f"Task updated: {clean[:40]} → {status}")
        return True

    except Exception as e:
        print(f"Task update error: {e}")
        return False


# ─── Webhook endpoint ────────────────────────────────────────────
@app.post("/webhook/github")
async def github_webhook(request: Request):
    """
    Receives GitHub PR events and updates Supabase task status.

    PR opened  → task moves to in_progress
    PR merged  → task moves to done
    PR closed (not merged) → task moves back to todo
    """
    # Read body
    body = await request.body()

    # Verify signature (optional but recommended)
    sig = request.headers.get("X-Hub-Signature-256", "")
    if not verify_signature(body, sig):
        raise HTTPException(status_code=401, detail="Invalid signature")

    # Parse event
    event = request.headers.get("X-GitHub-Event", "")
    payload = await request.json()

    if event != "pull_request":
        return {"status": "ignored", "event": event}

    action = payload.get("action", "")
    pr = payload.get("pull_request", {})
    pr_title = pr.get("title", "")
    pr_url   = pr.get("html_url", "")
    merged   = pr.get("merged", False)

    # Only process ARIA-generated PRs
    if not pr_title.startswith("[ARIA]"):
        return {"status": "ignored", "reason": "not an ARIA PR"}

    # Map GitHub action to task status
    if action == "opened" or action == "reopened":
        status = "in_progress"
        update_task_by_pr_title(pr_title, status, pr_url)
        return {"status": "updated", "task_status": status}

    elif action == "closed":
        if merged:
            status = "done"
        else:
            status = "todo"  # PR closed without merge — send back to todo
        update_task_by_pr_title(pr_title, status, pr_url)
        return {"status": "updated", "task_status": status}

    return {"status": "no_action", "action": action}


# ─── Health check ────────────────────────────────────────────────
@app.get("/")
def health():
    return {
        "status": "ARIA webhook server running",
        "endpoints": ["/webhook/github"]
    }


# ─── Local run ───────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)