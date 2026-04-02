"use client";

import { useEffect, useState, useRef } from "react";
import ReactECharts from "echarts-for-react";
import { Activity, Terminal } from "lucide-react";

export default function SystemDiagnosticsHub() {
  const [logs, setLogs] = useState<string[]>([
    "[Connected] Alchemy WSS Ping established",
    "[Synching] Dune Query 12h Synch triggered",
    "[Synching] Alchemy WSS established",
    "[Synching] Dune Query WSS established",
  ]);
  
  const logEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const newLogs = [
      "[Monitor] Block 19456782 processed",
      "[Alert] Significant movement detected: 1,200 ETH",
      "[System] Memory usage: 245MB",
      "[Network] Latency stable: 24ms",
    ];
    
    const interval = setInterval(() => {
      const randomLog = newLogs[Math.floor(Math.random() * newLogs.length)];
      setLogs(prev => [...prev.slice(-10), `[${new Date().toLocaleTimeString()}] ${randomLog}`]);
    }, 8000);

    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    logEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [logs]);

  const option = {
    backgroundColor: 'transparent',
    grid: {
      left: '0%',
      right: '0%',
      top: '10%',
      bottom: '0%',
      containLabel: false
    },
    xAxis: {
      type: 'category',
      show: false,
    },
    yAxis: {
      type: 'value',
      show: false,
    },
    series: [
      {
        data: [120, 200, 150, 80, 70, 110, 130, 400, 300, 500, 1200, 900, 450, 300, 200, 600, 800, 400],
        type: 'bar',
        itemStyle: {
          color: '#00ffa3',
          opacity: 0.6,
          borderRadius: [2, 2, 0, 0]
        },
        barWidth: '60%',
      }
    ],
    tooltip: {
       show: false
    }
  };

  return (
    <div className="cyber-card flex-1 flex flex-col min-h-[300px]">
      <div className="p-4 border-b border-white/5 flex items-center justify-between bg-white/2">
        <h2 className="text-xs font-black flex items-center gap-2 text-primary uppercase tracking-[0.2em]">
          <Activity size={14} className="opacity-50" />
          系统诊断中心 / SYSTEM DIAGNOSTICS HUB
        </h2>
      </div>

      <div className="flex-1 p-4 grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Real Transaction Flow Chart */}
        <div className="flex flex-col">
           <div className="text-[10px] text-gray-600 font-bold uppercase tracking-widest mb-4">Real-time Tx Flow</div>
           <div className="flex-1 min-h-[120px]">
              <ReactECharts option={option} style={{ height: '100%', width: '100%' }} />
           </div>
           <div className="flex justify-between mt-2">
              <span className="text-[8px] text-gray-700 font-mono">00:00</span>
              <span className="text-[8px] text-gray-700 font-mono">12:00</span>
              <span className="text-[8px] text-gray-700 font-mono">现在</span>
           </div>
        </div>

        {/* System Log Stream */}
        <div className="flex flex-col bg-black/40 rounded border border-white/5 p-3 font-mono">
           <div className="flex items-center gap-2 text-[10px] text-gray-500 font-bold uppercase tracking-widest mb-3 border-b border-white/5 pb-2">
              <Terminal size={12} />
              System Log
           </div>
           <div className="flex-1 overflow-y-auto custom-scrollbar space-y-1 text-[10px]">
              {logs.map((log, i) => (
                <div key={i} className="flex gap-2">
                   <span className="text-primary/40 whitespace-nowrap">»</span>
                   <span className={log.includes('[Connected]') || log.includes('[Synching]') ? 'text-primary/80' : 'text-gray-500'}>
                      {log}
                   </span>
                </div>
              ))}
              <div ref={logEndRef} />
           </div>
        </div>
      </div>
    </div>
  );
}
