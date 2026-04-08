# app.py — Phase 4 update
# Adds: scope guard, persistent memory, human approval gate
import streamlit as st
import datetime
import uuid
from agents.agent import ArchitectAgent
from agents.orchestrator import Orchestrator
from agents.scope_guard import ScopeGuard
from agents.policy_engine import PolicyEngine
from memory.persistent import PersistentMemory

import streamlit as st



# ─── Page config ────────────────────────────────────────────────
st.set_page_config(
    page_title="ARIA Agent",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─── Session state init ─────────────────────────────────────────
if "agent" not in st.session_state:
    st.session_state.agent = Orchestrator()

if "messages" not in st.session_state:
    st.session_state.messages = []

if "current_mode" not in st.session_state:
    st.session_state.current_mode = "ARCHITECT"

if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())[:8]

if "use_case" not in st.session_state:
    st.session_state.use_case = "AI_PLANNER"

if "pending_approval" not in st.session_state:
    st.session_state.pending_approval = None

if "persistent_memory" not in st.session_state:
    st.session_state.persistent_memory = PersistentMemory(
        st.session_state.session_id
    )
    saved = st.session_state.persistent_memory.load_history()
    if saved:
        st.session_state.messages = saved

# ─── Init scope guard ───────────────────────────────────────────
scope_guard = ScopeGuard(st.session_state.use_case)

# ─── Mode definitions ───────────────────────────────────────────
MODES = {
    "ARCHITECT": {"icon": "🏛️", "desc": "System design, ERD, tech stack"},
    "DEVELOPER": {"icon": "💻", "desc": "Code generation, Python & React"},
    "PLANNER":   {"icon": "📋", "desc": "Task breakdown with estimates"},
    "QA":        {"icon": "🧪", "desc": "Test plans and test cases"},
    "POLICY":    {"icon": "📜", "desc": "Rules, policies, governance"},
}

FILE_TYPES = {
    "ARCHITECT": ("output.md",  "text/markdown"),
    "DEVELOPER": ("output.py",  "text/x-python"),
    "PLANNER":   ("output.md",  "text/markdown"),
    "QA":        ("output.md",  "text/markdown"),
    "POLICY":    ("output.md",  "text/markdown"),
}

# ─── Sidebar ────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🧠 ARIA Agent")
    st.caption(f"Session: `{st.session_state.session_id}`")
    st.divider()

    st.markdown("**Active use case**")
    from config.use_cases import USE_CASES
    use_case_options = {k: v["name"] for k, v in USE_CASES.items()}
    selected_uc = st.selectbox(
        "Use case",
        options=list(use_case_options.keys()),
        format_func=lambda x: use_case_options[x],
        index=list(use_case_options.keys()).index(st.session_state.use_case),
        label_visibility="collapsed"
    )
    if selected_uc != st.session_state.use_case:
        st.session_state.use_case = selected_uc
        scope_guard.set_use_case(selected_uc)
        st.rerun()

    st.divider()
    st.markdown("**Select Mode**")
    for mode, meta in MODES.items():
        is_active = st.session_state.current_mode == mode
        btn_label = f"{meta['icon']} {mode}"
        if is_active:
            st.markdown(
                f"<div style='padding:8px 12px;background:#E1F5EE;"
                f"border-radius:8px;border-left:3px solid #1D9E75;"
                f"font-size:13px;font-weight:500;color:#085041'>"
                f"{btn_label}</div>",
                unsafe_allow_html=True
            )
        else:
            if st.button(btn_label, key=f"mode_{mode}", use_container_width=True):
                st.session_state.current_mode = mode
                st.session_state.agent.set_mode(mode)
                st.rerun()

    st.divider()

    with st.expander("Generate policy doc"):
        policy_type = st.selectbox("Policy type", [
            "DATA_RETENTION", "ACCESS_CONTROL",
            "API_USAGE", "PRIVACY", "SECURITY"
        ])
        if st.button("Generate", use_container_width=True):
            with st.spinner("Generating policy..."):
                engine = PolicyEngine(
                    use_case_name=USE_CASES[st.session_state.use_case]["name"],
                    stack=USE_CASES[st.session_state.use_case]["stack"]
                )
                policy_text = engine.generate(policy_type)
                ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": f"**{policy_type} POLICY**\n\n{policy_text}",
                    "mode": "POLICY",
                    "timestamp": ts
                })
                st.rerun()

    with st.expander("Set project context"):
        ctx_key = st.text_input("Key", placeholder="e.g. use_case")
        ctx_val = st.text_input("Value", placeholder="e.g. AI Planner App")
        if st.button("Save context", use_container_width=True):
            if ctx_key and ctx_val:
                st.session_state.agent.set_context(ctx_key, ctx_val)
                st.success(f"Saved: {ctx_key}")

    st.divider()
    if st.button("🔄 Reset conversation", use_container_width=True):
        st.session_state.messages = []
        st.session_state.agent.reset()
        st.session_state.current_mode = "ARCHITECT"
        st.session_state.persistent_memory.clear_session()
        st.rerun()

    st.divider()
    st.caption("Phase 4 · Scope Guard + Persistent Memory")

# ─── Main area ──────────────────────────────────────────────────
col1, col2 = st.columns([6, 1])
with col1:
    st.markdown(
        f"## {MODES[st.session_state.current_mode]['icon']} "
        f"{st.session_state.current_mode} mode"
    )
with col2:
    st.caption(f"{len(st.session_state.messages)} messages")

st.divider()

# ─── Chat history ───────────────────────────────────────────────
for i, msg in enumerate(st.session_state.messages):
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg["role"] == "assistant":
            mode = msg.get("mode", "ARCHITECT")
            fname, mime = FILE_TYPES.get(mode, ("output.md", "text/markdown"))
            ts = msg.get("timestamp", "output")
            st.download_button(
                label="⬇ Download",
                data=msg["content"],
                file_name=f"ARIA_{mode}_{ts}.{fname.split('.')[-1]}",
                mime=mime,
                key=f"dl_{i}"
            )

# ─── Approval gate ──────────────────────────────────────────────
if st.session_state.pending_approval:
    pa = st.session_state.pending_approval
    st.warning(
        f"**Approval required**\n\n"
        f"{pa['reason']}\n\n"
        f"Original message: *{pa['message']}*"
    )
    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("Approve & continue", use_container_width=True, type="primary"):
            with st.spinner("Processing..."):
                response = st.session_state.agent.chat(pa["message"])
            ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            mode = st.session_state.current_mode
            st.session_state.messages.append({
                "role": "assistant", "content": response,
                "mode": mode, "timestamp": ts
            })
            st.session_state.persistent_memory.save_message(
                "assistant", response, mode
            )
            st.session_state.pending_approval = None
            st.rerun()
    with col_b:
        if st.button("Reject & rephrase", use_container_width=True):
            st.session_state.pending_approval = None
            st.rerun()

# ─── Chat input ─────────────────────────────────────────────────
if prompt := st.chat_input("Ask ARIA anything..."):

    scope_result = scope_guard.check(prompt)
    is_high_risk = scope_guard.is_high_risk(prompt)

    st.session_state.messages.append({"role": "user", "content": prompt})
    st.session_state.persistent_memory.save_message("user", prompt)

    with st.chat_message("user"):
        st.markdown(prompt)

    if scope_result["status"] == "out_of_scope":
        st.session_state.pending_approval = {
            "message": prompt,
            "reason": scope_result["reason"],
            "type": "out_of_scope"
        }
        st.rerun()

    elif is_high_risk:
        st.session_state.pending_approval = {
            "message": prompt,
            "reason": "This request may affect a critical system decision. Please review before proceeding.",
            "type": "high_risk"
        }
        st.rerun()

    else:
        with st.chat_message("assistant"):
            with st.spinner("ARIA is thinking..."):
                response = st.session_state.agent.chat(prompt)
            st.markdown(response)
            ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            mode = st.session_state.current_mode
            fname, mime = FILE_TYPES.get(mode, ("output.md", "text/markdown"))
            st.download_button(
                label="⬇ Download",
                data=response,
                file_name=f"ARIA_{mode}_{ts}.{fname.split('.')[-1]}",
                mime=mime,
                key=f"dl_latest_{ts}"
            )

        st.session_state.messages.append({
            "role": "assistant", "content": response,
            "mode": mode, "timestamp": ts
        })
        st.session_state.persistent_memory.save_message(
            "assistant", response, mode
        )