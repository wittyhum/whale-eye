"use client";

import useSWR from "swr";
import { motion, AnimatePresence } from "framer-motion";
import { fetcher, API_BASE } from "@/lib/fetcher";
import { ExternalLink, Zap, ArrowDownLeft, ArrowUpRight, Repeat, ShieldAlert } from "lucide-react";

const CEX_MAP: Record<string, string> = {
  "0x28c6c06290d514ddd8897310521de05a3918a4b3": "Binance: Hot Wallet",
  "0x56eddb7aa87536c09ccc2793473599fd21a8b17f": "Binance: Wallet",
  "0xdfd5293d8e347dfe59e90efd55b2956a1343963d": "Binance: Wallet 2",
  "0x3f5ce5fbfe3e9af3971dd833d26ba9b5c936f0be": "Binance: Cold Wallet",
};

export default function AlertFeed() {
  const { data: alerts, error } = useSWR(`${API_BASE}/alerts`, fetcher, {
    refreshInterval: 5000,
  });

  const getSemanticInfo = (from: string, to: string) => {
    const fromLower = from.toLowerCase();
    const toLower = to.toLowerCase();
    
    if (CEX_MAP[toLower]) {
        return {
          title: "🚨 巨鲸充值：抛售预警",
          color: "text-secondary neon-text-red",
          bgColor: "bg-secondary/10",
          borderColor: "border-secondary/30",
          icon: <ArrowUpRight className="text-secondary" size={14} />
        };
    }
    
    if (CEX_MAP[fromLower]) {
        return {
          title: "🏦 巨鲸提现：机构囤货",
          color: "text-primary neon-text-green",
          bgColor: "bg-primary/10",
          borderColor: "border-primary/30",
          icon: <ArrowDownLeft className="text-primary" size={14} />
        };
    }

    return {
      title: "锁仓行为 / Transfer",
      color: "text-accent-blue neon-text-blue",
      bgColor: "bg-accent-blue/10",
      borderColor: "border-accent-blue/30",
      icon: <Repeat className="text-accent-blue" size={14} />
    };
  };

  if (!alerts || alerts.length === 0) {
    return (
      <div className="cyber-card flex-1 flex flex-col items-center justify-center p-12 min-h-[400px]">
        <div className="relative w-48 h-48 mb-8 flex items-center justify-center">
           <div className="absolute inset-0 rounded-full border border-primary/20 animate-pulse"></div>
           <div className="absolute inset-4 rounded-full border border-primary/10 animate-ping"></div>
           <ShieldAlert className="text-primary opacity-20" size={48} />
        </div>
        <div className="text-center">
           <h3 className="text-sm font-black text-primary uppercase tracking-[0.4em] mb-2 animate-pulse">Scanning Mainnet...</h3>
           <p className="text-[10px] font-mono text-gray-500 uppercase tracking-widest">System Stable. No whale movement detected.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="cyber-card flex-1 flex flex-col min-h-[400px]">
      <div className="p-4 border-b border-white/5 flex items-center justify-between bg-white/2">
        <h2 className="text-xs font-black flex items-center gap-2 text-primary uppercase tracking-[0.2em]">
          <Zap size={14} className="opacity-50" />
          资金流向语义化时间轴 / SEMANTIC TIMELINE
        </h2>
      </div>

      <div className="flex-1 overflow-y-auto custom-scrollbar p-6 relative">
        {/* Timeline dotted line */}
        <div className="absolute left-10 top-6 bottom-6 w-px border-l border-dashed border-white/10"></div>

        <div className="space-y-6">
          <AnimatePresence initial={false}>
            {alerts?.map((alert: any) => {
              const semantic = getSemanticInfo(alert.from_addr, alert.to_addr);
              const timeStr = new Date(alert.created_at).toLocaleTimeString('zh-CN', { hour12: false });

              return (
                <motion.div
                  key={alert.tx_hash}
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  className="relative pl-12 group"
                >
                  {/* Timeline dot */}
                  <div className="absolute left-[37px] top-2 w-2 h-2 rounded-full bg-white/20 border border-white/10 z-10"></div>
                  
                  <div className={`p-4 rounded border transition-all hover:brightness-110 ${semantic.bgColor} ${semantic.borderColor}`}>
                    <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                       <div className="flex items-start gap-4">
                          <div className="text-[10px] font-mono text-gray-600 font-bold mt-1 whitespace-nowrap">{timeStr}</div>
                          <div className="flex flex-col">
                             <div className="flex items-center gap-2">
                                <span className={`text-xs font-black tracking-tight ${semantic.color}`}>{semantic.title}</span>
                                <span className="text-[10px] font-mono text-gray-500 font-bold">
                                   {alert.from_addr.slice(0, 6)}...{alert.from_addr.slice(-4)} → {alert.to_addr.slice(0, 6)}...{alert.to_addr.slice(-4)}
                                </span>
                             </div>
                             <div className="flex items-center gap-3 mt-1.5">
                                <span className="text-lg font-black text-white italic">
                                   {parseFloat(alert.eth_value).toLocaleString()} <span className="text-[10px] font-medium not-italic opacity-50">ETH</span>
                                </span>
                             </div>
                          </div>
                       </div>

                       <div className="flex items-center gap-3 self-end md:self-center">
                          <a
                           href={`https://etherscan.io/tx/${alert.tx_hash}`}
                           target="_blank"
                           rel="noopener noreferrer"
                           className="p-2 bg-black/40 hover:bg-primary/20 rounded transition-all border border-white/5 text-gray-500 hover:text-primary"
                         >
                           <ExternalLink size={14} />
                         </a>
                       </div>
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
