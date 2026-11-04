import React, { useState, useEffect } from 'react';
import { Wrench, PlusCircle, CheckCircle, XCircle, Send, AlertOctagon, Activity, Radio } from 'lucide-react';
import TelemetryChart from './TelemetryChart.jsx';

export default function TechnicianTab({ currentMode, showToast }) {
  const [batteryId, setBatteryId] = useState('BAT-TECH-01');
  const [chemistry, setChemistry] = useState('LFP');
  const [ratedCapacity, setRatedCapacity] = useState('2.5');
  const [manufacturer, setManufacturer] = useState('EVE Energy');
  const [sourceVehicle, setSourceVehicle] = useState('Ola S1 Pro');

  // Telemetry stream state
  const [telemetryPackets, setTelemetryPackets] = useState([
    { sec: 1.0, v: 3.35, i: -1.2, t: 26.5 },
    { sec: 2.0, v: 3.34, i: -1.2, t: 26.8 },
    { sec: 3.0, v: 3.32, i: -1.2, t: 27.2 },
    { sec: 4.0, v: 3.31, i: -1.2, t: 27.6 },
    { sec: 5.0, v: 3.30, i: -1.2, t: 28.1 }
  ]);
  const [isStreaming, setIsStreaming] = useState(false);

  // Exchange approval form
  const [technicianId, setTechnicianId] = useState('TECH-704');
  const [approvalNotes, setApprovalNotes] = useState('Terminals clean, no electrolyte leakage or cell swelling detected.');
  const [isApproved, setIsApproved] = useState(true);
  const [lastTxn, setLastTxn] = useState(null);

  // Fetch telemetry packets for current battery
  const fetchTelemetryHistory = async () => {
    try {
      const res = await fetch(`/api/live-data/${batteryId}`);
      if (res.ok) {
        const packets = await res.json();
        if (Array.isArray(packets) && packets.length > 0) {
          setTelemetryPackets(packets);
        }
      }
    } catch (err) {
      console.error('Error fetching telemetry:', err);
    }
  };

  useEffect(() => {
    fetchTelemetryHistory();
  }, [batteryId]);

  // Battery Registration
  const handleRegisterBattery = async (e) => {
    e.preventDefault();
    try {
      const res = await fetch('/api/batteries', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          battery_id: batteryId,
          chemistry: chemistry,
          rated_capacity_ah: parseFloat(ratedCapacity),
          manufacturer: manufacturer,
          source_vehicle: sourceVehicle
        })
      });

      if (res.status === 201) {
        showToast(`Battery '${batteryId}' registered successfully!`, 'success');
      } else if (res.status === 409) {
        showToast(`Battery '${batteryId}' is already registered.`, 'warning');
      } else {
        showToast(`Registration failed: ${res.statusText}`, 'error');
      }
    } catch (err) {
      showToast('Error registering battery', 'error');
    }
  };

  // Push single simulated packet
  const handlePushTelemetry = async () => {
    const lastSec = telemetryPackets.length > 0 ? telemetryPackets[telemetryPackets.length - 1].sec : 0.0;
    const nextSec = Number((lastSec + 1.0).toFixed(1));
    const randomV = Number((3.25 + Math.random() * 0.1).toFixed(3));
    const randomT = Number((28.0 + Math.random() * 1.5).toFixed(1));

    const packet = {
      battery_id: batteryId,
      sec: nextSec,
      v: randomV,
      i: -1.25,
      t: randomT,
      event: 'DISCHARGE'
    };

    try {
      const res = await fetch('/api/live-data', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Data-Mode': currentMode
        },
        body: JSON.stringify(packet)
      });

      if (res.ok) {
        setTelemetryPackets((prev) => [...prev, packet]);
        showToast(`Telemetry packet ingested (Mode: ${currentMode})`, 'success');
      }
    } catch (err) {
      showToast('Failed to ingest telemetry packet', 'error');
    }
  };

  // Run AI Evaluation
  const handleRunEvaluation = async () => {
    try {
      const res = await fetch('/api/analysis/evaluate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          battery_id: batteryId,
          chemistry: chemistry,
          rated_capacity_ah: parseFloat(ratedCapacity)
        })
      });
      if (res.ok) {
        const report = await res.json();
        showToast(`Evaluated: SOH ${report.soh?.toFixed(1) || '--'}% | Decision: ${report.decision}`, 'success');
      } else {
        showToast('Evaluation failed', 'error');
      }
    } catch (err) {
      showToast('Error executing evaluation', 'error');
    }
  };

  // Submit Technician Approval
  const handleSubmitApproval = async (e) => {
    e.preventDefault();
    try {
      const res = await fetch('/api/exchanges/approve', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          battery_id: batteryId,
          technician_id: technicianId,
          approved: isApproved,
          notes: approvalNotes
        })
      });

      if (res.ok) {
        const txn = await res.json();
        setLastTxn(txn);
        showToast(`Transaction ${txn.transaction_id} recorded: ${txn.status}!`, 'success');
      } else {
        const errData = await res.json();
        showToast(errData.detail || 'Approval submission failed', 'error');
      }
    } catch (err) {
      showToast('Error submitting technician approval', 'error');
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* Top Section: Registration & Diagnostic Controls */}
      <div className="grid-2">
        {/* Registration Card */}
        <div className="card">
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '16px' }}>
            <PlusCircle size={18} color="#10b981" />
            <h3 style={{ fontSize: '1.05rem', fontWeight: 600 }}>Cell Registration</h3>
          </div>

          <form onSubmit={handleRegisterBattery} style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            <div className="grid-2">
              <div>
                <label style={{ fontSize: '0.75rem', color: '#94a3b8', display: 'block', marginBottom: '4px' }}>Battery ID</label>
                <input
                  type="text"
                  className="input mono"
                  value={batteryId}
                  onChange={(e) => setBatteryId(e.target.value)}
                  required
                />
              </div>
              <div>
                <label style={{ fontSize: '0.75rem', color: '#94a3b8', display: 'block', marginBottom: '4px' }}>Chemistry</label>
                <select className="select" value={chemistry} onChange={(e) => setChemistry(e.target.value)}>
                  <option value="LFP">LFP (Lithium Iron Phosphate)</option>
                  <option value="NMC">NMC (Nickel Manganese Cobalt)</option>
                </select>
              </div>
            </div>

            <div className="grid-3">
              <div>
                <label style={{ fontSize: '0.75rem', color: '#94a3b8', display: 'block', marginBottom: '4px' }}>Rated Ah</label>
                <input
                  type="number"
                  step="0.1"
                  className="input mono"
                  value={ratedCapacity}
                  onChange={(e) => setRatedCapacity(e.target.value)}
                  required
                />
              </div>
              <div>
                <label style={{ fontSize: '0.75rem', color: '#94a3b8', display: 'block', marginBottom: '4px' }}>Manufacturer</label>
                <input
                  type="text"
                  className="input"
                  value={manufacturer}
                  onChange={(e) => setManufacturer(e.target.value)}
                />
              </div>
              <div>
                <label style={{ fontSize: '0.75rem', color: '#94a3b8', display: 'block', marginBottom: '4px' }}>Source Vehicle</label>
                <input
                  type="text"
                  className="input"
                  value={sourceVehicle}
                  onChange={(e) => setSourceVehicle(e.target.value)}
                />
              </div>
            </div>

            <button type="submit" className="btn btn-primary" style={{ marginTop: '8px' }}>
              Register Asset to revolt_db
            </button>
          </form>
        </div>

        {/* Telemetry Actions & Diagnostic Triggers */}
        <div className="card">
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Activity size={18} color="#06b6d4" />
              <h3 style={{ fontSize: '1.05rem', fontWeight: 600 }}>Diagnostic Ingestion Stream</h3>
            </div>
            <span className="badge badge-cyan">{currentMode} MODE</span>
          </div>

          <p style={{ fontSize: '0.8rem', color: '#94a3b8', marginBottom: '16px' }}>
            Ingests telemetry packets directly into <code className="mono">tests</code> collection tagged with mode provenance header.
          </p>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            <div style={{ display: 'flex', gap: '10px' }}>
              <button onClick={handlePushTelemetry} className="btn btn-outline" style={{ flex: 1 }}>
                <Send size={14} /> Send Sample Telemetry Packet
              </button>
              <button onClick={fetchTelemetryHistory} className="btn btn-outline">
                Refresh Packets
              </button>
            </div>

            <button onClick={handleRunEvaluation} className="btn btn-primary" style={{ background: '#06b6d4', color: '#082f49' }}>
              Execute Full Diagnostic Assessment & SOH Extraction
            </button>
          </div>

          {/* Envelope Safety Screener Indicator */}
          <div style={{ marginTop: '16px', background: 'rgba(0,0,0,0.25)', padding: '12px', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.06)' }}>
            <div style={{ fontSize: '0.75rem', color: '#94a3b8', marginBottom: '6px' }}>Active Safety Screener Rules:</div>
            <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap', fontSize: '0.7rem' }}>
              <span className="badge badge-green">LFP Limits: 2.00V - 3.80V</span>
              <span className="badge badge-green">Temp Max: 55°C</span>
              <span className="badge badge-green">Thermal Rate: &lt; 0.5°C/s</span>
            </div>
          </div>
        </div>
      </div>

      {/* Live Telemetry Visualizer Chart */}
      <div className="card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
          <div>
            <h3 style={{ fontSize: '1.05rem', fontWeight: 600 }}>Multi-Variable Real-Time Telemetry Graph</h3>
            <span style={{ fontSize: '0.75rem', color: '#94a3b8' }}>
              Visualizing INA226 voltage, load current, and thermistor temperature
            </span>
          </div>
          <span className="mono badge badge-gray">Active Battery: {batteryId}</span>
        </div>

        <TelemetryChart data={telemetryPackets} />
      </div>

      {/* Technician Inspection & Formal Sign-Off Transaction */}
      <div className="card">
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '14px' }}>
          <Wrench size={18} color="#f59e0b" />
          <h3 style={{ fontSize: '1.05rem', fontWeight: 600 }}>Certified Technician Formal Sign-Off</h3>
        </div>
        <p style={{ fontSize: '0.8rem', color: '#94a3b8', marginBottom: '16px' }}>
          Submits authenticated inspection results. Upon approval, computes cryptographic signoff signature hash, records exchange transaction, and dispatches cell to recycler inventory.
        </p>

        <form onSubmit={handleSubmitApproval} style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
          <div className="grid-2">
            <div>
              <label style={{ fontSize: '0.75rem', color: '#94a3b8', display: 'block', marginBottom: '4px' }}>Technician ID</label>
              <input
                type="text"
                className="input mono"
                value={technicianId}
                onChange={(e) => setTechnicianId(e.target.value)}
                required
              />
            </div>

            <div>
              <label style={{ fontSize: '0.75rem', color: '#94a3b8', display: 'block', marginBottom: '4px' }}>Inspection Verdict</label>
              <div style={{ display: 'flex', gap: '12px', marginTop: '6px' }}>
                <label style={{ display: 'flex', alignItems: 'center', gap: '6px', cursor: 'pointer', fontSize: '0.875rem' }}>
                  <input
                    type="radio"
                    name="verdict"
                    checked={isApproved === true}
                    onChange={() => setIsApproved(true)}
                  />
                  <span style={{ color: '#34d399', fontWeight: 600 }}>APPROVED (Eligible for Exchange/Reuse)</span>
                </label>
                <label style={{ display: 'flex', alignItems: 'center', gap: '6px', cursor: 'pointer', fontSize: '0.875rem' }}>
                  <input
                    type="radio"
                    name="verdict"
                    checked={isApproved === false}
                    onChange={() => setIsApproved(false)}
                  />
                  <span style={{ color: '#f87171', fontWeight: 600 }}>REJECTED (Physical Damage / Hazard)</span>
                </label>
              </div>
            </div>
          </div>

          <div>
            <label style={{ fontSize: '0.75rem', color: '#94a3b8', display: 'block', marginBottom: '4px' }}>Physical Inspection Notes</label>
            <textarea
              className="textarea"
              rows="2"
              value={approvalNotes}
              onChange={(e) => setApprovalNotes(e.target.value)}
              placeholder="Record terminal condition, case swelling, dents, or corrosion..."
            />
          </div>

          <button
            type="submit"
            className={isApproved ? "btn btn-primary" : "btn btn-danger"}
            style={{ width: '100%', padding: '10px' }}
          >
            {isApproved ? 'Sign & Authorize Exchange Transaction' : 'Record Official Inspection Rejection'}
          </button>
        </form>

        {/* Transaction Receipt Display */}
        {lastTxn && (
          <div style={{ marginTop: '16px', background: 'rgba(16, 185, 129, 0.08)', border: '1px solid rgba(16, 185, 129, 0.3)', padding: '14px', borderRadius: '8px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
              <span className="badge badge-green">TRANSACTION CONFIRMED</span>
              <span className="mono" style={{ fontSize: '0.8rem', color: '#94a3b8' }}>{lastTxn.timestamp}</span>
            </div>
            <div className="grid-3" style={{ fontSize: '0.85rem' }}>
              <div>TXN ID: <span className="mono" style={{ color: '#34d399', fontWeight: 600 }}>{lastTxn.transaction_id}</span></div>
              <div>Status: <span style={{ fontWeight: 600 }}>{lastTxn.status}</span></div>
              <div>Credit: <span className="mono" style={{ color: '#10b981', fontWeight: 700 }}>₹{lastTxn.indicative_credit_inr?.toFixed(2) || '0.00'}</span></div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

