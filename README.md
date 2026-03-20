# architect-ai-agent
# ARIA Agent — Architect, Requirements and Implementation Agent

A production AI agent built with Claude API + Streamlit that acts as a
Senior Software Architect and Developer for your software use cases.

## Live App
https://aria-agent.streamlit.app/

## What it does
- **ARCHITECT mode** — system design, ERD, API contracts, tech stack decisions
- **DEVELOPER mode** — production Python and React code generation
- **PLANNER mode** — Epic > Story > Subtask breakdown with time estimates
- **QA mode** — test plans and test cases for every feature
- **POLICY mode** — data retention, access control, privacy policies

## Tech Stack
- Frontend: Streamlit (Python)
- AI: Anthropic Claude API (claude-sonnet-4)
- Database + Auth + Memory: Supabase (PostgreSQL)
- Hosting: Streamlit Cloud
- Language: Python 3.14

## Project Structure
```
architect-ai-agent/
├── agents/
│   ├── agent.py          # Main agent brain
│   ├── modes.py          # 5 mode definitions
│   ├── scope_guard.py    # Scope enforcement
│   └── policy_engine.py  # Policy doc generator
├── config/
│   └── use_cases.py      # Use case boundaries
├── memory/
│   ├── conversation.py   # In-session memory
│   └── persistent.py     # Supabase memory
├── prompts/
│   └── master_prompt.py  # Master system prompt
├── app.py                # Streamlit chat UI
└── requirements.txt
```

## Local Setup
```bash
git clone https://github.com/YOUR_USERNAME/architect-ai-agent.git
cd architect-ai-agent
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

Create `.env` file:
```
ANTHROPIC_API_KEY=sk-ant-...
SUPABASE_URL=https://yourproject.supabase.co
SUPABASE_KEY=your-anon-key
```

Run locally:
```bash
streamlit run app.py
```

## Adding a New Use Case
1. Open `config/use_cases.py`
2. Add a new entry following the existing template
3. Define `in_scope` and `out_of_scope` keyword lists
4. Select the new use case from the dropdown in the app

## Budget
- Anthropic API: ~$20-40/month typical usage
- Supabase: Free tier
- Streamlit Cloud: Free tier
- Total: Under $50/month

## Phases Completed
- Phase 1: Foundation — API, environment, first agent response
- Phase 2: Agent Brain — 5 modes, master prompt, memory
- Phase 3: Chat UI — Streamlit interface, mode switcher, downloads
- Phase 4: Scope Guard — scope enforcement, persistent memory, policy engine
- Phase 5: Deploy — Streamlit Cloud, secrets, budget alerts

## Next: Phase 6 — Hybrid Agent Architecture
Refactor into orchestrator + 5 specialist sub-agents for reduced
hallucination and tighter mode boundaries.