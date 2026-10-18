# ONE-SHOT PROMPT: Data Fetcher Module

## Objective
Build a robust, production-grade data fetching system for S&P 500 stocks using yfinance with intelligent caching, error handling, and fundamental data extraction.

## Technical Specifications

**File**: `D:\quant-edge\data\fetchers\yfinance_fetcher.py`

**Requirements**:
- Python 3.11+ with type hints (PEP 585 style: `list[str]` not `List[str]`)
- Dependencies: `yfinance`, `pandas`, `numpy`, `requests`, `beautifulsoup4`
- Cache data to `D:\quant-edge\data\cache\` using parquet format (NOT pickle - better versioning)
- Cache expiry: 24 hours for prices, 7 days for fundamentals
- Graceful degradation: if one stock fails, continue with others

## Core Functions to Implement

### 1. S&P 500 Ticker Fetching
```python
def get_sp500_tickers() -> list[str]:
    """
    Scrape current S&P 500 tickers from Wikipedia.
    Fallback to hardcoded list if scraping fails.
    Cache result for 7 days.
    
    Returns: List of ticker symbols (e.g., ['AAPL', 'MSFT', ...])
    """
```

**Data source**: `https://en.wikipedia.org/wiki/List_of_S%26P_500_companies`  
**Fallback**: If scraping fails, use static list of top 100 S&P 500 by market cap (hardcode these)

### 2. Price Data Fetching
```python
def fetch_prices(
    tickers: list[str],
    start_date: str,
    end_date: str,
    use_cache: bool = True
) -> pd.DataFrame:
    """
    Fetch adjusted close prices for multiple tickers.
    
    Args:
        tickers: List of stock symbols
        start_date: 'YYYY-MM-DD' format
        end_date: 'YYYY-MM-DD' format
        use_cache: Whether to use cached data
    
    Returns:
        DataFrame with DatetimeIndex, columns = tickers, values = adjusted close
        Missing data filled with forward-fill then backward-fill
    """
```

**Critical details**:
- Use `yf.download(tickers, start, end, group_by='ticker', progress=False)['Adj Close']`
- Handle ticker failures gracefully (log warning, exclude from results)
- Cache file: `cache/prices_{start}_{end}.parquet`
- If cached file exists and is <24h old, load it
- Round prices to 4 decimal places

### 3. Fundamental Data Fetching
```python
def fetch_fundamentals(tickers: list[str], use_cache: bool = True) -> pd.DataFrame:
    """
    Fetch key fundamental metrics for Magic Formula calculation.
    
    Required fields per ticker:
    - market_cap: Market capitalization
    - enterprise_value: EV = Market Cap + Total Debt - Cash
    - ebit: Earnings Before Interest & Tax (TTM)
    - net_income: Net income (TTM)
    - total_debt: Short-term + long-term debt
    - cash: Cash and equivalents
    - shareholders_equity: Book value of equity
    - revenue: Total revenue (TTM)
    
    Returns:
        DataFrame with index = tickers, columns = fundamental fields
        NaN for missing data (DO NOT drop tickers with missing data)
    """
```

**Data extraction from yfinance**:
```python
ticker_obj = yf.Ticker(symbol)
info = ticker_obj.info
financials = ticker_obj.financials  # Income statement
balance_sheet = ticker_obj.balance_sheet

# Extract (with fallbacks):
market_cap = info.get('marketCap', np.nan)
enterprise_value = info.get('enterpriseValue', np.nan)
ebit = info.get('ebit', np.nan)
# ... etc
```

**Cache**: `cache/fundamentals_{today}.parquet` (7-day expiry)

### 4. Cache Management
```python
def is_cache_valid(cache_path: str, max_age_hours: int = 24) -> bool:
    """Check if cache file exists and is younger than max_age_hours"""

def save_cache(df: pd.DataFrame, cache_path: str) -> None:
    """Save DataFrame to parquet with metadata"""

def load_cache(cache_path: str) -> pd.DataFrame | None:
    """Load cached parquet, return None if doesn't exist"""
```

### 5. Main Interface
```python
class DataFetcher:
    """Main interface for data fetching operations"""
    
    def __init__(self, cache_dir: str = "D:/quant-edge/data/cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def get_universe(self) -> list[str]:
        """Get S&P 500 ticker list"""
    
    def get_price_data(
        self, 
        start_date: str, 
        end_date: str,
        tickers: list[str] | None = None,
        use_cache: bool = True
    ) -> pd.DataFrame:
        """Fetch price data for universe or specific tickers"""
    
    def get_fundamental_data(
        self,
        tickers: list[str] | None = None,
        use_cache: bool = True
    ) -> pd.DataFrame:
        """Fetch fundamental data for universe or specific tickers"""
    
    def refresh_all(self) -> None:
        """Force refresh all cached data"""
```

## Error Handling Requirements

1. **Network Errors**: Retry up to 3 times with exponential backoff (1s, 2s, 4s)
2. **Missing Data**: Log warning, set to NaN, continue processing
3. **Malformed Data**: Catch ValueError/TypeError, log, set to NaN
4. **Rate Limiting**: If yfinance throttles, sleep 5s and retry

## Validation Requirements

**Include this test function**:
```python
def validate_data_quality(prices: pd.DataFrame, fundamentals: pd.DataFrame) -> dict:
    """
    Run data quality checks and return report.
    
    Checks:
    - Price data: % missing values, date range coverage
    - Fundamentals: % complete records, field coverage
    - Outliers: Detect extreme values (>3 std devs)
    
    Returns: Dict with keys ['prices_missing_pct', 'fundamentals_complete_pct', 'outlier_count']
    """
```

## Logging

Use Python `logging` module:
```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
```

Log:
- INFO: Successful cache loads, data fetches
- WARNING: Missing data, failed tickers
- ERROR: Network failures, parsing errors

## Output Example

After running:
```python
fetcher = DataFetcher()
prices = fetcher.get_price_data('2019-01-01', '2024-10-01')
fundamentals = fetcher.get_fundamental_data()
```

**Prices DataFrame**:
```
            AAPL      MSFT      GOOGL     ...
2019-01-02  157.92    101.12    1,045.23  ...
2019-01-03  142.19     99.95    1,016.55  ...
...
```

**Fundamentals DataFrame**:
```
       market_cap  enterprise_value     ebit  net_income  total_debt      cash  shareholders_equity   revenue
AAPL   2.8e12      2.7e12              120e9    95e9       110e9      50e9       60e9                390e9
MSFT   2.5e12      2.4e12              110e9    88e9       75e9       130e9      200e9               230e9
...
```

## Deliverables

1. **`yfinance_fetcher.py`** (main module, ~400-500 lines)
2. **`cache.py`** (cache utilities, ~100 lines)
3. **`__init__.py`** (export DataFetcher class)
4. **`requirements.txt`** (dependencies):
   ```
   yfinance>=0.2.40
   pandas>=2.1.0
   numpy>=1.24.0
   requests>=2.31.0
   beautifulsoup4>=4.12.0
   pyarrow>=14.0.0  # For parquet support
   ```

## Success Criteria

- [ ] Can fetch S&P 500 ticker list successfully
- [ ] Can fetch 5 years of price data for 500 stocks in <2 minutes
- [ ] Cache reduces subsequent fetches to <5 seconds
- [ ] Fundamental data includes all 8 required fields
- [ ] Gracefully handles at least 10% ticker failures
- [ ] Data quality report shows >90% completeness
- [ ] No crashes on network errors or missing data

## Code Quality Standards

- Type hints on all functions
- Docstrings (Google style) for all public functions
- No hardcoded paths (use Path object, configurable)
- PEP 8 compliant (max line 100 chars)
- No print statements (use logging)
- Defensive programming: assume API can fail at any time

## Time Estimate
**3-4 hours** for experienced Python developer

---

**GO BUILD IT.** This is the foundation of everything else. Make it rock-solid.
