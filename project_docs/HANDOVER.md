# AI & Developer Handover Guide: ReVolt

## 1. Handover Overview & Continuity Mandate
This document guarantees zero context loss and seamless continuation of development across AI models (Antigravity, ChatGPT, Claude) or human developers without restarting completed phases.

> **CRITICAL DIRECTIVE FOR INCOMING AGENTS:**
> DO NOT regenerate existing code, recreate files, or restart completed phases.
> Your first action MUST BE to inspect the files listed below and identify the exact active phase in `CURRENT_PROGRESS.md`.

---

## 2. Immediate Inspection Checklist for Incoming Agents
1. **Current Branch & Git State:**
   - Execute: `git status` and `git branch`
   - Active backend working branch: `feat-backend`
2. **Current Project State:**
   - Read [CURRENT_PROGRESS.md](file:///d:/battery_second/battery_second/project_docs/CURRENT_PROGRESS.md)
   - Verify completed phases and note the **Exact Next Action**.
3. **Approved Decisions (DO NOT OVERRIDE):**
   - Read [DECISION_LOG.md](file:///d:/battery_second/battery_second/project_docs/DECISION_LOG.md)
   - Respect canonical identifiers, enum types, and endpoints locked in DEC-001 through DEC-006.
4. **Permanent Development Rules:**
   - Read [DEVELOPMENT_RULES.md](file:///d:/battery_second/battery_second/project_docs/DEVELOPMENT_RULES.md)
   - Adhere strictly to the 14 mandatory development rules.
5. **Interface Contracts:**
   - Read [API_CONTRACTS.md](file:///d:/battery_second/battery_second/project_docs/API_CONTRACTS.md) and [DATABASE_SCHEMA.md](file:///d:/battery_second/battery_second/project_docs/DATABASE_SCHEMA.md)

---

## 3. Project Environment & Run Instructions

```bash
# 1. Activate Python virtual environment
.\venv\Scripts\activate

# 2. Verify installed packages
pip list

# 3. Check MongoDB service
# Ensure MongoDB Community Server is listening on localhost:27017

# 4. Run automated tests (Once implemented in Phase 2)
pytest tests/ -v
```

---

## 4. Key Repository Locations

| Purpose | Location |
| :--- | :--- |
| **Living Documentation** | `d:\battery_second\battery_second\project_docs\` |
| **Original Reference PDFs** | `d:\battery_second\battery_second\docs\reference\` |
| **Backend Source Code** | `d:\battery_second\battery_second\backend\` |
| **AI Intelligence Engine** | `d:\battery_second\battery_second\ai_engine\` (Phase 5) |
| **Hardware Bridge Scripts** | `d:\battery_second\battery_second\hardware\` (Phase 4) |
| **Frontend React SPA** | `d:\battery_second\battery_second\frontend\` (Phase 10) |
| **Test Suites** | `d:\battery_second\battery_second\tests\` (Phase 2+) |

---

## 5. Handover Prompt Template for AI Switching

When rate limits or session boundaries require switching to another AI assistant, copy and paste this exact prompt:

```markdown
You are joining the ongoing project "ReVolt: Smart EV Battery Assessment, Valuation and Circularity Platform" on branch feat-backend.

Phase 0 (Repository Baseline) and Phase 1 (Documentation and Architecture Freeze) are COMPLETE.

Before taking any action:
1. Inspect project_docs/CURRENT_PROGRESS.md to identify the current active phase and exact next action.
2. Read project_docs/DECISION_LOG.md to review all approved non-negotiable architectural decisions.
3. Read project_docs/DEVELOPMENT_RULES.md to adhere to the 14 project engineering rules.
4. Read project_docs/API_CONTRACTS.md and project_docs/DATABASE_SCHEMA.md.

Do NOT regenerate existing code or restart completed phases.
Wait for the Project Owner to provide the approved implementation prompt for the next phase.
```

