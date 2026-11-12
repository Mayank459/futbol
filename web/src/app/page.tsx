"use client";

import React, { useState, useEffect } from "react";
import { Navbar, TabKey } from "../components/Navbar";
import { LiveTicker } from "../components/LiveTicker";
import { MatchCenter } from "../components/MatchCenter";
import { CuratedSlipsView } from "../components/CuratedSlipsView";
import { SteamArbitrageView } from "../components/SteamArbitrageView";
import { SgpCopulaView } from "../components/SgpCopulaView";
import { QuantLabView } from "../components/QuantLabView";
import { PortfolioLedgerView } from "../components/PortfolioLedgerView";
import { KellyCalculatorModal } from "../components/KellyCalculatorModal";
import { BetSlipDrawer } from "../components/BetSlipDrawer";
import { SearchModal } from "../components/SearchModal";

// Static pre-compiled datasets
import matchesData from "../data/matches.json";
import curatedSlipsData from "../data/curated_slips.json";
import teamRatingsData from "../data/team_ratings.json";
import paperLedgerData from "../data/paper_ledger.json";
import steamAlertsData from "../data/steam_alerts.json";
import sgpCopulaData from "../data/sgp_copula.json";

import { 
  MatchFixture, 
  CuratedBetSlip, 
  TeamRating, 
  PaperBetRecord, 
  SteamAlert, 
  SameGameParlay, 
  ActiveSlipItem, 
  PortfolioSummary 
} from "../types";

export default function Home() {
  const [activeTab, setActiveTab] = useState<TabKey>("matches");
  const [activeSlip, setActiveSlip] = useState<ActiveSlipItem[]>([]);
  const [isSlipDrawerOpen, setIsSlipDrawerOpen] = useState<boolean>(false);
  const [isSearchOpen, setIsSearchOpen] = useState<boolean>(false);

  // Dynamic portfolio state (starts with pre-computed ledger, allows live simulation)
  const [ledgerRecords, setLedgerRecords] = useState<PaperBetRecord[]>(paperLedgerData.records as PaperBetRecord[]);
  const [summary, setSummary] = useState<PortfolioSummary>(paperLedgerData.summary as PortfolioSummary);

  // Type assertion on data
  const liveMatches = (matchesData.live_matches || []) as unknown as MatchFixture[];
  const upcomingMatches = (matchesData.matches || []) as unknown as MatchFixture[];
  const curatedSlips = (curatedSlipsData.slips || []) as unknown as CuratedBetSlip[];
  const teams = (teamRatingsData.teams || []) as unknown as TeamRating[];
  const steamAlerts = (steamAlertsData.alerts || []) as unknown as SteamAlert[];
  const sgps = (sgpCopulaData.sgps || []) as unknown as SameGameParlay[];

  // Load slip from localStorage on mount
  useEffect(() => {
    try {
      const saved = localStorage.getItem("stake_active_slip");
      if (saved) {
        setActiveSlip(JSON.parse(saved));
      }
    } catch (e) {
      // Ignore
    }
  }, []);

  // Sync slip to localStorage
  useEffect(() => {
    try {
      localStorage.setItem("stake_active_slip", JSON.stringify(activeSlip));
    } catch (e) {
      // Ignore
    }
  }, [activeSlip]);

  // Toggle leg in active slip
  const handleToggleLeg = (leg: ActiveSlipItem) => {
    setActiveSlip((prev) => {
      const exists = prev.some((l) => l.id === leg.id);
      if (exists) {
        return prev.filter((l) => l.id !== leg.id);
      } else {
        // Automatically open the drawer on desktop when a leg is added
        setIsSlipDrawerOpen(true);
        return [...prev, leg];
      }
    });
  };

  const handleRemoveLeg = (id: string) => {
    setActiveSlip((prev) => prev.filter((l) => l.id !== id));
  };

  const handleClearSlip = () => {
    setActiveSlip([]);
  };

  const handleLoadSlip = (legs: ActiveSlipItem[]) => {
    setActiveSlip(legs);
    setIsSlipDrawerOpen(true);
  };

  // Simulate placing custom accumulator bet
  const handleSimulatePlacedSlip = (
    totalOdds: number,
    stake: number,
    payout: number,
    profit: number
  ) => {
    const newBet: PaperBetRecord = {
      bet_id: `SIM_${Date.now()}`,
      category: activeSlip.length > 1 ? "UPCOMING_ACCA" : "UPCOMING_SINGLE",
      match_id: activeSlip[0]?.matchId || "custom",
      match_name: activeSlip.map((s) => s.selection).join(" + "),
      competition: activeSlip.length > 1 ? "Custom Cross-League Acca" : activeSlip[0]?.competition || "Custom Single",
      kickoff_str: "Simulated Live",
      market_type: activeSlip.length > 1 ? "Multi-Bet Accumulator" : activeSlip[0]?.marketType || "Single",
      selection: activeSlip.map((s) => `${s.selection} @ ${s.odds}`).join(", "),
      stake_odds: Number(totalOdds.toFixed(2)),
      fair_odds: Number((totalOdds * 0.95).toFixed(2)),
      model_probability: Number((1 / totalOdds).toFixed(3)),
      edge_pct: 5.2,
      stake_amount: stake,
      potential_payout: payout,
      potential_profit: profit,
      placed_at: new Date().toISOString().replace("T", " ").substring(0, 19) + " UTC",
      current_match_state: "PENDING KICKOFF",
      settlement_status: "PENDING",
      unrealized_or_realized_pnl: 0.0,
      notes: "Placed via Stake.ac Interactive Bet Slip Builder",
    };

    setLedgerRecords((prev) => [newBet, ...prev]);
    setSummary((prev) => ({
      ...prev,
      total_bets: prev.total_bets + 1,
      total_capital_staked: Number((prev.total_capital_staked + stake).toFixed(2)),
      accumulators: activeSlip.length > 1 ? prev.accumulators + 1 : prev.accumulators,
      upcoming_singles: activeSlip.length === 1 ? prev.upcoming_singles + 1 : prev.upcoming_singles,
    }));
  };

  // Simulate placing curated slip
  const handlePlaceSimulatedCuratedSlip = (slip: CuratedBetSlip) => {
    const newBet: PaperBetRecord = {
      bet_id: `CURATED_${Date.now()}`,
      category: "UPCOMING_ACCA",
      match_id: slip.slip_id,
      match_name: slip.slip_name,
      competition: "Curated Algorithmic Slip",
      kickoff_str: "Upcoming",
      market_type: slip.strategy_badge,
      selection: slip.legs.map((l) => `${l.selection} (${l.match_name})`).join("; "),
      stake_odds: slip.combined_odds,
      fair_odds: Number((1 / slip.combined_probability).toFixed(2)),
      model_probability: slip.combined_probability,
      edge_pct: slip.combined_edge,
      stake_amount: slip.suggested_stake_amount,
      potential_payout: slip.potential_payout,
      potential_profit: slip.net_profit_on_win,
      placed_at: new Date().toISOString().replace("T", " ").substring(0, 19) + " UTC",
      current_match_state: "PENDING KICKOFF",
      settlement_status: "PENDING",
      unrealized_or_realized_pnl: 0.0,
      notes: slip.strategy_description,
    };

    setLedgerRecords((prev) => [newBet, ...prev]);
    setSummary((prev) => ({
      ...prev,
      total_bets: prev.total_bets + 1,
      total_capital_staked: Number((prev.total_capital_staked + slip.suggested_stake_amount).toFixed(2)),
      accumulators: prev.accumulators + 1,
    }));
  };

  // Simulate placing SGP
  const handleSimulateSgp = (sgp: SameGameParlay) => {
    const newBet: PaperBetRecord = {
      bet_id: `SGP_${Date.now()}`,
      category: "SAME_GAME_PARLAY",
      match_id: sgp.match_id,
      match_name: sgp.match_name,
      competition: sgp.competition,
      kickoff_str: sgp.kickoff_str,
      market_type: "Same-Game Parlay",
      selection: `${sgp.combo_name}: ${sgp.legs.map((l) => l.description).join(" + ")}`,
      stake_odds: sgp.stake_offered_odds,
      fair_odds: sgp.true_fair_odds,
      model_probability: sgp.exact_joint_probability,
      edge_pct: sgp.ev_edge,
      stake_amount: sgp.suggested_stake_amount,
      potential_payout: sgp.potential_payout,
      potential_profit: sgp.net_profit,
      placed_at: new Date().toISOString().replace("T", " ").substring(0, 19) + " UTC",
      current_match_state: "PENDING KICKOFF",
      settlement_status: "PENDING",
      unrealized_or_realized_pnl: 0.0,
      notes: sgp.narrative,
    };

    setLedgerRecords((prev) => [newBet, ...prev]);
    setSummary((prev) => ({
      ...prev,
      total_bets: prev.total_bets + 1,
      total_capital_staked: Number((prev.total_capital_staked + sgp.suggested_stake_amount).toFixed(2)),
      same_game_parlays: prev.same_game_parlays + 1,
    }));
  };

  return (
    <div className="min-h-screen bg-cyber-darkest text-slate-100 flex flex-col bg-grid-pattern selection:bg-emerald-500 selection:text-black">
      {/* Top Navigation */}
      <Navbar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        slipCount={activeSlip.length}
        openSlipDrawer={() => setIsSlipDrawerOpen(true)}
        openSearch={() => setIsSearchOpen(true)}
        liveMatchesCount={liveMatches.length}
        steamAlertsCount={steamAlerts.length}
      />

      {/* Real-time Ticker */}
      <LiveTicker
        alerts={steamAlerts}
        summary={summary}
        onSelectAlert={(a) => {
          setActiveTab("steam");
        }}
      />

      {/* Main Container */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {activeTab === "matches" && (
          <MatchCenter
            liveMatches={liveMatches}
            upcomingMatches={upcomingMatches}
            activeSlip={activeSlip}
            onToggleLeg={handleToggleLeg}
          />
        )}

        {activeTab === "slips" && (
          <CuratedSlipsView
            slips={curatedSlips}
            onLoadSlip={handleLoadSlip}
            onPlaceSimulatedSlip={handlePlaceSimulatedCuratedSlip}
          />
        )}

        {activeTab === "steam" && (
          <SteamArbitrageView
            alerts={steamAlerts}
            onAddLeg={(leg) => {
              handleToggleLeg(leg);
            }}
          />
        )}

        {activeTab === "sgp" && (
          <SgpCopulaView
            sgps={sgps}
            onAddLeg={handleToggleLeg}
            onSimulateSgp={handleSimulateSgp}
          />
        )}

        {activeTab === "quant" && <QuantLabView teams={teams} />}

        {activeTab === "portfolio" && (
          <PortfolioLedgerView
            records={ledgerRecords}
            summary={summary}
          />
        )}

        {activeTab === "kelly" && <KellyCalculatorModal />}
      </main>

      {/* Slide-over Bet Slip Ticket Drawer */}
      <BetSlipDrawer
        isOpen={isSlipDrawerOpen}
        onClose={() => setIsSlipDrawerOpen(false)}
        items={activeSlip}
        onRemoveItem={handleRemoveLeg}
        onClearSlip={handleClearSlip}
        onSimulatePlacedSlip={handleSimulatePlacedSlip}
      />

      {/* Global Search Modal */}
      <SearchModal
        isOpen={isSearchOpen}
        onClose={() => setIsSearchOpen(false)}
        matches={[...liveMatches, ...upcomingMatches]}
        onSelectMatch={(m) => {
          setActiveTab("matches");
        }}
        onAddLeg={handleToggleLeg}
      />

      {/* Footer */}
      <footer className="border-t border-cyber-border/60 py-6 px-4 bg-cyber-darkest text-center text-xs text-slate-500 font-mono">
        <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-3">
          <div>
            STAKE.AC QUANT INTELLIGENCE TERMINAL • Dixon-Coles xG Calibrated • Online Kalman Filter
          </div>
          <div>
            CLV Tracking +6.38% vs Pinnacle Closing Line • Fractional Kelly Bankroll Management
          </div>
        </div>
      </footer>
    </div>
  );
}
