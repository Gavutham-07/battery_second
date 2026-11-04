import React, { useState, useEffect } from 'react';
import { Shield, ShieldCheck, ShieldAlert, QrCode, Search, FileCheck, CheckCircle2, AlertOctagon } from 'lucide-react';
import QRCodeDisplay from './QRCodeDisplay.jsx';

export default function AuditorTab({ defaultBatteryId, showToast }) {
  const [batteryId, setBatteryId] = useState(defaultBatteryId || 'BAT-101');
  const [passport, setPassport] = useState(null);
  const [loading, setLoading] = useState(false);

  // Verifier state
  const [verifyInput, setVerifyInput] = useState('');
  const [verifyResult, setVerifyResult] = useState(null);
  const [verifyLoading, setVerifyLoading] = useState(false);

  const fetchPassport = async (id) => {
    setLoading(true);
    try {
      // First try generate/get passport
      let res = await fetch(`/api/passport/${id}`);
      if (res.status === 404) {
        // Attempt generation if evaluated
        const genRes = await fetch('/api/passport/generate', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ battery_id: id })
        });
        if (genRes.ok) {
          res = genRes;
        }
      }

      if (res.ok) {
        const data = await res.json();
        setPassport(data);
        setVerifyInput(JSON.stringify(data, null, 2));
      } else {
        setPassport(null);
        showToast(`Passport for '${id}' not found or cell un-evaluated.`, 'warning');
      }
    } catch (err) {
      console.error('Error fetching passport:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (batteryId) {
      fetchPassport(batteryId);
    }
  }, []);

  const handleVerify = async () => {
    setVerifyLoading(true);
    try {
      let parsedPayload;
      try {
        parsedPayload = JSON.parse(verifyInput);
      } catch (e) {
        showToast('Invalid JSON format in passport verifier input', 'error');
        setVerifyLoading(false);
        return;
      }

      const res = await fetch('/api/passport/verify', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(parsedPayload)
      });

      if (res.ok) {
        const result = await res.json();
        setVerifyResult(result);
        if (result.valid) {
          showToast('Passport verified: Authentic & Untampered!', 'success');
        } else {
          showToast(`Tamper detected: ${result.error}`, 'error');
        }
      }
    } catch (err) {
      showToast('Error during passport verification', 'error');
    } finally {
      setVerifyLoading(false);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* Top Search Banner */}
      <div className="card" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '14px' }}>
        <div>
          <span style={{ fontSize: '0.75rem', color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.06em' }}>
            Public / Regulatory Audit Portal
          </span>
          <h2 style={{ fontSize: '1.4rem', fontWeight: 700, color: '#f8fafc', marginTop: '2px' }}>
            Digital Battery Passport & Cryptographic Integrity Audit
          </h2>
        </div>

        <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
          <input
            type="text"
            className="input mono"
            placeholder="Search Battery ID..."
            value={batteryId}
            onChange={(e) => setBatteryId(e.target.value)}
            style={{ width: '200px', fontSize: '0.85rem' }}
          />
          <button onClick={() => fetchPassport(batteryId)} className="btn btn-primary" style={{ fontSize: '0.85rem' }}>
            <Search size={14} /> Search
          </button>
        </div>
      </div>

      {/* Main Passport Viewer */}
      {passport ? (
        <div className="grid-2">
          {/* Left Column: Passport Specifications */}
          <div className="card">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <ShieldCheck size={20} color="#10b981" />
                <h3 style={{ fontSize: '1.1rem', fontWeight: 700 }}>EU / Global Digital Battery Passport</h3>
              </div>
              <span className="badge badge-green">SHA-256 SECURED</span>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', fontSize: '0.875rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid rgba(255,255,255,0.06)', paddingBottom: '8px' }}>
                <span style={{ color: '#94a3b8' }}>Battery Asset ID:</span>
                <span className="mono" style={{ fontWeight: 700, color: '#38bdf8' }}>{passport.battery_id}</span>
              </div>

              <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid rgba(255,255,255,0.06)', paddingBottom: '8px' }}>
                <span style={{ color: '#94a3b8' }}>Cell Chemistry:</span>
                <span style={{ fontWeight: 600 }}>{passport.chemistry}</span>
              </div>

              <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid rgba(255,255,255,0.06)', paddingBottom: '8px' }}>
                <span style={{ color: '#94a3b8' }}>Rated Capacity:</span>
                <span className="mono">{passport.rated_capacity_ah} Ah</span>
              </div>

              <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid rgba(255,255,255,0.06)', paddingBottom: '8px' }}>
                <span style={{ color: '#94a3b8' }}>Manufacturer & Heritage:</span>
                <span>{passport.manufacturer || 'EVE Energy'} ({passport.source_vehicle || 'Ola S1 Pro'})</span>
              </div>

              <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid rgba(255,255,255,0.06)', paddingBottom: '8px' }}>
                <span style={{ color: '#94a3b8' }}>Certified SOH:</span>
                <span className="mono" style={{ fontWeight: 700, color: '#10b981' }}>{passport.assessment?.soh?.toFixed(1) || '--'}%</span>
              </div>

              <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid rgba(255,255,255,0.06)', paddingBottom: '8px' }}>
                <span style={{ color: '#94a3b8' }}>Available Capacity:</span>
                <span className="mono" style={{ color: '#06b6d4' }}>{passport.assessment?.available_capacity_ah?.toFixed(3) || '--'} Ah</span>
              </div>

              <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid rgba(255,255,255,0.06)', paddingBottom: '8px' }}>
                <span style={{ color: '#94a3b8' }}>Safety Status & Decision:</span>
                <span>
                  <span className={passport.assessment?.safety_status === 'PASSED' ? 'badge badge-green' : 'badge badge-amber'} style={{ marginRight: '6px' }}>
                    {passport.assessment?.safety_status}
                  </span>
                  <span className="mono" style={{ fontSize: '0.8rem' }}>{passport.assessment?.decision}</span>
                </span>
              </div>

              <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid rgba(255,255,255,0.06)', paddingBottom: '8px' }}>
                <span style={{ color: '#94a3b8' }}>Acquisition Provenance:</span>
                <span className="badge badge-purple">{passport.assessment?.mode || 'LIVE'}</span>
              </div>

              <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid rgba(255,255,255,0.06)', paddingBottom: '8px' }}>
                <span style={{ color: '#94a3b8' }}>Issued At:</span>
                <span className="mono" style={{ fontSize: '0.75rem', color: '#94a3b8' }}>{passport.issued_at}</span>
              </div>
            </div>

            {/* Cryptographic Hash Card */}
            <div style={{ marginTop: '16px', background: 'rgba(0,0,0,0.3)', padding: '12px', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.08)' }}>
              <span style={{ fontSize: '0.7rem', color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.06em', display: 'block', marginBottom: '4px' }}>
                SHA-256 Canonical Integrity Hash:
              </span>
              <div className="mono" style={{ fontSize: '0.75rem', color: '#10b981', wordBreak: 'break-all' }}>
                {passport.integrity_hash}
              </div>
            </div>
          </div>

          {/* Right Column: Interactive QR Code Representation */}
          <div className="card" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '16px' }}>
              <QrCode size={18} color="#06b6d4" />
              <h3 style={{ fontSize: '1.05rem', fontWeight: 600 }}>Decentralized Asset QR Representation</h3>
            </div>

            <QRCodeDisplay qrString={passport.qr_code} batteryId={passport.battery_id} />
          </div>
        </div>
      ) : (
        <div className="card" style={{ textAlign: 'center', padding: '40px' }}>
          <p style={{ color: '#94a3b8', fontSize: '0.9rem' }}>
            {loading ? 'Fetching Digital Battery Passport...' : 'No passport found for this battery. Register and evaluate the cell first.'}
          </p>
        </div>
      )}

      {/* Cryptographic Tamper Verification Workbench */}
      <div className="card">
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '14px' }}>
          <FileCheck size={18} color="#a855f7" />
          <h3 style={{ fontSize: '1.05rem', fontWeight: 600 }}>Independent Passport Integrity Verification Workbench</h3>
        </div>
        <p style={{ fontSize: '0.8rem', color: '#94a3b8', marginBottom: '14px' }}>
          Auditors and buyers can paste any passport payload below. The engine serializes canonical fields and recalculates the SHA-256 checksum to detect any bit-level tampering.
        </p>

        <textarea
          className="textarea mono"
          rows="7"
          value={verifyInput}
          onChange={(e) => setVerifyInput(e.target.value)}
          placeholder="Paste passport JSON payload here..."
          style={{ fontSize: '0.78rem', marginBottom: '12px' }}
        />

        <div style={{ display: 'flex', gap: '10px' }}>
          <button
            onClick={handleVerify}
            disabled={verifyLoading}
            className="btn btn-primary"
            style={{ flex: 1 }}
          >
            {verifyLoading ? 'Computing Cryptographic Verification...' : 'Execute SHA-256 Integrity Verification'}
          </button>
        </div>

        {/* Verification Result Banner */}
        {verifyResult && (
          <div style={{
            marginTop: '16px',
            background: verifyResult.valid ? 'rgba(16, 185, 129, 0.08)' : 'rgba(239, 68, 68, 0.08)',
            border: verifyResult.valid ? '1px solid rgba(16, 185, 129, 0.3)' : '1px solid rgba(239, 68, 68, 0.3)',
            borderRadius: '8px',
            padding: '14px'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
              {verifyResult.valid ? <CheckCircle2 size={18} color="#10b981" /> : <AlertOctagon size={18} color="#ef4444" />}
              <span style={{ fontWeight: 700, color: verifyResult.valid ? '#34d399' : '#f87171' }}>
                {verifyResult.valid ? 'INTEGRITY VERIFIED: AUTHENTIC' : 'INTEGRITY CHECK FAILED: TAMPER DETECTED'}
              </span>
            </div>

            <div style={{ fontSize: '0.8rem', display: 'flex', flexDirection: 'column', gap: '4px' }}>
              <div>Computed Checksum: <span className="mono" style={{ color: '#38bdf8' }}>{verifyResult.computed_hash}</span></div>
              <div>Match Status: <span style={{ fontWeight: 600 }}>{verifyResult.matched ? 'MATCHED (100% Bit-for-bit)' : 'MISMATCH'}</span></div>
              {verifyResult.error && (
                <div style={{ color: '#f87171', fontWeight: 600 }}>Error: {verifyResult.error}</div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

