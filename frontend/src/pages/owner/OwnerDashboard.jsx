import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useBatteryStore } from '../../context/BatteryContext';
import {
  Layers,
  Clock,
  CheckCircle,
  Coins,
  QrCode,
  ArrowRight,
  ShieldAlert,
  BatteryCharging,
  Plus
} from 'lucide-react';

export default function OwnerDashboard() {
  const navigate = useNavigate();
  const { batteries } = useBatteryStore();

  const totalRegistered = batteries.length;
  const awaitingScreening = batteries.filter(b => b.status === 'Awaiting Screening').length;
  const assessed = batteries.filter(b => b.status === 'Assessed' || b.status === 'Approved').length;
  const availableOffers = batteries.filter(b => b.exchange_credit_inr && b.status !== 'Awaiting Screening').length;
  const availablePassports = batteries.filter(b => b.passport).length;

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="bg-white rounded-xl border border-slate-200 p-6 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 shadow-xs">
        <div>
          <h1 className="text-xl font-bold text-slate-900">EV Owner Dashboard</h1>
          <p className="text-xs text-slate-500 mt-1">
            Track registered EV batteries, view live diagnostic progress, and claim second-life exchange credits.
          </p>
        </div>
        <button
          onClick={() => navigate('/owner/batteries')}
          className="inline-flex items-center gap-2 px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg text-xs font-semibold shadow-xs transition-colors shrink-0"
        >
          <Plus className="w-4 h-4" />
          <span>Register New Battery</span>
        </button>
      </div>

      {/* Summary KPI Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-5 gap-4">
        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs">
          <div className="flex items-center justify-between text-slate-500 mb-2">
            <span className="text-xs font-medium">Registered</span>
            <Layers className="w-4 h-4 text-slate-400" />
          </div>
          <p className="text-2xl font-bold text-slate-900">{totalRegistered}</p>
          <p className="text-[11px] text-slate-400 mt-0.5">Total registered packs</p>
        </div>

        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs">
          <div className="flex items-center justify-between text-amber-600 mb-2">
            <span className="text-xs font-medium">Awaiting Test</span>
            <Clock className="w-4 h-4 text-amber-500" />
          </div>
          <p className="text-2xl font-bold text-amber-600">{awaitingScreening}</p>
          <p className="text-[11px] text-slate-400 mt-0.5">Pending screening test</p>
        </div>

        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs">
          <div className="flex items-center justify-between text-blue-600 mb-2">
            <span className="text-xs font-medium">Assessed</span>
            <CheckCircle className="w-4 h-4 text-blue-500" />
          </div>
          <p className="text-2xl font-bold text-blue-600">{assessed}</p>
          <p className="text-[11px] text-slate-400 mt-0.5">Diagnosed via AI engine</p>
        </div>

        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs">
          <div className="flex items-center justify-between text-emerald-600 mb-2">
            <span className="text-xs font-medium">Exchange Offers</span>
            <Coins className="w-4 h-4 text-emerald-500" />
          </div>
          <p className="text-2xl font-bold text-emerald-600">{availableOffers}</p>
          <p className="text-[11px] text-slate-400 mt-0.5">Valuations available</p>
        </div>

        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs col-span-2 lg:col-span-1">
          <div className="flex items-center justify-between text-purple-600 mb-2">
            <span className="text-xs font-medium">Passports</span>
            <QrCode className="w-4 h-4 text-purple-500" />
          </div>
          <p className="text-2xl font-bold text-purple-600">{availablePassports}</p>
          <p className="text-[11px] text-slate-400 mt-0.5">Minted QR Passports</p>
        </div>
      </div>

      {/* Recent Battery Activity */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-xs">
        <div className="p-4 border-b border-slate-100 flex items-center justify-between">
          <div>
            <h2 className="text-sm font-bold text-slate-900">Recent Battery Activity</h2>
            <p className="text-xs text-slate-500">Live operational status across all your vehicle batteries</p>
          </div>
          <button
            onClick={() => navigate('/owner/batteries')}
            className="text-xs font-semibold text-emerald-600 hover:text-emerald-700 flex items-center gap-1"
          >
            <span>View All</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>

        <div className="divide-y divide-slate-100">
          {batteries.map((b) => (
            <div key={b.battery_id} className="p-4 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 hover:bg-slate-50/60 transition-colors">
              <div className="flex items-start gap-3">
                <div className={`w-9 h-9 rounded-lg flex items-center justify-center shrink-0 mt-0.5 ${
                  b.safety_status === 'Critical Danger'
                    ? 'bg-rose-100 text-rose-700'
                    : (b.status === 'Approved' ? 'bg-emerald-100 text-emerald-700' : 'bg-slate-100 text-slate-700')
                }`}>
                  {b.safety_status === 'Critical Danger' ? <ShieldAlert className="w-5 h-5" /> : <BatteryCharging className="w-5 h-5" />}
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-sm text-slate-900">{b.battery_id}</span>
                    <span className="text-xs px-2 py-0.5 rounded font-medium bg-slate-100 text-slate-700 border border-slate-200">
                      {b.chemistry} • {b.rated_capacity_ah} Ah
                    </span>
                    <span className={`text-[11px] px-2 py-0.5 rounded-full font-medium ${
                      b.status === 'Approved'
                        ? 'bg-purple-100 text-purple-800'
                        : (b.status === 'Assessed' ? 'bg-blue-100 text-blue-800' : 'bg-amber-100 text-amber-800')
                    }`}>
                      {b.status}
                    </span>
                  </div>
                  <p className="text-xs text-slate-500 mt-1">
                    {b.vehicle_model} • Registered {new Date(b.registration_date).toLocaleDateString()}
                  </p>
                </div>
              </div>

              <div className="flex items-center gap-3">
                {b.soh_estimate !== null && (
                  <div className="text-right">
                    <p className="text-xs text-slate-400 font-medium">SOH</p>
                    <p className={`text-sm font-bold ${
                      b.soh_estimate >= 80 ? 'text-emerald-600' : (b.soh_estimate >= 60 ? 'text-amber-600' : 'text-rose-600')
                    }`}>
                      {b.soh_estimate}%
                    </p>
                  </div>
                )}
                <button
                  onClick={() => navigate('/owner/batteries')}
                  className="px-3 py-1.5 text-xs font-semibold text-slate-700 bg-slate-100 hover:bg-slate-200 rounded-lg transition-colors border border-slate-200"
                >
                  Check Details
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

