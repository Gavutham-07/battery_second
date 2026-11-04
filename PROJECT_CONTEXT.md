# PROJECT CONTEXT — REVOLT
## Smart EV Battery Second-Life Platform

### 1. Project Objective
ReVolt is an end-to-end platform that evaluates used electric vehicle (EV) batteries and identifies the optimal second-life application (e.g. E-Rickshaw/Light EV, Home Solar Storage, UPS/Telecom Backup, Solar Streetlight, or Material Recycling).

Key Capabilities:
1. Register used EV batteries (Chemistry: LFP, NMC, NCA; Rated Capacity).
2. Collect battery voltage, current, and temperature readings.
3. Perform a 90-second screening test with real-time telemetry.
4. Estimate State of Health (SOH) and prediction confidence.
5. Detect safety-related anomalies and thermal hazards.
6. Generate plain-English assessment explanations.
7. Recommend the most suitable second-life application.
8. Predict remaining useful life (RUL in years).
9. Calculate exchange credit (INR).
10. Record EV owner preferences (Reuse, Repurpose, Sell/Exchange).
11. Support Service Center Technician approval and minting of QR Battery Passports.
12. Verify battery passport integrity using SHA-256 cryptographic hashes.
13. Support Recycler batch sorting (Reuse, Repurpose, Recycle).
14. Group compatible individual battery cells into safe, balanced battery packs.
15. Display environmental and sustainability metrics (CO₂ avoided, waste diverted, recovered value).

---

### 2. Team Structure & Responsibilities
- **Member 1 (Hardware)**: ESP32 firmware, voltage/current/temp sensors, hardware data streaming, USB Serial/pyserial.
- **Member 2 (Backend & Database)**: FastAPI backend, MongoDB database, API endpoints, QR Battery Passport minting, SHA-256 verification.
- **Member 3 (AI & Battery Logic)**: XGBoost/Scikit-learn models, battery feature extraction, SOH estimation, confidence calculation, safety assessment, second-life matchmaker, residual lifetime prediction, cell pack grouping algorithm.
- **Member 4 (Frontend & Integration - CURRENT ROLE)**:
  - React, Vite, Tailwind CSS, Recharts, Lucide React, Axios, qrcode.react.
  - Portals: EV Owner Portal, Service Center Technician Portal, Recycler Portal, Public QR Verification.
  - Global persistent data source selector.
  - API integration, error handling, end-to-end workflow testing.
  - Continuity documentation (`PROJECT_CONTEXT.md`, `FRONTEND_HANDOFF.md`, `API_CONTRACT.md`, `CHANGELOG.md`, `AI_INSTRUCTIONS.md`, `.clinerules`).

---

### 3. Technology Stack
- **Frontend**: React 18 / Vite, Tailwind CSS, Recharts, Lucide React, Axios, qrcode.react, react-router-dom.
- **Backend**: Python, FastAPI, Pydantic, Uvicorn.
- **Database**: MongoDB.
- **AI/ML**: XGBoost, Scikit-learn, Rule-based safety validator.
- **Hardware Simulation**: ESP32 Serial, recorded test replay, virtual battery circuit simulator, MIT/Sandia lab dataset playback.

---

### 4. Repository Structure
```
ReVolt/
├── .git/
├── .clinerules
├── AI_INSTRUCTIONS.md
├── API_CONTRACT.md
├── CHANGELOG.md
├── FRONTEND_HANDOFF.md
├── PROJECT_CONTEXT.md
├── README.md
├── backend/               # Member 2 & Member 3 territory (FastAPI, MongoDB, ML)
├── hardware/              # Member 1 territory (ESP32 code, serial scripts)
└── frontend/              # Member 4 territory (React, Tailwind, Recharts)
    ├── public/
    ├── src/
    │   ├── assets/
    │   ├── components/    # Common UI (Sidebar, Navbar, DataSourceSelector, Cards, Modal)
    │   ├── context/       # Auth, DataSource, BatteryStore Contexts
    │   ├── pages/
    │   │   ├── landing/   # Landing & Role Selection
    │   │   ├── owner/     # EV Owner Portal (Dashboard, MyBatteries, Centers, Recommendations, Exchange, Impact, Passport)
    │   │   ├── tech/      # Technician Portal (Dashboard, Queue, Screening, WhatIf, Approval)
    │   │   ├── recycler/  # Recycler Portal (ImpactSummary, BatchSorting, PackGrouping)
    │   │   └── verify/    # Public QR Passport Verification
    │   ├── services/      # Centralized Axios API service
    │   ├── types/         # TypeScript or JSDoc data models
    │   ├── App.jsx
    │   ├── main.jsx
    │   └── index.css
    ├── package.json
    ├── tailwind.config.js
    └── vite.config.js
```

---

### 5. Design System & Conventions
- **Style Direction**: Clean, modern, professional SaaS-style dashboard. No neon, no excessive gradients, no glowing effects, no oversized text.
- **Color Palette**:
  - Background: White (`#ffffff`) or very light gray (`#f8fafc`).
  - Sidebar: Dark Navy (`#0f172a` / `#1e293b`).
  - Primary Accent: Muted Emerald Green (`#059669` / `#10b981`).
  - Secondary Accents: Soft Blue (`#3b82f6` / `#0284c7`), Slate Gray (`#64748b`).
  - Status Colors:
    - Safe / Healthy: Emerald (`#10b981`)
    - Warning / Moderate: Amber (`#f59e0b`)
    - Critical / Danger: Rose/Red (`#ef4444`)
- **Typography**: Clean sans-serif (Inter / system-ui).
- **Icons**: Lucide React.
- **Charts**: Recharts with clear labels, legends, units (V, A, °C), and clean tooltips.

---

### 6. Data Source Architecture & Modes
Global Persistent Data Source Selector available on:
1. Landing page.
2. Top-right header of every portal page.

Options:
1. `live_hardware` - Live Hardware (ESP32 via USB Serial)
2. `replay_recorded` - Replay Recorded Test
3. `virtual_circuit` - Virtual Battery Circuit (Simulated dynamics)
4. `lab_dataset` - Lab Dataset Cells (MIT/Sandia)

Status indicators:
- `Connected`
- `Disconnected`
- `Simulated`
- `Replay Active`
- `Loading`

Technicians can test with profiles in virtual/replay modes:
- `healthy` - Healthy Cell (~92% SOH, <35°C)
- `moderately_aged` - Moderately Aged Cell (~76% SOH, 35-42°C)
- `thermally_unsafe` - Thermally Unsafe Cell (>45°C thermal runaway flag)

---

### 7. Core Business & Technical Rules
1. **Single Battery Identity**: `battery_id` (e.g. `BAT-101`) is uniform across Owner registration, Technician Queue, Live Screening, AI Assessment, Approval, Passport QR, Recycler Batch, and Public Verification.
2. **Owner Preference vs AI Recommendation**:
   - Technical recommendation is determined by SOH and Safety Analysis.
   - Owner can choose preference (Reuse, Repurpose, Sell/Exchange).
   - Both are stored separately.
   - Owner preference NEVER overrides safety rules. If SOH < 60% or safety flags are active, Reuse/Repurpose is prohibited and Recycled is enforced.
3. **QR Battery Passport**:
   - Contains immutable assessment snapshot, technician signature, and SHA-256 digest.
   - Verified publicly via `/verify/:passport_id` or `/verify?hash=...`.
4. **Pack Grouping**:
   - Module creation requires cell-level inventory (Cell ID, SOH, Chemistry, Capacity).
   - Compatible cells must have similar chemistry and capacity with tight SOH delta (< 3-5%).
   - Explicit disclaimer that software grouping does not replace physical balancing/BMS assembly.

---

### 8. Current Implementation Status
- Phase 0: Repository inspected, git branch `feat-frontend` checked out, continuity documentation established.
- Phase 1: In progress. Setting up frontend application and design foundation.

