"use client";

import useSWR from "swr";
import { motion, AnimatePresence } from "framer-motion";
import { fetcher, API_BASE } from "@/lib/fetcher";
import { ArrowRight, ExternalLink, ShieldAlert } from "lucide-react";

export default function AlertFeed() {
  const { data: alerts, error } = useSWR(`${API_BASE}/alerts`, fetcher, {
    refreshInterval: 5000,
  });

  if (error) return <div className="text-red-500 p-6 glass rounded-2xl">实时监控连接异常</div>;

  return (
    <div className="glass rounded-2xl p-6 h-full flex flex-col shadow-2xl border border-white/5">
      <h2 className="text-xl font-bold mb-6 flex items-center gap-3">
        <div className="relative">
          <ShieldAlert className="text-primary" size={24} />
          <span className="absolute -top-1 -right-1 w-2.5 h-2.5 bg-red-500 rounded-full animate-ping"></span>
        </div>
        实时大额异动监控
      </h2>

      <div className="flex-1 overflow-y-auto pr-2 space-y-4">
        <AnimatePresence initial={false}>
          {alerts?.map((alert: any) => (
            <motion.div
              key={alert.tx_hash}
              initial={{ opacity: 0, x: -20, scale: 0.95 }}
              animate={{ opacity: 1, x: 0, scale: 1 }}
              exit={{ opacity: 0, scale: 0.9 }}
              transition={{ duration: 0.3 }}
              className="glass-hover rounded-2xl p-5 flex flex-col md:flex-row items-center justify-between gap-6 border border-white/5 relative overflow-hidden group"
            >
              <div className="absolute top-0 left-0 w-1 h-full bg-gradient-to-b from-primary/50 to-transparent"></div>
              
              <div className="flex items-center gap-5 w-full md:w-auto">
                <div className="hidden md:flex flex-col items-center">
                  <div className={`w-1.5 h-1.5 rounded-full ${alert.direction === 'Deposit' ? 'bg-secondary' : 'bg-primary'}`}></div>
                  <div className="w-px h-10 bg-gray-800 my-1"></div>
                  <div className={`w-1.5 h-1.5 rounded-full ${alert.direction === 'Deposit' ? 'bg-secondary' : 'bg-primary'}`}></div>
                </div>
                
                <div className="flex-1">
                  <div className="flex items-center gap-3">
                    <span className="text-primary font-mono text-sm bg-primary/5 px-2 py-0.5 rounded border border-primary/10">
                      {alert.from_addr.slice(0, 8)}...{alert.from_addr.slice(-6)}
                    </span>
                    <ArrowRight size={16} className="text-gray-600 group-hover:text-primary transition-colors" />
                    <span className="text-blue-400 font-mono text-sm bg-blue-500/5 px-2 py-0.5 rounded border border-blue-500/10">
                      {alert.to_addr.slice(0, 8)}...{alert.to_addr.slice(-6)}
                    </span>
                  </div>
                  <div className="flex items-center gap-3 mt-2 text-[11px] text-gray-500">
                    <span className="font-medium">{new Date(alert.created_at).toLocaleString('zh-CN')}</span>
                    <span className="w-1 h-1 rounded-full bg-gray-700"></span>
                    <span className="uppercase tracking-widest">{alert.direction === 'Deposit' ? '交易所充值' : alert.direction === 'Withdrawal' ? '交易所提现' : '大额转账'}</span>
                  </div>
                </div>
              </div>

              <div className="flex items-center justify-between w-full md:w-auto md:justify-end gap-8 border-t md:border-t-0 border-white/5 pt-3 md:pt-0">
                <div className="text-right">
                  <p className={`text-2xl font-black italic ${alert.direction === 'Deposit' ? 'text-secondary neon-text-red' : 'text-primary neon-text-green'}`}>
                    {parseFloat(alert.eth_value).toLocaleString()} <span className="text-xs italic font-medium opacity-70">ETH</span>
                  </p>
                </div>
                <a
                  href={`https://etherscan.io/tx/${alert.tx_hash}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="p-3 bg-white/5 hover:bg-primary/20 rounded-xl transition-all border border-white/5 hover:border-primary/40 group-hover:scale-110"
                >
                  <ExternalLink size={20} className="text-gray-400 group-hover:text-white" />
                </a>
              </div>
            </motion.div>
          ))}
        </AnimatePresence>
      </div>
    </div>
  );
}
