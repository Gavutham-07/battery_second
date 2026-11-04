# AI INSTRUCTIONS FOR REVOLT PROJECT

ATTENTION TO ANY AI ASSISTANT WORKING ON THIS REPOSITORY:
This is a 12-hour hackathon project developed by a 4-person team. Strict preservation rules apply.

---

### MANDATORY INITIAL STEPS BEFORE TOUCHING CODE:
1. **Read `PROJECT_CONTEXT.md`**: Understand the architecture, design system, and business rules.
2. **Read `FRONTEND_HANDOFF.md`**: Identify the current phase, completed pages, and the recorded next step.
3. **Read `API_CONTRACT.md`**: Follow exact field names and types (`battery_id`, `soh_estimate`, `confidence_score`, `safety_status`, etc.).
4. **Read `CHANGELOG.md`**: Review recent changes to understand what has already been built.
5. **Inspect the existing repository and current Git branch**:
   - Verify you are on `feat-frontend`.
   - Never force-push or discard uncommitted changes.
6. **Understand what is already implemented**:
   - DO NOT rebuild the project from scratch.
   - DO NOT delete or rewrite working components.
   - DO NOT modify backend (`/backend/`) or hardware (`/hardware/`) files without explicit permission.
7. **Continue from the recorded next step** in `FRONTEND_HANDOFF.md`.
8. **Make focused, minimal changes**:
   - Change only the requested component/page.
   - Reuse existing utilities, contexts, and styles.
9. **Update documentation**:
   - Keep `FRONTEND_HANDOFF.md` and `CHANGELOG.md` up to date with every milestone.
10. **Ask for clarification** if an architectural or data contract requirement is ambiguous.

---

### CODE RESTRICTIONS:
- Frontend working area is strictly within `/frontend/*`, `README.md`, `.clinerules`, and root documentation files.
- Use the central Axios instance in `frontend/src/services/api.js`. Do not hardcode `http://localhost:...` across individual components.
- Maintain design consistency: Dark Navy sidebar, Muted Emerald Green accents, Slate Gray, clean cards, Lucide icons, Recharts charts.
- Maintain single-battery state continuity across all portals.

