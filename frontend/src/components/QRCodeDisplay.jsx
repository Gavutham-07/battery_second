import React, { useState } from 'react';
import { QrCode, Check, Copy, ExternalLink } from 'lucide-react';

export default function QRCodeDisplay({ qrString, batteryId }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    if (qrString) {
      navigator.clipboard.writeText(qrString);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  // Generate a deterministic 21x21 QR-like matrix pattern based on hash
  const size = 21;
  const hash = qrString ? qrString.split('hash=')[1] || '0123456789abcdef' : '0123456789abcdef';

  const matrix = Array.from({ length: size }, (_, r) =>
    Array.from({ length: size }, (_, c) => {
      // Standard QR position detection patterns (corners)
      if (
        (r < 7 && c < 7) ||
        (r < 7 && c >= size - 7) ||
        (r >= size - 7 && c < 7)
      ) {
        if (
          r === 0 || r === 6 || c === 0 || c === 6 ||
          (r >= size - 7 && (r === size - 7 || r === size - 1)) ||
          (c >= size - 7 && (c === size - 7 || c === size - 1)) ||
          (r >= 2 && r <= 4 && c >= 2 && c <= 4) ||
          (r >= 2 && r <= 4 && c >= size - 5 && c <= size - 3) ||
          (r >= size - 5 && r <= size - 3 && c >= 2 && c <= 4)
        ) {
          return true;
        }
        return false;
      }
      // Pseudo-random bit based on char codes of hash and coords
      const charIndex = (r * size + c) % hash.length;
      return (hash.charCodeAt(charIndex) + r * 7 + c * 13) % 3 === 0;
    })
  );

  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '14px' }}>
      <div style={{
        background: '#fff',
        padding: '12px',
        borderRadius: '12px',
        boxShadow: '0 0 20px rgba(16, 185, 129, 0.2)',
        display: 'inline-block'
      }}>
        <svg width="140" height="140" viewBox={`0 0 ${size} ${size}`}>
          {matrix.map((row, r) =>
            row.map((cell, c) => (
              <rect
                key={`${r}-${c}`}
                x={c}
                y={r}
                width="1"
                height="1"
                fill={cell ? '#0a0f1d' : '#ffffff'}
              />
            ))
          )}
        </svg>
      </div>

      <div style={{ textAlign: 'center', width: '100%' }}>
        <p className="mono" style={{ fontSize: '0.75rem', color: '#94a3b8', wordBreak: 'break-all', marginBottom: '8px' }}>
          {qrString || `revolt://passport/${batteryId}`}
        </p>
        <button
          onClick={handleCopy}
          className="btn btn-outline"
          style={{ fontSize: '0.75rem', padding: '4px 10px' }}
        >
          {copied ? <Check size={14} color="#10b981" /> : <Copy size={14} />}
          {copied ? 'Copied QR Payload!' : 'Copy QR Payload'}
        </button>
      </div>
    </div>
  );
}

