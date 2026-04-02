"use client";

import { Wallet, History, Info, Clock } from "lucide-react";

interface WhaleDetailProps {
  whale: any;
}

function formatRelativeTime(isoString: string) {
  if (!isoString) return "N/A";
  try {
    const date = new Date(isoString);
    const now = new Date();
    const diffInSeconds = Math.floor((now.getTime() - date.getTime()) / 1000);

    if (isNaN(diffInSeconds)) return "N/A";
    if (diffInSeconds < 60) return "刚刚";
    if (diffInSeconds < 3600) return `${Math.floor(diffInSeconds / 60)}分钟前`;
    if (diffInSeconds < 86400) return `${Math.floor(diffInSeconds / 3600)}小时前`;
    return `${Math.floor(diffInSeconds / 86400)}天前`;
  } catch (e) {
    return "N/A";
  }
}

function getPrimaryActivityText(whale: any) {
  if (whale.last_active_time) {
    return formatRelativeTime(whale.last_active_time);
  }
  return "暂无活跃记录";
}

function getSecondaryActivityText(whale: any) {
  if (whale.last_active_time) {
    return new Date(whale.last_active_time).toLocaleString();
  }
  if (whale.last_synced) {
    return `名单同步时间：${new Date(whale.last_synced).toLocaleString()}`;
  }
  return "N/A";
}

export default function WhaleDetail({ whale }: WhaleDetailProps) {
  if (!whale) {
    return (
      <div className="cyber-card flex-1 flex flex-col items-center justify-center p-8 text-center opacity-30 min-h-[600px]">
        <div className="w-20 h-20 rounded-full border border-dashed border-gray-600 animate-spin-slow mb-6 flex items-center justify-center">
          <Wallet size={32} />
        </div>
        <h3 className="text-sm font-black uppercase tracking-[0.4em]">Select a Whale</h3>
        <p className="text-[10px] mt-2 font-mono uppercase tracking-widest">To view detailed intelligence</p>
      </div>
    );
  }

  const totalEthOut = whale.total_eth_out || 0;
  const txCount = whale.tx_count || 0;
  const avgTxValue = txCount > 0 ? (totalEthOut / txCount).toFixed(2) : "0.00";

  return (
    <div className="cyber-card flex-1 flex flex-col h-full overflow-hidden">
      <div className="scanline"></div>
      
      <div className="p-4 border-b border-white/5 bg-white/2">
        <h2 className="text-xs font-black flex items-center gap-2 text-primary uppercase tracking-[0.2em]">
          <Info size={14} className="opacity-50" />
          应链信息 / INTELLIGENCE
        </h2>
      </div>

      <div className="p-6 space-y-8 overflow-y-auto custom-scrollbar">
        {/* BALANCE AREA */}
        <div className="space-y-2">
          <div className="flex items-center gap-2 text-[10px] font-bold text-gray-500 uppercase tracking-widest">
            <Wallet size={12} className="text-primary" />
            BALANCE / TOTAL ETH OUT
          </div>
          <div className="text-4xl font-black italic text-white flex items-baseline gap-2">
            {totalEthOut.toLocaleString()} <span className="text-xs font-medium text-primary/60 not-italic">ETH</span>
          </div>
          <div className="text-[10px] font-bold text-gray-600 uppercase tracking-tighter">
            ENTITY: <span className="text-primary">{whale.entity_label || 'Mega Whale'}</span>
          </div>
        </div>

        {/* HISTORY AREA */}
        <div className="space-y-4">
          <div className="flex items-center gap-2 text-[10px] font-bold text-gray-500 uppercase tracking-widest border-b border-white/5 pb-2">
            <History size={12} className="text-primary" />
            HISTORY
          </div>
          
          <div className="grid grid-cols-2 gap-6">
            <div className="space-y-1">
              <div className="text-2xl font-black text-white font-mono">{txCount}</div>
              <div className="text-[9px] text-gray-600 uppercase font-bold tracking-widest">Tx Count</div>
            </div>
            <div className="space-y-1">
              <div className="text-2xl font-black text-primary font-mono">{avgTxValue}</div>
              <div className="text-[9px] text-gray-600 uppercase font-bold tracking-widest">Avg Value (ETH)</div>
            </div>
          </div>
        </div>

        {/* LAST ACTIVE AREA */}
        <div className="space-y-4 pt-4">
           <div className="flex items-center gap-2 text-[10px] font-bold text-gray-500 uppercase tracking-widest border-b border-white/5 pb-2">
            <Clock size={12} className="text-primary" />
            LAST ACTIVE (BLOCK TIME)
          </div>
          <div className="flex items-center gap-3">
             <div className="p-3 bg-white/5 rounded border border-white/5 flex-1">
                <div className="text-lg font-black text-white font-mono">{getPrimaryActivityText(whale)}</div>
                <div className="text-[8px] text-gray-600 uppercase font-bold mt-1 tracking-widest">
                   {getSecondaryActivityText(whale)}
                </div>
             </div>
          </div>
        </div>

        {/* IDENTITY AREA */}
        <div className="pt-8">
           <div className="text-[8px] font-mono text-gray-700 break-all uppercase border-t border-white/5 pt-4">
              Address: {whale.address || 'Unknown'}
           </div>
        </div>
      </div>
    </div>
  );
}
