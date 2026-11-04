import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useBatteryStore } from '../../context/BatteryContext';
import { useDataSource } from '../../context/DataSourceContext';
import {
  ListOrdered,
  Activity,
  CheckCircle2,
  Clock,
  AlertTriangle,
  ArrowRight,
  ShieldCheck,
  Radio,
  Sliders
} from 'lucide-react';

export default function TechnicianDashboard() {
  const navigate = useNavigate();
  const { batteries } = useBatteryStore();
  const { sourceMeta, status } = useDataSource();

  const totalRegistered = batteries.length;
  const awaitingScreening = batteries.filter(b => b.status === 'Awaiting Screening').length;
  const assessed = batteries.filter(b => b.status === 'Assessed').length;
  const approved = batteries.filter(b => b.status === 'Approved').length;
  const criticalCount = batteries.filter(b => b.safety_status === 'Critical Danger').length;

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="bg-white rounded-xl border border-slate-200 p-6 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 shadow-xs">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-bold text-slate-900">Technician Diagnostic Station</h1>
            <span className="px-2 py-0.5 rounded text-[11px] font-semibold bg-emerald-50 text-emerald-800 border border-emerald-200">
              Station ID: TECH-BLR-02
            </span>
          </div>
          <p className="text-xs text-slate-500 mt-1">
            Conduct 90-second electrochemical screening, evaluate thermal safety flags, and mint certified digital battery passports.
          </p>
        </div>

        <button
          onClick={() => navigate('/tech/queue')}
          className="inline-flex items-center gap-2 px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg text-xs font-semibold shadow-xs transition-colors shrink-0"
        >
          <ListOrdered className="w-4 h-4" />
          <span>Open Intake Queue</span>
        </button>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-5 gap-4">
        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs">
          <div className="flex items-center justify-between text-slate-500 mb-2">
            <span className="text-xs font-medium">Intake Queue</span>
            <ListOrdered className="w-4 h-4 text-slate-400" />
          </div>
          <p className="text-2xl font-bold text-slate-900">{totalRegistered}</p>
          <p className="text-[11px] text-slate-400 mt-0.5">Total registered units</p>
        </div>

        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs">
          <div className="flex items-center justify-between text-amber-600 mb-2">
            <span className="text-xs font-medium">Awaiting Test</span>
            <Clock className="w-4 h-4 text-amber-500" />
          </div>
          <p className="text-2xl font-bold text-amber-600">{awaitingScreening}</p>
          <p className="text-[11px] text-slate-400 mt-0.5">Ready for 90s screening</p>
        </div>

        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs">
          <div className="flex items-center justify-between text-blue-600 mb-2">
            <span className="text-xs font-medium">Assessed</span>
            <Activity className="w-4 h-4 text-blue-500" />
          </div>
          <p className="text-2xl font-bold text-blue-600">{assessed}</p>
          <p className="text-[11px] text-slate-400 mt-0.5">Pending sign-off</p>
        </div>

        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs">
          <div className="flex items-center justify-between text-purple-600 mb-2">
            <span className="text-xs font-medium">Passports Minted</span>
            <ShieldCheck className="w-4 h-4 text-purple-500" />
          </div>
          <p className="text-2xl font-bold text-purple-600">{approved}</p>
          <p className="text-[11px] text-slate-400 mt-0.5">Cryptographically certified</p>
        </div>

        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs col-span-2 lg:col-span-1">
          <div className="flex items-center justify-between text-rose-600 mb-2">
            <span className="text-xs font-medium">Critical Safety Flags</span>
            <AlertTriangle className="w-4 h-4 text-rose-500" />
          </div>
          <p className="text-2xl font-bold text-rose-600">{criticalCount}</p>
          <p className="text-[11px] text-slate-400 mt-0.5">Quarantined for recycling</p>
        </div>
      </div>

      {/* Active Screening Rig & Queue Overview */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Screening Rig State */}
        <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <span className="text-xs font-bold text-slate-900 uppercase">Screening Rig Status</span>
              <span className="text-xs font-semibold px-2 py-0.5 rounded bg-emerald-50 text-emerald-800 border border-emerald-200">
                {status}
              </span>
            </div>

            <div className="mt-4 space-y-3 text-xs text-slate-600">
              <div>
                <span className="text-slate-400">Current Stream Source:</span>
                <p className="font-bold text-slate-900">{sourceMeta.name}</p>
              </div>

              <div>
                <span className="text-slate-400">Sampling Rate:</span>
                <p className="font-semibold text-slate-800">1.0 Hz (1 sample / sec) • 90s Duration</p>
              </div>

              <div>
                <span className="text-slate-400">Screening Channels:</span>
                <p className="font-semibold text-slate-800">Voltage (V), Current (A), Thermistor (°C)</p>
              </div>
            </div>
          </div>

          <button
            onClick={() => navigate('/tech/screening')}
            className="mt-6 w-full py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg text-xs font-semibold transition-colors flex items-center justify-center gap-1.5"
          >
            <span>Launch 90s Screening Bench</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>

        {/* Priority Screening Queue */}
        <div className="lg:col-span-2 bg-white rounded-xl border border-slate-200 p-5 shadow-xs">
          <div className="flex items-center justify-between pb-3 border-b border-slate-100 mb-3">
            <div>
              <h2 className="text-sm font-bold text-slate-900">Priority Diagnostic Queue</h2>
              <p className="text-xs text-slate-500">Batteries registered by owners awaiting electrochemical profiling</p>
            </div>
            <button
              onClick={() => navigate('/tech/queue')}
              className="text-xs font-semibold text-emerald-600 hover:text-emerald-700 flex items-center gap-1"
            >
              <span>View All</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>

          <div className="divide-y divide-slate-100">
            {batteries.slice(0, 4).map((b) => (
              <div key={b.battery_id} className="py-3 flex items-center justify-between gap-3">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-xs text-slate-900">{b.battery_id}</span>
                    <span className="text-[10px] px-1.5 py-0.5 rounded font-semibold bg-slate-100 text-slate-700">
                      {b.chemistry} • {b.rated_capacity_ah} Ah
                    </span>
                    <span className={`text-[10px] px-2 py-0.5 rounded-full font-semibold ${
                      b.status === 'Approved' ? 'bg-purple-100 text-purple-800' :
                      (b.status === 'Assessed' ? 'bg-blue-100 text-blue-800' : 'bg-amber-100 text-amber-800')
                    }`}>
                      {b.status}
                    </span>
                  </div>
                  <p className="text-[11px] text-slate-400 mt-0.5">
                    Owner: {b.owner_name} • {b.vehicle_model}
                  </p>
                </div>

                <div>
                  {b.status === 'Awaiting Screening' ? (
                    <button
                      onClick={() => navigate(`/tech/screening?battery_id=${b.battery_id}`)}
                      className="px-3 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg text-xs font-semibold transition-colors"
                    >
                      Start Screening
                    </button>
                  ) : (
                    <button
                      onClick={() => navigate(`/tech/approval?battery_id=${b.battery_id}`)}
                      className="px-3 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg text-xs font-semibold transition-colors border border-slate-200"
                    >
                      View Report
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

