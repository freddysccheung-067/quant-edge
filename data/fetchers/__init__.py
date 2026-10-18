"""
Data fetching package for QuantEdge.

Provides robust market data acquisition with caching, retry logic,
and comprehensive error handling.
"""

from .yfinance_fetcher import (
    YFinanceFetcher,
    DataFetchError,
    CacheManager,
    setup_logging
)

__all__ = [
    'YFinanceFetcher',
    'DataFetchError',
    'CacheManager',
    'setup_logging',
]

# Version
__version__ = '1.0.0'
