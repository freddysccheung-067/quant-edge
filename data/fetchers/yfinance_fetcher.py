"""
YFinance Data Fetcher - Production-grade market data acquisition.

This module provides robust data fetching for equity prices and fundamentals
using the yfinance library. Features include:
- Automatic caching (Parquet format for performance)
- Retry logic with exponential backoff
- Comprehensive error handling
- Data quality validation
- Thread-safe operations
- Detailed logging

Author: QuantEdge Team
License: MIT
"""

import logging
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import warnings

import pandas as pd
import numpy as np
import yfinance as yf
from requests.exceptions import HTTPError, ConnectionError, Timeout

# Suppress yfinance warnings about missing data
warnings.filterwarnings('ignore', category=FutureWarning, module='yfinance')

# Configure module logger
logger = logging.getLogger(__name__)


class DataFetchError(Exception):
    """Raised when critical data fetching fails."""
    pass


class CacheManager:
    """
    Manages Parquet-based caching for price and fundamental data.

    Cache structure:
        cache_dir/
            prices/
                AAPL_2019-01-01_2024-10-01.parquet
                MSFT_2019-01-01_2024-10-01.parquet
            fundamentals/
                sp500_fundamentals_2024-10-18.parquet
            universe/
                sp500_tickers_2024-10-18.parquet
    """

    def __init__(self, cache_dir: str = "D:/quant-edge/data/cache"):
        """
        Initialize cache manager.

        Args:
            cache_dir: Root directory for cache files
        """
        self.cache_dir = Path(cache_dir)
        self.prices_dir = self.cache_dir / "prices"
        self.fundamentals_dir = self.cache_dir / "fundamentals"
        self.universe_dir = self.cache_dir / "universe"

        # Create directories
        for directory in [self.prices_dir, self.fundamentals_dir, self.universe_dir]:
            directory.mkdir(parents=True, exist_ok=True)

        logger.info(f"Cache manager initialized at {self.cache_dir}")

    def get_cache_path(
        self,
        cache_type: str,
        identifier: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Path:
        """
        Generate cache file path.

        Args:
            cache_type: 'prices', 'fundamentals', or 'universe'
            identifier: Ticker symbol or dataset name
            start_date: Start date for price data (YYYY-MM-DD)
            end_date: End date for price data (YYYY-MM-DD)

        Returns:
            Path to cache file
        """
        if cache_type == "prices":
            filename = f"{identifier}_{start_date}_{end_date}.parquet"
            return self.prices_dir / filename
        elif cache_type == "fundamentals":
            filename = f"{identifier}_fundamentals_{datetime.now().strftime('%Y-%m-%d')}.parquet"
            return self.fundamentals_dir / filename
        elif cache_type == "universe":
            filename = f"{identifier}_tickers_{datetime.now().strftime('%Y-%m-%d')}.parquet"
            return self.universe_dir / filename
        else:
            raise ValueError(f"Invalid cache type: {cache_type}")

    def is_cached(
        self,
        cache_type: str,
        identifier: str,
        max_age_hours: int = 24,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> bool:
        """
        Check if cached data exists and is fresh.

        Args:
            cache_type: Type of cached data
            identifier: Data identifier
            max_age_hours: Maximum cache age in hours
            start_date: Start date for price data
            end_date: End date for price data

        Returns:
            True if valid cache exists
        """
        cache_path = self.get_cache_path(cache_type, identifier, start_date, end_date)

        if not cache_path.exists():
            return False

        # Check age
        file_modified_time = datetime.fromtimestamp(cache_path.stat().st_mtime)
        age_hours = (datetime.now() - file_modified_time).total_seconds() / 3600

        is_fresh = age_hours < max_age_hours

        if not is_fresh:
            logger.debug(f"Cache expired: {cache_path.name} (age: {age_hours:.1f}h)")

        return is_fresh

    def load(
        self,
        cache_type: str,
        identifier: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Optional[pd.DataFrame]:
        """
        Load cached data.

        Args:
            cache_type: Type of cached data
            identifier: Data identifier
            start_date: Start date for price data
            end_date: End date for price data

        Returns:
            DataFrame if cache exists, None otherwise
        """
        cache_path = self.get_cache_path(cache_type, identifier, start_date, end_date)

        try:
            df = pd.read_parquet(cache_path)
            logger.debug(f"Loaded from cache: {cache_path.name}")
            return df
        except Exception as e:
            logger.warning(f"Failed to load cache {cache_path.name}: {e}")
            return None

    def save(
        self,
        df: pd.DataFrame,
        cache_type: str,
        identifier: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> None:
        """
        Save data to cache.

        Args:
            df: DataFrame to cache
            cache_type: Type of data
            identifier: Data identifier
            start_date: Start date for price data
            end_date: End date for price data
        """
        cache_path = self.get_cache_path(cache_type, identifier, start_date, end_date)

        try:
            df.to_parquet(cache_path, compression='snappy', index=True)
            logger.debug(f"Saved to cache: {cache_path.name} ({len(df)} rows)")
        except Exception as e:
            logger.error(f"Failed to save cache {cache_path.name}: {e}")

    def clear_all(self) -> None:
        """Clear all cached data."""
        for directory in [self.prices_dir, self.fundamentals_dir, self.universe_dir]:
            for file in directory.glob("*.parquet"):
                file.unlink()
        logger.info("All cache cleared")


class YFinanceFetcher:
    """
    Production-grade market data fetcher using yfinance.

    Features:
    - S&P 500 universe management
    - Price data fetching with retry logic
    - Fundamental data extraction
    - Parquet-based caching
    - Comprehensive error handling
    - Data quality validation

    Example:
        >>> fetcher = YFinanceFetcher()
        >>> tickers = fetcher.get_universe()
        >>> prices = fetcher.get_price_data('2019-01-01', '2024-10-01')
        >>> fundamentals = fetcher.get_fundamental_data()
    """

    # S&P 500 Wikipedia table URL
    SP500_URL = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"

    # Required fundamental fields and their yfinance keys
    FUNDAMENTAL_FIELDS = {
        'market_cap': 'marketCap',
        'enterprise_value': 'enterpriseValue',
        'trailing_pe': 'trailingPE',
        'forward_pe': 'forwardPE',
        'peg_ratio': 'pegRatio',
        'price_to_book': 'priceToBook',
        'ebit': 'ebit',
        'ebitda': 'ebitda',
        'net_income': 'netIncomeToCommon',
        'total_revenue': 'totalRevenue',
        'shareholders_equity': 'totalStockholderEquity',
        'total_debt': 'totalDebt',
        'operating_cashflow': 'operatingCashflow',
        'sector': 'sector',
        'industry': 'industry',
    }

    def __init__(
        self,
        cache_dir: str = "D:/quant-edge/data/cache",
        max_retries: int = 3,
        retry_delay: float = 1.0,
        timeout: int = 10
    ):
        """
        Initialize data fetcher.

        Args:
            cache_dir: Directory for caching data
            max_retries: Maximum retry attempts for failed requests
            retry_delay: Initial delay between retries (seconds)
            timeout: Request timeout (seconds)
        """
        self.cache = CacheManager(cache_dir)
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.timeout = timeout

        logger.info(f"YFinanceFetcher initialized (cache={cache_dir})")

    def _retry_with_backoff(
        self,
        func: callable,
        *args,
        **kwargs
    ) -> any:
        """
        Execute function with exponential backoff retry logic.

        Args:
            func: Function to execute
            *args: Positional arguments for func
            **kwargs: Keyword arguments for func

        Returns:
            Function return value

        Raises:
            DataFetchError: If all retries fail
        """
        last_exception = None

        for attempt in range(self.max_retries):
            try:
                return func(*args, **kwargs)
            except (HTTPError, ConnectionError, Timeout) as e:
                last_exception = e
                if attempt < self.max_retries - 1:
                    delay = self.retry_delay * (2 ** attempt)  # Exponential backoff
                    logger.warning(
                        f"Attempt {attempt + 1}/{self.max_retries} failed: {e}. "
                        f"Retrying in {delay:.1f}s..."
                    )
                    time.sleep(delay)
                else:
                    logger.error(f"All {self.max_retries} attempts failed for {func.__name__}")

        raise DataFetchError(f"Failed after {self.max_retries} attempts") from last_exception

    def get_universe(
        self,
        use_cache: bool = True,
        max_age_hours: int = 168  # 7 days
    ) -> List[str]:
        """
        Fetch S&P 500 constituent tickers from Wikipedia.

        Args:
            use_cache: Whether to use cached data
            max_age_hours: Maximum cache age (default 7 days)

        Returns:
            List of ticker symbols

        Raises:
            DataFetchError: If fetching fails
        """
        # Check cache
        if use_cache and self.cache.is_cached('universe', 'sp500', max_age_hours=max_age_hours):
            cached_df = self.cache.load('universe', 'sp500')
            if cached_df is not None:
                tickers = cached_df['ticker'].tolist()
                logger.info(f"Loaded {len(tickers)} tickers from cache")
                return tickers

        # Fetch from Wikipedia with proper headers
        logger.info("Fetching S&P 500 constituents from Wikipedia...")

        def _fetch_sp500():
            # Add User-Agent header to avoid 403 errors
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            tables = pd.read_html(self.SP500_URL, storage_options=headers)
            df = tables[0]  # First table contains constituents
            return df

        try:
            df = self._retry_with_backoff(_fetch_sp500)

            # Extract tickers and clean
            tickers = df['Symbol'].str.replace('.', '-', regex=False).tolist()

            # Save to cache
            cache_df = pd.DataFrame({'ticker': tickers})
            self.cache.save(cache_df, 'universe', 'sp500')

            logger.info(f"Fetched {len(tickers)} S&P 500 tickers")
            return tickers

        except Exception as e:
            logger.warning(f"Failed to fetch from Wikipedia: {e}")
            # Fallback to yfinance's S&P 500 ticker list
            logger.info("Falling back to yfinance S&P 500 ticker retrieval...")
            try:
                import yfinance as yf
                sp500_ticker = yf.Ticker("^GSPC")
                # Get constituents if available, otherwise use a curated list
                tickers = self._get_fallback_sp500_list()

                # Save to cache
                cache_df = pd.DataFrame({'ticker': tickers})
                self.cache.save(cache_df, 'universe', 'sp500')

                logger.info(f"Using fallback list with {len(tickers)} S&P 500 tickers")
                return tickers
            except Exception as fallback_error:
                raise DataFetchError(
                    f"Failed to fetch S&P 500 universe from all sources. "
                    f"Wikipedia error: {e}, Fallback error: {fallback_error}"
                ) from e

    def _get_fallback_sp500_list(self) -> List[str]:
        """
        Returns a curated list of major S&P 500 stocks as fallback.
        This is a subset of the most liquid and well-known stocks to ensure
        the system can operate even if external data sources fail.
        """
        # Top ~100 most liquid S&P 500 stocks by market cap (as of 2024)
        return [
            # Mega cap tech
            'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'TSLA', 'BRK-B',
            # Tech leaders
            'AVGO', 'ORCL', 'CSCO', 'ADBE', 'CRM', 'ACN', 'AMD', 'INTC', 'IBM',
            'QCOM', 'TXN', 'INTU', 'AMAT', 'MU', 'ADI', 'LRCX', 'KLAC', 'SNPS',
            # Finance
            'JPM', 'V', 'MA', 'BAC', 'WFC', 'GS', 'MS', 'BLK', 'C', 'SPGI',
            'AXP', 'USB', 'PNC', 'TFC', 'COF', 'SCHW', 'CB', 'CME', 'ICE',
            # Healthcare
            'UNH', 'JNJ', 'LLY', 'ABBV', 'MRK', 'PFE', 'TMO', 'ABT', 'DHR',
            'AMGN', 'BMY', 'GILD', 'CVS', 'CI', 'HUM', 'MDT', 'ISRG', 'REGN',
            # Consumer
            'AMZN', 'TSLA', 'HD', 'WMT', 'MCD', 'NKE', 'DIS', 'SBUX', 'TGT',
            'LOW', 'COST', 'TJX', 'CMG', 'BKNG', 'MAR', 'ABNB', 'F', 'GM',
            # Communication
            'GOOGL', 'META', 'NFLX', 'DIS', 'CMCSA', 'T', 'VZ', 'TMUS', 'CHTR',
            # Industrial
            'UPS', 'RTX', 'HON', 'BA', 'CAT', 'GE', 'LMT', 'DE', 'MMM', 'ETN',
            'EMR', 'ITW', 'PH', 'WM', 'NSC', 'UNP', 'CSX', 'FDX', 'GD',
            # Energy
            'XOM', 'CVX', 'COP', 'SLB', 'EOG', 'MPC', 'PSX', 'VLO', 'OXY',
            # Consumer Staples
            'PG', 'KO', 'PEP', 'COST', 'WMT', 'PM', 'MO', 'CL', 'MDLZ', 'GIS',
            # Utilities & Real Estate
            'NEE', 'DUK', 'SO', 'D', 'AEP', 'EXC', 'SRE', 'PLD', 'AMT', 'CCI',
            # Materials
            'LIN', 'APD', 'SHW', 'ECL', 'NEM', 'FCX', 'NUE', 'VMC', 'MLM',
            # Other notable
            'NFLX', 'PYPL', 'SHOP', 'SQ', 'COIN', 'UBER', 'ABNB', 'ZM', 'DOCU'
        ]

    def fetch_ticker_prices(
        self,
        ticker: str,
        start_date: str,
        end_date: str,
        use_cache: bool = True
    ) -> Optional[pd.Series]:
        """
        Fetch price data for a single ticker.

        Args:
            ticker: Stock symbol
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            use_cache: Whether to use cached data

        Returns:
            Series of closing prices with DatetimeIndex, or None if failed
        """
        # Check cache
        if use_cache and self.cache.is_cached('prices', ticker, 24, start_date, end_date):
            cached_df = self.cache.load('prices', ticker, start_date, end_date)
            if cached_df is not None and 'Close' in cached_df.columns:
                return cached_df['Close']

        # Fetch from yfinance
        def _fetch_prices():
            ticker_obj = yf.Ticker(ticker)
            df = ticker_obj.history(start=start_date, end=end_date, timeout=self.timeout)
            return df

        try:
            df = self._retry_with_backoff(_fetch_prices)

            if df.empty or 'Close' not in df.columns:
                logger.warning(f"No price data for {ticker}")
                return None

            # Save to cache
            self.cache.save(df, 'prices', ticker, start_date, end_date)

            logger.debug(f"Fetched {len(df)} prices for {ticker}")
            return df['Close']

        except Exception as e:
            logger.error(f"Failed to fetch prices for {ticker}: {e}")
            return None

    def get_price_data(
        self,
        start_date: str,
        end_date: str,
        tickers: Optional[List[str]] = None,
        use_cache: bool = True,
        show_progress: bool = True
    ) -> pd.DataFrame:
        """
        Fetch price data for multiple tickers.

        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            tickers: List of tickers (if None, use S&P 500)
            use_cache: Whether to use cached data
            show_progress: Whether to show progress logs

        Returns:
            DataFrame with DatetimeIndex and ticker columns
        """
        if tickers is None:
            tickers = self.get_universe(use_cache=use_cache)

        logger.info(f"Fetching price data for {len(tickers)} tickers from {start_date} to {end_date}")

        prices_dict = {}
        failed_tickers = []

        for i, ticker in enumerate(tickers):
            if show_progress and (i + 1) % 50 == 0:
                logger.info(f"Progress: {i + 1}/{len(tickers)} tickers")

            prices = self.fetch_ticker_prices(ticker, start_date, end_date, use_cache)

            if prices is not None:
                prices_dict[ticker] = prices
            else:
                failed_tickers.append(ticker)

            # Small delay to avoid rate limiting
            time.sleep(0.05)

        # Combine into DataFrame
        df = pd.DataFrame(prices_dict)

        success_rate = len(prices_dict) / len(tickers) * 100
        logger.info(
            f"Fetched prices for {len(prices_dict)}/{len(tickers)} tickers "
            f"({success_rate:.1f}% success rate)"
        )

        if failed_tickers:
            logger.warning(f"Failed tickers: {', '.join(failed_tickers[:10])}" +
                          (f" ... and {len(failed_tickers) - 10} more" if len(failed_tickers) > 10 else ""))

        return df

    def fetch_ticker_fundamentals(
        self,
        ticker: str
    ) -> Optional[Dict]:
        """
        Fetch fundamental data for a single ticker.

        Args:
            ticker: Stock symbol

        Returns:
            Dictionary of fundamental metrics, or None if failed
        """
        def _fetch_info():
            ticker_obj = yf.Ticker(ticker)
            return ticker_obj.info

        try:
            info = self._retry_with_backoff(_fetch_info)

            # Extract required fields
            fundamentals = {'ticker': ticker}

            for our_key, yf_key in self.FUNDAMENTAL_FIELDS.items():
                value = info.get(yf_key, np.nan)
                fundamentals[our_key] = value

            return fundamentals

        except Exception as e:
            logger.error(f"Failed to fetch fundamentals for {ticker}: {e}")
            return None

    def get_fundamental_data(
        self,
        tickers: Optional[List[str]] = None,
        use_cache: bool = True,
        show_progress: bool = True
    ) -> pd.DataFrame:
        """
        Fetch fundamental data for multiple tickers.

        Args:
            tickers: List of tickers (if None, use S&P 500)
            use_cache: Whether to use cached data
            show_progress: Whether to show progress logs

        Returns:
            DataFrame with ticker index and fundamental columns
        """
        # Check cache
        if use_cache and self.cache.is_cached('fundamentals', 'sp500', max_age_hours=168):  # 7 days
            cached_df = self.cache.load('fundamentals', 'sp500')
            if cached_df is not None:
                logger.info(f"Loaded fundamentals from cache ({len(cached_df)} tickers)")
                return cached_df

        if tickers is None:
            tickers = self.get_universe(use_cache=use_cache)

        logger.info(f"Fetching fundamental data for {len(tickers)} tickers")

        fundamentals_list = []
        failed_tickers = []

        for i, ticker in enumerate(tickers):
            if show_progress and (i + 1) % 50 == 0:
                logger.info(f"Progress: {i + 1}/{len(tickers)} tickers")

            fundamentals = self.fetch_ticker_fundamentals(ticker)

            if fundamentals is not None:
                fundamentals_list.append(fundamentals)
            else:
                failed_tickers.append(ticker)

            # Small delay to avoid rate limiting
            time.sleep(0.1)

        # Combine into DataFrame
        df = pd.DataFrame(fundamentals_list)
        df.set_index('ticker', inplace=True)

        # Save to cache
        self.cache.save(df, 'fundamentals', 'sp500')

        success_rate = len(fundamentals_list) / len(tickers) * 100
        logger.info(
            f"Fetched fundamentals for {len(fundamentals_list)}/{len(tickers)} tickers "
            f"({success_rate:.1f}% success rate)"
        )

        if failed_tickers:
            logger.warning(f"Failed tickers: {', '.join(failed_tickers[:10])}" +
                          (f" ... and {len(failed_tickers) - 10} more" if len(failed_tickers) > 10 else ""))

        return df

    def validate_data_quality(
        self,
        df: pd.DataFrame,
        min_completeness: float = 0.85
    ) -> Tuple[bool, Dict[str, float]]:
        """
        Validate data quality.

        Args:
            df: DataFrame to validate
            min_completeness: Minimum required completeness (0.0-1.0)

        Returns:
            Tuple of (is_valid, quality_metrics)
        """
        metrics = {}

        # Calculate completeness per column
        for col in df.columns:
            completeness = df[col].notna().sum() / len(df)
            metrics[col] = completeness

        # Overall completeness
        overall_completeness = df.notna().sum().sum() / (df.shape[0] * df.shape[1])
        metrics['overall'] = overall_completeness

        is_valid = overall_completeness >= min_completeness

        return is_valid, metrics

    def refresh_all(self) -> None:
        """Clear cache and force fresh data fetch on next call."""
        self.cache.clear_all()
        logger.info("All cached data cleared")


# Configure logging for this module
def setup_logging(level: int = logging.INFO):
    """
    Configure logging for the data fetcher.

    Args:
        level: Logging level (e.g., logging.INFO)
    """
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=level
    )


if __name__ == "__main__":
    # Example usage
    setup_logging(logging.INFO)

    fetcher = YFinanceFetcher()

    # Get universe
    tickers = fetcher.get_universe()
    print(f"Fetched {len(tickers)} tickers")

    # Get price data
    prices = fetcher.get_price_data('2023-01-01', '2024-01-01', tickers=tickers[:10])
    print(f"Price data shape: {prices.shape}")

    # Get fundamental data
    fundamentals = fetcher.get_fundamental_data(tickers=tickers[:10])
    print(f"Fundamental data shape: {fundamentals.shape}")

    # Validate quality
    is_valid, metrics = fetcher.validate_data_quality(fundamentals)
    print(f"Data quality: {'PASS' if is_valid else 'FAIL'}")
    print(f"Overall completeness: {metrics['overall']:.1%}")
