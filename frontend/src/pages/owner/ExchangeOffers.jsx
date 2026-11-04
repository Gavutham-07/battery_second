import React, { useState } from 'react';
import { useBatteryStore } from '../../context/BatteryContext';
import { Coins, CheckCircle, Clock, ShieldCheck, ArrowRight, AlertCircle } from 'lucide-react';

export default function ExchangeOffers() {
  const { batteries, acceptExchangeOffer } = useBatteryStore();
  const [successMsg, setSuccessMsg] = useState('');

  const handleAccept = (battery_id) => {
    acceptExchangeOffer(battery_id);
    setSuccessMsg(`Exchange offer accepted for ${battery_id}! Exchange voucher has been generated.`);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-xl font-bold text-slate-900">Exchange Offers & Buyback Valuations</h1>
        <p className="text-xs text-slate-500 mt-1">
          Review residual electrochemical valuation and redeem certified buyback credits toward second-life repowering or new vehicle battery packs.
        </p>
      </div>

      {successMsg && (
        <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-xl flex items-center justify-between text-xs text-emerald-800">
          <div className="flex items-center gap-2">
            <CheckCircle className="w-4 h-4 text-emerald-600 shrink-0" />
            <span>{successMsg}</span>
          </div>
          <button onClick={() => setSuccessMsg('')} className="text-emerald-700 font-bold ml-2">✕</button>
        </div>
      )}

      {/* Offers Table / Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
        {batteries.map((b) => {
          const isAssessed = b.status === 'Assessed' || b.status === 'Approved';
          const credit = b.exchange_credit_inr || (b.rated_capacity_ah * 500);

          return (
            <div
              key={b.battery_id}
              className={`bg-white rounded-xl border p-5 shadow-xs flex flex-col justify-between transition-all ${
                b.exchange_offer_accepted ? 'border-emerald-500 bg-emerald-50/20' : 'border-slate-200'
              }`}
            >
              <div>
                <div className="flex items-center justify-between mb-3">
                  <span className="font-bold text-base text-slate-900">{b.battery_id}</span>
                  <span className={`text-[11px] font-semibold px-2 py-0.5 rounded-full ${
                    b.exchange_offer_accepted
                      ? 'bg-emerald-100 text-emerald-800'
                      : (isAssessed ? 'bg-blue-100 text-blue-800' : 'bg-amber-100 text-amber-800')
                  }`}>
                    {b.exchange_offer_accepted ? 'Offer Accepted' : (isAssessed ? 'Offer Available' : 'Pending Screening')}
                  </span>
                </div>

                <div className="text-xs text-slate-600 space-y-1 mb-4">
                  <p><span className="text-slate-400">Chemistry:</span> {b.chemistry} ({b.rated_capacity_ah} Ah)</p>
                  <p><span className="text-slate-400">Diagnostic Status:</span> <span className="font-semibold text-slate-800">{b.status}</span></p>
                  <p><span className="text-slate-400">Assessed SOH:</span> <span className="font-semibold text-slate-800">{b.soh_estimate !== null ? `${b.soh_estimate}%` : 'Pending'}</span></p>
                  <p><span className="text-slate-400">Approval:</span> <span className="font-semibold text-slate-800">{b.passport ? 'Verified Passport Minted' : 'Awaiting Approval'}</span></p>
                </div>

                {isAssessed ? (
                  <div className="p-3 bg-slate-50 rounded-xl border border-slate-100 mb-4">
                    <span className="text-[11px] font-semibold text-slate-500">Calculated Second-Life Valuation</span>
                    <p className="text-2xl font-extrabold text-emerald-600 mt-0.5">
                      ₹{credit.toLocaleString()}
                    </p>
                    <p className="text-[10px] text-slate-400 mt-1">
                      Computed via capacity retention ({b.remaining_capacity_ah} Ah) & market raw material recovery indices.
                    </p>
                  </div>
                ) : (
                  <div className="p-3 bg-amber-50 rounded-xl border border-amber-200 text-xs text-amber-800 mb-4 flex items-start gap-2">
                    <Clock className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
                    <div>
                      <p className="font-semibold">Diagnostic Pending</p>
                      <p className="text-[11px] text-amber-700 mt-0.5">Definitive buyback value will be computed upon 90s screening test.</p>
                    </div>
                  </div>
                )}
              </div>

              <div>
                {b.exchange_offer_accepted ? (
                  <div className="w-full py-2 bg-emerald-100 text-emerald-800 rounded-lg text-xs font-semibold text-center flex items-center justify-center gap-1.5 border border-emerald-200">
                    <CheckCircle className="w-3.5 h-3.5" />
                    <span>Offer Accepted & Credited</span>
                  </div>
                ) : isAssessed ? (
                  <button
                    onClick={() => handleAccept(b.battery_id)}
                    className="w-full py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg text-xs font-semibold transition-colors shadow-xs flex items-center justify-center gap-1.5"
                  >
                    <span>Accept Exchange Offer</span>
                    <ArrowRight className="w-3.5 h-3.5" />
                  </button>
                ) : (
                  <button
                    disabled
                    className="w-full py-2 bg-slate-100 text-slate-400 rounded-lg text-xs font-semibold cursor-not-allowed border border-slate-200 text-center"
                  >
                    Screening Required
                  </button>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

