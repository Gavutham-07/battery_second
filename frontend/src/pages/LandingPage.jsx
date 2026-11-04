import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import DataSourceSelector from '../components/DataSourceSelector';
import { useBatteryStore } from '../context/BatteryContext';
import {
  BatteryCharging,
  User,
  Wrench,
  Recycle,
  ShieldCheck,
  ArrowRight,
  Sparkles,
  Layers,
  Activity,
  Boxes,
  Search
} from 'lucide-react';

export default function LandingPage() {
  const navigate = useNavigate();
  const { batteries } = useBatteryStore();
  const [searchId, setSearchId] = useState('');

  const handleVerifySearch = (e) => {
    e.preventDefault();
    if (searchId.trim()) {
      navigate(`/verify/${searchId.trim().toUpperCase()}`);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col">
      {/* Top Header */}
      <header className="bg-white border-b border-slate-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-9 h-9 rounded-lg bg-emerald-600 flex items-center justify-center text-white shadow-sm">
              <BatteryCharging className="w-5 h-5" />
            </div>
            <div>
              <span className="text-xl font-bold text-slate-900 tracking-tight">Re<span className="text-emerald-600">Volt</span></span>
              <span className="hidden sm:inline-block ml-2 text-xs font-medium text-slate-500 border-l border-slate-200 pl-2">
                EV Battery Second-Life Platform
              </span>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={() => navigate('/classic')}
              className="hidden md:inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-slate-700 bg-slate-100 hover:bg-slate-200 rounded-lg transition-colors border border-slate-200"
              title="Switch to Classic 4-Stakeholder Tabbed View"
            >
              <Layers className="w-3.5 h-3.5 text-slate-500" />
              <span>Classic Console</span>
            </button>
            <DataSourceSelector />
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="py-12 md:py-16 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto w-full text-center">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-50 border border-emerald-200 text-xs font-semibold text-emerald-800 mb-4">
          <Sparkles className="w-3.5 h-3.5 text-emerald-600" />
          <span>AI-Powered 90-Second Fast Battery Screening & Passport System</span>
        </div>
        <h1 className="text-3xl sm:text-5xl font-extrabold text-slate-900 tracking-tight max-w-4xl mx-auto leading-tight">
          Maximizing EV Battery Second-Life Value Through Intelligent Diagnostic Passports
        </h1>
        <p className="mt-4 text-base sm:text-lg text-slate-600 max-w-2xl mx-auto">
          Connect EV owners, certified service technicians, and recyclers on a single verified platform. Evaluate SOH, prevent thermal runaway, and route cells to optimal second-life applications.
        </p>

        {/* Global Public Passport Verification Bar */}
        <div className="mt-8 max-w-md mx-auto">
          <form onSubmit={handleVerifySearch} className="flex items-center gap-2 p-1.5 bg-white rounded-xl border border-slate-300 shadow-sm focus-within:border-emerald-500 focus-within:ring-1 focus-within:ring-emerald-500">
            <Search className="w-4 h-4 text-slate-400 ml-2" />
            <input
              type="text"
              value={searchId}
              onChange={(e) => setSearchId(e.target.value)}
              placeholder="Verify Battery Passport (e.g. BAT-103)"
              className="w-full text-xs sm:text-sm bg-transparent border-0 focus:ring-0 text-slate-800 placeholder-slate-400"
            />
            <button
              type="submit"
              className="px-3.5 py-2 text-xs font-semibold text-white bg-emerald-600 hover:bg-emerald-700 rounded-lg transition-colors whitespace-nowrap"
            >
              Verify
            </button>
          </form>
          <p className="text-[11px] text-slate-500 mt-1.5">
            Public verification does not require an account. Try <span onClick={() => setSearchId('BAT-103')} className="text-emerald-700 font-semibold cursor-pointer underline">BAT-103</span>
          </p>
        </div>
      </section>

      {/* Stakeholder Role Portals */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pb-16 flex-1 w-full">
        <div className="text-center mb-8">
          <h2 className="text-xl font-bold text-slate-900">Select Stakeholder Portal</h2>
          <p className="text-xs text-slate-500 mt-1">Enter your dedicated workspace with full end-to-end data continuity</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* EV Owner Portal Card */}
          <div className="bg-white rounded-2xl border border-slate-200 p-6 flex flex-col justify-between shadow-xs hover:border-emerald-500/50 hover:shadow-md transition-all">
            <div>
              <div className="w-12 h-12 rounded-xl bg-blue-50 border border-blue-200 flex items-center justify-center text-blue-700 mb-4">
                <User className="w-6 h-6" />
              </div>
              <span className="text-[11px] font-bold uppercase tracking-wider text-blue-700 bg-blue-50 px-2 py-0.5 rounded">
                Portal 1
              </span>
              <h3 className="text-lg font-bold text-slate-900 mt-2">EV Owner Portal</h3>
              <p className="text-xs text-slate-600 mt-2 leading-relaxed">
                Register retired vehicle battery packs, check assessment results, locate certified diagnostic hubs, express reuse/sell preferences, and view your battery's CO₂ savings.
              </p>

              <div className="mt-4 pt-4 border-t border-slate-100 space-y-2">
                <div className="flex items-center gap-2 text-xs text-slate-600">
                  <Layers className="w-3.5 h-3.5 text-emerald-600" />
                  <span>Battery Registration & Status</span>
                </div>
                <div className="flex items-center gap-2 text-xs text-slate-600">
                  <Sparkles className="w-3.5 h-3.5 text-emerald-600" />
                  <span>AI Second-Life Recommendations</span>
                </div>
                <div className="flex items-center gap-2 text-xs text-slate-600">
                  <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" />
                  <span>Verified QR Passport & Exchange Offers</span>
                </div>
              </div>
            </div>

            <button
              onClick={() => navigate('/owner')}
              className="mt-6 w-full flex items-center justify-center gap-2 px-4 py-2.5 bg-slate-900 hover:bg-slate-800 text-white rounded-xl text-xs font-semibold transition-colors"
            >
              <span>Enter Owner Portal</span>
              <ArrowRight className="w-4 h-4 text-emerald-400" />
            </button>
          </div>

          {/* Service Center Technician Portal Card */}
          <div className="bg-white rounded-2xl border-2 border-emerald-600/40 p-6 flex flex-col justify-between shadow-sm hover:border-emerald-600 hover:shadow-md transition-all relative">
            <div className="absolute -top-3 right-6 bg-emerald-600 text-white text-[10px] font-bold px-2.5 py-0.5 rounded-full uppercase tracking-wider shadow-xs">
              Primary Diagnostic Station
            </div>
            <div>
              <div className="w-12 h-12 rounded-xl bg-emerald-50 border border-emerald-200 flex items-center justify-center text-emerald-700 mb-4">
                <Wrench className="w-6 h-6" />
              </div>
              <span className="text-[11px] font-bold uppercase tracking-wider text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded">
                Portal 2
              </span>
              <h3 className="text-lg font-bold text-slate-900 mt-2">Technician Portal</h3>
              <p className="text-xs text-slate-600 mt-2 leading-relaxed">
                Execute guided 90-second screening tests, observe live Voltage/Current/Temperature telemetry curves, run What-If simulations, and mint cryptographically verified QR passports.
              </p>

              <div className="mt-4 pt-4 border-t border-slate-100 space-y-2">
                <div className="flex items-center gap-2 text-xs text-slate-600">
                  <Activity className="w-3.5 h-3.5 text-emerald-600" />
                  <span>90s Live Screening & Waveforms</span>
                </div>
                <div className="flex items-center gap-2 text-xs text-slate-600">
                  <Sparkles className="w-3.5 h-3.5 text-emerald-600" />
                  <span>SOH & Thermal Runaway Detection</span>
                </div>
                <div className="flex items-center gap-2 text-xs text-slate-600">
                  <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" />
                  <span>Approve & Mint SHA-256 Passports</span>
                </div>
              </div>
            </div>

            <button
              onClick={() => navigate('/tech')}
              className="mt-6 w-full flex items-center justify-center gap-2 px-4 py-2.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl text-xs font-semibold transition-colors shadow-sm"
            >
              <span>Enter Technician Portal</span>
              <ArrowRight className="w-4 h-4 text-white" />
            </button>
          </div>

          {/* Recycler Portal Card */}
          <div className="bg-white rounded-2xl border border-slate-200 p-6 flex flex-col justify-between shadow-xs hover:border-emerald-500/50 hover:shadow-md transition-all">
            <div>
              <div className="w-12 h-12 rounded-xl bg-amber-50 border border-amber-200 flex items-center justify-center text-amber-700 mb-4">
                <Recycle className="w-6 h-6" />
              </div>
              <span className="text-[11px] font-bold uppercase tracking-wider text-amber-700 bg-amber-50 px-2 py-0.5 rounded">
                Portal 3
              </span>
              <h3 className="text-lg font-bold text-slate-900 mt-2">Recycler Portal</h3>
              <p className="text-xs text-slate-600 mt-2 leading-relaxed">
                Sort assessed battery inventory into Reuse, Repurpose, or Material Recovery batches with automated safety lockouts. Build balanced secondary battery packs from cell inventory.
              </p>

              <div className="mt-4 pt-4 border-t border-slate-100 space-y-2">
                <div className="flex items-center gap-2 text-xs text-slate-600">
                  <Layers className="w-3.5 h-3.5 text-emerald-600" />
                  <span>Automated Batch Sorting</span>
                </div>
                <div className="flex items-center gap-2 text-xs text-slate-600">
                  <Boxes className="w-3.5 h-3.5 text-emerald-600" />
                  <span>Cell Pack Compatibility Grouping</span>
                </div>
                <div className="flex items-center gap-2 text-xs text-slate-600">
                  <Activity className="w-3.5 h-3.5 text-emerald-600" />
                  <span>Facility CO₂ & Waste Diverted Metrics</span>
                </div>
              </div>
            </div>

            <button
              onClick={() => navigate('/recycler')}
              className="mt-6 w-full flex items-center justify-center gap-2 px-4 py-2.5 bg-slate-900 hover:bg-slate-800 text-white rounded-xl text-xs font-semibold transition-colors"
            >
              <span>Enter Recycler Portal</span>
              <ArrowRight className="w-4 h-4 text-emerald-400" />
            </button>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-white border-t border-slate-200 py-6 text-center text-xs text-slate-500">
        <p>ReVolt Smart EV Battery Second-Life Platform — Team 4-Member Architecture Integration</p>
        <p className="mt-1 text-[11px] text-slate-400">
          Hardware (ESP32) • Backend (FastAPI / MongoDB) • AI (XGBoost / Safety Diagnostics) • Frontend (React / Tailwind)
        </p>
      </footer>
    </div>
  );
}
