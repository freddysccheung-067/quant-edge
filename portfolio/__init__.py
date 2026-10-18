"""
Portfolio Optimization Module

This module handles portfolio construction using modern portfolio theory (MPT)
and advanced optimization techniques from Skfolio.

Optimization Methods:
    - Equal Weight: Baseline strategy
    - Mean-Variance (Markowitz): Classic risk-return optimization
    - Hierarchical Risk Parity (HRP): Correlation-based allocation
    - Maximum Sharpe Ratio: Risk-adjusted return maximization

References:
    - Markowitz, H. (1952). Portfolio Selection
    - Lopez de Prado, M. (2016). Building Diversified Portfolios
    - Skfolio documentation: https://skfolio.org/
"""

from .optimizer import (
    PortfolioOptimizer,
    optimize_portfolio,
    construct_equal_weight_portfolio,
    backtest_portfolio
)

__all__ = [
    'PortfolioOptimizer',
    'optimize_portfolio',
    'construct_equal_weight_portfolio',
    'backtest_portfolio',
]
