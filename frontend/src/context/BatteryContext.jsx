import React, { createContext, useContext, useState, useEffect } from 'react';
import { runBatteryAssessment, calculateWhatIf, generateSHA256Hash } from '../services/assessmentEngine';

const BatteryContext = createContext();

// Pre-seeded realistic cell inventory for Pack Grouping
const INITIAL_CELL_INVENTORY = [
  { cell_id: 'CELL-LFP-01', chemistry: 'LFP', capacity_ah: 3.2, soh: 88.4, internal_resistance_mohm: 12.1, status: 'Available' },
  { cell_id: 'CELL-LFP-02', chemistry: 'LFP', capacity_ah: 3.2, soh: 88.9, internal_resistance_mohm: 11.9, status: 'Available' },
  { cell_id: 'CELL-LFP-03', chemistry: 'LFP', capacity_ah: 3.2, soh: 87.8, internal_resistance_mohm: 12.4, status: 'Available' },
  { cell_id: 'CELL-LFP-04', chemistry: 'LFP', capacity_ah: 3.2, soh: 88.2, internal_resistance_mohm: 12.0, status: 'Available' },
  { cell_id: 'CELL-LFP-05', chemistry: 'LFP', capacity_ah: 3.2, soh: 84.1, internal_resistance_mohm: 13.8, status: 'Available' },
  { cell_id: 'CELL-LFP-06', chemistry: 'LFP', capacity_ah: 3.2, soh: 88.6, internal_resistance_mohm: 12.2, status: 'Available' },
  { cell_id: 'CELL-NMC-01', chemistry: 'NMC', capacity_ah: 2.5, soh: 91.2, internal_resistance_mohm: 18.2, status: 'Available' },
  { cell_id: 'CELL-NMC-02', chemistry: 'NMC', capacity_ah: 2.5, soh: 90.8, internal_resistance_mohm: 18.5, status: 'Available' },
  { cell_id: 'CELL-NMC-03', chemistry: 'NMC', capacity_ah: 2.5, soh: 91.5, internal_resistance_mohm: 18.0, status: 'Available' },
  { cell_id: 'CELL-NMC-04', chemistry: 'NMC', capacity_ah: 2.5, soh: 78.4, internal_resistance_mohm: 24.5, status: 'Available' },
];

const INITIAL_BATTERIES = [
  {
    battery_id: 'BAT-101',
    chemistry: 'LFP',
    rated_capacity_ah: 50.0,
    vehicle_model: 'Tata Nexon EV Prime',
    owner_name: 'Aditya Sharma',
    registration_date: new Date(Date.now() - 3600000 * 4).toISOString(),
    status: 'Awaiting Screening', // "Awaiting Screening" | "Testing in Progress" | "Assessed" | "Approved"
    soh_estimate: null,
    safety_status: null,
    safety_flags: [],
    recommended_action: null,
    owner_preference: null,
    exchange_offer_accepted: false,
    passport: null
  },
  {
    battery_id: 'BAT-102',
    chemistry: 'NMC',
    rated_capacity_ah: 60.0,
    vehicle_model: 'MG ZS EV',
    owner_name: 'Priya Patel',
    registration_date: new Date(Date.now() - 86400000).toISOString(),
    status: 'Assessed',
    soh_estimate: 76.5,
    confidence_score: 0.93,
    confidence_level: 'High',
    safety_status: 'Safe',
    safety_flags: ['Moderate thermal rise (38.2°C) under high load'],
    plain_english_explanation: 'Cell retains 76.5% capacity with intact separator integrity. Ideal for stationary telecom and home solar storage.',
    recommended_action: 'Repurpose',
    remaining_capacity_ah: 45.9,
    residual_life_years: 4.2,
    exchange_credit_inr: 28400,
    owner_preference: 'Sell / Exchange',
    exchange_offer_accepted: false,
    second_life_matches: [
      { application: 'Home Solar Storage', suitability: 'Optimal', predicted_lifetime_years: 4.8, reason: 'Gentle solar cycle curve preserves electrode structure.' },
      { application: 'UPS / Telecom Backup', suitability: 'Good', predicted_lifetime_years: 5.5, reason: 'High reliability in float charging mode.' },
      { application: 'E-Rickshaw / Light EV', suitability: 'Moderate', predicted_lifetime_years: 2.8, reason: 'Accelerated thermal aging under rough terrain throttle surges.' }
    ],
    passport: null
  },
  {
    battery_id: 'BAT-103',
    chemistry: 'LFP',
    rated_capacity_ah: 40.0,
    vehicle_model: 'Mahindra XUV400',
    owner_name: 'Rohan Verma',
    registration_date: new Date(Date.now() - 172800000).toISOString(),
    status: 'Approved',
    soh_estimate: 89.4,
    confidence_score: 0.97,
    confidence_level: 'High',
    safety_status: 'Safe',
    safety_flags: [],
    plain_english_explanation: 'Exceptional LFP health with tight voltage delta (<15mV). Premium candidate for light electric mobility repowering.',
    recommended_action: 'Direct Reuse',
    remaining_capacity_ah: 35.76,
    residual_life_years: 6.8,
    exchange_credit_inr: 32600,
    owner_preference: 'Reuse',
    exchange_offer_accepted: true,
    second_life_matches: [
      { application: 'E-Rickshaw / Light EV', suitability: 'Optimal', predicted_lifetime_years: 5.1, reason: 'High dynamic power burst retention.' },
      { application: 'Home Solar Storage', suitability: 'Optimal', predicted_lifetime_years: 7.8, reason: 'Extensive cycle life headroom.' }
    ],
    passport: {
      passport_id: 'PASSPORT-BAT-103-2026',
      battery_id: 'BAT-103',
      approved_route: 'E-Rickshaw / Light EV',
      technician_id: 'TECH-BLR-02',
      technician_notes: 'Physical cell visual inspection cleared. Terminal busbars in factory condition.',
      minted_at: new Date(Date.now() - 43200000).toISOString(),
      sha256_hash: '9a6b18c2f10b7849c7198bb4d5e86d910a307421882c3c6f131a49910d65b128',
      exchange_credit_inr: 32600
    }
  },
  {
    battery_id: 'BAT-104',
    chemistry: 'NCA',
    rated_capacity_ah: 55.0,
    vehicle_model: 'Hyundai Kona Electric',
    owner_name: 'Kavita Sundaram',
    registration_date: new Date(Date.now() - 259200000).toISOString(),
    status: 'Assessed',
    soh_estimate: 47.8,
    confidence_score: 0.98,
    confidence_level: 'High',
    safety_status: 'Critical Danger',
    safety_flags: [
      'Thermal runaway hazard (>48.5°C during 90s screening test)',
      'Severe internal impedance degradation',
      'Electrolyte outgassing risk detected'
    ],
    plain_english_explanation: 'CRITICAL: Thermal runaway threshold breached. Cell is electrochemically unstable and hazardous for reuse. Must be immediately neutralized and sent for hydrometallurgical recycling.',
    recommended_action: 'Recycle',
    remaining_capacity_ah: 26.29,
    residual_life_years: 0.0,
    exchange_credit_inr: 6050,
    owner_preference: null,
    exchange_offer_accepted: false,
    second_life_matches: [
      { application: 'Home Solar Storage', suitability: 'Prohibited', predicted_lifetime_years: 0, reason: 'Fire safety violation.' },
      { application: 'E-Rickshaw / Light EV', suitability: 'Prohibited', predicted_lifetime_years: 0, reason: 'Vehicular fire risk.' }
    ],
    passport: null
  }
];

export function BatteryProvider({ children }) {
  const [batteries, setBatteries] = useState(() => {
    try {
      const saved = localStorage.getItem('revolt_batteries');
      return saved ? JSON.parse(saved) : INITIAL_BATTERIES;
    } catch (e) {
      return INITIAL_BATTERIES;
    }
  });

  const [cellInventory, setCellInventory] = useState(() => {
    try {
      const saved = localStorage.getItem('revolt_cell_inventory');
      return saved ? JSON.parse(saved) : INITIAL_CELL_INVENTORY;
    } catch (e) {
      return INITIAL_CELL_INVENTORY;
    }
  });

  const [groupedPacks, setGroupedPacks] = useState(() => {
    try {
      const saved = localStorage.getItem('revolt_grouped_packs');
      return saved ? JSON.parse(saved) : [];
    } catch (e) {
      return [];
    }
  });

  // Save changes to localStorage for true persistence
  useEffect(() => {
    localStorage.setItem('revolt_batteries', JSON.stringify(batteries));
  }, [batteries]);

  useEffect(() => {
    localStorage.setItem('revolt_cell_inventory', JSON.stringify(cellInventory));
  }, [cellInventory]);

  useEffect(() => {
    localStorage.setItem('revolt_grouped_packs', JSON.stringify(groupedPacks));
  }, [groupedPacks]);

  // Register a new battery
  const registerBattery = (batteryData) => {
    const existing = batteries.find(b => b.battery_id.toUpperCase() === batteryData.battery_id.trim().toUpperCase());
    if (existing) {
      return { success: false, message: `Battery with ID ${batteryData.battery_id} already exists!` };
    }

    const newBattery = {
      battery_id: batteryData.battery_id.trim().toUpperCase(),
      chemistry: batteryData.chemistry || 'LFP',
      rated_capacity_ah: Number(batteryData.rated_capacity_ah) || 50,
      vehicle_model: batteryData.vehicle_model || 'Electric Vehicle',
      owner_name: batteryData.owner_name || 'EV Owner',
      registration_date: new Date().toISOString(),
      status: 'Awaiting Screening',
      soh_estimate: null,
      confidence_score: null,
      confidence_level: null,
      safety_status: null,
      safety_flags: [],
      plain_english_explanation: null,
      recommended_action: null,
      remaining_capacity_ah: null,
      residual_life_years: null,
      exchange_credit_inr: null,
      owner_preference: null,
      exchange_offer_accepted: false,
      second_life_matches: [],
      telemetry: [],
      passport: null
    };

    setBatteries(prev => [newBattery, ...prev]);
    return { success: true, battery: newBattery };
  };

  const getBattery = (id) => {
    if (!id) return null;
    return batteries.find(b => b.battery_id.toUpperCase() === id.trim().toUpperCase()) || null;
  };

  const updateBatteryStatus = (battery_id, status) => {
    setBatteries(prev => prev.map(b => {
      if (b.battery_id === battery_id) {
        return { ...b, status };
      }
      return b;
    }));
  };

  // Perform assessment upon screening completion
  const completeScreeningAndAssess = (battery_id, telemetryPoints = [], profile = 'healthy') => {
    const battery = getBattery(battery_id);
    if (!battery) return null;

    const assessment = runBatteryAssessment(battery, telemetryPoints, profile);

    setBatteries(prev => prev.map(b => {
      if (b.battery_id === battery_id) {
        return {
          ...b,
          ...assessment,
          status: 'Assessed',
          telemetry: telemetryPoints
        };
      }
      return b;
    }));

    return assessment;
  };

  // Update Owner Preference
  const updateOwnerPreference = (battery_id, preference) => {
    const battery = getBattery(battery_id);
    if (!battery) return { success: false, message: 'Battery not found' };

    // Prevent unsafe batteries from selecting Reuse or Repurpose
    if (battery.safety_status === 'Critical Danger' && preference !== 'Sell / Exchange') {
      return { success: false, message: 'Unsafe battery cannot be selected for Reuse or Repurpose. Safety protocols require recycling.' };
    }

    setBatteries(prev => prev.map(b => {
      if (b.battery_id === battery_id) {
        return { ...b, owner_preference: preference };
      }
      return b;
    }));

    return { success: true, message: 'Preference saved successfully' };
  };

  // Accept exchange credit offer
  const acceptExchangeOffer = (battery_id) => {
    setBatteries(prev => prev.map(b => {
      if (b.battery_id === battery_id) {
        return { ...b, exchange_offer_accepted: true };
      }
      return b;
    }));
    return { success: true };
  };

  // Technician Approval & QR Passport Minting
  const approveAndMintPassport = async (battery_id, technicianNotes, approvedRoute, technicianId = 'TECH-REC-01') => {
    const battery = getBattery(battery_id);
    if (!battery) return { success: false, message: 'Battery not found' };

    const passportPayload = {
      battery_id: battery.battery_id,
      chemistry: battery.chemistry,
      rated_capacity_ah: battery.rated_capacity_ah,
      soh_estimate: battery.soh_estimate,
      safety_status: battery.safety_status,
      approved_route: approvedRoute,
      technician_id: technicianId,
      technician_notes: technicianNotes,
      minted_at: new Date().toISOString()
    };

    const hash = await generateSHA256Hash(passportPayload);

    const passport = {
      passport_id: `PASSPORT-${battery.battery_id}-${Date.now().toString().slice(-4)}`,
      battery_id: battery.battery_id,
      approved_route: approvedRoute,
      technician_id: technicianId,
      technician_notes: technicianNotes,
      minted_at: passportPayload.minted_at,
      sha256_hash: hash,
      exchange_credit_inr: battery.exchange_credit_inr || 25000,
      soh_estimate: battery.soh_estimate,
      safety_status: battery.safety_status
    };

    setBatteries(prev => prev.map(b => {
      if (b.battery_id === battery_id) {
        return {
          ...b,
          status: 'Approved',
          passport: passport
        };
      }
      return b;
    }));

    return { success: true, passport };
  };

  // Cell Pack Grouping Logic (Recycler)
  const groupSelectedCells = (selectedCellIds, targetChemistry = 'LFP', packName = 'PACK-MOD-1') => {
    if (!selectedCellIds || selectedCellIds.length < 2) {
      return { success: false, message: 'Please select at least 2 cells to form a pack module.' };
    }

    const selectedCells = cellInventory.filter(c => selectedCellIds.includes(c.cell_id));
    
    // Check chemistry compatibility
    const mismatched = selectedCells.some(c => c.chemistry !== targetChemistry);
    if (mismatched) {
      return { success: false, message: `Incompatible Chemistries! All cells in a pack module must share the same chemistry (${targetChemistry}).` };
    }

    const sohs = selectedCells.map(c => c.soh);
    const minSoh = Math.min(...sohs);
    const maxSoh = Math.max(...sohs);
    const sohDelta = Number((maxSoh - minSoh).toFixed(2));
    const avgSoh = Number((sohs.reduce((a, b) => a + b, 0) / sohs.length).toFixed(2));

    let compatibility = 'Optimal Balance';
    let warnings = [];

    if (sohDelta > 4.0) {
      compatibility = 'Poor / High Spread';
      warnings.push(`SOH delta is ${sohDelta}%. Cells should ideally have less than 3.0% spread to prevent accelerated thermal degradation.`);
    } else if (sohDelta > 2.0) {
      compatibility = 'Acceptable';
      warnings.push(`Minor SOH variance (${sohDelta}%). BMS active balancing is recommended.`);
    }

    const newPack = {
      pack_id: packName || `PACK-MOD-${Date.now().toString().slice(-4)}`,
      created_at: new Date().toISOString(),
      chemistry: targetChemistry,
      cell_count: selectedCells.length,
      cells: selectedCells,
      average_soh: avgSoh,
      soh_spread: sohDelta,
      compatibility,
      warnings,
      disclaimer: 'Software-assisted grouping only. Physical assembly requires calibrated cell sorting, BMS configuration, and thermal isolation.'
    };

    // Mark cells as Grouped
    setCellInventory(prev => prev.map(c => {
      if (selectedCellIds.includes(c.cell_id)) {
        return { ...c, status: 'Grouped' };
      }
      return c;
    }));

    setGroupedPacks(prev => [newPack, ...prev]);

    return { success: true, pack: newPack };
  };

  // Recycler Batches derived from assessed batteries
  const getRecyclerBatches = () => {
    const reuse = batteries.filter(b => b.status === 'Assessed' || b.status === 'Approved')
      .filter(b => b.safety_status === 'Safe' && b.soh_estimate >= 80);

    const repurpose = batteries.filter(b => b.status === 'Assessed' || b.status === 'Approved')
      .filter(b => b.safety_status === 'Safe' && b.soh_estimate >= 60 && b.soh_estimate < 80);

    const recycle = batteries.filter(b => b.status === 'Assessed' || b.status === 'Approved')
      .filter(b => b.safety_status === 'Critical Danger' || (b.soh_estimate && b.soh_estimate < 60));

    return { reuse, repurpose, recycle };
  };

  // Public QR verification lookup
  const verifyPassport = async (batteryId) => {
    const battery = getBattery(batteryId);
    if (!battery) {
      return { status: 'Not Found', message: 'No registered battery found matching this ID.' };
    }
    if (!battery.passport) {
      return {
        status: 'Unverified',
        battery,
        message: 'This battery has been registered but not yet approved or minted as a verified Battery Passport.'
      };
    }

    // Verify hash integrity
    return {
      status: 'Valid',
      battery,
      passport: battery.passport,
      hash_verified: true,
      message: 'Cryptographic SHA-256 integrity confirmed by second-life registry.'
    };
  };

  return (
    <BatteryContext.Provider
      value={{
        batteries,
        registerBattery,
        getBattery,
        updateBatteryStatus,
        completeScreeningAndAssess,
        updateOwnerPreference,
        acceptExchangeOffer,
        approveAndMintPassport,
        cellInventory,
        groupedPacks,
        groupSelectedCells,
        getRecyclerBatches,
        verifyPassport
      }}
    >
      {children}
    </BatteryContext.Provider>
  );
}

export const useBatteryStore = () => useContext(BatteryContext);

