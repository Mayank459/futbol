"""De-vigging (Margin Removal) Algorithms.

Provides:
1. Proportional (Multiplicative / Standard normalization)
2. Power (Logarithmic method)
3. Shin's Method (Accounts for favorite-longshot bias by modeling insider trading parameter z)
"""

from typing import Dict, List
import numpy as np
from scipy.optimize import brentq


def devig_proportional(odds: Dict[str, float]) -> Dict[str, float]:
    """Basic proportional margin removal:
    p_i = (1 / O_i) / sum(1 / O_k)
    """
    implied = {k: 1.0 / v for k, v in odds.items()}
    overround = sum(implied.values())
    return {k: round(v / overround, 6) for k, v in implied.items()}


def devig_power(odds: Dict[str, float]) -> Dict[str, float]:
    """Power (Logarithmic) method:
    Finds exponent k such that sum((1 / O_i)^k) == 1.0.
    Mitigates favorite-longshot bias more effectively than proportional.
    """
    inv_odds = np.array([1.0 / v for v in odds.values()])
    keys = list(odds.keys())

    # Objective function
    def f(k):
        return np.sum(inv_odds ** k) - 1.0

    try:
        # k typically sits between 1.0 and 1.5 when overround > 1.0
        k_opt = brentq(f, 0.5, 3.0)
        fair_probs = inv_odds ** k_opt
        fair_probs /= np.sum(fair_probs)
        return {k: round(float(p), 6) for k, p in zip(keys, fair_probs)}
    except Exception:
        # Fallback to proportional if root-finding fails
        return devig_proportional(odds)


def devig_shin(odds: Dict[str, float]) -> Dict[str, float]:
    """Shin's method for margin removal.
    Accounts for the favorite-longshot bias by assuming bookmaker margin is set to protect
    against informed bettors with probability z of knowing the true outcome.

    Formula:
    pi_i = 1 / O_i
    p_i = (sqrt(z^2 + 4 * (1 - z) * (pi_i^2 / sum(pi))) - z) / (2 * (1 - z))
    """
    keys = list(odds.keys())
    inv_odds = np.array([1.0 / odds[k] for k in keys], dtype=float)
    sum_inv = np.sum(inv_odds)

    if sum_inv <= 1.0:
        # No margin or negative margin (arbitrage line)
        norm = inv_odds / sum_inv
        return {k: round(float(p), 6) for k, p in zip(keys, norm)}

    # Objective function: find z in [0, 0.4] such that sum(p_i) == 1.0
    def objective(z):
        if abs(1.0 - z) < 1e-9:
            return 1.0
        num = np.sqrt(z**2 + 4.0 * (1.0 - z) * (inv_odds**2 / sum_inv)) - z
        den = 2.0 * (1.0 - z)
        p = num / den
        return np.sum(p) - 1.0

    try:
        # Check boundary condition
        z_opt = brentq(objective, 0.0, 0.4, xtol=1e-6)
        num = np.sqrt(z_opt**2 + 4.0 * (1.0 - z_opt) * (inv_odds**2 / sum_inv)) - z_opt
        den = 2.0 * (1.0 - z_opt)
        p_opt = num / den
        p_opt /= np.sum(p_opt)  # Clean normalization
        return {k: round(float(p), 6) for k, p in zip(keys, p_opt)}
    except Exception:
        # If Shin optimization fails, use Power method as robust fallback
        return devig_power(odds)


def get_fair_sharp_probabilities(odds: Dict[str, float], method: str = "shin") -> Dict[str, float]:
    """Helper to dispatch to the preferred devigging method."""
    if method == "shin":
        return devig_shin(odds)
    elif method == "power":
        return devig_power(odds)
    elif method == "proportional":
        return devig_proportional(odds)
    else:
        raise ValueError(f"Unknown devig method: {method}")

