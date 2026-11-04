# Development Rules & Engineering Protocol: ReVolt

## 1. Mandatory Development Rules (The 14 Non-Negotiable Laws)

1. **Rule 1 — Never Assume Unimplemented Features Exist:** Always inspect actual codebase files; never assume a module, route, or model exists merely because it was mentioned in documentation.
2. **Rule 2 — Inspect Before Replacing Code:** Never replace existing working code without reading and understanding its current behavior and dependents.
3. **Rule 3 — Modify Only What Was Requested:** When asked to alter a specific component (e.g., passport layout), do not rewrite unrelated backend routes, alter database collections, or modify the AI engine.
4. **Rule 4 — Consistent Naming & Architecture:** Strictly maintain canonical identifiers (`revolt_db`, `battery_id`, `soh`, `available_capacity_ah`, `Digital Battery Passport`, `MBCO`). Never independently rename established variables or endpoints.
5. **Rule 5 — Ask Questions Before Making Assumptions:** Stop and seek clarification from the Project Owner when an operational boundary, threshold, or contract is ambiguous. Never invent thresholds or requirements.
6. **Rule 6 — Strict Dependency Policy:** Check existing Python (`3.12.10`) and Node (`v24.13.0`) runtimes before adding packages. Pin exact versions; test imports immediately.
7. **Rule 7 — Zero Secrets in Repositories:** Never commit `.env`, private keys, passwords, or cloud credentials.
8. **Rule 8 — Targeted Patches Over Full Rewrites:** Prefer targeted, surgical edits over rewriting large files from scratch to minimize token consumption and regression bugs.
9. **Rule 9 — Test-Driven Verification:** Run relevant unit and integration tests after every meaningful modification.
10. **Rule 10 — No Phantom Claims:** Never claim a feature is complete or functional without presenting concrete test output or terminal logs as evidence.
11. **Rule 11 — Backward Compatibility:** Maintain compatibility with existing schemas and routes unless a breaking change is formally authorized.
12. **Rule 12 — Mandatory Phase-by-Phase Gates:** Never begin the next implementation phase automatically. Stop after completing an authorized phase and wait for explicit Project Owner sign-off.
13. **Rule 13 — Preserve Git History & Branches:** Maintain clean Git history; do not rebase destructively or force-push over shared branches.
14. **Rule 14 — Continuous Context Maintenance:** Keep `CURRENT_PROGRESS.md`, `CHANGELOG.md`, `DECISION_LOG.md`, and `HANDOVER.md` accurate and up to date after every phase.

---

## 2. Token & Rate-Limit Optimization Protocol
- **Focused File Reads:** Inspect only the specific files relevant to the active task; do not recursively dump the entire repository.
- **Concise Reporting:** Report results using dense, structured Markdown tables and bullet points rather than conversational filler.
- **Fail Fast:** Run unit tests before executing heavy integration suites.

