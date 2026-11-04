import React, { useState, useEffect } from 'react';
import { User, Wrench, RefreshCw, ShieldCheck, BatteryCharging, Check, AlertCircle, ArrowLeft } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import ModeBanner from '../components/ModeBanner.jsx';
import CustomerTab from '../components/CustomerTab.jsx';
import TechnicianTab from '../components/TechnicianTab.jsx';
import RecyclerTab from '../components/RecyclerTab.jsx';
import AuditorTab from '../components/AuditorTab.jsx';

export default function ClassicConsole() {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState('customer'); // 'customer' | 'technician' | 'recycler' | 'auditor'
  const [currentMode, setCurrentMode] = useState('LIVE'); // 'LIVE' | 'REPLAY' | 'VIRTUAL' | 'DATASET'
  const [apiHealth, setApiHealth] = useState('checking');
  const [batteryId, setBatteryId] = useState('BAT-101');
  const [toast, setToast] = useState(null);

  // Show Toast
  const showToast = (message, type = 'info') => {
    setToast({ message, type });
    setTimeout(() => {
      setToast((curr) => (curr?.message === message ? null : curr));
    }, 4000);
  };

  // Check backend health
  const checkHealth = async () => {
    try {
      const res = await fetch('/api/health');
      if (res.ok) {
        const data = await res.json();
        setApiHealth(data.status);
      } else {
        setApiHealth('degraded');
      }
    } catch (err) {
      setApiHealth('offline');
    }
  };

  useEffect(() => {
    checkHealth();
    const interval = setInterval(checkHealth, 15000);
    return () => clearInterval(interval);
  }, []);

  const tabs = [
    { id: 'customer', label: 'Customer / EV Owner', icon: User, desc: 'Health, Valuation & RUL' },
    { id: 'technician', label: 'Certified Technician', icon: Wrench, desc: 'Diagnostics & Sign-Off' },
    { id: 'recycler', label: 'Recycler / Refurbisher', icon: RefreshCw, desc: 'Inventory & 4S Grouping' },
    { id: 'auditor', label: 'Public / Auditor', icon: ShieldCheck, desc: 'Battery Passport & Integrity' }
  ];

  return (
    <div className="classic-console" style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      {/* Platform Header */}
      <header style={{
        background: 'rgba(10, 15, 29, 0.95)',
        borderBottom: '1px solid rgba(255, 255, 255, 0.08)',
        padding: '16px 24px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        flexWrap: 'wrap',
        gap: '16px'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <button
            onClick={() => navigate('/')}
            style={{
              background: 'rgba(255, 255, 255, 0.05)',
              border: '1px solid rgba(255, 255, 255, 0.1)',
              borderRadius: '6px',
              color: '#94a3b8',
              padding: '6px 10px',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              fontSize: '0.8rem'
            }}
          >
            <ArrowLeft size={14} /> Back to Hub
          </button>
          <div style={{
            background: 'linear-gradient(135deg, #10b981 0%, #06b6d4 100%)',
            width: '36px',
            height: '36px',
            borderRadius: '8px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            boxShadow: '0 0 16px rgba(16, 185, 129, 0.4)'
          }}>
            <BatteryCharging size={22} color="#042f2e" />
          </div>
          <div>
            <h1 style={{ fontSize: '1.25rem', fontWeight: 800, letterSpacing: '-0.02em', color: '#fff' }}>
              Re<span style={{ color: '#10b981' }}>Volt</span> Classic Console
            </h1>
            <span style={{ fontSize: '0.7rem', color: '#94a3b8', letterSpacing: '0.04em' }}>
              4-Stakeholder Tabbed View
            </span>
          </div>
        </div>

        {/* Global Active Battery Input */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <span style={{ fontSize: '0.75rem', color: '#94a3b8' }}>Target Battery:</span>
          <input
            type="text"
            className="input mono"
            value={batteryId}
            onChange={(e) => setBatteryId(e.target.value)}
            style={{ width: '130px', padding: '4px 8px', fontSize: '0.8rem', background: '#0f172a', color: '#f8fafc', border: '1px solid rgba(255,255,255,0.15)', borderRadius: '4px' }}
          />
        </div>
      </header>

      {/* 4-Mode Provenance Banner */}
      <ModeBanner currentMode={currentMode} setMode={setCurrentMode} apiHealth={apiHealth} />

      {/* Stakeholder Tab Navigation */}
      <nav style={{
        background: 'rgba(15, 23, 42, 0.6)',
        borderBottom: '1px solid rgba(255, 255, 255, 0.06)',
        padding: '0 24px',
        display: 'flex',
        gap: '4px',
        overflowX: 'auto'
      }}>
        {tabs.map((tab) => {
          const Icon = tab.icon;
          const active = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                padding: '14px 18px',
                background: 'transparent',
                border: 'none',
                borderBottom: active ? '2px solid #10b981' : '2px solid transparent',
                color: active ? '#10b981' : '#94a3b8',
                cursor: 'pointer',
                fontWeight: active ? 700 : 500,
                fontSize: '0.875rem',
                whiteSpace: 'nowrap',
                transition: 'all 0.15s ease'
              }}
            >
              <Icon size={16} />
              <span>{tab.label}</span>
            </button>
          );
        })}
      </nav>

      {/* Main Stakeholder Viewport */}
      <main style={{ flex: 1, padding: '24px', maxWidth: '1400px', margin: '0 auto', width: '100%' }}>
        {activeTab === 'customer' && (
          <CustomerTab batteryId={batteryId} currentMode={currentMode} showToast={showToast} />
        )}
        {activeTab === 'technician' && (
          <TechnicianTab currentMode={currentMode} showToast={showToast} />
        )}
        {activeTab === 'recycler' && (
          <RecyclerTab showToast={showToast} />
        )}
        {activeTab === 'auditor' && (
          <AuditorTab defaultBatteryId={batteryId} showToast={showToast} />
        )}
      </main>

      {/* Toast Notification Banner */}
      {toast && (
        <div style={{
          position: 'fixed',
          bottom: '24px',
          right: '24px',
          background: toast.type === 'error' ? 'rgba(239, 68, 68, 0.95)' : toast.type === 'warning' ? 'rgba(245, 158, 11, 0.95)' : 'rgba(16, 185, 129, 0.95)',
          color: toast.type === 'warning' ? '#0a0f1d' : '#fff',
          padding: '12px 20px',
          borderRadius: '8px',
          boxShadow: '0 8px 24px rgba(0,0,0,0.5)',
          display: 'flex',
          alignItems: 'center',
          gap: '10px',
          fontSize: '0.875rem',
          fontWeight: 600,
          zIndex: 9999,
          animation: 'fadeIn 0.2s ease'
        }}>
          {toast.type === 'error' ? <AlertCircle size={18} /> : <Check size={18} />}
          <span>{toast.message}</span>
        </div>
      )}

      {/* Footer */}
      <footer style={{
        background: 'rgba(10, 15, 29, 0.8)',
        borderTop: '1px solid rgba(255, 255, 255, 0.05)',
        padding: '14px 24px',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        flexWrap: 'wrap',
        gap: '12px',
        fontSize: '0.75rem',
        color: '#64748b'
      }}>
        <div>
          ReVolt Platform v1.0.0 &bull; Team: Mona (HW), Member 2 (Backend/DB), Member 3 (AI Engine), Amrutha (Frontend)
        </div>
        <div className="mono">
          FastAPI &bull; MongoDBCommunity &bull; React &bull; SHA-256 Passports
        </div>
      </footer>
    </div>
  );
}
