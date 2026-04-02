"use client";

import { useEffect, useState } from "react";
import useSWR from "swr";
import { fetcher, API_BASE } from "@/lib/fetcher";
import { Clock, ShieldCheck, Zap } from "lucide-react";

export default function SystemIntegrityBar() {
  const { data: stats } = useSWR(`${API_BASE}/stats`, fetcher, {
    refreshInterval: 30000,
  });

  const [ping, setPing] = useState(24);
  const [countdown, setCountdown] = useState("04:22:15");

  useEffect(() => {
    const interval = setInterval(() => {
      setPing(Math.floor(Math.random() * (45 - 15) + 15));
    }, 5000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    const timer = setInterval(() => {
      const parts = countdown.split(":").map(Number);
      let s = parts[2] - 1;
      let m = parts[1];
      let h = parts[0];
      if (s < 0) { s = 59; m -= 1; }
      if (m < 0) { m = 59; h -= 1; }
      if (h < 0) { h = 11; m = 59; s = 59; }
      setCountdown(
        `${h.toString().padStart(2, '0')}:${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`
      );
    }, 1000);
    return () => clearInterval(timer);
  }, [countdown]);

  return (
    <div className="flex flex-col lg:flex-row items-center gap-6 mb-8">
      {/* Brand Section */}
      <div className="flex flex-col mr-auto">
        <h1 className="text-4xl font-black tracking-tighter italic leading-none flex items-center gap-2">
          WHALE<span className="text-primary neon-text-green">-EYE</span>
        </h1>
        <div className="flex items-center gap-2 mt-1">
          <span className="text-[10px] font-bold tracking-[0.3em] uppercase text-white/40">
            WEB3 巨鲸情报系统
          </span>
        </div>
      </div>

      {/* Stats Bar */}
      <div className="flex items-center gap-4">
        {/* WSS Ping */}
        <div className="cyber-card px-4 py-3 min-w-[160px] border-accent-blue/20 flex flex-col justify-center">
          <div className="flex items-center gap-2 mb-1">
            <div className="relative">
              <Zap size={14} className="text-accent-blue" />
              <div className="absolute -top-1 -right-1 w-1.5 h-1.5 bg-accent-blue rounded-full animate-pulse shadow-[0_0_8px_#00d1ff]"></div>
            </div>
            <div className="text-[10px] text-gray-500 font-bold uppercase tracking-wider">WSS Ping</div>
          </div>
          <div className="text-xl font-black text-accent-blue font-mono leading-none ml-5">{ping}ms</div>
        </div>

        {/* Last Sync */}
        <div className="cyber-card px-4 py-3 min-w-[180px] border-primary/20 flex flex-col justify-center">
          <div className="flex items-center gap-2 mb-1">
            <div className="relative">
              <Clock size={14} className="text-primary" />
              <div className="absolute -top-1 -right-1 w-1.5 h-1.5 bg-primary rounded-full animate-pulse shadow-[0_0_8px_#00ffa3]"></div>
            </div>
            <div className="text-[10px] text-gray-500 font-bold uppercase tracking-wider">Last Sync 倒计时</div>
          </div>
          <div className="text-xl font-black text-primary font-mono leading-none ml-5">{countdown}</div>
        </div>

        {/* Watchlist Active */}
        <div className="cyber-card px-4 py-3 min-w-[220px] flex flex-col justify-center">
          <div className="flex items-center gap-2 mb-1">
            <div className="relative">
              <ShieldCheck size={14} className="text-white/60" />
              <div className="absolute -top-1 -right-1 w-1.5 h-1.5 bg-primary rounded-full animate-pulse-glow shadow-[0_0_8px_#00ffa3]"></div>
            </div>
            <div className="text-[10px] text-gray-500 font-bold uppercase tracking-wider">Watchlist Active</div>
          </div>
          <div className="flex items-center gap-3 ml-5">
            <span className="text-xl font-black text-white font-mono leading-none">{stats?.active_whales || 50}</span>
            <div className="flex items-center gap-1.5 bg-primary/10 px-2 py-0.5 rounded border border-primary/20">
              <div className="w-1 h-1 bg-primary rounded-full animate-pulse"></div>
              <span className="text-[8px] text-primary font-bold uppercase tracking-widest">Active</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
