"use client";

import React, { useState, useMemo } from "react";
import Image from "next/image";
import { 
  ChevronDown, 
  ChevronUp, 
  ShieldCheck, 
  Plus, 
  Check, 
  Tv, 
  MapPin, 
  Calendar, 
  Filter, 
  Sparkles, 
  Info,
  Radio
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { MatchFixture, ActiveSlipItem } from "../types";

interface MatchCenterProps {
  liveMatches: MatchFixture[];
  upcomingMatches: MatchFixture[];
  activeSlip: ActiveSlipItem[];
  onToggleLeg: (item: ActiveSlipItem) => void;
}

export const MatchCenter: React.FC<MatchCenterProps> = ({
  liveMatches,
  upcomingMatches,
  activeSlip,
  onToggleLeg,
}) => {
  const [selectedLeague, setSelectedLeague] = useState<string>("ALL");
  const [filterType, setFilterType] = useState<"ALL" | "LIVE" | "HIGH_EV" | "SAFE">("ALL");
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [expandedMatchId, setExpandedMatchId] = useState<string | null>(null);

  // Extract unique leagues
  const leagues = useMemo(() => {
    const set = new Set<string>();
    [...liveMatches, ...upcomingMatches].forEach((m) => {
      if (m.competition) {
        // Normalize competition name
        if (m.competition.includes("Premier League")) set.add("Premier League");
        else if (m.competition.includes("La Liga") || m.competition.includes("Primera")) set.add("La Liga");
        else if (m.competition.includes("Serie A")) set.add("Serie A");
        else if (m.competition.includes("Bundesliga")) set.add("Bundesliga");
        else if (m.competition.includes("Ligue 1")) set.add("Ligue 1");
        else if (m.competition.includes("UEFA") || m.competition.includes("Champions")) set.add("UEFA Nations / Europe");
        else set.add("International / Other");
      }
    });
    return ["ALL", ...Array.from(set)];
  }, [liveMatches, upcomingMatches]);

  // Check if a selection is in the active bet slip
  const isInSlip = (matchId: string, marketType: string, selection: string) => {
    return activeSlip.some(
      (s) => s.matchId === matchId && s.marketType === marketType && s.selection === selection
    );
  };

  // Filtered fixtures
  const filteredMatches = useMemo(() => {
    let list = [...liveMatches, ...upcomingMatches];

    if (filterType === "LIVE") {
      list = list.filter((m) => m.is_live);
    } else if (filterType === "HIGH_EV") {
      list = list.filter(
        (m) =>
          (m.edges && (m.edges.home > 2.5 || m.edges.draw > 2.5 || m.edges.away > 2.5)) ||
          m.secondary_markets?.some((sm) => sm.edge > 3.0)
      );
    } else if (filterType === "SAFE") {
      list = list.filter(
        (m) =>
          m.best_safety_pick?.safety_rating === "Ultra-Safe" ||
          m.secondary_markets?.some((sm) => sm.win_probability >= 0.75)
      );
    }

    if (selectedLeague !== "ALL") {
      list = list.filter((m) => {
        if (selectedLeague === "Premier League") return m.competition?.includes("Premier League");
        if (selectedLeague === "La Liga") return m.competition?.includes("La Liga") || m.competition?.includes("Primera");
        if (selectedLeague === "Serie A") return m.competition?.includes("Serie A");
        if (selectedLeague === "Bundesliga") return m.competition?.includes("Bundesliga");
        if (selectedLeague === "Ligue 1") return m.competition?.includes("Ligue 1");
        if (selectedLeague === "UEFA Nations / Europe") return m.competition?.includes("UEFA") || m.competition?.includes("Champions");
        return true;
      });
    }

    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      list = list.filter(
        (m) =>
          m.match_name.toLowerCase().includes(q) ||
          m.competition?.toLowerCase().includes(q) ||
          m.home_team?.toLowerCase().includes(q) ||
          m.away_team?.toLowerCase().includes(q)
      );
    }

    return list;
  }, [liveMatches, upcomingMatches, selectedLeague, filterType, searchQuery]);

  return (
    <div className="space-y-6">
      {/* Top Filter Bar */}
      <div className="glass-panel rounded-2xl p-4 sm:p-5">
        <div className="flex flex-col lg:flex-row items-start lg:items-center justify-between gap-4">
          {/* Status filters */}
          <div className="flex items-center flex-wrap gap-2">
            {[
              { id: "ALL", label: "All Fixtures", count: liveMatches.length + upcomingMatches.length },
              { id: "LIVE", label: "🔴 In-Play Live", count: liveMatches.length },
              { id: "HIGH_EV", label: "🔥 Sharp +EV Edge (>+2.5%)" },
              { id: "SAFE", label: "🛡️ Fortress Safe (≥75% Win Prob)" },
            ].map((f) => (
              <button
                key={f.id}
                onClick={() => setFilterType(f.id as any)}
                className={`px-3 py-1.5 rounded-xl text-xs font-semibold transition-all ${
                  filterType === f.id
                    ? "bg-emerald-500 text-black shadow-md shadow-emerald-500/20"
                    : "bg-cyber-darkest text-slate-400 hover:text-white border border-cyber-border"
                }`}
              >
                <span>{f.label}</span>
                {f.count !== undefined && (
                  <span className="ml-1.5 opacity-75 font-mono">({f.count})</span>
                )}
              </button>
            ))}
          </div>

          {/* Quick Search inside match center */}
          <div className="w-full lg:w-72">
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search team, venue, or league..."
              className="w-full bg-cyber-darkest border border-cyber-border rounded-xl px-3.5 py-1.5 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-cyan-500 font-mono transition-colors"
            />
          </div>
        </div>

        {/* League Selector Pills */}
        <div className="flex items-center gap-2 overflow-x-auto pt-4 mt-3 border-t border-cyber-border/60 scrollbar-none">
          <Filter className="w-3.5 h-3.5 text-slate-500 shrink-0" />
          <span className="text-xs text-slate-400 font-mono shrink-0">Competition:</span>
          {leagues.map((lg) => (
            <button
              key={lg}
              onClick={() => setSelectedLeague(lg)}
              className={`whitespace-nowrap px-3 py-1 rounded-lg text-xs font-medium transition-all ${
                selectedLeague === lg
                  ? "bg-cyan-500/20 text-cyan-300 border border-cyan-500/40"
                  : "bg-cyber-darkest/70 text-slate-400 hover:text-slate-300 border border-cyber-border/70"
              }`}
            >
              {lg}
            </button>
          ))}
        </div>
      </div>

      {/* Match Fixture Cards Grid */}
      <div className="space-y-4">
        {filteredMatches.length === 0 ? (
          <div className="glass-panel rounded-2xl p-12 text-center text-slate-400">
            <p className="text-sm">No matches found matching the selected filters.</p>
          </div>
        ) : (
          filteredMatches.map((m) => {
            const isExpanded = expandedMatchId === m.match_id;
            const isLive = m.is_live;

            return (
              <motion.div
                key={m.match_id}
                layout
                initial={{ opacity: 0, y: 12 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.2 }}
                className={`glass-panel rounded-2xl overflow-hidden border transition-all ${
                  isLive
                    ? "border-rose-500/40 bg-gradient-to-r from-rose-950/20 via-cyber-card to-cyber-card"
                    : "border-cyber-border hover:border-slate-600/60"
                }`}
              >
                {/* Header: Competition, Date Pill & Broadcast */}
                <div className="flex items-center justify-between px-5 py-3 border-b border-cyber-border/60 bg-cyber-darkest/40 text-xs">
                  <div className="flex items-center gap-3">
                    {isLive ? (
                      <span className="flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-rose-500/20 border border-rose-500/40 text-rose-300 font-mono font-bold text-[11px] animate-pulse">
                        <Radio className="w-3 h-3 text-rose-400" />
                        LIVE {m.current_minute || "IN-PLAY"}
                      </span>
                    ) : (
                      <span className="flex items-center gap-1.5 px-2.5 py-0.5 rounded-md bg-cyan-950/40 border border-cyan-800/40 text-cyan-300 font-mono font-semibold text-[11px]">
                        <Calendar className="w-3 h-3 text-cyan-400" />
                        {m.kickoff_time}
                      </span>
                    )}

                    <span className="font-semibold text-slate-300 truncate max-w-[200px] sm:max-w-none">
                      {m.competition}
                    </span>
                  </div>

                  <div className="hidden sm:flex items-center gap-4 text-slate-400 text-[11px] font-mono">
                    <span className="flex items-center gap-1">
                      <MapPin className="w-3 h-3 text-slate-500" />
                      {m.venue || "Stadium"}
                    </span>
                    <span className="flex items-center gap-1">
                      <Tv className="w-3 h-3 text-slate-500" />
                      {m.broadcaster || "Live Broadcast"}
                    </span>
                  </div>
                </div>

                {/* Scoreboard / Team Row */}
                <div className="p-5">
                  <div className="grid grid-cols-1 md:grid-cols-12 items-center gap-4">
                    {/* Home Team */}
                    <div className="md:col-span-4 flex items-center justify-start md:justify-end gap-3.5">
                      <span className="font-bold text-base sm:text-lg text-white text-right">
                        {m.home_team}
                      </span>
                      {m.home_logo ? (
                        <img
                          src={m.home_logo}
                          alt={m.home_team}
                          className="w-10 h-10 object-contain drop-shadow-md shrink-0"
                          onError={(e) => {
                            (e.target as any).style.display = "none";
                          }}
                        />
                      ) : (
                        <div className="w-10 h-10 rounded-full bg-slate-800 flex items-center justify-center font-bold text-slate-400 text-xs shrink-0">
                          {m.home_team.substring(0, 2).toUpperCase()}
                        </div>
                      )}
                    </div>

                    {/* Center Score / VS Badge */}
                    <div className="md:col-span-4 flex flex-col items-center justify-center py-1">
                      {isLive ? (
                        <div className="flex flex-col items-center">
                          <div className="flex items-center gap-3 font-mono font-black text-2xl text-white bg-cyber-darkest px-4 py-1 rounded-xl border border-rose-500/40">
                            <span className="text-emerald-400">{m.home_score ?? 0}</span>
                            <span className="text-slate-500">-</span>
                            <span className="text-rose-400">{m.away_score ?? 0}</span>
                          </div>
                          <span className="text-[10px] text-rose-300 font-mono mt-1 font-semibold">
                            {m.momentum || "Live Match in Progress"}
                          </span>
                        </div>
                      ) : (
                        <div className="flex flex-col items-center">
                          <span className="px-3 py-1 rounded-full bg-cyber-card border border-cyber-border text-xs font-mono font-bold text-slate-400">
                            VS
                          </span>
                          {m.is_uncertain_1x2 && (
                            <span className="mt-1.5 text-[10px] text-amber-400 font-mono bg-amber-500/10 border border-amber-500/20 px-2 py-0.5 rounded">
                              ⚖️ 1X2 Volatile (Secondary Edge)
                            </span>
                          )}
                        </div>
                      )}
                    </div>

                    {/* Away Team */}
                    <div className="md:col-span-4 flex items-center justify-start gap-3.5">
                      {m.away_logo ? (
                        <img
                          src={m.away_logo}
                          alt={m.away_team}
                          className="w-10 h-10 object-contain drop-shadow-md shrink-0"
                          onError={(e) => {
                            (e.target as any).style.display = "none";
                          }}
                        />
                      ) : (
                        <div className="w-10 h-10 rounded-full bg-slate-800 flex items-center justify-center font-bold text-slate-400 text-xs shrink-0">
                          {m.away_team.substring(0, 2).toUpperCase()}
                        </div>
                      )}
                      <span className="font-bold text-base sm:text-lg text-white text-left">
                        {m.away_team}
                      </span>
                    </div>
                  </div>

                  {/* Primary 1X2 Market Odds Grid */}
                  <div className="mt-5 grid grid-cols-3 gap-2.5 sm:gap-4">
                    {/* Home Win */}
                    <button
                      onClick={() =>
                        onToggleLeg({
                          id: `${m.match_id}_1X2_home`,
                          matchId: m.match_id,
                          matchName: m.match_name,
                          competition: m.competition,
                          kickoffStr: m.kickoff_time,
                          marketType: "1X2",
                          selection: `${m.home_team} Win`,
                          odds: m.stake_odds.home,
                          winProb: m.fair_probabilities.home,
                          homeTeam: m.home_team,
                          awayTeam: m.away_team,
                          homeLogo: m.home_logo,
                          awayLogo: m.away_logo,
                        })
                      }
                      className={`group p-3 rounded-xl border text-left transition-all ${
                        isInSlip(m.match_id, "1X2", `${m.home_team} Win`)
                          ? "bg-emerald-500/20 border-emerald-500 text-white shadow-md shadow-emerald-500/10"
                          : "bg-cyber-darkest/60 border-cyber-border hover:border-emerald-500/50 hover:bg-cyber-card"
                      }`}
                    >
                      <div className="flex items-center justify-between text-xs text-slate-400 font-mono">
                        <span className="truncate">{m.home_team} (1)</span>
                        {isInSlip(m.match_id, "1X2", `${m.home_team} Win`) ? (
                          <Check className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
                        ) : (
                          <Plus className="w-3.5 h-3.5 opacity-0 group-hover:opacity-100 text-emerald-400 transition-opacity shrink-0" />
                        )}
                      </div>
                      <div className="flex items-baseline justify-between mt-1">
                        <span className="text-base sm:text-lg font-black font-mono text-white group-hover:text-emerald-400 transition-colors">
                          {m.stake_odds.home}
                        </span>
                        {m.edges?.home !== undefined && (
                          <span
                            className={`text-[10px] font-mono font-bold px-1.5 py-0.2 rounded ${
                              m.edges.home > 0
                                ? "bg-emerald-500/20 text-emerald-400"
                                : "bg-slate-800 text-slate-400"
                            }`}
                          >
                            {m.edges.home > 0 ? `+${m.edges.home}%` : `${m.edges.home}%`}
                          </span>
                        )}
                      </div>
                      <div className="text-[10px] text-slate-500 font-mono mt-0.5">
                        Fair: {m.fair_odds.home} ({(m.fair_probabilities.home * 100).toFixed(0)}%)
                      </div>
                    </button>

                    {/* Draw */}
                    <button
                      onClick={() =>
                        onToggleLeg({
                          id: `${m.match_id}_1X2_draw`,
                          matchId: m.match_id,
                          matchName: m.match_name,
                          competition: m.competition,
                          kickoffStr: m.kickoff_time,
                          marketType: "1X2",
                          selection: "Draw",
                          odds: m.stake_odds.draw,
                          winProb: m.fair_probabilities.draw,
                          homeTeam: m.home_team,
                          awayTeam: m.away_team,
                          homeLogo: m.home_logo,
                          awayLogo: m.away_logo,
                        })
                      }
                      className={`group p-3 rounded-xl border text-left transition-all ${
                        isInSlip(m.match_id, "1X2", "Draw")
                          ? "bg-emerald-500/20 border-emerald-500 text-white shadow-md shadow-emerald-500/10"
                          : "bg-cyber-darkest/60 border-cyber-border hover:border-emerald-500/50 hover:bg-cyber-card"
                      }`}
                    >
                      <div className="flex items-center justify-between text-xs text-slate-400 font-mono">
                        <span>Draw (X)</span>
                        {isInSlip(m.match_id, "1X2", "Draw") ? (
                          <Check className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
                        ) : (
                          <Plus className="w-3.5 h-3.5 opacity-0 group-hover:opacity-100 text-emerald-400 transition-opacity shrink-0" />
                        )}
                      </div>
                      <div className="flex items-baseline justify-between mt-1">
                        <span className="text-base sm:text-lg font-black font-mono text-white group-hover:text-emerald-400 transition-colors">
                          {m.stake_odds.draw}
                        </span>
                        {m.edges?.draw !== undefined && (
                          <span
                            className={`text-[10px] font-mono font-bold px-1.5 py-0.2 rounded ${
                              m.edges.draw > 0
                                ? "bg-emerald-500/20 text-emerald-400"
                                : "bg-slate-800 text-slate-400"
                            }`}
                          >
                            {m.edges.draw > 0 ? `+${m.edges.draw}%` : `${m.edges.draw}%`}
                          </span>
                        )}
                      </div>
                      <div className="text-[10px] text-slate-500 font-mono mt-0.5">
                        Fair: {m.fair_odds.draw} ({(m.fair_probabilities.draw * 100).toFixed(0)}%)
                      </div>
                    </button>

                    {/* Away Win */}
                    <button
                      onClick={() =>
                        onToggleLeg({
                          id: `${m.match_id}_1X2_away`,
                          matchId: m.match_id,
                          matchName: m.match_name,
                          competition: m.competition,
                          kickoffStr: m.kickoff_time,
                          marketType: "1X2",
                          selection: `${m.away_team} Win`,
                          odds: m.stake_odds.away,
                          winProb: m.fair_probabilities.away,
                          homeTeam: m.home_team,
                          awayTeam: m.away_team,
                          homeLogo: m.home_logo,
                          awayLogo: m.away_logo,
                        })
                      }
                      className={`group p-3 rounded-xl border text-left transition-all ${
                        isInSlip(m.match_id, "1X2", `${m.away_team} Win`)
                          ? "bg-emerald-500/20 border-emerald-500 text-white shadow-md shadow-emerald-500/10"
                          : "bg-cyber-darkest/60 border-cyber-border hover:border-emerald-500/50 hover:bg-cyber-card"
                      }`}
                    >
                      <div className="flex items-center justify-between text-xs text-slate-400 font-mono">
                        <span className="truncate">{m.away_team} (2)</span>
                        {isInSlip(m.match_id, "1X2", `${m.away_team} Win`) ? (
                          <Check className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
                        ) : (
                          <Plus className="w-3.5 h-3.5 opacity-0 group-hover:opacity-100 text-emerald-400 transition-opacity shrink-0" />
                        )}
                      </div>
                      <div className="flex items-baseline justify-between mt-1">
                        <span className="text-base sm:text-lg font-black font-mono text-white group-hover:text-emerald-400 transition-colors">
                          {m.stake_odds.away}
                        </span>
                        {m.edges?.away !== undefined && (
                          <span
                            className={`text-[10px] font-mono font-bold px-1.5 py-0.2 rounded ${
                              m.edges.away > 0
                                ? "bg-emerald-500/20 text-emerald-400"
                                : "bg-slate-800 text-slate-400"
                            }`}
                          >
                            {m.edges.away > 0 ? `+${m.edges.away}%` : `${m.edges.away}%`}
                          </span>
                        )}
                      </div>
                      <div className="text-[10px] text-slate-500 font-mono mt-0.5">
                        Fair: {m.fair_odds.away} ({(m.fair_probabilities.away * 100).toFixed(0)}%)
                      </div>
                    </button>
                  </div>

                  {/* Secondary Markets Expand / Collapse Toggle */}
                  {m.secondary_markets && m.secondary_markets.length > 0 && (
                    <div className="mt-4 pt-3 border-t border-cyber-border/40 flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        {m.best_safety_pick && (
                          <span className="text-[11px] font-mono text-emerald-300 bg-emerald-950/40 border border-emerald-800/40 px-2 py-0.5 rounded flex items-center gap-1">
                            <ShieldCheck className="w-3 h-3 text-emerald-400" />
                            Safety Pick: <strong>{m.best_safety_pick.selection}</strong> @ {m.best_safety_pick.odds} ({(m.best_safety_pick.win_probability * 100).toFixed(0)}%)
                          </span>
                        )}
                      </div>

                      <button
                        onClick={() => setExpandedMatchId(isExpanded ? null : m.match_id)}
                        className="text-xs font-mono text-cyan-400 hover:text-cyan-300 flex items-center gap-1 transition-colors"
                      >
                        <span>{isExpanded ? "Hide Secondary Markets" : `Explore Alternative Markets (${m.secondary_markets.length})`}</span>
                        {isExpanded ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
                      </button>
                    </div>
                  )}

                  {/* Expanded Secondary Markets Panel */}
                  <AnimatePresence>
                    {isExpanded && m.secondary_markets && (
                      <motion.div
                        initial={{ opacity: 0, height: 0 }}
                        animate={{ opacity: 1, height: "auto" }}
                        exit={{ opacity: 0, height: 0 }}
                        transition={{ duration: 0.2 }}
                        className="mt-4 overflow-hidden pt-2"
                      >
                        <div className="p-4 rounded-xl bg-cyber-darkest/80 border border-cyber-border space-y-3">
                          <div className="flex items-center justify-between text-xs text-slate-400 font-mono pb-2 border-b border-cyber-border/40">
                            <span>Alternative Market (Draw No Bet, Double Chance, BTTS, Goals)</span>
                            <span>Model Win %</span>
                          </div>

                          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2.5">
                            {m.secondary_markets.map((sec, idx) => {
                              const inSlip = isInSlip(m.match_id, sec.market_type, sec.selection);
                              return (
                                <button
                                  key={idx}
                                  onClick={() =>
                                    onToggleLeg({
                                      id: `${m.match_id}_${sec.market_type}_${sec.selection}`,
                                      matchId: m.match_id,
                                      matchName: m.match_name,
                                      competition: m.competition,
                                      kickoffStr: m.kickoff_time,
                                      marketType: sec.market_type,
                                      selection: sec.selection,
                                      odds: sec.odds,
                                      winProb: sec.win_probability,
                                      homeTeam: m.home_team,
                                      awayTeam: m.away_team,
                                      homeLogo: m.home_logo,
                                      awayLogo: m.away_logo,
                                    })
                                  }
                                  className={`p-2.5 rounded-lg border text-left flex items-center justify-between transition-all ${
                                    inSlip
                                      ? "bg-cyan-500/20 border-cyan-500 text-white"
                                      : "bg-cyber-card/60 border-cyber-border hover:border-cyan-500/50 hover:bg-cyber-card"
                                  }`}
                                >
                                  <div>
                                    <div className="text-[11px] text-slate-400 font-mono flex items-center gap-1.5">
                                      <span>{sec.market_type}</span>
                                      {sec.safety_rating === "Ultra-Safe" && (
                                        <span className="text-[9px] px-1 py-0.2 rounded bg-emerald-500/20 text-emerald-400 font-bold">
                                          SAFE
                                        </span>
                                      )}
                                    </div>
                                    <div className="text-xs font-bold text-white mt-0.5">
                                      {sec.selection}
                                    </div>
                                  </div>

                                  <div className="text-right">
                                    <div className="text-sm font-black font-mono text-cyan-400">
                                      {sec.odds}
                                    </div>
                                    <div className="text-[10px] text-slate-400 font-mono">
                                      {(sec.win_probability * 100).toFixed(0)}% Win
                                    </div>
                                  </div>
                                </button>
                              );
                            })}
                          </div>
                        </div>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </div>
              </motion.div>
            );
          })
        )}
      </div>
    </div>
  );
};

