"use client";

import { useState } from "react";
import SystemIntegrityBar from "@/components/SystemIntegrityBar";
import WhaleList from "@/components/WhaleList";
import WhaleDetail from "@/components/WhaleDetail";
import AlertFeed from "@/components/AlertFeed";
import SystemDiagnosticsHub from "@/components/SystemDiagnosticsHub";

export default function Home() {
  const [selectedWhale, setSelectedWhale] = useState<string | null>(null);

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
            selectedAddress={selectedWhale} 
          />
        </div>

        {/* Middle Column: Whale Detail - 3/12 width */}
        <div className="lg:col-span-3 flex flex-col overflow-hidden">
          <WhaleDetail address={selectedWhale} />
        </div>

        {/* Right Column: Alerts and Diagnostics - 6/12 width */}
        <div className="lg:col-span-6 flex flex-col gap-6 overflow-hidden">
          {/* Top Half: Semantic Intelligence Feed */}
          <div className="flex-1 overflow-hidden flex flex-col">
            <AlertFeed />
          </div>

          {/* Bottom Half: System Diagnostics Hub */}
          <div className="h-[350px] flex flex-col overflow-hidden">
            <SystemDiagnosticsHub />
          </div>
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
