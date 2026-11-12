# ⚽ Stake.ac Quant Terminal — Autonomous Football AI Value-Betting & Trading Platform

A modern, high-frequency quantitative sports betting, latency arbitrage, and portfolio intelligence web application built with **Next.js 14 (App Router)**, **TypeScript**, **Tailwind CSS**, and **Framer Motion**. Designed for zero-friction deployment to **Vercel**.

---

## 🚀 Live Demo & Key Modules

1. **⚽ Match Center (Live & Upcoming Fixtures)**:
   - Real-time in-play broadcast cards with live scoreboards, match minute indicators, momentum tickers, and club crests.
   - 160+ European fixtures across **Premier League**, **La Liga**, **Serie A**, **Bundesliga**, **Ligue 1**, and **UEFA Nations League**.
   - 1X2 Comparison Matrix: **Stake Retail Odds** vs **Pinnacle Sharp Closing Line** vs **Shin De-Vigged Fair Odds** with Expected Value (+EV) badges.
   - Interactive Secondary Markets Explorer: **Draw No Bet (DNB)**, **Double Chance (1X/X2)**, **Both Teams To Score (BTTS Yes/No)**, **Over 1.5 Goals**, and **Team Clean Sheet**.
   - 1-Click Interactive Bet Selection directly synced to the active bet slip drawer.

2. **🎯 Curated Algorithmic Bet Slips**:
   - **🛡️ Fortress Acca (Neon Emerald)**: Combines high-certainty Double Chance and dominant home favorites (~75-85% win probability).
   - **⚖️ Uncertainty Hedge Acca (Neon Violet)**: Replaces volatile 1X2 games with Draw No Bet and Poisson-derived BTTS hedges.
   - **🔥 Pure +EV Multiplier (Cyber Amber)**: Exploits retail execution latency against Pinnacle fair lines.
   - **⚡ Double Lock (Electric Cyan)**: 2-leg high-roller precision multiplier for optimal Kelly sizing.
   - 1-Click "Copy Stake.ac Ticket" and "Place Paper Bet" with confetti celebration.

3. **⚡ Real-Time Steam & Latency Arbitrage Radar**:
   - Detects rapid Pinnacle line movement ($\Delta \text{Odds}/\Delta t$) where Stake's retail odds lag behind.
   - Urgency classification (`CRITICAL` <2m, `HIGH` <5m, `MODERATE`) with countdown windows and edge capture buttons.

4. **🧬 Same-Game Parlay (SGP) Copula Engine**:
   - Eliminates naive independence fallacy ($P(A \cap B) \neq P(A) \cdot P(B)$).
   - Direct integration over bivariate Poisson score matrices to calculate exact joint probabilities, unlocking up to **+45% Correlation Edge Boost**.

5. **🔬 Quant Lab & Head-to-Head Poisson Match Simulator**:
   - Interactive match simulator: pick any 2 of 96 European clubs to simulate expected scorelines, home advantage, goal intensity ($\lambda, \mu$), and Poisson score distribution.
   - Comprehensive European club leaderboard: xG Attack, xG Defense, and Online Kalman Filter Form Momentum ($\Delta \text{Rating}/\Delta t$).

6. **📊 Paper-Trading Portfolio & PnL Ledger**:
   - Real-time portfolio performance tracking: Total Capital Staked, Net PnL, Win Rate (%), and Closing Line Value (+6.38% CLV).
   - Live In-Play positions table with minute-by-minute updates.
   - Filters for Singles, Accumulators, and SGPs with CSV export.

7. **🧮 Fractional Kelly Risk Calculator**:
   - Interactive sliders for Bankroll, Offered Odds, and Model Win Probability.
   - Full Kelly vs Half Kelly vs Quarter Kelly comparison with a 20-bet Monte Carlo compounding simulation preview.

8. **🎫 Slide-over Bet Slip Drawer & Global Search (⌘K)**:
   - Interactive ticket builder calculating combined accumulator odds and joint win probabilities in real time.
   - Global search modal across all clubs, leagues, and venues.

---

## 🛠️ Local Development

### Prerequisites
- Node.js 18+ (tested on Node v24)
- Python 3.10+ (for re-exporting quant models from local CSVs/SQLite)

### Run Web App
```bash
# From repository root:
npm run dev

# Or directly in web directory:
cd web
npm run dev
```
Open [http://localhost:3000](http://localhost:3000) in your browser.

### Re-export Data from Python Quant Engine
If you run new backtests or update the SQLite paper ledger:
```bash
python scripts/export_web_data.py
```

---

## 🌐 Deploy to Vercel

### Option 1: Vercel Git Integration (Recommended)
1. Push this repository to GitHub or GitLab.
2. Go to [vercel.com/new](https://vercel.com/new) and import the repository.
3. If deploying from the repository root:
   - The included `vercel.json` and `package.json` will automatically orchestrate the build.
   - Alternatively, set **Root Directory** to `web`.
4. Click **Deploy**. Done!

### Option 2: Vercel CLI
```bash
cd web
npm install -g vercel
vercel deploy
```
