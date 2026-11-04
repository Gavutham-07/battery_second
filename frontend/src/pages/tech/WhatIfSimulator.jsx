import React, { useState, useMemo } from 'react';
import { useSearchParams } from 'react-router-dom';
import { useBatteryStore } from '../../context/BatteryContext';
import { calculateWhatIf } from '../../services/assessmentEngine';
import { Sliders, RotateCcw, Clock, Thermometer, BatteryCharging, AlertTriangle, Info, ArrowUpRight } from 'lucide-react';

export default function WhatIfSimulator() {
  const [searchParams] = useSearchParams();
  const { batteries } = useBatteryStore();

  const initialId = searchParams.get('battery_id') || batteries.find(b => b.soh_estimate !== null)?.battery_id || batteries[0]?.battery_id;
  const [selectedBatteryId, setSelectedBatteryId] = useState(initialId);

  // Sliders state (defaults: 6h daily usage, 28°C ambient, 70% DoD)
  const [dailyUsageHours, setDailyUsageHours] = useState(6);
  const [ambientTempC, setAmbientTempC] = useState(28);
  const [depthOfDischargePct, setDepthOfDischargePct] = useState(70);

  const currentBattery = batteries.find(b => b.battery_id === selectedBatteryId) || batteries[0];

  const whatIfResult = useMemo(() => {
    return calculateWhatIf(currentBattery, {
      dailyUsageHours: Number(dailyUsageHours),
      ambientTempC: Number(ambientTempC),
      depthOfDischargePct: Number(depthOfDischargePct)
    });
  }, [currentBattery, dailyUsageHours, ambientTempC, depthOfDischargePct]);

  const handleReset = () => {
    setDailyUsageHours(6);
    setAmbientTempC(28);
    setDepthOfDischargePct(70);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-xs flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-slate-900">What-If Operating Lifetime Simulator</h1>
          <p className="text-xs text-slate-500 mt-1">
            Simulate accelerated electrochemical degradation curves by varying daily duty cycles, ambient thermal load, and depth of discharge.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <label className="text-xs font-semibold text-slate-600">Select Battery:</label>
          <select
            value={selectedBatteryId}
            onChange={(e) => setSelectedBatteryId(e.target.value)}
            className="text-xs font-bold px-3 py-1.5 rounded-lg border border-slate-300 bg-white focus:border-emerald-500"
          >
            {batteries.map((b) => (
              <option key={b.battery_id} value={b.battery_id}>
                {b.battery_id} ({b.chemistry} • SOH: {b.soh_estimate !== null ? `${b.soh_estimate}%` : 'Unscreened'})
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Notice Banner */}
      <div className="p-3 bg-blue-50 border border-blue-200 rounded-xl text-xs text-blue-900 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Info className="w-4 h-4 text-blue-600 shrink-0" />
          <span>Notice: These are computational predictions based on semi-empirical degradation models, not newly conducted physical screening tests.</span>
        </div>
        <button
          onClick={handleReset}
          className="inline-flex items-center gap-1 text-xs font-semibold text-blue-700 hover:text-blue-900 underline whitespace-nowrap ml-2"
        >
          <RotateCcw className="w-3 h-3" />
          <span>Reset to Recommended Conditions</span>
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Sliders Control Panel */}
        <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-xs space-y-6">
          <div className="flex items-center justify-between pb-3 border-b border-slate-100">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-800">Operating Variable Controls</span>
            <Sliders className="w-4 h-4 text-slate-400" />
          </div>

          {/* Slider 1: Daily Usage */}
          <div>
            <div className="flex items-center justify-between text-xs mb-1">
              <span className="font-semibold text-slate-700 flex items-center gap-1.5">
                <Clock className="w-3.5 h-3.5 text-blue-600" />
                <span>Daily Operating Duty</span>
              </span>
              <span className="font-bold text-slate-900 bg-slate-100 px-2 py-0.5 rounded">{dailyUsageHours} hrs/day</span>
            </div>
            <input
              type="range"
              min="1"
              max="16"
              step="1"
              value={dailyUsageHours}
              onChange={(e) => setDailyUsageHours(e.target.value)}
              className="w-full accent-emerald-600 cursor-pointer"
            />
            <div className="flex justify-between text-[10px] text-slate-400 mt-0.5">
              <span>1 hr (Float/UPS)</span>
              <span>8 hrs (Fleet EV)</span>
              <span>16 hrs (Continuous)</span>
            </div>
          </div>

          {/* Slider 2: Ambient Temperature */}
          <div>
            <div className="flex items-center justify-between text-xs mb-1">
              <span className="font-semibold text-slate-700 flex items-center gap-1.5">
                <Thermometer className="w-3.5 h-3.5 text-amber-600" />
                <span>Ambient Operating Temp</span>
              </span>
              <span className={`font-bold px-2 py-0.5 rounded ${ambientTempC >= 38 ? 'bg-rose-100 text-rose-800' : 'bg-slate-100 text-slate-900'}`}>
                {ambientTempC} °C
              </span>
            </div>
            <input
              type="range"
              min="15"
              max="45"
              step="1"
              value={ambientTempC}
              onChange={(e) => setAmbientTempC(e.target.value)}
              className="w-full accent-amber-600 cursor-pointer"
            />
            <div className="flex justify-between text-[10px] text-slate-400 mt-0.5">
              <span>15°C (Climate-Controlled)</span>
              <span>28°C (Nominal)</span>
              <span>45°C (High Tropical Heat)</span>
            </div>
          </div>

          {/* Slider 3: Depth of Discharge (DoD) */}
          <div>
            <div className="flex items-center justify-between text-xs mb-1">
              <span className="font-semibold text-slate-700 flex items-center gap-1.5">
                <BatteryCharging className="w-3.5 h-3.5 text-purple-600" />
                <span>Depth of Discharge (DoD)</span>
              </span>
              <span className="font-bold text-slate-900 bg-slate-100 px-2 py-0.5 rounded">{depthOfDischargePct}%</span>
            </div>
            <input
              type="range"
              min="20"
              max="100"
              step="5"
              value={depthOfDischargePct}
              onChange={(e) => setDepthOfDischargePct(e.target.value)}
              className="w-full accent-purple-600 cursor-pointer"
            />
            <div className="flex justify-between text-[10px] text-slate-400 mt-0.5">
              <span>20% (Conservative)</span>
              <span>70% (Standard)</span>
              <span>100% (Full Deep Cycle)</span>
            </div>
          </div>

          <button
            onClick={handleReset}
            className="w-full py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg text-xs font-semibold transition-colors flex items-center justify-center gap-1.5 border border-slate-300"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            <span>Reset to Recommended Conditions</span>
          </button>
        </div>

        {/* Prediction Results Display */}
        <div className="lg:col-span-2 space-y-4">
          <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-xs space-y-6">
            <div>
              <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">Simulated Lifetime Impact</span>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mt-3">
                <div className="p-4 bg-slate-50 rounded-xl border border-slate-200">
                  <span className="text-[11px] text-slate-500 font-semibold">Baseline RUL</span>
                  <p className="text-2xl font-bold text-slate-700 mt-1">{whatIfResult.baseline_residual_life_years} <span className="text-xs font-normal">years</span></p>
                  <p className="text-[10px] text-slate-400 mt-0.5">Standard 1 cycle/day, 28°C</p>
                </div>

                <div className="p-4 bg-emerald-50 rounded-xl border border-emerald-200">
                  <span className="text-[11px] text-emerald-800 font-semibold">Simulated Residual Life</span>
                  <p className="text-3xl font-extrabold text-emerald-700 mt-1">{whatIfResult.simulated_residual_life_years} <span className="text-xs font-normal">years</span></p>
                  <p className="text-[10px] text-emerald-600 mt-0.5">
                    {whatIfResult.simulated_residual_life_years >= whatIfResult.baseline_residual_life_years
                      ? `+${(whatIfResult.simulated_residual_life_years - whatIfResult.baseline_residual_life_years).toFixed(1)} yr lifespan bonus`
                      : `${(whatIfResult.simulated_residual_life_years - whatIfResult.baseline_residual_life_years).toFixed(1)} yr thermal/cycling deficit`}
                  </p>
                </div>

                <div className="p-4 bg-slate-50 rounded-xl border border-slate-200">
                  <span className="text-[11px] text-slate-500 font-semibold">Projected Cycle Life</span>
                  <p className="text-2xl font-bold text-slate-900 mt-1">{whatIfResult.cycle_life_projection} <span className="text-xs font-normal">cycles</span></p>
                  <p className="text-[10px] text-slate-400 mt-0.5">Before 60% end-of-second-life</p>
                </div>
              </div>
            </div>

            {/* Thermal Stress & Engineering Notes */}
            <div className="p-4 bg-slate-50 rounded-xl border border-slate-200 space-y-2 text-xs">
              <div className="flex items-center justify-between">
                <span className="font-semibold text-slate-700">Thermal & Electrochemical Stress:</span>
                <span className={`px-2.5 py-0.5 rounded font-bold text-xs ${
                  ambientTempC >= 38 ? 'bg-rose-100 text-rose-800' : (ambientTempC >= 32 ? 'bg-amber-100 text-amber-800' : 'bg-emerald-100 text-emerald-800')
                }`}>
                  {whatIfResult.thermal_stress_factor}
                </span>
              </div>
              <p className="text-slate-600 leading-relaxed bg-white p-3 rounded-lg border border-slate-200 mt-2">
                <strong>Technician Recommendation:</strong> {whatIfResult.recommendation_note}
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

