import random
import numpy as np
from typing import Dict, List

class MonteCarloBacktest:
    """
    Monte Carlo simulation backtest for 50/50 trading game.
    - Risk: $100 per trade (loss)
    - Reward: $300 per trade (win)
    - 1:3 Risk/Reward Ratio
    """
    
    def __init__(self, initial_capital: float = 10000, risk_per_trade: float = 100,
                 reward_per_trade: float = 300, win_probability: float = 0.5,
                 num_simulations: int = 1000):
        self.initial_capital = initial_capital
        self.risk_per_trade = risk_per_trade
        self.reward_per_trade = reward_per_trade
        self.win_probability = win_probability
        self.num_simulations = num_simulations
        self.results = []
    
    def run_single_simulation(self) -> Dict:
        """Run a single Monte Carlo simulation with 50/50 coin flip"""
        capital = self.initial_capital
        trades = []
        equity_curve = [capital]
        wins = 0
        losses = 0
        max_trades = 100
        
        for trade_num in range(max_trades):
            if capital <= 0:
                break
            
            trade_result = random.random() < self.win_probability
            
            if trade_result:
                capital += self.reward_per_trade
                wins += 1
            else:
                capital -= self.risk_per_trade
                losses += 1
            
            equity_curve.append(capital)
            trades.append({
                "trade_num": trade_num + 1,
                "result": "WIN" if trade_result else "LOSS",
                "pnl": self.reward_per_trade if trade_result else -self.risk_per_trade,
                "capital": capital
            })
        
        total_trades = wins + losses
        final_pnl = capital - self.initial_capital
        total_return = (final_pnl / self.initial_capital) * 100 if self.initial_capital > 0 else 0
        win_rate = (wins / total_trades * 100) if total_trades > 0 else 0
        max_capital = max(equity_curve)
        min_capital = min(equity_curve)
        max_drawdown = min_capital - self.initial_capital
        
        return {
            "final_capital": capital,
            "final_pnl": final_pnl,
            "total_return_pct": total_return,
            "trades": trades,
            "wins": wins,
            "losses": losses,
            "total_trades": total_trades,
            "win_rate": win_rate,
            "equity_curve": equity_curve,
            "max_capital": max_capital,
            "min_capital": min_capital,
            "max_drawdown": max_drawdown,
            "account_survived": capital > 0
        }
    
    def run_monte_carlo_analysis(self) -> Dict:
        """Run multiple Monte Carlo simulations and analyze results"""
        self.results = []
        
        for _ in range(self.num_simulations):
            result = self.run_single_simulation()
            self.results.append(result)
        
        final_capitals = [r["final_capital"] for r in self.results]
        final_pnls = [r["final_pnl"] for r in self.results]
        total_returns = [r["total_return_pct"] for r in self.results]
        win_rates = [r["win_rate"] for r in self.results]
        max_drawdowns = [r["max_drawdown"] for r in self.results]
        survived = sum(1 for r in self.results if r["account_survived"])
        
        analysis = {
            "num_simulations": self.num_simulations,
            "initial_capital": self.initial_capital,
            "risk_per_trade": self.risk_per_trade,
            "reward_per_trade": self.reward_per_trade,
            "expected_ratio": f"{self.reward_per_trade}:{self.risk_per_trade}",
            "final_capital": {
                "mean": round(np.mean(final_capitals), 2),
                "median": round(np.median(final_capitals), 2),
                "std_dev": round(np.std(final_capitals), 2),
                "min": round(np.min(final_capitals), 2),
                "max": round(np.max(final_capitals), 2),
                "p5": round(np.percentile(final_capitals, 5), 2),
                "p25": round(np.percentile(final_capitals, 25), 2),
                "p75": round(np.percentile(final_capitals, 75), 2),
                "p95": round(np.percentile(final_capitals, 95), 2),
            },
            "final_pnl": {
                "mean": round(np.mean(final_pnls), 2),
                "median": round(np.median(final_pnls), 2),
                "std_dev": round(np.std(final_pnls), 2),
                "min": round(np.min(final_pnls), 2),
                "max": round(np.max(final_pnls), 2),
            },
            "total_return_pct": {
                "mean": round(np.mean(total_returns), 2),
                "median": round(np.median(total_returns), 2),
                "std_dev": round(np.std(total_returns), 2),
                "min": round(np.min(total_returns), 2),
                "max": round(np.max(total_returns), 2),
            },
            "win_rate": {
                "mean": round(np.mean(win_rates), 2),
                "median": round(np.median(win_rates), 2),
                "std_dev": round(np.std(win_rates), 2),
            },
            "max_drawdown": {
                "mean": round(np.mean(max_drawdowns), 2),
                "median": round(np.median(max_drawdowns), 2),
                "min": round(np.min(max_drawdowns), 2),
                "max": round(np.max(max_drawdowns), 2),
            },
            "survival_rate_pct": round((survived / self.num_simulations) * 100, 2),
            "accounts_survived": survived,
            "accounts_blown_up": self.num_simulations - survived,
            "probability_of_profit": round((sum(1 for p in final_pnls if p > 0) / len(final_pnls)) * 100, 2),
        }
        
        return analysis


def monte_carlo_backtest_btc(num_simulations: int = 1000, initial_capital: float = 10000) -> Dict:
    """Run Monte Carlo backtest. Simulates 50/50 trading with 1:3 R/R ratio"""
    backtest = MonteCarloBacktest(
        initial_capital=initial_capital,
        risk_per_trade=100,
        reward_per_trade=300,
        win_probability=0.5,
        num_simulations=num_simulations
    )
    
    analysis = backtest.run_monte_carlo_analysis()
    
    return {
        "status": "success",
        "backtest_type": "Monte Carlo Simulation - 50/50 Trading Game",
        "analysis": analysis,
        "interpretation": {
            "message": "Based on 50/50 coin flip trading with 1:3 R/R ratio",
            "expected_profit_per_trade": 100,
            "note": "With 1:3 RR and 50% win rate, expected value is +$100 per trade"
        }
    }
