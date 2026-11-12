"use client";

import React, { useState, useMemo } from "react";
import { 
  SlidersHorizontal, 
  ShieldCheck, 
  TrendingUp, 
  AlertTriangle, 
  RotateCcw,
  Sparkles
} from "lucide-react";
import { motion } from "framer-motion";

export const KellyCalculatorModal: React.FC = () => {
  const [bankroll, setBankroll] = useState<number>(1000);
  const [odds, setOdds] = useState<number>(2.10);
  const [winProbPct, setWinProbPct] = useState<number>(53.5);
  const [fractionMultiplier, setFractionMultiplier] = useState<number>(0.25); // Quarter Kelly default

  // Kelly formula
  const calc = useMemo(() => {
    const p = winProbPct / 100;
    const q = 1 - p;
    const b = odds - 1; // decimal odds - 1

    if (b <= 0 || p <= 0) return null;

    // Full kelly: (bp - q) / b
    const fullKellyFraction = (b * p - q) / b;
    const edgePct = (p * odds - 1) * 100;

    const adjustedFraction = Math.max(0, fullKellyFraction * fractionMultiplier);
    const suggestedStake = bankroll * adjustedFraction;
    const potentialProfit = suggestedStake * b;

    return {
      edgePct: edgePct.toFixed(2),
      isPositiveEV: edgePct > 0,
      fullKellyFraction: (fullKellyFraction * 100).toFixed(2),
      fullKellyDollar: (bankroll * Math.max(0, fullKellyFraction)).toFixed(2),
      halfKellyDollar: (bankroll * Math.max(0, fullKellyFraction * 0.5)).toFixed(2),
      quarterKellyDollar: (bankroll * Math.max(0, fullKellyFraction * 0.25)).toFixed(2),
      activeStake: suggestedStake.toFixed(2),
      activeFractionPct: (adjustedFraction * 100).toFixed(2),
      potentialProfit: potentialProfit.toFixed(2),
    };
  }, [bankroll, odds, winProbPct, fractionMultiplier]);

  // Monte Carlo 100-bet trajectory preview simulation
  const simulation = useMemo(() => {
    if (!calc || !calc.isPositiveEV) return [];
    const p = winProbPct / 100;
    const b = odds - 1;
    const fullK = Math.max(0, (b * p - (1 - p)) / b);

    let bQuarter = bankroll;
    let bHalf = bankroll;
    let bFull = bankroll;

    const points = [{ bet: 0, quarter: bankroll, half: bankroll, full: bankroll }];

    // Deterministic progression for visualization
    for (let i = 1; i <= 20; i++) {
      const isWin = (i * 7 + 3) % 10 < p * 10;
      if (isWin) {
        bQuarter += bQuarter * (fullK * 0.25) * b;
        bHalf += bHalf * (fullK * 0.5) * b;
        bFull += bFull * fullK * b;
      } else {
        bQuarter -= bQuarter * (fullK * 0.25);
        bHalf -= bHalf * (fullK * 0.5);
        bFull -= bFull * fullK;
      }
      points.push({
        bet: i,
        quarter: Math.round(bQuarter),
        half: Math.round(bHalf),
        full: Math.round(bFull),
      });
    }
    return points;
  }, [bankroll, odds, winProbPct, calc]);

  return (
    <div className="space-y-6">
      {/* Intro Header */}
      <div className="glass-panel rounded-2xl p-6 border-cyan-500/30 bg-gradient-to-r from-cyan-950/20 via-cyber-card to-cyber-card">
        <div className="flex items-center gap-2 text-xs font-mono text-cyan-400 mb-1">
          <SlidersHorizontal className="w-4 h-4" />
          <span>CAPITAL PRESERVATION & SIZING ENGINE</span>
        </div>
        <h2 className="text-xl sm:text-2xl font-black text-white mb-2">
          Fractional Kelly Risk Calculator
        </h2>
        <p className="text-sm text-slate-400 max-w-2xl">
          Mathematically optimal bet sizing. Full Kelly maximizes logarithmic utility but suffers severe 50%+ drawdowns. Fractional sizing (Quarter Kelly) eliminates bankruptcy risk while delivering stable geometric compound growth.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Inputs Card */}
        <div className="lg:col-span-5 glass-panel rounded-2xl p-6 space-y-5">
          <h3 className="text-base font-bold text-white font-mono flex items-center gap-2">
            <span>INPUT PARAMETERS</span>
          </h3>

          <div>
            <label className="text-xs font-mono text-slate-400 flex justify-between mb-1">
              <span>Total Bankroll Capital ($)</span>
              <strong className="text-white">${bankroll}</strong>
            </label>
            <input
              type="range"
              min={100}
              max={10000}
              step={100}
              value={bankroll}
              onChange={(e) => setBankroll(Number(e.target.value))}
              className="w-full accent-cyan-400"
            />
          </div>

          <div>
            <label className="text-xs font-mono text-slate-400 flex justify-between mb-1">
              <span>Stake.ac Offered Odds (Decimal)</span>
              <strong className="text-cyan-400">{odds.toFixed(2)}</strong>
            </label>
            <input
              type="range"
              min={1.1}
              max={6.0}
              step={0.05}
              value={odds}
              onChange={(e) => setOdds(Number(e.target.value))}
              className="w-full accent-cyan-400"
            />
          </div>

          <div>
            <label className="text-xs font-mono text-slate-400 flex justify-between mb-1">
              <span>Model True Win Probability (%)</span>
              <strong className="text-emerald-400">{winProbPct.toFixed(1)}%</strong>
            </label>
            <input
              type="range"
              min={10}
              max={90}
              step={0.5}
              value={winProbPct}
              onChange={(e) => setWinProbPct(Number(e.target.value))}
              className="w-full accent-emerald-400"
            />
          </div>

          <div>
            <label className="text-xs font-mono text-slate-400 mb-2 block">
              Kelly Risk Fraction:
            </label>
            <div className="grid grid-cols-3 gap-2 font-mono text-xs">
              {[
                { label: "Quarter (0.25x)", val: 0.25, rec: true },
                { label: "Half (0.50x)", val: 0.5 },
                { label: "Full (1.00x)", val: 1.0 },
              ].map((f) => (
                <button
                  key={f.val}
                  onClick={() => setFractionMultiplier(f.val)}
                  className={`py-2 px-2 rounded-xl font-bold transition-all ${
                    fractionMultiplier === f.val
                      ? "bg-cyan-500 text-black shadow-md shadow-cyan-500/20"
                      : "bg-cyber-darkest text-slate-400 border border-cyber-border hover:text-white"
                  }`}
                >
                  <div>{f.label}</div>
                  {f.rec && <div className="text-[9px] text-black/70">Recommended</div>}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Right Output Dashboard */}
        <div className="lg:col-span-7 glass-panel rounded-2xl p-6 space-y-6 flex flex-col justify-between">
          <div>
            <h3 className="text-base font-bold text-white font-mono mb-4">
              SIZING RESULTS & EXPECTED VALUE
            </h3>

            {calc && (
              <div className="space-y-4">
                {/* Edge Status */}
                <div
                  className={`p-3.5 rounded-xl border flex items-center justify-between font-mono text-xs ${
                    calc.isPositiveEV
                      ? "bg-emerald-950/20 border-emerald-500/40 text-emerald-300"
                      : "bg-rose-950/20 border-rose-500/40 text-rose-300"
                  }`}
                >
                  <span className="flex items-center gap-1.5 font-bold">
                    {calc.isPositiveEV ? (
                      <TrendingUp className="w-4 h-4 text-emerald-400" />
                    ) : (
                      <AlertTriangle className="w-4 h-4 text-rose-400" />
                    )}
                    {calc.isPositiveEV ? "POSITIVE EXPECTED VALUE (+EV)" : "NEGATIVE VALUE (-EV: DO NOT BET)"}
                  </span>
                  <span className="font-black text-sm">
                    {calc.edgePct > "0" ? `+${calc.edgePct}%` : `${calc.edgePct}%`} Edge
                  </span>
                </div>

                {/* Sizing Recommendations Grid */}
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 font-mono text-center">
                  <div className="p-4 rounded-xl bg-cyan-950/20 border border-cyan-500/40">
                    <div className="text-xs text-cyan-400 font-bold">QUARTER KELLY</div>
                    <div className="text-2xl font-black text-white mt-1">
                      ${calc.quarterKellyDollar}
                    </div>
                    <div className="text-[10px] text-slate-400 mt-1">Safest variance curve</div>
                  </div>

                  <div className="p-4 rounded-xl bg-purple-950/20 border border-purple-500/40">
                    <div className="text-xs text-purple-400 font-bold">HALF KELLY</div>
                    <div className="text-2xl font-black text-white mt-1">
                      ${calc.halfKellyDollar}
                    </div>
                    <div className="text-[10px] text-slate-400 mt-1">Balanced compound growth</div>
                  </div>

                  <div className="p-4 rounded-xl bg-amber-950/20 border border-amber-500/40">
                    <div className="text-xs text-amber-400 font-bold">FULL KELLY</div>
                    <div className="text-2xl font-black text-white mt-1">
                      ${calc.fullKellyDollar}
                    </div>
                    <div className="text-[10px] text-slate-400 mt-1">High variance / swings</div>
                  </div>
                </div>

                {/* Active Choice Summary */}
                <div className="p-4 rounded-xl bg-cyber-darkest border border-cyber-border font-mono text-xs space-y-2">
                  <div className="flex justify-between">
                    <span className="text-slate-400">Selected Fraction Stake:</span>
                    <strong className="text-emerald-400 font-bold text-sm">
                      ${calc.activeStake} ({calc.activeFractionPct}% of bankroll)
                    </strong>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Net Profit on Winning Bet:</span>
                    <strong className="text-white font-bold text-sm">
                      +${calc.potentialProfit}
                    </strong>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Quick Simulation Progress Table */}
          {simulation.length > 0 && (
            <div className="pt-4 border-t border-cyber-border/60">
              <div className="text-xs font-mono text-slate-400 mb-2">
                Compound Simulation Preview (20 Bets Trajectory):
              </div>
              <div className="grid grid-cols-4 gap-2 text-center font-mono text-[11px] bg-cyber-darkest p-2 rounded-xl">
                <div>
                  <div className="text-slate-500">BET #</div>
                  <div className="text-white font-bold">20 Bets</div>
                </div>
                <div>
                  <div className="text-cyan-400">QUARTER K</div>
                  <div className="text-white font-bold">
                    ${simulation[simulation.length - 1].quarter}
                  </div>
                </div>
                <div>
                  <div className="text-purple-400">HALF K</div>
                  <div className="text-white font-bold">
                    ${simulation[simulation.length - 1].half}
                  </div>
                </div>
                <div>
                  <div className="text-amber-400">FULL K</div>
                  <div className="text-white font-bold">
                    ${simulation[simulation.length - 1].full}
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

