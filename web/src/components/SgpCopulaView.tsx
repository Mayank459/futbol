"use client";

import React, { useState } from "react";
import { 
  Sparkles, 
  Layers, 
  TrendingUp, 
  Plus, 
  Check, 
  Info,
  DollarSign
} from "lucide-react";
import { motion } from "framer-motion";
import confetti from "canvas-confetti";
import { SameGameParlay, ActiveSlipItem } from "../types";

interface SgpCopulaViewProps {
  sgps: SameGameParlay[];
  onAddLeg: (leg: ActiveSlipItem) => void;
  onSimulateSgp: (sgp: SameGameParlay) => void;
}

export const SgpCopulaView: React.FC<SgpCopulaViewProps> = ({
  sgps,
  onAddLeg,
  onSimulateSgp,
}) => {
  const [selectedMatch, setSelectedMatch] = useState<string>("ALL");
  const [addedIds, setAddedIds] = useState<Set<string>>(new Set());

  // Distinct matches
  const matchOptions = Array.from(new Set(sgps.map((s) => s.match_name)));

  const filteredSgps = sgps.filter((s) => {
    if (selectedMatch === "ALL") return true;
    return s.match_name === selectedMatch;
  });

  const handleAddSgp = (sgp: SameGameParlay) => {
    setAddedIds((prev) => new Set(prev).add(sgp.match_id + sgp.combo_name));
    onAddLeg({
      id: `${sgp.match_id}_SGP_${sgp.combo_name}`,
      matchId: sgp.match_id,
      matchName: sgp.match_name,
      competition: sgp.competition,
      kickoffStr: sgp.kickoff_str,
      marketType: "Same-Game Parlay (Copula)",
      selection: sgp.combo_name,
      odds: sgp.stake_offered_odds,
      winProb: sgp.exact_joint_probability,
      homeTeam: sgp.home_team,
      awayTeam: sgp.away_team,
      homeLogo: sgp.home_logo,
      awayLogo: sgp.away_logo,
    });
  };

  const handlePlacePaperSgp = (sgp: SameGameParlay) => {
    confetti({
      particleCount: 60,
      spread: 60,
      origin: { y: 0.6 },
    });
    onSimulateSgp(sgp);
  };

  return (
    <div className="space-y-6">
      {/* Intro Banner */}
      <div className="glass-panel rounded-2xl p-6 border-cyan-500/30 bg-gradient-to-r from-cyan-950/20 via-cyber-card to-cyber-card">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 text-xs font-mono text-cyan-400 mb-1">
              <Sparkles className="w-4 h-4" />
              <span>BIVARIATE COPULA CORRELATION ENGINE</span>
            </div>
            <h2 className="text-xl sm:text-2xl font-black text-white">
              Same-Game Parlays (SGP) Quant Combinator
            </h2>
            <p className="text-sm text-slate-400 max-w-2xl mt-1">
              Eliminates the naive independence fallacy. Integrates directly across bivariate Poisson score probability matrices to capture up to +45% correlation boost on same-match multis.
            </p>
          </div>

          {/* Match Filter */}
          <div className="w-full md:w-64">
            <label className="text-xs font-mono text-slate-400 mb-1 block">Filter Match:</label>
            <select
              value={selectedMatch}
              onChange={(e) => setSelectedMatch(e.target.value)}
              className="w-full bg-cyber-darkest border border-cyber-border rounded-xl px-3 py-1.5 text-xs text-slate-200 font-mono focus:outline-none focus:border-cyan-500"
            >
              <option value="ALL">All Available Matches ({sgps.length} SGPs)</option>
              {matchOptions.map((m) => (
                <option key={m} value={m}>
                  {m}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* SGP Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {filteredSgps.map((sgp, idx) => {
          const isAdded = addedIds.has(sgp.match_id + sgp.combo_name);

          return (
            <motion.div
              key={idx}
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.2 }}
              className="glass-panel rounded-2xl p-5 border border-cyan-500/30 bg-cyber-card flex flex-col justify-between hover:border-cyan-500/60 transition-all shadow-lg shadow-cyan-500/5"
            >
              <div>
                {/* Header */}
                <div className="flex items-center justify-between text-xs font-mono text-slate-400 mb-2">
                  <span className="truncate max-w-[200px]">{sgp.competition}</span>
                  <span className="text-cyan-400 font-bold bg-cyan-950/40 px-2 py-0.5 rounded border border-cyan-800/40">
                    +{sgp.correlation_boost_pct}% BOOST
                  </span>
                </div>

                <div className="text-sm font-black text-white mb-1">
                  {sgp.match_name}
                </div>

                <div className="text-xs font-bold text-cyan-300 font-mono mb-2">
                  {sgp.combo_name}
                </div>

                <p className="text-xs text-slate-400 mb-4 italic">
                  &ldquo;{sgp.narrative}&rdquo;
                </p>

                {/* Correlated Legs */}
                <div className="space-y-2 mb-4">
                  {sgp.legs.map((leg, lIdx) => (
                    <div
                      key={lIdx}
                      className="p-2.5 rounded-lg bg-cyber-darkest/70 border border-cyber-border/70 flex items-center justify-between text-xs font-mono"
                    >
                      <span className="text-slate-200">{leg.description}</span>
                      <span className="text-cyan-400 font-bold">
                        {(leg.marginal_prob * 100).toFixed(0)}%
                      </span>
                    </div>
                  ))}
                </div>

                {/* Correlation Metrics Grid */}
                <div className="grid grid-cols-3 gap-2 p-3 rounded-xl bg-cyber-darkest border border-cyber-border mb-4 font-mono text-center text-xs">
                  <div>
                    <div className="text-[10px] text-slate-400">OFFERED ODDS</div>
                    <div className="text-base font-black text-emerald-400">
                      {sgp.stake_offered_odds}x
                    </div>
                  </div>
                  <div>
                    <div className="text-[10px] text-slate-400">FAIR ODDS</div>
                    <div className="text-base font-black text-slate-300">
                      {sgp.true_fair_odds}x
                    </div>
                  </div>
                  <div>
                    <div className="text-[10px] text-slate-400">EV EDGE</div>
                    <div className="text-base font-black text-amber-400">
                      +{sgp.ev_edge}%
                    </div>
                  </div>
                </div>
              </div>

              {/* Action Buttons */}
              <div className="grid grid-cols-2 gap-2 font-mono text-xs">
                <button
                  onClick={() => handleAddSgp(sgp)}
                  className={`py-2 px-3 rounded-xl font-bold flex items-center justify-center gap-1.5 transition-colors ${
                    isAdded
                      ? "bg-cyan-500/20 text-cyan-300 border border-cyan-500/40"
                      : "bg-cyber-darkest border border-cyber-border text-slate-300 hover:text-white hover:border-slate-500"
                  }`}
                >
                  {isAdded ? (
                    <>
                      <Check className="w-3.5 h-3.5" />
                      <span>Added</span>
                    </>
                  ) : (
                    <>
                      <Plus className="w-3.5 h-3.5" />
                      <span>Add to Slip</span>
                    </>
                  )}
                </button>

                <button
                  onClick={() => handlePlacePaperSgp(sgp)}
                  className="py-2 px-3 rounded-xl bg-cyan-500 hover:bg-cyan-400 text-black font-black flex items-center justify-center gap-1.5 transition-colors shadow-md shadow-cyan-500/20"
                >
                  <DollarSign className="w-3.5 h-3.5" />
                  <span>Paper Bet (${sgp.suggested_stake_amount})</span>
                </button>
              </div>
            </motion.div>
          );
        })}
      </div>
    </div>
  );
};

