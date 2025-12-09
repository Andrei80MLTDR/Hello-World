"""Advanced Statistical Engine for DD Reduction and Risk Management"""
import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from scipy import stats
import logging

logger = logging.getLogger(__name__)


@dataclass
class StatisticalMetrics:
    """Container for advanced statistical analysis results"""
    kelly_fraction: float
    kelly_position_size: float
    bayesian_probability: float
    lln_confidence: float
    clt_normality_pvalue: float
    adjusted_sharpe_ratio: float
    risk_adjusted_dd: float


class AdvancedStatisticalEngine:
    """Advanced Statistical Engine for Portfolio Optimization"""

    def __init__(self, 
                 initial_capital: float = 10000.0,
                 risk_free_rate: float = 0.02,
                 min_trades_for_lln: int = 30):
        self.initial_capital = initial_capital
        self.risk_free_rate = risk_free_rate
        self.min_trades_for_lln = min_trades_for_lln

    def calculate_kelly_criterion(
        self,
        win_rate: float,
        avg_win: float,
        avg_loss: float,
        total_trades: int
    ) -> Dict[str, float]:
        """
        Calculate Kelly Criterion for optimal position sizing.
        
        Kelly % = (W * B - L) / B
        where:
        - W = win probability
        - B = ratio of avg_win to avg_loss
        - L = loss probability
        
        Args:
            win_rate: Proportion of winning trades (0-1)
            avg_win: Average profit per winning trade
            avg_loss: Average loss per losing trade (positive value)
            total_trades: Total number of trades for confidence adjustment
            
        Returns:
            Dict with kelly_fraction, adjusted_kelly, and position_size
        """
        if avg_loss <= 0 or total_trades < 5:
            return {
                'kelly_fraction': 0.02,  # Conservative default
                'adjusted_kelly': 0.01,  # Half Kelly
                'position_size': self.initial_capital * 0.01
            }

        b_ratio = avg_win / avg_loss if avg_loss > 0 else 1.0
        w = win_rate
        l = 1 - win_rate

        # Standard Kelly Formula
        kelly_raw = (w * b_ratio - l) / b_ratio if b_ratio > 0 else 0

        # Ensure Kelly is reasonable
        kelly_fraction = max(0.001, min(kelly_raw, 0.25))  # Cap at 25%

        # Trade confidence multiplier: more trades = higher confidence
        trade_confidence = min(1.0, total_trades / 100)
        adjusted_kelly = kelly_fraction * trade_confidence * 0.5  # Half Kelly for safety

        position_size = self.initial_capital * adjusted_kelly

        return {
            'kelly_fraction': kelly_fraction,
            'adjusted_kelly': adjusted_kelly,
            'position_size': position_size,
            'trade_confidence': trade_confidence
        }

    def bayesian_signal_update(
        self,
        prior_probability: float,
        signal_accuracy: float,
        signal_fired: bool,
        historical_signal_bias: float = 0.5
    ) -> float:
        """
        Bayesian update for signal confidence using likelihood ratios.
        
        Posterior = (Likelihood * Prior) / Evidence
        
        Args:
            prior_probability: Prior belief in signal (0-1)
            signal_accuracy: Known accuracy of the signal (0-1)
            signal_fired: Whether signal triggered
            historical_signal_bias: Historical accuracy of signal when it fires
            
        Returns:
            Updated probability estimate (0-1)
        """
        # Ensure valid inputs
        prior_probability = max(0.01, min(0.99, prior_probability))
        signal_accuracy = max(0.51, min(0.99, signal_accuracy))  # Must be > 50%
        historical_signal_bias = max(0.4, min(0.9, historical_signal_bias))

        if signal_fired:
            # P(Signal=True | State=True)
            likelihood_true = signal_accuracy
            # P(Signal=True | State=False)
            likelihood_false = 1 - signal_accuracy
        else:
            likelihood_true = 1 - signal_accuracy
            likelihood_false = signal_accuracy

        # Bayes rule: P(State | Signal)
        numerator = likelihood_true * prior_probability
        denominator = (
            likelihood_true * prior_probability +
            likelihood_false * (1 - prior_probability)
        )

        posterior = numerator / denominator if denominator > 0 else prior_probability

        return max(0.01, min(0.99, posterior))

    def law_of_large_numbers_validation(
        self,
        returns: List[float],
        confidence_level: float = 0.95
    ) -> Dict[str, float]:
        """
        Law of Large Numbers (LLN) validation.
        Tests if accumulated returns converge to expected value.
        
        Args:
            returns: List of individual trade returns
            confidence_level: Confidence level for interval (0.90-0.99)
            
        Returns:
            Dict with LLN metrics and convergence status
        """
        returns = np.array(returns)
        n_trades = len(returns)

        if n_trades < self.min_trades_for_lln:
            return {
                'converged': False,
                'confidence': 0.0,
                'mean_estimate': np.mean(returns),
                'cumulative_returns': float(np.sum(returns)),
                'trades_needed': self.min_trades_for_lln - n_trades,
                'current_trades': n_trades
            }

        # Calculate running mean
        cumsum = np.cumsum(returns)
        running_mean = cumsum / np.arange(1, n_trades + 1)

        # Recent mean (last 10% of trades)
        recent_window = max(1, int(n_trades * 0.1))
        recent_mean = np.mean(returns[-recent_window:])
        historical_mean = np.mean(returns[:-recent_window]) if n_trades > recent_window else np.mean(returns)

        # Mean absolute difference from estimate
        variance = np.var(returns)
        std_error = np.sqrt(variance / n_trades)

        # T-test for convergence
        t_stat, p_value = stats.ttest_ind(
            returns[:n_trades//2],
            returns[n_trades//2:]
        ) if n_trades > 10 else (0, 0.5)

        converged = p_value > (1 - confidence_level)

        return {
            'converged': converged,
            'confidence': float(1 - p_value),
            'mean_estimate': float(np.mean(returns)),
            'cumulative_returns': float(np.sum(returns)),
            'std_error': float(std_error),
            'variance': float(variance),
            'recent_mean': float(recent_mean),
            'historical_mean': float(historical_mean),
            'trades_count': n_trades,
            'p_value': float(p_value)
        }

    def central_limit_theorem_analysis(
        self,
        returns: List[float],
        window_size: int = 5
    ) -> Dict[str, float]:
        """
        Central Limit Theorem (CLT) analysis.
        Tests if sample means approach normal distribution.
        
        Args:
            returns: List of individual trade returns
            window_size: Window for aggregating returns
            
        Returns:
            Dict with normality tests and distribution metrics
        """
        returns = np.array(returns)
        n_trades = len(returns)

        if n_trades < window_size * 5:  # Need enough data
            return {
                'normal': False,
                'normality_pvalue': 0.0,
                'skewness': float(stats.skew(returns)),
                'kurtosis': float(stats.kurtosis(returns)),
                'samples': n_trades
            }

        # Create windows of aggregated returns
        n_windows = n_trades // window_size
        windowed_returns = [
            np.sum(returns[i*window_size:(i+1)*window_size])
            for i in range(n_windows)
        ]

        # Shapiro-Wilk test for normality
        if len(windowed_returns) > 3:
            stat, p_value = stats.shapiro(windowed_returns)
        else:
            stat, p_value = 0, 0.5

        # Kolmogorov-Smirnov test
        ks_stat, ks_pvalue = stats.kstest(
            (np.array(windowed_returns) - np.mean(windowed_returns)) / np.std(windowed_returns),
            'norm'
        )

        normal = p_value > 0.05

        return {
            'normal': normal,
            'shapiro_pvalue': float(p_value),
            'ks_pvalue': float(ks_pvalue),
            'skewness': float(stats.skew(windowed_returns)),
            'kurtosis': float(stats.kurtosis(windowed_returns)),
            'window_size': window_size,
            'windows': len(windowed_returns),
            'total_samples': n_trades
        }

    def calculate_adjusted_metrics(
        self,
        trades: List[Dict],
        win_rate: float,
        avg_win: float,
        avg_loss: float,
        sharpe_ratio: float,
        max_drawdown: float
    ) -> StatisticalMetrics:
        """
        Calculate comprehensive statistical metrics for DD reduction.
        
        Args:
            trades: List of trade dictionaries
            win_rate: Proportion of winning trades
            avg_win: Average winning trade
            avg_loss: Average losing trade
            sharpe_ratio: Original Sharpe ratio
            max_drawdown: Original maximum drawdown
            
        Returns:
            StatisticalMetrics object with all calculations
        """
        returns = [t.get('profit_loss', 0) for t in trades]
        total_trades = len(trades)

        # Kelly Criterion
        kelly_result = self.calculate_kelly_criterion(
            win_rate, avg_win, avg_loss, total_trades
        )
        kelly_position = kelly_result['adjusted_kelly']

        # Bayesian Update
        prior_prob = win_rate
        signal_accuracy = min(0.99, win_rate + 0.1)  # Conservative estimate
        bayesian_prob = self.bayesian_signal_update(
            prior_prob, signal_accuracy, True
        )

        # LLN Validation
        lln_result = self.law_of_large_numbers_validation(returns)
        lln_confidence = lln_result.get('confidence', 0.0)

        # CLT Analysis
        clt_result = self.central_limit_theorem_analysis(returns)
        clt_pvalue = clt_result.get('shapiro_pvalue', 0.0)

        # Risk Adjustments
        # DD reduction formula: estimated_dd = max_dd * (1 - kelly_position_size)
        risk_adjusted_dd = max_drawdown * (1 - kelly_position)
        adjusted_sharpe = sharpe_ratio * (1 + kelly_position)

        return StatisticalMetrics(
            kelly_fraction=kelly_result['adjusted_kelly'],
            kelly_position_size=kelly_result['position_size'],
            bayesian_probability=bayesian_prob,
            lln_confidence=lln_confidence,
            clt_normality_pvalue=clt_pvalue,
            adjusted_sharpe_ratio=adjusted_sharpe,
            risk_adjusted_dd=risk_adjusted_dd
        )
