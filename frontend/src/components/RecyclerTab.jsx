import React, { useState, useEffect } from 'react';
import { Layers, RefreshCw, CheckCircle, AlertTriangle, Box, Cpu, Zap } from 'lucide-react';

export default function RecyclerTab({ showToast }) {
  const [inventory, setInventory] = useState([]);
  const [loading, setLoading] = useState(false);
  const [statusFilter, setStatusFilter] = useState('');
  const [chemFilter, setChemFilter] = useState('');

  // Grouping state
  const [targetChemistry, setTargetChemistry] = useState('LFP');
  const [targetCapacity, setTargetCapacity] = useState('2.5');
  const [packSize, setPackSize] = useState(4);
  const [maxVariance, setMaxVariance] = useState(3.0);
  const [groupingResult, setGroupingResult] = useState(null);
  const [groupingLoading, setGroupingLoading] = useState(false);

  const fetchInventory = async () => {
    setLoading(true);
    try {
      let url = '/api/inventory?';
      if (statusFilter) url += `status=${statusFilter}&`;
      if (chemFilter) url += `chemistry=${chemFilter}&`;

      const res = await fetch(url);
      if (res.ok) {
        const data = await res.json();
        setInventory(data);
      }
    } catch (err) {
      console.error('Error fetching inventory:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchInventory();
  }, [statusFilter, chemFilter]);

  const handleGroupCells = async (e) => {
    e.preventDefault();
    setGroupingLoading(true);
    try {
      const res = await fetch('/api/inventory/group-cells', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          chemistry: targetChemistry,
          target_capacity_ah: parseFloat(targetCapacity),
          pack_size: parseInt(packSize, 10),
          max_soh_variance: parseFloat(maxVariance),
          reserve_cells: true
        })
      });

      if (res.ok) {
        const result = await res.json();
        setGroupingResult(result);
        if (result.eligible) {
          showToast(`Formed 4S Pack ${result.pack_id} with σ = ${result.soh_std_dev}%!`, 'success');
        } else {
          showToast(`Warning: Pack exceeds variance tolerance (${result.suitability})`, 'warning');
        }
        fetchInventory();
      } else {
        const err = await res.json();
        showToast(err.detail || 'Grouping failed', 'error');
      }
    } catch (err) {
      showToast('Error grouping cells', 'error');
    } finally {
      setGroupingLoading(false);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* Top Section: Balanced Pack Grouping Engine */}
      <div className="card">
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '14px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Box size={18} color="#10b981" />
            <h3 style={{ fontSize: '1.05rem', fontWeight: 600 }}>
              Balanced 4-Cell Pack Grouping Engine (Series-Parallel Second Life)
            </h3>
          </div>
          <span className="badge badge-green">&sigma;<sub>SOH</sub> &le; 3.0% GUARANTEE</span>
        </div>

        <p style={{ fontSize: '0.8rem', color: '#94a3b8', marginBottom: '16px' }}>
          Computes optimal 4-cell combinations for second-life 4S BESS packs by minimizing intra-pack SOH variance and isolating degraded outlier cells.
        </p>

        <form onSubmit={handleGroupCells} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <div className="grid-4">
            <div>
              <label style={{ fontSize: '0.75rem', color: '#94a3b8', display: 'block', marginBottom: '4px' }}>Target Chemistry</label>
              <select className="select" value={targetChemistry} onChange={(e) => setTargetChemistry(e.target.value)}>
                <option value="LFP">LFP (3.2V nominal)</option>
                <option value="NMC">NMC (3.7V nominal)</option>
              </select>
            </div>

            <div>
              <label style={{ fontSize: '0.75rem', color: '#94a3b8', display: 'block', marginBottom: '4px' }}>Target Capacity (Ah)</label>
              <input
                type="number"
                step="0.1"
                className="input mono"
                value={targetCapacity}
                onChange={(e) => setTargetCapacity(e.target.value)}
                required
              />
            </div>

            <div>
              <label style={{ fontSize: '0.75rem', color: '#94a3b8', display: 'block', marginBottom: '4px' }}>Pack Size (Cells)</label>
              <input
                type="number"
                className="input mono"
                value={packSize}
                onChange={(e) => setPackSize(e.target.value)}
                min="2"
                max="16"
                required
              />
            </div>

            <div>
              <label style={{ fontSize: '0.75rem', color: '#94a3b8', display: 'block', marginBottom: '4px' }}>Max Allowable &sigma;<sub>SOH</sub> (%)</label>
              <input
                type="number"
                step="0.1"
                className="input mono"
                value={maxVariance}
                onChange={(e) => setMaxVariance(e.target.value)}
                required
              />
            </div>
          </div>

          <button
            type="submit"
            className="btn btn-primary"
            disabled={groupingLoading}
            style={{ width: '100%', padding: '10px' }}
          >
            {groupingLoading ? 'Optimizing Cell Subsets...' : 'Run Variance Minimization & Form 4S Pack'}
          </button>
        </form>

        {/* Grouping Result Card */}
        {groupingResult && (
          <div style={{
            marginTop: '18px',
            background: groupingResult.eligible ? 'rgba(16, 185, 129, 0.08)' : 'rgba(239, 68, 68, 0.08)',
            border: groupingResult.eligible ? '1px solid rgba(16, 185, 129, 0.3)' : '1px solid rgba(239, 68, 68, 0.3)',
            borderRadius: '8px',
            padding: '16px'
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                {groupingResult.eligible ? <CheckCircle size={18} color="#10b981" /> : <AlertTriangle size={18} color="#ef4444" />}
                <h4 style={{ fontWeight: 700, fontSize: '0.95rem', color: groupingResult.eligible ? '#34d399' : '#f87171' }}>
                  {groupingResult.suitability === 'APPROVED_FOR_4S_STORAGE' ? '4S Second-Life Pack Approved' : 'Unsuitable: Outlier Variance Detected'}
                </h4>
              </div>
              <span className="mono badge badge-purple">{groupingResult.pack_id}</span>
            </div>

            <div className="grid-4" style={{ marginBottom: '12px', fontSize: '0.85rem' }}>
              <div>Mean SOH: <span className="mono" style={{ fontWeight: 700, color: '#10b981' }}>{groupingResult.mean_soh}%</span></div>
              <div>Intra-Pack Variance (&sigma;<sup>2</sup>): <span className="mono">{groupingResult.soh_variance}</span></div>
              <div>Std Dev (&sigma;): <span className="mono" style={{ fontWeight: 700, color: groupingResult.soh_std_dev <= 3.0 ? '#10b981' : '#f87171' }}>{groupingResult.soh_std_dev}%</span></div>
              <div>Chemistry: <span className="mono">{groupingResult.chemistry}</span></div>
            </div>

            <div style={{ background: 'rgba(0,0,0,0.2)', padding: '10px', borderRadius: '6px' }}>
              <span style={{ fontSize: '0.75rem', color: '#94a3b8', display: 'block', marginBottom: '6px' }}>
                Selected Balanced Cell Assets:
              </span>
              <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                {groupingResult.selected_battery_ids?.map((id) => (
                  <span key={id} className="mono badge badge-cyan">
                    {id}
                  </span>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Recycler Cell Inventory Table */}
      <div className="card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px', flexWrap: 'wrap', gap: '12px' }}>
          <div>
            <h3 style={{ fontSize: '1.05rem', fontWeight: 600 }}>Retired Cell Inventory Stream</h3>
            <span style={{ fontSize: '0.75rem', color: '#94a3b8' }}>
              Live inventory repository in revolt_db (Total tracked: {inventory.length} cells)
            </span>
          </div>

          <div style={{ display: 'flex', gap: '10px' }}>
            <select
              className="select"
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              style={{ width: '160px', fontSize: '0.8rem' }}
            >
              <option value="">All Statuses</option>
              <option value="AVAILABLE">AVAILABLE</option>
              <option value="RESERVED_FOR_PACK">RESERVED_FOR_PACK</option>
            </select>

            <select
              className="select"
              value={chemFilter}
              onChange={(e) => setChemFilter(e.target.value)}
              style={{ width: '120px', fontSize: '0.8rem' }}
            >
              <option value="">All Chem</option>
              <option value="LFP">LFP</option>
              <option value="NMC">NMC</option>
            </select>

            <button onClick={fetchInventory} className="btn btn-outline" style={{ fontSize: '0.8rem' }}>
              <RefreshCw size={14} /> Refresh
            </button>
          </div>
        </div>

        <div className="table-container">
          <table>
            <thead>
              <tr>
                <th>Cell ID</th>
                <th>Chemistry</th>
                <th>SOH (%)</th>
                <th>Status</th>
                <th>Pack Assignment</th>
                <th>Quantity</th>
              </tr>
            </thead>
            <tbody>
              {inventory.length === 0 ? (
                <tr>
                  <td colSpan="6" style={{ textAlign: 'center', color: '#64748b', padding: '24px' }}>
                    {loading ? 'Loading inventory items...' : 'No inventory records found. Approve cells from technician tab to populate.'}
                  </td>
                </tr>
              ) : (
                inventory.map((item, idx) => (
                  <tr key={item.battery_id || idx}>
                    <td className="mono" style={{ fontWeight: 600, color: '#38bdf8' }}>{item.battery_id}</td>
                    <td>{item.chemistry}</td>
                    <td className="mono" style={{ fontWeight: 600, color: (item.soh || 0) >= 80 ? '#34d399' : '#fbbf24' }}>
                      {item.soh !== undefined ? `${item.soh.toFixed(1)}%` : '--'}
                    </td>
                    <td>
                      <span className={item.status === 'AVAILABLE' ? 'badge badge-green' : 'badge badge-purple'}>
                        {item.status}
                      </span>
                    </td>
                    <td className="mono" style={{ color: item.pack_id ? '#c084fc' : '#64748b' }}>
                      {item.pack_id || '--'}
                    </td>
                    <td className="mono">{item.quantity || 1}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

