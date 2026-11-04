import React from 'react';
import { Outlet } from 'react-router-dom';
import Navbar from '../../components/Navbar';
import Sidebar from '../../components/Sidebar';

export default function TechLayout() {
  return (
    <div className="min-h-screen bg-slate-50 flex flex-col">
      <Navbar role="tech" roleTitle="Service Center Technician" />
      <div className="flex-1 flex">
        <Sidebar portal="tech" />
        <main className="flex-1 p-6 lg:p-8 max-w-7xl mx-auto w-full overflow-y-auto">
          <Outlet />
        </main>
      </div>
    </div>
  );
}

