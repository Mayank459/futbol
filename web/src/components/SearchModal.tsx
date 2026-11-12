"use client";

import React, { useState, useEffect } from "react";
import { Search, X, Calendar, ArrowRight, Zap, ShieldCheck } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { MatchFixture, ActiveSlipItem } from "../types";

interface SearchModalProps {
  isOpen: boolean;
  onClose: () => void;
  matches: MatchFixture[];
  onSelectMatch: (match: MatchFixture) => void;
  onAddLeg: (leg: ActiveSlipItem) => void;
}

export const SearchModal: React.FC<SearchModalProps> = ({
  isOpen,
  onClose,
  matches,
  onSelectMatch,
  onAddLeg,
}) => {
  const [query, setQuery] = useState("");

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === "k") {
        e.preventDefault();
        if (isOpen) onClose();
      } else if (e.key === "Escape" && isOpen) {
        onClose();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, onClose]);

  const results = query.trim()
    ? matches
        .filter(
          (m) =>
            m.match_name.toLowerCase().includes(query.toLowerCase()) ||
            m.competition?.toLowerCase().includes(query.toLowerCase()) ||
            m.home_team?.toLowerCase().includes(query.toLowerCase()) ||
            m.away_team?.toLowerCase().includes(query.toLowerCase())
        )
        .slice(0, 10)
    : matches.slice(0, 6);

  if (!isOpen) return null;

  return (
    <AnimatePresence>
      <div className="fixed inset-0 z-50 flex items-start justify-center pt-20 px-4">
        {/* Backdrop */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          onClick={onClose}
          className="fixed inset-0 bg-black/80 backdrop-blur-sm"
        />

        {/* Modal Box */}
        <motion.div
          initial={{ opacity: 0, scale: 0.96, y: -10 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.96, y: -10 }}
          className="relative w-full max-w-2xl bg-cyber-darkest border border-cyber-border rounded-2xl shadow-2xl overflow-hidden z-10"
        >
          {/* Search Input Bar */}
          <div className="p-4 border-b border-cyber-border flex items-center gap-3 bg-cyber-card/60">
            <Search className="w-5 h-5 text-slate-400 shrink-0" />
            <input
              type="text"
              autoFocus
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search by team (e.g. Arsenal, Real Madrid), competition or venue..."
              className="w-full bg-transparent text-sm text-white placeholder-slate-500 focus:outline-none font-mono"
            />
            {query && (
              <button
                onClick={() => setQuery("")}
                className="text-slate-400 hover:text-white"
              >
                <X className="w-4 h-4" />
              </button>
            )}
            <kbd className="hidden sm:inline font-mono text-[10px] bg-cyber-darkest px-2 py-0.5 rounded border border-cyber-border text-slate-400">
              ESC
            </kbd>
          </div>

          {/* Results List */}
          <div className="max-h-[60vh] overflow-y-auto p-3 space-y-2">
            <div className="px-3 py-1 text-[11px] font-mono text-slate-500">
              {query ? `RESULTS (${results.length})` : "RECOMMENDED UPCOMING FIXTURES"}
            </div>

            {results.length === 0 ? (
              <div className="p-8 text-center text-xs font-mono text-slate-500">
                No fixtures found matching &ldquo;{query}&rdquo;
              </div>
            ) : (
              results.map((m) => (
                <div
                  key={m.match_id}
                  className="p-3 rounded-xl bg-cyber-card/40 hover:bg-cyber-card border border-cyber-border/70 hover:border-cyan-500/50 transition-all flex items-center justify-between group cursor-pointer"
                  onClick={() => {
                    onSelectMatch(m);
                    onClose();
                  }}
                >
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-full bg-slate-800 flex items-center justify-center text-xs font-bold text-slate-400">
                      ⚽
                    </div>
                    <div>
                      <div className="text-xs font-bold text-white group-hover:text-cyan-400 transition-colors">
                        {m.match_name}
                      </div>
                      <div className="text-[11px] text-slate-400 font-mono">
                        {m.competition} • {m.kickoff_time}
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center gap-2">
                    <span className="font-mono text-xs text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20">
                      {m.stake_odds.home} / {m.stake_odds.draw} / {m.stake_odds.away}
                    </span>
                    <ArrowRight className="w-4 h-4 text-slate-500 group-hover:text-white group-hover:translate-x-0.5 transition-all" />
                  </div>
                </div>
              ))
            )}
          </div>
        </motion.div>
      </div>
    </AnimatePresence>
  );
};

