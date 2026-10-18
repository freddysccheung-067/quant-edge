# ONE-SHOT PROMPT: Live Signal Generator & Execution System

## Objective
Build a production CLI tool that generates daily trading signals from the Magic Formula strategy and tracks live portfolio performance.

## Technical Specifications

**Files**:
- `D:\quant-edge\execution\signal_generator.py` (core logic)
- `D:\quant-edge\execution\portfolio_tracker.py` (position tracking)
- `D:\quant-edge\run_signals.py` (CLI entry point)

**Dependencies**: 
```
pandas>=2.1.0
numpy>=1.24.0
pyyaml>=6.0
colorama>=0.4.6  # For colored console output
tabulate>=0.9.0  # For formatted tables
```

## Signal Generator

**File**: `D:\quant-edge\execution\signal_generator.py`

```python
import pandas as pd
import numpy as np
from datetime import datetime, date
from pathlib import Path
from typing import Literal

class SignalGenerator:
    """
    Generate trading signals from Magic Formula scores.
    
    Compares current scores to previous rebalance to determine:
    - BUY: Stock in new top N, not in current holdings
    - SELL: Stock in current holdings, not in new top N
    - HOLD: Stock in both current holdings and new top N
    """
    
    def __init__(
        self,
        config_path: str = "D:/quant-edge/config/config.yaml",
        portfolio_path: str = "D:/quant-edge/data/portfolio.csv"
    ):
        self.config = self.load_config(config_path)
        self.portfolio_path = Path(portfolio_path)
        self.current_holdings = self.load_portfolio()
    
    def load_config(self, path: str) -> dict:
        """Load configuration from YAML"""
        import yaml
        with open(path, 'r') as f:
            return yaml.safe_load(f)
    
    def load_portfolio(self) -> pd.DataFrame:
        """
        Load current portfolio holdings.
        
        Returns DataFrame with columns:
        - ticker: Stock symbol
        - shares: Number of shares held
        - entry_price: Price when bought
        - entry_date: Date purchased
        - current_value: Current position value
        
        If file doesn't exist, return empty DataFrame.
        """
        if self.portfolio_path.exists():
            return pd.read_csv(self.portfolio_path, index_col='ticker')
        else:
            return pd.DataFrame(columns=['ticker', 'shares', 'entry_price', 
                                         'entry_date', 'current_value'])
    
    def generate_signals(
        self,
        scores: pd.DataFrame,
        prices: pd.DataFrame,
        target_date: date | None = None
    ) -> pd.DataFrame:
        """
        Generate trading signals.
        
        Args:
            scores: Magic Formula scores (sorted, best first)
            prices: Current price data (DatetimeIndex x tickers)
            target_date: Date to generate signals for (default today)
        
        Returns:
            DataFrame with columns:
            - ticker
            - action: 'BUY' | 'SELL' | 'HOLD'
            - magic_rank: Current rank
            - current_price: Latest price
            - target_weight: Target portfolio weight (1/N for buys)
            - target_shares: Number of shares to hold
            - shares_to_trade: Change in shares (positive = buy, negative = sell)
        """
        if target_date is None:
            target_date = date.today()
        
        top_n = self.config['strategy']['top_n']
        
        # Get current top N stocks
        new_holdings = scores.head(top_n).copy()
        
        # Get latest prices
        latest_prices = prices.loc[target_date] if target_date in prices.index else prices.iloc[-1]
        
        # Calculate target portfolio value
        cash = self.config['backtest']['initial_capital']
        portfolio_value = self.calculate_portfolio_value(latest_prices)
        target_position_value = portfolio_value / top_n
        
        signals = []
        
        # BUY signals (in new top N, not currently held)
        for ticker in new_holdings.index:
            if ticker not in self.current_holdings.index:
                current_price = latest_prices.get(ticker, np.nan)
                if pd.notna(current_price):
                    target_shares = int(target_position_value / current_price)
                    signals.append({
                        'ticker': ticker,
                        'action': 'BUY',
                        'magic_rank': new_holdings.loc[ticker, 'magic_rank'],
                        'current_price': current_price,
                        'target_weight': 1 / top_n,
                        'target_shares': target_shares,
                        'shares_to_trade': target_shares,
                    })
        
        # SELL signals (currently held, not in new top N)
        for ticker in self.current_holdings.index:
            if ticker not in new_holdings.index:
                current_price = latest_prices.get(ticker, np.nan)
                current_shares = self.current_holdings.loc[ticker, 'shares']
                signals.append({
                    'ticker': ticker,
                    'action': 'SELL',
                    'magic_rank': np.nan,
                    'current_price': current_price,
                    'target_weight': 0,
                    'target_shares': 0,
                    'shares_to_trade': -current_shares,
                })
        
        # HOLD signals (in both)
        for ticker in new_holdings.index:
            if ticker in self.current_holdings.index:
                current_price = latest_prices.get(ticker, np.nan)
                current_shares = self.current_holdings.loc[ticker, 'shares']
                signals.append({
                    'ticker': ticker,
                    'action': 'HOLD',
                    'magic_rank': new_holdings.loc[ticker, 'magic_rank'],
                    'current_price': current_price,
                    'target_weight': 1 / top_n,
                    'target_shares': current_shares,
                    'shares_to_trade': 0,
                })
        
        return pd.DataFrame(signals).sort_values('action')
    
    def calculate_portfolio_value(self, latest_prices: pd.Series) -> float:
        """Calculate current portfolio value"""
        if self.current_holdings.empty:
            return self.config['backtest']['initial_capital']
        
        total_value = 0
        for ticker, row in self.current_holdings.iterrows():
            current_price = latest_prices.get(ticker, np.nan)
            if pd.notna(current_price):
                total_value += row['shares'] * current_price
        
        # Add cash (simplified: assume no cash tracking for now)
        return total_value if total_value > 0 else self.config['backtest']['initial_capital']
    
    def export_signals(self, signals: pd.DataFrame, output_path: str) -> None:
        """Export signals to CSV"""
        signals.to_csv(output_path, index=False)
        print(f"Signals exported to {output_path}")
```

## Portfolio Tracker

**File**: `D:\quant-edge\execution\portfolio_tracker.py`

```python
import pandas as pd
from pathlib import Path
from datetime import datetime

class PortfolioTracker:
    """
    Track current positions and performance.
    """
    
    def __init__(self, portfolio_path: str = "D:/quant-edge/data/portfolio.csv"):
        self.portfolio_path = Path(portfolio_path)
        self.portfolio = self.load()
    
    def load(self) -> pd.DataFrame:
        """Load portfolio from CSV"""
        if self.portfolio_path.exists():
            return pd.read_csv(self.portfolio_path)
        else:
            return pd.DataFrame(columns=[
                'ticker', 'shares', 'entry_price', 'entry_date', 
                'current_price', 'current_value', 'pnl', 'pnl_pct'
            ])
    
    def save(self) -> None:
        """Save portfolio to CSV"""
        self.portfolio_path.parent.mkdir(parents=True, exist_ok=True)
        self.portfolio.to_csv(self.portfolio_path, index=False)
    
    def update_position(
        self,
        ticker: str,
        shares: int,
        price: float,
        date: str
    ) -> None:
        """
        Update or create position.
        
        Args:
            ticker: Stock symbol
            shares: Number of shares (0 = close position)
            price: Transaction price
            date: Transaction date (YYYY-MM-DD)
        """
        if shares == 0:
            # Close position
            self.portfolio = self.portfolio[self.portfolio['ticker'] != ticker]
        else:
            # Update or create position
            if ticker in self.portfolio['ticker'].values:
                idx = self.portfolio['ticker'] == ticker
                self.portfolio.loc[idx, 'shares'] = shares
                self.portfolio.loc[idx, 'entry_price'] = price
                self.portfolio.loc[idx, 'entry_date'] = date
            else:
                new_row = pd.DataFrame([{
                    'ticker': ticker,
                    'shares': shares,
                    'entry_price': price,
                    'entry_date': date,
                    'current_price': price,
                    'current_value': shares * price,
                    'pnl': 0,
                    'pnl_pct': 0,
                }])
                self.portfolio = pd.concat([self.portfolio, new_row], ignore_index=True)
        
        self.save()
    
    def update_prices(self, latest_prices: pd.Series) -> None:
        """Update current prices and calculate P&L"""
        for idx, row in self.portfolio.iterrows():
            ticker = row['ticker']
            if ticker in latest_prices.index:
                current_price = latest_prices[ticker]
                entry_price = row['entry_price']
                shares = row['shares']
                
                self.portfolio.at[idx, 'current_price'] = current_price
                self.portfolio.at[idx, 'current_value'] = current_price * shares
                self.portfolio.at[idx, 'pnl'] = (current_price - entry_price) * shares
                self.portfolio.at[idx, 'pnl_pct'] = ((current_price / entry_price) - 1) * 100
        
        self.save()
    
    def get_summary(self) -> dict:
        """Calculate portfolio summary statistics"""
        if self.portfolio.empty:
            return {
                'total_value': 0,
                'total_pnl': 0,
                'total_pnl_pct': 0,
                'num_positions': 0,
                'winners': 0,
                'losers': 0,
            }
        
        return {
            'total_value': self.portfolio['current_value'].sum(),
            'total_pnl': self.portfolio['pnl'].sum(),
            'total_pnl_pct': (self.portfolio['pnl'].sum() / 
                             (self.portfolio['entry_price'] * self.portfolio['shares']).sum()) * 100,
            'num_positions': len(self.portfolio),
            'winners': (self.portfolio['pnl'] > 0).sum(),
            'losers': (self.portfolio['pnl'] < 0).sum(),
        }
```

## CLI Tool

**File**: `D:\quant-edge\run_signals.py`

```python
#!/usr/bin/env python3
"""
QuantEdge Signal Generator

Usage:
    python run_signals.py                    # Generate signals for today
    python run_signals.py --date 2024-10-18  # Generate signals for specific date
    python run_signals.py --show-portfolio   # Show current portfolio
    python run_signals.py --execute          # Execute trades (manual confirmation)
"""

import argparse
from datetime import datetime, date
from colorama import Fore, Style, init
from tabulate import tabulate

from data.fetchers import DataFetcher
from factors.composite import magic_formula_score
from execution.signal_generator import SignalGenerator
from execution.portfolio_tracker import PortfolioTracker

# Initialize colorama
init(autoreset=True)

def print_header(text: str):
    """Print colored header"""
    print(f"\n{Fore.CYAN}{'='*70}")
    print(f"{Fore.CYAN}{text:^70}")
    print(f"{Fore.CYAN}{'='*70}{Style.RESET_ALL}\n")

def print_signals(signals: pd.DataFrame):
    """Print signals in formatted table"""
    # Color code by action
    def color_action(action):
        if action == 'BUY':
            return f"{Fore.GREEN}{action}{Style.RESET_ALL}"
        elif action == 'SELL':
            return f"{Fore.RED}{action}{Style.RESET_ALL}"
        else:
            return f"{Fore.YELLOW}{action}{Style.RESET_ALL}"
    
    # Format table
    table_data = []
    for _, row in signals.iterrows():
        table_data.append([
            color_action(row['action']),
            row['ticker'],
            f"${row['current_price']:.2f}",
            row['target_shares'],
            row['shares_to_trade'],
            f"${row['target_shares'] * row['current_price']:,.2f}"
        ])
    
    headers = ['Action', 'Ticker', 'Price', 'Target Shares', 'Shares to Trade', 'Value']
    print(tabulate(table_data, headers=headers, tablefmt='grid'))

def main():
    parser = argparse.ArgumentParser(description='QuantEdge Signal Generator')
    parser.add_argument('--date', type=str, help='Date for signals (YYYY-MM-DD)')
    parser.add_argument('--show-portfolio', action='store_true', help='Show current portfolio')
    parser.add_argument('--execute', action='store_true', help='Execute trades')
    parser.add_argument('--export', type=str, help='Export signals to CSV')
    
    args = parser.parse_args()
    
    # Parse date
    target_date = datetime.strptime(args.date, '%Y-%m-%d').date() if args.date else date.today()
    
    print_header("QuantEdge - Magic Formula Signal Generator")
    print(f"Date: {target_date}\n")
    
    # Show portfolio if requested
    if args.show_portfolio:
        tracker = PortfolioTracker()
        print_header("Current Portfolio")
        print(tracker.portfolio.to_string())
        summary = tracker.get_summary()
        print(f"\nTotal Value: ${summary['total_value']:,.2f}")
        print(f"Total P&L: ${summary['total_pnl']:,.2f} ({summary['total_pnl_pct']:.2f}%)")
        print(f"Positions: {summary['num_positions']} (W: {summary['winners']}, L: {summary['losers']})")
        return
    
    # Fetch data
    print("Fetching data...")
    fetcher = DataFetcher()
    prices = fetcher.get_price_data('2019-01-01', target_date.strftime('%Y-%m-%d'))
    fundamentals = fetcher.get_fundamental_data()
    
    # Calculate scores
    print("Calculating Magic Formula scores...")
    scores = magic_formula_score(fundamentals)
    
    # Generate signals
    print("Generating signals...\n")
    generator = SignalGenerator()
    signals = generator.generate_signals(scores, prices, target_date)
    
    # Print signals
    print_header("Trading Signals")
    print_signals(signals)
    
    # Export if requested
    if args.export:
        generator.export_signals(signals, args.export)
    
    # Execute if requested
    if args.execute:
        print(f"\n{Fore.YELLOW}Execute trades? This will update portfolio.csv (y/n): {Style.RESET_ALL}", end='')
        confirm = input().lower()
        if confirm == 'y':
            tracker = PortfolioTracker()
            for _, signal in signals.iterrows():
                if signal['action'] in ['BUY', 'SELL']:
                    tracker.update_position(
                        signal['ticker'],
                        signal['target_shares'],
                        signal['current_price'],
                        target_date.strftime('%Y-%m-%d')
                    )
            print(f"{Fore.GREEN}Portfolio updated!{Style.RESET_ALL}")
        else:
            print("Execution cancelled.")

if __name__ == '__main__':
    main()
```

## Configuration File

**File**: `D:\quant-edge\config\config.yaml`

```yaml
universe:
  source: "sp500"
  min_market_cap: 2e9

strategy:
  name: "magic_formula"
  top_n: 15
  rebalance_freq: "monthly"

factors:
  quality:
    metric: "roe"
    min_value: 0.1
  value:
    metric: "earnings_yield"
    min_value: 0.05

risk:
  max_position_size: 0.15
  max_sector_exposure: 0.30
  stop_loss_pct: 0.20

backtest:
  start_date: "2019-01-01"
  end_date: "2024-10-01"
  initial_capital: 25000
  commission: 0.001
  slippage: 0.0005
```

## Deliverables

1. **`signal_generator.py`**: Core signal logic (~300 lines)
2. **`portfolio_tracker.py`**: Position tracking (~200 lines)
3. **`run_signals.py`**: CLI tool (~150 lines)
4. **`config.yaml`**: Configuration
5. **`portfolio.csv`**: Portfolio state (created on first run)

## Success Criteria

- [ ] Generates signals in <30 seconds
- [ ] Color-coded terminal output (green BUY, red SELL)
- [ ] Handles missing price data gracefully
- [ ] Portfolio.csv tracks all positions
- [ ] Can run daily without errors
- [ ] Export to CSV works
- [ ] Shows P&L for current positions

## Time Estimate
**2-3 hours**

---

**GO BUILD IT.** This is what you'll use every day during the competition.
