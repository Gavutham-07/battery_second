# Member B Handover

## Done
- B1: Install that works anywhere + in-memory test mode (`f4c44ae`)
- B3: Stream endpoint + analyze mapping (`008ad46`)
- B4: Approval and passport verification (`[B4] Approval and passport verification`)

## In progress
- None

## Next step
Start Task B5: What-if, recycler batch, pack grouping in backend/main.py.

## Blocked
- None

## Notes
- Task B4 checks fully passed:
  - Wrong PIN returns HTTP 403.
  - Unknown battery returns HTTP 404.
  - Untested battery / FURTHER_TESTING_REQUIRED returns HTTP 409.
  - Valid approval generates verifiable passport and returns HTTP 200 with passport object.
  - GET /api/verify/<id> validates recomputed SHA-256 hash bit-for-bit, returns VERIFIED and maps safety status per Contract C3.
  - `python -m pytest -p tests.fakemongo_plugin -q tests/unit/test_passport.py` passed 7/7.
