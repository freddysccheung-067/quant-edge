"""
Magic Formula Implementation

The Magic Formula is a value investing strategy developed by Joel Greenblatt
that combines quality and value factors to identify undervalued, high-quality companies.

Formula:
    Quality = Return on Invested Capital (ROIC) or similar profitability metrics
    Value = Earnings Yield (inverse P/E) or similar valuation metrics

    Final Score = Average(Quality Rank, Value Rank)

Lower scores are better (rank 1 is best).

References:
    - Greenblatt, J. (2006). The Little Book That Beats the Market
    - Academic validation: Multiple studies show 10-15% annual alpha vs benchmarks

Author: quant-edge Team
Date: 2024-10-18
"""

import pandas as pd
import numpy as np
from typing import Optional, Dict, List, Tuple
import logging

logger = logging.getLogger(__name__)


class MagicFormulaCalculator:
    """
    Calculate Magic Formula scores for a universe of stocks.

    This implementation uses:
        - Quality: Return on Equity (ROE) as proxy for ROIC
        - Value: Earnings Yield (1 / P/E)

    Args:
        min_market_cap (float): Minimum market cap in USD (default: 50M)
        min_liquidity (float): Minimum average daily volume (default: 100k)
        exclude_financials (bool): Exclude financial sector (default: True)

    Example:
        >>> calculator = MagicFormulaCalculator()
        >>> fundamentals = fetcher.get_fundamental_data(tickers)
        >>> scores = calculator.calculate(fundamentals)
        >>> top_20 = scores.head(20)
    """

    def __init__(
        self,
        min_market_cap: float = 50_000_000,
        min_liquidity: float = 100_000,
        exclude_financials: bool = True
    ):
        self.min_market_cap = min_market_cap
        self.min_liquidity = min_liquidity
        self.exclude_financials = exclude_financials

        logger.info(f"Initialized Magic Formula Calculator")
        logger.info(f"  Min Market Cap: ${self.min_market_cap:,.0f}")
        logger.info(f"  Min Liquidity: {self.min_liquidity:,.0f} shares/day")
        logger.info(f"  Exclude Financials: {self.exclude_financials}")

    def calculate(self, fundamentals: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate Magic Formula scores for all stocks in the universe.

        Args:
            fundamentals: DataFrame with fundamental data (from YFinanceFetcher)

        Returns:
            DataFrame with columns:
                - ticker: Stock ticker
                - roe: Return on Equity (%)
                - earnings_yield: Earnings Yield (%)
                - quality_rank: Rank by ROE (1 = best)
                - value_rank: Rank by Earnings Yield (1 = best)
                - magic_formula_score: Average of quality_rank and value_rank
                - final_rank: Final ranking (1 = best)

        Example:
            >>> scores = calculator.calculate(fundamentals)
            >>> top_stocks = scores.head(30)  # Top 30 stocks
        """
        logger.info(f"Calculating Magic Formula for {len(fundamentals)} stocks...")

        # 1. Filter universe
        df = self._filter_universe(fundamentals)
        logger.info(f"  After filtering: {len(df)} stocks remain")

        if len(df) == 0:
            logger.warning("No stocks passed filters!")
            return pd.DataFrame()

        # 2. Calculate quality metrics
        df = self._calculate_quality(df)

        # 3. Calculate value metrics
        df = self._calculate_value(df)

        # 4. Remove invalid data
        df = df.dropna(subset=['roe', 'earnings_yield'])
        logger.info(f"  After removing invalid data: {len(df)} stocks")

        if len(df) == 0:
            logger.warning("No valid data after calculations!")
            return pd.DataFrame()

        # 5. Rank stocks
        df = self._rank_stocks(df)

        # 6. Calculate final Magic Formula score
        df['magic_formula_score'] = (df['quality_rank'] + df['value_rank']) / 2
        df['final_rank'] = df['magic_formula_score'].rank(method='min').astype(int)

        # 7. Sort and format output
        output_cols = [
            'ticker', 'roe', 'earnings_yield',
            'quality_rank', 'value_rank', 'magic_formula_score', 'final_rank',
            'market_cap', 'avg_volume', 'sector'
        ]

        result = df[output_cols].sort_values('final_rank').reset_index(drop=True)

        logger.info(f"Magic Formula calculation complete!")
        logger.info(f"  Top stock: {result.iloc[0]['ticker']} (score: {result.iloc[0]['magic_formula_score']:.1f})")
        logger.info(f"  ROE range: {result['roe'].min():.1f}% to {result['roe'].max():.1f}%")
        logger.info(f"  Earnings Yield range: {result['earnings_yield'].min():.1f}% to {result['earnings_yield'].max():.1f}%")

        return result

    def _filter_universe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Apply screening filters to remove unsuitable stocks."""
        original_count = len(df)

        # Filter 1: Market cap
        if 'market_cap' in df.columns:
            df = df[df['market_cap'] >= self.min_market_cap]
            logger.debug(f"    Market cap filter: {original_count} -> {len(df)}")

        # Filter 2: Liquidity
        if 'avg_volume' in df.columns:
            df = df[df['avg_volume'] >= self.min_liquidity]
            logger.debug(f"    Liquidity filter: {len(df)} stocks")

        # Filter 3: Financials (optional)
        if self.exclude_financials and 'sector' in df.columns:
            df = df[df['sector'] != 'Financial Services']
            logger.debug(f"    Financial exclusion: {len(df)} stocks")

        return df.copy()

    def _calculate_quality(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate quality metrics.

        We use Return on Equity (ROE) as the quality proxy.
        ROE = Net Income / Shareholders' Equity

        Higher ROE = better quality company.
        """
        # Method 1: Use pre-calculated ROE if available
        if 'return_on_equity' in df.columns:
            df['roe'] = df['return_on_equity'] * 100  # Convert to percentage

        # Method 2: Calculate from Net Income / Book Value
        elif 'net_income_to_common' in df.columns and 'book_value' in df.columns:
            df['roe'] = (df['net_income_to_common'] / df['book_value']) * 100

        # Method 3: Estimate from P/E and P/B ratios
        # ROE ≈ (P/B) / (P/E)
        elif 'trailing_pe' in df.columns and 'price_to_book' in df.columns:
            df['roe'] = (df['price_to_book'] / df['trailing_pe']) * 100
            logger.warning("Using estimated ROE from P/E and P/B ratios")

        else:
            logger.error("Cannot calculate ROE - missing required fields")
            df['roe'] = np.nan

        # Sanity check: ROE should be between -100% and 200%
        df.loc[df['roe'] < -100, 'roe'] = np.nan
        df.loc[df['roe'] > 200, 'roe'] = np.nan

        return df

    def _calculate_value(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate value metrics.

        We use Earnings Yield as the value proxy.
        Earnings Yield = Earnings / Price = 1 / P/E

        Higher Earnings Yield = cheaper stock (better value).
        """
        if 'trailing_pe' in df.columns:
            # Earnings Yield = 1 / P/E
            df['earnings_yield'] = (1 / df['trailing_pe']) * 100  # Convert to percentage

            # Handle edge cases
            df.loc[df['trailing_pe'] <= 0, 'earnings_yield'] = np.nan  # Negative earnings
            df.loc[df['trailing_pe'] > 100, 'earnings_yield'] = np.nan  # P/E too high (essentially no earnings)

        else:
            logger.error("Cannot calculate Earnings Yield - missing P/E ratio")
            df['earnings_yield'] = np.nan

        # Sanity check: Earnings Yield should be between -10% and 50%
        df.loc[df['earnings_yield'] < -10, 'earnings_yield'] = np.nan
        df.loc[df['earnings_yield'] > 50, 'earnings_yield'] = np.nan

        return df

    def _rank_stocks(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Rank stocks by quality and value.

        Rank 1 = best (highest ROE, highest Earnings Yield)
        """
        # Quality rank: Higher ROE is better
        df['quality_rank'] = df['roe'].rank(method='min', ascending=False).astype(int)

        # Value rank: Higher Earnings Yield is better (cheaper relative to earnings)
        df['value_rank'] = df['earnings_yield'].rank(method='min', ascending=False).astype(int)

        return df


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def calculate_magic_formula_score(
    fundamentals: pd.DataFrame,
    min_market_cap: float = 50_000_000,
    min_liquidity: float = 100_000,
    exclude_financials: bool = True
) -> pd.DataFrame:
    """
    One-liner function to calculate Magic Formula scores.

    Args:
        fundamentals: Fundamental data from YFinanceFetcher
        min_market_cap: Minimum market cap filter (default: $50M)
        min_liquidity: Minimum daily volume (default: 100k shares)
        exclude_financials: Exclude financial sector (default: True)

    Returns:
        DataFrame ranked by Magic Formula score

    Example:
        >>> from data.fetchers import YFinanceFetcher
        >>> from factors import calculate_magic_formula_score
        >>>
        >>> fetcher = YFinanceFetcher()
        >>> fundamentals = fetcher.get_fundamental_data(fetcher.get_universe())
        >>> scores = calculate_magic_formula_score(fundamentals)
        >>> print(scores.head(20))  # Top 20 stocks
    """
    calculator = MagicFormulaCalculator(
        min_market_cap=min_market_cap,
        min_liquidity=min_liquidity,
        exclude_financials=exclude_financials
    )
    return calculator.calculate(fundamentals)


def get_magic_formula_rankings(
    fundamentals: pd.DataFrame,
    top_n: int = 30,
    **kwargs
) -> List[str]:
    """
    Get top N stock tickers from Magic Formula ranking.

    Args:
        fundamentals: Fundamental data
        top_n: Number of top stocks to return (default: 30)
        **kwargs: Additional arguments for MagicFormulaCalculator

    Returns:
        List of ticker symbols

    Example:
        >>> tickers = get_magic_formula_rankings(fundamentals, top_n=20)
        >>> print(f"Top 20 stocks: {tickers}")
    """
    scores = calculate_magic_formula_score(fundamentals, **kwargs)

    if len(scores) == 0:
        logger.warning("No stocks in Magic Formula ranking!")
        return []

    top_stocks = scores.head(top_n)['ticker'].tolist()

    logger.info(f"Top {top_n} Magic Formula stocks:")
    for i, ticker in enumerate(top_stocks[:10], 1):
        logger.info(f"  {i}. {ticker}")

    if len(top_stocks) > 10:
        logger.info(f"  ... and {len(top_stocks) - 10} more")

    return top_stocks
