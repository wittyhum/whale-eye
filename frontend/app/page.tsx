"use client";

import { useState, useEffect } from "react";
import useSWR from "swr";
import { fetcher, API_BASE } from "@/lib/fetcher";
import SystemIntegrityBar from "@/components/SystemIntegrityBar";
import WhaleList from "@/components/WhaleList";
import WhaleDetail from "@/components/WhaleDetail";
import AlertFeed from "@/components/AlertFeed";

export default function Home() {
  const [selectedWhale, setSelectedWhale] = useState<any>(null);

  // Fetch initial data to set default selected whale
  const { data, error, isLoading } = useSWR(`${API_BASE}/whales?page=1&size=50`, fetcher);

  useEffect(() => {
    if (data?.data && data.data.length > 0 && !selectedWhale) {
      setSelectedWhale(data.data[0]);
    }
  }, [data, selectedWhale]);

  if (error) return <div className="min-h-screen flex items-center justify-center text-red-500 font-mono">API CONNECTION ERROR</div>;

  return (
    <main className="min-h-screen p-6 max-w-[1920px] mx-auto flex flex-col h-screen overflow-hidden">
      {/* Top Section: System Integrity Bar */}
      <SystemIntegrityBar />

      {/* Main Content: 3-Column Layout */}
      <div className="flex-1 grid grid-cols-1 lg:grid-cols-12 gap-6 overflow-hidden min-h-0">

        {/* Left Column: Whale Grid (Whale List) - 3/12 width */}
        <div className="lg:col-span-3 flex flex-col overflow-hidden">
          <WhaleList 
            onSelect={setSelectedWhale} 
            selectedAddress={selectedWhale?.address} 
          />
        </div>

        {/* Middle Column: Whale Detail - 3/12 width */}
        <div className="lg:col-span-3 flex flex-col overflow-hidden">
          <WhaleDetail whale={selectedWhale} />
        </div>

        {/* Right Column: Semantic Timeline - 6/12 width */}
        <div className="lg:col-span-6 flex flex-col overflow-hidden">
          <AlertFeed />
        </div>
      </div>

      {/* Site Footer Decoration */}
      <footer className="mt-6 pt-4 border-t border-white/5 flex flex-col md:flex-row items-center justify-between opacity-30 shrink-0">
        <div className="text-[9px] font-mono tracking-widest uppercase">
          [ SYSTEM LOG: CONNECTION ESTABLISHED // ENCRYPTION AES-256 ]
        </div>
        <div className="flex gap-8 text-[9px] font-bold uppercase tracking-[0.2em]">
          <span>© 2026 Whale-Eye Intel</span>
          <span>Terms of Intelligence</span>
        </div>
      </footer>
    </main>
  );
}
