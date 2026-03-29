"""
Backtesting module for Project Pantheon MMCI strategy validation.

Provides historical signal replay, P&L calculation, and performance metrics.
"""

from pantheon.backtest.engine import BacktestEngine, BacktestResult, Trade

__all__ = ['BacktestEngine', 'BacktestResult', 'Trade']
