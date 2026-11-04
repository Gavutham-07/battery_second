# Issue Register: ReVolt

## Active Issues, Risks & Blocker Log

| Issue ID | Severity | Category | Description | Affected Component | Current Status | Remediation / Action Item |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **ISS-001** | Medium | Documentation | Original Master Plan & System Design PDFs are not yet in `docs/reference/`. | `docs/reference/` | **OPEN** | Project Owner to copy PDFs to `docs/reference/`. |
| **ISS-002** | High | Code Quality | `backend/main.py` contains invalid Python CLI string `notepad passport.py`. | Backend Entrypoint | **TRACKED** | Replace with proper FastAPI application in Phase 2. |
| **ISS-003** | Medium | Configuration | `backend/.env` is 0 bytes (empty). | Environment Config | **TRACKED** | Populate verified environment variables in Phase 2. |
| **ISS-004** | High | Schema Integrity | `backend/schemas.py` allows unconstrained strings and unbounded SOH floats. | Data Contracts | **TRACKED** | Update schemas to enforce DEC-001 & DEC-002 in Phase 2. |
| **ISS-005** | Medium | Environment | Windows sandbox isolation blocks local socket access to MongoDB on port 27017. | Database Connectivity | **MITIGATED** | Execute live DB integration tests with sandbox bypass when authorized. |
| **ISS-006** | Medium | Analytics | Exact MBCO objective weights not yet mathematically calibrated. | AI Decision Engine | **PENDING** | Member 3 and Project Owner to finalize in Phase 6. |
| **ISS-007** | Low | Data Science | NASA, Oxford, MIT, and Sandia datasets not yet verified. | Dataset Mode | **PENDING** | Project Owner to select and approve specific benchmark dataset. |

