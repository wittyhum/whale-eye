"use client";

import useSWR from "swr";
import { fetcher, API_BASE } from "@/lib/fetcher";
import { Activity, Droplets, Server } from "lucide-react";

export default function WhaleStats() {
  const { data, error } = useSWR(`${API_BASE}/stats`, fetcher, {
    refreshInterval: 5000,
  });

  if (error) return <div className="text-red-500">加载数据失败</div>;
  if (!data) return <div className="animate-pulse">数据同步中...</div>;

  const isNetPositive = data.netflow_24h > 0;

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
      <div className="glass p-5 rounded-2xl flex items-center gap-5 border-l-4 border-l-primary shadow-xl">
        <div className="p-3 bg-primary/10 rounded-xl">
          <Droplets className="text-primary" size={28} />
        </div>
        <div>
          <p className="text-gray-400 text-xs font-medium mb-1">24H 净流入 (ETH)</p>
          <p className={`text-3xl font-black ${isNetPositive ? 'text-primary' : 'text-secondary'} neon-text-${isNetPositive ? 'green' : 'red'}`}>
            {isNetPositive ? '+' : ''}{data.netflow_24h.toLocaleString(undefined, { maximumFractionDigits: 2 })}
          </p>
        </div>
      </div>

      <div className="glass p-5 rounded-2xl flex items-center gap-5 border-l-4 border-l-blue-500 shadow-xl">
        <div className="p-3 bg-blue-500/10 rounded-xl">
          <Activity className="text-blue-400" size={28} />
        </div>
        <div>
          <p className="text-gray-400 text-xs font-medium mb-1">活跃巨鲸数量</p>
          <p className="text-3xl font-black text-white">{data.active_whales}</p>
        </div>
      </div>

      <div className="glass p-5 rounded-2xl flex items-center gap-5 border-l-4 border-l-gray-600 shadow-xl">
        <div className="p-3 bg-gray-500/10 rounded-xl">
          <Server className="text-gray-400" size={28} />
        </div>
        <div>
          <p className="text-gray-400 text-xs font-medium mb-1">监控系统状态</p>
          <div className="flex items-center gap-2 mt-1">
            <div className="w-2.5 h-2.5 rounded-full bg-green-500 animate-pulse"></div>
            <p className="text-lg font-bold text-gray-200">运行正常</p>
          </div>
        </div>
      </div>
    </div>
  );
}
