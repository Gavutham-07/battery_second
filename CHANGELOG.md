# CHANGELOG — REVOLT

All notable changes and architectural updates will be documented here.

## [1.0.0] - 2026-11-04

### Completed Full-Stack Frontend Demonstration
- **Architecture & Setup**:
  - Initialized Vite + React 18 + Tailwind CSS + Lucide Icons + Recharts + qrcode.react in `frontend/`.
  - Configured professional SaaS styling palette: Dark Navy (`#0f172a`), Muted Emerald Green (`#059669`/`#10b981`), and Slate gray cards.
  - Successfully compiled with `npm run build` (0 errors, 2197 modules transformed).
  - Dev server running on `http://localhost:5173/` (verified HTTP 200 OK).

- **Global Persistence & Data Sources**:
  - Implemented `DataSourceContext` and persistent top-right `DataSourceSelector` accessible across all pages.
  - Supported all 4 data sources: Virtual Battery Circuit, Replay Recorded Test, Lab Dataset Cells (MIT/Sandia), and Live Hardware (ESP32) with honest disconnection alerts.
  - Supported test profiles: Healthy Cell, Moderately Aged Cell, and Thermally Unsafe Cell.
  - Implemented unified `BatteryContext` with `localStorage` persistence ensuring seamless data continuity across portals.

- **EV Owner Portal**:
  - Built `OwnerDashboard`: Summary KPIs, recent battery activity.
  - Built `MyBatteries`: Single combined page with Registration Form at top and registered battery cards below with live "Check Status" modal.
  - Built `FindServiceCenters`: Geo-distance computation, partner diagnostic centers, and booking.
  - Built `Recommendations`: AI application matches vs separate Owner Preferences (Reuse, Repurpose, Sell/Exchange) with strict safety lockout.
  - Built `ExchangeOffers`: Buyback valuations and acceptance flow.
  - Built `EnvironmentalImpact`: CO₂ avoided, toxic waste diverted, and circular capital.
  - Built `MyBatteryPassport`: Digital certificate, SVG QR code, SHA-256 hash proof, and print/PDF download.

- **Service Center Technician Portal**:
  - Built `TechnicianDashboard`: Intake queue counters, active screening rig status.
  - Built `BatteryQueue`: Actionable table with 1-click "Start Screening" that auto-loads battery ID into the test bench.
  - Built `BatteryScreening`: Single-page guided workflow, live Voltage (V), Current (A), and Temperature (°C) charts, 90s test telemetry, and assessment auto-displayed directly below charts on the same page.
  - Built `WhatIfSimulator`: Daily usage (1-16h), Ambient temperature (15-45°C), and DoD (20-100%) sliders with reset button.
  - Built `ApprovalPassport`: Technician notes, route assignment, and SHA-256 QR passport minting.

- **Recycler Portal**:
  - Built `ImpactSummary`: Facility-level aggregate operational metrics and batch distributions.
  - Built `BatchSorting`: Segregation into Motive Reuse, Stationary Repurpose, and Hydrometallurgical Recycling with safety lockout.
  - Built `PackGrouping`: Cell inventory selection, SOH spread calculation, weak-cell alerts, and explicit safety disclaimer.

- **Public QR Verification**:
  - Built `PublicVerification`: Accessible via QR scan or battery ID lookup (`/verify/:battery_id`) without authentication, validating cryptographic SHA-256 integrity.

- **Project Continuity Documentation**:
  - Updated `PROJECT_CONTEXT.md`, `FRONTEND_HANDOFF.md`, `API_CONTRACT.md`, `CHANGELOG.md`, `AI_INSTRUCTIONS.md`, and `.clinerules`.
