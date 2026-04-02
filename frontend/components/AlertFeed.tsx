"use client";

import useSWR from "swr";
import { motion, AnimatePresence } from "framer-motion";
import { fetcher, API_BASE } from "@/lib/fetcher";
import { ExternalLink, Zap, ArrowDownLeft, ArrowUpRight, Repeat } from "lucide-react";

export default function AlertFeed() {
  const { data: alerts, error } = useSWR(`${API_BASE}/alerts`, fetcher, {
    refreshInterval: 5000,
  });

  const getSemanticInfo = (direction: string) => {
    switch (direction) {
      case 'Deposit':
        return {
          label: '潜在抛售预警',
          action: '[Deposit to Binance]',
          color: 'text-secondary neon-text-red',
          bgColor: 'bg-secondary/10',
          borderColor: 'border-secondary/30',
          icon: <ArrowUpRight className="text-secondary" size={14} />,
          identColor: 'bg-secondary'
        };
      case 'Withdrawal':
        return {
          label: '机构囤货信号',
          action: '[Withdrawal to Whale]',
          color: 'text-primary neon-text-green',
          bgColor: 'bg-primary/10',
          borderColor: 'border-primary/30',
          icon: <ArrowDownLeft className="text-primary" size={14} />,
          identColor: 'bg-primary'
        };
      default:
        return {
          label: '锁仓行为 / Transfer',
          action: '[Whale to Cold Wallet]',
          color: 'text-accent-blue neon-text-blue',
          bgColor: 'bg-accent-blue/10',
          borderColor: 'border-accent-blue/30',
          icon: <Repeat className="text-accent-blue" size={14} />,
          identColor: 'bg-accent-blue'
        };
    }
  };

  if (alerts && alerts.length === 0) {
    return (
      <div className="cyber-card flex-1 flex flex-col items-center justify-center p-12 min-h-[400px]">
        <div className="relative w-48 h-48 mb-8">
           {/* Radar Scanner */}
           <div className="absolute inset-0 rounded-full border border-primary/20"></div>
           <div className="absolute inset-0 rounded-full border border-primary/10 scale-75"></div>
           <div className="absolute inset-0 rounded-full border border-primary/5 scale-50"></div>
           <div className="absolute inset-0 radar-gradient rounded-full animate-[radar-scan_4s_linear_infinite]"></div>
           <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-1 h-1 bg-primary rounded-full shadow-[0_0_10px_#00ffa3]"></div>
        </div>
        <div className="text-center">
           <h3 className="text-sm font-black text-primary uppercase tracking-[0.4em] mb-2 animate-pulse">Scanning Mainnet...</h3>
           <p className="text-[10px] font-mono text-gray-500 uppercase tracking-widest">CALM ATM. NO WHALE MOVEMENT DETECTED.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="cyber-card flex-1 flex flex-col min-h-[400px]">
      <div className="p-4 border-b border-white/5 flex items-center justify-between bg-white/2">
        <h2 className="text-xs font-black flex items-center gap-2 text-primary uppercase tracking-[0.2em]">
          <Zap size={14} className="opacity-50" />
          资金流向语义化时间轴 / SEMANTIC INTELLIGENCE FEED
        </h2>
      </div>

      <div className="flex-1 overflow-y-auto custom-scrollbar p-4 relative">
        {/* Timeline line */}
        <div className="absolute left-6 top-4 bottom-4 w-px bg-white/5"></div>

        <div className="space-y-4">
          <AnimatePresence initial={false}>
            {alerts?.map((alert: any) => {
              const semantic = getSemanticInfo(alert.direction);
              const date = new Date(alert.created_at);
              const timeStr = date.toLocaleTimeString('zh-CN', { hour12: false });

              return (
                <motion.div
                  key={alert.tx_hash}
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  className="relative pl-10 group"
                >
                  {/* Timeline dot */}
                  <div className={`absolute left-[1.125rem] top-2 w-2 h-2 rounded-full border-2 border-[#0d1117] z-10 ${semantic.identColor}`}></div>
                  
                  <div className={`flex items-center justify-between p-3 rounded border ${semantic.bgColor} ${semantic.borderColor} transition-all hover:brightness-125`}>
                    <div className="flex items-center gap-4">
                       <span className="text-[10px] font-mono text-gray-600 font-bold">{timeStr}</span>
                       <div className="flex items-center gap-2">
                          <div className="w-6 h-6 rounded bg-black/40 flex items-center justify-center border border-white/5">
                             <img 
                               src={`https://api.dicebear.com/7.x/identicon/svg?seed=${alert.from_addr}`} 
                               alt="from" 
                               className="w-4 h-4 opacity-60"
                             />
                          </div>
                          <div className="flex flex-col">
                             <div className="flex items-center gap-2">
                                <span className={`text-xs font-black tracking-tight ${semantic.color}`}>{semantic.label}</span>
                                <span className="text-[10px] font-mono text-gray-400 font-bold">{semantic.action}</span>
                             </div>
                             <div className="flex items-center gap-1 text-[9px] text-gray-500 font-bold uppercase mt-0.5">
                                <span>{parseFloat(alert.eth_value).toLocaleString()} ETH</span>
                                <span className="opacity-20 mx-1">|</span>
                                <span>{alert.from_addr.slice(0, 6)}...{alert.from_addr.slice(-4)}</span>
                             </div>
                          </div>
                       </div>
                    </div>

                    <div className="flex items-center gap-3">
                       <div className="w-6 h-6 rounded bg-black/40 flex items-center justify-center border border-white/5">
                          <img 
                            src={`https://api.dicebear.com/7.x/identicon/svg?seed=${alert.to_addr}`} 
                            alt="to" 
                            className="w-4 h-4 opacity-60"
                          />
                       </div>
                       <a
                        href={`https://etherscan.io/tx/${alert.tx_hash}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="p-1.5 bg-black/40 hover:bg-primary/20 rounded transition-all border border-white/5 text-gray-500 hover:text-primary"
                      >
                        <ExternalLink size={12} />
                      </a>
                    </div>
                  </div>
                </motion.div>
              );
            })}
          </AnimatePresence>
        </div>
      </div>
    </div>
  );
}
