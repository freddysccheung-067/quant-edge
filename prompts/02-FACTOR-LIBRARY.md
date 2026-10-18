# ONE-SHOT PROMPT: Factor Library (Magic Formula)

## Objective
Implement a clean, vectorized factor calculation library for the Magic Formula strategy with proper normalization, ranking, and outlier handling.

## Technical Specifications

**Files**: 
- `D:\quant-edge\factors\value.py` (value factors)
- `D:\quant-edge\factors\quality.py` (quality factors)
- `D:\quant-edge\factors\composite.py` (factor combination)
- `D:\quant-edge\factors\__init__.py` (exports)

**Dependencies**: `pandas`, `numpy`, `scipy`  
**Python**: 3.11+ with type hints

## Factor Definitions (Magic Formula)

### Quality Factor: Return on Equity (ROE)
```python
def calculate_roe(fundamentals: pd.DataFrame) -> pd.Series:
    """
    ROE = Net Income / Shareholders' Equity
    
    Higher is better. Measures how efficiently company generates profit.
    
    Args:
        fundamentals: DataFrame with columns ['net_income', 'shareholders_equity']
        
    Returns:
        Series with index = tickers, values = ROE (ratio, not percentage)
        
    Handling:
    - Negative equity: Set to NaN (company has more liabilities than assets)
    - Zero equity: Set to NaN
    - Extreme values: Winsorize at 1st and 99th percentile (cap outliers)
    - Valid range after winsorization: typically -0.5 to 2.0
    """
```

**Implementation notes**:
- Use `pd.Series.clip()` for winsorization
- Check for division by zero before calculating
- Inf values become NaN

### Value Factor: Earnings Yield
```python
def calculate_earnings_yield(fundamentals: pd.DataFrame) -> pd.Series:
    """
    Earnings Yield = EBIT / Enterprise Value
    
    Higher is better. Inverse of P/E ratio but uses operating income.
    
    Args:
        fundamentals: DataFrame with columns ['ebit', 'enterprise_value']
        
    Returns:
        Series with index = tickers, values = earnings yield (ratio)
        
    Handling:
    - Negative EBIT: Set to NaN (unprofitable, avoid)
    - Zero/Negative EV: Set to NaN (invalid)
    - Winsorize at 1st and 99th percentile
    - Valid range: typically 0.01 to 0.50 (1% to 50% yield)
    """
```

**Alternative (if EBIT data is poor)**:
```python
def calculate_pe_ratio(fundamentals: pd.DataFrame) -> pd.Series:
    """
    P/E = Market Cap / Net Income
    Then invert to get earnings yield: 1 / (P/E)
    """
```

## Ranking & Normalization

### Cross-Sectional Ranking
```python
def rank_factor(factor_series: pd.Series, ascending: bool = False) -> pd.Series:
    """
    Convert factor values to ranks (1 = best, N = worst).
    
    Args:
        factor_series: Raw factor values (may contain NaN)
        ascending: If True, lower values are better (e.g., P/E ratio)
                   If False, higher values are better (e.g., ROE)
    
    Returns:
        Series with same index, values = ranks (1 to N)
        NaN values are excluded from ranking, remain NaN
    
    Method: Use pandas .rank(method='average', na_option='keep')
    """
```

### Z-Score Normalization (Optional Enhancement)
```python
def zscore_normalize(factor_series: pd.Series) -> pd.Series:
    """
    Z-score: (value - mean) / std
    
    Centers factor at 0, scales by standard deviation.
    Useful for combining factors with different units.
    
    Returns:
        Normalized series (mean ≈ 0, std ≈ 1)
    """
```

## Composite Factor (Magic Formula Score)

**File**: `D:\quant-edge\factors\composite.py`

```python
def magic_formula_score(fundamentals: pd.DataFrame) -> pd.DataFrame:
    """
    Combine quality (ROE) and value (Earnings Yield) into single score.
    
    Process:
    1. Calculate ROE for all stocks
    2. Calculate Earnings Yield for all stocks
    3. Rank each factor independently (higher = better rank)
    4. Average the two ranks: magic_rank = (roe_rank + ey_rank) / 2
    5. Sort by magic_rank (lower rank = better stock)
    
    Args:
        fundamentals: DataFrame from data fetcher
        
    Returns:
        DataFrame with columns:
        - ticker (index)
        - roe: Raw ROE value
        - earnings_yield: Raw EY value
        - roe_rank: Rank (1 = best)
        - ey_rank: Rank (1 = best)
        - magic_rank: Combined rank (1 = best)
        - percentile: Magic rank as percentile (100 = best)
        
    Sorted by magic_rank ascending (best stocks first)
    
    Stocks with NaN in either factor are excluded from final ranking.
    """
```

**Example output**:
```
ticker    roe    earnings_yield  roe_rank  ey_rank  magic_rank  percentile
NVDA     0.45        0.08          5         12        8.5          98
AAPL     0.38        0.06         15         25       20.0          96
MSFT     0.42        0.05         10         45       27.5          94
...
```

## Filter Functions

```python
def apply_universe_filters(
    df: pd.DataFrame,
    min_market_cap: float = 2e9,  # $2B
    min_roe: float = 0.10,  # 10%
    min_earnings_yield: float = 0.03,  # 3%
) -> pd.DataFrame:
    """
    Filter stocks that don't meet minimum quality criteria.
    
    Removes:
    - Market cap < $2B (illiquid small caps)
    - ROE < 10% (low quality)
    - Earnings Yield < 3% (too expensive)
    - Any stock with NaN in critical fields
    
    Returns: Filtered DataFrame (same columns as input)
    """
```

## Sector Neutralization (Optional Enhancement)

```python
def sector_neutral_ranks(
    df: pd.DataFrame,
    sector_column: str = 'sector'
) -> pd.DataFrame:
    """
    Rank stocks within their sector instead of universe-wide.
    
    Prevents sector concentration (e.g., all tech stocks in 2024).
    
    Process:
    1. Group by sector
    2. Rank within each sector
    3. Concatenate results
    
    Returns: DataFrame with sector-neutral ranks
    """
```

## Validation & Diagnostics

```python
def factor_diagnostics(df: pd.DataFrame) -> dict:
    """
    Calculate factor quality metrics.
    
    Returns dict with:
    - 'completeness': % of stocks with valid scores
    - 'roe_distribution': {'mean', 'median', 'std', 'min', 'max'}
    - 'ey_distribution': {'mean', 'median', 'std', 'min', 'max'}
    - 'correlation': Correlation between ROE and EY (should be low)
    - 'top_10_tickers': List of best-ranked stocks
    - 'bottom_10_tickers': List of worst-ranked stocks
    """
```

## Example Usage

```python
from factors.composite import magic_formula_score
from data.fetchers import DataFetcher

# Fetch data
fetcher = DataFetcher()
fundamentals = fetcher.get_fundamental_data()

# Calculate Magic Formula scores
scored = magic_formula_score(fundamentals)

# Get top 15 stocks
top_15 = scored.head(15)
print(top_15[['roe', 'earnings_yield', 'magic_rank']])

# Apply filters
from factors.composite import apply_universe_filters
filtered = apply_universe_filters(scored, min_market_cap=5e9)
```

## Critical Implementation Details

### Winsorization Example
```python
def winsorize(series: pd.Series, limits=(0.01, 0.01)) -> pd.Series:
    """
    Cap extreme values at percentiles.
    limits=(0.01, 0.01) means cap at 1st and 99th percentile.
    """
    lower = series.quantile(limits[0])
    upper = series.quantile(1 - limits[1])
    return series.clip(lower=lower, upper=upper)
```

### Handling Missing Data
- **Strategy**: Exclude stocks with missing data from ranking
- **DO NOT**: Fill with median/mean (introduces bias)
- **DO NOT**: Drop entirely (want to keep in dataset for logging)
- **DO**: Keep NaN, exclude from `.rank()`, report % completeness

### Performance Optimization
- Use vectorized pandas operations (no loops)
- Cache intermediate calculations if reused
- Target: Process 500 stocks in <1 second

## Deliverables

1. **`value.py`**: Earnings yield, P/E ratio calculations (~100 lines)
2. **`quality.py`**: ROE, ROIC calculations (~100 lines)
3. **`composite.py`**: Magic formula combination, filters, diagnostics (~200 lines)
4. **`__init__.py`**: Export main functions
5. **`test_factors.py`**: Unit tests (optional but recommended)

## Success Criteria

- [ ] Magic formula score calculated for >400 stocks
- [ ] Top-ranked stocks have ROE > 15% and EY > 5%
- [ ] Correlation between ROE and EY is < 0.5 (factors are independent)
- [ ] No inf or -inf values in output
- [ ] Runs in <2 seconds for 500 stocks
- [ ] Diagnostics report shows >85% data completeness
- [ ] Code is fully vectorized (no for loops over tickers)

## Academic References (For Understanding)

**Magic Formula**:
- Joel Greenblatt, "The Little Book That Beats the Market" (2005)
- Formula: Rank(ROE) + Rank(Earnings Yield), buy top-ranked

**Why It Works**:
- ROE captures quality (avoid junk companies)
- Earnings Yield captures value (avoid overpaying)
- Combination finds "good companies at fair prices"

## Time Estimate
**2-3 hours** for experienced quant developer

---

**GO BUILD IT.** This is where the alpha comes from. Get the math right.
