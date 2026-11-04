import React from 'react';
import { useBatteryStore } from '../../context/BatteryContext';
import { Leaf, Award, Recycle, Zap, ArrowUpRight, TrendingUp } from 'lucide-react';

export default function EnvironmentalImpact() {
  const { batteries } = useBatteryStore();

  // Compute owner's personal metrics based on their registered batteries
  const assessedBatteries = batteries.filter(b => b.status === 'Assessed' || b.status === 'Approved');

  // Estimates: ~4.5 kg of hazardous e-waste diverted per 10 Ah of battery cell; ~12.2 kg CO2 avoided per repurposed pack
  const totalCapacityAh = assessedBatteries.reduce((acc, b) => acc + (b.rated_capacity_ah || 50), 0);
  const totalWasteDivertedKg = Math.round((totalCapacityAh / 10) * 4.5);
  const totalCo2AvoidedKg = Math.round(assessedBatteries.length * 145);
  const totalRecoveredValue = assessedBatteries.reduce((acc, b) => acc + (b.exchange_credit_inr || 0), 0);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-xl font-bold text-slate-900">My Environmental & Circular Impact</h1>
        <p className="text-xs text-slate-500 mt-1">
          Tracking the ecological sustainability contributions of your retired vehicle battery packs diverted from toxic landfills.
        </p>
      </div>

      {/* Main Impact KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
        <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs">
          <div className="w-10 h-10 rounded-xl bg-emerald-50 border border-emerald-200 flex items-center justify-center text-emerald-700 mb-3">
            <Recycle className="w-5 h-5" />
          </div>
          <span className="text-xs font-semibold text-slate-500">Hazardous Waste Diverted</span>
          <p className="text-3xl font-extrabold text-slate-900 mt-1">{totalWasteDivertedKg} <span className="text-sm font-semibold text-slate-400">kg</span></p>
          <p className="text-[11px] text-slate-400 mt-1">Heavy metals (Lithium, Nickel, Cobalt) kept out of landfills</p>
        </div>

        <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs">
          <div className="w-10 h-10 rounded-xl bg-blue-50 border border-blue-200 flex items-center justify-center text-blue-700 mb-3">
            <Leaf className="w-5 h-5" />
          </div>
          <span className="text-xs font-semibold text-slate-500">Net CO₂ Emissions Avoided</span>
          <p className="text-3xl font-extrabold text-slate-900 mt-1">{totalCo2AvoidedKg} <span className="text-sm font-semibold text-slate-400">kg CO₂e</span></p>
          <p className="text-[11px] text-slate-400 mt-1">Equivalent to planting ~{Math.round(totalCo2AvoidedKg / 22)} urban trees</p>
        </div>

        <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs">
          <div className="w-10 h-10 rounded-xl bg-purple-50 border border-purple-200 flex items-center justify-center text-purple-700 mb-3">
            <Award className="w-5 h-5" />
          </div>
          <span className="text-xs font-semibold text-slate-500">Recovered Circular Capital</span>
          <p className="text-3xl font-extrabold text-slate-900 mt-1">₹{totalRecoveredValue.toLocaleString()}</p>
          <p className="text-[11px] text-slate-400 mt-1">Direct buyback value injected back into clean mobility</p>
        </div>
      </div>

      {/* Circular Lifecycle Breakdown */}
      <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-xs space-y-4">
        <h2 className="text-sm font-bold text-slate-900">How ReVolt Closes the Battery Lifecycle Loop</h2>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
          <div className="p-4 bg-slate-50 rounded-xl border border-slate-200 space-y-2">
            <div className="flex items-center gap-2 font-bold text-slate-900">
              <span className="w-6 h-6 rounded-full bg-emerald-600 text-white flex items-center justify-center text-xs">1</span>
              <span>Primary EV Retirement</span>
            </div>
            <p className="text-slate-600 leading-relaxed">
              When an EV battery reaches 70–80% SOH, it no longer satisfies automotive acceleration specs, but possesses substantial electrochemical energy density.
            </p>
          </div>

          <div className="p-4 bg-slate-50 rounded-xl border border-slate-200 space-y-2">
            <div className="flex items-center gap-2 font-bold text-slate-900">
              <span className="w-6 h-6 rounded-full bg-emerald-600 text-white flex items-center justify-center text-xs">2</span>
              <span>Fast 90s Screening & Passport</span>
            </div>
            <p className="text-slate-600 leading-relaxed">
              Electrochemical impedance spectroscopy and thermal delta profiling rapidly separate healthy modules from hazardous runaway cells without costly disassembly.
            </p>
          </div>

          <div className="p-4 bg-slate-50 rounded-xl border border-slate-200 space-y-2">
            <div className="flex items-center gap-2 font-bold text-slate-900">
              <span className="w-6 h-6 rounded-full bg-emerald-600 text-white flex items-center justify-center text-xs">3</span>
              <span>Stationary Second-Life Deployment</span>
            </div>
            <p className="text-slate-600 leading-relaxed">
              Approved modules power solar microgrids, UPS backup, and light mobility for an additional 4–7 years before final closed-loop hydrometallurgical recycling.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

