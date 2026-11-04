import React, { useState } from 'react';

export default function TelemetryChart({ data = [] }) {
  const [activeMetric, setActiveMetric] = useState('v'); // 'v' | 'i' | 't'

  if (!data || data.length === 0) {
    return (
      <div style={{
        height: '240px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        color: '#64748b',
        fontSize: '0.875rem',
        border: '1px dashed rgba(255,255,255,0.1)',
        borderRadius: '8px'
      }}>
        No telemetry packets ingested yet. Stream live packets or run replay.
      </div>
    );
  }

  const width = 650;
  const height = 220;
  const padding = { top: 20, right: 30, bottom: 30, left: 50 };

  const graphWidth = width - padding.left - padding.right;
  const graphHeight = height - padding.top - padding.bottom;

  // Extract selected metric values
  const values = data.map((d) => d[activeMetric] ?? 0);
  const minVal = Math.min(...values);
  const maxVal = Math.max(...values);
  const valRange = maxVal - minVal === 0 ? 1 : maxVal - minVal;

  // Compute SVG polyline points
  const points = data.map((d, index) => {
    const x = padding.left + (index / Math.max(data.length - 1, 1)) * graphWidth;
    const y = padding.top + graphHeight - ((d[activeMetric] - minVal) / valRange) * graphHeight;
    return `${x},${y}`;
  }).join(' ');

  const metricColors = {
    v: { stroke: '#10b981', fill: 'rgba(16, 185, 129, 0.1)', unit: 'V', label: 'Voltage' },
    i: { stroke: '#06b6d4', fill: 'rgba(6, 182, 212, 0.1)', unit: 'A', label: 'Current' },
    t: { stroke: '#f59e0b', fill: 'rgba(245, 158, 11, 0.1)', unit: '°C', label: 'Temperature' }
  };

  const curr = metricColors[activeMetric];
  const lastPacket = data[data.length - 1] || {};

  return (
    <div style={{ width: '100%' }}>
      {/* Metric Toggle Tabs */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
        <div style={{ display: 'flex', gap: '8px' }}>
          {Object.entries(metricColors).map(([key, cfg]) => (
            <button
              key={key}
              onClick={() => setActiveMetric(key)}
              style={{
                padding: '4px 10px',
                borderRadius: '6px',
                fontSize: '0.75rem',
                fontWeight: 600,
                cursor: 'pointer',
                border: activeMetric === key ? `1px solid ${cfg.stroke}` : '1px solid rgba(255,255,255,0.08)',
                background: activeMetric === key ? 'rgba(255,255,255,0.08)' : 'transparent',
                color: activeMetric === key ? cfg.stroke : '#94a3b8'
              }}
            >
              {cfg.label} ({lastPacket[key] !== undefined ? `${lastPacket[key]}${cfg.unit}` : '--'})
            </button>
          ))}
        </div>
        <span className="mono" style={{ fontSize: '0.75rem', color: '#94a3b8' }}>
          Packets: {data.length} | Range: [{minVal.toFixed(2)} - {maxVal.toFixed(2)} {curr.unit}]
        </span>
      </div>

      {/* SVG Canvas */}
      <div style={{ overflowX: 'auto', background: 'rgba(0,0,0,0.2)', borderRadius: '8px', padding: '8px' }}>
        <svg viewBox={`0 0 ${width} ${height}`} style={{ width: '100%', height: 'auto', display: 'block' }}>
          {/* Grid lines */}
          <line x1={padding.left} y1={padding.top} x2={width - padding.right} y2={padding.top} stroke="rgba(255,255,255,0.06)" />
          <line x1={padding.left} y1={padding.top + graphHeight / 2} x2={width - padding.right} y2={padding.top + graphHeight / 2} stroke="rgba(255,255,255,0.06)" />
          <line x1={padding.left} y1={height - padding.bottom} x2={width - padding.right} y2={height - padding.bottom} stroke="rgba(255,255,255,0.12)" />

          {/* Y Axis Labels */}
          <text x={padding.left - 8} y={padding.top + 4} fill="#64748b" fontSize="10" textAnchor="end" fontFamily="monospace">
            {maxVal.toFixed(2)}
          </text>
          <text x={padding.left - 8} y={padding.top + graphHeight / 2 + 4} fill="#64748b" fontSize="10" textAnchor="end" fontFamily="monospace">
            {((maxVal + minVal) / 2).toFixed(2)}
          </text>
          <text x={padding.left - 8} y={height - padding.bottom} fill="#64748b" fontSize="10" textAnchor="end" fontFamily="monospace">
            {minVal.toFixed(2)}
          </text>

          {/* Graph Curve */}
          <polyline
            fill="none"
            stroke={curr.stroke}
            strokeWidth="2.5"
            strokeLinecap="round"
            strokeLinejoin="round"
            points={points}
          />

          {/* Data Points */}
          {data.map((d, index) => {
            const x = padding.left + (index / Math.max(data.length - 1, 1)) * graphWidth;
            const y = padding.top + graphHeight - ((d[activeMetric] - minVal) / valRange) * graphHeight;
            return (
              <circle
                key={index}
                cx={x}
                cy={y}
                r="3"
                fill={curr.stroke}
                opacity="0.8"
              >
                <title>{`Sec: ${d.sec}s | ${curr.label}: ${d[activeMetric]}${curr.unit}`}</title>
              </circle>
            );
          })}
        </svg>
      </div>
    </div>
  );
}

