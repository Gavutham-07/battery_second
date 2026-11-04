import React from 'react';
import { Radio, Database, Cpu, PlayCircle, ShieldCheck, Activity } from 'lucide-react';

export default function ModeBanner({ currentMode, setMode, apiHealth }) {
  const modes = [
    { id: 'LIVE', label: 'LIVE HARDWARE', icon: Cpu, desc: 'ESP32 + INA226 physical UART stream' },
    { id: 'REPLAY', label: 'BENCH REPLAY', icon: PlayCircle, desc: 'Recorded cycler discharge profiles' },
    { id: 'VIRTUAL', label: 'VIRTUAL SIM', icon: Radio, desc: 'Electro-thermal 18650 physics engine' },
    { id: 'DATASET', label: 'BENCHMARK DATA', icon: Database, desc: 'Standardized reference baseline' }
  ];

  return (
    <div style={{
      background: 'rgba(15, 23, 42, 0.85)',
      borderBottom: '1px solid rgba(255, 255, 255, 0.08)',
      padding: '10px 24px',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      flexWrap: 'wrap',
      gap: '12px'
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
        <span style={{ fontSize: '0.75rem', fontWeight: 700, color: '#94a3b8', letterSpacing: '0.08em' }}>
          DATA ACQUISITION PROVENANCE:
        </span>
        <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
          {modes.map((m) => {
            const Icon = m.icon;
            const active = currentMode === m.id;
            return (
              <button
                key={m.id}
                onClick={() => setMode(m.id)}
                title={m.desc}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                  padding: '5px 12px',
                  borderRadius: '6px',
                  fontSize: '0.75rem',
                  fontWeight: 600,
                  cursor: 'pointer',
                  border: active ? '1px solid #10b981' : '1px solid rgba(255, 255, 255, 0.1)',
                  background: active ? 'rgba(16, 185, 129, 0.2)' : 'rgba(255, 255, 255, 0.03)',
                  color: active ? '#34d399' : '#94a3b8',
                  transition: 'all 0.15s ease'
                }}
              >
                <Icon size={14} />
                {m.label}
              </button>
            );
          })}
        </div>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: '16px', fontSize: '0.75rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <span style={{
            width: '8px',
            height: '8px',
            borderRadius: '50%',
            background: apiHealth === 'healthy' ? '#10b981' : '#f59e0b',
            boxShadow: apiHealth === 'healthy' ? '0 0 8px #10b981' : 'none'
          }} />
          <span style={{ color: apiHealth === 'healthy' ? '#34d399' : '#fbbf24', fontWeight: 600 }}>
            BACKEND: {apiHealth ? apiHealth.toUpperCase() : 'CHECKING...'}
          </span>
        </div>
        <div className="badge badge-purple" style={{ fontSize: '0.7rem' }}>
          ACTIVE MODE: {currentMode}
        </div>
      </div>
    </div>
  );
}

