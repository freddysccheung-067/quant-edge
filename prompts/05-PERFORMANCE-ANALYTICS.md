# ONE-SHOT PROMPT: Performance Analysis & Visualization

## Objective
Build comprehensive performance analytics module to evaluate backtest results, calculate risk metrics, and generate visualizations for decision-making.

## Technical Specifications

**File**: `D:\quant-edge\backtesting\performance.py`

**Dependencies**:
```
pandas>=2.1.0
numpy>=1.24.0
matplotlib>=3.7.0
seaborn>=0.12.0
scipy>=1.11.0
```

**Python**: 3.11+ with type hints

## Core Metrics to Implement

### 1. Returns Analysis

```python
import pandas as pd
import numpy as np
from typing import Literal

def calculate_returns(
    portfolio_values: pd.Series | list[float],
    frequency: Literal['daily', 'monthly', 'yearly'] = 'daily'
) -> pd.Series:
    """
    Calculate returns from portfolio values.
    
    Args:
        portfolio_values: Time series of portfolio values
        frequency: Return frequency
    
    Returns:
        Series of returns (decimal, not percentage)
    """
    if isinstance(portfolio_values, list):
        portfolio_values = pd.Series(portfolio_values)
    
    returns = portfolio_values.pct_change().dropna()
    
    if frequency == 'monthly':
        returns = returns.resample('M').apply(lambda x: (1 + x).prod() - 1)
    elif frequency == 'yearly':
        returns = returns.resample('Y').apply(lambda x: (1 + x).prod() - 1)
    
    return returns

def calculate_cagr(
    start_value: float,
    end_value: float,
    years: float
) -> float:
    """
    Compound Annual Growth Rate.
    
    CAGR = (End Value / Start Value)^(1/years) - 1
    """
    return (end_value / start_value) ** (1 / years) - 1

def calculate_total_return(portfolio_values: pd.Series) -> float:
    """Total return from start to end"""
    return (portfolio_values.iloc[-1] / portfolio_values.iloc[0]) - 1
```

### 2. Risk Metrics

```python
def calculate_volatility(
    returns: pd.Series,
    annualize: bool = True,
    periods_per_year: int = 252
) -> float:
    """
    Calculate return volatility (standard deviation).
    
    Args:
        returns: Daily returns
        annualize: If True, annualize the result
        periods_per_year: 252 for daily, 12 for monthly
    
    Returns:
        Annualized volatility (decimal)
    """
    vol = returns.std()
    if annualize:
        vol *= np.sqrt(periods_per_year)
    return vol

def calculate_sharpe_ratio(
    returns: pd.Series,
    risk_free_rate: float = 0.02,
    periods_per_year: int = 252
) -> float:
    """
    Sharpe Ratio = (Mean Return - Risk Free Rate) / Volatility
    
    Higher is better. >1.0 is good, >2.0 is excellent.
    
    Args:
        returns: Daily returns
        risk_free_rate: Annual risk-free rate (default 2%)
        periods_per_year: For annualization
    
    Returns:
        Sharpe ratio
    """
    excess_returns = returns - (risk_free_rate / periods_per_year)
    if excess_returns.std() == 0:
        return 0.0
    return np.sqrt(periods_per_year) * excess_returns.mean() / excess_returns.std()

def calculate_sortino_ratio(
    returns: pd.Series,
    risk_free_rate: float = 0.02,
    periods_per_year: int = 252
) -> float:
    """
    Sortino Ratio = (Mean Return - Risk Free Rate) / Downside Deviation
    
    Like Sharpe but only penalizes downside volatility.
    """
    excess_returns = returns - (risk_free_rate / periods_per_year)
    downside_returns = excess_returns[excess_returns < 0]
    downside_std = downside_returns.std()
    
    if downside_std == 0:
        return 0.0
    
    return np.sqrt(periods_per_year) * excess_returns.mean() / downside_std

def calculate_max_drawdown(portfolio_values: pd.Series) -> dict:
    """
    Maximum drawdown: largest peak-to-trough decline.
    
    Returns dict with:
    - max_drawdown: Maximum drawdown (decimal)
    - max_drawdown_pct: Maximum drawdown (percentage)
    - peak_date: Date of peak before max drawdown
    - trough_date: Date of trough (lowest point)
    - recovery_date: Date recovered to peak (or None if not recovered)
    - drawdown_duration: Days from peak to trough
    """
    # Calculate running maximum
    running_max = portfolio_values.expanding().max()
    
    # Calculate drawdown
    drawdown = (portfolio_values - running_max) / running_max
    
    # Find maximum drawdown
    max_dd = drawdown.min()
    trough_idx = drawdown.idxmin()
    
    # Find peak before trough
    peak_idx = portfolio_values[:trough_idx].idxmax()
    
    # Find recovery date (if any)
    recovery_idx = None
    for idx in portfolio_values[trough_idx:].index:
        if portfolio_values[idx] >= portfolio_values[peak_idx]:
            recovery_idx = idx
            break
    
    # Calculate duration
    duration = (trough_idx - peak_idx).days if hasattr(trough_idx - peak_idx, 'days') else None
    
    return {
        'max_drawdown': max_dd,
        'max_drawdown_pct': max_dd * 100,
        'peak_date': peak_idx,
        'trough_date': trough_idx,
        'recovery_date': recovery_idx,
        'drawdown_duration': duration,
    }

def calculate_calmar_ratio(
    returns: pd.Series,
    portfolio_values: pd.Series
) -> float:
    """
    Calmar Ratio = CAGR / Max Drawdown
    
    Measures return relative to worst drawdown.
    Higher is better. >3.0 is excellent.
    """
    cagr = calculate_cagr(
        portfolio_values.iloc[0],
        portfolio_values.iloc[-1],
        len(portfolio_values) / 252  # Assume daily data
    )
    
    max_dd = calculate_max_drawdown(portfolio_values)['max_drawdown']
    
    if max_dd == 0:
        return 0.0
    
    return abs(cagr / max_dd)
```

### 3. Win Rate Analysis

```python
def calculate_win_rate(returns: pd.Series) -> dict:
    """
    Calculate win rate statistics.
    
    Returns dict with:
    - win_rate: % of positive return periods
    - avg_win: Average winning return
    - avg_loss: Average losing return
    - win_loss_ratio: Avg win / Avg loss
    - best_day: Best single-day return
    - worst_day: Worst single-day return
    """
    wins = returns[returns > 0]
    losses = returns[returns < 0]
    
    return {
        'win_rate': len(wins) / len(returns) * 100,
        'avg_win': wins.mean() if len(wins) > 0 else 0,
        'avg_loss': losses.mean() if len(losses) > 0 else 0,
        'win_loss_ratio': abs(wins.mean() / losses.mean()) if len(losses) > 0 and losses.mean() != 0 else 0,
        'best_day': returns.max(),
        'worst_day': returns.min(),
    }
```

### 4. Benchmark Comparison

```python
def compare_to_benchmark(
    strategy_returns: pd.Series,
    benchmark_returns: pd.Series
) -> dict:
    """
    Compare strategy to benchmark (e.g., SPY).
    
    Returns dict with:
    - alpha: Excess return over benchmark
    - beta: Sensitivity to benchmark
    - correlation: Correlation with benchmark
    - tracking_error: Volatility of excess returns
    - information_ratio: Alpha / Tracking Error
    """
    # Align returns
    aligned = pd.DataFrame({
        'strategy': strategy_returns,
        'benchmark': benchmark_returns
    }).dropna()
    
    # Calculate metrics
    from scipy import stats
    
    beta, alpha, _, _, _ = stats.linregress(
        aligned['benchmark'],
        aligned['strategy']
    )
    
    excess_returns = aligned['strategy'] - aligned['benchmark']
    tracking_error = excess_returns.std() * np.sqrt(252)
    
    information_ratio = (excess_returns.mean() * 252) / tracking_error if tracking_error != 0 else 0
    
    return {
        'alpha': alpha * 252,  # Annualized
        'beta': beta,
        'correlation': aligned.corr().iloc[0, 1],
        'tracking_error': tracking_error,
        'information_ratio': information_ratio,
    }
```

## Visualization Functions

```python
import matplotlib.pyplot as plt
import seaborn as sns

plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")

def plot_equity_curve(
    portfolio_values: pd.Series,
    benchmark_values: pd.Series | None = None,
    title: str = "Portfolio Equity Curve",
    figsize: tuple = (14, 7)
):
    """
    Plot portfolio value over time.
    
    Args:
        portfolio_values: Strategy portfolio values
        benchmark_values: Optional benchmark for comparison
        title: Plot title
        figsize: Figure size
    """
    fig, ax = plt.subplots(figsize=figsize)
    
    # Normalize to 100
    norm_portfolio = portfolio_values / portfolio_values.iloc[0] * 100
    ax.plot(norm_portfolio.index, norm_portfolio.values, 
            label='Strategy', linewidth=2, color='#4CAF50')
    
    if benchmark_values is not None:
        norm_benchmark = benchmark_values / benchmark_values.iloc[0] * 100
        ax.plot(norm_benchmark.index, norm_benchmark.values,
                label='Benchmark (SPY)', linewidth=2, color='#2196F3', alpha=0.7)
    
    ax.set_title(title, fontsize=16, fontweight='bold')
    ax.set_xlabel('Date', fontsize=12)
    ax.set_ylabel('Portfolio Value (Base = 100)', fontsize=12)
    ax.legend(fontsize=11)
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    return fig

def plot_drawdown(
    portfolio_values: pd.Series,
    title: str = "Drawdown Analysis",
    figsize: tuple = (14, 5)
):
    """Plot drawdown over time"""
    fig, ax = plt.subplots(figsize=figsize)
    
    running_max = portfolio_values.expanding().max()
    drawdown = (portfolio_values - running_max) / running_max * 100
    
    ax.fill_between(drawdown.index, drawdown.values, 0,
                     color='#F44336', alpha=0.3, label='Drawdown')
    ax.plot(drawdown.index, drawdown.values, color='#F44336', linewidth=1.5)
    
    ax.set_title(title, fontsize=16, fontweight='bold')
    ax.set_xlabel('Date', fontsize=12)
    ax.set_ylabel('Drawdown (%)', fontsize=12)
    ax.legend(fontsize=11)
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    return fig

def plot_monthly_returns(
    returns: pd.Series,
    title: str = "Monthly Returns Heatmap",
    figsize: tuple = (12, 8)
):
    """Plot monthly returns as heatmap"""
    # Resample to monthly
    monthly_returns = returns.resample('M').apply(lambda x: (1 + x).prod() - 1)
    
    # Create pivot table (Year x Month)
    monthly_returns_df = pd.DataFrame({
        'Year': monthly_returns.index.year,
        'Month': monthly_returns.index.month,
        'Return': monthly_returns.values * 100
    })
    
    pivot = monthly_returns_df.pivot(index='Year', columns='Month', values='Return')
    
    fig, ax = plt.subplots(figsize=figsize)
    sns.heatmap(pivot, annot=True, fmt='.1f', cmap='RdYlGn', center=0,
                cbar_kws={'label': 'Return (%)'}, ax=ax)
    
    ax.set_title(title, fontsize=16, fontweight='bold')
    ax.set_xlabel('Month', fontsize=12)
    ax.set_ylabel('Year', fontsize=12)
    
    plt.tight_layout()
    return fig

def plot_return_distribution(
    returns: pd.Series,
    title: str = "Return Distribution",
    figsize: tuple = (12, 5)
):
    """Plot return distribution histogram"""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=figsize)
    
    # Histogram
    ax1.hist(returns * 100, bins=50, color='#2196F3', alpha=0.7, edgecolor='black')
    ax1.axvline(returns.mean() * 100, color='red', linestyle='--', 
                linewidth=2, label=f'Mean: {returns.mean()*100:.2f}%')
    ax1.set_title('Return Distribution', fontsize=14, fontweight='bold')
    ax1.set_xlabel('Daily Return (%)', fontsize=11)
    ax1.set_ylabel('Frequency', fontsize=11)
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Q-Q plot
    from scipy import stats
    stats.probplot(returns, dist="norm", plot=ax2)
    ax2.set_title('Q-Q Plot (Normality Test)', fontsize=14, fontweight='bold')
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    return fig
```

## Main Performance Report Class

```python
class PerformanceReport:
    """
    Comprehensive performance analysis.
    """
    
    def __init__(
        self,
        portfolio_values: pd.Series,
        benchmark_values: pd.Series | None = None
    ):
        self.portfolio_values = portfolio_values
        self.benchmark_values = benchmark_values
        self.returns = calculate_returns(portfolio_values)
        
        if benchmark_values is not None:
            self.benchmark_returns = calculate_returns(benchmark_values)
    
    def generate_report(self) -> dict:
        """Generate complete performance metrics"""
        years = len(self.portfolio_values) / 252
        
        metrics = {
            'Total Return': f"{calculate_total_return(self.portfolio_values) * 100:.2f}%",
            'CAGR': f"{calculate_cagr(self.portfolio_values.iloc[0], self.portfolio_values.iloc[-1], years) * 100:.2f}%",
            'Volatility': f"{calculate_volatility(self.returns) * 100:.2f}%",
            'Sharpe Ratio': f"{calculate_sharpe_ratio(self.returns):.2f}",
            'Sortino Ratio': f"{calculate_sortino_ratio(self.returns):.2f}",
            'Calmar Ratio': f"{calculate_calmar_ratio(self.returns, self.portfolio_values):.2f}",
        }
        
        # Drawdown metrics
        dd = calculate_max_drawdown(self.portfolio_values)
        metrics['Max Drawdown'] = f"{dd['max_drawdown_pct']:.2f}%"
        metrics['Max DD Duration'] = f"{dd['drawdown_duration']} days" if dd['drawdown_duration'] else 'N/A'
        
        # Win rate
        wr = calculate_win_rate(self.returns)
        metrics['Win Rate'] = f"{wr['win_rate']:.2f}%"
        metrics['Avg Win'] = f"{wr['avg_win'] * 100:.2f}%"
        metrics['Avg Loss'] = f"{wr['avg_loss'] * 100:.2f}%"
        metrics['Win/Loss Ratio'] = f"{wr['win_loss_ratio']:.2f}"
        
        # Benchmark comparison
        if self.benchmark_values is not None:
            bench = compare_to_benchmark(self.returns, self.benchmark_returns)
            metrics['Alpha'] = f"{bench['alpha'] * 100:.2f}%"
            metrics['Beta'] = f"{bench['beta']:.2f}"
            metrics['Information Ratio'] = f"{bench['information_ratio']:.2f}"
        
        return metrics
    
    def print_report(self):
        """Print formatted report"""
        from tabulate import tabulate
        
        metrics = self.generate_report()
        table = [[k, v] for k, v in metrics.items()]
        
        print("\n" + "="*60)
        print("PERFORMANCE REPORT".center(60))
        print("="*60 + "\n")
        print(tabulate(table, headers=['Metric', 'Value'], tablefmt='grid'))
    
    def plot_all(self, save_path: str | None = None):
        """Generate all plots"""
        fig1 = plot_equity_curve(self.portfolio_values, self.benchmark_values)
        fig2 = plot_drawdown(self.portfolio_values)
        fig3 = plot_monthly_returns(self.returns)
        fig4 = plot_return_distribution(self.returns)
        
        if save_path:
            fig1.savefig(f"{save_path}_equity.png", dpi=300, bbox_inches='tight')
            fig2.savefig(f"{save_path}_drawdown.png", dpi=300, bbox_inches='tight')
            fig3.savefig(f"{save_path}_monthly.png", dpi=300, bbox_inches='tight')
            fig4.savefig(f"{save_path}_distribution.png", dpi=300, bbox_inches='tight')
        
        plt.show()
```

## Deliverables

1. **`performance.py`**: All metrics and plotting (~600 lines)
2. **`__init__.py`**: Exports

## Success Criteria

- [ ] Calculates all standard metrics (Sharpe, Sortino, Calmar, etc.)
- [ ] Generates professional-quality plots
- [ ] Benchmark comparison works
- [ ] Monthly heatmap displays correctly
- [ ] Runs in <5 seconds for 5 years of data

## Time Estimate
**3-4 hours**

---

**GO BUILD IT.** This tells you if the strategy actually works.
