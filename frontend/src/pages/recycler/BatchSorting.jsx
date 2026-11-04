import React, { useState } from 'react';
import { useBatteryStore } from '../../context/BatteryContext';
import { Layers, ShieldAlert, ShieldCheck, CheckCircle2, AlertTriangle, ArrowRight, Filter, Search } from 'lucide-react';

export default function BatchSorting() {
  const { batteries } = useBatteryStore();

  const [activeTab, setActiveTab] = useState('ALL');
  const [searchTerm, setSearchTerm] = useState('');
  const [feedbackMsg, setFeedbackMsg] = useState('');

  const assessedBatteries = batteries.filter(b => b.status === 'Assessed' || b.status === 'Approved');

  const filtered = assessedBatteries.filter(b => {
    const matchesSearch = b.battery_id.toLowerCase().includes(searchTerm.toLowerCase()) ||
      b.chemistry.toLowerCase().includes(searchTerm.toLowerCase());

    if (activeTab === 'ALL') return matchesSearch;
    if (activeTab === 'REUSE') return matchesSearch && b.recommended_action === 'Direct Reuse';
    if (activeTab === 'REPURPOSE') return matchesSearch && b.recommended_action === 'Repurpose';
    if (activeTab === 'RECYCLE') return matchesSearch && (b.recommended_action === 'Recycle' || b.safety_status === 'Critical Danger');
    return matchesSearch;
  });

  const handleRouteSort = (battery, targetBatch) => {
    if (battery.safety_status === 'Critical Danger' && targetBatch !== 'Recycle') {
      setFeedbackMsg(`SAFETY ENFORCEMENT: ${battery.battery_id} has critical thermal runaway flags. Sorting into "${targetBatch}" is strictly prohibited by safety policy.`);
      return;
    }

    setFeedbackMsg(`Battery ${battery.battery_id} successfully queued into "${targetBatch}" processing stream.`);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-xl font-bold text-slate-900">Recycler Batch Sorting & Route Allocation</h1>
        <p className="text-xs text-slate-500 mt-1">
          Segregate assessed EV battery packs into secondary applications with automated safety protocol enforcement.
        </p>
      </div>

      {feedbackMsg && (
        <div className={`p-4 rounded-xl border flex items-center justify-between text-xs ${
          feedbackMsg.includes('SAFETY') ? 'bg-rose-50 border-rose-300 text-rose-900' : 'bg-emerald-50 border-emerald-200 text-emerald-800'
        }`}>
          <div className="flex items-center gap-2">
            {feedbackMsg.includes('SAFETY') ? <AlertTriangle className="w-4 h-4 text-rose-600 shrink-0" /> : <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />}
            <span>{feedbackMsg}</span>
          </div>
          <button onClick={() => setFeedbackMsg('')} className="font-bold ml-2">✕</button>
        </div>
      )}

      {/* Filter and Search Bar */}
      <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs flex flex-col sm:flex-row items-center justify-between gap-3">
        <div className="relative flex-1 w-full sm:max-w-xs">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Search battery ID, chemistry..."
            className="w-full pl-9 pr-3 py-1.5 text-xs rounded-lg border border-slate-300 focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500"
          />
        </div>

        <div className="flex items-center gap-2 overflow-x-auto w-full sm:w-auto">
          {['ALL', 'REUSE', 'REPURPOSE', 'RECYCLE'].map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`px-3 py-1.5 text-xs font-semibold rounded-lg transition-colors whitespace-nowrap ${
                activeTab === tab
                  ? 'bg-slate-900 text-white'
                  : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
              }`}
            >
              {tab === 'ALL' ? 'All Batches' : tab}
            </button>
          ))}
        </div>
      </div>

      {/* Sorting Table */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-xs overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 border-b border-slate-200 text-slate-600 uppercase font-semibold">
              <tr>
                <th className="px-5 py-3.5">Battery ID</th>
                <th className="px-5 py-3.5">Chemistry</th>
                <th className="px-5 py-3.5">Assessed SOH</th>
                <th className="px-5 py-3.5">Safety Classification</th>
                <th className="px-5 py-3.5">AI Recommended Route</th>
                <th className="px-5 py-3.5 text-right">Route Allocation</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {filtered.map((b) => {
                const isCritical = b.safety_status === 'Critical Danger';

                return (
                  <tr key={b.battery_id} className="hover:bg-slate-50/70 transition-colors">
                    <td className="px-5 py-4">
                      <span className="font-bold text-slate-900 text-sm">{b.battery_id}</span>
                      <p className="text-[10px] text-slate-400">{b.vehicle_model || 'EV Fleet'}</p>
                    </td>

                    <td className="px-5 py-4">
                      <span className="font-semibold px-2 py-0.5 rounded bg-slate-100 text-slate-700">
                        {b.chemistry} ({b.rated_capacity_ah} Ah)
                      </span>
                    </td>

                    <td className="px-5 py-4">
                      <span className={`text-sm font-bold ${
                        b.soh_estimate >= 80 ? 'text-emerald-600' : (b.soh_estimate >= 60 ? 'text-amber-600' : 'text-rose-600')
                      }`}>
                        {b.soh_estimate}%
                      </span>
                    </td>

                    <td className="px-5 py-4">
                      <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-semibold ${
                        isCritical ? 'bg-rose-100 text-rose-800' : 'bg-emerald-100 text-emerald-800'
                      }`}>
                        {isCritical ? <ShieldAlert className="w-3.5 h-3.5" /> : <ShieldCheck className="w-3.5 h-3.5" />}
                        <span>{b.safety_status}</span>
                      </span>
                    </td>

                    <td className="px-5 py-4 font-semibold text-slate-800">
                      {b.recommended_action}
                    </td>

                    <td className="px-5 py-4 text-right">
                      <div className="inline-flex items-center gap-1.5">
                        <button
                          disabled={isCritical}
                          onClick={() => handleRouteSort(b, 'Reuse')}
                          className={`px-2.5 py-1 rounded text-[11px] font-semibold transition-colors border ${
                            isCritical
                              ? 'bg-slate-100 text-slate-300 border-slate-200 cursor-not-allowed'
                              : 'bg-emerald-50 hover:bg-emerald-100 text-emerald-800 border-emerald-200'
                          }`}
                          title={isCritical ? 'Unsafe battery cannot be reused' : 'Route to Motive Reuse'}
                        >
                          Reuse
                        </button>

                        <button
                          disabled={isCritical}
                          onClick={() => handleRouteSort(b, 'Repurpose')}
                          className={`px-2.5 py-1 rounded text-[11px] font-semibold transition-colors border ${
                            isCritical
                              ? 'bg-slate-100 text-slate-300 border-slate-200 cursor-not-allowed'
                              : 'bg-blue-50 hover:bg-blue-100 text-blue-800 border-blue-200'
                          }`}
                          title={isCritical ? 'Unsafe battery cannot be repurposed' : 'Route to Stationary Storage'}
                        >
                          Repurpose
                        </button>

                        <button
                          onClick={() => handleRouteSort(b, 'Recycle')}
                          className="px-2.5 py-1 rounded text-[11px] font-semibold bg-rose-50 hover:bg-rose-100 text-rose-800 border border-rose-200 transition-colors"
                        >
                          Recycle
                        </button>
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

