"use client";

import { useState, useMemo, useEffect } from "react";
import useSWR from "swr";
import { fetcher, API_BASE } from "@/lib/fetcher";
import { ChevronLeft, ChevronRight, Hash, Clock } from "lucide-react";

interface WhaleListProps {
  onSelect?: (whale: any) => void;
  selectedAddress?: string | null;
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

function getActivityLabel(whale: any) {
  if (whale.last_active_time) {
    return formatRelativeTime(whale.last_active_time);
  }
  if (whale.last_synced) {
    return `已同步 ${formatRelativeTime(whale.last_synced)}`;
  }
  return "暂无活跃记录";
}

export default function WhaleList({ onSelect, selectedAddress }: WhaleListProps) {
  const [page, setPage] = useState(1);
  const pageSize = 10;
  
  // Fetch 50 whales for client-side pagination as per instruction
  const { data, error, isLoading } = useSWR(`${API_BASE}/whales?page=1&size=50`, fetcher, {
    refreshInterval: 30000,
  });

  const allWhales = data?.data || [];
  const totalWhales = allWhales.length;
  const totalPages = Math.max(1, Math.ceil(totalWhales / pageSize));
  
  const paginatedWhales = useMemo(() => {
    return allWhales.slice((page - 1) * pageSize, page * pageSize);
  }, [allWhales, page, pageSize]);

  // Handle case where current page might be out of bounds after data refresh
  useEffect(() => {
    if (page > totalPages && totalPages > 0) {
      setPage(totalPages);
    }
  }, [totalPages, page]);

  if (error) return <div className="p-4 text-red-400 text-xs font-mono">LIST_ERROR: {error.message}</div>;

  return (
    <div className="cyber-card flex flex-col h-full">
      <div className="scanline"></div>
      
      <div className="p-4 border-b border-white/5 flex items-center justify-between bg-white/2">
        <h2 className="text-xs font-black flex items-center gap-2 text-primary uppercase tracking-[0.2em]">
          <Hash size={14} className="opacity-50" />
          巨鲸监控名单 <span className="text-gray-600 font-mono">(TOTAL: {totalWhales})</span>
        </h2>
      </div>

      <div className="flex-1 overflow-y-auto custom-scrollbar p-2">
        <div className="space-y-2">
          {isLoading ? (
            Array.from({ length: 10 }).map((_, i) => (
              <div key={i} className="animate-pulse flex items-center gap-3 p-3 rounded bg-white/5">
                <div className="w-10 h-10 rounded bg-white/10"></div>
                <div className="flex-1 space-y-2">
                   <div className="h-2 bg-white/10 rounded w-1/2"></div>
                   <div className="h-2 bg-white/10 rounded w-1/4"></div>
                </div>
              </div>
            ))
          ) : paginatedWhales.map((whale: any, index: number) => {
            const isSelected = selectedAddress?.toLowerCase() === whale.address?.toLowerCase();
            
            return (
              <div 
                key={whale.address} 
                onClick={() => onSelect?.(whale)}
                className={`group flex items-center gap-3 p-3 rounded cursor-pointer transition-all border ${
                  isSelected 
                    ? "bg-primary/10 border-primary shadow-[0_0_15px_rgba(0,255,163,0.3)]" 
                    : "border-transparent hover:bg-white/5 hover:border-white/10"
                }`}
              >
                <div className="text-[10px] font-mono text-gray-700 w-4 font-bold">
                  {((page - 1) * pageSize + index + 1).toString().padStart(2, '0')}
                </div>
                
                {/* Identicon */}
                <div className="w-10 h-10 rounded-lg overflow-hidden border border-white/10 bg-black/40 flex-shrink-0">
                  <img 
                    src={`https://api.dicebear.com/7.x/identicon/svg?seed=${whale.address}`} 
                    alt="avatar" 
                    className="w-full h-full opacity-80"
                  />
                </div>

                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <p className={`text-xs font-mono truncate ${
                      isSelected ? "text-primary" : "text-gray-400 group-hover:text-white"
                    }`}>
                      {whale.address}
                    </p>
                  </div>
                  
                  <div className="flex items-center gap-2 mt-1">
                    <span className={`text-[8px] font-bold uppercase tracking-widest ${isSelected ? 'text-primary' : 'text-gray-500'}`}>
                       {whale.entity_label || 'Mega Whale'}
                    </span>
                    <span className="text-gray-700 text-[8px]">•</span>
                    <div className="flex items-center gap-1">
                       <Clock size={8} className="text-gray-600" />
                       <span className="text-[8px] text-gray-600 font-bold uppercase">
                         {getActivityLabel(whale)}
                       </span>
                    </div>
                  </div>
                </div>

                <div className="text-right">
                  <p className={`text-sm font-black italic tracking-tighter ${
                    isSelected ? "text-primary neon-text-green" : "text-white"
                  }`}>
                    {Math.round(whale.total_eth_out || 0).toLocaleString()}
                  </p>
                  <p className="text-[8px] uppercase text-gray-600 font-bold">ETH OUT</p>
                </div>
              </div>
            );
          })}
        </div>
        
        {!isLoading && paginatedWhales.length === 0 && (
           <div className="flex flex-col items-center justify-center py-20 opacity-20">
             <p className="text-xs font-mono tracking-widest uppercase">No data found</p>
           </div>
        )}
      </div>

      {/* Pagination Container */}
      <div className="flex items-center justify-between p-4 border-t border-white/5 bg-black/20">
        <button
          onClick={() => setPage(p => Math.max(1, p - 1))}
          disabled={page === 1}
          className="p-1.5 rounded bg-white/5 hover:bg-primary/20 disabled:opacity-10 transition-all text-primary border border-white/10 backdrop-blur-md"
        >
          <ChevronLeft size={16} />
        </button>
        <div className="text-[10px] font-bold text-gray-500 tracking-[0.2em] uppercase">
          PAGE <span className="text-primary">{page}</span> OF {totalPages}
        </div>
        <button
          onClick={() => setPage(p => Math.min(totalPages, p + 1))}
          disabled={page >= totalPages}
          className="p-1.5 rounded bg-white/5 hover:bg-primary/20 disabled:opacity-10 transition-all text-primary border border-white/10 backdrop-blur-md"
        >
          <ChevronRight size={16} />
        </button>
      </div>
    </div>
  );
}
