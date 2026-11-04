import React, { useState } from 'react';
import { useBatteryStore } from '../../context/BatteryContext';
import { Sparkles, ShieldCheck, ShieldAlert, CheckCircle2, AlertTriangle, ArrowRight, Sun, Car, Zap, Lightbulb } from 'lucide-react';

export default function Recommendations() {
  const { batteries, updateOwnerPreference } = useBatteryStore();

  // Pick first battery or allow dropdown switch
  const [selectedBatteryId, setSelectedBatteryId] = useState(() => {
    return batteries[0]?.battery_id || '';
  });

  const [preferenceSaved, setPreferenceSaved] = useState('');
  const [preferenceError, setPreferenceError] = useState('');

  const currentBattery = batteries.find(b => b.battery_id === selectedBatteryId) || batteries[0];

  const handlePreferenceSelect = (pref) => {
    setPreferenceSaved('');
    setPreferenceError('');

    if (!currentBattery) return;

    const res = updateOwnerPreference(currentBattery.battery_id, pref);
    if (res.success) {
      setPreferenceSaved(`Your preference "${pref}" has been recorded alongside the technical recommendation!`);
    } else {
      setPreferenceError(res.message);
    }
  };

  const getAppIcon = (name) => {
    switch (name) {
      case 'Home Solar Storage':
        return <Sun className="w-5 h-5 text-amber-500" />;
      case 'E-Rickshaw / Light EV':
        return <Car className="w-5 h-5 text-blue-500" />;
      case 'UPS / Telecom Backup':
        return <Zap className="w-5 h-5 text-purple-500" />;
      case 'Solar Streetlight':
      default:
        return <Lightbulb className="w-5 h-5 text-emerald-500" />;
    }
  };

  return (
    <div className="space-y-6">
      {/* Page Header + Battery Selector */}
      <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-xs flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-slate-900">Second-Life Recommendations & Owner Preferences</h1>
          <p className="text-xs text-slate-500 mt-1">
            Review AI electrochemical suitability and submit your second-life preference (Reuse, Repurpose, or Sell/Exchange).
          </p>
        </div>

        <div className="flex items-center gap-2">
          <label className="text-xs font-semibold text-slate-600 whitespace-nowrap">Selected Battery:</label>
          <select
            value={selectedBatteryId}
            onChange={(e) => {
              setSelectedBatteryId(e.target.value);
              setPreferenceSaved('');
              setPreferenceError('');
            }}
            className="text-xs font-semibold px-3 py-1.5 rounded-lg border border-slate-300 bg-white focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500"
          >
            {batteries.map((b) => (
              <option key={b.battery_id} value={b.battery_id}>
                {b.battery_id} ({b.status})
              </option>
            ))}
          </select>
        </div>
      </div>

      {preferenceSaved && (
        <div className="p-3 bg-emerald-50 border border-emerald-200 rounded-xl flex items-center justify-between text-xs text-emerald-800">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
            <span>{preferenceSaved}</span>
          </div>
          <button onClick={() => setPreferenceSaved('')} className="text-emerald-700 font-bold ml-2">✕</button>
        </div>
      )}

      {preferenceError && (
        <div className="p-3 bg-rose-50 border border-rose-200 rounded-xl flex items-center justify-between text-xs text-rose-800">
          <div className="flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-rose-600 shrink-0" />
            <span>{preferenceError}</span>
          </div>
          <button onClick={() => setPreferenceError('')} className="text-rose-700 font-bold ml-2">✕</button>
        </div>
      )}

      {/* Battery Diagnostic Status Alert */}
      {!currentBattery || currentBattery.status === 'Awaiting Screening' ? (
        <div className="p-6 bg-amber-50 rounded-xl border border-amber-200 text-center space-y-2">
          <div className="w-10 h-10 rounded-full bg-amber-100 text-amber-700 flex items-center justify-center mx-auto">
            <Sparkles className="w-5 h-5" />
          </div>
          <h3 className="font-bold text-sm text-amber-900">Preliminary Guidance Only — Screening Pending</h3>
          <p className="text-xs text-amber-800 max-w-xl mx-auto">
            Battery <span className="font-bold">{currentBattery?.battery_id}</span> is awaiting physical 90-second electrochemical screening at a certified service center. Confirmed second-life application matchmaker requires verified sensor telemetry.
          </p>
        </div>
      ) : (
        <>
          {/* Dual Recommendation vs Preference Comparison Header */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="p-4 bg-emerald-50/60 rounded-xl border border-emerald-200 shadow-xs">
              <span className="text-[11px] font-bold uppercase tracking-wider text-emerald-700">
                1. AI Technical Assessment
              </span>
              <p className="text-lg font-extrabold text-slate-900 mt-1">
                {currentBattery.recommended_action || 'Pending'}
              </p>
              <p className="text-xs text-slate-600 mt-1">
                Based on measured SOH ({currentBattery.soh_estimate}%) and safety classification ({currentBattery.safety_status}).
              </p>
            </div>

            <div className="p-4 bg-blue-50/60 rounded-xl border border-blue-200 shadow-xs">
              <span className="text-[11px] font-bold uppercase tracking-wider text-blue-700">
                2. EV Owner Stored Preference
              </span>
              <p className="text-lg font-extrabold text-slate-900 mt-1">
                {currentBattery.owner_preference || 'No Preference Selected Yet'}
              </p>
              <p className="text-xs text-slate-600 mt-1">
                Stored separately in database — does not override AI technical recommendation or safety limits.
              </p>
            </div>
          </div>

          {/* Critical Safety Notice if Unsafe */}
          {currentBattery.safety_status === 'Critical Danger' && (
            <div className="p-4 bg-rose-50 border border-rose-300 rounded-xl text-xs text-rose-900 flex items-start gap-3">
              <ShieldAlert className="w-5 h-5 text-rose-600 shrink-0 mt-0.5" />
              <div>
                <p className="font-bold text-sm text-rose-950">Safety Lockout Active</p>
                <p className="mt-1 text-rose-800 leading-relaxed">
                  Thermal runaway or severe electrochemical degradation detected during screening. To safeguard public and residential safety, Reuse and Repurposing are strictly prohibited for this pack. This unit is scheduled for certified hydrometallurgical recycling.
                </p>
              </div>
            </div>
          )}

          {/* Second Life Applications Grid */}
          <div>
            <h2 className="text-sm font-bold text-slate-900 mb-3">AI Application Matchmaker (Ranked by Suitability)</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {currentBattery.second_life_matches?.map((app, idx) => (
                <div key={idx} className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs flex flex-col justify-between">
                  <div>
                    <div className="flex items-start justify-between gap-3 mb-2">
                      <div className="flex items-center gap-2.5">
                        <div className="p-2 rounded-lg bg-slate-100 border border-slate-200">
                          {getAppIcon(app.application)}
                        </div>
                        <div>
                          <h3 className="font-bold text-sm text-slate-900">{app.application}</h3>
                          <span className={`text-[10px] font-bold px-2 py-0.5 rounded ${
                            app.suitability === 'Optimal' ? 'bg-emerald-100 text-emerald-800' :
                            (app.suitability === 'Good' ? 'bg-blue-100 text-blue-800' :
                            (app.suitability === 'Prohibited' ? 'bg-rose-100 text-rose-800' : 'bg-slate-100 text-slate-700'))
                          }`}>
                            {app.suitability}
                          </span>
                        </div>
                      </div>

                      <div className="text-right">
                        <span className="text-[10px] text-slate-400">Projected RUL:</span>
                        <p className="text-sm font-bold text-slate-800">{app.predicted_lifetime_years} yrs</p>
                      </div>
                    </div>

                    <p className="text-xs text-slate-600 mt-3 leading-relaxed bg-slate-50 p-2.5 rounded-lg border border-slate-100">
                      {app.reason}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Owner Preference Selection Control */}
          <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-xs space-y-4">
            <div>
              <h2 className="text-sm font-bold text-slate-900">Submit Your Second-Life Intent</h2>
              <p className="text-xs text-slate-500 mt-0.5">
                Express how you would like ReVolt to process your battery pack.
              </p>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              <button
                type="button"
                disabled={currentBattery.safety_status === 'Critical Danger'}
                onClick={() => handlePreferenceSelect('Reuse')}
                className={`p-4 rounded-xl border text-left transition-all ${
                  currentBattery.safety_status === 'Critical Danger'
                    ? 'opacity-40 cursor-not-allowed bg-slate-50 border-slate-200'
                    : (currentBattery.owner_preference === 'Reuse'
                        ? 'border-emerald-600 bg-emerald-50/60 ring-2 ring-emerald-500/20'
                        : 'border-slate-200 bg-white hover:bg-slate-50')
                }`}
              >
                <div className="flex items-center justify-between mb-1">
                  <span className="font-bold text-sm text-slate-900">Direct Reuse</span>
                  {currentBattery.owner_preference === 'Reuse' && <CheckCircle2 className="w-4 h-4 text-emerald-600" />}
                </div>
                <p className="text-[11px] text-slate-500">
                  Repower light electric mobility (E-Rickshaw / fleet vehicle) if cell metrics permit.
                </p>
              </button>

              <button
                type="button"
                disabled={currentBattery.safety_status === 'Critical Danger'}
                onClick={() => handlePreferenceSelect('Repurpose')}
                className={`p-4 rounded-xl border text-left transition-all ${
                  currentBattery.safety_status === 'Critical Danger'
                    ? 'opacity-40 cursor-not-allowed bg-slate-50 border-slate-200'
                    : (currentBattery.owner_preference === 'Repurpose'
                        ? 'border-emerald-600 bg-emerald-50/60 ring-2 ring-emerald-500/20'
                        : 'border-slate-200 bg-white hover:bg-slate-50')
                }`}
              >
                <div className="flex items-center justify-between mb-1">
                  <span className="font-bold text-sm text-slate-900">Repurpose</span>
                  {currentBattery.owner_preference === 'Repurpose' && <CheckCircle2 className="w-4 h-4 text-emerald-600" />}
                </div>
                <p className="text-[11px] text-slate-500">
                  Deploy in stationary clean-energy storage (Home Solar, UPS, Telecom tower).
                </p>
              </button>

              <button
                type="button"
                onClick={() => handlePreferenceSelect('Sell / Exchange')}
                className={`p-4 rounded-xl border text-left transition-all ${
                  currentBattery.owner_preference === 'Sell / Exchange'
                    ? 'border-emerald-600 bg-emerald-50/60 ring-2 ring-emerald-500/20'
                    : 'border-slate-200 bg-white hover:bg-slate-50'
                }`}
              >
                <div className="flex items-center justify-between mb-1">
                  <span className="font-bold text-sm text-slate-900">Sell / Exchange</span>
                  {currentBattery.owner_preference === 'Sell / Exchange' && <CheckCircle2 className="w-4 h-4 text-emerald-600" />}
                </div>
                <p className="text-[11px] text-slate-500">
                  Claim immediate buyback exchange credit (₹{currentBattery.exchange_credit_inr?.toLocaleString() || '25,000'}) towards an upgraded battery.
                </p>
              </button>
            </div>

            <div className="p-3 bg-slate-50 rounded-lg text-[11px] text-slate-500 border border-slate-200">
              <strong>Notice to Owners:</strong> Selecting "Reuse" expresses intent and does not guarantee you personally receive the same refurbished pack. Packs are sorted into certified secondary batches meeting strict regulatory safety specifications.
            </div>
          </div>
        </>
      )}
    </div>
  );
}

