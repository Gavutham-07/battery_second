import React from 'react';
import { useBatteryStore } from '../../context/BatteryContext';
import { BarChart3, Recycle, Leaf, TrendingUp, Layers, CheckCircle2, ShieldAlert, Award } from 'lucide-react';

export default function ImpactSummary() {
  const { batteries, getRecyclerBatches } = useBatteryStore();
  const { reuse, repurpose, recycle } = getRecyclerBatches();

  const totalProcessed = batteries.filter(b => b.status === 'Assessed' || b.status === 'Approved').length;
  const totalWasteDivertedKg = Math.round(totalProcessed * 42.5); // avg kg pack weight diverted
  const totalCo2AvoidedKg = Math.round(totalProcessed * 180.0);
  const totalRecoveredValueInr = batteries.reduce((acc, b) => acc + (b.exchange_credit_inr || 0), 0);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-xl font-bold text-slate-900">Recycler Facility Aggregate Impact & Throughput</h1>
        <p className="text-xs text-slate-500 mt-1">
          High-level operational metrics across all secondary intake, refurbishment sorting, and hydrometallurgical material recovery batches.
        </p>
      </div>

      {/* Aggregate KPI Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
        <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs">
          <div className="flex items-center justify-between text-slate-500 mb-2">
            <span className="text-xs font-semibold">Total Recovered Capital</span>
            <Award className="w-5 h-5 text-emerald-600" />
          </div>
          <p className="text-2xl font-extrabold text-slate-900">₹{totalRecoveredValueInr.toLocaleString()}</p>
          <p className="text-[11px] text-slate-400 mt-1">Direct secondary market value</p>
        </div>

        <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs">
          <div className="flex items-center justify-between text-slate-500 mb-2">
            <span className="text-xs font-semibold">Hazardous Waste Diverted</span>
            <Recycle className="w-5 h-5 text-blue-600" />
          </div>
          <p className="text-2xl font-extrabold text-slate-900">{totalWasteDivertedKg} <span className="text-sm font-semibold text-slate-400">kg</span></p>
          <p className="text-[11px] text-slate-400 mt-1">Lithium & cathode active materials</p>
        </div>

        <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs">
          <div className="flex items-center justify-between text-slate-500 mb-2">
            <span className="text-xs font-semibold">Total CO₂e Avoided</span>
            <Leaf className="w-5 h-5 text-emerald-600" />
          </div>
          <p className="text-2xl font-extrabold text-slate-900">{totalCo2AvoidedKg} <span className="text-sm font-semibold text-slate-400">kg</span></p>
          <p className="text-[11px] text-slate-400 mt-1">Offset vs virgin mineral extraction</p>
        </div>

        <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs">
          <div className="flex items-center justify-between text-slate-500 mb-2">
            <span className="text-xs font-semibold">Batteries Processed</span>
            <Layers className="w-5 h-5 text-purple-600" />
          </div>
          <p className="text-2xl font-extrabold text-slate-900">{totalProcessed}</p>
          <p className="text-[11px] text-slate-400 mt-1">Completed 90s screening</p>
        </div>
      </div>

      {/* Batch Distribution Breakdown */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
        <div className="bg-white rounded-xl border border-emerald-200 p-5 shadow-xs">
          <div className="flex items-center justify-between mb-3">
            <span className="text-xs font-bold uppercase tracking-wider text-emerald-800">1. Motive Reuse Batch</span>
            <span className="text-xs px-2 py-0.5 rounded-full font-bold bg-emerald-100 text-emerald-800">{reuse.length} Packs</span>
          </div>
          <p className="text-xs text-slate-600 leading-relaxed">
            High health packs (SOH ≥ 80% & Safe). High dynamic peak C-rate capability suitable for e-rickshaws, farm tractors, and light utility EVs.
          </p>
          <div className="mt-4 pt-3 border-t border-slate-100 text-xs text-slate-500">
            {reuse.map(b => (
              <div key={b.battery_id} className="flex justify-between py-1">
                <span className="font-semibold text-slate-800">{b.battery_id}</span>
                <span className="text-emerald-600 font-bold">{b.soh_estimate}% SOH</span>
              </div>
            ))}
            {reuse.length === 0 && <p className="text-slate-400 italic">No packs currently in reuse threshold.</p>}
          </div>
        </div>

        <div className="bg-white rounded-xl border border-blue-200 p-5 shadow-xs">
          <div className="flex items-center justify-between mb-3">
            <span className="text-xs font-bold uppercase tracking-wider text-blue-800">2. Stationary Repurpose</span>
            <span className="text-xs px-2 py-0.5 rounded-full font-bold bg-blue-100 text-blue-800">{repurpose.length} Packs</span>
          </div>
          <p className="text-xs text-slate-600 leading-relaxed">
            Moderate health packs (60% ≤ SOH &lt; 80% & Safe). Ideal for gentle 0.2C–0.5C daily charge cycles in residential solar and telecom backup.
          </p>
          <div className="mt-4 pt-3 border-t border-slate-100 text-xs text-slate-500">
            {repurpose.map(b => (
              <div key={b.battery_id} className="flex justify-between py-1">
                <span className="font-semibold text-slate-800">{b.battery_id}</span>
                <span className="text-blue-600 font-bold">{b.soh_estimate}% SOH</span>
              </div>
            ))}
            {repurpose.length === 0 && <p className="text-slate-400 italic">No packs currently in repurpose batch.</p>}
          </div>
        </div>

        <div className="bg-white rounded-xl border border-rose-200 p-5 shadow-xs">
          <div className="flex items-center justify-between mb-3">
            <span className="text-xs font-bold uppercase tracking-wider text-rose-800">3. Hydrometallurgy Recycle</span>
            <span className="text-xs px-2 py-0.5 rounded-full font-bold bg-rose-100 text-rose-800">{recycle.length} Packs</span>
          </div>
          <p className="text-xs text-slate-600 leading-relaxed">
            Depleted packs (&lt;60% SOH) or Critical Thermal Danger units. Quarantined for safe shredding and high-yield black mass chemical extraction.
          </p>
          <div className="mt-4 pt-3 border-t border-slate-100 text-xs text-slate-500">
            {recycle.map(b => (
              <div key={b.battery_id} className="flex justify-between py-1">
                <span className="font-semibold text-slate-800">{b.battery_id}</span>
                <span className="text-rose-600 font-bold">{b.soh_estimate}% SOH</span>
              </div>
            ))}
            {recycle.length === 0 && <p className="text-slate-400 italic">No packs currently in recycle quarantine.</p>}
          </div>
        </div>
      </div>
    </div>
  );
}

