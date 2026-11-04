# Technology Stack & Environment Policy: ReVolt

## 1. Runtime & Language Versions

| Layer / Component | Technology | Version | Execution Context |
| :--- | :--- | :--- | :--- |
| **Backend Runtime** | Python | `3.12.10` | Virtual environment at `.\venv` |
| **API Framework** | FastAPI | `0.162.0` | Asynchronous ASGI REST server |
| **ASGI Web Server** | Uvicorn | `0.54.0` | Standard server with uvloop support |
| **Database Driver** | PyMongo | `4.19.0` | Synchronous/threaded MongoDB client |
| **Data Validation** | Pydantic | `2.14.2` | Type enforcement & schema serialization |
| **Environment Mgmt** | python-dotenv | `1.2.4` | `.env` parameter injection |
| **Database Server** | MongoDB Community | `7.0+` | Running locally at `mongodb://localhost:27017` |
| **Frontend Runtime**| Node.js | `v24.13.0` | Frontend build engine |
| **Package Manager** | npm | `11.6.2` | Frontend dependency manager |
| **Frontend UI** | React / Vite | `React 18.x / 19.x` | Single Page Application SPA |
| **Styling & Icons** | Tailwind CSS / Lucide | Latest | Utility-first styling |
| **Charts** | Recharts / Chart.js | Latest | Real-time telemetry visualization |
| **Hardware MCU** | ESP32-WROOM-32 | Tensilica Xtensa | Sensor acquisition controller |
| **Sensors** | INA226 + 10k NTC | Hardware I2C | Voltage, Current, Power & Temp |

---

## 2. Environment Configuration (`backend/.env`)

The backend requires the following configuration parameters:

```env
# Application Settings
APP_NAME=ReVolt
APP_ENV=development
DEBUG=True
PORT=8000
HOST=0.0.0.0

# Database Configuration
MONGO_URI=mongodb://localhost:27017
MONGO_DB_NAME=revolt_db

# Security & CORS
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
```

---

## 3. Dependency Policy
- **Pinning:** All Python dependencies in `requirements.txt` must be pinned with exact major, minor, and patch numbers prior to Phase 12 release.
- **Minimal Footprint:** No external dependencies may be added without evaluating footprint, licensing, and vulnerability risk.
- **Consistency:** Virtual environment in `.\venv` is the sole standard execution environment.

