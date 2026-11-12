"use client";

import React, { useState } from "react";
import { 
  X, 
  Trash2, 
  Ticket, 
  Copy, 
  Check, 
  DollarSign, 
  Sparkles, 
  Calendar,
  Layers,
  ArrowRight
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import confetti from "canvas-confetti";
import { ActiveSlipItem } from "../types";

interface BetSlipDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  items: ActiveSlipItem[];
  onRemoveItem: (id: string) => void;
  onClearSlip: () => void;
  onSimulatePlacedSlip: (totalOdds: number, stake: number, payout: number, profit: number) => void;
}

export const BetSlipDrawer: React.FC<BetSlipDrawerProps> = ({
  isOpen,
  onClose,
  items,
  onRemoveItem,
  onClearSlip,
  onSimulatePlacedSlip,
}) => {
  const [stakeAmount, setStakeAmount] = useState<number>(25);
  const [copied, setCopied] = useState<boolean>(false);

  // Compute combined odds and win prob
  const combinedOdds = items.reduce((acc, item) => acc * item.odds, 1);
  const combinedProb = items.reduce((acc, item) => acc * item.winProb, 1);
  const potentialPayout = stakeAmount * combinedOdds;
  const potentialProfit = potentialPayout - stakeAmount;

  const handleCopyTicket = () => {
    let text = `⚽ STAKE.AC QUANT BET SLIP\n`;
    text += `Legs: ${items.length} | Combined Odds: ${combinedOdds.toFixed(2)}x\n`;
    text += `Suggested Stake: $${stakeAmount} | Return: $${potentialPayout.toFixed(2)}\n\n`;
    items.forEach((leg, idx) => {
      text += `${idx + 1}. [${leg.competition}] ${leg.matchName}\n`;
      text += `   Pick: ${leg.selection} (${leg.marketType}) @ ${leg.odds.toFixed(2)}\n`;
      text += `   Date: ${leg.kickoffStr}\n\n`;
    });
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2500);
  };

  const handleSimulateBet = () => {
    confetti({
      particleCount: 100,
      spread: 70,
      origin: { y: 0.5 },
      colors: ["#10b981", "#06b6d4", "#f59e0b", "#a855f7"],
    });
    onSimulatePlacedSlip(combinedOdds, stakeAmount, potentialPayout, potentialProfit);
    onClearSlip();
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50"
          />

          {/* Drawer Sheet */}
          <motion.div
            initial={{ x: "100%" }}
            animate={{ x: 0 }}
            exit={{ x: "100%" }}
            transition={{ type: "spring", damping: 30, stiffness: 350 }}
            className="fixed top-0 right-0 bottom-0 w-full sm:w-[450px] bg-cyber-darkest border-l border-cyber-border z-50 flex flex-col justify-between shadow-2xl"
          >
            {/* Header */}
            <div className="p-5 border-b border-cyber-border flex items-center justify-between bg-cyber-card/80">
              <div className="flex items-center gap-2.5">
                <Ticket className="w-5 h-5 text-emerald-400" />
                <h3 className="text-base font-black text-white font-mono">
                  ACTIVE BET SLIP ({items.length})
                </h3>
              </div>

              <div className="flex items-center gap-2">
                {items.length > 0 && (
                  <button
                    onClick={onClearSlip}
                    className="p-1.5 rounded-lg text-slate-400 hover:text-rose-400 hover:bg-cyber-darkest transition-colors text-xs font-mono flex items-center gap-1"
                    title="Clear Slip"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                )}
                <button
                  onClick={onClose}
                  className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-cyber-darkest transition-colors"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>
            </div>

            {/* Slip Content / Legs List */}
            <div className="flex-1 overflow-y-auto p-5 space-y-3">
              {items.length === 0 ? (
                <div className="h-full flex flex-col items-center justify-center text-center p-6 text-slate-500 font-mono">
                  <Ticket className="w-12 h-12 text-slate-700 mb-3" />
                  <p className="text-sm text-slate-400 font-bold mb-1">
                    Your Bet Slip is Empty
                  </p>
                  <p className="text-xs max-w-xs text-slate-500">
                    Click on any odds button in Match Center, Curated Slips, or Steam Radar to add selections to your ticket.
                  </p>
                </div>
              ) : (
                items.map((leg) => (
                  <motion.div
                    key={leg.id}
                    layout
                    initial={{ opacity: 0, scale: 0.95 }}
                    animate={{ opacity: 1, scale: 1 }}
                    exit={{ opacity: 0, scale: 0.95 }}
                    className="p-3.5 rounded-xl bg-cyber-card border border-cyber-border flex flex-col gap-2 relative group"
                  >
                    {/* Top Row: League & Remove */}
                    <div className="flex items-center justify-between text-xs font-mono">
                      <span className="text-slate-400 truncate max-w-[240px]">
                        {leg.competition}
                      </span>
                      <button
                        onClick={() => onRemoveItem(leg.id)}
                        className="text-slate-500 hover:text-rose-400 transition-colors"
                      >
                        <X className="w-4 h-4" />
                      </button>
                    </div>

                    {/* Match Name */}
                    <div className="text-xs font-bold text-white">
                      {leg.matchName}
                    </div>

                    {/* Market & Pick */}
                    <div className="flex items-center justify-between pt-1 border-t border-cyber-border/40 text-xs font-mono">
                      <div>
                        <span className="text-emerald-400 font-bold">
                          {leg.selection}
                        </span>
                        <span className="text-slate-500 text-[10px] ml-1">
                          ({leg.marketType})
                        </span>
                      </div>

                      <div className="text-right">
                        <span className="font-black text-white bg-cyber-darkest px-2 py-0.5 rounded border border-cyber-border text-xs">
                          {leg.odds.toFixed(2)}
                        </span>
                      </div>
                    </div>
                  </motion.div>
                ))
              )}
            </div>

            {/* Bottom Sizing & Action Sheet */}
            {items.length > 0 && (
              <div className="p-5 border-t border-cyber-border bg-cyber-card/90 space-y-4">
                {/* Financial Summary */}
                <div className="grid grid-cols-3 gap-2 text-center font-mono text-xs p-3 rounded-xl bg-cyber-darkest border border-cyber-border">
                  <div>
                    <div className="text-[10px] text-slate-400">COMBINED ODDS</div>
                    <div className="text-base font-black text-emerald-400 mt-0.5">
                      {combinedOdds.toFixed(2)}x
                    </div>
                  </div>
                  <div>
                    <div className="text-[10px] text-slate-400">WIN PROB</div>
                    <div className="text-base font-black text-cyan-400 mt-0.5">
                      {(combinedProb * 100).toFixed(1)}%
                    </div>
                  </div>
                  <div>
                    <div className="text-[10px] text-slate-400">NET PROFIT</div>
                    <div className="text-base font-black text-amber-400 mt-0.5">
                      +${potentialProfit.toFixed(2)}
                    </div>
                  </div>
                </div>

                {/* Stake Presets & Input */}
                <div>
                  <div className="flex justify-between text-xs font-mono text-slate-300 mb-1.5">
                    <span>Stake Amount:</span>
                    <strong className="text-white">${stakeAmount}</strong>
                  </div>

                  <div className="grid grid-cols-4 gap-2 mb-2">
                    {[10, 25, 50, 100].map((amt) => (
                      <button
                        key={amt}
                        onClick={() => setStakeAmount(amt)}
                        className={`py-1.5 rounded-lg text-xs font-mono font-bold transition-all ${
                          stakeAmount === amt
                            ? "bg-emerald-500 text-black"
                            : "bg-cyber-darkest text-slate-400 border border-cyber-border hover:text-white"
                        }`}
                      >
                        ${amt}
                      </button>
                    ))}
                  </div>

                  <input
                    type="range"
                    min={5}
                    max={500}
                    step={5}
                    value={stakeAmount}
                    onChange={(e) => setStakeAmount(Number(e.target.value))}
                    className="w-full accent-emerald-400"
                  />
                </div>

                {/* Primary Action Buttons */}
                <div className="grid grid-cols-2 gap-2 font-mono text-xs">
                  <button
                    onClick={handleCopyTicket}
                    className="py-2.5 px-3 rounded-xl bg-cyber-darkest border border-cyber-border text-slate-300 hover:text-white hover:border-slate-500 font-bold flex items-center justify-center gap-1.5 transition-colors"
                  >
                    {copied ? (
                      <>
                        <Check className="w-3.5 h-3.5 text-emerald-400" />
                        <span className="text-emerald-400">Copied!</span>
                      </>
                    ) : (
                      <>
                        <Copy className="w-3.5 h-3.5 text-slate-400" />
                        <span>Copy Stake Slip</span>
                      </>
                    )}
                  </button>

                  <button
                    onClick={handleSimulateBet}
                    className="py-2.5 px-3 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-black font-black flex items-center justify-center gap-1.5 transition-colors shadow-lg shadow-emerald-500/25"
                  >
                    <DollarSign className="w-4 h-4" />
                    <span>Place Paper Bet</span>
                  </button>
                </div>
              </div>
            )}
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
};

