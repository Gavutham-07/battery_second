import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { DataSourceProvider } from './context/DataSourceContext';
import { BatteryProvider } from './context/BatteryContext';

// Landing & Verification
import LandingPage from './pages/LandingPage';
import PublicVerification from './pages/verify/PublicVerification';

// Owner Portal
import OwnerLayout from './pages/owner/OwnerLayout';
import OwnerDashboard from './pages/owner/OwnerDashboard';
import MyBatteries from './pages/owner/MyBatteries';
import FindServiceCenters from './pages/owner/FindServiceCenters';
import Recommendations from './pages/owner/Recommendations';
import ExchangeOffers from './pages/owner/ExchangeOffers';
import EnvironmentalImpact from './pages/owner/EnvironmentalImpact';
import MyBatteryPassport from './pages/owner/MyBatteryPassport';

// Technician Portal
import TechLayout from './pages/tech/TechLayout';
import TechnicianDashboard from './pages/tech/TechnicianDashboard';
import BatteryQueue from './pages/tech/BatteryQueue';
import BatteryScreening from './pages/tech/BatteryScreening';
import WhatIfSimulator from './pages/tech/WhatIfSimulator';
import ApprovalPassport from './pages/tech/ApprovalPassport';

// Recycler Portal
import RecyclerLayout from './pages/recycler/RecyclerLayout';
import ImpactSummary from './pages/recycler/ImpactSummary';
import BatchSorting from './pages/recycler/BatchSorting';
import PackGrouping from './pages/recycler/PackGrouping';

export default function App() {
  return (
    <DataSourceProvider>
      <BatteryProvider>
        <BrowserRouter>
          <Routes>
            {/* Landing Page */}
            <Route path="/" element={<LandingPage />} />

            {/* Public Verification */}
            <Route path="/verify" element={<PublicVerification />} />
            <Route path="/verify/:battery_id" element={<PublicVerification />} />

            {/* EV Owner Portal */}
            <Route path="/owner" element={<OwnerLayout />}>
              <Route index element={<OwnerDashboard />} />
              <Route path="batteries" element={<MyBatteries />} />
              <Route path="centers" element={<FindServiceCenters />} />
              <Route path="recommendations" element={<Recommendations />} />
              <Route path="offers" element={<ExchangeOffers />} />
              <Route path="impact" element={<EnvironmentalImpact />} />
              <Route path="passport" element={<MyBatteryPassport />} />
            </Route>

            {/* Technician Portal */}
            <Route path="/tech" element={<TechLayout />}>
              <Route index element={<TechnicianDashboard />} />
              <Route path="queue" element={<BatteryQueue />} />
              <Route path="screening" element={<BatteryScreening />} />
              <Route path="what-if" element={<WhatIfSimulator />} />
              <Route path="approval" element={<ApprovalPassport />} />
            </Route>

            {/* Recycler Portal */}
            <Route path="/recycler" element={<RecyclerLayout />}>
              <Route index element={<ImpactSummary />} />
              <Route path="batches" element={<BatchSorting />} />
              <Route path="pack-grouping" element={<PackGrouping />} />
            </Route>

            {/* Fallback */}
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </BrowserRouter>
      </BatteryProvider>
    </DataSourceProvider>
  );
}

