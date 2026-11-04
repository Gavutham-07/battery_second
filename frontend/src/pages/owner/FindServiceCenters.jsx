import React, { useState } from 'react';
import { MapPin, Search, Navigation, Phone, Clock, CheckCircle2, ShieldCheck, Building2 } from 'lucide-react';

const DEMO_CENTERS = [
  {
    id: 'CTR-01',
    name: 'Bengaluru East Fast Diagnostic Hub',
    area: 'Whitefield, Bengaluru',
    pincode: '560066',
    address: 'Plot 14, EPIP Industrial Zone, Whitefield, Bengaluru',
    distance_km: 3.8,
    phone: '+91 80 4123 9081',
    hours: '08:00 AM – 08:00 PM (Mon-Sat)',
    slots_available: 4,
    estimated_buyback_range: '₹22,000 – ₹38,000',
    certified: true
  },
  {
    id: 'CTR-02',
    name: 'Koramangala EV Battery Testing & Repowering',
    area: 'Koramangala, Bengaluru',
    pincode: '560034',
    address: '80 Feet Road, 4th Block, Koramangala, Bengaluru',
    distance_km: 7.2,
    phone: '+91 80 2553 4410',
    hours: '09:00 AM – 07:00 PM (All days)',
    slots_available: 2,
    estimated_buyback_range: '₹20,000 – ₹35,000',
    certified: true
  },
  {
    id: 'CTR-03',
    name: 'Electronic City Second-Life Transit Depot',
    area: 'Electronic City Phase 1, Bengaluru',
    pincode: '560100',
    address: 'Tech Park Corridor, Electronic City Phase 1, Bengaluru',
    distance_km: 14.5,
    phone: '+91 80 6789 1100',
    hours: '08:30 AM – 06:30 PM (Mon-Fri)',
    slots_available: 6,
    estimated_buyback_range: '₹24,000 – ₹42,000',
    certified: true
  },
  {
    id: 'CTR-04',
    name: 'Chennai Guindy Industrial Diagnostic Hub',
    area: 'Guindy, Chennai',
    pincode: '600032',
    address: 'SIDCO Industrial Estate, Guindy, Chennai',
    distance_km: 340.0,
    phone: '+91 44 2250 8821',
    hours: '09:00 AM – 06:00 PM (Mon-Sat)',
    slots_available: 5,
    estimated_buyback_range: '₹21,000 – ₹36,000',
    certified: true
  }
];

export default function FindServiceCenters() {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCenter, setSelectedCenter] = useState(null);
  const [bookedSuccess, setBookedSuccess] = useState('');
  const [locationUsed, setLocationUsed] = useState(false);

  const handleUseLocation = () => {
    setLocationUsed(true);
    setSearchTerm('Bengaluru Urban');
  };

  const filteredCenters = DEMO_CENTERS.filter(c =>
    c.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    c.area.toLowerCase().includes(searchTerm.toLowerCase()) ||
    c.pincode.includes(searchTerm)
  );

  const handleBook = (center) => {
    setSelectedCenter(center);
    setBookedSuccess(`Screening slot confirmed at ${center.name}! Your registered batteries are mapped for diagnostic intake.`);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-xl font-bold text-slate-900">Find Certified Diagnostic Centers</h1>
        <p className="text-xs text-slate-500 mt-1">
          Locate approved testing hubs equipped with ReVolt 90-second electrochemical screening rigs and QR minting terminals.
        </p>
      </div>

      {bookedSuccess && (
        <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-xl flex items-center justify-between text-xs text-emerald-800">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
            <span>{bookedSuccess}</span>
          </div>
          <button onClick={() => setBookedSuccess('')} className="text-emerald-700 font-bold ml-4">✕</button>
        </div>
      )}

      {/* Search and Location Bar */}
      <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs flex flex-col sm:flex-row items-center gap-3">
        <div className="relative flex-1 w-full">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Search by city, area (e.g. Whitefield, Koramangala) or PIN code (560066)..."
            className="w-full pl-9 pr-3 py-2 text-xs rounded-lg border border-slate-300 focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500"
          />
        </div>

        <button
          onClick={handleUseLocation}
          className="w-full sm:w-auto inline-flex items-center justify-center gap-1.5 px-3.5 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg text-xs font-semibold border border-slate-200 transition-colors whitespace-nowrap"
        >
          <Navigation className="w-3.5 h-3.5 text-emerald-600" />
          <span>{locationUsed ? 'Location Active' : 'Use Current Location'}</span>
        </button>
      </div>

      {/* Centers Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {filteredCenters.map((center) => (
          <div
            key={center.id}
            className={`bg-white rounded-xl border p-5 shadow-xs flex flex-col justify-between transition-all ${
              selectedCenter?.id === center.id ? 'border-emerald-500 ring-2 ring-emerald-500/20' : 'border-slate-200 hover:border-slate-300'
            }`}
          >
            <div>
              <div className="flex items-start justify-between gap-3 mb-2">
                <div>
                  <h3 className="font-bold text-sm text-slate-900">{center.name}</h3>
                  <p className="text-xs text-slate-500 flex items-center gap-1 mt-0.5">
                    <MapPin className="w-3.5 h-3.5 text-slate-400 shrink-0" />
                    <span>{center.address}</span>
                  </p>
                </div>
                <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-50 text-emerald-800 border border-emerald-200 shrink-0">
                  {center.distance_km} km away
                </span>
              </div>

              <div className="my-3 py-3 border-y border-slate-100 grid grid-cols-2 gap-2 text-xs text-slate-600">
                <div className="flex items-center gap-1.5">
                  <Phone className="w-3.5 h-3.5 text-slate-400" />
                  <span>{center.phone}</span>
                </div>
                <div className="flex items-center gap-1.5">
                  <Clock className="w-3.5 h-3.5 text-slate-400" />
                  <span>{center.hours}</span>
                </div>
              </div>

              <div className="flex items-center justify-between text-xs bg-slate-50 p-2.5 rounded-lg border border-slate-100 mb-4">
                <div>
                  <span className="text-[11px] text-slate-400">Est. Buyback Range:</span>
                  <p className="font-bold text-slate-800">{center.estimated_buyback_range}</p>
                </div>
                <div className="text-right">
                  <span className="text-[11px] text-slate-400">Screening Bays:</span>
                  <p className="font-semibold text-emerald-600">{center.slots_available} available today</p>
                </div>
              </div>
            </div>

            <button
              onClick={() => handleBook(center)}
              className="w-full py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg text-xs font-semibold transition-colors shadow-xs"
            >
              Select & Schedule Diagnostic Drop-off
            </button>
          </div>
        ))}
      </div>

      <div className="p-3 bg-slate-100 rounded-lg text-[11px] text-slate-500">
        Demo partner locations displayed for demonstration. Real-world centers require ISO/IEC 17025 accredited battery testing facilities.
      </div>
    </div>
  );
}

