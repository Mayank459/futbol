"use client";

import React from "react";
import { 
  Activity, 
  TrendingUp, 
  Zap, 
  ShieldAlert, 
  Layers, 
  SlidersHorizontal, 
  Ticket, 
  BarChart3, 
  Search,
  Sparkles
} from "lucide-react";
import { motion } from "framer-motion";

export type TabKey = 
  | "matches" 
  | "slips" 
  | "steam" 
  | "sgp" 
  | "quant" 
  | "portfolio" 
  | "kelly";

interface NavbarProps {
  activeTab: TabKey;
  setActiveTab: (tab: TabKey) => void;
  slipCount: number;
  openSlipDrawer: () => void;
  openSearch: () => void;
  liveMatchesCount: number;
  steamAlertsCount: number;
}

export const Navbar: React.FC<NavbarProps> = ({
  activeTab,
  setActiveTab,
  slipCount,
  openSlipDrawer,
  openSearch,
  liveMatchesCount,
  steamAlertsCount,
}) => {
  const tabs = [
    { key: "matches" as TabKey, label: "Match Center", icon: Activity, badge: liveMatchesCount > 0 ? `${liveMatchesCount} LIVE` : undefined, badgeColor: "bg-rose-500" },
    { key: "slips" as TabKey, label: "Curated Accas", icon: Layers, badge: "4 SLIPS", badgeColor: "bg-emerald-500" },
    { key: "steam" as TabKey, label: "Steam Radar", icon: Zap, badge: steamAlertsCount > 0 ? `${steamAlertsCount} ALERTS` : undefined, badgeColor: "bg-amber-500" },
    { key: "sgp" as TabKey, label: "SGP Copula", icon: Sparkles, badge: "BOOST", badgeColor: "bg-cyan-500" },
    { key: "quant" as TabKey, label: "Quant Lab", icon: BarChart3 },
    { key: "portfolio" as TabKey, label: "Paper Ledger", icon: TrendingUp },
    { key: "kelly" as TabKey, label: "Risk Calculator", icon: SlidersHorizontal },
  ];

  return (
    <header className="sticky top-0 z-40 bg-cyber-darkest/90 backdrop-blur-md border-b border-cyber-border">
      {/* Top micro-bar */}
      <div className="hidden md:flex items-center justify-between px-6 py-1.5 text-xs text-slate-400 border-b border-cyber-border/40 font-mono">
        <div className="flex items-center gap-4">
          <span className="flex items-center gap-1.5 text-emerald-400">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse-fast inline-block" />
            LIVE FEED CONNECTED
          </span>
          <span className="text-slate-600">|</span>
          <span>SHIN DEVIG ENGINE: <strong className="text-slate-200">ACTIVE</strong></span>
          <span className="text-slate-600">|</span>
          <span>BOOKMAKER MIRROR: <strong className="text-slate-200">STAKE.AC / PINNACLE FAIR</strong></span>
        </div>
        <div className="flex items-center gap-4">
          <span className="text-slate-300">AVG CLV: <span className="text-emerald-400 font-bold">+6.38%</span></span>
          <span className="text-slate-600">|</span>
          <span className="text-slate-300">KELLY SIZING: <span className="text-cyan-400 font-bold">FRACTIONAL 0.25x</span></span>
          <span className="text-slate-600">|</span>
          <span className="text-slate-400">UTC CLOCK: <strong className="text-slate-200">{new Date().toLocaleTimeString('en-GB', { timeZone: 'UTC' })} UTC</strong></span>
        </div>
      </div>

      {/* Main navigation row */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo Brand */}
          <div className="flex items-center gap-3 cursor-pointer" onClick={() => setActiveTab("matches")}>
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-emerald-600 to-cyan-500 p-0.5 shadow-lg shadow-emerald-500/20">
              <div className="w-full h-full bg-cyber-darkest rounded-[10px] flex items-center justify-center">
                <span className="text-xl">⚽</span>
              </div>
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-extrabold text-lg tracking-wider text-white">
                  STAKE<span className="text-emerald-400">.AC</span>
                </span>
                <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 uppercase font-semibold">
                  Quant v2.4
                </span>
              </div>
              <p className="text-[11px] text-slate-400 tracking-tight font-mono">Autonomous Sports Intelligence Terminal</p>
            </div>
          </div>

          {/* Desktop Nav Tabs */}
          <nav className="hidden lg:flex items-center gap-1">
            {tabs.map((tab) => {
              const Icon = tab.icon;
              const isActive = activeTab === tab.key;
              return (
                <button
                  key={tab.key}
                  onClick={() => setActiveTab(tab.key)}
                  className={`relative px-3.5 py-2 rounded-lg text-xs font-medium transition-all duration-200 flex items-center gap-2 ${
                    isActive
                      ? "text-white"
                      : "text-slate-400 hover:text-slate-200 hover:bg-cyber-card"
                  }`}
                >
                  {isActive && (
                    <motion.div
                      layoutId="navPill"
                      className="absolute inset-0 bg-gradient-to-r from-emerald-500/20 via-cyan-500/10 to-transparent border border-emerald-500/40 rounded-lg -z-10"
                      transition={{ type: "spring", stiffness: 450, damping: 35 }}
                    />
                  )}
                  <Icon className={`w-3.5 h-3.5 ${isActive ? "text-emerald-400" : "text-slate-400"}`} />
                  <span>{tab.label}</span>
                  {tab.badge && (
                    <span className={`text-[9px] font-mono px-1.5 py-0.2 rounded-full font-bold text-white ${tab.badgeColor}`}>
                      {tab.badge}
                    </span>
                  )}
                </button>
              );
            })}
          </nav>

          {/* Right Action Buttons */}
          <div className="flex items-center gap-3">
            {/* Search shortcut button */}
            <button
              onClick={openSearch}
              className="hidden sm:flex items-center gap-2 px-3 py-1.5 rounded-lg bg-cyber-card border border-cyber-border text-xs text-slate-400 hover:text-white hover:border-slate-600 transition-colors"
            >
              <Search className="w-3.5 h-3.5 text-slate-400" />
              <span>Search fixtures...</span>
              <kbd className="font-mono text-[10px] bg-cyber-darkest px-1.5 py-0.5 rounded border border-cyber-border text-slate-500">
                ⌘K
              </kbd>
            </button>

            {/* Active Bet Slip Drawer Button */}
            <motion.button
              whileHover={{ scale: 1.03 }}
              whileTap={{ scale: 0.97 }}
              onClick={openSlipDrawer}
              className="relative flex items-center gap-2.5 px-4 py-2 rounded-xl bg-gradient-to-r from-emerald-500 to-emerald-600 hover:from-emerald-400 hover:to-emerald-500 text-black font-bold text-xs shadow-lg shadow-emerald-500/25 transition-all"
            >
              <Ticket className="w-4 h-4" />
              <span className="hidden sm:inline">BET SLIP</span>
              <span className="w-5 h-5 rounded-full bg-black text-emerald-400 font-mono text-xs flex items-center justify-center font-black">
                {slipCount}
              </span>
            </motion.button>
          </div>
        </div>
      </div>

      {/* Mobile Horizontal Sub-Navigation */}
      <div className="lg:hidden flex items-center overflow-x-auto px-4 py-2 gap-2 border-t border-cyber-border/60 scrollbar-none">
        {tabs.map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.key;
          return (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              className={`whitespace-nowrap px-3 py-1.5 rounded-lg text-xs font-medium flex items-center gap-1.5 shrink-0 ${
                isActive
                  ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/40"
                  : "bg-cyber-card text-slate-400 border border-cyber-border"
              }`}
            >
              <Icon className="w-3.5 h-3.5" />
              <span>{tab.label}</span>
              {tab.badge && (
                <span className={`text-[8px] font-mono px-1 py-0.2 rounded-full font-bold text-white ${tab.badgeColor}`}>
                  {tab.badge}
                </span>
              )}
            </button>
          );
        })}
      </div>
    </header>
  );
};

