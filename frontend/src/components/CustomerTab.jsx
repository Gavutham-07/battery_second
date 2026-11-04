import React, { useState, useEffect } from 'react';
import { Gauge, TrendingUp, IndianRupee, Sliders, AlertTriangle, CheckCircle, ShieldAlert, Zap } from 'lucide-react';

export default function CustomerTab({ batteryId, currentMode, showToast }) {
  const [assessment, setAssessment] = useState(null);
  const [valuation, setValuation] = useState(null);
  const [whatIf, setWhatIf] = useState({
    daily_hours: 4.0,
    temp_c: 28.0,
    dod_pct: 80.0
  });
  const [simulationResult, setSimulationResult] = useState(null);
  const [loading, setLoading] = useState(false);

  // Fetch assessment & valuation for the battery
  const fetchData = async () => {
    setLoading(true);
    try {
      const resVal = await fetch(`/api/analysis/valuation/${batteryId}`);
      if (resVal.ok) {
        const valData = await resVal.json();
        setValuation(valData);
      }

      const resRep = await fetch(`/api/analysis/reports/${batteryId}`);
      if (resRep.ok) {
        const repData = await resRep.json();
        setAssessment(repData);
      }

      // Initial what-if run
      runSimulation();
    } catch (err) {
      console.error('Error fetching customer data:', err);
    } finally {
      setLoading(false);
    }
  };

  const runSimulation = async () => {
    try {
      const res = await fetch('/api/analysis/what-if', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          battery_id: batteryId,
          daily_hours: parseFloat(whatIf.daily_hours),
          temp_c: parseFloat(whatIf.temp_c),
          dod_pct: parseFloat(whatIf.dod_pct)
        })
      });
      if (res.ok) {
        const data = await res.json();
        setSimulationResult(data);
      }
    } catch (err) {
      console.error('Simulation error:', err);
    }
  };

  useEffect(() => {
    fetchData();
  }, [batteryId]);

  const getSafetyBadge = (status) => {
    switch (status) {
      case 'PASSED':
        return <span className="badge badge-green"><CheckCircle size={12} /> PASSED</span>;
      case 'WARNING':
        return <span className="badge badge-amber"><AlertTriangle size={12} /> WARNING</span>;
      case 'FAILED':
        return <span className="badge badge-red"><ShieldAlert size={12} /> FAILED</span>;
      default:
        return <span className="badge badge-gray">UNKNOWN</span>;
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* Top Banner: Battery Summary */}
      <div className="card" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '16px' }}>
        <div>
          <span style={{ fontSize: '0.75rem', color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.06em' }}>
            Battery Owner Diagnostics Portal
          </span>
          <h2 style={{ fontSize: '1.4rem', fontWeight: 700, color: '#f8fafc', marginTop: '2px' }}>
            Vehicle Cell: <span className="mono" style={{ color: '#10b981' }}>{batteryId}</span>
          </h2>
        </div>
        <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
          <button onClick={fetchData} className="btn btn-outline" style={{ fontSize: '0.8rem' }}>
            Refresh Data
          </button>
        </div>
      </div>

      {/* Grid 1: Diagnostic Metrics */}
      <div className="grid-4">
        <div className="card">
          <span style={{ fontSize: '0.75rem', color: '#94a3b8' }}>State of Health (SOH)</span>
          <div style={{ fontSize: '1.8rem', fontWeight: 700, color: '#10b981', marginTop: '4px' }} className="mono">
            {assessment?.soh !== undefined ? `${assessment.soh.toFixed(1)}%` : '--'}
          </div>
          <span style={{ fontSize: '0.75rem', color: '#64748b' }}>Decoupled degradation indicator</span>
        </div>

        <div className="card">
          <span style={{ fontSize: '0.75rem', color: '#94a3b8' }}>Available Capacity</span>
          <div style={{ fontSize: '1.8rem', fontWeight: 700, color: '#06b6d4', marginTop: '4px' }} className="mono">
            {assessment?.available_capacity_ah !== undefined ? `${assessment.available_capacity_ah.toFixed(3)} Ah` : '--'}
          </div>
          <span style={{ fontSize: '0.75rem', color: '#64748b' }}>Coulomb counted capacity</span>
        </div>

        <div className="card">
          <span style={{ fontSize: '0.75rem', color: '#94a3b8' }}>Safety Status</span>
          <div style={{ marginTop: '8px' }}>
            {getSafetyBadge(assessment?.safety_status || 'PASSED')}
          </div>
          <span style={{ fontSize: '0.75rem', color: '#64748b', display: 'block', marginTop: '6px' }}>
            Thermal & electrical envelope
          </span>
        </div>

        <div className="card">
          <span style={{ fontSize: '0.75rem', color: '#94a3b8' }}>Confidence & Decision</span>
          <div style={{ fontSize: '1.1rem', fontWeight: 700, color: '#a855f7', marginTop: '4px' }} className="mono">
            {assessment?.decision || 'CONTINUE_EV'}
          </div>
          <span style={{ fontSize: '0.75rem', color: '#64748b' }}>
            Confidence: {assessment?.confidence !== undefined ? `${assessment.confidence.toFixed(1)}%` : '--'}
          </span>
        </div>
      </div>

      {/* Grid 2: MBCO Circularity & Valuation Breakdown */}
      <div className="grid-2">
        {/* MBCO Recommendations */}
        <div className="card">
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '14px' }}>
            <TrendingUp size={18} color="#10b981" />
            <h3 style={{ fontSize: '1.05rem', fontWeight: 600 }}>Optimal Circularity Route (MBCO)</h3>
          </div>
          <p style={{ fontSize: '0.8rem', color: '#94a3b8', marginBottom: '14px' }}>
            Multi-Objective Circularity Optimisation evaluating technical fit, safety, and economic return.
          </p>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            {(assessment?.mbco_recommendations || [
              { route: 'Residential Solar BESS', suitability_score: 0.95, technical_fit: true, safety_eligible: true },
              { route: 'Commercial UPS Backup', suitability_score: 0.88, technical_fit: true, safety_eligible: true },
              { route: 'Light EV / 2-Wheeler', suitability_score: 0.82, technical_fit: true, safety_eligible: true },
              { route: 'Direct Material Recycling', suitability_score: 0.35, technical_fit: true, safety_eligible: true }
            ]).map((rec, i) => (
              <div
                key={i}
                style={{
                  padding: '10px 14px',
                  borderRadius: '8px',
                  background: i === 0 ? 'rgba(16, 185, 129, 0.1)' : 'rgba(255,255,255,0.02)',
                  border: i === 0 ? '1px solid rgba(16, 185, 129, 0.3)' : '1px solid rgba(255,255,255,0.05)',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center'
                }}
              >
                <div>
                  <div style={{ fontWeight: 600, fontSize: '0.875rem', color: i === 0 ? '#34d399' : '#f8fafc' }}>
                    {i === 0 ? '★ ' : ''}{rec.route}
                  </div>
                  <span style={{ fontSize: '0.72rem', color: '#64748b' }}>
                    Tech Fit: {rec.technical_fit ? 'YES' : 'NO'} | Safety: {rec.safety_eligible ? 'ELIGIBLE' : 'DISQUALIFIED'}
                  </span>
                </div>
                <div style={{ textAlign: 'right' }}>
                  <span className="mono" style={{ fontWeight: 700, fontSize: '0.95rem', color: i === 0 ? '#10b981' : '#94a3b8' }}>
                    {(rec.suitability_score * 100).toFixed(0)}%
                  </span>
                  <div style={{ fontSize: '0.7rem', color: '#64748b' }}>Suitability</div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Indicative Valuation Breakdown */}
        <div className="card">
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '14px' }}>
            <IndianRupee size={18} color="#06b6d4" />
            <h3 style={{ fontSize: '1.05rem', fontWeight: 600 }}>Transparent Trade-In Valuation</h3>
          </div>
          <p style={{ fontSize: '0.8rem', color: '#94a3b8', marginBottom: '14px' }}>
            Itemized, non-opaque indicative valuation calculated from live capacity, SOH, and scrap floor guarantees.
          </p>

          <div style={{ background: 'rgba(0,0,0,0.3)', borderRadius: '8px', padding: '16px', marginBottom: '14px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px', fontSize: '0.85rem' }}>
              <span style={{ color: '#94a3b8' }}>Base Chemistry Credit ({valuation?.chemistry || 'LFP'} @ ₹{valuation?.breakdown?.chemistry_base_rate_per_ah || 120}/Ah):</span>
              <span className="mono" style={{ color: '#f8fafc' }}>₹{valuation?.breakdown?.gross_capacity_credit_inr?.toFixed(2) || '252.00'}</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px', fontSize: '0.85rem' }}>
              <span style={{ color: '#94a3b8' }}>Degradation Penalty:</span>
              <span className="mono" style={{ color: '#fbbf24' }}>-₹{valuation?.breakdown?.degradation_penalty_inr?.toFixed(2) || '40.32'}</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px', fontSize: '0.85rem' }}>
              <span style={{ color: '#94a3b8' }}>Safety Risk Penalty:</span>
              <span className="mono" style={{ color: '#f87171' }}>-₹{valuation?.breakdown?.safety_risk_penalty_inr?.toFixed(2) || '0.00'}</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '12px', fontSize: '0.85rem' }}>
              <span style={{ color: '#94a3b8' }}>Diagnostic Refurbish Fee:</span>
              <span className="mono" style={{ color: '#f87171' }}>-₹{valuation?.breakdown?.diagnostic_refurbish_fee_inr?.toFixed(2) || '25.00'}</span>
            </div>
            <div style={{ borderTop: '1px solid rgba(255,255,255,0.1)', paddingTop: '10px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <span style={{ fontWeight: 700, fontSize: '1rem', color: '#f8fafc' }}>Net Indicative Credit:</span>
                <div style={{ fontSize: '0.72rem', color: '#10b981' }}>Scrap Floor: ₹{valuation?.breakdown?.material_scrap_floor_inr?.toFixed(2) || '15.00'}</div>
              </div>
              <span className="mono" style={{ fontWeight: 800, fontSize: '1.4rem', color: '#10b981' }}>
                ₹{valuation?.net_indicative_valuation_inr?.toFixed(2) || '186.68'}
              </span>
            </div>
          </div>
          <p style={{ fontSize: '0.7rem', color: '#64748b', fontStyle: 'italic' }}>
            Disclaimer: Indicative prototype valuation based on real-time electro-chemical testing. Not an official commercial guarantee.
          </p>
        </div>
      </div>

      {/* Section 3: Interactive What-If Lifetime Simulator */}
      <div className="card">
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '14px' }}>
          <Sliders size={18} color="#f59e0b" />
          <h3 style={{ fontSize: '1.05rem', fontWeight: 600 }}>Conditional Remaining Useful Life (RUL) What-If Simulator</h3>
        </div>
        <p style={{ fontSize: '0.8rem', color: '#94a3b8', marginBottom: '18px' }}>
          Simulates Arrhenius thermal stress ($E_a/R$), Wöhler Depth-of-Discharge power law ($DoD^{1.4}$), and daily turnover to estimate cycle life to the 70% knee point.
        </p>

        <div className="grid-3" style={{ marginBottom: '20px' }}>
          {/* Daily Usage Slider */}
          <div style={{ background: 'rgba(0,0,0,0.25)', padding: '14px', borderRadius: '8px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
              <span style={{ fontSize: '0.8rem', color: '#94a3b8' }}>Daily Utilization</span>
              <span className="mono" style={{ fontWeight: 700, color: '#10b981' }}>{whatIf.daily_hours} hrs/day</span>
            </div>
            <input
              type="range"
              min="1.0"
              max="16.0"
              step="0.5"
              value={whatIf.daily_hours}
              onChange={(e) => {
                setWhatIf({ ...whatIf, daily_hours: e.target.value });
                setTimeout(runSimulation, 50);
              }}
            />
          </div>

          {/* Operating Temp Slider */}
          <div style={{ background: 'rgba(0,0,0,0.25)', padding: '14px', borderRadius: '8px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
              <span style={{ fontSize: '0.8rem', color: '#94a3b8' }}>Operating Temperature</span>
              <span className="mono" style={{ fontWeight: 700, color: '#06b6d4' }}>{whatIf.temp_c}°C</span>
            </div>
            <input
              type="range"
              min="15.0"
              max="50.0"
              step="1.0"
              value={whatIf.temp_c}
              onChange={(e) => {
                setWhatIf({ ...whatIf, temp_c: e.target.value });
                setTimeout(runSimulation, 50);
              }}
            />
          </div>

          {/* Depth of Discharge Slider */}
          <div style={{ background: 'rgba(0,0,0,0.25)', padding: '14px', borderRadius: '8px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
              <span style={{ fontSize: '0.8rem', color: '#94a3b8' }}>Depth of Discharge (DoD)</span>
              <span className="mono" style={{ fontWeight: 700, color: '#f59e0b' }}>{whatIf.dod_pct}%</span>
            </div>
            <input
              type="range"
              min="30.0"
              max="100.0"
              step="5.0"
              value={whatIf.dod_pct}
              onChange={(e) => {
                setWhatIf({ ...whatIf, dod_pct: e.target.value });
                setTimeout(runSimulation, 50);
              }}
            />
          </div>
        </div>

        {/* Simulation Output Cards */}
        <div className="grid-4" style={{ background: 'rgba(16, 185, 129, 0.05)', border: '1px solid rgba(16, 185, 129, 0.2)', borderRadius: '8px', padding: '16px' }}>
          <div>
            <span style={{ fontSize: '0.75rem', color: '#94a3b8' }}>Projected Cycle Life:</span>
            <div className="mono" style={{ fontSize: '1.4rem', fontWeight: 800, color: '#10b981', marginTop: '2px' }}>
              {simulationResult?.projected_cycle_life || 1420} cycles
            </div>
          </div>

          <div>
            <span style={{ fontSize: '0.75rem', color: '#94a3b8' }}>Projected Useful Life:</span>
            <div className="mono" style={{ fontSize: '1.4rem', fontWeight: 800, color: '#06b6d4', marginTop: '2px' }}>
              ~{simulationResult?.projected_months_remaining || 34} months
            </div>
          </div>

          <div>
            <span style={{ fontSize: '0.75rem', color: '#94a3b8' }}>Stress Acceleration:</span>
            <div className="mono" style={{ fontSize: '1.4rem', fontWeight: 800, color: '#f59e0b', marginTop: '2px' }}>
              {simulationResult?.acceleration_factor?.toFixed(2) || '1.18'}x
            </div>
          </div>

          <div>
            <span style={{ fontSize: '0.75rem', color: '#94a3b8' }}>Recommended DoD Limit:</span>
            <div className="mono" style={{ fontSize: '1.4rem', fontWeight: 800, color: '#a855f7', marginTop: '2px' }}>
              &le; {simulationResult?.recommended_dod_limit || 80.0}%
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

