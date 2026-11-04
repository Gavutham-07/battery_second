import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

const client = axios.create({
  baseURL: API_BASE_URL,
  timeout: 4000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Centralized API Service for ReVolt
// Modularly wraps backend calls with graceful fallback for local hackathon demo mode.
export const api = {
  // Battery Registration
  registerBattery: async (data) => {
    try {
      const response = await client.post('/api/register-battery', data);
      return response.data;
    } catch (err) {
      // Backend not running / offline fallback
      return null;
    }
  },

  // Battery Queue
  getBatteries: async () => {
    try {
      const response = await client.get('/api/batteries');
      return response.data;
    } catch (err) {
      return null;
    }
  },

  // Telemetry stream init
  simulateStream: async (batteryId, dataSource, testProfile) => {
    try {
      const response = await client.post('/api/simulate-stream', {
        battery_id: batteryId,
        data_source: dataSource,
        test_profile: testProfile,
      });
      return response.data;
    } catch (err) {
      return null;
    }
  },

  // Polling live telemetry
  getLiveData: async (batteryId) => {
    try {
      const response = await client.get(`/api/live-data/${batteryId}`);
      return response.data;
    } catch (err) {
      return null;
    }
  },

  // AI Analysis
  analyzeBattery: async (batteryId) => {
    try {
      const response = await client.post('/api/analyze', { battery_id: batteryId });
      return response.data;
    } catch (err) {
      return null;
    }
  },

  // What-If Scenario
  whatIf: async (payload) => {
    try {
      const response = await client.post('/api/what-if', payload);
      return response.data;
    } catch (err) {
      return null;
    }
  },

  // Approval & Passport Minting
  approveAndExchange: async (payload) => {
    try {
      const response = await client.post('/api/approve-and-exchange', payload);
      return response.data;
    } catch (err) {
      return null;
    }
  },

  // QR Verification
  verifyPassport: async (batteryId) => {
    try {
      const response = await client.get(`/api/verify/${batteryId}`);
      return response.data;
    } catch (err) {
      return null;
    }
  },

  // Recycler Batches
  getRecyclerBatch: async () => {
    try {
      const response = await client.get('/api/recycler-batch');
      return response.data;
    } catch (err) {
      return null;
    }
  },

  // Pack Grouping
  groupCells: async (payload) => {
    try {
      const response = await client.post('/api/group-cells', payload);
      return response.data;
    } catch (err) {
      return null;
    }
  }
};

export default api;

