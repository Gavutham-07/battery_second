import React, { useState } from 'react';
import { useBatteryStore } from '../../context/BatteryContext';
import {
  Layers,
  PlusCircle,
  CheckCircle2,
  AlertTriangle,
  Clock,
  ShieldCheck,
  ShieldAlert,
  Sparkles,
  ArrowRight,
  Info,
  QrCode,
  Coins
} from 'lucide-react';

export default function MyBatteries() {
  const { batteries, registerBattery } = useBatteryStore();

  // Registration Form State
  const [formData, setFormData] = useState({
    battery_id: '',
    chemistry: 'LFP',
    rated_capacity_ah: '',
    vehicle_model: '',
    owner_name: ''
  });

  const [formSuccess, setFormSuccess] = useState('');
  const [formError, setFormError] = useState('');

  // Selected battery for modal / status check
  const [selectedBattery, setSelectedBattery] = useState(null);

  const handleSubmit = (e) => {
    e.preventDefault();
    setFormSuccess('');
    setFormError('');

    if (!formData.battery_id.trim()) {
      setFormError('Battery ID is required (e.g. BAT-105)');
      return;
    }
    if (!formData.rated_capacity_ah || Number(formData.rated_capacity_ah) <= 0) {
      setFormError('Please enter a valid rated capacity in Ah');
      return;
    }

    const result = registerBattery({
      battery_id: formData.battery_id.trim(),
      chemistry: formData.chemistry,
      rated_capacity_ah: Number(formData.rated_capacity_ah),
      vehicle_model: formData.vehicle_model.trim() || 'EV Fleet Vehicle',
      owner_name: formData.owner_name.trim() || 'EV Owner'
    });

    if (result.success) {
      setFormSuccess(`Battery ${result.battery.battery_id} registered successfully! Status: Awaiting Screening.`);
      setFormData({
        battery_id: '',
        chemistry: 'LFP',
        rated_capacity_ah: '',
        vehicle_model: '',
        owner_name: ''
      });
      // Automatically open status drawer for newly registered battery
      setSelectedBattery(result.battery);
    } else {
      setFormError(result.message || 'Failed to register battery');
    }
  };

  return (
    <div className="space-y-8">
      {/* Page Header */}
      <div>
        <h1 className="text-xl font-bold text-slate-900">My Batteries & Screening Status</h1>
        <p className="text-xs text-slate-500 mt-1">
          Register new retired EV batteries and inspect live diagnostic reports on the same unified page.
        </p>
      </div>

      {/* 1. Registration Form Card (at the top) */}
      <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-xs">
        <div className="flex items-center gap-2 mb-4 pb-3 border-b border-slate-100">
          <PlusCircle className="w-5 h-5 text-emerald-600" />
          <h2 className="text-sm font-bold text-slate-900">Register EV Battery Pack</h2>
        </div>

        {formSuccess && (
          <div className="mb-4 p-3 bg-emerald-50 border border-emerald-200 rounded-lg flex items-center gap-2 text-xs text-emerald-800">
            <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
            <span>{formSuccess}</span>
          </div>
        )}

        {formError && (
          <div className="mb-4 p-3 bg-rose-50 border border-rose-200 rounded-lg flex items-center gap-2 text-xs text-rose-800">
            <AlertTriangle className="w-4 h-4 text-rose-600 shrink-0" />
            <span>{formError}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">
              Battery ID <span className="text-rose-500">*</span>
            </label>
            <input
              type="text"
              required
              value={formData.battery_id}
              onChange={(e) => setFormData({ ...formData, battery_id: e.target.value })}
              placeholder="e.g. BAT-105"
              className="w-full text-xs px-3 py-2 rounded-lg border border-slate-300 focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">
              Chemistry <span className="text-rose-500">*</span>
            </label>
            <select
              value={formData.chemistry}
              onChange={(e) => setFormData({ ...formData, chemistry: e.target.value })}
              className="w-full text-xs px-3 py-2 rounded-lg border border-slate-300 focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 bg-white"
            >
              <option value="LFP">LFP (Lithium Iron Phosphate)</option>
              <option value="NMC">NMC (Nickel Manganese Cobalt)</option>
              <option value="NCA">NCA (Nickel Cobalt Aluminum)</option>
            </select>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">
              Rated Capacity (Ah) <span className="text-rose-500">*</span>
            </label>
            <input
              type="number"
              step="0.1"
              required
              value={formData.rated_capacity_ah}
              onChange={(e) => setFormData({ ...formData, rated_capacity_ah: e.target.value })}
              placeholder="e.g. 50"
              className="w-full text-xs px-3 py-2 rounded-lg border border-slate-300 focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">
              Vehicle Model (Optional)
            </label>
            <input
              type="text"
              value={formData.vehicle_model}
              onChange={(e) => setFormData({ ...formData, vehicle_model: e.target.value })}
              placeholder="e.g. Tata Nexon EV"
              className="w-full text-xs px-3 py-2 rounded-lg border border-slate-300 focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500"
            />
          </div>

          <div className="md:col-span-4 flex justify-end">
            <button
              type="submit"
              className="px-5 py-2.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg text-xs font-semibold shadow-xs transition-colors"
            >
              Register Battery
            </button>
          </div>
        </form>
      </div>

      {/* 2. Registered Batteries List (below form on the SAME page) */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-bold text-slate-900">Registered Batteries ({batteries.length})</h2>
          <span className="text-xs text-slate-500">Click "Check Status" for real-time diagnostics</span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {batteries.map((b) => (
            <div
              key={b.battery_id}
              className={`bg-white rounded-xl border p-5 shadow-xs flex flex-col justify-between transition-all ${
                selectedBattery?.battery_id === b.battery_id ? 'border-emerald-500 ring-2 ring-emerald-500/20' : 'border-slate-200 hover:border-slate-300'
              }`}
            >
              <div>
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-2">
                    <span className="text-base font-bold text-slate-900">{b.battery_id}</span>
                    <span className="text-[11px] font-semibold px-2 py-0.5 rounded bg-slate-100 text-slate-700 border border-slate-200">
                      {b.chemistry}
                    </span>
                  </div>

                  <span className={`text-[11px] font-semibold px-2 py-0.5 rounded-full ${
                    b.status === 'Approved'
                      ? 'bg-purple-100 text-purple-800'
                      : (b.status === 'Assessed' ? 'bg-blue-100 text-blue-800' : 'bg-amber-100 text-amber-800')
                  }`}>
                    {b.status}
                  </span>
                </div>

                <div className="text-xs text-slate-600 space-y-1 mb-4">
                  <p><span className="text-slate-400">Capacity:</span> {b.rated_capacity_ah} Ah</p>
                  <p><span className="text-slate-400">Vehicle:</span> {b.vehicle_model || 'N/A'}</p>
                  <p><span className="text-slate-400">Registered:</span> {new Date(b.registration_date).toLocaleDateString()}</p>
                </div>

                {b.soh_estimate !== null ? (
                  <div className="p-3 bg-slate-50 rounded-lg border border-slate-100 mb-4">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-medium text-slate-600">Assessed SOH</span>
                      <span className={`text-base font-bold ${
                        b.soh_estimate >= 80 ? 'text-emerald-600' : (b.soh_estimate >= 60 ? 'text-amber-600' : 'text-rose-600')
                      }`}>
                        {b.soh_estimate}%
                      </span>
                    </div>
                    <div className="flex items-center justify-between mt-1 text-[11px] text-slate-500">
                      <span>Safety: <strong className={b.safety_status === 'Critical Danger' ? 'text-rose-600' : 'text-emerald-700'}>{b.safety_status}</strong></span>
                      <span>Route: <strong className="text-slate-700">{b.recommended_action || 'N/A'}</strong></span>
                    </div>
                  </div>
                ) : (
                  <div className="p-3 bg-amber-50/60 rounded-lg border border-amber-200/60 mb-4 text-xs text-amber-800 flex items-center gap-2">
                    <Clock className="w-4 h-4 text-amber-600 shrink-0" />
                    <span>Awaiting technician 90s screening test</span>
                  </div>
                )}
              </div>

              <button
                onClick={() => setSelectedBattery(b)}
                className="w-full py-2 bg-slate-100 hover:bg-slate-200 text-slate-800 rounded-lg text-xs font-semibold transition-colors flex items-center justify-center gap-1.5 border border-slate-200"
              >
                <span>Check Status</span>
                <ArrowRight className="w-3.5 h-3.5 text-slate-500" />
              </button>
            </div>
          ))}
        </div>
      </div>

      {/* 3. Status Detail Modal / Drawer */}
      {selectedBattery && (
        <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto border border-slate-200 shadow-xl p-6">
            <div className="flex items-center justify-between pb-4 border-b border-slate-100">
              <div className="flex items-center gap-2.5">
                <span className="text-lg font-bold text-slate-900">{selectedBattery.battery_id}</span>
                <span className="text-xs px-2.5 py-0.5 rounded-full font-semibold bg-slate-100 text-slate-700">
                  {selectedBattery.chemistry} • {selectedBattery.rated_capacity_ah} Ah
                </span>
                <span className={`text-xs px-2.5 py-0.5 rounded-full font-semibold ${
                  selectedBattery.status === 'Approved' ? 'bg-purple-100 text-purple-800' : (selectedBattery.status === 'Assessed' ? 'bg-blue-100 text-blue-800' : 'bg-amber-100 text-amber-800')
                }`}>
                  {selectedBattery.status}
                </span>
              </div>
              <button
                onClick={() => setSelectedBattery(null)}
                className="w-7 h-7 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-500 flex items-center justify-center text-sm font-bold"
              >
                ✕
              </button>
            </div>

            <div className="py-4 space-y-4">
              {/* If NOT Tested */}
              {selectedBattery.status === 'Awaiting Screening' && (
                <div className="p-5 bg-amber-50 rounded-xl border border-amber-200 space-y-3">
                  <div className="flex items-center gap-2 text-amber-900 font-bold text-sm">
                    <Clock className="w-5 h-5 text-amber-600" />
                    <span>Status: Awaiting Technician Screening</span>
                  </div>
                  <p className="text-xs text-amber-800 leading-relaxed">
                    This battery has been successfully registered in the ReVolt network. It is currently placed in the Service Center queue for a physical 90-second electrochemical screening test.
                  </p>
                  <div className="p-3 bg-white rounded-lg border border-amber-200 text-xs text-slate-700 space-y-1">
                    <p><strong className="text-slate-900">Registration Timestamp:</strong> {new Date(selectedBattery.registration_date).toLocaleString()}</p>
                    <p><strong className="text-slate-900">Assigned Diagnostic Test:</strong> 90s Voltage/Current/Thermal Profiling</p>
                    <p className="text-slate-500 italic mt-1">
                      Note: AI State of Health (SOH) and safety diagnostics are never fabricated before physical sensor readings are streamed.
                    </p>
                  </div>
                </div>
              )}

              {/* If Assessed / Approved */}
              {selectedBattery.soh_estimate !== null && (
                <div className="space-y-4">
                  {/* SOH & Safety Overview */}
                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                    <div className="p-3 bg-slate-50 rounded-xl border border-slate-200">
                      <span className="text-[11px] font-semibold text-slate-500">State of Health (SOH)</span>
                      <p className={`text-2xl font-bold mt-1 ${
                        selectedBattery.soh_estimate >= 80 ? 'text-emerald-600' : (selectedBattery.soh_estimate >= 60 ? 'text-amber-600' : 'text-rose-600')
                      }`}>
                        {selectedBattery.soh_estimate}%
                      </p>
                      <p className="text-[10px] text-slate-400">Confidence: {(selectedBattery.confidence_score * 100).toFixed(0)}% ({selectedBattery.confidence_level})</p>
                    </div>

                    <div className="p-3 bg-slate-50 rounded-xl border border-slate-200">
                      <span className="text-[11px] font-semibold text-slate-500">Safety Status</span>
                      <p className={`text-base font-bold mt-1 flex items-center gap-1 ${
                        selectedBattery.safety_status === 'Critical Danger' ? 'text-rose-600' : 'text-emerald-700'
                      }`}>
                        {selectedBattery.safety_status === 'Critical Danger' ? <ShieldAlert className="w-4 h-4" /> : <ShieldCheck className="w-4 h-4" />}
                        {selectedBattery.safety_status}
                      </p>
                      <p className="text-[10px] text-slate-400">Max Temp: {selectedBattery.max_test_temperature_c || 29.5}°C</p>
                    </div>

                    <div className="p-3 bg-slate-50 rounded-xl border border-slate-200">
                      <span className="text-[11px] font-semibold text-slate-500">Recommended Route</span>
                      <p className="text-base font-bold text-slate-900 mt-1">
                        {selectedBattery.recommended_action}
                      </p>
                      <p className="text-[10px] text-slate-400">Remaining: {selectedBattery.remaining_capacity_ah} Ah</p>
                    </div>
                  </div>

                  {/* Safety Flags if any */}
                  {selectedBattery.safety_flags && selectedBattery.safety_flags.length > 0 && (
                    <div className="p-3 bg-rose-50 border border-rose-200 rounded-xl text-xs text-rose-900 space-y-1">
                      <div className="font-bold flex items-center gap-1.5 text-rose-800">
                        <AlertTriangle className="w-4 h-4" />
                        <span>Safety Diagnostics Flags:</span>
                      </div>
                      <ul className="list-disc list-inside text-rose-700 pl-1 space-y-0.5">
                        {selectedBattery.safety_flags.map((flag, idx) => (
                          <li key={idx}>{flag}</li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* Plain-English Explanation */}
                  <div className="p-3 bg-blue-50/60 border border-blue-200/60 rounded-xl text-xs text-blue-950">
                    <span className="font-bold text-blue-900 flex items-center gap-1 mb-1">
                      <Info className="w-3.5 h-3.5 text-blue-600" />
                      AI Diagnostic Explanation:
                    </span>
                    <p className="leading-relaxed text-blue-900/90">{selectedBattery.plain_english_explanation}</p>
                  </div>

                  {/* Second-Life Recommendations */}
                  <div>
                    <h3 className="text-xs font-bold text-slate-900 mb-2">Second-Life Suitability Breakdown</h3>
                    <div className="space-y-2">
                      {selectedBattery.second_life_matches?.map((m, idx) => (
                        <div key={idx} className="p-2.5 bg-slate-50 rounded-lg border border-slate-200 flex items-center justify-between text-xs">
                          <div>
                            <span className="font-semibold text-slate-800">{m.application}</span>
                            <p className="text-[11px] text-slate-500">{m.reason}</p>
                          </div>
                          <div className="text-right shrink-0 ml-3">
                            <span className={`px-2 py-0.5 rounded font-semibold text-[10px] ${
                              m.suitability === 'Optimal' ? 'bg-emerald-100 text-emerald-800' :
                              (m.suitability === 'Good' ? 'bg-blue-100 text-blue-800' :
                              (m.suitability === 'Prohibited' ? 'bg-rose-100 text-rose-800' : 'bg-slate-200 text-slate-700'))
                            }`}>
                              {m.suitability}
                            </span>
                            <p className="text-[10px] text-slate-400 mt-0.5">~{m.predicted_lifetime_years} yrs</p>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Valuation & Passport Status */}
                  <div className="p-3 bg-slate-100 rounded-xl flex items-center justify-between text-xs">
                    <div className="flex items-center gap-2">
                      <Coins className="w-4 h-4 text-emerald-600" />
                      <div>
                        <span className="text-slate-500">Exchange Buyback Valuation:</span>
                        <p className="text-sm font-bold text-slate-900">₹{selectedBattery.exchange_credit_inr?.toLocaleString() || 'N/A'}</p>
                      </div>
                    </div>

                    <div className="flex items-center gap-2">
                      <QrCode className="w-4 h-4 text-purple-600" />
                      <div>
                        <span className="text-slate-500">QR Passport:</span>
                        <p className="font-semibold text-slate-800">
                          {selectedBattery.passport ? 'Minted & Verified' : 'Pending Technician Approval'}
                        </p>
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>

            <div className="pt-3 border-t border-slate-100 flex justify-end">
              <button
                onClick={() => setSelectedBattery(null)}
                className="px-4 py-2 bg-slate-800 hover:bg-slate-900 text-white rounded-lg text-xs font-semibold"
              >
                Close Report
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

