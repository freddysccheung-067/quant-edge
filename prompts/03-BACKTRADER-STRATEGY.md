# ONE-SHOT PROMPT: Backtrader Strategy Implementation

## Objective
Build a production-ready Backtrader strategy that implements the Magic Formula with proper rebalancing, commission modeling, position sizing, and performance tracking.

## Technical Specifications

**File**: `D:\quant-edge\strategies\magic_formula.py`

**Dependencies**: 
```
backtrader>=1.9.78
pandas>=2.1.0
numpy>=1.24.0
```

**Python**: 3.11+ with type hints

## Backtrader Concepts (Quick Primer)

Backtrader is an event-driven backtesting framework:
- **Cerebro**: Main engine that runs the backtest
- **Strategy**: Your trading logic (when to buy/sell)
- **Data Feeds**: Price data fed into the strategy
- **Broker**: Simulates order execution and tracks portfolio

**Key Methods**:
- `__init__()`: Initialize indicators, variables
- `next()`: Called every trading day with current bar
- `notify_order()`: Called when order is filled/cancelled
- `notify_trade()`: Called when position is closed
- `stop()`: Called at end of backtest

## Strategy Implementation

### Main Strategy Class

```python
import backtrader as bt
import pandas as pd
from datetime import datetime, timedelta

class MagicFormulaStrategy(bt.Strategy):
    """
    Magic Formula momentum strategy with monthly rebalancing.
    
    Strategy Logic:
    1. Every rebalance_days (default 30), calculate Magic Formula ranks
    2. Close all existing positions
    3. Open new positions in top N stocks
    4. Equal-weight all positions (1/N of portfolio each)
    5. Hold until next rebalance
    
    Parameters:
    - top_n: Number of stocks to hold (default 15)
    - rebalance_days: Days between rebalances (default 30)
    - commission: Commission per trade as fraction (default 0.001 = 0.1%)
    """
    
    params = (
        ('top_n', 15),
        ('rebalance_days', 30),
        ('fundamental_data', None),  # Pass scored DataFrame here
        ('verbose', True),
    )
    
    def __init__(self):
        """Initialize strategy state"""
        # Track rebalancing
        self.rebalance_date = None
        self.days_since_rebalance = 0
        
        # Track orders
        self.order_dict = {}  # {data: order}
        
        # Performance tracking
        self.trade_log = []
        self.portfolio_values = []
        
        # Pre-process fundamental data
        self.fundamental_scores = self.params.fundamental_data
        if self.fundamental_scores is None:
            raise ValueError("Must provide fundamental_data parameter")
    
    def next(self):
        """Called on every trading day"""
        current_date = self.datas[0].datetime.date(0)
        
        # Track portfolio value
        self.portfolio_values.append({
            'date': current_date,
            'value': self.broker.getvalue(),
            'cash': self.broker.getcash()
        })
        
        # Check if rebalance day
        if self.should_rebalance(current_date):
            if self.params.verbose:
                print(f"\n{'='*60}")
                print(f"REBALANCE: {current_date}")
                print(f"Portfolio Value: ${self.broker.getvalue():,.2f}")
                print(f"{'='*60}")
            
            self.rebalance_portfolio(current_date)
            self.rebalance_date = current_date
    
    def should_rebalance(self, current_date) -> bool:
        """Determine if today is a rebalance day"""
        if self.rebalance_date is None:
            return True  # First day
        
        days_elapsed = (current_date - self.rebalance_date).days
        return days_elapsed >= self.params.rebalance_days
    
    def rebalance_portfolio(self, current_date):
        """
        Rebalance: close all positions, open new ones in top-ranked stocks.
        """
        # 1. Close all existing positions
        for data in self.datas:
            position_size = self.getposition(data).size
            if position_size != 0:
                self.close(data=data)
                if self.params.verbose:
                    print(f"  CLOSE: {data._name}, Size: {position_size}")
        
        # 2. Get top N stocks by Magic Formula rank
        top_stocks = self.get_top_stocks(current_date, self.params.top_n)
        
        if len(top_stocks) == 0:
            print(f"  WARNING: No valid stocks found for {current_date}")
            return
        
        # 3. Calculate position sizes (equal weight)
        portfolio_value = self.broker.getvalue()
        target_position_value = portfolio_value / len(top_stocks)
        
        # 4. Open new positions
        for ticker in top_stocks:
            data = self.get_data_by_name(ticker)
            if data is None:
                continue
            
            current_price = data.close[0]
            shares = int(target_position_value / current_price)
            
            if shares > 0:
                self.buy(data=data, size=shares)
                if self.params.verbose:
                    print(f"  BUY: {ticker}, Shares: {shares}, "
                          f"Price: ${current_price:.2f}, "
                          f"Value: ${shares * current_price:,.2f}")
    
    def get_top_stocks(self, current_date, n: int) -> list[str]:
        """
        Get top N stocks by Magic Formula rank.
        
        In reality, you'd filter by current_date if fundamental data changes.
        For simplicity, use static ranking from initialization.
        """
        # Filter for stocks that exist in data feeds
        available_tickers = {data._name for data in self.datas}
        
        # Get top N from fundamental scores
        top_stocks = []
        for ticker in self.fundamental_scores.index:
            if ticker in available_tickers:
                top_stocks.append(ticker)
            if len(top_stocks) >= n:
                break
        
        return top_stocks
    
    def get_data_by_name(self, ticker: str):
        """Find data feed by ticker name"""
        for data in self.datas:
            if data._name == ticker:
                return data
        return None
    
    def notify_order(self, order):
        """Called when order is submitted/executed/cancelled"""
        if order.status in [order.Completed]:
            if order.isbuy():
                msg = f"BUY EXECUTED: {order.data._name}, Price: ${order.executed.price:.2f}, Size: {order.executed.size}"
            elif order.issell():
                msg = f"SELL EXECUTED: {order.data._name}, Price: ${order.executed.price:.2f}, Size: {order.executed.size}"
            
            if self.params.verbose:
                print(f"    {msg}")
    
    def notify_trade(self, trade):
        """Called when a position is closed (profit realized)"""
        if trade.isclosed:
            self.trade_log.append({
                'ticker': trade.data._name,
                'profit': trade.pnl,
                'pnl_pct': trade.pnl / trade.value if trade.value != 0 else 0,
            })
            
            if self.params.verbose:
                print(f"    TRADE CLOSED: {trade.data._name}, "
                      f"P&L: ${trade.pnl:.2f} ({trade.pnl/trade.value*100:.2f}%)")
    
    def stop(self):
        """Called at end of backtest"""
        final_value = self.broker.getvalue()
        print(f"\n{'='*60}")
        print(f"BACKTEST COMPLETE")
        print(f"Final Portfolio Value: ${final_value:,.2f}")
        print(f"Total Return: {(final_value/self.broker.startingcash - 1)*100:.2f}%")
        print(f"{'='*60}")
```

## Backtest Engine Setup

**File**: `D:\quant-edge\backtesting\backtrader_engine.py`

```python
import backtrader as bt
import pandas as pd
from pathlib import Path
from datetime import datetime

class BacktestEngine:
    """
    Wrapper for Backtrader that simplifies setup and execution.
    """
    
    def __init__(
        self,
        initial_cash: float = 25000,
        commission: float = 0.001,  # 0.1%
        slippage: float = 0.0005,   # 0.05%
    ):
        self.cerebro = bt.Cerebro()
        self.cerebro.broker.setcash(initial_cash)
        self.cerebro.broker.setcommission(commission=commission)
        
        # Add slippage (optional)
        # self.cerebro.broker.set_slippage_perc(slippage)
        
        # Add analyzers
        self.cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe')
        self.cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
        self.cerebro.addanalyzer(bt.analyzers.Returns, _name='returns')
        self.cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trades')
    
    def add_data(
        self,
        prices: pd.DataFrame,
        tickers: list[str] | None = None
    ):
        """
        Add price data for multiple stocks.
        
        Args:
            prices: DataFrame with DatetimeIndex, columns = tickers
            tickers: Subset of tickers to use (if None, use all)
        """
        if tickers is None:
            tickers = prices.columns.tolist()
        
        for ticker in tickers:
            if ticker not in prices.columns:
                print(f"Warning: {ticker} not in price data")
                continue
            
            # Create DataFrame with required columns for Backtrader
            data_df = pd.DataFrame({
                'open': prices[ticker],
                'high': prices[ticker],
                'low': prices[ticker],
                'close': prices[ticker],
                'volume': 0,  # Not used
            }).dropna()
            
            # Convert to Backtrader data feed
            data_feed = bt.feeds.PandasData(
                dataname=data_df,
                name=ticker,
                fromdate=data_df.index.min(),
                todate=data_df.index.max()
            )
            
            self.cerebro.adddata(data_feed)
        
        print(f"Added {len(tickers)} data feeds to backtest")
    
    def run(self, strategy_class, strategy_params: dict):
        """
        Run backtest with given strategy.
        
        Args:
            strategy_class: Backtrader Strategy class (not instance)
            strategy_params: Dict of strategy parameters
        
        Returns:
            results: Strategy instance(s) after run
        """
        self.cerebro.addstrategy(strategy_class, **strategy_params)
        
        print(f"Starting Portfolio Value: ${self.cerebro.broker.getvalue():,.2f}")
        results = self.cerebro.run()
        print(f"Ending Portfolio Value: ${self.cerebro.broker.getvalue():,.2f}")
        
        return results[0]  # Return first (only) strategy
    
    def get_performance_metrics(self, strategy) -> dict:
        """Extract performance metrics from analyzers"""
        sharpe = strategy.analyzers.sharpe.get_analysis()
        drawdown = strategy.analyzers.drawdown.get_analysis()
        returns = strategy.analyzers.returns.get_analysis()
        trades = strategy.analyzers.trades.get_analysis()
        
        return {
            'sharpe_ratio': sharpe.get('sharperatio', None),
            'max_drawdown': drawdown.get('max', {}).get('drawdown', None),
            'total_return': returns.get('rtot', None),
            'avg_return': returns.get('ravg', None),
            'total_trades': trades.get('total', {}).get('total', 0),
            'won_trades': trades.get('won', {}).get('total', 0),
            'lost_trades': trades.get('lost', {}).get('total', 0),
        }
    
    def plot(self, **kwargs):
        """Plot backtest results"""
        self.cerebro.plot(**kwargs)
```

## Usage Example

**File**: `D:\quant-edge\run_backtest.py`

```python
from data.fetchers import DataFetcher
from factors.composite import magic_formula_score
from strategies.magic_formula import MagicFormulaStrategy
from backtesting.backtrader_engine import BacktestEngine

# 1. Fetch data
print("Fetching data...")
fetcher = DataFetcher()
prices = fetcher.get_price_data('2019-01-01', '2024-10-01')
fundamentals = fetcher.get_fundamental_data()

# 2. Calculate Magic Formula scores
print("Calculating scores...")
scored = magic_formula_score(fundamentals)

# 3. Get top 50 stocks for backtesting (more than we'll hold, for survivorship)
top_50_tickers = scored.head(50).index.tolist()

# 4. Setup backtest
print("Setting up backtest...")
engine = BacktestEngine(initial_cash=25000, commission=0.001)
engine.add_data(prices, tickers=top_50_tickers)

# 5. Run backtest
print("Running backtest...")
strategy_params = {
    'top_n': 15,
    'rebalance_days': 30,
    'fundamental_data': scored,
    'verbose': False,  # Set True for detailed logs
}

strategy = engine.run(MagicFormulaStrategy, strategy_params)

# 6. Get results
metrics = engine.get_performance_metrics(strategy)
print("\n" + "="*60)
print("PERFORMANCE METRICS")
print("="*60)
for key, value in metrics.items():
    print(f"{key:20s}: {value}")

# 7. Plot (optional)
# engine.plot()
```

## Deliverables

1. **`magic_formula.py`**: Strategy class (~300 lines)
2. **`backtrader_engine.py`**: Engine wrapper (~200 lines)
3. **`run_backtest.py`**: Example script (~50 lines)
4. **`__init__.py`**: Exports

## Success Criteria

- [ ] Backtest runs without errors for 5-year period
- [ ] Rebalancing occurs exactly every 30 days
- [ ] 15 positions held at each rebalance
- [ ] Commission of 0.1% applied to all trades
- [ ] Sharpe ratio > 0.8, max drawdown < 25%
- [ ] Portfolio value matches manual calculation
- [ ] Trade log shows all entries/exits
- [ ] Can plot equity curve

## Time Estimate
**3-4 hours** for someone familiar with Backtrader

---

**GO BUILD IT.** This proves whether the strategy actually works.
