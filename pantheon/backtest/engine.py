"""
Backtesting Framework for Project Pantheon MMCI Strategy

Enables historical validation of MMCI signals with realistic P&L calculations,
risk metrics, and performance analysis.

Usage:
    python -m pantheon.backtest.engine --days 90 --initial-capital 100000
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from datetime import datetime, timedelta, timezone
from typing import Optional
from dataclasses import dataclass, field
import statistics
from loguru import logger

from pantheon.db.session import SessionLocal
from pantheon.db.models import SignalRecord, PaperTrade


@dataclass
class Trade:
    """Represents a single backtested trade."""
    symbol: str
    direction: str
    entry_price: float
    entry_date: datetime
    exit_price: float
    exit_date: datetime
    pnl_pct: float
    pnl_absolute: float
    signal_score: float
    risk_level: int


@dataclass
class BacktestResult:
    """Comprehensive backtest results."""
    total_return: float = 0.0
    sharpe_ratio: float = 0.0
    max_drawdown: float = 0.0
    win_rate: float = 0.0
    profit_factor: float = 0.0
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    avg_win_pct: float = 0.0
    avg_loss_pct: float = 0.0
    avg_holding_period: float = 0.0  # days
    trades: list = field(default_factory=list)
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            'total_return': round(self.total_return, 2),
            'sharpe_ratio': round(self.sharpe_ratio, 2),
            'max_drawdown': round(self.max_drawdown, 2),
            'win_rate': round(self.win_rate, 2),
            'profit_factor': round(self.profit_factor, 2),
            'total_trades': self.total_trades,
            'winning_trades': self.winning_trades,
            'losing_trades': self.losing_trades,
            'avg_win_pct': round(self.avg_win_pct, 2),
            'avg_loss_pct': round(self.avg_loss_pct, 2),
            'avg_holding_period': round(self.avg_holding_period, 1),
        }


class BacktestEngine:
    """
    Backtesting engine for MMCI strategy validation.
    
    Features:
    - Historical signal replay from database
    - Realistic P&L calculation (including direction)
    - Risk metrics (Sharpe, drawdown, win rate)
    - Trade-by-trade analysis
    """
    
    def __init__(self, initial_capital: float = 100000):
        """
        Initialize backtest engine.
        
        Args:
            initial_capital: Starting capital (default: ₹100,000)
        """
        self.initial_capital = initial_capital
        self.capital = initial_capital
        self.positions = {}  # symbol -> position
        self.trades = []
        self.equity_curve = []
    
    def run(
        self,
        days: int = 90,
        symbol: Optional[str] = None,
        min_score: float = 0.3,
        max_position_size: float = 0.20,
    ) -> BacktestResult:
        """
        Run backtest on historical signals.
        
        Args:
            days: Number of days to backtest (default: 90)
            symbol: Filter by specific symbol (None = all)
            min_score: Minimum MMCI score to trade (default: 0.3)
            max_position_size: Max position as % of capital (default: 20%)
        
        Returns:
            BacktestResult with comprehensive metrics
        """
        logger.info(f"Starting backtest: {days} days, min_score={min_score}")
        
        # Fetch historical signals
        db = SessionLocal()
        try:
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
            
            query = db.query(SignalRecord).filter(
                SignalRecord.timestamp >= cutoff_date,
                SignalRecord.consensus_score >= min_score,
                SignalRecord.direction != "HOLD",
            )
            
            if symbol:
                query = query.filter(SignalRecord.symbol == symbol)
            
            signals = query.order_by(SignalRecord.timestamp).all()
            logger.info(f"Found {len(signals)} signals to backtest")
            
            if not signals:
                logger.warning("No signals found for backtest period")
                return BacktestResult()
            
            # Replay signals
            self._replay_signals(signals, max_position_size)
            
            # Calculate metrics
            result = self._calculate_metrics()
            
            return result
            
        finally:
            db.close()
    
    def _replay_signals(self, signals: list, max_position_size: float):
        """Replay historical signals and simulate trades."""
        for signal in signals:
            symbol = signal.symbol
            direction = signal.direction
            score = signal.consensus_score
            risk_level = signal.risk_level
            entry_price = signal.entry_price
            
            if not entry_price:
                continue
            
            # Calculate position size
            position_value = self.capital * max_position_size
            position_size = position_value / entry_price
            
            # Check if we already have a position
            if symbol in self.positions:
                continue  # Skip if already positioned
            
            # Open position
            self.positions[symbol] = {
                'direction': direction,
                'entry_price': entry_price,
                'entry_date': signal.timestamp,
                'position_size': position_size,
                'score': score,
                'risk_level': risk_level,
            }
            
            self.equity_curve.append({
                'date': signal.timestamp,
                'equity': self.capital,
                'type': 'ENTRY',
                'symbol': symbol,
            })
        
        # For backtest, we'll use outcome data if available
        self._close_positions_with_outcomes()
    
    def _close_positions_with_outcomes(self):
        """Close positions using actual outcome data from database."""
        db = SessionLocal()
        try:
            for symbol, position in list(self.positions.items()):
                # Find the signal record with outcome
                signal_record = db.query(SignalRecord).filter(
                    SignalRecord.symbol == symbol,
                    SignalRecord.timestamp == position['entry_date'],
                    SignalRecord.outcome != None,
                ).first()
                
                if signal_record and signal_record.outcome_date:
                    # Calculate exit price based on outcome
                    entry_price = position['entry_price']
                    direction = position['direction']
                    
                    if signal_record.outcome == "BUY":
                        # Price went up 2%+
                        exit_price = entry_price * 1.02
                    elif signal_record.outcome == "SELL":
                        # Price went down 2%+
                        exit_price = entry_price * 0.98
                    else:  # HOLD
                        # Price stayed within ±2%
                        exit_price = entry_price
                    
                    # For SELL positions, invert P&L
                    if direction == "SELL":
                        pnl_pct = (entry_price - exit_price) / entry_price * 100
                    else:
                        pnl_pct = (exit_price - entry_price) / entry_price * 100
                    
                    pnl_absolute = position['position_size'] * (exit_price - entry_price)
                    if direction == "SELL":
                        pnl_absolute = -pnl_absolute
                    
                    # Create trade record
                    trade = Trade(
                        symbol=symbol,
                        direction=direction,
                        entry_price=entry_price,
                        entry_date=position['entry_date'],
                        exit_price=exit_price,
                        exit_date=signal_record.outcome_date,
                        pnl_pct=pnl_pct,
                        pnl_absolute=pnl_absolute,
                        signal_score=position['score'],
                        risk_level=position['risk_level'],
                    )
                    
                    self.trades.append(trade)
                    self.capital += pnl_absolute
                    
                    self.equity_curve.append({
                        'date': signal_record.outcome_date,
                        'equity': self.capital,
                        'type': 'EXIT',
                        'symbol': symbol,
                    })
                    
                    # Remove from open positions
                    del self.positions[symbol]
                    
        finally:
            db.close()
    
    def _calculate_metrics(self) -> BacktestResult:
        """Calculate comprehensive backtest metrics."""
        if not self.trades:
            return BacktestResult()
        
        # Basic counts
        total_trades = len(self.trades)
        winning_trades = [t for t in self.trades if t.pnl_pct > 0]
        losing_trades = [t for t in self.trades if t.pnl_pct < 0]
        
        # Win rate
        win_rate = len(winning_trades) / total_trades if total_trades > 0 else 0
        
        # Average win/loss
        avg_win = statistics.mean([t.pnl_pct for t in winning_trades]) if winning_trades else 0
        avg_loss = statistics.mean([t.pnl_pct for t in losing_trades]) if losing_trades else 0
        
        # Profit factor
        gross_profit = sum([t.pnl_absolute for t in winning_trades])
        gross_loss = abs(sum([t.pnl_absolute for t in losing_trades]))
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
        
        # Total return
        total_return = ((self.capital - self.initial_capital) / self.initial_capital) * 100
        
        # Sharpe ratio (annualized)
        if len(self.trades) >= 2:
            pnl_series = [t.pnl_pct for t in self.trades]
            avg_pnl = statistics.mean(pnl_series)
            std_pnl = statistics.stdev(pnl_series)
            sharpe_ratio = (avg_pnl / std_pnl) * (252 ** 0.5) if std_pnl > 0 else 0
        else:
            sharpe_ratio = 0
        
        # Maximum drawdown
        max_drawdown = self._calculate_max_drawdown()
        
        # Average holding period
        holding_periods = [
            (t.exit_date - t.entry_date).days
            for t in self.trades
            if t.exit_date and t.entry_date
        ]
        avg_holding_period = statistics.mean(holding_periods) if holding_periods else 0
        
        return BacktestResult(
            total_return=total_return,
            sharpe_ratio=sharpe_ratio,
            max_drawdown=max_drawdown,
            win_rate=win_rate,
            profit_factor=profit_factor,
            total_trades=total_trades,
            winning_trades=len(winning_trades),
            losing_trades=len(losing_trades),
            avg_win_pct=avg_win,
            avg_loss_pct=avg_loss,
            avg_holding_period=avg_holding_period,
            trades=self.trades,
        )
    
    def _calculate_max_drawdown(self) -> float:
        """Calculate maximum drawdown from equity curve."""
        if not self.equity_curve:
            return 0.0
        
        equity_values = [point['equity'] for point in self.equity_curve]
        
        peak = equity_values[0]
        max_dd = 0.0
        
        for equity in equity_values:
            if equity > peak:
                peak = equity
            
            drawdown = (peak - equity) / peak * 100
            if drawdown > max_dd:
                max_dd = drawdown
        
        return max_dd
    
    def print_report(self, result: BacktestResult):
        """Print formatted backtest report."""
        print("\n" + "="*80)
        print("BACKTEST RESULTS")
        print("="*80)
        print(f"\nPeriod: {result.total_trades} trades")
        print(f"Initial Capital: ₹{self.initial_capital:,.0f}")
        print(f"Final Capital: ₹{self.capital:,.0f}")
        
        print(f"\n📊 Performance Metrics:")
        print(f"  Total Return:    {result.total_return:+.2f}%")
        print(f"  Sharpe Ratio:    {result.sharpe_ratio:.2f}")
        print(f"  Max Drawdown:    {result.max_drawdown:.2f}%")
        print(f"  Win Rate:        {result.win_rate:.1%}")
        print(f"  Profit Factor:   {result.profit_factor:.2f}")
        
        print(f"\n📈 Trade Statistics:")
        print(f"  Total Trades:    {result.total_trades}")
        print(f"  Winning:         {result.winning_trades}")
        print(f"  Losing:          {result.losing_trades}")
        print(f"  Avg Win:         {result.avg_win_pct:+.2f}%")
        print(f"  Avg Loss:        {result.avg_loss_pct:+.2f}%")
        print(f"  Avg Hold:        {result.avg_holding_period:.1f} days")
        
        print("\n" + "="*80)
        
        # Assessment
        if result.sharpe_ratio >= 1.5 and result.win_rate >= 0.55:
            print("✅ STRATEGY PASSED: Ready for paper trading")
        elif result.sharpe_ratio >= 1.0 and result.win_rate >= 0.50:
            print("⚠️  STRATEGY ACCEPTABLE: Needs more testing")
        else:
            print("❌ STRATEGY FAILED: Requires optimization")
        
        print("="*80 + "\n")


def main():
    """CLI entry point for backtesting."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Backtest MMCI strategy')
    parser.add_argument('--days', type=int, default=90, help='Backtest period in days')
    parser.add_argument('--capital', type=float, default=100000, help='Initial capital')
    parser.add_argument('--min-score', type=float, default=0.3, help='Minimum MMCI score')
    parser.add_argument('--symbol', type=str, default=None, help='Filter by symbol')
    
    args = parser.parse_args()
    
    # Run backtest
    engine = BacktestEngine(initial_capital=args.capital)
    result = engine.run(
        days=args.days,
        symbol=args.symbol,
        min_score=args.min_score,
    )
    
    # Print report
    engine.print_report(result)
    
    # Save results (optional)
    # import json
    # with open('backtest_results.json', 'w') as f:
    #     json.dump(result.to_dict(), f, indent=2)


if __name__ == "__main__":
    main()
