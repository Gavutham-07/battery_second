import React from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import {
  LayoutDashboard,
  Layers,
  MapPin,
  Sparkles,
  Coins,
  Leaf,
  QrCode,
  LogOut,
  ListOrdered,
  Activity,
  Sliders,
  CheckCircle2,
  BarChart3,
  Boxes,
  ShieldCheck
} from 'lucide-react';

const OWNER_NAV = [
  { name: 'Dashboard', path: '/owner', icon: LayoutDashboard, exact: true },
  { name: 'My Batteries', path: '/owner/batteries', icon: Layers },
  { name: 'Find Service Centers', path: '/owner/centers', icon: MapPin },
  { name: 'Recommendations', path: '/owner/recommendations', icon: Sparkles },
  { name: 'Exchange Offers', path: '/owner/offers', icon: Coins },
  { name: 'My Environmental Impact', path: '/owner/impact', icon: Leaf },
  { name: 'My Battery Passport', path: '/owner/passport', icon: QrCode },
];

const TECH_NAV = [
  { name: 'Dashboard', path: '/tech', icon: LayoutDashboard, exact: true },
  { name: 'Battery Queue', path: '/tech/queue', icon: ListOrdered },
  { name: 'Battery Screening', path: '/tech/screening', icon: Activity },
  { name: 'What-If Simulator', path: '/tech/what-if', icon: Sliders },
  { name: 'Approval & Passport', path: '/tech/approval', icon: CheckCircle2 },
];

const RECYCLER_NAV = [
  { name: 'Impact Summary', path: '/recycler', icon: BarChart3, exact: true },
  { name: 'Batch Sorting', path: '/recycler/batches', icon: Layers },
  { name: 'Battery Pack Grouping', path: '/recycler/pack-grouping', icon: Boxes },
];

export default function Sidebar({ portal = 'owner' }) {
  const navigate = useNavigate();

  let navItems = OWNER_NAV;
  let portalTitle = 'EV Owner';

  if (portal === 'tech') {
    navItems = TECH_NAV;
    portalTitle = 'Technician Station';
  } else if (portal === 'recycler') {
    navItems = RECYCLER_NAV;
    portalTitle = 'Recycler Hub';
  }

  return (
    <aside className="w-64 bg-slate-900 border-r border-slate-800 flex flex-col shrink-0 min-h-[calc(100vh-4rem)]">
      {/* Sidebar Header / Portal Tag */}
      <div className="p-4 border-b border-slate-800/80">
        <p className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">Stakeholder Portal</p>
        <p className="text-sm font-bold text-white mt-0.5">{portalTitle}</p>
      </div>

      {/* Navigation Links */}
      <nav className="flex-1 p-3 space-y-1">
        {navItems.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.path}
              to={item.path}
              end={item.exact}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2.5 rounded-lg text-xs font-medium transition-all ${
                  isActive
                    ? 'bg-emerald-600/20 text-emerald-400 border border-emerald-500/30'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
                }`
              }
            >
              <Icon className="w-4 h-4 shrink-0" />
              <span>{item.name}</span>
            </NavLink>
          );
        })}
      </nav>

      {/* Public QR Verification Shortcut & Logout */}
      <div className="p-3 border-t border-slate-800 space-y-1">
        <NavLink
          to="/verify"
          className="flex items-center gap-3 px-3 py-2 rounded-lg text-xs font-medium text-slate-400 hover:text-emerald-400 hover:bg-slate-800 transition-colors"
        >
          <ShieldCheck className="w-4 h-4 text-emerald-500" />
          <span>Public QR Verify</span>
        </NavLink>

        <button
          onClick={() => navigate('/')}
          className="w-full flex items-center gap-3 px-3 py-2 rounded-lg text-xs font-medium text-rose-400/80 hover:text-rose-300 hover:bg-rose-950/20 transition-colors"
        >
          <LogOut className="w-4 h-4" />
          <span>Exit Portal</span>
        </button>
      </div>
    </aside>
  );
}

