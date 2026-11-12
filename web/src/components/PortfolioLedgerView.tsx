"use client";

import React, { useState, useMemo } from "react";
import { 
  TrendingUp, 
  TrendingDown, 
  Download, 
  Search, 
  Filter, 
  Clock, 
  CheckCircle2, 
  ShieldAlert,
  Radio,
  Sparkles
} from "lucide-react";
import { motion } from "framer-motion";
import { PaperBetRecord, PortfolioSummary } from "../types";

interface PortfolioLedgerViewProps {
  records: PaperBetRecord[];
  summary: PortfolioSummary;
  onSettleBet?: (betId: string, won: boolean) => void;
}

export const PortfolioLedgerView: React.FC<PortfolioLedgerViewProps> = ({
  records,
  summary,
  onSettleBet,
}) => {
  const [categoryFilter, setCategoryFilter] = useState<string>("ALL");
  const [statusFilter, setStatusFilter] = useState<string>("ALL");
  const [searchQuery, setSearchQuery] = useState<string>("");

  // Categories
  const categories = [
    { id: "ALL", label: "All Portfolio", count: records.length },
    { id: "LIVE_IN_PLAY", label: "🔴 In-Play Live", count: records.filter((r) => r.category === "LIVE_IN_PLAY").length },
    { id: "UPCOMING_SINGLE", label: "Upcoming Singles", count: records.filter((r) => r.category === "UPCOMING_SINGLE").length },
    { id: "UPCOMING_ACCA", label: "Accumulators", count: records.filter((r) => r.category === "UPCOMING_ACCA").length },
    { id: "SAME_GAME_PARLAY", label: "SGP Parlays", count: records.filter((r) => r.category === "SAME_GAME_PARLAY").length },
  ];

  const filteredRecords = useMemo(() => {
    let list = [...records];
    if (categoryFilter !== "ALL") {
      list = list.filter((r) => r.category === categoryFilter);
    }
    if (statusFilter !== "ALL") {
      list = list.filter((r) => r.settlement_status.includes(statusFilter));
    }
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      list = list.filter(
        (r) =>
          r.match_name.toLowerCase().includes(q) ||
          r.selection.toLowerCase().includes(q) ||
          r.competition.toLowerCase().includes(q)
      );
    }
    return list;
  }, [records, categoryFilter, statusFilter, searchQuery]);

  const exportCSV = () => {
    const headers = [
      "Bet ID",
      "Category",
      "Match",
      "Competition",
      "Market",
      "Selection",
      "Odds",
      "Stake ($)",
      "Payout ($)",
      "State",
      "Status",
      "PnL ($)",
      "Placed At",
    ];
    const rows = filteredRecords.map((r) => [
      r.bet_id,
      r.category,
      `"${r.match_name}"`,
      `"${r.competition}"`,
      r.market_type,
      `"${r.selection}"`,
      r.stake_odds,
      r.stake_amount,
      r.potential_payout,
      `"${r.current_match_state}"`,
      `"${r.settlement_status}"`,
      r.unrealized_or_realized_pnl,
      r.placed_at,
    ]);
    const csvContent =
      "data:text/csv;charset=utf-8," +
      [headers.join(","), ...rows.map((e) => e.join(","))].join("\n");
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", `stake_paper_trading_ledger_${Date.now()}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div className="space-y-6">
      {/* Financial KPI Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="glass-panel rounded-2xl p-4 sm:p-5 border-cyber-border font-mono">
          <div className="text-xs text-slate-400">TOTAL CAPITAL STAKED</div>
          <div className="text-2xl sm:text-3xl font-black text-white mt-1">
            ${summary.total_capital_staked.toFixed(2)}
          </div>
          <div className="text-xs text-slate-500 mt-1">{summary.total_bets} simulated positions</div>
        </div>

        <div className="glass-panel rounded-2xl p-4 sm:p-5 border-emerald-500/30 bg-emerald-950/10 font-mono">
          <div className="text-xs text-emerald-400 font-semibold flex items-center gap-1">
            <TrendingUp className="w-3.5 h-3.5" />
            NET PROFIT / LOSS
          </div>
          <div className="text-2xl sm:text-3xl font-black text-emerald-400 mt-1">
            +${summary.net_pnl.toFixed(2)}
          </div>
          <div className="text-xs text-emerald-500 mt-1 font-bold">
            {summary.roi_pct > 0 ? `+${summary.roi_pct}%` : `${summary.roi_pct}%`} ROI
          </div>
        </div>

        <div className="glass-panel rounded-2xl p-4 sm:p-5 border-cyan-500/30 bg-cyan-950/10 font-mono">
          <div className="text-xs text-cyan-400 font-semibold">PORTFOLIO WIN RATE</div>
          <div className="text-2xl sm:text-3xl font-black text-cyan-300 mt-1">
            {summary.win_rate_pct}%
          </div>
          <div className="text-xs text-cyan-500 mt-1">Empirical backtest calibrated</div>
        </div>

        <div className="glass-panel rounded-2xl p-4 sm:p-5 border-purple-500/30 bg-purple-950/10 font-mono">
          <div className="text-xs text-purple-400 font-semibold">CLOSING LINE VALUE</div>
          <div className="text-2xl sm:text-3xl font-black text-purple-300 mt-1">
            +{summary.avg_clv_pct}%
          </div>
          <div className="text-xs text-purple-400/80 mt-1">vs Pinnacle No-Vig Fair</div>
        </div>
      </div>

      {/* Control Bar: Filters, Search & Export */}
      <div className="glass-panel rounded-2xl p-4 sm:p-5 space-y-4">
        <div className="flex flex-col lg:flex-row items-start lg:items-center justify-between gap-4">
          {/* Categories */}
          <div className="flex items-center flex-wrap gap-2">
            {categories.map((c) => (
              <button
                key={c.id}
                onClick={() => setCategoryFilter(c.id)}
                className={`px-3 py-1.5 rounded-xl text-xs font-mono font-semibold transition-all ${
                  categoryFilter === c.id
                    ? "bg-emerald-500 text-black shadow-md shadow-emerald-500/20"
                    : "bg-cyber-darkest text-slate-400 hover:text-white border border-cyber-border"
                }`}
              >
                <span>{c.label}</span>
                <span className="ml-1 opacity-75">({c.count})</span>
              </button>
            ))}
          </div>

          {/* Right Tools */}
          <div className="flex items-center gap-3 w-full lg:w-auto justify-between lg:justify-end">
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search positions..."
              className="bg-cyber-darkest border border-cyber-border rounded-xl px-3 py-1.5 text-xs text-slate-200 font-mono focus:outline-none focus:border-cyan-500 w-full sm:w-48"
            />

            <button
              onClick={exportCSV}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-cyber-darkest border border-cyber-border text-xs font-mono text-slate-300 hover:text-white hover:border-slate-500 transition-colors shrink-0"
            >
              <Download className="w-3.5 h-3.5 text-cyan-400" />
              <span>Export CSV</span>
            </button>
          </div>
        </div>

        {/* Status Filters */}
        <div className="flex items-center gap-2 overflow-x-auto pt-2 border-t border-cyber-border/40 font-mono text-xs">
          <span className="text-slate-500 shrink-0">Status:</span>
          {["ALL", "IN_PLAY", "WINNING", "PENDING", "WON"].map((st) => (
            <button
              key={st}
              onClick={() => setStatusFilter(st)}
              className={`px-2.5 py-1 rounded-lg text-[11px] transition-colors ${
                statusFilter === st
                  ? "bg-cyan-500/20 text-cyan-300 border border-cyan-500/40"
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              {st}
            </button>
          ))}
        </div>
      </div>

      {/* Ledger Table */}
      <div className="glass-panel rounded-2xl overflow-hidden border border-cyber-border">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs font-mono">
            <thead className="bg-cyber-darkest text-slate-400 border-b border-cyber-border">
              <tr>
                <th className="py-3 px-4">MATCH & FIXTURE</th>
                <th className="py-3 px-4">MARKET / SELECTION</th>
                <th className="py-3 px-4 text-center">ODDS</th>
                <th className="py-3 px-4 text-right">STAKE ($)</th>
                <th className="py-3 px-4">MATCH STATE</th>
                <th className="py-3 px-4">STATUS</th>
                <th className="py-3 px-4 text-right">PnL ($)</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-cyber-border bg-cyber-card/60">
              {filteredRecords.length === 0 ? (
                <tr>
                  <td colSpan={7} className="py-8 text-center text-slate-500">
                    No positions found matching filters.
                  </td>
                </tr>
              ) : (
                filteredRecords.slice(0, 50).map((r, idx) => {
                  const isWinning = r.settlement_status.includes("WINNING");
                  const isTied = r.settlement_status.includes("TIED");
                  const isWon = r.settlement_status.includes("WON");
                  const isLost = r.settlement_status.includes("LOST");

                  return (
                    <tr key={idx} className="hover:bg-cyber-card transition-colors">
                      <td className="py-3.5 px-4">
                        <div className="font-bold text-white text-xs">
                          {r.match_name}
                        </div>
                        <div className="text-[11px] text-slate-400 truncate max-w-[220px]">
                          {r.competition}
                        </div>
                      </td>

                      <td className="py-3.5 px-4">
                        <div className="font-bold text-emerald-400">
                          {r.selection}
                        </div>
                        <div className="text-[10px] text-slate-400">
                          {r.market_type}
                        </div>
                      </td>

                      <td className="py-3.5 px-4 text-center">
                        <span className="font-bold text-slate-200 bg-cyber-darkest px-2 py-0.5 rounded border border-cyber-border">
                          {r.stake_odds.toFixed(2)}
                        </span>
                      </td>

                      <td className="py-3.5 px-4 text-right font-bold text-white">
                        ${r.stake_amount.toFixed(2)}
                      </td>

                      <td className="py-3.5 px-4 text-slate-300">
                        {r.current_match_state.includes("'") ? (
                          <span className="text-rose-400 font-bold flex items-center gap-1">
                            <span className="w-1.5 h-1.5 rounded-full bg-rose-500 animate-pulse" />
                            {r.current_match_state}
                          </span>
                        ) : (
                          r.current_match_state
                        )}
                      </td>

                      <td className="py-3.5 px-4">
                        <span
                          className={`inline-block px-2 py-0.5 rounded text-[10px] font-bold ${
                            isWon || isWinning
                              ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/40"
                              : isTied
                              ? "bg-cyan-500/20 text-cyan-300 border border-cyan-500/40"
                              : isLost
                              ? "bg-rose-500/20 text-rose-300 border border-rose-500/40"
                              : "bg-slate-800 text-slate-300"
                          }`}
                        >
                          {r.settlement_status}
                        </span>
                      </td>

                      <td
                        className={`py-3.5 px-4 text-right font-black ${
                          r.unrealized_or_realized_pnl > 0
                            ? "text-emerald-400"
                            : r.unrealized_or_realized_pnl < 0
                            ? "text-rose-400"
                            : "text-slate-400"
                        }`}
                      >
                        {r.unrealized_or_realized_pnl > 0
                          ? `+$${r.unrealized_or_realized_pnl.toFixed(2)}`
                          : `$${r.unrealized_or_realized_pnl.toFixed(2)}`}
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

