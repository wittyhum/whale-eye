"use client";

import { useState } from "react";
import useSWR from "swr";
import { fetcher, API_BASE } from "@/lib/fetcher";
import { User, ChevronLeft, ChevronRight, Hash } from "lucide-react";

export default function WhaleList() {
  const [page, setPage] = useState(1);
  const pageSize = 10;
  
  const { data, error } = useSWR(`${API_BASE}/whales?page=${page}&size=${pageSize}`, fetcher, {
    refreshInterval: 30000,
  });

  const whales = data?.data || [];
  const total = data?.total || 0;
  const totalPages = Math.ceil(total / pageSize);

  return (
    <div className="cyber-box rounded-lg p-5 flex flex-col h-full bg-[#0d1117]/80 shadow-[0_0_50px_rgba(0,0,0,0.5)]">
      <div className="scanline"></div>
      
      <div className="flex items-center justify-between mb-6 border-b border-primary/20 pb-3">
        <h2 className="text-sm font-black flex items-center gap-2 text-primary uppercase tracking-[0.2em] italic">
          <Hash size={16} />
          巨鲸监控名录
        </h2>
        <span className="text-[10px] bg-primary/10 px-2 py-0.5 rounded text-primary border border-primary/20 font-bold">
          TOTAL: {total}
        </span>
      </div>

      <div className="flex-1 space-y-2 overflow-y-auto mb-6 pr-1 custom-scrollbar">
        {whales.map((whale: any, index: number) => (
          <div key={whale.address} className="group flex items-center gap-3 p-2 rounded-lg hover:bg-primary/5 transition-all border border-transparent hover:border-primary/10">
            <div className="text-[10px] font-mono text-gray-600 w-4 font-bold">
              {((page - 1) * pageSize + index + 1).toString().padStart(2, '0')}
            </div>
            
            <div className="flex-1 min-w-0">
              <p className="text-xs font-mono text-gray-400 truncate group-hover:text-primary transition-colors">
                {whale.address}
              </p>
              <div className="flex items-center gap-2 mt-0.5 text-[9px] text-gray-600">
                <span className="uppercase tracking-tighter">交互次数: {whale.tx_count}</span>
              </div>
            </div>

            <div className="text-right">
              <p className="text-xs font-black text-white group-hover:text-primary">
                {Math.round(whale.total_eth_out).toLocaleString()}
              </p>
              <p className="text-[8px] uppercase text-gray-500 font-bold">ETH OUT</p>
            </div>
          </div>
        ))}
        {whales.length === 0 && <div className="text-center py-10 text-gray-600 text-xs">暂无数据</div>}
      </div>

      {/* Pagination Container */}
      <div className="flex items-center justify-between pt-4 border-t border-primary/10 bg-[#0d1117]/50 -mx-5 px-5 rounded-b-lg">
        <button
          onClick={() => setPage(p => Math.max(1, p - 1))}
          disabled={page === 1}
          className="p-1.5 rounded bg-white/5 hover:bg-primary/20 disabled:opacity-20 transition-all text-primary"
        >
          <ChevronLeft size={16} />
        </button>
        <div className="text-[10px] font-bold text-gray-500 tracking-[0.2em] uppercase">
          PAGE <span className="text-primary">{page}</span> OF {totalPages || 1}
        </div>
        <button
          onClick={() => setPage(p => Math.min(totalPages, p + 1))}
          disabled={page >= totalPages}
          className="p-1.5 rounded bg-white/5 hover:bg-primary/20 disabled:opacity-20 transition-all text-primary"
        >
          <ChevronRight size={16} />
        </button>
      </div>
    </div>
  );
}
