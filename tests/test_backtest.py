"""
Tests for backtesting framework.
"""

import pytest
from datetime import datetime, timedelta, timezone

from pantheon.backtest.engine import BacktestEngine, BacktestResult, Trade


class TestBacktestEngine:
    """Test backtest engine functionality."""
    
    def test_initialization(self):
        """Test engine initializes correctly."""
        engine = BacktestEngine(initial_capital=100000)
        assert engine.initial_capital == 100000
        assert engine.capital == 100000
        assert len(engine.trades) == 0
    
    def test_empty_backtest(self):
        """Test backtest with no signals."""
        engine = BacktestEngine()
        result = engine.run(days=30)
        
        assert isinstance(result, BacktestResult)
        assert result.total_trades == 0
        assert result.sharpe_ratio == 0.0
    
    def test_backtest_result_metrics(self):
        """Test backtest result calculation."""
        # Create mock trades
        trades = [
            Trade(
                symbol='TEST1',
                direction='BUY',
                entry_price=100,
                entry_date=datetime.now(timezone.utc) - timedelta(days=10),
                exit_price=105,
                exit_date=datetime.now(timezone.utc),
                pnl_pct=5.0,
                pnl_absolute=500,
                signal_score=0.5,
                risk_level=2,
            ),
            Trade(
                symbol='TEST2',
                direction='BUY',
                entry_price=200,
                entry_date=datetime.now(timezone.utc) - timedelta(days=8),
                exit_price=190,
                exit_date=datetime.now(timezone.utc),
                pnl_pct=-5.0,
                pnl_absolute=-500,
                signal_score=0.4,
                risk_level=3,
            ),
        ]
        
        engine = BacktestEngine()
        engine.trades = trades
        engine.capital = 100000  # No change
        
        result = engine._calculate_metrics()
        
        assert result.total_trades == 2
        assert result.winning_trades == 1
        assert result.losing_trades == 1
        assert result.win_rate == 0.5
        assert result.avg_win_pct == 5.0
        assert result.avg_loss_pct == -5.0
    
    def test_max_drawdown_calculation(self):
        """Test maximum drawdown calculation."""
        engine = BacktestEngine()
        
        # Create equity curve with drawdown
        engine.equity_curve = [
            {'date': datetime.now(timezone.utc) - timedelta(days=3), 'equity': 100000},
            {'date': datetime.now(timezone.utc) - timedelta(days=2), 'equity': 110000},  # Peak
            {'date': datetime.now(timezone.utc) - timedelta(days=1), 'equity': 95000},   # Drawdown
            {'date': datetime.now(timezone.utc), 'equity': 105000},
        ]
        
        max_dd = engine._calculate_max_drawdown()
        
        # Drawdown from 110k to 95k = 13.6%
        assert 13.0 <= max_dd <= 14.0
    
    def test_backtest_result_to_dict(self):
        """Test result serialization."""
        result = BacktestResult(
            total_return=15.5,
            sharpe_ratio=1.8,
            max_drawdown=-12.3,
            win_rate=0.58,
            profit_factor=2.1,
            total_trades=50,
        )
        
        result_dict = result.to_dict()
        
        assert isinstance(result_dict, dict)
        assert 'total_return' in result_dict
        assert 'sharpe_ratio' in result_dict
        assert result_dict['total_return'] == 15.5
        assert result_dict['sharpe_ratio'] == 1.8


class TestTrade:
    """Test Trade dataclass."""
    
    def test_trade_creation(self):
        """Test trade object creation."""
        trade = Trade(
            symbol='RELIANCE',
            direction='BUY',
            entry_price=1348.10,
            entry_date=datetime.now(timezone.utc),
            exit_price=1375.00,
            exit_date=datetime.now(timezone.utc) + timedelta(days=5),
            pnl_pct=2.0,
            pnl_absolute=2690,
            signal_score=0.5,
            risk_level=2,
        )
        
        assert trade.symbol == 'RELIANCE'
        assert trade.direction == 'BUY'
        assert trade.pnl_pct == 2.0
        assert trade.pnl_absolute == 2690


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
