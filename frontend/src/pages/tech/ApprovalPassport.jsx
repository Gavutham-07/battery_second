import React, { useState } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { QRCodeSVG } from 'qrcode.react';
import { useBatteryStore } from '../../context/BatteryContext';
import {
  ShieldCheck,
  CheckCircle2,
  AlertTriangle,
  QrCode,
  Download,
  Printer,
  FileCheck,
  Hash,
  ArrowRight,
  ExternalLink,
  Award
} from 'lucide-react';
import { Link } from 'react-router-dom';

export default function ApprovalPassport() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { batteries, approveAndMintPassport, getBattery } = useBatteryStore();

  const initialId = searchParams.get('battery_id') || batteries.find(b => b.status === 'Assessed')?.battery_id || batteries[0]?.battery_id;
  const [selectedBatteryId, setSelectedBatteryId] = useState(initialId);

  const currentBattery = getBattery(selectedBatteryId) || batteries[0];

  const [technicianNotes, setTechnicianNotes] = useState(
    'Cell visual inspection passed. Busbar terminals intact. Electrochemical impedance within nominal parameters.'
  );
  const [approvedRoute, setApprovedRoute] = useState(
    currentBattery?.recommended_action === 'Direct Reuse'
      ? 'E-Rickshaw / Light EV'
      : (currentBattery?.recommended_action === 'Recycle' ? 'Material Recovery (Recycling)' : 'Home Solar Storage')
  );

  const [isMinting, setIsMinting] = useState(false);
  const [mintSuccess, setMintSuccess] = useState('');
  const [mintError, setMintError] = useState('');

  const isAssessed = currentBattery?.status === 'Assessed' || currentBattery?.status === 'Approved';
  const passport = currentBattery?.passport;

  const handleMint = async (e) => {
    e.preventDefault();
    setMintSuccess('');
    setMintError('');
    setIsMinting(true);

    try {
      const res = await approveAndMintPassport(
        currentBattery.battery_id,
        technicianNotes,
        approvedRoute,
        'TECH-BLR-02'
      );

      if (res.success) {
        setMintSuccess(`Digital Battery Passport successfully minted for ${currentBattery.battery_id}! Cryptographic SHA-256 hash registered.`);
      } else {
        setMintError(res.message || 'Failed to approve battery');
      }
    } catch (err) {
      setMintError('Unexpected error during passport minting');
    } finally {
      setIsMinting(false);
    }
  };

  const getVerificationUrl = (id) => {
    return `${window.location.origin}/verify/${id}`;
  };

  return (
    <div className="space-y-6">
      {/* Header & Battery Selector */}
      <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-xs flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-slate-900">Technician Approval & QR Passport Minting</h1>
          <p className="text-xs text-slate-500 mt-1">
            Review electrochemical diagnostic findings, assign certified secondary application, and generate a tamper-evident SHA-256 QR passport.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <label className="text-xs font-semibold text-slate-600">Select Battery:</label>
          <select
            value={selectedBatteryId}
            onChange={(e) => {
              setSelectedBatteryId(e.target.value);
              setMintSuccess('');
              setMintError('');
            }}
            className="text-xs font-bold px-3 py-1.5 rounded-lg border border-slate-300 bg-white focus:border-emerald-500"
          >
            {batteries.map((b) => (
              <option key={b.battery_id} value={b.battery_id}>
                {b.battery_id} ({b.status} • {b.chemistry})
              </option>
            ))}
          </select>
        </div>
      </div>

      {mintSuccess && (
        <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-xl flex items-center justify-between text-xs text-emerald-800">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
            <span>{mintSuccess}</span>
          </div>
          <button onClick={() => setMintSuccess('')} className="text-emerald-700 font-bold ml-2">✕</button>
        </div>
      )}

      {mintError && (
        <div className="p-4 bg-rose-50 border border-rose-200 rounded-xl flex items-center justify-between text-xs text-rose-800">
          <div className="flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-rose-600 shrink-0" />
            <span>{mintError}</span>
          </div>
          <button onClick={() => setMintError('')} className="text-rose-700 font-bold ml-2">✕</button>
        </div>
      )}

      {!isAssessed ? (
        <div className="p-8 bg-amber-50 rounded-2xl border border-amber-200 text-center space-y-3">
          <div className="w-12 h-12 rounded-full bg-amber-100 text-amber-700 flex items-center justify-center mx-auto">
            <AlertTriangle className="w-6 h-6" />
          </div>
          <h3 className="font-bold text-base text-amber-900">Physical Screening Required Prior to Minting</h3>
          <p className="text-xs text-amber-800 max-w-lg mx-auto">
            Battery <span className="font-bold">{currentBattery?.battery_id}</span> has not yet completed the 90-second electrochemical screening test. A digital passport cannot be minted on unverified hardware telemetry.
          </p>
          <button
            onClick={() => navigate(`/tech/screening?battery_id=${currentBattery?.battery_id}`)}
            className="mt-2 px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg text-xs font-semibold shadow-xs"
          >
            Launch Screening for {currentBattery?.battery_id}
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Diagnostic Assessment Summary Card */}
          <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-xs space-y-5">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <span className="text-xs font-bold uppercase tracking-wider text-slate-800">Assessment Summary</span>
              <span className="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-slate-100 text-slate-700">
                {currentBattery.battery_id}
              </span>
            </div>

            <div className="grid grid-cols-2 gap-3 text-xs">
              <div className="p-3 bg-slate-50 rounded-xl border border-slate-100">
                <span className="text-slate-400">Assessed SOH:</span>
                <p className={`text-2xl font-bold mt-0.5 ${
                  currentBattery.soh_estimate >= 80 ? 'text-emerald-600' :
                  (currentBattery.soh_estimate >= 60 ? 'text-amber-600' : 'text-rose-600')
                }`}>
                  {currentBattery.soh_estimate}%
                </p>
              </div>

              <div className="p-3 bg-slate-50 rounded-xl border border-slate-100">
                <span className="text-slate-400">Safety Classification:</span>
                <p className={`text-base font-bold mt-1 flex items-center gap-1 ${
                  currentBattery.safety_status === 'Critical Danger' ? 'text-rose-600' : 'text-emerald-700'
                }`}>
                  {currentBattery.safety_status}
                </p>
              </div>

              <div className="p-3 bg-slate-50 rounded-xl border border-slate-100">
                <span className="text-slate-400">AI Recommended Action:</span>
                <p className="font-bold text-slate-900 mt-1">{currentBattery.recommended_action}</p>
              </div>

              <div className="p-3 bg-slate-50 rounded-xl border border-slate-100">
                <span className="text-slate-400">Exchange Buyback Credit:</span>
                <p className="font-bold text-emerald-600 mt-1">₹{currentBattery.exchange_credit_inr?.toLocaleString()}</p>
              </div>
            </div>

            <div className="p-3 bg-slate-50 rounded-xl border border-slate-200 text-xs text-slate-700 space-y-1">
              <p className="font-semibold text-slate-900">AI Diagnostic Justification:</p>
              <p className="text-[11px] leading-relaxed text-slate-600">{currentBattery.plain_english_explanation}</p>
            </div>

            {/* Approval Form */}
            <form onSubmit={handleMint} className="space-y-4 pt-2">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Assign Approved Second-Life Application <span className="text-rose-500">*</span>
                </label>
                <select
                  value={approvedRoute}
                  onChange={(e) => setApprovedRoute(e.target.value)}
                  disabled={currentBattery.safety_status === 'Critical Danger'}
                  className="w-full text-xs px-3 py-2 rounded-lg border border-slate-300 focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 bg-white"
                >
                  <option value="Home Solar Storage">Home Solar Storage (Stationary ESS)</option>
                  <option value="E-Rickshaw / Light EV">E-Rickshaw / Light EV (Motive Repower)</option>
                  <option value="UPS / Telecom Backup">UPS / Telecom Tower Backup</option>
                  <option value="Solar Streetlight">Solar Streetlight Micro-Storage</option>
                  <option value="Material Recovery (Recycling)">Material Recovery (Hydrometallurgical Recycling)</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Technician Diagnostic Sign-off Notes
                </label>
                <textarea
                  rows="3"
                  value={technicianNotes}
                  onChange={(e) => setTechnicianNotes(e.target.value)}
                  className="w-full text-xs px-3 py-2 rounded-lg border border-slate-300 focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500"
                />
              </div>

              <button
                type="submit"
                disabled={isMinting}
                className="w-full py-2.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg text-xs font-semibold shadow-xs transition-colors flex items-center justify-center gap-2"
              >
                <FileCheck className="w-4 h-4" />
                <span>{passport ? 'Re-Mint Updated Passport' : 'Approve & Mint QR Battery Passport'}</span>
              </button>
            </form>
          </div>

          {/* Minted Passport Preview */}
          <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-xs flex flex-col justify-between">
            {passport ? (
              <div className="space-y-4">
                <div className="flex items-center justify-between pb-3 border-b border-slate-100">
                  <span className="text-xs font-bold text-emerald-700 uppercase tracking-wider flex items-center gap-1.5">
                    <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                    <span>Minted Digital Passport</span>
                  </span>
                  <span className="text-[11px] font-mono text-slate-400">{passport.passport_id}</span>
                </div>

                <div className="flex flex-col items-center justify-center p-4 bg-slate-50 rounded-2xl border border-slate-200 text-center">
                  <div className="p-3 bg-white rounded-xl shadow-xs border border-slate-200">
                    <QRCodeSVG
                      value={getVerificationUrl(currentBattery.battery_id)}
                      size={140}
                      level="H"
                      includeMargin={true}
                    />
                  </div>
                  <p className="text-[11px] font-semibold text-slate-800 mt-2">Scan with Smartphone or Scanner</p>
                  <Link
                    to={`/verify/${currentBattery.battery_id}`}
                    target="_blank"
                    className="text-[11px] font-semibold text-emerald-600 hover:text-emerald-700 underline flex items-center gap-1 mt-1"
                  >
                    <span>Inspect Public Verification Page</span>
                    <ExternalLink className="w-3 h-3" />
                  </Link>
                </div>

                <div className="p-3 bg-slate-900 text-slate-200 rounded-xl text-xs space-y-1 font-mono">
                  <div className="flex items-center justify-between text-slate-400 text-[10px]">
                    <span className="flex items-center gap-1">
                      <Hash className="w-3 h-3 text-emerald-400" />
                      <span>SHA-256 Checksum</span>
                    </span>
                    <span className="text-emerald-400">Verified</span>
                  </div>
                  <p className="text-[10px] text-emerald-300 break-all bg-slate-950 p-2 rounded border border-slate-800">
                    {passport.sha256_hash}
                  </p>
                </div>

                <div className="text-xs text-slate-600 space-y-1 bg-slate-50 p-3 rounded-lg border border-slate-100">
                  <p><strong className="text-slate-800">Approved Route:</strong> {passport.approved_route}</p>
                  <p><strong className="text-slate-800">Technician:</strong> {passport.technician_id}</p>
                  <p><strong className="text-slate-800">Minted:</strong> {new Date(passport.minted_at).toLocaleString()}</p>
                </div>
              </div>
            ) : (
              <div className="h-full flex flex-col items-center justify-center text-center p-8 space-y-3">
                <div className="w-16 h-16 rounded-2xl bg-slate-100 text-slate-400 flex items-center justify-center">
                  <QrCode className="w-8 h-8" />
                </div>
                <h3 className="font-bold text-sm text-slate-800">Passport Ready for Minting</h3>
                <p className="text-xs text-slate-500 max-w-xs">
                  Fill in the technician sign-off notes on the left and click "Approve & Mint QR Battery Passport" to generate the immutable cryptographic record.
                </p>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

