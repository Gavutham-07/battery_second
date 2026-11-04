import React, { useState } from 'react';
import { useDataSource } from '../context/DataSourceContext';
import { Database, Cpu, PlayCircle, Radio, AlertTriangle, CheckCircle, ChevronDown, RefreshCw } from 'lucide-react';

export default function DataSourceSelector({ compact = false }) {
  const {
    selectedSource,
    setSelectedSource,
    testProfile,
    setTestProfile,
    status,
    sourceMeta,
    DATA_SOURCES,
    TEST_PROFILES,
    hardwareDetected,
    setHardwareDetected
  } = useDataSource();

  const [isOpen, setIsOpen] = useState(false);

  const getSourceIcon = (id) => {
    switch (id) {
      case 'live_hardware':
        return <Cpu className="w-4 h-4" />;
      case 'replay_recorded':
        return <PlayCircle className="w-4 h-4" />;
      case 'lab_dataset':
        return <Database className="w-4 h-4" />;
      case 'virtual_circuit':
      default:
        return <Radio className="w-4 h-4" />;
    }
  };

  const getStatusBadge = (st) => {
    switch (st) {
      case 'Connected':
        return <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium bg-emerald-100 text-emerald-800 border border-emerald-200"><CheckCircle className="w-3 h-3 text-emerald-600" /> Connected</span>;
      case 'Disconnected':
        return <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium bg-amber-100 text-amber-800 border border-amber-200"><AlertTriangle className="w-3 h-3 text-amber-600" /> Disconnected</span>;
      case 'Replay Active':
        return <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800 border border-blue-200"><PlayCircle className="w-3 h-3 text-blue-600" /> Replay Active</span>;
      case 'Simulated':
      default:
        return <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium bg-slate-100 text-slate-700 border border-slate-300"><Radio className="w-3 h-3 text-emerald-600" /> Simulated</span>;
    }
  };

  return (
    <div className="relative inline-block text-left">
      <div className="flex items-center gap-2">
        <button
          type="button"
          onClick={() => setIsOpen(!isOpen)}
          className={`inline-flex items-center justify-between gap-2 px-3 py-1.5 text-xs font-medium rounded-lg border bg-white shadow-sm hover:bg-slate-50 transition-colors ${
            selectedSource === 'live_hardware' && !hardwareDetected ? 'border-amber-300' : 'border-slate-300'
          }`}
        >
          <div className="flex items-center gap-2">
            <span className="text-slate-500">{getSourceIcon(selectedSource)}</span>
            <span className="font-semibold text-slate-800">{sourceMeta.name}</span>
          </div>
          <div className="flex items-center gap-1.5 ml-2">
            {getStatusBadge(status)}
            <ChevronDown className="w-3.5 h-3.5 text-slate-400" />
          </div>
        </button>

        {/* Profile indicator if in Virtual Circuit */}
        {selectedSource === 'virtual_circuit' && !compact && (
          <div className="hidden lg:flex items-center text-xs text-slate-500 bg-slate-100 px-2 py-1 rounded-md border border-slate-200">
            <span className="text-slate-400 mr-1.5">Profile:</span>
            <span className="font-medium text-slate-700 capitalize">{testProfile.replace('_', ' ')}</span>
          </div>
        )}
      </div>

      {isOpen && (
        <>
          <div className="fixed inset-0 z-40" onClick={() => setIsOpen(false)} />
          <div className="origin-top-right absolute right-0 mt-2 w-80 rounded-xl shadow-lg bg-white ring-1 ring-black ring-opacity-5 divide-y divide-slate-100 z-50">
            <div className="p-3 bg-slate-50 rounded-t-xl">
              <p className="text-xs font-semibold text-slate-700 uppercase tracking-wider">Global Data Source</p>
              <p className="text-xs text-slate-500 mt-0.5">Controls telemetry stream across all portals</p>
            </div>

            <div className="py-1">
              {DATA_SOURCES.map((source) => (
                <button
                  key={source.id}
                  onClick={() => {
                    setSelectedSource(source.id);
                    setIsOpen(false);
                  }}
                  className={`w-full text-left px-3.5 py-2.5 text-xs hover:bg-slate-50 flex items-start justify-between transition-colors ${
                    selectedSource === source.id ? 'bg-emerald-50/50' : ''
                  }`}
                >
                  <div className="flex items-start gap-2.5">
                    <span className="mt-0.5 text-slate-600">{getSourceIcon(source.id)}</span>
                    <div>
                      <p className={`font-medium ${selectedSource === source.id ? 'text-emerald-900 font-semibold' : 'text-slate-800'}`}>
                        {source.name}
                      </p>
                      <p className="text-slate-500 text-[11px] mt-0.5 leading-snug">{source.description}</p>
                    </div>
                  </div>
                </button>
              ))}
            </div>

            {/* Test Profile Selection for Simulated / Replay modes */}
            {(selectedSource === 'virtual_circuit' || selectedSource === 'replay_recorded') && (
              <div className="p-3 bg-slate-50">
                <label className="block text-[11px] font-semibold text-slate-600 uppercase mb-1.5">
                  Screening Test Profile
                </label>
                <div className="space-y-1">
                  {TEST_PROFILES.map((p) => (
                    <button
                      key={p.id}
                      onClick={() => setTestProfile(p.id)}
                      className={`w-full text-left px-2.5 py-1.5 rounded text-xs flex items-center justify-between border ${
                        testProfile === p.id
                          ? 'border-emerald-500 bg-white text-emerald-800 font-medium shadow-xs'
                          : 'border-slate-200 bg-slate-100 text-slate-600 hover:bg-white'
                      }`}
                    >
                      <span>{p.name}</span>
                      {testProfile === p.id && <CheckCircle className="w-3 h-3 text-emerald-600" />}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {/* Hardware Status Note */}
            {selectedSource === 'live_hardware' && (
              <div className="p-3 bg-amber-50 rounded-b-xl border-t border-amber-100">
                <div className="flex items-start gap-2 text-xs text-amber-800">
                  <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
                  <div>
                    <p className="font-semibold">Hardware Telemetry Rig</p>
                    <p className="text-[11px] text-amber-700 mt-0.5">
                      {hardwareDetected
                        ? 'ESP32 serial connection detected on COM port (115200 baud).'
                        : 'No ESP32 detected on USB/COM port. To run simulated screening, switch to Virtual Circuit.'}
                    </p>
                    <button
                      onClick={() => setHardwareDetected(!hardwareDetected)}
                      className="mt-2 text-[11px] text-amber-900 font-semibold underline hover:text-amber-950 flex items-center gap-1"
                    >
                      <RefreshCw className="w-3 h-3" />
                      {hardwareDetected ? 'Simulate Hardware Disconnect' : 'Simulate ESP32 Plug-In'}
                    </button>
                  </div>
                </div>
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
}

