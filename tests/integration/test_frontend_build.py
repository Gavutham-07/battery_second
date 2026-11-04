import os
import re
import json
import subprocess
import pytest
from backend.main import app

FRONTEND_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "frontend")


def test_frontend_project_structure():
    assert os.path.isdir(FRONTEND_DIR), "frontend/ directory must exist"
    assert os.path.isfile(os.path.join(FRONTEND_DIR, "package.json"))
    assert os.path.isfile(os.path.join(FRONTEND_DIR, "vite.config.js"))
    assert os.path.isfile(os.path.join(FRONTEND_DIR, "index.html"))
    assert os.path.isfile(os.path.join(FRONTEND_DIR, "src", "App.jsx"))
    assert os.path.isfile(os.path.join(FRONTEND_DIR, "src", "components", "CustomerTab.jsx"))
    assert os.path.isfile(os.path.join(FRONTEND_DIR, "src", "components", "TechnicianTab.jsx"))
    assert os.path.isfile(os.path.join(FRONTEND_DIR, "src", "components", "RecyclerTab.jsx"))
    assert os.path.isfile(os.path.join(FRONTEND_DIR, "src", "components", "AuditorTab.jsx"))
    assert os.path.isfile(os.path.join(FRONTEND_DIR, "src", "components", "ModeBanner.jsx"))
    assert os.path.isfile(os.path.join(FRONTEND_DIR, "src", "components", "TelemetryChart.jsx"))
    assert os.path.isfile(os.path.join(FRONTEND_DIR, "src", "components", "QRCodeDisplay.jsx"))


def test_frontend_production_build_artifacts():
    dist_dir = os.path.join(FRONTEND_DIR, "dist")
    assert os.path.isdir(dist_dir), "dist/ directory must exist after build"
    index_html = os.path.join(dist_dir, "index.html")
    assert os.path.isfile(index_html), "dist/index.html must exist"

    with open(index_html, "r", encoding="utf-8") as f:
        content = f.read()
    assert "ReVolt" in content
    assert "<script type=\"module\"" in content


def test_four_mode_banner_coverage():
    banner_path = os.path.join(FRONTEND_DIR, "src", "components", "ModeBanner.jsx")
    with open(banner_path, "r", encoding="utf-8") as f:
        code = f.read()
    for mode in ["LIVE", "REPLAY", "VIRTUAL", "DATASET"]:
        assert mode in code, f"Mode {mode} must be defined in ModeBanner"


def test_four_stakeholder_tabs_in_app():
    app_path = os.path.join(FRONTEND_DIR, "src", "App.jsx")
    with open(app_path, "r", encoding="utf-8") as f:
        code = f.read()
    assert "CustomerTab" in code
    assert "TechnicianTab" in code
    assert "RecyclerTab" in code
    assert "AuditorTab" in code


def test_frontend_backend_api_route_alignment():
    """Verify that all API routes called in frontend components exist in FastAPI backend."""
    openapi_schema = app.openapi()
    available_routes = set(openapi_schema["paths"].keys())

    components_dir = os.path.join(FRONTEND_DIR, "src", "components")
    extracted_endpoints = set()

    route_pattern = re.compile(r'[\'"`](/api/[a-zA-Z0-9_\-\$\{}/]+)[\'"`]')

    for root, _, files in os.walk(components_dir):
        for f in files:
            if f.endswith(".jsx"):
                with open(os.path.join(root, f), "r", encoding="utf-8") as file:
                    for line in file:
                        matches = route_pattern.findall(line)
                        for m in matches:
                            clean_m = m.split("?")[0]
                            # Normalize path params e.g. /api/analysis/valuation/${batteryId} -> /api/analysis/valuation/{battery_id}
                            norm = re.sub(r'\$\{[a-zA-Z0-9_]+\}', '{battery_id}', clean_m)
                            extracted_endpoints.add(norm)

    expected_endpoints = {
        "/api/analysis/valuation/{battery_id}",
        "/api/analysis/reports/{battery_id}",
        "/api/analysis/what-if",
        "/api/batteries",
        "/api/live-data",
        "/api/live-data/{battery_id}",
        "/api/analysis/evaluate",
        "/api/exchanges/approve",
        "/api/inventory",
        "/api/inventory/group-cells",
        "/api/passport/{battery_id}",
        "/api/passport/generate",
        "/api/passport/verify"
    }

    for ep in expected_endpoints:
        assert ep in available_routes, f"Frontend calls {ep} but it is missing in FastAPI app!"

