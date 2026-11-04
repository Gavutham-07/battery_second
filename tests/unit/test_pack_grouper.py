import pytest
from backend.pack_grouper import find_optimal_cell_pack


def test_pack_grouper_insufficient_cells():
    cells = [
        {"battery_id": "BAT-1", "chemistry": "LFP", "soh": 85.0},
        {"battery_id": "BAT-2", "chemistry": "LFP", "soh": 84.0},
    ]
    res = find_optimal_cell_pack(cells, chemistry="LFP", pack_size=4)
    assert res["eligible"] is False
    assert res["suitability"] == "INSUFFICIENT_CELLS"
    assert res["available_count"] == 2
    assert res["required_count"] == 4


def test_pack_grouper_perfect_match():
    cells = [
        {"battery_id": "BAT-1", "chemistry": "LFP", "soh": 85.0},
        {"battery_id": "BAT-2", "chemistry": "LFP", "soh": 85.0},
        {"battery_id": "BAT-3", "chemistry": "LFP", "soh": 85.0},
        {"battery_id": "BAT-4", "chemistry": "LFP", "soh": 85.0},
    ]
    res = find_optimal_cell_pack(cells, chemistry="LFP", pack_size=4, max_std_dev=3.0)
    assert res["eligible"] is True
    assert res["cell_count"] == 4
    assert res["mean_soh"] == 85.0
    assert res["soh_variance"] == 0.0
    assert res["soh_std_dev"] == 0.0
    assert res["suitability"] == "APPROVED_FOR_4S_STORAGE"
    assert len(res["selected_battery_ids"]) == 4


def test_pack_grouper_variance_minimization_and_outlier_filtering():
    # 7 available cells: 4 tight cells, 1 degraded outlier, 2 ultra-fresh cells
    cells = [
        {"battery_id": "BAT-DEG", "chemistry": "LFP", "soh": 55.0},    # Outlier low
        {"battery_id": "BAT-C1", "chemistry": "LFP", "soh": 82.0},
        {"battery_id": "BAT-C2", "chemistry": "LFP", "soh": 83.0},
        {"battery_id": "BAT-C3", "chemistry": "LFP", "soh": 83.5},
        {"battery_id": "BAT-C4", "chemistry": "LFP", "soh": 84.0},
        {"battery_id": "BAT-FRESH1", "chemistry": "LFP", "soh": 96.0}, # Outlier high
        {"battery_id": "BAT-FRESH2", "chemistry": "LFP", "soh": 98.0}, # Outlier high
    ]
    res = find_optimal_cell_pack(cells, chemistry="LFP", pack_size=4, max_std_dev=3.0)
    assert res["eligible"] is True
    assert set(res["selected_battery_ids"]) == {"BAT-C1", "BAT-C2", "BAT-C3", "BAT-C4"}
    assert res["soh_std_dev"] <= 3.0
    assert res["suitability"] == "APPROVED_FOR_4S_STORAGE"


def test_pack_grouper_outlier_rejection():
    # 4 cells that have too wide variance (spread across 40% to 95%)
    cells = [
        {"battery_id": "BAT-1", "chemistry": "LFP", "soh": 50.0},
        {"battery_id": "BAT-2", "chemistry": "LFP", "soh": 68.0},
        {"battery_id": "BAT-3", "chemistry": "LFP", "soh": 82.0},
        {"battery_id": "BAT-4", "chemistry": "LFP", "soh": 96.0},
    ]
    res = find_optimal_cell_pack(cells, chemistry="LFP", pack_size=4, max_std_dev=3.0)
    assert res["eligible"] is False
    assert res["soh_std_dev"] > 3.0
    assert res["suitability"] == "UNSUITABLE_FOR_GROUPING"


def test_pack_grouper_chemistry_isolation():
    # 3 LFP cells and 3 NMC cells. Neither chemistry alone has 4 cells.
    cells = [
        {"battery_id": "BAT-L1", "chemistry": "LFP", "soh": 84.0},
        {"battery_id": "BAT-L2", "chemistry": "LFP", "soh": 84.5},
        {"battery_id": "BAT-L3", "chemistry": "LFP", "soh": 85.0},
        {"battery_id": "BAT-N1", "chemistry": "NMC", "soh": 84.0},
        {"battery_id": "BAT-N2", "chemistry": "NMC", "soh": 84.5},
        {"battery_id": "BAT-N3", "chemistry": "NMC", "soh": 85.0},
    ]
    # Asking for LFP pack must not include NMC cells
    res = find_optimal_cell_pack(cells, chemistry="LFP", pack_size=4)
    assert res["eligible"] is False
    assert res["suitability"] == "INSUFFICIENT_CELLS"
    assert res["available_count"] == 3


def test_pack_grouper_custom_pack_size():
    cells = [
        {"battery_id": "BAT-1", "chemistry": "LFP", "soh": 84.0},
        {"battery_id": "BAT-2", "chemistry": "LFP", "soh": 84.5},
    ]
    res = find_optimal_cell_pack(cells, chemistry="LFP", pack_size=2, max_std_dev=1.0)
    assert res["eligible"] is True
    assert res["cell_count"] == 2
    assert len(res["selected_battery_ids"]) == 2
    assert res["soh_std_dev"] <= 1.0

