import React, { createContext, useContext, useState, useEffect } from 'react';

const DataSourceContext = createContext();

export const DATA_SOURCES = [
  {
    id: 'virtual_circuit',
    name: 'Virtual Battery Circuit',
    type: 'Simulated',
    badgeColor: 'bg-emerald-100 text-emerald-800 border-emerald-300',
    description: 'Dynamic electrochemical impedance model with selectable cell degradation profiles.'
  },
  {
    id: 'replay_recorded',
    name: 'Replay Recorded Test',
    type: 'Replay Active',
    badgeColor: 'bg-blue-100 text-blue-800 border-blue-300',
    description: 'High-fidelity replay of 90-second fleet screening test cycles.'
  },
  {
    id: 'lab_dataset',
    name: 'Lab Dataset Cells (MIT/Sandia)',
    type: 'Simulated',
    badgeColor: 'bg-purple-100 text-purple-800 border-purple-300',
    description: 'Laboratory degradation bench dataset (MIT/Sandia open battery archives).'
  },
  {
    id: 'live_hardware',
    name: 'Live Hardware (ESP32)',
    type: 'Disconnected',
    badgeColor: 'bg-amber-100 text-amber-800 border-amber-300',
    description: 'Direct serial USB stream from ESP32 voltage/current/thermistor screening rig.'
  }
];

export const TEST_PROFILES = [
  { id: 'healthy', name: 'Healthy Cell (~91% SOH, <30°C)', description: 'Nominal discharge plateau, stable impedance' },
  { id: 'moderately_aged', name: 'Moderately Aged Cell (~75% SOH, 38°C)', description: 'Degraded capacity, elevated thermal slope' },
  { id: 'thermally_unsafe', name: 'Thermally Unsafe Cell (<50% SOH, >45°C)', description: 'Thermal runaway hazard, severe voltage sag' }
];

export function DataSourceProvider({ children }) {
  const [selectedSource, setSelectedSource] = useState(() => {
    return localStorage.getItem('revolt_data_source') || 'virtual_circuit';
  });

  const [testProfile, setTestProfile] = useState(() => {
    return localStorage.getItem('revolt_test_profile') || 'healthy';
  });

  const [hardwareDetected, setHardwareDetected] = useState(false);

  useEffect(() => {
    localStorage.setItem('revolt_data_source', selectedSource);
  }, [selectedSource]);

  useEffect(() => {
    localStorage.setItem('revolt_test_profile', testProfile);
  }, [testProfile]);

  // Determine dynamic status label
  const getStatus = () => {
    if (selectedSource === 'live_hardware') {
      return hardwareDetected ? 'Connected' : 'Disconnected';
    }
    if (selectedSource === 'replay_recorded') {
      return 'Replay Active';
    }
    return 'Simulated';
  };

  const getSourceMeta = () => {
    return DATA_SOURCES.find(s => s.id === selectedSource) || DATA_SOURCES[0];
  };

  return (
    <DataSourceContext.Provider
      value={{
        selectedSource,
        setSelectedSource,
        testProfile,
        setTestProfile,
        status: getStatus(),
        sourceMeta: getSourceMeta(),
        hardwareDetected,
        setHardwareDetected,
        DATA_SOURCES,
        TEST_PROFILES
      }}
    >
      {children}
    </DataSourceContext.Provider>
  );
}

export const useDataSource = () => useContext(DataSourceContext);

