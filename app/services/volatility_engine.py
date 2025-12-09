import numpy as np
from typing import List, Dict


class VolatilityEngine:
    """Calculate realized and implied volatility for position sizing"""

    @staticmethod
    def calculate_returns(prices: List[float]) -> List[float]:
        """Calculate log returns from prices"""
        if len(prices) < 2:
            return [0.0]
        returns: List[float] = []
        for i in range(1, len(prices)):
            if prices[i - 1] > 0:
                ret = np.log(prices[i] / prices[i - 1])
                returns.append(ret)
        return returns if returns else [0.0]

    @staticmethod
    def calculate_realized_vol(prices: List[float], period: int = 20) -> float:
        """Calculate realized volatility"""
        try:
            if len(prices) < period:
                return 0.02
            returns = VolatilityEngine.calculate_returns(prices[-period:])
            if not returns or len(returns) < 2:
                return 0.02
            vol = float(np.std(returns))
            return max(0.001, min(vol, 0.5))
        except Exception:
            return 0.02

    @staticmethod
    def calculate_garch_vol(
        prices: List[float],
        period: int = 20,
        alpha: float = 0.1,
        beta: float = 0.8,
    ) -> float:
        """GARCH(1,1) volatility estimation"""
        try:
            if len(prices) < period:
                return VolatilityEngine.calculate_realized_vol(prices)
            returns = VolatilityEngine.calculate_returns(prices[-period:])
            if not returns or len(returns) < 2:
                return 0.02
            omega = (1 - alpha - beta) * (np.mean(returns) ** 2)
            sigma_sq = np.var(returns)
            for ret in returns:
                sigma_sq = omega + alpha * (ret ** 2) + beta * sigma_sq
            vol = float(np.sqrt(sigma_sq))
            return max(0.001, min(vol, 0.5))
        except Exception:
            return VolatilityEngine.calculate_realized_vol(prices)

    @staticmethod
    def get_volatility_regime(vol: float) -> str:
        """Classify volatility regime"""
        if vol < 0.01:
            return "very_low"
        if vol < 0.02:
            return "low"
        if vol < 0.04:
            return "moderate"
        if vol < 0.08:
            return "high"
        return "extreme"


class KellyFraction:
    """Kelly Criterion for optimal position sizing"""

    @staticmethod
    def calculate_kelly_full(win_rate: float, avg_win: float, avg_loss: float) -> float:
        """Full Kelly formula: f* = (bp - q) / b"""
        try:
            if avg_loss <= 0 or win_rate <= 0 or win_rate >= 1:
                return 0.0
            loss_rate = 1 - win_rate
            payoff_ratio = avg_win / avg_loss
            kelly = (payoff_ratio * win_rate - loss_rate) / payoff_ratio
            return max(0.0, min(kelly, 0.25))
        except Exception:
            return 0.0

    @staticmethod
    def calculate_kelly_fractional(full_kelly: float, fraction: float = 0.25) -> float:
        """Fractional Kelly = f* * fraction (default 1/4 Kelly)"""
        return full_kelly * fraction

    @staticmethod
    def estimate_ruin_probability(
        kelly_fraction: float,
        num_trades: int,
        win_rate: float,
    ) -> float:
        """Estimate probability of ruin over N trades"""
        try:
            if kelly_fraction <= 0 or win_rate <= 0:
                return 0.0
            loss_rate = 1 - win_rate
            if loss_rate == 0:
                return 0.0
            ratio = loss_rate / win_rate
            exponent = kelly_fraction * num_trades
            prob = ratio ** exponent
            return min(prob, 1.0)
        except Exception:
            return 0.0


class PositionSizer:
    """Unified position sizing engine"""

    @staticmethod
    def calculate_position_size(
        account_size: float,
        entry_price: float,
        stop_loss_price: float,
        win_rate: float,
        avg_win: float,
        avg_loss: float,
        current_vol: float,
        max_risk_per_trade: float = 0.02,
        kelly_fraction: float = 0.25,
    ) -> Dict:
        """Calculate position size using Kelly + volatility"""
        try:
            full_kelly = KellyFraction.calculate_kelly_full(
                win_rate=win_rate,
                avg_win=avg_win,
                avg_loss=avg_loss,
            )
            fractional_kelly = KellyFraction.calculate_kelly_fractional(
                full_kelly=full_kelly,
                fraction=kelly_fraction,
            )

            vol_regime = VolatilityEngine.get_volatility_regime(current_vol)

            risk_amount = account_size * max_risk_per_trade
            price_distance = abs(entry_price - stop_loss_price)

            if price_distance > 0:
                risk_based_size = risk_amount / price_distance
            else:
                risk_based_size = account_size * 0.01

            position_size = min(account_size * fractional_kelly, risk_based_size)
            actual_risk = (
                (position_size * price_distance) / account_size
                if account_size > 0
                else 0
            )

            ruin_prob = KellyFraction.estimate_ruin_probability(
                kelly_fraction=fractional_kelly,
                num_trades=100,
                win_rate=win_rate,
            )

            return {
                "position_size": max(0, position_size),
                "position_pct": position_size / account_size if account_size > 0 else 0,
                "risk_pct": actual_risk,
                "kelly_fraction": fractional_kelly,
                "full_kelly": full_kelly,
                "vol_regime": vol_regime,
                "vol_current": current_vol,
                "ruin_prob_100_trades": ruin_prob,
                "kelly_win_rate": win_rate,
                "kelly_payoff_ratio": avg_win / avg_loss if avg_loss > 0 else 0,
            }
        except Exception as e:
            print(f"Error in position sizing: {e}")
            return {
                "position_size": 0,
                "position_pct": 0,
                "risk_pct": 0,
                "kelly_fraction": 0,
                "full_kelly": 0,
                "vol_regime": "unknown",
                "vol_current": 0,
                "ruin_prob_100_trades": 0,
                "kelly_win_rate": 0,
                "kelly_payoff_ratio": 0,
            }
