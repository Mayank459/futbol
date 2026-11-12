"""Telegram & Webhook Alert Dispatcher for Stake Value Bets.

Sends formatted instant notifications when:
1. A high-conviction +EV value bet is detected on Stake (stake.ac).
2. A dominating-teams Multi-Bet slip is ready to place.
3. Market Steam / Line Movement is detected (Stake lagging Pinnacle).
Supports both live Telegram Bot API and local console/logging fallback.
"""

import os
import requests
from typing import Dict, Optional, List
from datetime import datetime, timezone
from src.core.schemas import BetRecommendation
from src.modeling.multibet import MultiBetSlip


class TelegramNotifier:
    def __init__(
        self,
        bot_token: Optional[str] = None,
        chat_id: Optional[str] = None,
        stake_mirror: str = "stake.ac"
    ):
        self.bot_token = bot_token or os.getenv("TELEGRAM_BOT_TOKEN")
        self.chat_id = chat_id or os.getenv("TELEGRAM_CHAT_ID")
        self.stake_mirror = stake_mirror
        self.is_active = bool(self.bot_token and self.chat_id)

    def send_message(self, text: str) -> bool:
        """Sends a markdown message to the configured Telegram chat."""
        if not self.is_active:
            # Fallback to stdout/logging if no token configured
            print(f"\n[TELEGRAM DISPATCH (Simulated)]\n{text}\n")
            return True

        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": text,
            "parse_mode": "Markdown"
        }
        try:
            resp = requests.post(url, json=payload, timeout=8)
            return resp.status_code == 200
        except Exception as e:
            print(f"Telegram dispatch error: {e}")
            return False

    def notify_value_pick(self, pick: BetRecommendation) -> bool:
        """Dispatches an alert for an individual +EV value bet."""
        msg = (
            f"🚨 *NEW VALUE BET ON STAKE* ({self.stake_mirror})\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"⚽ *Match:* {pick.home_team} vs {pick.away_team}\n"
            f"🏆 *League:* {pick.competition}\n"
            f"👉 *Pick:* `{pick.selection.upper()}` @ *{pick.offered_odds}*\n"
            f"⚡ *Pinnacle Fair Line:* {pick.fair_sharp_odds}\n"
            f"📈 *Pure Sharp Edge:* +{pick.edge*100:.2f}%\n"
            f"💰 *Recommended Stake:* ${pick.suggested_stake_amount:.2f} ({pick.stake_fraction*100:.2f}%)\n"
            f"🔒 *Confidence:* {pick.confidence_label.upper()}\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🕒 _{datetime.now(timezone.utc).strftime('%H:%M:%S UTC')}_"
        )
        return self.send_message(msg)

    def notify_multibet(self, multibet: MultiBetSlip) -> bool:
        """Dispatches an alert for a dominating-favorites Multi-Bet parlay."""
        legs_text = ""
        for i, leg in enumerate(multibet.legs, 1):
            legs_text += f"{i}. *{leg.match_name}* -> `{leg.selection}` @ {leg.odds} ({leg.win_probability*100:.0f}% win)\n"

        msg = (
            f"🎯 *NEW STAKE MULTI-BET SLIP* ({self.stake_mirror})\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"⚡ *Dominating Favorites Parlay*\n\n"
            f"{legs_text}\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🔥 *Multiplied Odds:* *{multibet.combined_odds}x*\n"
            f"📊 *Joint Probability:* {multibet.combined_probability*100:.1f}%\n"
            f"💵 *Suggested Stake:* ${multibet.suggested_stake_amount:.2f}\n"
            f"🚀 *Potential Payout:* *${multibet.potential_payout:.2f}* (+${multibet.net_profit_on_win:.2f})\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🕒 _{datetime.now(timezone.utc).strftime('%H:%M:%S UTC')}_"
        )
        return self.send_message(msg)

