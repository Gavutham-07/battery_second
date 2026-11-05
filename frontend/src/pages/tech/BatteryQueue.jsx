import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useBatteryStore } from '../../context/BatteryContext';
import {
  ListOrdered,
  Search,
  Filter,
  ArrowRight,
  Clock,
  CheckCircle2,
  AlertTriangle,
  PlayCircle,
  FileText
} from 'lucide-react';

export default function BatteryQueue() {
  const navigate = useNavigate();
  const { batteries } = useBatteryStore();

  const [filterStatus, setFilterStatus] = useState('ALL');
  const [searchTerm, setSearchTerm] = useState('');

  const filteredBatteries = batteries.filter(b => {
    const matchesSearch = b.battery_id.toLowerCase().includes(searchTerm.toLowerCase()) ||
      b.chemistry.toLowerCase().includes(searchTerm.toLowerCase()) ||
      b.vehicle_model?.toLowerCase().includes(searchTerm.toLowerCase());

    if (filterStatus === 'ALL') return matchesSearch;
    return matchesSearch && b.status === filterStatus;
  });

  const handleStartScreening = (battery_id) => {
    // Navigate to Battery Screening page with battery_id pre-loaded in URL param!
    navigate(`/tech/screening?battery_id=${battery_id}`);
  };

  const handleViewAssessment = (battery_id) => {
    navigate(`/tech/approval?battery_id=${battery_id}`);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-xl font-bold text-slate-900">Technician Diagnostic Intake Queue</h1>
        <p className="text-xs text-slate-500 mt-1">
          Registered EV batteries in queue for electrochemical testing. Select "Start Screening" to auto-load the battery into the diagnostic bench.
        </p>
      </div>

      {/* Filter and Search Bar */}
      <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs flex flex-col sm:flex-row items-center justify-between gap-3">
        <div className="relative flex-1 w-full sm:max-w-xs">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Search battery ID, chemistry, model..."
            className="w-full pl-9 pr-3 py-1.5 text-xs rounded-lg border border-slate-300 focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 bg-white text-slate-900"
          />
        </div>

        <div className="flex items-center gap-2 w-full sm:w-auto overflow-x-auto">
          {['ALL', 'Awaiting Screening', 'Assessed', 'Approved'].map((status) => (
            <button
              key={status}
              onClick={() => setFilterStatus(status)}
              className={`px-3 py-1.5 text-xs font-semibold rounded-lg transition-colors whitespace-nowrap ${
                filterStatus === status
                  ? 'bg-slate-900 text-white'
                  : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
              }`}
            >
              {status}
            </button>
          ))}
        </div>
      </div>

      {/* Table of Batteries */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-xs overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 border-b border-slate-200 text-slate-600 uppercase font-semibold">
              <tr>
                <th className="px-5 py-3.5">Battery ID</th>
                <th className="px-5 py-3.5">Chemistry</th>
                <th className="px-5 py-3.5">Rated Capacity</th>
                <th className="px-5 py-3.5">Registration Date</th>
                <th className="px-5 py-3.5">Status</th>
                <th className="px-5 py-3.5 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {filteredBatteries.map((b) => (
                <tr key={b.battery_id} className="hover:bg-slate-50/70 transition-colors">
                  <td className="px-5 py-4">
                    <span className="font-bold text-slate-900 text-sm">{b.battery_id}</span>
                    <p className="text-[11px] text-slate-400 mt-0.5">{b.vehicle_model || 'Vehicle Pack'}</p>
                  </td>

                  <td className="px-5 py-4">
                    <span className="font-semibold px-2 py-0.5 rounded bg-slate-100 text-slate-700 border border-slate-200">
                      {b.chemistry}
                    </span>
                  </td>

                  <td className="px-5 py-4 font-medium text-slate-800">
                    {b.rated_capacity_ah} Ah
                  </td>

                  <td className="px-5 py-4 text-slate-500">
                    {new Date(b.registration_date).toLocaleDateString()}
                  </td>

                  <td className="px-5 py-4">
                    <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-semibold ${
                      b.status === 'Approved' ? 'bg-purple-100 text-purple-800' :
                      (b.status === 'Assessed' ? 'bg-blue-100 text-blue-800' : 'bg-amber-100 text-amber-800')
                    }`}>
                      {b.status === 'Approved' ? <CheckCircle2 className="w-3 h-3 text-purple-600" /> :
                       (b.status === 'Assessed' ? <FileText className="w-3 h-3 text-blue-600" /> : <Clock className="w-3 h-3 text-amber-600" />)}
                      <span>{b.status}</span>
                    </span>
                  </td>

                  <td className="px-5 py-4 text-right">
                    {b.status === 'Awaiting Screening' && (
                      <button
                        onClick={() => handleStartScreening(b.battery_id)}
                        className="inline-flex items-center gap-1.5 px-3.5 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg text-xs font-semibold shadow-xs transition-colors"
                      >
                        <PlayCircle className="w-3.5 h-3.5" />
                        <span>Start Screening</span>
                      </button>
                    )}

                    {b.status === 'Testing in Progress' && (
                      <button
                        onClick={() => handleStartScreening(b.battery_id)}
                        className="inline-flex items-center gap-1.5 px-3.5 py-1.5 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-xs font-semibold shadow-xs transition-colors"
                      >
                        <span>View Test</span>
                      </button>
                    )}

                    {(b.status === 'Assessed' || b.status === 'Approved') && (
                      <button
                        onClick={() => handleViewAssessment(b.battery_id)}
                        className="inline-flex items-center gap-1.5 px-3.5 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg text-xs font-semibold border border-slate-300 transition-colors"
                      >
                        <FileText className="w-3.5 h-3.5 text-slate-500" />
                        <span>View Assessment</span>
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

