import React, { useState, useEffect, useRef } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { useBatteryStore } from '../../context/BatteryContext';
import { useDataSource } from '../../context/DataSourceContext';
import { generateTelemetryPoint } from '../../services/dataSimulation';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid
} from 'recharts';
import {
  Activity,
  Play,
  Square,
  RotateCcw,
  ShieldAlert,
  ShieldCheck,
  CheckCircle2,
  AlertTriangle,
  ArrowRight,
  Info,
  Clock,
  Radio,
  Sliders,
  ChevronRight,
  Zap,
  Thermometer,
  Gauge
} from 'lucide-react';

export default function BatteryScreening() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { batteries, completeScreeningAndAssess, getBattery } = useBatteryStore();
  const {
    selectedSource,
    testProfile,
    setTestProfile,
    status: sourceStatus,
    sourceMeta,
    hardwareDetected
  } = useDataSource();

  // Selected battery (pre-loaded from URL param if available)
  const initialBatteryId = searchParams.get('battery_id') || batteries[0]?.battery_id || '';
  const [selectedBatteryId, setSelectedBatteryId] = useState(initialBatteryId);

  // Active Screening Test State
  const [isTesting, setIsTesting] = useState(false);
  const [isCompleted, setIsCompleted] = useState(false);
  const [currentSecond, setCurrentSecond] = useState(0);
  const [telemetryHistory, setTelemetryHistory] = useState([]);
  const [fastMode, setFastMode] = useState(false); // 5x speed for rapid demo presentations
  const [assessmentResult, setAssessmentResult] = useState(null);
  const [errorMessage, setErrorMessage] = useState('');

  const timerRef = useRef(null);

  const currentBattery = getBattery(selectedBatteryId) || batteries[0];

  // Sync if battery changes
  useEffect(() => {
    if (currentBattery?.telemetry && currentBattery.telemetry.length > 0 && currentBattery.status !== 'Awaiting Screening') {
      setTelemetryHistory(currentBattery.telemetry);
      setIsCompleted(true);
      setAssessmentResult(currentBattery);
    } else {
      setTelemetryHistory([]);
      setIsCompleted(false);
      setAssessmentResult(null);
      setCurrentSecond(0);
    }
  }, [selectedBatteryId]);

  // Clean timer on unmount
  useEffect(() => {
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, []);

  // Live polling / stream simulation loop
  useEffect(() => {
    if (isTesting) {
      const intervalMs = fastMode ? 150 : 1000;
      timerRef.current = setInterval(() => {
        setCurrentSecond((prevSec) => {
          const nextSec = prevSec + 1;
          const point = generateTelemetryPoint(nextSec, testProfile, selectedSource);
          setTelemetryHistory((prevHistory) => [...prevHistory, point]);

          if (nextSec >= 90) {
            // Complete Test at 90s
            clearInterval(timerRef.current);
            setIsTesting(false);
            setIsCompleted(true);
            finishTest([...telemetryHistory, point]);
            return 90;
          }
          return nextSec;
        });
      }, intervalMs);
    } else {
      if (timerRef.current) clearInterval(timerRef.current);
    }

    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [isTesting, fastMode, testProfile, selectedSource]);

  const handleStartTest = () => {
    setErrorMessage('');
    if (selectedSource === 'live_hardware' && !hardwareDetected) {
      setErrorMessage('ESP32 Live Hardware is not connected on serial COM/USB. Please switch data source to "Virtual Battery Circuit" or toggle hardware simulation in the top-right selector.');
      return;
    }

    setIsTesting(true);
    setIsCompleted(false);
    setCurrentSecond(0);
    setTelemetryHistory([]);
    setAssessmentResult(null);
  };

  const handleStopTest = () => {
    setIsTesting(false);
    if (timerRef.current) clearInterval(timerRef.current);
  };

  const handleResetTest = () => {
    setIsTesting(false);
    setIsCompleted(false);
    setCurrentSecond(0);
    setTelemetryHistory([]);
    setAssessmentResult(null);
    setErrorMessage('');
  };

  const finishTest = (finalTelemetry) => {
    const assessed = completeScreeningAndAssess(selectedBatteryId, finalTelemetry, testProfile);
    setAssessmentResult(assessed);
  };

  // Latest Telemetry Reading
  const latestPoint = telemetryHistory[telemetryHistory.length - 1] || {
    voltage: 3.35,
    current: 10.0,
    temperature: 25.0
  };

  return (
    <div className="space-y-6">
      {/* Step 1: Battery Confirmation Banner */}
      <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="w-6 h-6 rounded-full bg-emerald-600 text-white flex items-center justify-center text-xs font-bold">1</span>
            <h1 className="text-lg font-bold text-slate-900">Step 1: Confirm Screening Battery</h1>
          </div>
          <p className="text-xs text-slate-500 mt-0.5 ml-8">
            Pre-loaded from queue. Confirm registered parameters before starting electrochemical excitation.
          </p>
        </div>

        <div className="flex items-center gap-3 ml-8 md:ml-0">
          <label className="text-xs font-semibold text-slate-600">Select Battery:</label>
          <select
            value={selectedBatteryId}
            disabled={isTesting}
            onChange={(e) => {
              setSelectedBatteryId(e.target.value);
              handleResetTest();
            }}
            className="text-xs font-bold px-3 py-1.5 rounded-lg border border-slate-300 bg-white focus:border-emerald-500"
          >
            {batteries.map((b) => (
              <option key={b.battery_id} value={b.battery_id}>
                {b.battery_id} — {b.chemistry} ({b.rated_capacity_ah} Ah) — {b.status}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Selected Battery Specs Card */}
      {currentBattery && (
        <div className="bg-slate-900 text-white rounded-xl p-4 flex flex-wrap items-center justify-between gap-4 text-xs">
          <div>
            <span className="text-slate-400 font-medium">Battery ID:</span>
            <p className="text-base font-bold text-white">{currentBattery.battery_id}</p>
          </div>
          <div>
            <span className="text-slate-400 font-medium">Chemistry:</span>
            <p className="font-semibold text-emerald-400">{currentBattery.chemistry}</p>
          </div>
          <div>
            <span className="text-slate-400 font-medium">Rated Capacity:</span>
            <p className="font-semibold text-white">{currentBattery.rated_capacity_ah} Ah</p>
          </div>
          <div>
            <span className="text-slate-400 font-medium">Vehicle / Owner:</span>
            <p className="font-semibold text-white">{currentBattery.vehicle_model} ({currentBattery.owner_name})</p>
          </div>
          <div>
            <span className="text-slate-400 font-medium">Data Stream:</span>
            <p className="font-semibold text-emerald-400">{sourceMeta.name}</p>
          </div>
        </div>
      )}

      {errorMessage && (
        <div className="p-4 bg-rose-50 border border-rose-200 rounded-xl flex items-center justify-between text-xs text-rose-800">
          <div className="flex items-center gap-2">
            <AlertTriangle className="w-5 h-5 text-rose-600 shrink-0" />
            <span>{errorMessage}</span>
          </div>
          <button onClick={() => setErrorMessage('')} className="text-rose-700 font-bold ml-2">✕</button>
        </div>
      )}

      {/* Step 2: Test Controls & Profile Selection */}
      <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
          <div className="flex items-center gap-2">
            <span className="w-6 h-6 rounded-full bg-emerald-600 text-white flex items-center justify-center text-xs font-bold">2</span>
            <h2 className="text-sm font-bold text-slate-900">Step 2: 90-Second Screening Excitation</h2>
          </div>

          <div className="flex items-center gap-2">
            {/* Fast Mode Toggle for Hackathon presentations */}
            <button
              type="button"
              disabled={isTesting}
              onClick={() => setFastMode(!fastMode)}
              className={`px-2.5 py-1 text-xs rounded-lg font-medium border transition-colors ${
                fastMode ? 'bg-purple-100 text-purple-800 border-purple-300' : 'bg-slate-100 text-slate-600 border-slate-200'
              }`}
              title="Fast screening for rapid presentation demos"
            >
              {fastMode ? '⚡ Fast Screening (5x Speed)' : '⏱ Normal 1s/tick'}
            </button>

            {!isTesting && !isCompleted && (
              <button
                onClick={handleStartTest}
                className="inline-flex items-center gap-1.5 px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg text-xs font-semibold shadow-xs transition-colors"
              >
                <Play className="w-4 h-4 fill-white" />
                <span>Start 90s Screening Test</span>
              </button>
            )}

            {isTesting && (
              <button
                onClick={handleStopTest}
                className="inline-flex items-center gap-1.5 px-4 py-2 bg-rose-600 hover:bg-rose-700 text-white rounded-lg text-xs font-semibold shadow-xs transition-colors"
              >
                <Square className="w-4 h-4 fill-white" />
                <span>Interrupt Test</span>
              </button>
            )}

            {(isCompleted || currentSecond > 0) && !isTesting && (
              <button
                onClick={handleResetTest}
                className="inline-flex items-center gap-1.5 px-3 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg text-xs font-semibold border border-slate-300 transition-colors"
              >
                <RotateCcw className="w-4 h-4" />
                <span>Reset Screening Bench</span>
              </button>
            )}
          </div>
        </div>

        {/* Test Profile Selector when in Virtual Circuit */}
        {(selectedSource === 'virtual_circuit' || selectedSource === 'replay_recorded') && !isTesting && !isCompleted && (
          <div className="p-3 bg-slate-50 rounded-xl border border-slate-200">
            <span className="text-[11px] font-bold text-slate-600 uppercase">Select Cell Degradation Profile to Test:</span>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 mt-2">
              {[
                { id: 'healthy', label: 'Healthy Cell', sub: '~91% SOH, <30°C' },
                { id: 'moderately_aged', label: 'Moderately Aged', sub: '~75% SOH, 38°C' },
                { id: 'thermally_unsafe', label: 'Thermally Unsafe Cell', sub: '<50% SOH, >45°C Runaway' }
              ].map(p => (
                <button
                  key={p.id}
                  onClick={() => setTestProfile(p.id)}
                  className={`p-2.5 rounded-lg border text-left text-xs transition-all ${
                    testProfile === p.id
                      ? (p.id === 'thermally_unsafe' ? 'border-rose-500 bg-rose-50 text-rose-900 font-semibold' : 'border-emerald-500 bg-emerald-50 text-emerald-900 font-semibold')
                      : 'border-slate-200 bg-white hover:bg-slate-100 text-slate-700'
                  }`}
                >
                  <p>{p.label}</p>
                  <p className="text-[10px] text-slate-500 font-normal">{p.sub}</p>
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Live Gauges / Readouts Banner */}
        <div className="grid grid-cols-2 md:grid-cols-5 gap-3 pt-2">
          <div className="p-3 bg-slate-50 rounded-xl border border-slate-200">
            <div className="flex items-center gap-1.5 text-slate-500 mb-1 text-[11px]">
              <Clock className="w-3.5 h-3.5" />
              <span>Elapsed / Duration</span>
            </div>
            <p className="text-xl font-bold text-slate-900">{currentSecond}s <span className="text-xs font-normal text-slate-400">/ 90s</span></p>
            <div className="w-full bg-slate-200 h-1.5 rounded-full mt-2 overflow-hidden">
              <div
                className="bg-emerald-600 h-full transition-all duration-300"
                style={{ width: `${(currentSecond / 90) * 100}%` }}
              />
            </div>
          </div>

          <div className="p-3 bg-slate-50 rounded-xl border border-slate-200">
            <div className="flex items-center gap-1.5 text-blue-600 mb-1 text-[11px]">
              <Zap className="w-3.5 h-3.5" />
              <span>Voltage (V)</span>
            </div>
            <p className="text-xl font-bold text-blue-700">{latestPoint.voltage.toFixed(3)} <span className="text-xs font-normal text-slate-500">V</span></p>
            <p className="text-[10px] text-slate-400 mt-1">LFP Plateau (3.2–3.4V)</p>
          </div>

          <div className="p-3 bg-slate-50 rounded-xl border border-slate-200">
            <div className="flex items-center gap-1.5 text-purple-600 mb-1 text-[11px]">
              <Gauge className="w-3.5 h-3.5" />
              <span>Current (A)</span>
            </div>
            <p className="text-xl font-bold text-purple-700">{latestPoint.current.toFixed(2)} <span className="text-xs font-normal text-slate-500">A</span></p>
            <p className="text-[10px] text-slate-400 mt-1">Discharge rate (10A)</p>
          </div>

          <div className="p-3 bg-slate-50 rounded-xl border border-slate-200">
            <div className="flex items-center gap-1.5 text-amber-600 mb-1 text-[11px]">
              <Thermometer className="w-3.5 h-3.5" />
              <span>Temperature (°C)</span>
            </div>
            <p className={`text-xl font-bold ${latestPoint.temperature >= 45 ? 'text-rose-600 animate-pulse' : 'text-slate-900'}`}>
              {latestPoint.temperature.toFixed(1)} <span className="text-xs font-normal text-slate-500">°C</span>
            </p>
            <p className="text-[10px] text-slate-400 mt-1">{latestPoint.temperature >= 45 ? '⚠️ Thermal Runaway!' : 'Normal Operating Band'}</p>
          </div>

          <div className="p-3 bg-slate-50 rounded-xl border border-slate-200 col-span-2 md:col-span-1">
            <span className="text-slate-500 text-[11px]">Stream Status</span>
            <p className="text-base font-bold text-slate-800 mt-1">
              {isTesting ? 'Streaming Active' : (isCompleted ? 'Test Completed' : 'Bench Ready')}
            </p>
            <p className="text-[10px] text-slate-400 mt-0.5">{sourceMeta.name}</p>
          </div>
        </div>
      </div>

      {/* Step 3: Three Separate Live Telemetry Charts (Voltage, Current, Temperature) */}
      <div className="space-y-4">
        <div className="flex items-center gap-2">
          <span className="w-6 h-6 rounded-full bg-emerald-600 text-white flex items-center justify-center text-xs font-bold">3</span>
          <h2 className="text-sm font-bold text-slate-900">Step 3: Real-Time Diagnostic Waveforms</h2>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          {/* Chart 1: Voltage */}
          <div className="bg-white rounded-xl border border-slate-200 p-4 shadow-xs">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-bold text-slate-800">Cell Voltage (V)</span>
              <span className="text-[11px] font-semibold text-blue-600">{latestPoint.voltage} V</span>
            </div>
            <div className="h-44 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={telemetryHistory}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                  <XAxis dataKey="time" domain={[0, 90]} tick={{ fontSize: 10 }} unit="s" />
                  <YAxis domain={['auto', 'auto']} tick={{ fontSize: 10 }} unit="V" />
                  <Tooltip formatter={(value) => [`${value} V`, 'Voltage']} labelFormatter={(l) => `Time: ${l}s`} />
                  <Line type="monotone" dataKey="voltage" stroke="#2563eb" strokeWidth={2} dot={false} isAnimationActive={false} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Chart 2: Current */}
          <div className="bg-white rounded-xl border border-slate-200 p-4 shadow-xs">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-bold text-slate-800">Discharge Current (A)</span>
              <span className="text-[11px] font-semibold text-purple-600">{latestPoint.current} A</span>
            </div>
            <div className="h-44 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={telemetryHistory}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                  <XAxis dataKey="time" domain={[0, 90]} tick={{ fontSize: 10 }} unit="s" />
                  <YAxis domain={['auto', 'auto']} tick={{ fontSize: 10 }} unit="A" />
                  <Tooltip formatter={(value) => [`${value} A`, 'Current']} labelFormatter={(l) => `Time: ${l}s`} />
                  <Line type="monotone" dataKey="current" stroke="#9333ea" strokeWidth={2} dot={false} isAnimationActive={false} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Chart 3: Temperature */}
          <div className="bg-white rounded-xl border border-slate-200 p-4 shadow-xs">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-bold text-slate-800">Cell Thermistor (°C)</span>
              <span className={`text-[11px] font-semibold ${latestPoint.temperature >= 45 ? 'text-rose-600' : 'text-amber-600'}`}>
                {latestPoint.temperature} °C
              </span>
            </div>
            <div className="h-44 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={telemetryHistory}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                  <XAxis dataKey="time" domain={[0, 90]} tick={{ fontSize: 10 }} unit="s" />
                  <YAxis domain={['auto', 'auto']} tick={{ fontSize: 10 }} unit="°C" />
                  <Tooltip formatter={(value) => [`${value} °C`, 'Temperature']} labelFormatter={(l) => `Time: ${l}s`} />
                  <Line
                    type="monotone"
                    dataKey="temperature"
                    stroke={latestPoint.temperature >= 45 ? '#e11d48' : '#d97706'}
                    strokeWidth={2}
                    dot={false}
                    isAnimationActive={false}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>
      </div>

      {/* Step 4 & 5: Assessment Results BELOW the charts on the SAME PAGE */}
      {isCompleted && assessmentResult && (
        <div className="bg-white rounded-2xl border-2 border-emerald-500/40 p-6 shadow-sm space-y-6">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between pb-4 border-b border-slate-200 gap-3">
            <div className="flex items-center gap-2.5">
              <span className="w-7 h-7 rounded-full bg-emerald-600 text-white flex items-center justify-center text-xs font-bold">4</span>
              <div>
                <h2 className="text-base font-bold text-slate-900">Step 4 & 5: AI Assessment & Second-Life Matchmaker</h2>
                <p className="text-xs text-slate-500">Evaluation computed directly from 90s telemetry history</p>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <button
                onClick={() => navigate(`/tech/what-if?battery_id=${selectedBatteryId}`)}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg text-xs font-semibold border border-slate-300 transition-colors"
              >
                <Sliders className="w-3.5 h-3.5" />
                <span>What-If Simulator</span>
              </button>

              <button
                onClick={() => navigate(`/tech/approval?battery_id=${selectedBatteryId}`)}
                className="inline-flex items-center gap-1.5 px-4 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg text-xs font-semibold shadow-xs transition-colors"
              >
                <span>Approve & Mint Passport</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>

          {/* SOH, Safety, Action Metrics */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="p-4 bg-slate-50 rounded-xl border border-slate-200">
              <span className="text-xs font-medium text-slate-500">State of Health (SOH)</span>
              <p className={`text-3xl font-extrabold mt-1 ${
                assessmentResult.soh_estimate >= 80 ? 'text-emerald-600' :
                (assessmentResult.soh_estimate >= 60 ? 'text-amber-600' : 'text-rose-600')
              }`}>
                {assessmentResult.soh_estimate}%
              </p>
              <p className="text-[11px] text-slate-400 mt-1">
                Confidence: {(assessmentResult.confidence_score * 100).toFixed(0)}% ({assessmentResult.confidence_level})
              </p>
            </div>

            <div className="p-4 bg-slate-50 rounded-xl border border-slate-200">
              <span className="text-xs font-medium text-slate-500">Safety Classification</span>
              <p className={`text-xl font-bold mt-1 flex items-center gap-1.5 ${
                assessmentResult.safety_status === 'Critical Danger' ? 'text-rose-600' : 'text-emerald-700'
              }`}>
                {assessmentResult.safety_status === 'Critical Danger' ? <ShieldAlert className="w-5 h-5 text-rose-600" /> : <ShieldCheck className="w-5 h-5 text-emerald-600" />}
                <span>{assessmentResult.safety_status}</span>
              </p>
              <p className="text-[11px] text-slate-400 mt-1">
                Peak Temp: {assessmentResult.max_test_temperature_c}°C
              </p>
            </div>

            <div className="p-4 bg-slate-50 rounded-xl border border-slate-200">
              <span className="text-xs font-medium text-slate-500">Recommended Route</span>
              <p className="text-xl font-bold text-slate-900 mt-1">
                {assessmentResult.recommended_action}
              </p>
              <p className="text-[11px] text-slate-400 mt-1">
                Retained: {assessmentResult.remaining_capacity_ah} Ah
              </p>
            </div>

            <div className="p-4 bg-slate-50 rounded-xl border border-slate-200">
              <span className="text-xs font-medium text-slate-500">Exchange Buyback Credit</span>
              <p className="text-xl font-bold text-emerald-600 mt-1">
                ₹{assessmentResult.exchange_credit_inr?.toLocaleString()}
              </p>
              <p className="text-[11px] text-slate-400 mt-1">
                Estimated RUL: {assessmentResult.residual_life_years} years
              </p>
            </div>
          </div>

          {/* Safety Flags Warning */}
          {assessmentResult.safety_flags && assessmentResult.safety_flags.length > 0 && (
            <div className="p-4 bg-rose-50 border border-rose-300 rounded-xl text-xs text-rose-900 space-y-1">
              <div className="flex items-center gap-2 font-bold text-rose-800">
                <AlertTriangle className="w-4 h-4 text-rose-600" />
                <span>Critical Safety Flags Detected:</span>
              </div>
              <ul className="list-disc list-inside text-rose-700 space-y-0.5">
                {assessmentResult.safety_flags.map((flag, idx) => (
                  <li key={idx}>{flag}</li>
                ))}
              </ul>
            </div>
          )}

          {/* Plain English Explanation */}
          <div className="p-4 bg-blue-50/70 border border-blue-200 rounded-xl text-xs text-blue-950">
            <span className="font-bold text-blue-900 flex items-center gap-1 mb-1">
              <Info className="w-4 h-4 text-blue-600" />
              AI Technical Assessment Diagnostic:
            </span>
            <p className="leading-relaxed text-blue-900/90">{assessmentResult.plain_english_explanation}</p>
          </div>

          {/* Second-Life Matchmaker */}
          <div>
            <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider mb-3">
              Second-Life Application Suitability Matchmaker
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {assessmentResult.second_life_matches?.map((m, idx) => (
                <div key={idx} className="p-3 bg-slate-50 rounded-xl border border-slate-200 flex items-start justify-between gap-3 text-xs">
                  <div>
                    <span className="font-bold text-slate-900">{m.application}</span>
                    <p className="text-[11px] text-slate-600 mt-1 leading-snug">{m.reason}</p>
                  </div>
                  <div className="text-right shrink-0">
                    <span className={`px-2 py-0.5 rounded font-bold text-[10px] ${
                      m.suitability === 'Optimal' ? 'bg-emerald-100 text-emerald-800' :
                      (m.suitability === 'Good' ? 'bg-blue-100 text-blue-800' :
                      (m.suitability === 'Prohibited' ? 'bg-rose-100 text-rose-800' : 'bg-slate-200 text-slate-700'))
                    }`}>
                      {m.suitability}
                    </span>
                    <p className="text-[10px] text-slate-400 mt-1 font-semibold">{m.predicted_lifetime_years} yrs RUL</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

