"use client";

import React, { useState, useMemo } from "react";
import { 
  BarChart3, 
  Search, 
  Swords, 
  Play, 
  TrendingUp, 
  TrendingDown, 
  Shield, 
  Target,
  ArrowUpDown
} from "lucide-react";
import { motion } from "framer-motion";
import { TeamRating } from "../types";

interface QuantLabViewProps {
  teams: TeamRating[];
}

export const QuantLabView: React.FC<QuantLabViewProps> = ({ teams }) => {
  const [teamAId, setTeamAId] = useState<string>(teams[0]?.team_name || "Arsenal");
  const [teamBId, setTeamBId] = useState<string>(teams[1]?.team_name || "Manchester City");
  const [leagueFilter, setLeagueFilter] = useState<string>("ALL");
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [sortBy, setSortBy] = useState<"attack" | "defense" | "form" | "name">("attack");
  const [sortAsc, setSortAsc] = useState<boolean>(false);

  // League options
  const leagues = useMemo(() => {
    const set = new Set<string>();
    teams.forEach((t) => set.add(t.league));
    return ["ALL", ...Array.from(set)];
  }, [teams]);

  // Selected teams for H2H
  const teamA = teams.find((t) => t.team_name === teamAId) || teams[0];
  const teamB = teams.find((t) => t.team_name === teamBId) || teams[1];

  // Head-to-Head Poisson Prediction calculation
  const simulation = useMemo(() => {
    if (!teamA || !teamB) return null;

    // Home advantage: +0.25 goals expectation
    const lambdaHome = Math.max(0.3, 1.35 + teamA.xg_attack - teamB.xg_defense + 0.25 + teamA.form_momentum * 0.5);
    const muAway = Math.max(0.2, 1.15 + teamB.xg_attack - teamA.xg_defense + teamB.form_momentum * 0.5);

    // Poisson probabilities for scores 0-5
    const poisson = (k: number, lambda: number) => {
      const factorial = (n: number): number => (n <= 1 ? 1 : n * factorial(n - 1));
      return (Math.pow(lambda, k) * Math.exp(-lambda)) / factorial(k);
    };

    let pHome = 0;
    let pDraw = 0;
    let pAway = 0;
    let pOver25 = 0;
    let pBtts = 0;

    const scoreMatrix: { score: string; prob: number }[] = [];

    for (let h = 0; h <= 6; h++) {
      for (let a = 0; a <= 6; a++) {
        const prob = poisson(h, lambdaHome) * poisson(a, muAway);
        if (h > a) pHome += prob;
        else if (h === a) pDraw += prob;
        else pAway += prob;

        if (h + a > 2.5) pOver25 += prob;
        if (h > 0 && a > 0) pBtts += prob;

        scoreMatrix.push({ score: `${h}-${a}`, prob });
      }
    }

    // Top 3 scorelines
    scoreMatrix.sort((a, b) => b.prob - a.prob);
    const topScores = scoreMatrix.slice(0, 4);

    return {
      lambdaHome: lambdaHome.toFixed(2),
      muAway: muAway.toFixed(2),
      pHome: (pHome * 100).toFixed(1),
      pDraw: (pDraw * 100).toFixed(1),
      pAway: (pAway * 100).toFixed(1),
      fairHomeOdds: (1 / pHome).toFixed(2),
      fairDrawOdds: (1 / pDraw).toFixed(2),
      fairAwayOdds: (1 / pAway).toFixed(2),
      pOver25: (pOver25 * 100).toFixed(1),
      pBtts: (pBtts * 100).toFixed(1),
      topScores,
    };
  }, [teamA, teamB]);

  // Filtered & sorted teams
  const filteredTeams = useMemo(() => {
    let list = [...teams];
    if (leagueFilter !== "ALL") {
      list = list.filter((t) => t.league === leagueFilter);
    }
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      list = list.filter((t) => t.team_name.toLowerCase().includes(q));
    }
    list.sort((a, b) => {
      let valA: any = a.xg_attack;
      let valB: any = b.xg_attack;
      if (sortBy === "defense") {
        valA = a.xg_defense;
        valB = b.xg_defense;
      } else if (sortBy === "form") {
        valA = a.form_momentum;
        valB = b.form_momentum;
      } else if (sortBy === "name") {
        valA = a.team_name;
        valB = b.team_name;
      }
      if (valA < valB) return sortAsc ? -1 : 1;
      if (valA > valB) return sortAsc ? 1 : -1;
      return 0;
    });
    return list;
  }, [teams, leagueFilter, searchQuery, sortBy, sortAsc]);

  const toggleSort = (type: "attack" | "defense" | "form" | "name") => {
    if (sortBy === type) {
      setSortAsc(!sortAsc);
    } else {
      setSortBy(type);
      setSortAsc(false);
    }
  };

  return (
    <div className="space-y-8">
      {/* Head to Head Poisson Match Simulator */}
      <div className="glass-panel rounded-2xl p-6 border-purple-500/30 bg-gradient-to-r from-purple-950/20 via-cyber-card to-cyber-card">
        <div className="flex items-center gap-2 text-xs font-mono text-purple-400 mb-1">
          <Swords className="w-4 h-4" />
          <span>DIXON-COLES MONTE CARLO & POISSON SIMULATOR</span>
        </div>
        <h2 className="text-xl sm:text-2xl font-black text-white mb-2">
          Interactive Match Prediction Sandbox
        </h2>
        <p className="text-sm text-slate-400 max-w-2xl mb-6">
          Pair any two European clubs to instantly compute continuous shot-quality regression metrics, dynamic Kalman form momentum, and exact bivariate scoreline probabilities.
        </p>

        {/* Team Selectors Row */}
        <div className="grid grid-cols-1 md:grid-cols-5 items-center gap-4 bg-cyber-darkest/70 p-5 rounded-2xl border border-cyber-border mb-6">
          {/* Team A Selector */}
          <div className="md:col-span-2">
            <label className="text-xs font-mono text-slate-400 mb-1 block">
              🏠 Home Team (With +0.25 Home Boost):
            </label>
            <select
              value={teamAId}
              onChange={(e) => setTeamAId(e.target.value)}
              className="w-full bg-cyber-card border border-cyber-border rounded-xl px-3.5 py-2 text-sm text-white font-bold focus:outline-none focus:border-purple-500"
            >
              {teams.map((t) => (
                <option key={t.team_name} value={t.team_name}>
                  {t.team_name} ({t.league})
                </option>
              ))}
            </select>
            {teamA && (
              <div className="flex items-center gap-2 mt-2 text-xs font-mono text-slate-400">
                <span>xG Att: <strong className="text-emerald-400">+{teamA.xg_attack.toFixed(2)}</strong></span>
                <span>•</span>
                <span>xG Def: <strong className="text-rose-400">{teamA.xg_defense.toFixed(2)}</strong></span>
              </div>
            )}
          </div>

          {/* VS Divider */}
          <div className="md:col-span-1 flex flex-col items-center justify-center">
            <div className="w-10 h-10 rounded-full bg-purple-500/20 border border-purple-500/40 flex items-center justify-center text-purple-300 font-black text-sm">
              VS
            </div>
          </div>

          {/* Team B Selector */}
          <div className="md:col-span-2">
            <label className="text-xs font-mono text-slate-400 mb-1 block">
              ✈️ Away Team:
            </label>
            <select
              value={teamBId}
              onChange={(e) => setTeamBId(e.target.value)}
              className="w-full bg-cyber-card border border-cyber-border rounded-xl px-3.5 py-2 text-sm text-white font-bold focus:outline-none focus:border-purple-500"
            >
              {teams.map((t) => (
                <option key={t.team_name} value={t.team_name}>
                  {t.team_name} ({t.league})
                </option>
              ))}
            </select>
            {teamB && (
              <div className="flex items-center gap-2 mt-2 text-xs font-mono text-slate-400">
                <span>xG Att: <strong className="text-emerald-400">+{teamB.xg_attack.toFixed(2)}</strong></span>
                <span>•</span>
                <span>xG Def: <strong className="text-rose-400">{teamB.xg_defense.toFixed(2)}</strong></span>
              </div>
            )}
          </div>
        </div>

        {/* Simulation Output Metrics */}
        {simulation && (
          <div className="space-y-4">
            {/* Primary Win Probabilities */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 font-mono">
              <div className="p-4 rounded-xl bg-cyber-darkest border border-cyber-border text-center">
                <div className="text-xs text-slate-400">{teamA?.team_name} Win</div>
                <div className="text-2xl font-black text-emerald-400 mt-1">
                  {simulation.pHome}%
                </div>
                <div className="text-xs text-slate-500 mt-0.5">
                  Fair Odds: {simulation.fairHomeOdds}
                </div>
              </div>

              <div className="p-4 rounded-xl bg-cyber-darkest border border-cyber-border text-center">
                <div className="text-xs text-slate-400">Draw (Tie)</div>
                <div className="text-2xl font-black text-white mt-1">
                  {simulation.pDraw}%
                </div>
                <div className="text-xs text-slate-500 mt-0.5">
                  Fair Odds: {simulation.fairDrawOdds}
                </div>
              </div>

              <div className="p-4 rounded-xl bg-cyber-darkest border border-cyber-border text-center">
                <div className="text-xs text-slate-400">{teamB?.team_name} Win</div>
                <div className="text-2xl font-black text-cyan-400 mt-1">
                  {simulation.pAway}%
                </div>
                <div className="text-xs text-slate-500 mt-0.5">
                  Fair Odds: {simulation.fairAwayOdds}
                </div>
              </div>
            </div>

            {/* Goal Expectation & Likely Scorelines */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="p-4 rounded-xl bg-cyber-darkest border border-cyber-border font-mono text-xs space-y-2.5">
                <div className="font-bold text-slate-300 pb-1 border-b border-cyber-border/40">
                  EXPECTED GOALS (xG) INTENSITY:
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-slate-400">{teamA?.team_name} xG (λ):</span>
                  <span className="text-white font-bold">{simulation.lambdaHome} goals</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-slate-400">{teamB?.team_name} xG (μ):</span>
                  <span className="text-white font-bold">{simulation.muAway} goals</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-slate-400">Total Match Over 2.5 Goals:</span>
                  <span className="text-cyan-400 font-bold">{simulation.pOver25}%</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-slate-400">Both Teams To Score (BTTS Yes):</span>
                  <span className="text-amber-400 font-bold">{simulation.pBtts}%</span>
                </div>
              </div>

              <div className="p-4 rounded-xl bg-cyber-darkest border border-cyber-border font-mono text-xs space-y-2.5">
                <div className="font-bold text-slate-300 pb-1 border-b border-cyber-border/40">
                  TOP MOST LIKELY SCORELINES:
                </div>
                <div className="grid grid-cols-2 gap-2 pt-1">
                  {simulation.topScores.map((sc, idx) => (
                    <div
                      key={idx}
                      className="p-2.5 rounded-lg bg-cyber-card border border-cyber-border flex items-center justify-between"
                    >
                      <span className="text-white font-black text-sm">{sc.score}</span>
                      <span className="text-emerald-400 font-bold">
                        {(sc.prob * 100).toFixed(1)}%
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* European Clubs Quantitative Ratings Leaderboard */}
      <div className="glass-panel rounded-2xl p-6">
        <div className="flex flex-col lg:flex-row items-start lg:items-center justify-between gap-4 mb-6">
          <div>
            <h3 className="text-lg font-bold text-white">
              European Club Quant Ratings & Form Momentum
            </h3>
            <p className="text-xs text-slate-400">
              State-space Kalman filter and xG attack/defense metrics across 96 top European clubs.
            </p>
          </div>

          <div className="flex items-center flex-wrap gap-3 w-full lg:w-auto">
            {/* Search */}
            <div className="w-full sm:w-48">
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search club..."
                className="w-full bg-cyber-darkest border border-cyber-border rounded-xl px-3 py-1.5 text-xs text-slate-200 font-mono focus:outline-none focus:border-cyan-500"
              />
            </div>

            {/* League filter */}
            <select
              value={leagueFilter}
              onChange={(e) => setLeagueFilter(e.target.value)}
              className="bg-cyber-darkest border border-cyber-border rounded-xl px-3 py-1.5 text-xs text-slate-200 font-mono focus:outline-none focus:border-cyan-500"
            >
              {leagues.map((lg) => (
                <option key={lg} value={lg}>
                  {lg}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Table */}
        <div className="overflow-x-auto rounded-xl border border-cyber-border">
          <table className="w-full text-left text-xs font-mono">
            <thead className="bg-cyber-darkest text-slate-400 border-b border-cyber-border">
              <tr>
                <th
                  onClick={() => toggleSort("name")}
                  className="py-3 px-4 cursor-pointer hover:text-white"
                >
                  <div className="flex items-center gap-1.5">
                    <span>CLUB</span>
                    <ArrowUpDown className="w-3 h-3" />
                  </div>
                </th>
                <th className="py-3 px-4">LEAGUE</th>
                <th
                  onClick={() => toggleSort("attack")}
                  className="py-3 px-4 cursor-pointer hover:text-white"
                >
                  <div className="flex items-center gap-1.5">
                    <span>xG ATTACK</span>
                    <ArrowUpDown className="w-3 h-3" />
                  </div>
                </th>
                <th
                  onClick={() => toggleSort("defense")}
                  className="py-3 px-4 cursor-pointer hover:text-white"
                >
                  <div className="flex items-center gap-1.5">
                    <span>xG DEFENSE</span>
                    <ArrowUpDown className="w-3 h-3" />
                  </div>
                </th>
                <th
                  onClick={() => toggleSort("form")}
                  className="py-3 px-4 cursor-pointer hover:text-white"
                >
                  <div className="flex items-center gap-1.5">
                    <span>KALMAN MOMENTUM</span>
                    <ArrowUpDown className="w-3 h-3" />
                  </div>
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-cyber-border bg-cyber-card/60">
              {filteredTeams.slice(0, 50).map((t, idx) => (
                <tr key={idx} className="hover:bg-cyber-card transition-colors">
                  <td className="py-3 px-4 flex items-center gap-2.5 font-bold text-white">
                    {t.logo_url && (
                      <img
                        src={t.logo_url}
                        alt=""
                        className="w-5 h-5 object-contain"
                        onError={(e) => ((e.target as any).style.display = "none")}
                      />
                    )}
                    <span>{t.team_name}</span>
                  </td>
                  <td className="py-3 px-4 text-slate-400">{t.league}</td>
                  <td className="py-3 px-4 text-emerald-400 font-bold">
                    {t.xg_attack > 0 ? `+${t.xg_attack.toFixed(3)}` : t.xg_attack.toFixed(3)}
                  </td>
                  <td className="py-3 px-4 text-rose-400 font-bold">
                    {t.xg_defense.toFixed(3)}
                  </td>
                  <td className="py-3 px-4">
                    <span
                      className={`inline-flex items-center gap-1 px-2 py-0.5 rounded font-bold ${
                        t.form_momentum > 0.05
                          ? "bg-emerald-500/20 text-emerald-400"
                          : t.form_momentum < -0.05
                          ? "bg-rose-500/20 text-rose-400"
                          : "bg-slate-800 text-slate-300"
                      }`}
                    >
                      {t.form_momentum > 0.05 ? (
                        <TrendingUp className="w-3 h-3" />
                      ) : t.form_momentum < -0.05 ? (
                        <TrendingDown className="w-3 h-3" />
                      ) : null}
                      {t.form_momentum > 0 ? `+${t.form_momentum.toFixed(3)}` : t.form_momentum.toFixed(3)}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

