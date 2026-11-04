import React, { useState } from 'react';
import { useBatteryStore } from '../../context/BatteryContext';
import { Boxes, PlusCircle, CheckCircle2, AlertTriangle, Info, Layers, BatteryCharging, Zap } from 'lucide-react';

export default function PackGrouping() {
  const { cellInventory, groupedPacks, groupSelectedCells } = useBatteryStore();

  const [selectedCellIds, setSelectedCellIds] = useState([]);
  const [targetChemistry, setTargetChemistry] = useState('LFP');
  const [packName, setPackName] = useState('PACK-MOD-1');
  const [actionMsg, setActionMsg] = useState('');
  const [errorMsg, setErrorMsg] = useState('');

  const toggleSelectCell = (cellId) => {
    setSelectedCellIds(prev =>
      prev.includes(cellId) ? prev.filter(id => id !== cellId) : [...prev, cellId]
    );
  };

  const handleCreatePack = (e) => {
    e.preventDefault();
    setActionMsg('');
    setErrorMsg('');

    const res = groupSelectedCells(selectedCellIds, targetChemistry, packName);
    if (res.success) {
      setActionMsg(`Pack Module ${res.pack.pack_id} formed successfully with ${res.pack.cell_count} cells! Average SOH: ${res.pack.average_soh}%, Spread: ${res.pack.soh_spread}%.`);
      setSelectedCellIds([]);
      setPackName(`PACK-MOD-${groupedPacks.length + 2}`);
    } else {
      setErrorMsg(res.message);
    }
  };

  // Preview metrics for currently selected cells
  const selectedCells = cellInventory.filter(c => selectedCellIds.includes(c.cell_id));
  const currentSOHs = selectedCells.map(c => c.soh);
  const avgSOH = currentSOHs.length > 0 ? (currentSOHs.reduce((a, b) => a + b, 0) / currentSOHs.length).toFixed(2) : 0;
  const spreadSOH = currentSOHs.length > 1 ? (Math.max(...currentSOHs) - Math.min(...currentSOHs)).toFixed(2) : 0;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-xl font-bold text-slate-900">Cell-Level Pack Grouping & Balancing Module</h1>
        <p className="text-xs text-slate-500 mt-1">
          Select individual retired cells to calculate electrochemical delta, identify weak cells, and synthesize balanced second-life pack modules.
        </p>
      </div>

      {actionMsg && (
        <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-xl flex items-center justify-between text-xs text-emerald-800">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
            <span>{actionMsg}</span>
          </div>
          <button onClick={() => setActionMsg('')} className="text-emerald-700 font-bold ml-2">✕</button>
        </div>
      )}

      {errorMsg && (
        <div className="p-4 bg-rose-50 border border-rose-200 rounded-xl flex items-center justify-between text-xs text-rose-800">
          <div className="flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-rose-600 shrink-0" />
            <span>{errorMsg}</span>
          </div>
          <button onClick={() => setErrorMsg('')} className="text-rose-700 font-bold ml-2">✕</button>
        </div>
      )}

      {/* Mandatory Engineering Disclaimer */}
      <div className="p-3 bg-amber-50/80 border border-amber-200 rounded-xl text-xs text-amber-900 flex items-start gap-2">
        <Info className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
        <p className="leading-relaxed">
          <strong>Important Engineering Notice:</strong> Algorithmic pack grouping pairs cells based on SOH tolerances and internal impedance metrics. This software simulation does not substitute calibrated physical balancing, thermal insulation, or master BMS configuration.
        </p>
      </div>

      {/* Two Column Workspace: Inventory Table vs Module Builder */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Available Cells Inventory */}
        <div className="lg:col-span-2 bg-white rounded-xl border border-slate-200 p-5 shadow-xs space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-slate-100">
            <div>
              <span className="text-xs font-bold uppercase tracking-wider text-slate-800">Available Cell Inventory</span>
              <p className="text-[11px] text-slate-400">Select compatible cells to assemble into a module</p>
            </div>
            <span className="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-slate-100 text-slate-700">
              {cellInventory.filter(c => c.status === 'Available').length} Available
            </span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50 border-b border-slate-200 text-slate-600 uppercase font-semibold">
                <tr>
                  <th className="px-3 py-2.5 w-8">Select</th>
                  <th className="px-3 py-2.5">Cell ID</th>
                  <th className="px-3 py-2.5">Chemistry</th>
                  <th className="px-3 py-2.5">Capacity</th>
                  <th className="px-3 py-2.5">SOH</th>
                  <th className="px-3 py-2.5">Impedance</th>
                  <th className="px-3 py-2.5">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {cellInventory.map((cell) => {
                  const isSelected = selectedCellIds.includes(cell.cell_id);
                  const isGrouped = cell.status === 'Grouped';

                  return (
                    <tr
                      key={cell.cell_id}
                      onClick={() => !isGrouped && toggleSelectCell(cell.cell_id)}
                      className={`cursor-pointer transition-colors ${
                        isSelected ? 'bg-emerald-50/80' : (isGrouped ? 'opacity-40 bg-slate-50 cursor-not-allowed' : 'hover:bg-slate-50')
                      }`}
                    >
                      <td className="px-3 py-3">
                        <input
                          type="checkbox"
                          disabled={isGrouped}
                          checked={isSelected}
                          onChange={() => toggleSelectCell(cell.cell_id)}
                          className="rounded text-emerald-600 focus:ring-emerald-500 cursor-pointer"
                        />
                      </td>

                      <td className="px-3 py-3 font-bold text-slate-900">{cell.cell_id}</td>
                      <td className="px-3 py-3 font-medium text-slate-700">{cell.chemistry}</td>
                      <td className="px-3 py-3 text-slate-600">{cell.capacity_ah} Ah</td>
                      <td className="px-3 py-3">
                        <span className={`font-bold ${cell.soh >= 85 ? 'text-emerald-600' : 'text-amber-600'}`}>
                          {cell.soh}%
                        </span>
                      </td>
                      <td className="px-3 py-3 text-slate-500">{cell.internal_resistance_mohm} mΩ</td>
                      <td className="px-3 py-3">
                        <span className={`text-[10px] px-2 py-0.5 rounded font-semibold ${
                          cell.status === 'Grouped' ? 'bg-slate-200 text-slate-700' : 'bg-emerald-100 text-emerald-800'
                        }`}>
                          {cell.status}
                        </span>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>

        {/* Pack Synthesis Builder Panel */}
        <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs flex flex-col justify-between space-y-4">
          <div className="space-y-4">
            <div className="pb-3 border-b border-slate-100 flex items-center justify-between">
              <span className="text-xs font-bold uppercase tracking-wider text-slate-800">Module Configuration</span>
              <Boxes className="w-4 h-4 text-emerald-600" />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Target Chemistry</label>
              <select
                value={targetChemistry}
                onChange={(e) => setTargetChemistry(e.target.value)}
                className="w-full text-xs px-3 py-2 rounded-lg border border-slate-300 bg-white focus:border-emerald-500"
              >
                <option value="LFP">LFP (Lithium Iron Phosphate)</option>
                <option value="NMC">NMC (Nickel Manganese Cobalt)</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Module Name / ID</label>
              <input
                type="text"
                value={packName}
                onChange={(e) => setPackName(e.target.value)}
                className="w-full text-xs px-3 py-2 rounded-lg border border-slate-300 focus:border-emerald-500"
              />
            </div>

            {/* Live Synthesis Preview */}
            <div className="p-3 bg-slate-50 rounded-xl border border-slate-200 space-y-2 text-xs">
              <span className="font-bold text-slate-800">Selected Cells ({selectedCellIds.length}):</span>
              <div className="flex flex-wrap gap-1">
                {selectedCellIds.map(id => (
                  <span key={id} className="text-[10px] px-2 py-0.5 bg-emerald-100 text-emerald-900 rounded font-semibold">
                    {id}
                  </span>
                ))}
                {selectedCellIds.length === 0 && (
                  <p className="text-[11px] text-slate-400 italic">Select cells from the table</p>
                )}
              </div>

              <div className="pt-2 border-t border-slate-200 grid grid-cols-2 gap-2 text-xs">
                <div>
                  <span className="text-slate-400">Average SOH:</span>
                  <p className="font-bold text-slate-900 text-sm">{avgSOH}%</p>
                </div>
                <div>
                  <span className="text-slate-400">SOH Spread (Delta):</span>
                  <p className={`font-bold text-sm ${spreadSOH > 4 ? 'text-rose-600' : (spreadSOH > 2 ? 'text-amber-600' : 'text-emerald-600')}`}>
                    {spreadSOH}%
                  </p>
                </div>
              </div>

              {spreadSOH > 4 && (
                <div className="p-2 bg-rose-50 text-rose-800 text-[10px] rounded border border-rose-200 mt-1">
                  ⚠️ Spread exceeds recommended 3.0% threshold. May cause premature module imbalance.
                </div>
              )}
            </div>
          </div>

          <button
            onClick={handleCreatePack}
            disabled={selectedCellIds.length < 2}
            className={`w-full py-2.5 rounded-lg text-xs font-semibold shadow-xs transition-colors flex items-center justify-center gap-1.5 ${
              selectedCellIds.length < 2
                ? 'bg-slate-100 text-slate-400 cursor-not-allowed'
                : 'bg-emerald-600 hover:bg-emerald-700 text-white'
            }`}
          >
            <Boxes className="w-4 h-4" />
            <span>Synthesize Pack Module</span>
          </button>
        </div>
      </div>

      {/* Previously Synthesized Modules */}
      {groupedPacks.length > 0 && (
        <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs space-y-3">
          <span className="text-xs font-bold uppercase tracking-wider text-slate-800">Synthesized Secondary Pack Modules</span>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {groupedPacks.map((p) => (
              <div key={p.pack_id} className="p-4 bg-slate-50 rounded-xl border border-slate-200 text-xs space-y-2">
                <div className="flex items-center justify-between">
                  <span className="font-bold text-slate-900 text-sm">{p.pack_id}</span>
                  <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-100 text-emerald-800">
                    {p.compatibility}
                  </span>
                </div>
                <div className="flex gap-4 text-slate-600">
                  <p><span className="text-slate-400">Chemistry:</span> {p.chemistry}</p>
                  <p><span className="text-slate-400">Cells:</span> {p.cell_count}</p>
                  <p><span className="text-slate-400">Avg SOH:</span> <strong className="text-slate-900">{p.average_soh}%</strong></p>
                  <p><span className="text-slate-400">Spread:</span> {p.soh_spread}%</p>
                </div>
                <div className="flex flex-wrap gap-1 pt-1">
                  {p.cells.map(c => (
                    <span key={c.cell_id} className="text-[10px] px-1.5 py-0.5 bg-white border border-slate-200 rounded text-slate-700">
                      {c.cell_id} ({c.soh}%)
                    </span>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

