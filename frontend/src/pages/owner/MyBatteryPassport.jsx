import React, { useState } from 'react';
import { QRCodeSVG } from 'qrcode.react';
import { useBatteryStore } from '../../context/BatteryContext';
import { QrCode, ShieldCheck, Download, Printer, CheckCircle, Clock, ExternalLink, Hash, Award } from 'lucide-react';
import { Link } from 'react-router-dom';

export default function MyBatteryPassport() {
  const { batteries } = useBatteryStore();

  const approvedBatteries = batteries.filter(b => b.passport);
  const [selectedId, setSelectedId] = useState(() => {
    return approvedBatteries[0]?.battery_id || batteries[0]?.battery_id || '';
  });

  const battery = batteries.find(b => b.battery_id === selectedId) || batteries[0];
  const passport = battery?.passport;

  const handlePrint = () => {
    window.print();
  };

  const getVerificationUrl = (id) => {
    return `${window.location.origin}/verify/${id}`;
  };

  return (
    <div className="space-y-6">
      {/* Header & Battery Selector */}
      <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-xs flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-slate-900">My Battery Passport</h1>
          <p className="text-xs text-slate-500 mt-1">
            Digitally minted Battery Passports backed by cryptographic SHA-256 hash integrity.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <label className="text-xs font-semibold text-slate-600">Select Battery:</label>
          <select
            value={selectedId}
            onChange={(e) => setSelectedId(e.target.value)}
            className="text-xs font-semibold px-3 py-1.5 rounded-lg border border-slate-300 bg-white text-slate-900 focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500"
          >
            {batteries.map((b) => (
              <option key={b.battery_id} value={b.battery_id}>
                {b.battery_id} {b.passport ? '(Minted Passport)' : '(Pending Approval)'}
              </option>
            ))}
          </select>
        </div>
      </div>

      {!passport ? (
        <div className="p-8 bg-amber-50 rounded-2xl border border-amber-200 text-center space-y-3">
          <div className="w-12 h-12 rounded-full bg-amber-100 text-amber-700 flex items-center justify-center mx-auto">
            <Clock className="w-6 h-6" />
          </div>
          <h3 className="font-bold text-base text-amber-900">Passport Not Yet Minted</h3>
          <p className="text-xs text-amber-800 max-w-lg mx-auto leading-relaxed">
            Battery <span className="font-bold">{battery?.battery_id}</span> is currently in status <strong className="underline">{battery?.status}</strong>. Battery passports are officially minted only after a technician completes physical screening and registers cryptographic sign-off.
          </p>
        </div>
      ) : (
        <div className="bg-white rounded-2xl border border-slate-200 p-6 sm:p-8 shadow-sm space-y-6 max-w-3xl mx-auto print:border-none print:shadow-none">
          {/* Certificate Header */}
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between pb-6 border-b border-slate-200 gap-4">
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 rounded-xl bg-emerald-600 text-white flex items-center justify-center shadow-xs">
                <Award className="w-7 h-7" />
              </div>
              <div>
                <span className="text-[11px] font-bold text-emerald-700 uppercase tracking-widest bg-emerald-50 px-2.5 py-0.5 rounded-full border border-emerald-200">
                  Certified Battery Passport
                </span>
                <h2 className="text-xl font-extrabold text-slate-900 mt-1">ReVolt Digital Circular Passport</h2>
              </div>
            </div>

            <div className="flex items-center gap-2 print:hidden">
              <button
                onClick={handlePrint}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg text-xs font-semibold border border-slate-300 transition-colors"
              >
                <Printer className="w-4 h-4" />
                <span>Print / Save PDF</span>
              </button>
            </div>
          </div>

          {/* QR Code and Primary Attributes */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-6 items-center">
            <div className="flex flex-col items-center justify-center p-4 bg-slate-50 rounded-2xl border border-slate-200 text-center">
              <div className="p-3 bg-white rounded-xl shadow-xs border border-slate-200">
                <QRCodeSVG
                  value={getVerificationUrl(battery.battery_id)}
                  size={150}
                  level="H"
                  includeMargin={true}
                />
              </div>
              <p className="text-[10px] text-slate-500 mt-2 font-medium">Scan to verify public authenticity</p>
              <Link
                to={`/verify/${battery.battery_id}`}
                className="mt-2 text-[11px] font-semibold text-emerald-600 hover:text-emerald-700 flex items-center gap-1 underline"
              >
                <span>Open Public Verification</span>
                <ExternalLink className="w-3 h-3" />
              </Link>
            </div>

            <div className="sm:col-span-2 space-y-3">
              <div className="grid grid-cols-2 gap-3 text-xs">
                <div className="p-3 bg-slate-50 rounded-xl border border-slate-100">
                  <span className="text-slate-400 font-medium">Battery Identifier</span>
                  <p className="text-base font-bold text-slate-900 mt-0.5">{battery.battery_id}</p>
                </div>

                <div className="p-3 bg-slate-50 rounded-xl border border-slate-100">
                  <span className="text-slate-400 font-medium">Chemistry</span>
                  <p className="text-base font-bold text-slate-900 mt-0.5">{battery.chemistry} ({battery.rated_capacity_ah} Ah)</p>
                </div>

                <div className="p-3 bg-slate-50 rounded-xl border border-slate-100">
                  <span className="text-slate-400 font-medium">Certified SOH</span>
                  <p className="text-base font-bold text-emerald-600 mt-0.5">{battery.soh_estimate}%</p>
                </div>

                <div className="p-3 bg-slate-50 rounded-xl border border-slate-100">
                  <span className="text-slate-400 font-medium">Safety Verification</span>
                  <p className="text-base font-bold text-emerald-700 mt-0.5 flex items-center gap-1">
                    <ShieldCheck className="w-4 h-4 text-emerald-600" />
                    <span>{battery.safety_status}</span>
                  </p>
                </div>
              </div>

              <div className="p-3 bg-emerald-50/60 rounded-xl border border-emerald-200 text-xs">
                <span className="text-emerald-800 font-bold">Approved Second-Life Route:</span>
                <p className="text-sm font-extrabold text-slate-900 mt-0.5">{passport.approved_route}</p>
                <p className="text-[11px] text-slate-600 mt-1">Technician ID: {passport.technician_id} • Minted: {new Date(passport.minted_at).toLocaleString()}</p>
              </div>
            </div>
          </div>

          {/* SHA-256 Hash Integrity Block */}
          <div className="p-4 bg-slate-900 text-slate-200 rounded-xl text-xs space-y-1.5 font-mono">
            <div className="flex items-center justify-between text-slate-400 text-[11px]">
              <span className="flex items-center gap-1">
                <Hash className="w-3.5 h-3.5 text-emerald-400" />
                <span>Cryptographic SHA-256 Immutable Digest</span>
              </span>
              <span className="text-emerald-400 font-semibold">Integrity Verified</span>
            </div>
            <p className="text-[11px] text-emerald-300 break-all bg-slate-950 p-2.5 rounded-lg border border-slate-800">
              {passport.sha256_hash}
            </p>
            <p className="text-[10px] text-slate-400 font-sans mt-1">
              Tamper-evident record registered across the second-life exchange network.
            </p>
          </div>
        </div>
      )}
    </div>
  );
}

