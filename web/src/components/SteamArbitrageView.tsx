"use client";

import React, { useState } from "react";
import { 
  Zap, 
  Flame, 
  Clock, 
  TrendingDown, 
  ShieldAlert, 
  ArrowUpRight, 
  Calendar,
  Check
} from "lucide-react";
import { motion } from "framer-motion";
import { SteamAlert, ActiveSlipItem } from "../types";

interface SteamArbitrageViewProps {
  alerts: SteamAlert[];
  onAddLeg: (leg: ActiveSlipItem) => void;
}

export const SteamArbitrageView: React.FC<SteamArbitrageViewProps> = ({
  alerts,
  onAddLeg,
}) => {
  const [selectedUrgency, setSelectedUrgency] = useState<string>("ALL");
  const [lockedIds, setLockedIds] = useState<Set<string>>(new Set());

  const filteredAlerts = alerts.filter((a) => {
    if (selectedUrgency === "ALL") return true;
    return a.urgency_level === selectedUrgency;
  });

  const handleLockIn = (alert: SteamAlert) => {
    setLockedIds((prev) => new Set(prev).add(alert.match_id + alert.selection));
    onAddLeg({
      id: `${alert.match_id}_STEAM_${alert.selection}`,
      matchId: alert.match_id,
      matchName: alert.match_name,
      competition: alert.competition,
      kickoffStr: alert.kickoff_str,
      marketType: "1X2 (Steam Arbitrage)",
      selection: `${alert.team_selected} Win`,
      odds: alert.stake_current_odds,
      winProb: 1.0 / alert.pinnacle_fair_odds,
      homeTeam: alert.home_team,
      awayTeam: alert.away_team,
      homeLogo: alert.home_logo,
      awayLogo: alert.away_logo,
    });
  };

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="glass-panel rounded-2xl p-6 border-amber-500/30 bg-gradient-to-r from-amber-950/20 via-cyber-card to-cyber-card">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 text-xs font-mono text-amber-400 mb-1">
              <Flame className="w-4 h-4 animate-pulse-fast" />
              <span>REAL-TIME LATENCY & STEAM ARBITRAGE RADAR</span>
            </div>
            <h2 className="text-xl sm:text-2xl font-black text-white">
              Pinnacle vs Stake Price Velocity Monitor
            </h2>
            <p className="text-sm text-slate-400 max-w-2xl mt-1">
              Sharp syndicates have crushed Pinnacle closing lines. Stake retail mirrors are lagging behind, opening high-alpha latency windows.
            </p>
          </div>

          <div className="flex items-center gap-2">
            {["ALL", "CRITICAL", "HIGH", "MODERATE"].map((lvl) => (
              <button
                key={lvl}
                onClick={() => setSelectedUrgency(lvl)}
                className={`px-3 py-1.5 rounded-xl text-xs font-mono font-bold transition-all ${
                  selectedUrgency === lvl
                    ? "bg-amber-500 text-black shadow-lg shadow-amber-500/20"
                    : "bg-cyber-darkest text-slate-400 hover:text-white border border-cyber-border"
                }`}
              >
                {lvl}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Steam Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {filteredAlerts.length === 0 ? (
          <div className="col-span-full glass-panel rounded-2xl p-12 text-center text-slate-400 font-mono">
            No active steam events matching the {selectedUrgency} filter.
          </div>
        ) : (
          filteredAlerts.map((a, idx) => {
            const isCritical = a.urgency_level === "CRITICAL";
            const isHigh = a.urgency_level === "HIGH";
            const isLocked = lockedIds.has(a.match_id + a.selection);

            return (
              <motion.div
                key={idx}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.2 }}
                className={`glass-panel rounded-2xl p-5 border flex flex-col justify-between ${
                  isCritical
                    ? "border-amber-500/50 bg-amber-950/10"
                    : isHigh
                    ? "border-cyan-500/40 bg-cyan-950/10"
                    : "border-cyber-border bg-cyber-card"
                }`}
              >
                <div>
                  {/* Top Badges */}
                  <div className="flex items-center justify-between mb-3 text-xs font-mono">
                    <span
                      className={`px-2 py-0.5 rounded-full font-bold flex items-center gap-1 ${
                        isCritical
                          ? "bg-amber-500/20 text-amber-300 border border-amber-500/40 animate-pulse"
                          : isHigh
                          ? "bg-cyan-500/20 text-cyan-300 border border-cyan-500/40"
                          : "bg-slate-800 text-slate-300"
                      }`}
                    >
                      <Zap className="w-3 h-3" />
                      {a.urgency_level} URGENCY
                    </span>

                    <span className="text-slate-400 flex items-center gap-1">
                      <Clock className="w-3 h-3" />
                      ~{Math.round(a.estimated_window_seconds / 60)}m window
                    </span>
                  </div>

                  {/* Match Info */}
                  <div className="text-xs text-slate-400 font-mono mb-1 truncate">
                    {a.competition} • {a.kickoff_str}
                  </div>
                  <h3 className="text-base font-bold text-white mb-3">
                    {a.match_name}
                  </h3>

                  {/* Pricing Matrix */}
                  <div className="grid grid-cols-2 gap-2 p-3 rounded-xl bg-cyber-darkest border border-cyber-border/70 mb-4 font-mono text-xs">
                    <div>
                      <div className="text-[10px] text-slate-400">STAKE OFFERED</div>
                      <div className="text-lg font-black text-emerald-400">
                        {a.stake_current_odds}
                      </div>
                      <div className="text-[10px] text-slate-500">Retail line (unadjusted)</div>
                    </div>
                    <div>
                      <div className="text-[10px] text-slate-400">PINNACLE SHARP</div>
                      <div className="text-lg font-black text-rose-400">
                        {a.pinnacle_current_odds}
                      </div>
                      <div className="text-[10px] text-slate-500">Fair: {a.pinnacle_fair_odds}</div>
                    </div>
                  </div>

                  {/* Edge Breakdown */}
                  <div className="flex items-center justify-between text-xs font-mono p-2 rounded-lg bg-cyber-darkest/40 border border-cyber-border mb-4">
                    <span className="text-slate-300">
                      Pick: <strong className="text-white">{a.team_selected}</strong>
                    </span>
                    <span className="text-emerald-400 font-bold bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20">
                      +{a.lag_edge_pct}% Edge
                    </span>
                  </div>
                </div>

                {/* Action button */}
                <button
                  onClick={() => handleLockIn(a)}
                  className={`w-full py-2 px-3 rounded-xl font-mono text-xs font-bold transition-all flex items-center justify-center gap-1.5 ${
                    isLocked
                      ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/40"
                      : "bg-amber-500 hover:bg-amber-400 text-black shadow-md shadow-amber-500/20"
                  }`}
                >
                  {isLocked ? (
                    <>
                      <Check className="w-3.5 h-3.5" />
                      <span>Added to Bet Slip</span>
                    </>
                  ) : (
                    <>
                      <ArrowUpRight className="w-3.5 h-3.5" />
                      <span>Lock In Latency Arbitrage</span>
                    </>
                  )}
                </button>
              </motion.div>
            );
          })
        )}
      </div>
    </div>
  );
};

