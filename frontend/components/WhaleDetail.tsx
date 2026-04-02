"use client";

import { useMemo } from "react";
import { Hash, TrendingUp, Wallet, History, Info } from "lucide-react";

interface WhaleDetailProps {
  address: string | null;
}

export default function WhaleDetail({ address }: WhaleDetailProps) {
  if (!address) {
    return (
      <div className="cyber-card flex-1 flex flex-col items-center justify-center p-8 text-center opacity-30 min-h-[600px]">
        <div className="w-20 h-20 rounded-full border border-dashed border-gray-600 animate-spin-slow mb-6 flex items-center justify-center">
          <Wallet size={32} />
        </div>
        <h3 className="text-sm font-black uppercase tracking-[0.3em]">Select a Whale</h3>
        <p className="text-[10px] mt-2 font-mono uppercase tracking-widest">To view detailed intelligence</p>
      </div>
    );
  }

  return (
    <div className="cyber-card flex-1 flex flex-col min-h-[600px] overflow-hidden">
      <div className="scanline"></div>
      
      <div className="p-4 border-b border-white/5 bg-white/2">
        <h2 className="text-xs font-black flex items-center gap-2 text-primary uppercase tracking-[0.2em]">
          <Info size={14} className="opacity-50" />
          应链信息 / INTELLIGENCE
        </h2>
      </div>

      <div className="p-6 space-y-8 overflow-y-auto custom-scrollbar">
        {/* Balance Card */}
        <div className="space-y-2">
          <div className="flex items-center gap-2 text-[10px] font-bold text-gray-500 uppercase tracking-widest">
            <Wallet size={12} className="text-primary" />
            Balance
          </div>
          <div className="text-3xl font-black italic text-white flex items-baseline gap-2">
            26,295 <span className="text-xs font-medium text-primary/60 not-italic">ETH</span>
          </div>
        </div>

        {/* History Section */}
        <div className="space-y-4">
          <div className="flex items-center gap-2 text-[10px] font-bold text-gray-500 uppercase tracking-widest border-b border-white/5 pb-2">
            <History size={12} className="text-primary" />
            History
          </div>
          
          <div className="space-y-6">
            <div className="space-y-1">
              <div className="text-xl font-black text-white font-mono">1,304,385 ETH</div>
              <div className="text-[9px] text-gray-600 uppercase font-bold tracking-widest">Total Volume</div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="p-3 bg-white/2 rounded border border-white/5">
                <div className="text-[8px] text-gray-600 uppercase font-bold mb-1">Last Sync 倒计时</div>
                <div className="text-sm font-black text-primary font-mono">04:22:15</div>
              </div>
              <div className="p-3 bg-white/2 rounded border border-white/5">
                <div className="text-[8px] text-gray-600 uppercase font-bold mb-1">Token (EHR)</div>
                <div className="text-sm font-black text-white font-mono">0.0683</div>
              </div>
            </div>
          </div>
        </div>

        {/* Additional Mock Stats */}
        <div className="space-y-4 pt-4">
           <div className="flex items-center gap-2 text-[10px] font-bold text-gray-500 uppercase tracking-widest border-b border-white/5 pb-2">
            <TrendingUp size={12} className="text-primary" />
            Performance
          </div>
          <div className="space-y-3">
             <div className="flex justify-between items-end border-b border-white/5 pb-2">
                <span className="text-[9px] text-gray-500 font-bold uppercase">Win Rate</span>
                <span className="text-xs font-black text-primary">68.5%</span>
             </div>
             <div className="flex justify-between items-end border-b border-white/5 pb-2">
                <span className="text-[9px] text-gray-500 font-bold uppercase">Estimated PnL</span>
                <span className="text-xs font-black text-accent-blue">+4,250 ETH</span>
             </div>
          </div>
        </div>
      </div>

      <div className="mt-auto p-4 bg-black/40 border-t border-white/5">
         <div className="text-[8px] font-mono text-gray-600 truncate uppercase tracking-widest">
            Identity: {address}
         </div>
      </div>
    </div>
  );
}
