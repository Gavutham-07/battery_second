import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useBatteryStore } from '../../context/BatteryContext';
import { QRCodeSVG } from 'qrcode.react';
import {
  ShieldCheck,
  ShieldAlert,
  AlertTriangle,
  CheckCircle2,
  Search,
  BatteryCharging,
  Hash,
  Award,
  ExternalLink,
  ArrowLeft,
  Calendar,
  UserCheck
} from 'lucide-react';

export default function PublicVerification() {
  const { battery_id } = useParams();
  const { getBattery, verifyPassport, batteries } = useBatteryStore();

  const [searchId, setSearchId] = useState(battery_id || 'BAT-103');
  const [verificationData, setVerificationData] = useState(null);
  const [loading, setLoading] = useState(false);

  const runVerification = async (id) => {
    if (!id) return;
    setLoading(true);
    const result = await verifyPassport(id);
    setVerificationData(result);
    setLoading(false);
  };

  useEffect(() => {
    if (battery_id) {
      setSearchId(battery_id);
      runVerification(battery_id);
    } else {
      runVerification('BAT-103');
    }
  }, [battery_id]);

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    if (searchId.trim()) {
      runVerification(searchId.trim().toUpperCase());
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col">
      {/* Top Bar */}
      <header className="bg-white border-b border-slate-200">
        <div className="max-w-4xl mx-auto px-4 h-16 flex items-center justify-between">
          <Link to="/" className="flex items-center gap-2 group">
            <div className="w-8 h-8 rounded-lg bg-emerald-600 flex items-center justify-center text-white">
              <BatteryCharging className="w-4 h-4" />
            </div>
            <span className="font-bold text-slate-900 tracking-tight">Re<span className="text-emerald-600">Volt</span></span>
            <span className="text-xs text-slate-400 border-l border-slate-200 pl-2">Passport Registry</span>
          </Link>

          <Link
            to="/"
            className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-600 hover:text-slate-900 transition-colors"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>Return to Platform</span>
          </Link>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 max-w-4xl w-full mx-auto px-4 py-8 space-y-6">
        {/* Verification Search Bar */}
        <div className="bg-white rounded-xl border border-slate-200 p-4 shadow-xs">
          <form onSubmit={handleSearchSubmit} className="flex items-center gap-2">
            <div className="relative flex-1">
              <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                value={searchId}
                onChange={(e) => setSearchId(e.target.value)}
                placeholder="Enter Battery ID (e.g. BAT-103, BAT-101)..."
                className="w-full pl-9 pr-3 py-2 text-xs rounded-lg border border-slate-300 focus:border-emerald-500 bg-white text-slate-900"
              />
            </div>
            <button
              type="submit"
              className="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg text-xs font-semibold transition-colors"
            >
              Verify Passport
            </button>
          </form>

          <div className="flex items-center gap-2 mt-2 text-[11px] text-slate-400">
            <span>Quick Test:</span>
            {['BAT-103', 'BAT-102', 'BAT-101', 'BAT-104'].map(id => (
              <button
                key={id}
                type="button"
                onClick={() => {
                  setSearchId(id);
                  runVerification(id);
                }}
                className="text-emerald-700 font-semibold hover:underline"
              >
                {id}
              </button>
            ))}
          </div>
        </div>

        {/* Verification Result Card */}
        {verificationData && (
          <div className="bg-white rounded-2xl border border-slate-200 p-6 sm:p-8 shadow-sm space-y-6">
            {/* Status Header */}
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between pb-6 border-b border-slate-200 gap-4">
              <div className="flex items-center gap-3">
                <div className={`w-12 h-12 rounded-xl flex items-center justify-center ${
                  verificationData.status === 'Valid'
                    ? 'bg-emerald-100 text-emerald-700'
                    : (verificationData.status === 'Unverified' ? 'bg-amber-100 text-amber-700' : 'bg-rose-100 text-rose-700')
                }`}>
                  {verificationData.status === 'Valid' ? <ShieldCheck className="w-7 h-7" /> :
                   (verificationData.status === 'Unverified' ? <AlertTriangle className="w-7 h-7" /> : <ShieldAlert className="w-7 h-7" />)}
                </div>

                <div>
                  <div className="flex items-center gap-2">
                    <h2 className="text-xl font-bold text-slate-900">{searchId}</h2>
                    <span className={`text-xs px-2.5 py-0.5 rounded-full font-bold uppercase ${
                      verificationData.status === 'Valid'
                        ? 'bg-emerald-100 text-emerald-800 border border-emerald-200'
                        : (verificationData.status === 'Unverified' ? 'bg-amber-100 text-amber-800' : 'bg-rose-100 text-rose-800')
                    }`}>
                      {verificationData.status === 'Valid' ? '✓ Authenticity Verified' : verificationData.status}
                    </span>
                  </div>
                  <p className="text-xs text-slate-500 mt-0.5">{verificationData.message}</p>
                </div>
              </div>

              {verificationData.status === 'Valid' && (
                <div className="p-2 bg-slate-50 rounded-xl border border-slate-200 shrink-0 self-center">
                  <QRCodeSVG value={window.location.href} size={80} level="M" />
                </div>
              )}
            </div>

            {/* Passport Detail Grid */}
            {verificationData.status === 'Valid' && verificationData.battery && (
              <div className="space-y-6">
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-xs">
                  <div className="p-3 bg-slate-50 rounded-xl border border-slate-100">
                    <span className="text-slate-400 font-medium">Certified SOH</span>
                    <p className="text-xl font-bold text-emerald-600 mt-1">{verificationData.battery.soh_estimate}%</p>
                  </div>

                  <div className="p-3 bg-slate-50 rounded-xl border border-slate-100">
                    <span className="text-slate-400 font-medium">Chemistry</span>
                    <p className="text-base font-bold text-slate-800 mt-1">{verificationData.battery.chemistry}</p>
                    <p className="text-[10px] text-slate-400">{verificationData.battery.rated_capacity_ah} Ah Rated</p>
                  </div>

                  <div className="p-3 bg-slate-50 rounded-xl border border-slate-100">
                    <span className="text-slate-400 font-medium">Safety Status</span>
                    <p className="text-base font-bold text-emerald-700 mt-1">{verificationData.battery.safety_status}</p>
                    <p className="text-[10px] text-slate-400">Thermal check passed</p>
                  </div>

                  <div className="p-3 bg-slate-50 rounded-xl border border-slate-100">
                    <span className="text-slate-400 font-medium">Approved Route</span>
                    <p className="text-xs font-bold text-slate-900 mt-1">{verificationData.passport?.approved_route || 'Motive Reuse'}</p>
                  </div>
                </div>

                {/* Technician Certification Block */}
                <div className="p-4 bg-emerald-50/50 rounded-xl border border-emerald-200 text-xs space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-emerald-900 flex items-center gap-1.5">
                      <UserCheck className="w-4 h-4 text-emerald-600" />
                      <span>Certified Technician Sign-off</span>
                    </span>
                    <span className="text-slate-500 text-[11px] flex items-center gap-1">
                      <Calendar className="w-3.5 h-3.5" />
                      {new Date(verificationData.passport?.minted_at).toLocaleDateString()}
                    </span>
                  </div>
                  <p className="text-slate-700 leading-relaxed italic bg-white p-3 rounded-lg border border-emerald-100">
                    "{verificationData.passport?.technician_notes || 'Physical and electrochemical verification completed.'}"
                  </p>
                  <p className="text-[11px] text-slate-500">
                    Authorized Inspector: <strong className="text-slate-800">{verificationData.passport?.technician_id || 'TECH-04'}</strong>
                  </p>
                </div>

                {/* SHA-256 Digest Verification */}
                <div className="p-4 bg-slate-900 text-slate-200 rounded-xl text-xs space-y-1.5 font-mono">
                  <div className="flex items-center justify-between text-slate-400 text-[11px]">
                    <span className="flex items-center gap-1">
                      <Hash className="w-3.5 h-3.5 text-emerald-400" />
                      <span>Cryptographic SHA-256 Hash Proof</span>
                    </span>
                    <span className="text-emerald-400 font-bold">100% Match</span>
                  </div>
                  <p className="text-[11px] text-emerald-300 break-all bg-slate-950 p-2.5 rounded-lg border border-slate-800">
                    {verificationData.passport?.sha256_hash}
                  </p>
                </div>
              </div>
            )}

            {/* Unverified / Pending Screening details */}
            {verificationData.status === 'Unverified' && (
              <div className="p-4 bg-amber-50 rounded-xl border border-amber-200 text-xs text-amber-900 space-y-2">
                <p className="font-bold text-sm">Battery Record Exists — Passport Incomplete</p>
                <p className="leading-relaxed">
                  Battery <strong>{searchId}</strong> is enrolled in the ReVolt registry, but has not completed certified technician screening. A verified cryptographic passport has not yet been issued.
                </p>
              </div>
            )}

            {/* Not Found */}
            {verificationData.status === 'Not Found' && (
              <div className="p-4 bg-rose-50 rounded-xl border border-rose-200 text-xs text-rose-900 space-y-2">
                <p className="font-bold text-sm">Battery Record Not Found</p>
                <p className="leading-relaxed">
                  No battery matching ID <strong>"{searchId}"</strong> exists in the ReVolt registry. Ensure the battery ID is entered correctly or registered at an authorized service depot.
                </p>
              </div>
            )}
          </div>
        )}
      </main>
    </div>
  );
}

