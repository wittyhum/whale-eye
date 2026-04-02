"use client";

import ReactECharts from "echarts-for-react";
import useSWR from "swr";
import { fetcher, API_BASE } from "@/lib/fetcher";

export default function NetflowChart() {
  const { data: stats } = useSWR(`${API_BASE}/stats`, fetcher, {
    refreshInterval: 10000,
  });

  // Simple mock data based on 24H netflow to show a trend
  const netflow = stats?.netflow_24h || 0;
  
  const option = {
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(23, 27, 34, 0.9)',
      borderColor: 'rgba(0, 255, 163, 0.3)',
      textStyle: { color: '#fff' }
    },
    grid: {
      top: '10%',
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: ['00:00', '04:00', '08:00', '12:00', '16:00', '20:00', '现在'],
      axisLine: { lineStyle: { color: 'rgba(255,255,255,0.1)' } },
      axisLabel: { color: '#666' }
    },
    yAxis: {
      type: 'value',
      splitLine: { lineStyle: { color: 'rgba(255,255,255,0.05)' } },
      axisLabel: { color: '#666' }
    },
    series: [
      {
        name: '24H 净流向趋势',
        type: 'line',
        smooth: true,
        symbol: 'none',
        lineStyle: {
          width: 3,
          color: netflow >= 0 ? '#00FFA3' : '#FF3B69'
        },
        areaStyle: {
          color: {
            type: 'linear',
            x: 0, y: 0, x2: 0, y2: 1,
            colorStops: [
              { offset: 0, color: netflow >= 0 ? 'rgba(0, 255, 163, 0.2)' : 'rgba(255, 59, 105, 0.2)' },
              { offset: 1, color: 'transparent' }
            ]
          }
        },
        data: [
          netflow * 0.2, 
          netflow * 0.5, 
          netflow * 0.3, 
          netflow * 0.8, 
          netflow * 0.6, 
          netflow * 0.9, 
          netflow
        ]
      }
    ]
  };

  return (
    <div className="glass rounded-2xl p-6 shadow-xl border border-white/5">
      <h3 className="text-sm font-medium text-gray-400 mb-4 flex items-center gap-2">
        <span className="w-2 h-2 rounded-full bg-blue-500"></span>
        资金流向实时态势 (24H)
      </h3>
      <div className="h-[200px]">
        <ReactECharts option={option} style={{ height: '100%' }} />
      </div>
    </div>
  );
}
