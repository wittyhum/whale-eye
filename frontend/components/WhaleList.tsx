"use client";

import { useState } from "react";
import useSWR from "swr";
import { fetcher, API_BASE } from "@/lib/fetcher";
import { ChevronLeft, ChevronRight, Hash, ExternalLink } from "lucide-react";

interface WhaleListProps {
  onSelect?: (address: string) => void;
  selectedAddress?: string | null;
}

export default function WhaleList({ onSelect, selectedAddress }: WhaleListProps) {
  const [page, setPage] = useState(1);
  const pageSize = 10;
  
  const { data, error } = useSWR(`${API_BASE}/whales?page=${page}&size=${pageSize}`, fetcher, {
    refreshInterval: 30000,
  });

  const whales = data?.data || [];
  const total = data?.total || 0;
  const totalPages = Math.ceil(total / pageSize);

  return (
    <div className="cyber-card flex flex-col h-full min-h-[600px]">
      <div className="scanline"></div>
      
      <div className="p-4 border-b border-white/5 flex items-center justify-between bg-white/2">
        <h2 className="text-xs font-black flex items-center gap-2 text-primary uppercase tracking-[0.2em]">
          <Hash size={14} className="opacity-50" />
          巨鲸监控名单 <span className="text-gray-600 font-mono">(TOTAL: {total})</span>
        </h2>
        <span className="text-[10px] bg-primary/10 px-2 py-0.5 rounded text-primary border border-primary/20 font-bold">
          TOTAL: {total}
        </span>
      </div>

      <div className="flex-1 overflow-y-auto custom-scrollbar p-2">
        <div className="space-y-1">
          {whales.map((whale: any, index: number) => {
            const isActive = whale.tx_count > 5; // Simple logic for demo
            const isSelected = selectedAddress === whale.address;
            
            return (
              <div 
                key={whale.address} 
                onClick={() => onSelect?.(whale.address)}
                className={`group flex items-center gap-3 p-3 rounded cursor-pointer transition-all border ${
                  isSelected 
                    ? "bg-primary/10 border-primary/40 shadow-[inset_0_0_15px_rgba(0,255,163,0.1)]" 
                    : "border-transparent hover:bg-white/5 hover:border-white/10"
                }`}
              >
                <div className="text-[10px] font-mono text-gray-700 w-4 font-bold group-hover:text-primary/40 transition-colors">
                  {((page - 1) * pageSize + index + 1).toString().padStart(2, '0')}
                </div>
                
                {/* Identicon */}
                <div className="w-10 h-10 rounded-lg overflow-hidden border border-white/10 bg-black/40 flex-shrink-0">
                  <img 
                    src={`https://api.dicebear.com/7.x/identicon/svg?seed=${whale.address}`} 
                    alt="avatar" 
                    className="w-full h-full opacity-80 group-hover:opacity-100 transition-opacity"
                  />
                </div>

                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <p className={`text-xs font-mono truncate transition-colors ${
                      isSelected ? "text-primary" : "text-gray-400 group-hover:text-white"
                    }`}>
                      {whale.address}
                    </p>
                    <a 
                      href={`https://etherscan.io/address/${whale.address}`} 
                      target="_blank" 
                      onClick={(e) => e.stopPropagation()}
                      className="opacity-0 group-hover:opacity-100 transition-opacity"
                    >
                      <ExternalLink size={10} className="text-gray-600 hover:text-primary" />
                    </a>
                  </div>
                  
                  <div className="flex items-center gap-2 mt-1">
                    <div className="flex items-center gap-1.5">
                      <div className={`w-1.5 h-1.5 rounded-full ${isActive ? 'bg-primary animate-pulse shadow-[0_0_5px_#00ffa3]' : 'bg-gray-600'}`}></div>
                      <span className={`text-[8px] font-bold uppercase tracking-widest ${isActive ? 'text-primary/70' : 'text-gray-600'}`}>
                        {isActive ? 'Active' : 'Dormant'}
                      </span>
                    </div>
                    <span className="text-gray-700 text-[8px]">•</span>
                    <span className="text-[8px] text-gray-500 font-bold uppercase tracking-tighter">
                      Total Holding: <span className="text-gray-300">{(whale.total_eth_out * 2.5).toFixed(0)} ETH</span>
                    </span>
                  </div>
                </div>

                <div className="text-right">
                  <p className={`text-sm font-black italic tracking-tighter transition-colors ${
                    isSelected ? "text-primary" : "text-white group-hover:text-primary"
                  }`}>
                    {Math.round(whale.total_eth_out).toLocaleString()}
                  </p>
                  <p className="text-[8px] uppercase text-gray-600 font-bold">ETH OUT</p>
                </div>
              </div>
            );
          })}
        </div>
        
        {whales.length === 0 && (
          <div className="flex flex-col items-center justify-center py-20 opacity-20">
            <div className="w-16 h-16 rounded-full border border-dashed border-primary animate-spin-slow mb-4"></div>
            <p className="text-xs font-mono tracking-widest">SCANNING DATA...</p>
          </div>
        )}
      </div>

      {/* Pagination Container */}
      <div className="flex items-center justify-between p-3 border-t border-white/5 bg-black/20">
        <button
          onClick={() => setPage(p => Math.max(1, p - 1))}
          disabled={page === 1}
          className="p-1 rounded bg-white/2 hover:bg-primary/20 disabled:opacity-10 transition-all text-primary border border-white/5"
        >
          <ChevronLeft size={14} />
        </button>
        <div className="text-[9px] font-bold text-gray-600 tracking-[0.2em] uppercase">
          PAGE <span className="text-primary">{page}</span> / {totalPages || 1}
        </div>
        <button
          onClick={() => setPage(p => Math.min(totalPages, p + 1))}
          disabled={page >= totalPages}
          className="p-1 rounded bg-white/2 hover:bg-primary/20 disabled:opacity-10 transition-all text-primary border border-white/5"
        >
          <ChevronRight size={14} />
        </button>
      </div>
    </div>
  );
}
