"use client";

import React, { useState } from "react";
import { 
  ShieldCheck, 
  Layers, 
  Zap, 
  Flame, 
  Copy, 
  Check, 
  ArrowRight, 
  Calendar, 
  TrendingUp,
  Percent,
  DollarSign
} from "lucide-react";
import { motion } from "framer-motion";
import confetti from "canvas-confetti";
import { CuratedBetSlip, ActiveSlipItem } from "../types";

interface CuratedSlipsViewProps {
  slips: CuratedBetSlip[];
  onLoadSlip: (legs: ActiveSlipItem[]) => void;
  onPlaceSimulatedSlip: (slip: CuratedBetSlip) => void;
}

export const CuratedSlipsView: React.FC<CuratedSlipsViewProps> = ({
  slips,
  onLoadSlip,
  onPlaceSimulatedSlip,
}) => {
  const [copiedId, setCopiedId] = useState<string | null>(null);

  const handleCopy = (slip: CuratedBetSlip) => {
    navigator.clipboard.writeText(slip.copyable_text || `Slip: ${slip.slip_name}\nOdds: ${slip.combined_odds}`);
    setCopiedId(slip.slip_id);
    setTimeout(() => setCopiedId(null), 2500);
  };

  const handleSimulateBet = (slip: CuratedBetSlip) => {
    // Trigger celebratory confetti
    confetti({
      particleCount: 80,
      spread: 70,
      origin: { y: 0.6 },
      colors: ["#10b981", "#06b6d4", "#f59e0b", "#8b5cf6"],
    });
    onPlaceSimulatedSlip(slip);
  };

  const getStrategyColors = (badge: string) => {
    if (badge.includes("FORTRESS")) {
      return {
        border: "border-emerald-500/40",
        bg: "bg-emerald-950/15",
        pill: "bg-emerald-500/20 text-emerald-400 border-emerald-500/40",
        accent: "text-emerald-400",
        glow: "shadow-emerald-500/10",
      };
    }
    if (badge.includes("HEDGE")) {
      return {
        border: "border-purple-500/40",
        bg: "bg-purple-950/15",
        pill: "bg-purple-500/20 text-purple-400 border-purple-500/40",
        accent: "text-purple-400",
        glow: "shadow-purple-500/10",
      };
    }
    if (badge.includes("+EV")) {
      return {
        border: "border-amber-500/40",
        bg: "bg-amber-950/15",
        pill: "bg-amber-500/20 text-amber-400 border-amber-500/40",
        accent: "text-amber-400",
        glow: "shadow-amber-500/10",
      };
    }
    return {
      border: "border-cyan-500/40",
      bg: "bg-cyan-950/15",
      pill: "bg-cyan-500/20 text-cyan-400 border-cyan-500/40",
      accent: "text-cyan-400",
      glow: "shadow-cyan-500/10",
    };
  };

  return (
    <div className="space-y-6">
      {/* Overview Intro */}
      <div className="glass-panel rounded-2xl p-6">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 text-xs font-mono text-emerald-400 mb-1">
              <ShieldCheck className="w-4 h-4" />
              <span>QUANT ALGORITHMIC MULTI-BETS</span>
            </div>
            <h2 className="text-xl sm:text-2xl font-black text-white">
              Autonomous Precision Bet Slips
            </h2>
            <p className="text-sm text-slate-400 max-w-2xl mt-1">
              Four specialized cross-league accumulators dynamically calibrated using Shin de-vigging, Poisson expectation, and Kelly risk allocation.
            </p>
          </div>

          <div className="flex items-center gap-3 font-mono text-xs text-slate-400 bg-cyber-darkest/60 px-4 py-2.5 rounded-xl border border-cyber-border">
            <span>KELLY BANKROLL FRACTION:</span>
            <span className="text-cyan-400 font-bold">0.25x (Quarter Kelly)</span>
          </div>
        </div>
      </div>

      {/* 4 Strategy Slips Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {slips.map((slip) => {
          const colors = getStrategyColors(slip.strategy_badge);

          return (
            <motion.div
              key={slip.slip_id}
              initial={{ opacity: 0, scale: 0.98 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.25 }}
              className={`glass-panel rounded-2xl border ${colors.border} ${colors.bg} p-6 flex flex-col justify-between shadow-xl ${colors.glow} relative overflow-hidden`}
            >
              {/* Top Strategy Header */}
              <div>
                <div className="flex items-center justify-between gap-3 mb-2">
                  <span className={`text-[11px] font-mono font-bold px-2.5 py-0.5 rounded-full border ${colors.pill}`}>
                    {slip.strategy_badge}
                  </span>
                  <span className="text-xs font-mono text-slate-400">
                    {slip.legs.length} LEGS ACCUMULATOR
                  </span>
                </div>

                <h3 className="text-lg font-bold text-white mb-1">
                  {slip.slip_name}
                </h3>
                <p className="text-xs text-slate-400 mb-5">
                  {slip.strategy_description}
                </p>

                {/* Individual Legs Ticket Items */}
                <div className="space-y-3 mb-6">
                  {slip.legs.map((leg, idx) => (
                    <div
                      key={idx}
                      className="p-3.5 rounded-xl bg-cyber-darkest/80 border border-cyber-border/80 flex flex-col gap-2"
                    >
                      {/* Match & Date Row */}
                      <div className="flex items-center justify-between text-xs font-mono">
                        <span className="text-slate-400 truncate max-w-[200px]">
                          {leg.competition}
                        </span>
                        <span className="text-[11px] text-cyan-400 font-semibold flex items-center gap-1 bg-cyan-950/40 px-2 py-0.5 rounded border border-cyan-800/40">
                          <Calendar className="w-3 h-3" />
                          {leg.kickoff_str}
                        </span>
                      </div>

                      {/* Teams & Logos */}
                      <div className="flex items-center justify-between py-1">
                        <div className="flex items-center gap-2">
                          {leg.home_logo && (
                            <img
                              src={leg.home_logo}
                              alt=""
                              className="w-5 h-5 object-contain"
                              onError={(e) => ((e.target as any).style.display = "none")}
                            />
                          )}
                          <span className="text-xs font-bold text-white">
                            {leg.match_name}
                          </span>
                        </div>

                        <div className="text-right">
                          <span className="text-xs font-mono font-black text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20">
                            {leg.odds.toFixed(2)}
                          </span>
                        </div>
                      </div>

                      {/* Pick Selection & Hedge explanation */}
                      <div className="flex items-center justify-between pt-1 border-t border-cyber-border/40 text-[11px]">
                        <span className="font-semibold text-slate-200">
                          Pick: <strong className={colors.accent}>{leg.selection}</strong> ({leg.market_type})
                        </span>
                        <span className="text-slate-400 font-mono">
                          {(leg.win_probability * 100).toFixed(0)}% Win Prob
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Bottom Financial Metrics Grid & Action Buttons */}
              <div>
                <div className="grid grid-cols-4 gap-2 p-3.5 rounded-xl bg-cyber-darkest/90 border border-cyber-border mb-4 text-center font-mono">
                  <div>
                    <div className="text-[10px] text-slate-400">COMBINED ODDS</div>
                    <div className="text-base font-black text-white mt-0.5">
                      {slip.combined_odds.toFixed(2)}x
                    </div>
                  </div>
                  <div>
                    <div className="text-[10px] text-slate-400">WIN PROB</div>
                    <div className="text-base font-black text-cyan-400 mt-0.5">
                      {(slip.combined_probability * 100).toFixed(1)}%
                    </div>
                  </div>
                  <div>
                    <div className="text-[10px] text-slate-400">SUGGESTED STAKE</div>
                    <div className="text-base font-black text-emerald-400 mt-0.5">
                      ${slip.suggested_stake_amount.toFixed(2)}
                    </div>
                  </div>
                  <div>
                    <div className="text-[10px] text-slate-400">POTENTIAL PROFIT</div>
                    <div className="text-base font-black text-amber-400 mt-0.5">
                      +${slip.net_profit_on_win.toFixed(2)}
                    </div>
                  </div>
                </div>

                {/* Action Buttons */}
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 text-xs font-mono">
                  <button
                    onClick={() =>
                      onLoadSlip(
                        slip.legs.map((l) => ({
                          id: `${l.match_id}_${l.market_type}_${l.selection}`,
                          matchId: l.match_id,
                          matchName: l.match_name,
                          competition: l.competition,
                          kickoffStr: l.kickoff_str,
                          marketType: l.market_type,
                          selection: l.selection,
                          odds: l.odds,
                          winProb: l.win_probability,
                          homeTeam: l.home_team,
                          awayTeam: l.away_team,
                          homeLogo: l.home_logo,
                          awayLogo: l.away_logo,
                        }))
                      )
                    }
                    className="px-3 py-2 rounded-xl bg-cyber-darkest border border-cyber-border text-slate-300 hover:text-white hover:border-slate-500 font-semibold transition-colors flex items-center justify-center gap-1.5"
                  >
                    <span>Load into Slip</span>
                    <ArrowRight className="w-3.5 h-3.5" />
                  </button>

                  <button
                    onClick={() => handleCopy(slip)}
                    className="px-3 py-2 rounded-xl bg-cyber-darkest border border-cyber-border text-slate-300 hover:text-white hover:border-slate-500 font-semibold transition-colors flex items-center justify-center gap-1.5"
                  >
                    {copiedId === slip.slip_id ? (
                      <>
                        <Check className="w-3.5 h-3.5 text-emerald-400" />
                        <span className="text-emerald-400">Copied Slip!</span>
                      </>
                    ) : (
                      <>
                        <Copy className="w-3.5 h-3.5 text-slate-400" />
                        <span>Copy Stake Code</span>
                      </>
                    )}
                  </button>

                  <button
                    onClick={() => handleSimulateBet(slip)}
                    className="px-3 py-2 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-black font-black transition-colors flex items-center justify-center gap-1.5 shadow-lg shadow-emerald-500/20"
                  >
                    <DollarSign className="w-3.5 h-3.5" />
                    <span>Place Paper Bet</span>
                  </button>
                </div>
              </div>
            </motion.div>
          );
        })}
      </div>
    </div>
  );
};

