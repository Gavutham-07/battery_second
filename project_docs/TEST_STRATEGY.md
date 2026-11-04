# Test Strategy & Quality Assurance: ReVolt

## 1. Quality Assurance Philosophy
In compliance with Rule 8 and Rule 13:
- **No Claims Without Evidence:** No feature or phase transition may be declared complete without verifiable test output.
- **Fail Early:** Safety gates, boundary errors, and contract schema violations must fail explicitly with descriptive error codes rather than propagating silent defaults.
- **Targeted & Regression Testing:** Unit and focused tests are executed during development, followed by regression verification before code freeze.

---

## 2. Testing Levels & Matrix

| Level | Scope | Framework | Execution Frequency |
| :--- | :--- | :--- | :--- |
| **Unit Testing** | Pydantic model validation, SHA-256 hash calculation, safety rule matrix, what-if math formulas. | `pytest` | On every code change before commit. |
| **API Integration** | FastAPI endpoint tests using `httpx.AsyncClient` or `starlette.testclient.TestClient`. | `pytest` | Prior to phase sign-off. |
| **Database Persistence** | CRUD operations, unique constraints, compound indexes in `revolt_db`. | `pytest` + PyMongo | Phase 2, Phase 3, and Phase 8 sign-off. |
| **Cryptographic Tamper** | Digital Battery Passport verification under payload byte tampering. | `pytest` | Phase 8 sign-off. |
| **System End-to-End** | Simulated ingestion $\rightarrow$ AI assessment $\rightarrow$ Passport $\rightarrow$ UI consumption. | Automation Scripts | Phase 11 & Phase 12. |

---

## 3. Test Suites Directory Structure (`tests/`)

```text
tests/
├── unit/
│   ├── test_schemas.py           # Validates Pydantic schemas and numerical bounds
│   ├── test_passport.py          # Validates canonical SHA-256 hash & tampering detection
│   └── test_safety_rules.py      # Validates safety precedence and decision tree
├── integration/
│   ├── test_api_health.py        # Validates /api/health and database ping
│   ├── test_batteries_api.py     # Validates registration and duplicate handling
│   ├── test_telemetry_api.py     # Validates POST /api/live-data ingestion
│   └── test_exchanges_api.py     # Validates technician approvals and transactions
└── fixtures/
    ├── sample_telemetry.json     # Sample live packets
    └── mock_passport.json        # Validated passport sample
```

---

## 4. Execution Commands

```bash
# Run all unit tests
pytest tests/unit/ -v

# Run API integration tests
pytest tests/integration/ -v

# Run complete test suite with coverage report
pytest --cov=backend --cov-report=term-missing tests/
```

