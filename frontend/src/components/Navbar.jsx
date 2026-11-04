import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import DataSourceSelector from './DataSourceSelector';
import { BatteryCharging, LogOut, ShieldCheck, UserCheck, Wrench, Recycle } from 'lucide-react';

export default function Navbar({ role = 'owner', roleTitle = 'EV Owner Portal' }) {
  const navigate = useNavigate();

  const getRoleIcon = () => {
    switch (role) {
      case 'tech':
        return <Wrench className="w-4 h-4 text-emerald-600" />;
      case 'recycler':
        return <Recycle className="w-4 h-4 text-emerald-600" />;
      case 'owner':
      default:
        return <UserCheck className="w-4 h-4 text-emerald-600" />;
    }
  };

  return (
    <header className="sticky top-0 z-30 bg-white border-b border-slate-200">
      <div className="px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        {/* Brand & Portal Title */}
        <div className="flex items-center gap-4">
          <Link to="/" className="flex items-center gap-2.5 group">
            <div className="w-9 h-9 rounded-lg bg-emerald-600 flex items-center justify-center text-white shadow-sm group-hover:bg-emerald-700 transition-colors">
              <BatteryCharging className="w-5 h-5" />
            </div>
            <div>
              <span className="text-lg font-bold text-slate-900 tracking-tight">Re<span className="text-emerald-600">Volt</span></span>
              <span className="hidden sm:inline-block ml-2 text-xs font-medium text-slate-400 border-l border-slate-200 pl-2">
                EV Battery Second-Life
              </span>
            </div>
          </Link>

          <div className="hidden md:flex items-center gap-2 pl-3 border-l border-slate-200">
            <span className="p-1 rounded bg-emerald-50 border border-emerald-200">
              {getRoleIcon()}
            </span>
            <span className="text-xs font-semibold text-slate-700 uppercase tracking-wide">
              {roleTitle}
            </span>
          </div>
        </div>

        {/* Global Data Source Selector + Actions */}
        <div className="flex items-center gap-3">
          <DataSourceSelector />

          <button
            onClick={() => navigate('/')}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-slate-600 hover:text-slate-900 bg-slate-100 hover:bg-slate-200 rounded-lg transition-colors border border-slate-200"
            title="Switch stakeholder portal / Return to Landing"
          >
            <LogOut className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">Portals</span>
          </button>
        </div>
      </div>
    </header>
  );
}

