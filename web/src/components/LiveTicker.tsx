"use client";

import React from "react";
import { Zap, TrendingUp, ShieldCheck, Flame, ArrowUpRight } from "lucide-react";
import { SteamAlert, PortfolioSummary } from "../types";

interface LiveTickerProps {
  alerts: SteamAlert[];
  summary: PortfolioSummary;
  onSelectAlert: (alert: SteamAlert) => void;
}

export const LiveTicker: React.FC<LiveTickerProps> = ({ alerts, summary, onSelectAlert }) => {
  return (
    <div className="bg-cyber-card/80 border-b border-cyber-border py-2 px-4 sm:px-6 lg:px-8 overflow-hidden relative">
      <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-3 text-xs">
        {/* Left: Summary Metric Pills */}
        <div className="flex items-center flex-wrap gap-2.5 shrink-0">
          <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-emerald-500/10 border border-emerald-500/20 text-emerald-300 font-mono">
            <TrendingUp className="w-3.5 h-3.5 text-emerald-400" />
            <span>NET PNL:</span>
            <strong className="text-emerald-400">+${summary.net_pnl.toFixed(2)}</strong>
            <span className="text-[10px] text-emerald-500/80">({summary.roi_pct > 0 ? `+${summary.roi_pct}%` : `${summary.roi_pct}%`} ROI)</span>
          </div>

          <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-cyan-500/10 border border-cyan-500/20 text-cyan-300 font-mono">
            <ShieldCheck className="w-3.5 h-3.5 text-cyan-400" />
            <span>WIN RATE:</span>
            <strong className="text-white">{summary.win_rate_pct}%</strong>
          </div>

          <div className="hidden sm:flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-purple-500/10 border border-purple-500/20 text-purple-300 font-mono">
            <span>CLV ALPHA:</span>
            <strong className="text-purple-300">+{summary.avg_clv_pct}%</strong>
          </div>
        </div>

        {/* Right: Urgent Steam Flash Alert */}
        {alerts.length > 0 && (
          <div className="flex items-center gap-2 overflow-hidden w-full md:w-auto justify-end">
            <span className="flex items-center gap-1 text-amber-400 font-bold shrink-0 text-[11px] uppercase tracking-wider font-mono">
              <Flame className="w-3.5 h-3.5 text-amber-400 animate-pulse-fast" />
              HOT ARBITRAGE STEAM:
            </span>
            <div
              onClick={() => onSelectAlert(alerts[0])}
              className="flex items-center gap-2 px-3 py-1 rounded bg-amber-500/15 border border-amber-500/30 text-amber-200 hover:bg-amber-500/25 cursor-pointer transition-colors max-w-full truncate text-[11px] font-mono group"
            >
              <span className="font-semibold text-white group-hover:text-amber-300 transition-colors">
                {alerts[0].match_name}
              </span>
              <span className="text-slate-400">→</span>
              <span className="bg-amber-400/20 px-1.5 py-0.5 rounded text-amber-300 font-bold">
                {alerts[0].selection} @ {alerts[0].stake_current_odds}
              </span>
              <span className="text-emerald-400 font-bold">
                +{alerts[0].lag_edge_pct}% Edge
              </span>
              <ArrowUpRight className="w-3 h-3 text-amber-400 shrink-0" />
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

