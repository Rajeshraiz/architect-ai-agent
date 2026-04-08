# app.py — Phase 6 Week 3
# New: Use Cases tab, dynamic tech stack, per-use-case GitHub repos

import streamlit as st
import datetime
import uuid

from agents.orchestrator import Orchestrator
from agents.scrum_master_agent import ScrumMasterAgent
from agents.scope_guard import ScopeGuard
from agents.policy_engine import PolicyEngine
from agents.approval_gate import ApprovalGate
from memory.persistent import PersistentMemory
from memory.task_store import TaskStore
from memory.use_case_store import UseCaseStore

st.set_page_config(
    page_title="ARIA Agent",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─── Session state ───────────────────────────────────────────────
DEFAULTS = {
    "dark_mode": True,
    "current_mode": "ARCHITECT",
    "current_uc_key": "AI_PLANNER",
    "messages": [],
    "pending_approval": None,
    "pending_task": None,
    "pending_task_batch": None,
    "show_new_task": False,
    "latest_standup": None,
    "standup_time": None,
    "show_new_uc_form": False,
    "uc_stack_suggestion": None,
}
for k, v in DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = v

if "agent" not in st.session_state:
    st.session_state.agent = Orchestrator()
if "scrum_master" not in st.session_state:
    st.session_state.scrum_master = ScrumMasterAgent()
if "task_store" not in st.session_state:
    st.session_state.task_store = TaskStore()
if "uc_store" not in st.session_state:
    st.session_state.uc_store = UseCaseStore()
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())[:8]
if "persistent_memory" not in st.session_state:
    st.session_state.persistent_memory = PersistentMemory(
        st.session_state.session_id)
    saved = st.session_state.persistent_memory.load_history()
    if saved:
        st.session_state.messages = saved

# ─── Load active use case ────────────────────────────────────────
uc_store: UseCaseStore = st.session_state.uc_store
active_uc = uc_store.get_by_key(st.session_state.current_uc_key) or {}
uc_name  = active_uc.get("name", "AI Planner App")
uc_repo  = active_uc.get("github_repo", "")
uc_stack = uc_store.get_stack_string(st.session_state.current_uc_key)

# ─── Dynamic scope guard ─────────────────────────────────────────
in_scope_kw, out_scope_kw = uc_store.get_scope_keywords(
    st.session_state.current_uc_key)
scope_guard = ScopeGuard(st.session_state.current_uc_key)
# Override keywords from DB
if in_scope_kw:
    scope_guard.use_case = {
        "name": uc_name,
        "in_scope": in_scope_kw,
        "out_of_scope": out_scope_kw
    }

# ─── Theme ───────────────────────────────────────────────────────
dark = st.session_state.dark_mode
T = {
    "bg":   "#0E0E14" if dark else "#F8F8FC",
    "bg2":  "#12121C" if dark else "#FFFFFF",
    "bg3":  "#1A1A2E" if dark else "#F0EFF8",
    "border":"#1E1E2E" if dark else "#E2E0F0",
    "text": "#E2E8F0" if dark else "#1A1A2E",
    "text2":"#8888AA" if dark else "#5A5A7A",
    "text3":"#3A3A55" if dark else "#A0A0C0",
    "accent":"#7C6EF8" if dark else "#534AB7",
    "card": "#16162A" if dark else "#FFFFFF",
    "cb":   "#252545" if dark else "#E2E0F0",
    "wbg":  "#1C1A0E" if dark else "#FFFBEB",
    "wb":   "#F59E0B44",
    "wt":   "#F59E0B",
    "todo": "#F59E0B",
    "prog": "#7C6EF8",
    "done": "#1D9E75",
}

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500&family=DM+Sans:wght@300;400;500;600&display=swap');
html,body,[class*="css"]{{font-family:'DM Sans',sans-serif;color:{T['text']}}}
.stApp{{background:{T['bg']}}}
.main .block-container{{padding-top:1.5rem;padding-bottom:2rem;max-width:960px}}
[data-testid="stSidebar"]{{background:{T['bg2']};border-right:1px solid {T['border']}}}
[data-testid="stSidebar"] p,[data-testid="stSidebar"] label,[data-testid="stSidebar"] span,[data-testid="stSidebar"] div{{color:{T['text']} !important}}
.stTabs [data-baseweb="tab-list"]{{background:{T['bg2']};border-radius:12px;padding:4px;gap:4px;border:1px solid {T['border']};margin-bottom:1.2rem}}
.stTabs [data-baseweb="tab"]{{background:transparent;border-radius:8px;color:{T['text2']} !important;font-family:'DM Sans',sans-serif;font-weight:500;font-size:13px;padding:6px 18px;border:none}}
.stTabs [aria-selected="true"]{{background:{T['bg3']} !important;color:{T['text']} !important}}
[data-testid="stChatMessage"]{{background:{T['card']} !important;border:1px solid {T['cb']};border-radius:10px;margin-bottom:8px}}
[data-testid="stChatMessage"] p,[data-testid="stChatMessage"] li{{color:{T['text']} !important}}
[data-testid="stChatInputTextArea"] textarea{{background:{T['bg2']} !important;border:1px solid {T['border']} !important;color:{T['text']} !important;border-radius:10px !important}}
.stButton>button{{background:{T['bg3']};border:1px solid {T['border']};color:{T['text']};border-radius:8px;font-family:'DM Sans',sans-serif;font-size:13px;transition:all 0.15s}}
.stButton>button:hover{{border-color:{T['accent']};color:{T['text']}}}
[data-testid="stDownloadButton"]>button{{font-size:11px;padding:4px 12px;margin-top:6px;opacity:0.7}}
[data-testid="stSelectbox"]>div>div{{background:{T['bg2']} !important;border-color:{T['border']} !important;color:{T['text']} !important}}
[data-testid="stTextInput"] input,[data-testid="stTextArea"] textarea{{background:{T['bg2']} !important;border-color:{T['border']} !important;color:{T['text']} !important}}
[data-testid="metric-container"]{{background:{T['card']};border:1px solid {T['cb']};border-radius:10px;padding:14px 16px}}
[data-testid="metric-container"] label{{color:{T['text2']} !important;font-size:12px !important}}
[data-testid="metric-container"] [data-testid="stMetricValue"]{{color:{T['text']} !important;font-size:22px !important;font-weight:600 !important}}
hr{{border-color:{T['border']} !important;opacity:0.5}}
[data-testid="stAlert"]{{background:{T['wbg']} !important;border-color:{T['wb']} !important;color:{T['text']} !important;border-radius:10px}}
[data-testid="stExpander"]{{background:{T['bg2']};border:1px solid {T['border']};border-radius:10px}}
[data-testid="stExpander"] summary{{color:{T['text2']} !important;font-size:13px}}
[data-testid="stForm"]{{background:{T['card']};border:1px solid {T['cb']};border-radius:12px;padding:16px}}
code{{background:{T['bg3']} !important;color:{T['accent']} !important;border-radius:4px;padding:1px 6px;font-family:'JetBrains Mono',monospace;font-size:12px}}
pre{{background:{T['bg3']} !important;border:1px solid {T['border']};border-radius:8px;padding:12px 16px}}
pre code{{background:transparent !important;color:{T['text']} !important;padding:0}}
::-webkit-scrollbar{{width:4px}}
::-webkit-scrollbar-track{{background:{T['bg']}}}
::-webkit-scrollbar-thumb{{background:{T['border']};border-radius:2px}}
/* Sticky tab bar — freezes tabs at top while scrolling */
[data-testid="stTabs"] > div:first-child {{
    position: sticky;
    top: 0;
    z-index: 999;
    background: {T['bg']};
    padding-top: 8px;
    padding-bottom: 4px;
    border-bottom: 1px solid {T['border']};
    margin-bottom: 0 !important;
}}
 
/* Ensure tab content scrolls underneath */
[data-testid="stTabs"] > div:nth-child(2) {{
    padding-top: 16px;
}}
</style>
""", unsafe_allow_html=True)

# ─── Constants ───────────────────────────────────────────────────
MODES = {
    "ARCHITECT":{"icon":"🏛️","color":"#534AB7","desc":"Design + ERD + tech stack"},
    "DEVELOPER":{"icon":"💻","color":"#1D9E75","desc":"Code + unit tests + PR"},
    "PLANNER":  {"icon":"📋","color":"#EF9F27","desc":"Tasks + epics + estimates"},
    "QA":       {"icon":"🧪","color":"#E24B4A","desc":"Tests + bug reports"},
    "POLICY":   {"icon":"📜","color":"#378ADD","desc":"GDPR + OWASP + SOC2"},
}
FILE_TYPES = {
    "ARCHITECT":("output.md","text/markdown"),
    "DEVELOPER":("output.py","text/x-python"),
    "PLANNER":  ("output.md","text/markdown"),
    "QA":       ("output.md","text/markdown"),
    "POLICY":   ("output.md","text/markdown"),
}

# ─── Sidebar ─────────────────────────────────────────────────────
with st.sidebar:
    cl, ct = st.columns([3,1])
    with cl:
        st.markdown(
            f"<div style='font-size:20px;font-weight:600;color:{T['text']};letter-spacing:-0.5px;margin-bottom:2px'>🧠 ARIA</div>"
            f"<div style='font-size:10px;color:{T['text3']};letter-spacing:1.5px'>ARCHITECT · AI · AGENT</div>",
            unsafe_allow_html=True)
    with ct:
        if st.button("🌙" if dark else "☀️", key="theme_btn"):
            st.session_state.dark_mode = not dark
            st.rerun()

    st.markdown(
        f"<div style='font-size:11px;color:{T['text3']};margin-top:4px'>"
        f"Session <span style='color:{T['accent']};font-family:JetBrains Mono'>"
        f"{st.session_state.session_id}</span></div>",
        unsafe_allow_html=True)
    st.divider()

    # Use case selector from Supabase
    st.markdown(f"<div style='font-size:11px;color:{T['text3']};letter-spacing:2px;text-transform:uppercase;margin-bottom:6px'>Active Use Case</div>", unsafe_allow_html=True)
    uc_options = uc_store.to_dropdown_options()
    if uc_options:
        sel_uc = st.selectbox(
            "uc", options=list(uc_options.keys()),
            format_func=lambda x: uc_options.get(x, x),
            index=list(uc_options.keys()).index(st.session_state.current_uc_key)
                  if st.session_state.current_uc_key in uc_options else 0,
            label_visibility="collapsed")
        if sel_uc != st.session_state.current_uc_key:
            st.session_state.current_uc_key = sel_uc
            st.session_state.messages = []
            st.session_state.agent.reset()
            st.rerun()
    else:
        st.info("No use cases yet — create one in the Use Cases tab.")

    # Show active repo
    if uc_repo:
        st.markdown(
            f"<div style='font-size:11px;color:{T['text3']};margin-top:4px'>"
            f"Repo: <span style='color:{T['accent']};font-family:JetBrains Mono'>{uc_repo}</span></div>",
            unsafe_allow_html=True)

    st.divider()

    # Mode buttons
    st.markdown(f"<div style='font-size:11px;color:{T['text3']};letter-spacing:2px;text-transform:uppercase;margin-bottom:8px'>Agent Mode</div>", unsafe_allow_html=True)
    for mode, meta in MODES.items():
        is_active = st.session_state.current_mode == mode
        if is_active:
            st.markdown(
                f"<div style='padding:10px 12px;background:{T['bg3']};border-radius:8px;"
                f"border-left:3px solid {meta['color']};margin-bottom:5px'>"
                f"<div style='font-size:13px;font-weight:500;color:{T['text']}'>{meta['icon']} {mode}</div>"
                f"<div style='font-size:11px;color:{T['text2']};margin-top:2px'>{meta['desc']}</div></div>",
                unsafe_allow_html=True)
        else:
            if st.button(f"{meta['icon']} {mode}", key=f"mode_{mode}",
                         use_container_width=True):
                st.session_state.current_mode = mode
                st.session_state.agent.set_mode(mode)
                st.rerun()

    st.divider()
    with st.expander("📜 Policy + Compliance"):
        pt = st.selectbox("pt",["DATA_RETENTION","ACCESS_CONTROL","API_USAGE","PRIVACY","SECURITY"],label_visibility="collapsed")
        if st.button("Generate policy", use_container_width=True):
            with st.spinner("Generating..."):
                engine = PolicyEngine(use_case_name=uc_name, stack=uc_stack)
                policy_text = engine.generate(pt)
                ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                st.session_state.messages.append({
                    "role":"assistant",
                    "content":f"**{pt} POLICY**\n\n{policy_text}",
                    "mode":"POLICY","timestamp":ts})
                st.rerun()

    with st.expander("⚙️ Project context"):
        ck = st.text_input("Key", placeholder="e.g. stack", key="ctx_k")
        cv = st.text_input("Value", placeholder="e.g. FastAPI", key="ctx_v")
        if st.button("Save context", use_container_width=True):
            if ck and cv:
                st.session_state.agent.set_context(ck, cv)
                st.success(f"Saved: {ck}")

    st.divider()
    if st.button("🔄 Reset conversation", use_container_width=True):
        st.session_state.messages = []
        st.session_state.agent.reset()
        st.session_state.current_mode = "ARCHITECT"
        st.session_state.persistent_memory.clear_session()
        st.session_state.pending_approval = None
        st.session_state.pending_task = None
        st.session_state.pending_task_batch = None
        st.rerun()

    st.markdown(f"<div style='font-size:10px;color:{T['text3']};text-align:center;margin-top:8px'>Phase 6 W3 · ARIA Hybrid Agent</div>", unsafe_allow_html=True)

# ─── Tabs ────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs(["💬  Chat","📋  Task Board","🗂  Use Cases","📊  Standup"])


# ════════════════════════════════════════
# TAB 1 — CHAT
# ════════════════════════════════════════
with tab1:
    mode = st.session_state.current_mode
    meta = MODES[mode]
    hc1, hc2 = st.columns([5,1])
    with hc1:
        ac = meta['color']
        st.markdown(
            f"<div style='display:flex;align-items:center;gap:10px;margin-bottom:4px'>"
            f"<span style='font-size:22px'>{meta['icon']}</span>"
            f"<span style='font-size:18px;font-weight:500;color:{T['text']}'>{mode} mode</span>"
            f"<span style='font-size:11px;padding:3px 10px;border-radius:20px;"
            f"background:{T['bg3']};color:{ac};border:1px solid {ac}44'>{meta['desc']}</span>"
            f"</div>",
            unsafe_allow_html=True)
    with hc2:
        st.markdown(f"<div style='text-align:right;font-size:11px;color:{T['text3']};padding-top:8px'>{len(st.session_state.messages)} msgs</div>", unsafe_allow_html=True)
    st.divider()

    # Chat history
    for i, msg in enumerate(st.session_state.messages):
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg["role"] == "assistant":
                m = msg.get("mode","ARCHITECT")
                fname, mime = FILE_TYPES.get(m,("output.md","text/markdown"))
                ts_v = msg.get("timestamp","output")
                st.download_button(
                    label="⬇ Download", data=msg["content"],
                    file_name=f"ARIA_{m}_{ts_v}.{fname.split('.')[-1]}",
                    mime=mime, key=f"dl_{i}")

                # Approve Architecture button
                if m == "ARCHITECT" and not msg.get("arch_approved"):
                    if st.button("✅ Approve Architecture — generate tasks",
                                 key=f"approve_arch_{i}"):
                        with st.spinner("Saving architecture..."):
                            saved_arch = st.session_state.task_store.save_architecture(
                                st.session_state.current_uc_key,
                                msg["content"])
                        arch_id = saved_arch["id"] if saved_arch else None
                        with st.spinner("Scrum Master generating task breakdown..."):
                            tasks = st.session_state.scrum_master\
                                .generate_tasks_from_architecture(
                                    msg["content"],
                                    st.session_state.current_uc_key)
                        if tasks:
                            st.session_state.pending_task_batch = {
                                "tasks": tasks,
                                "architecture_id": arch_id,
                                "use_case": st.session_state.current_uc_key
                            }
                            st.session_state.messages[i]["arch_approved"] = True
                        else:
                            st.error("Could not generate tasks. Ask ARIA to elaborate on the design first.")
                        st.rerun()

                # PR creation button — appears when Developer signals ready
                if m == "DEVELOPER" and "ARIA_PR_READY:" in msg["content"]:
                    pr_key = f"pr_create_{i}"
                    if not msg.get("pr_created"):
 
                        # Parse filename and description from signal line
                        try:
                            signal_line = [
                                l for l in msg["content"].split("\\n")
                                if "ARIA_PR_READY:" in l
                            ][0]
                            parts = signal_line.replace("ARIA_PR_READY:","").strip().split("|")
                            pr_filename = parts[0].strip() if parts else "src/output.py"
                            pr_desc     = parts[1].strip() if len(parts) > 1 else "ARIA generated code"
                        except Exception:
                            pr_filename = "src/output.py"
                            pr_desc     = "ARIA generated code"
 
                        # Get active use case repo
                        active_uc_data = uc_store.get_by_key(
                            st.session_state.current_uc_key)
                        uc_repo_name = active_uc_data.get(
                            "github_repo","") if active_uc_data else ""
 
                        if uc_repo_name:
                            st.markdown(
                                f"<div style='background:{T['bg3']};border:1px solid "
                                f"{T['accent']}44;border-radius:8px;padding:10px 14px;"
                                f"margin-top:8px'>"
                                f"<div style='font-size:12px;color:{T['text2']};margin-bottom:6px'>"
                                f"Ready to create PR in <code>{uc_repo_name}</code></div>"
                                f"<div style='font-size:11px;color:{T['text3']}'>"
                                f"File: {pr_filename}</div></div>",
                                unsafe_allow_html=True)
 
                            if st.button(
                                f"🔀 Create GitHub PR — {pr_desc[:50]}",
                                key=pr_key,
                                use_container_width=False
                            ):
                                with st.spinner("Creating PR on GitHub..."):
                                    try:
                                        from integrations.github_integration import GitHubIntegration
                                        gh = GitHubIntegration()
 
                                        # Extract code block from response
                                        content = msg["content"]
                                        code_start = content.find("```")
                                        code_end   = content.rfind("```")
                                        if code_start >= 0 and code_end > code_start:
                                            code_block = content[code_start:code_end+3]
                                            # Remove markdown fences
                                            lines = code_block.split("\\n")
                                            code_only = "\\n".join(
                                                lines[1:-1] if len(lines) > 2 else lines
                                            )
                                        else:
                                            code_only = content
 
                                        pr_url, ok, pr_msg = gh.create_pr(
                                            repo_name=uc_repo_name,
                                            title=pr_desc,
                                            code=code_only,
                                            filename=pr_filename,
                                            description=f"Generated by ARIA in DEVELOPER mode.\\n\\n{pr_desc}",
                                            mode="DEVELOPER"
                                        )
 
                                        if ok:
                                            st.session_state.messages[i]["pr_created"] = True
                                            st.session_state.messages[i]["pr_url"] = pr_url
                                            ts_pr = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                                            st.session_state.messages.append({
                                                "role": "assistant",
                                                "content": (
                                                    f"PR created successfully in `{uc_repo_name}`\\n\\n"
                                                    f"[View PR on GitHub]({pr_url})\\n\\n"
                                                    f"CI will run tests automatically. "
                                                    f"The task will move to **In Progress** on the Kanban board."
                                                ),
                                                "mode": "DEVELOPER",
                                                "timestamp": ts_pr
                                            })
                                            st.rerun()
                                        else:
                                            st.error(f"PR failed: {pr_msg}")
                                    except Exception as e:
                                        st.error(f"GitHub error: {e}")
                        else:
                            st.warning(
                                "No GitHub repo configured for this use case. "
                                "Go to the Use Cases tab and add a repo name."
                            )
 
                # Show PR link if already created
                elif m == "DEVELOPER" and msg.get("pr_url"):
                    pr_url_val = msg["pr_url"]
                    ac = T["accent"]
                    st.markdown(
                        f"<a href='{pr_url_val}' target='_blank' "
                        f"style='font-size:11px;color:{ac}'>View PR on GitHub →</a>",
                        unsafe_allow_html=True)        

    # Task batch preview
    if st.session_state.pending_task_batch:
        batch = st.session_state.pending_task_batch
        tasks = batch["tasks"]
        phases = {}
        for t in tasks:
            phases.setdefault(t.get("phase","Phase 1"), []).append(t)
        total_h = sum(t.get("estimated_hours",0) for t in tasks)
        ac = T["accent"]
        st.markdown(
            f"<div style='background:{T['bg3']};border:1px solid {ac}44;"
            f"border-radius:12px;padding:16px;margin:10px 0'>"
            f"<div style='font-size:14px;font-weight:500;color:{T['text']};margin-bottom:4px'>"
            f"📋 {len(tasks)} tasks across {len(phases)} phases — {total_h}h estimated</div>"
            f"<div style='font-size:12px;color:{T['text2']}'>Review then approve to add to Kanban</div></div>",
            unsafe_allow_html=True)

        for ph, ph_tasks in phases.items():
            ph_h = sum(t.get("estimated_hours",0) for t in ph_tasks)
            st.markdown(f"<div style='font-size:11px;font-weight:500;color:{ac};letter-spacing:1px;text-transform:uppercase;margin:10px 0 6px'>{ph} · {len(ph_tasks)} tasks · {ph_h}h</div>", unsafe_allow_html=True)
            for t in ph_tasks:
                p = t.get("priority","P2")
                pc = {"P1":"#EF4444","P2":"#F59E0B","P3":"#888"}.get(p,"#888")
                h = t.get("estimated_hours",0)
                title = t.get("title","")
                desc = t.get("description","")
                desc_s = (desc[:100]+"...") if len(desc)>100 else desc
                assigned = t.get("assigned_to","")
                dep = t.get("depends_on_index")
                dep_t = f" · depends on task {dep+1}" if dep is not None else ""
                card_bg = T["card"]
                card_b = T["cb"]
                text_c = T["text"]
                text2_c = T["text2"]
                text3_c = T["text3"]
                desc_html = f"<div style='font-size:11px;color:{text3_c};margin-top:4px'>{desc_s}</div>" if desc_s else ""
                st.markdown(
                    f"<div style='background:{card_bg};border:1px solid {card_b};"
                    f"border-radius:8px;padding:10px 14px;margin-bottom:6px'>"
                    f"<div style='display:flex;justify-content:space-between'>"
                    f"<div style='font-size:13px;font-weight:500;color:{text_c}'>{title}</div>"
                    f"<div style='font-size:11px;color:{text2_c};flex-shrink:0;margin-left:10px'>{h}h</div></div>"
                    f"<div style='font-size:11px;color:{text2_c};margin-top:4px'>"
                    f"<span style='color:{pc};font-weight:600'>{p}</span> · {assigned}{dep_t}</div>"
                    f"{desc_html}</div>",
                    unsafe_allow_html=True)

        ba, bb, bc = st.columns(3)
        with ba:
            if st.button(f"✅ Approve all {len(tasks)} tasks",
                         use_container_width=True, key="approve_batch"):
                with st.spinner(f"Adding {len(tasks)} tasks to Kanban..."):
                    created = st.session_state.task_store.batch_create_tasks(
                        tasks, batch["use_case"], batch.get("architecture_id"))
                st.session_state.pending_task_batch = None
                ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                summary = "\n".join([
                    f"- **{t['title']}** — {t.get('phase','')} · {t.get('priority','P2')} · {t.get('assigned_to','')}"
                    for t in created[:8]])
                more = f"\n\n...and {len(created)-8} more." if len(created)>8 else ""
                st.session_state.messages.append({
                    "role":"assistant",
                    "content":f"**{len(created)} tasks added to Kanban.**\n\n{summary}{more}\n\nSwitch to the Task Board tab.",
                    "mode":"PLANNER","timestamp":ts})
                st.rerun()
        with bb:
            if st.button("✏️ Edit before approving",
                         use_container_width=True, key="edit_batch"):
                st.info("Approve the batch first, then edit individual tasks on the Task Board.")
        with bc:
            if st.button("❌ Reject batch",
                         use_container_width=True, key="reject_batch"):
                st.session_state.pending_task_batch = None
                st.rerun()

    # Single task approval
    if st.session_state.pending_task:
        pt_t = st.session_state.pending_task
        wbg = T['wbg']; wb = T['wb']; wt = T['wt']
        text_c = T['text']; text2_c = T['text2']; text3_c = T['text3']
        st.markdown(
            f"<div style='background:{wbg};border:1px solid {wb};"
            f"border-radius:10px;padding:16px;margin:8px 0'>"
            f"<div style='font-size:12px;color:{wt};font-weight:600;margin-bottom:8px'>⏳ Task approval required</div>"
            f"<div style='font-size:14px;font-weight:500;color:{text_c};margin-bottom:6px'>{pt_t.get('title','')}</div>"
            f"<div style='font-size:12px;color:{text2_c}'>Priority: {pt_t.get('priority','P2')} · Assign to: {pt_t.get('assigned_to','TBD')}</div>"
            f"<div style='font-size:12px;color:{text3_c};margin-top:4px'>{pt_t.get('reason','')}</div></div>",
            unsafe_allow_html=True)
        ta, tb = st.columns(2)
        with ta:
            if st.button("✅ Approve task", use_container_width=True, key="approve_task"):
                created = ApprovalGate.approve_task(pt_t, st.session_state.current_uc_key)
                if created:
                    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                    st.session_state.messages.append({
                        "role":"assistant",
                        "content":f"Task approved.\n\n**{pt_t.get('title')}** added to Kanban.",
                        "mode":"PLANNER","timestamp":ts})
                st.session_state.pending_task = None
                st.rerun()
        with tb:
            if st.button("❌ Reject task", use_container_width=True, key="reject_task"):
                st.session_state.pending_task = None
                st.rerun()

    # Scope approval
    if st.session_state.pending_approval:
        pa = st.session_state.pending_approval
        st.warning(f"**Approval required**\n\n{pa['reason']}\n\n*Original: {pa['message']}*")
        sa, sb = st.columns(2)
        with sa:
            if st.button("Approve & continue", use_container_width=True,
                         type="primary", key="approve_scope"):
                with st.spinner("Processing..."):
                    response = st.session_state.agent.chat(pa["message"])
                ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                m = st.session_state.current_mode
                st.session_state.messages.append({"role":"assistant","content":response,"mode":m,"timestamp":ts})
                st.session_state.persistent_memory.save_message("assistant",response,m)
                st.session_state.pending_approval = None
                st.rerun()
        with sb:
            if st.button("Reject & rephrase", use_container_width=True, key="reject_scope"):
                st.session_state.pending_approval = None
                st.rerun()

    # Chat input
    if prompt := st.chat_input("Ask ARIA anything..."):
        scope_result = scope_guard.check(prompt)
        is_hr = scope_guard.is_high_risk(prompt)
        st.session_state.messages.append({"role":"user","content":prompt})
        st.session_state.persistent_memory.save_message("user", prompt)
        with st.chat_message("user"):
            st.markdown(prompt)
        if scope_result["status"] == "out_of_scope":
            st.session_state.pending_approval = {"message":prompt,"reason":scope_result["reason"],"type":"out_of_scope"}
            st.rerun()
        elif is_hr:
            st.session_state.pending_approval = {"message":prompt,"reason":"This may affect a critical system decision.","type":"high_risk"}
            st.rerun()
        else:
            with st.chat_message("assistant"):
                with st.spinner(f"ARIA thinking in {mode} mode..."):
                    response = st.session_state.agent.chat(prompt)
                st.markdown(response)
                ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                fname, mime = FILE_TYPES.get(mode,("output.md","text/markdown"))
                st.download_button(label="⬇ Download", data=response,
                    file_name=f"ARIA_{mode}_{ts}.{fname.split('.')[-1]}",
                    mime=mime, key=f"dl_latest_{ts}")
            st.session_state.messages.append({"role":"assistant","content":response,"mode":mode,"timestamp":ts})
            st.session_state.persistent_memory.save_message("assistant",response,mode)
            suggestion = st.session_state.scrum_master.scan_for_tasks(
                st.session_state.messages, st.session_state.current_uc_key)
            if suggestion:
                st.session_state.pending_task = suggestion
                st.rerun()


# ════════════════════════════════════════
# TAB 2 — TASK BOARD
# ════════════════════════════════════════
with tab2:
    bh1, bh2 = st.columns([4,1])
    with bh1:
        st.markdown(
            f"<div style='font-size:18px;font-weight:500;color:{T['text']};margin-bottom:4px'>📋 Task Board</div>"
            f"<div style='font-size:12px;color:{T['text2']}'>{uc_name}</div>",
            unsafe_allow_html=True)
    with bh2:
        if st.button("+ New task", use_container_width=True, key="new_task_btn"):
            st.session_state.show_new_task = not st.session_state.show_new_task
    st.divider()

    if st.session_state.show_new_task:
        with st.form("new_task_form"):
            t_title = st.text_input("Title", placeholder="e.g. Fix login timeout bug")
            t_desc  = st.text_area("Description", height=70)
            fc1,fc2,fc3 = st.columns(3)
            with fc1: t_pri = st.selectbox("Priority",["P1","P2","P3"])
            with fc2: t_assign = st.selectbox("Assign to",["DEVELOPER","ARCHITECT","QA","POLICY","PLANNER"])
            with fc3: t_phase = st.text_input("Phase", value="Phase 1")
            if st.form_submit_button("Create task") and t_title:
                new_t = st.session_state.task_store.create_task(
                    use_case=st.session_state.current_uc_key,
                    title=t_title, description=t_desc,
                    assigned_to=t_assign, created_by="PRODUCT_OWNER",
                    priority=t_pri, phase=t_phase)
                if new_t:
                    st.session_state.task_store.approve_task(new_t["id"], True, "Created by PO")
                st.session_state.show_new_task = False
                st.rerun()

    phases_data = st.session_state.task_store.get_tasks_by_phase(st.session_state.current_uc_key)
    all_tasks = st.session_state.task_store.get_tasks(st.session_state.current_uc_key)
    approved = [t for t in all_tasks if t.get("po_approved")]
    todo_t = [t for t in approved if t["status"]=="todo"]
    prog_t = [t for t in approved if t["status"]=="in_progress"]
    done_t = [t for t in approved if t["status"]=="done"]

    m1,m2,m3,m4 = st.columns(4)
    m1.metric("Total", len(approved))
    m2.metric("To Do", len(todo_t))
    m3.metric("In Progress", len(prog_t))
    m4.metric("Done", len(done_t))
    st.divider()

    def task_card(task, col_key):
        p = task.get("priority","P2")
        pc = {"P1":"#EF4444","P2":"#F59E0B","P3":"#888"}.get(p,"#888")
        desc = task.get("description","")
        desc_s = (desc[:80]+"...") if len(desc)>80 else desc
        pr = task.get("github_pr_url","")
        h = task.get("estimated_hours",0)
        assigned = task.get("assigned_to","")
        title = task["title"]
        cb = T["card"]; cbb = T["cb"]
        tc = T["text"]; tc2 = T["text2"]; tc3 = T["text3"]; ac = T["accent"]
        pr_html = f" &middot; <a href='{pr}' target='_blank' style='color:{ac}'>PR</a>" if pr else ""
        h_html = f" &middot; {h}h" if h else ""
        d_html = f"<div style='font-size:11px;color:{tc3};margin-top:4px'>{desc_s}</div>" if desc_s else ""
        st.markdown(
            f"<div style='background:{cb};border:1px solid {cbb};border-radius:8px;padding:11px 14px;margin-bottom:8px'>"
            f"<div style='font-size:13px;font-weight:500;color:{tc};margin-bottom:5px'>{title}</div>"
            f"<div style='font-size:11px;color:{tc2}'><span style='color:{pc};font-weight:600'>{p}</span>"
            f" &middot; {assigned}{h_html}{pr_html}</div>{d_html}</div>",
            unsafe_allow_html=True)
        s = task["status"]
        ca,cb2 = st.columns(2)
        if s=="todo":
            with ca:
                if st.button("▶ Start",key=f"s_{task['id']}_{col_key}",use_container_width=True):
                    st.session_state.task_store.update_status(task["id"],"in_progress"); st.rerun()
        elif s=="in_progress":
            with ca:
                if st.button("✅ Done",key=f"d_{task['id']}_{col_key}",use_container_width=True):
                    st.session_state.task_store.update_status(task["id"],"done"); st.rerun()
            with cb2:
                if st.button("↩ Todo",key=f"b_{task['id']}_{col_key}",use_container_width=True):
                    st.session_state.task_store.update_status(task["id"],"todo"); st.rerun()
        elif s=="done":
            with ca:
                if st.button("↩ Reopen",key=f"r_{task['id']}_{col_key}",use_container_width=True):
                    st.session_state.task_store.update_status(task["id"],"in_progress"); st.rerun()

    if not phases_data:
        st.markdown(f"<div style='text-align:center;padding:60px 0;font-size:13px;color:{T['text3']}'>No tasks yet. Switch to ARCHITECT mode, generate a design,<br>then click <strong>Approve Architecture</strong> to auto-generate tasks.</div>", unsafe_allow_html=True)
    else:
        for ph_name in sorted(phases_data.keys()):
            ph_tasks = [t for t in phases_data[ph_name] if t.get("po_approved")]
            if not ph_tasks:
                continue
            done_c = sum(1 for t in ph_tasks if t["status"]=="done")
            total_c = len(ph_tasks)
            pct = round((done_c/total_c)*100) if total_c else 0
            all_done = done_c == total_c
            hc = T["done"] if all_done else T["accent"]
            badge = f"<div style='font-size:11px;padding:2px 10px;border-radius:20px;background:#E1F5EE;color:#085041'>Phase complete</div>" if all_done else ""
            st.markdown(
                f"<div style='display:flex;align-items:center;gap:12px;margin:16px 0 10px'>"
                f"<div style='font-size:13px;font-weight:500;color:{hc}'>{ph_name}</div>"
                f"<div style='flex:1;height:3px;background:{T['border']};border-radius:2px;overflow:hidden'>"
                f"<div style='height:100%;width:{pct}%;background:{hc};transition:width 0.4s'></div></div>"
                f"<div style='font-size:11px;color:{T['text3']}'>{done_c}/{total_c}</div>{badge}</div>",
                unsafe_allow_html=True)
            todo_p = [t for t in ph_tasks if t["status"]=="todo"]
            prog_p = [t for t in ph_tasks if t["status"]=="in_progress"]
            done_p = [t for t in ph_tasks if t["status"]=="done"]
            k1,k2,k3 = st.columns(3)
            with k1:
                st.markdown(f"<div style='font-size:10px;letter-spacing:2px;text-transform:uppercase;color:{T['todo']};margin-bottom:10px;font-family:JetBrains Mono'>TO DO · {len(todo_p)}</div>", unsafe_allow_html=True)
                if not todo_p: st.markdown(f"<div style='font-size:11px;color:{T['text3']};text-align:center;padding:16px 0'>—</div>", unsafe_allow_html=True)
                for t in todo_p: task_card(t, f"todo_{ph_name[:4]}")
            with k2:
                st.markdown(f"<div style='font-size:10px;letter-spacing:2px;text-transform:uppercase;color:{T['prog']};margin-bottom:10px;font-family:JetBrains Mono'>IN PROGRESS · {len(prog_p)}</div>", unsafe_allow_html=True)
                if not prog_p: st.markdown(f"<div style='font-size:11px;color:{T['text3']};text-align:center;padding:16px 0'>—</div>", unsafe_allow_html=True)
                for t in prog_p: task_card(t, f"prog_{ph_name[:4]}")
            with k3:
                st.markdown(f"<div style='font-size:10px;letter-spacing:2px;text-transform:uppercase;color:{T['done']};margin-bottom:10px;font-family:JetBrains Mono'>DONE · {len(done_p)}</div>", unsafe_allow_html=True)
                if not done_p: st.markdown(f"<div style='font-size:11px;color:{T['text3']};text-align:center;padding:16px 0'>—</div>", unsafe_allow_html=True)
                for t in done_p: task_card(t, f"done_{ph_name[:4]}")
            st.divider()


# ════════════════════════════════════════
# TAB 3 — USE CASES
# ════════════════════════════════════════
with tab3:
    uch1, uch2 = st.columns([4,1])
    with uch1:
        st.markdown(
            f"<div style='font-size:18px;font-weight:500;color:{T['text']};margin-bottom:4px'>🗂 Use Cases</div>"
            f"<div style='font-size:12px;color:{T['text2']}'>Manage all your use cases and tech stacks</div>",
            unsafe_allow_html=True)
    with uch2:
        if st.button("+ New use case", use_container_width=True, key="new_uc_btn"):
            st.session_state.show_new_uc_form = not st.session_state.show_new_uc_form

    st.divider()

    # New use case form
    if st.session_state.show_new_uc_form:
        with st.form("new_uc_form"):
            st.markdown(f"<div style='font-size:14px;font-weight:500;color:{T['text']};margin-bottom:12px'>Create new use case</div>", unsafe_allow_html=True)

            uc_col1, uc_col2 = st.columns(2)
            with uc_col1:
                new_uc_name = st.text_input("Use case name *", placeholder="e.g. Invoice Management App")
                new_uc_key  = st.text_input("Key (unique, no spaces) *", placeholder="e.g. INVOICE_APP")
            with uc_col2:
                new_uc_desc = st.text_area("Description", placeholder="What does this app do?", height=100)

            st.markdown(f"<div style='font-size:12px;font-weight:500;color:{T['text2']};margin:10px 0 6px'>GitHub Repository</div>", unsafe_allow_html=True)
            gc1, gc2 = st.columns([3,1])
            with gc1:
                new_uc_repo = st.text_input("Repo name", placeholder="e.g. Rajeshraiz/invoice-app")
            with gc2:
                create_repo_opt = st.selectbox("Auto-create?", ["Ask me","Yes — create it","No — I will create manually"])

            st.markdown(f"<div style='font-size:12px;font-weight:500;color:{T['text2']};margin:10px 0 4px'>Tech Stack — leave blank for ARIA to suggest best fit</div>", unsafe_allow_html=True)
            sc1, sc2, sc3 = st.columns(3)
            with sc1:
                new_frontend = st.text_input("Frontend", placeholder="e.g. React Native")
                new_backend  = st.text_input("Backend",  placeholder="e.g. FastAPI")
            with sc2:
                new_database = st.text_input("Database", placeholder="e.g. Supabase")
                new_ai       = st.text_input("AI Layer",  placeholder="e.g. Claude API")
            with sc3:
                new_hosting  = st.text_input("Hosting",  placeholder="e.g. Railway + Vercel")
                new_auth     = st.text_input("Auth",     placeholder="e.g. Supabase Auth")

            st.markdown(f"<div style='font-size:12px;font-weight:500;color:{T['text2']};margin:10px 0 4px'>Scope (comma separated keywords)</div>", unsafe_allow_html=True)
            new_in  = st.text_input("In scope", placeholder="invoice, payment, pdf, export, dashboard")
            new_out = st.text_input("Out of scope", placeholder="voice, offline, mobile native")

            submitted = st.form_submit_button("Create use case")
            if submitted:
                if not new_uc_name or not new_uc_key:
                    st.error("Name and Key are required.")
                else:
                    # Handle GitHub repo
                    #repo_to_save = new_uc_repo
                    #repo_created = False

                    #if create_repo_opt == "Yes — create it" and new_uc_repo:
                        #try:
                            #from integrations.github_integration import GitHubIntegration
                            #gh = GitHubIntegration()
                            #_, success, msg = gh.create_repo(
                            #    new_uc_repo, new_uc_desc)
                            #if success:
                            #    st.success(f"GitHub repo created: {new_uc_repo}")
                            #    repo_created = True
                            #else:
                            #    st.warning(f"Could not create repo: {msg}")
                        #except Exception as e:
                            #st.warning(f"GitHub error: {e}")
                            # Handle GitHub repo
                    repo_to_save = new_uc_repo
                    repo_created = False
                    webhook_created = False
 
                    if create_repo_opt == "Yes — create it" and new_uc_repo:
                        try:
                            from integrations.github_integration import GitHubIntegration
                            gh = GitHubIntegration()
 
                            # One call: creates repo + webhook automatically
                            setup = gh.setup_repo_with_webhook(
                                new_uc_repo, new_uc_desc
                            )
 
                            if setup["repo_ok"]:
                                repo_created = True
                                st.success(f"GitHub repo created: {new_uc_repo}")
                            else:
                                st.warning(f"Could not create repo: {setup['messages'][0]}")
 
                            if setup.get("webhook_ok"):
                                webhook_created = True
                                st.success("Webhook configured automatically — Kanban will auto-update on PRs")
                            else:
                                # Webhook failed but repo is ok — show warning not error
                                if len(setup["messages"]) > 1:
                                    st.info(setup["messages"][-1])
 
                        except Exception as e:
                            st.warning(f"GitHub error: {e}")

                    # If stack fields left blank, ARIA suggests defaults
                    final_backend  = new_backend  or "FastAPI"
                    final_frontend = new_frontend or "React Native"
                    final_database = new_database or "Supabase (PostgreSQL)"
                    final_ai       = new_ai       or "Claude API (claude-sonnet-4)"
                    final_hosting  = new_hosting  or "Railway + Vercel"
                    final_auth     = new_auth     or "Supabase Auth"

                    created_uc = uc_store.create(
                        key=new_uc_key,
                        name=new_uc_name,
                        description=new_uc_desc,
                        github_repo=repo_to_save,
                        stack_frontend=final_frontend,
                        stack_backend=final_backend,
                        stack_database=final_database,
                        stack_ai=final_ai,
                        stack_hosting=final_hosting,
                        stack_auth=final_auth,
                        in_scope=new_in,
                        out_of_scope=new_out
                    )
                    if created_uc:
                        if repo_created:
                            uc_store.mark_repo_created(new_uc_key)
                        st.success(f"Use case '{new_uc_name}' created!")
                        st.session_state.show_new_uc_form = False
                        st.rerun()
                    else:
                        st.error("Could not create use case. Key may already exist.")

    # List existing use cases
    all_ucs = uc_store.get_all()
    if not all_ucs:
        st.markdown(f"<div style='text-align:center;padding:40px 0;font-size:13px;color:{T['text3']}'>No use cases yet. Click + New use case to create one.</div>", unsafe_allow_html=True)
    else:
        for uc in all_ucs:
            is_active = uc["key"] == st.session_state.current_uc_key
            border_c = T["accent"] if is_active else T["cb"]
            bg_c = T["bg3"] if is_active else T["card"]

            with st.expander(
                f"{'▶ ' if is_active else ''}{uc['name']} {'(active)' if is_active else ''}",
                expanded=is_active
            ):
                ec1, ec2 = st.columns([3,1])
                with ec1:
                    st.markdown(f"<div style='font-size:12px;color:{T['text2']};margin-bottom:8px'>{uc.get('description','')}</div>", unsafe_allow_html=True)
                    repo = uc.get("github_repo","")
                    if repo:
                        repo_url = f"https://github.com/{repo}"
                        st.markdown(f"<div style='font-size:11px;color:{T['text3']}'>Repo: <a href='{repo_url}' target='_blank' style='color:{T['accent']}'>{repo}</a></div>", unsafe_allow_html=True)
                with ec2:
                    if not is_active:
                        if st.button("Set active", key=f"set_{uc['key']}", use_container_width=True):
                            st.session_state.current_uc_key = uc["key"]
                            st.session_state.messages = []
                            st.session_state.agent.reset()
                            st.rerun()

                # Tech stack display + edit
                st.markdown(f"<div style='font-size:11px;font-weight:500;color:{T['text2']};letter-spacing:1px;text-transform:uppercase;margin:10px 0 8px'>Tech Stack</div>", unsafe_allow_html=True)
                sc1, sc2, sc3 = st.columns(3)
                stack_fields = [
                    ("Frontend",  "stack_frontend"),
                    ("Backend",   "stack_backend"),
                    ("Database",  "stack_database"),
                    ("AI Layer",  "stack_ai"),
                    ("Hosting",   "stack_hosting"),
                    ("Auth",      "stack_auth"),
                ]
                for idx, (label, field) in enumerate(stack_fields):
                    col = [sc1,sc2,sc3][idx%3]
                    with col:
                        new_val = st.text_input(
                            label,
                            value=uc.get(field,""),
                            key=f"stack_{uc['key']}_{field}")
                        if new_val != uc.get(field,""):
                            uc_store.update(uc["key"], **{field: new_val})

                # Scope keywords
                with st.expander("Scope keywords"):
                    new_in_s = st.text_area(
                        "In scope (comma separated)",
                        value=uc.get("in_scope",""), height=70,
                        key=f"in_{uc['key']}")
                    new_out_s = st.text_area(
                        "Out of scope (comma separated)",
                        value=uc.get("out_of_scope",""), height=70,
                        key=f"out_{uc['key']}")
                    if st.button("Save scope", key=f"save_scope_{uc['key']}"):
                        uc_store.update(uc["key"],
                                        in_scope=new_in_s,
                                        out_of_scope=new_out_s)
                        st.success("Scope saved.")
                        st.rerun()

                # Danger zone
                if not is_active:
                    if st.button(f"Delete {uc['name']}", key=f"del_{uc['key']}"):
                        uc_store.deactivate(uc["key"])
                        st.rerun()


# ════════════════════════════════════════
# TAB 4 — STANDUP
# ════════════════════════════════════════
with tab4:
    sh1, sh2 = st.columns([4,1])
    with sh1:
        st.markdown(
            f"<div style='font-size:18px;font-weight:500;color:{T['text']};margin-bottom:4px'>📊 Daily Standup</div>"
            f"<div style='font-size:12px;color:{T['text2']}'>Generated by Scrum Master agent</div>",
            unsafe_allow_html=True)
    with sh2:
        if st.button("Generate", use_container_width=True, key="gen_standup"):
            with st.spinner("Generating standup..."):
                standup = st.session_state.scrum_master.generate_standup(
                    st.session_state.current_uc_key)
                st.session_state.latest_standup = standup
                st.session_state.standup_time = datetime.datetime.now().strftime("%b %d %Y · %H:%M")
    st.divider()
    if st.session_state.latest_standup:
        st.markdown(f"<div style='font-size:11px;color:{T['text3']};margin-bottom:12px'>Last generated: {st.session_state.standup_time}</div>", unsafe_allow_html=True)
        st.markdown(st.session_state.latest_standup)
        st.divider()
        st.download_button(
            label="⬇ Download standup",
            data=st.session_state.latest_standup,
            file_name=f"standup_{datetime.datetime.now().strftime('%Y%m%d')}.md",
            mime="text/markdown")
    else:
        st.markdown(f"<div style='font-size:13px;color:{T['text3']};text-align:center;padding:60px 0'>Click Generate to create today's standup summary</div>", unsafe_allow_html=True)