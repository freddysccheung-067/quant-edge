"""
Portfolio Optimizer Implementation

Provides production-grade portfolio construction using Skfolio and modern
portfolio theory techniques.

Author: quant-edge Team
Date: 2024-10-18
"""

import pandas as pd
import numpy as np
from typing import Optional, Dict, List, Tuple, Literal
import logging
from datetime import datetime, timedelta

# Skfolio imports
from skfolio import Population, RiskMeasure
from skfolio.optimization import MeanRisk, HierarchicalRiskParity, EqualWeighted
from skfolio.pre_selection import SelectKExtremes
from skfolio.prior import EmpiricalPrior

logger = logging.getLogger(__name__)


class PortfolioOptimizer:
    """
    Construct optimized portfolios using various allocation strategies.

    Supports multiple optimization methods:
        - equal_weight: Simple 1/N allocation
        - mean_variance: Markowitz optimization
        - max_sharpe: Maximum Sharpe ratio
        - hrp: Hierarchical Risk Parity

    Args:
        method: Optimization method (default: 'equal_weight')
        target_positions: Number of positions in portfolio (default: 20)
        risk_free_rate: Annual risk-free rate (default: 0.04)
        max_weight: Maximum weight per position (default: 0.15)
        min_weight: Minimum weight per position (default: 0.01)

    Example:
        >>> optimizer = PortfolioOptimizer(method='max_sharpe', target_positions=20)
        >>> prices = fetcher.get_price_data(tickers=top_stocks, start_date='2020-01-01')
        >>> weights, metrics = optimizer.optimize(prices)
        >>> print(f"Expected return: {metrics['return']*100:.1f}%")
        >>> print(f"Volatility: {metrics['volatility']*100:.1f}%")
        >>> print(f"Sharpe ratio: {metrics['sharpe']:.2f}")
    """

    def __init__(
        self,
        method: Literal['equal_weight', 'mean_variance', 'max_sharpe', 'hrp'] = 'equal_weight',
        target_positions: int = 20,
        risk_free_rate: float = 0.04,
        max_weight: float = 0.15,
        min_weight: float = 0.01
    ):
        self.method = method
        self.target_positions = target_positions
        self.risk_free_rate = risk_free_rate
        self.max_weight = max_weight
        self.min_weight = min_weight

        logger.info(f"Initialized Portfolio Optimizer")
        logger.info(f"  Method: {self.method}")
        logger.info(f"  Target positions: {self.target_positions}")
        logger.info(f"  Weight limits: {self.min_weight*100:.1f}% - {self.max_weight*100:.1f}%")
        logger.info(f"  Risk-free rate: {self.risk_free_rate*100:.1f}%")

    def optimize(
        self,
        prices: pd.DataFrame,
        existing_holdings: Optional[Dict[str, float]] = None
    ) -> Tuple[Dict[str, float], Dict[str, float]]:
        """
        Optimize portfolio weights based on historical price data.

        Args:
            prices: Historical price data (index=dates, columns=tickers)
            existing_holdings: Optional dict of current holdings {ticker: weight}
                             (used for rebalancing to minimize turnover)

        Returns:
            Tuple of (weights, metrics):
                weights: Dict mapping ticker -> portfolio weight
                metrics: Dict containing:
                    - return: Expected annual return
                    - volatility: Expected annual volatility
                    - sharpe: Sharpe ratio
                    - turnover: Turnover from existing holdings (if provided)

        Example:
            >>> weights, metrics = optimizer.optimize(prices)
            >>> # Invest $25,000
            >>> for ticker, weight in weights.items():
            >>>     shares = int((25000 * weight) / current_prices[ticker])
            >>>     print(f"{ticker}: {shares} shares (${25000*weight:.2f})")
        """
        logger.info(f"Optimizing portfolio: {len(prices.columns)} tickers, "
                    f"{len(prices)} days of data")

        # 1. Validate inputs
        prices = self._validate_prices(prices)

        # 2. Select top stocks if needed
        if len(prices.columns) > self.target_positions:
            prices = self._select_top_stocks(prices)
            logger.info(f"  Selected top {self.target_positions} stocks by recent performance")

        # 3. Run optimization based on method
        if self.method == 'equal_weight':
            weights_series = self._equal_weight_optimization(prices)
        elif self.method == 'mean_variance':
            weights_series = self._mean_variance_optimization(prices)
        elif self.method == 'max_sharpe':
            weights_series = self._max_sharpe_optimization(prices)
        elif self.method == 'hrp':
            weights_series = self._hrp_optimization(prices)
        else:
            raise ValueError(f"Unknown optimization method: {self.method}")

        # 4. Convert to dict
        weights = weights_series.to_dict()

        # 5. Calculate metrics
        metrics = self._calculate_metrics(prices, weights, existing_holdings)

        # 6. Log results
        self._log_results(weights, metrics)

        return weights, metrics

    def _validate_prices(self, prices: pd.DataFrame) -> pd.DataFrame:
        """Validate and clean price data."""
        # Remove tickers with too much missing data
        missing_pct = prices.isna().sum() / len(prices)
        valid_tickers = missing_pct[missing_pct < 0.1].index

        if len(valid_tickers) < len(prices.columns):
            removed = len(prices.columns) - len(valid_tickers)
            logger.warning(f"  Removed {removed} tickers with >10% missing data")
            prices = prices[valid_tickers]

        # Forward fill missing values
        prices = prices.ffill()

        # Check minimum data requirement
        min_days = 60  # At least ~3 months of data
        if len(prices) < min_days:
            raise ValueError(f"Need at least {min_days} days of data, got {len(prices)}")

        return prices

    def _select_top_stocks(self, prices: pd.DataFrame) -> pd.DataFrame:
        """
        Select top N stocks by recent performance.

        This is a simple momentum-based pre-selection. More sophisticated
        methods could use the Magic Formula scores.
        """
        # Calculate 60-day return for each stock
        returns_60d = (prices.iloc[-1] / prices.iloc[-60] - 1)

        # Select top N by return
        top_tickers = returns_60d.nlargest(self.target_positions).index

        return prices[top_tickers]

    def _equal_weight_optimization(self, prices: pd.DataFrame) -> pd.Series:
        """Simple 1/N allocation."""
        n = len(prices.columns)
        weights = pd.Series(1.0 / n, index=prices.columns)

        logger.info(f"  Equal weight: {1.0/n*100:.1f}% per position")
        return weights

    def _mean_variance_optimization(self, prices: pd.DataFrame) -> pd.Series:
        """Markowitz mean-variance optimization."""
        # Calculate returns
        returns = prices.pct_change().dropna()

        # Setup optimizer
        model = MeanRisk(
            risk_measure=RiskMeasure.VARIANCE,
            prior_estimator=EmpiricalPrior(),
            min_weights=self.min_weight,
            max_weights=self.max_weight
        )

        # Fit
        model.fit(returns)

        # Get weights
        weights = pd.Series(model.weights_, index=prices.columns)

        logger.info(f"  Mean-variance optimization complete")
        return weights

    def _max_sharpe_optimization(self, prices: pd.DataFrame) -> pd.Series:
        """
        Maximum Sharpe ratio optimization.

        This finds the portfolio with the best risk-adjusted return.
        """
        # Calculate returns
        returns = prices.pct_change().dropna()

        # Setup optimizer targeting maximum Sharpe
        model = MeanRisk(
            risk_measure=RiskMeasure.STANDARD_DEVIATION,
            objective_function='max_sharpe',
            prior_estimator=EmpiricalPrior(),
            min_weights=self.min_weight,
            max_weights=self.max_weight
        )

        # Fit
        model.fit(returns)

        # Get weights
        weights = pd.Series(model.weights_, index=prices.columns)

        logger.info(f"  Maximum Sharpe optimization complete")
        return weights

    def _hrp_optimization(self, prices: pd.DataFrame) -> pd.Series:
        """
        Hierarchical Risk Parity optimization.

        This uses correlation structure to build a diversified portfolio
        without relying on return forecasts.
        """
        # Calculate returns
        returns = prices.pct_change().dropna()

        # Setup HRP optimizer
        model = HierarchicalRiskParity(
            prior_estimator=EmpiricalPrior()
        )

        # Fit
        model.fit(returns)

        # Get weights
        weights = pd.Series(model.weights_, index=prices.columns)

        logger.info(f"  HRP optimization complete")
        return weights

    def _calculate_metrics(
        self,
        prices: pd.DataFrame,
        weights: Dict[str, float],
        existing_holdings: Optional[Dict[str, float]] = None
    ) -> Dict[str, float]:
        """Calculate portfolio performance metrics."""
        # Convert weights dict to series aligned with prices
        weights_series = pd.Series(weights)
        weights_series = weights_series.reindex(prices.columns, fill_value=0)
        weights_series = weights_series / weights_series.sum()  # Renormalize

        # Calculate returns
        returns = prices.pct_change().dropna()

        # Portfolio returns
        portfolio_returns = (returns * weights_series).sum(axis=1)

        # Annualized metrics (252 trading days)
        annual_return = portfolio_returns.mean() * 252
        annual_vol = portfolio_returns.std() * np.sqrt(252)
        sharpe = (annual_return - self.risk_free_rate) / annual_vol if annual_vol > 0 else 0

        metrics = {
            'return': annual_return,
            'volatility': annual_vol,
            'sharpe': sharpe,
            'num_positions': (weights_series > 0).sum()
        }

        # Calculate turnover if existing holdings provided
        if existing_holdings is not None:
            existing_series = pd.Series(existing_holdings).reindex(prices.columns, fill_value=0)
            turnover = np.abs(weights_series - existing_series).sum() / 2
            metrics['turnover'] = turnover

        return metrics

    def _log_results(self, weights: Dict[str, float], metrics: Dict[str, float]):
        """Log optimization results."""
        logger.info(f"\nPortfolio Optimization Results:")
        logger.info(f"  Positions: {metrics['num_positions']}")
        logger.info(f"  Expected Return: {metrics['return']*100:.1f}%")
        logger.info(f"  Volatility: {metrics['volatility']*100:.1f}%")
        logger.info(f"  Sharpe Ratio: {metrics['sharpe']:.2f}")

        if 'turnover' in metrics:
            logger.info(f"  Turnover: {metrics['turnover']*100:.1f}%")

        logger.info(f"\nTop 5 Holdings:")
        sorted_weights = sorted(weights.items(), key=lambda x: x[1], reverse=True)
        for ticker, weight in sorted_weights[:5]:
            logger.info(f"    {ticker}: {weight*100:.1f}%")


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def optimize_portfolio(
    prices: pd.DataFrame,
    method: str = 'equal_weight',
    target_positions: int = 20,
    **kwargs
) -> Tuple[Dict[str, float], Dict[str, float]]:
    """
    One-liner function to optimize a portfolio.

    Args:
        prices: Historical price data
        method: Optimization method
        target_positions: Number of positions
        **kwargs: Additional arguments for PortfolioOptimizer

    Returns:
        Tuple of (weights, metrics)

    Example:
        >>> weights, metrics = optimize_portfolio(prices, method='max_sharpe', target_positions=20)
    """
    optimizer = PortfolioOptimizer(
        method=method,
        target_positions=target_positions,
        **kwargs
    )
    return optimizer.optimize(prices)


def construct_equal_weight_portfolio(
    tickers: List[str],
    n_positions: int = 20
) -> Dict[str, float]:
    """
    Construct a simple equal-weight portfolio.

    Args:
        tickers: List of stock tickers
        n_positions: Number of positions (default: 20)

    Returns:
        Dict mapping ticker -> weight

    Example:
        >>> top_stocks = get_magic_formula_rankings(fundamentals, top_n=30)
        >>> weights = construct_equal_weight_portfolio(top_stocks, n_positions=20)
    """
    selected = tickers[:n_positions]
    weight = 1.0 / len(selected)

    weights = {ticker: weight for ticker in selected}

    logger.info(f"Equal-weight portfolio: {len(selected)} positions @ {weight*100:.1f}% each")

    return weights


def backtest_portfolio(
    weights: Dict[str, float],
    prices: pd.DataFrame,
    initial_capital: float = 25000.0,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> pd.DataFrame:
    """
    Backtest portfolio performance over time.

    Args:
        weights: Portfolio weights {ticker: weight}
        prices: Historical price data
        initial_capital: Starting capital (default: $25,000)
        start_date: Backtest start date (default: first date in prices)
        end_date: Backtest end date (default: last date in prices)

    Returns:
        DataFrame with columns:
            - portfolio_value: Total portfolio value
            - daily_return: Daily return
            - cumulative_return: Cumulative return from start

    Example:
        >>> results = backtest_portfolio(weights, prices, initial_capital=25000)
        >>> print(f"Final value: ${results['portfolio_value'].iloc[-1]:,.2f}")
        >>> print(f"Total return: {results['cumulative_return'].iloc[-1]*100:.1f}%")
    """
    # Filter to date range
    if start_date:
        prices = prices[prices.index >= start_date]
    if end_date:
        prices = prices[prices.index <= end_date]

    # Filter to tickers in weights
    tickers = list(weights.keys())
    prices = prices[tickers]

    # Calculate returns
    returns = prices.pct_change().dropna()

    # Portfolio returns
    weights_series = pd.Series(weights)
    portfolio_returns = (returns * weights_series).sum(axis=1)

    # Build equity curve
    equity_curve = (1 + portfolio_returns).cumprod() * initial_capital

    # Create results DataFrame
    results = pd.DataFrame({
        'portfolio_value': equity_curve,
        'daily_return': portfolio_returns,
        'cumulative_return': equity_curve / initial_capital - 1
    })

    # Calculate statistics
    final_value = results['portfolio_value'].iloc[-1]
    total_return = results['cumulative_return'].iloc[-1]
    annual_return = portfolio_returns.mean() * 252
    annual_vol = portfolio_returns.std() * np.sqrt(252)
    sharpe = (annual_return - 0.04) / annual_vol if annual_vol > 0 else 0

    max_dd = (results['portfolio_value'] / results['portfolio_value'].cummax() - 1).min()

    logger.info(f"\nBacktest Results ({prices.index[0].date()} to {prices.index[-1].date()}):")
    logger.info(f"  Initial Capital: ${initial_capital:,.2f}")
    logger.info(f"  Final Value: ${final_value:,.2f}")
    logger.info(f"  Total Return: {total_return*100:.1f}%")
    logger.info(f"  Annual Return: {annual_return*100:.1f}%")
    logger.info(f"  Annual Volatility: {annual_vol*100:.1f}%")
    logger.info(f"  Sharpe Ratio: {sharpe:.2f}")
    logger.info(f"  Max Drawdown: {max_dd*100:.1f}%")

    return results
