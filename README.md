# QuantEdge Trading System

**Production-grade quantitative trading system combining Magic Formula factor investing with modern portfolio optimization.**

Built for the BestBrokers investment competition, designed to scale to real-world trading.

---

## 🎯 Quick Start (2 Minutes to Trading Signals)

```bash
# 1. Setup environment
cd D:\quant-edge
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

# 2. Generate trading signals
python run_system.py --method max_sharpe --positions 20 --capital 25000

# 3. Check output
# Open trading_signals.csv for your actionable buy list
```

**Output**: `trading_signals.csv` with exact shares to buy for each stock.

---

## 📊 What This System Does

### Strategy Overview

**Magic Formula (Joel Greenblatt)** + **Modern Portfolio Theory**

1. **Universe**: S&P 500 stocks
2. **Factor Selection**: Quality (ROE) × Value (Earnings Yield)
3. **Portfolio Construction**: Risk-optimized allocation
4. **Rebalancing**: Weekly/monthly signals

### Expected Performance

- **Greenblatt's track record**: 30.8% annual return (1988-2004)
- **Academic validation**: 10-15% alpha vs S&P 500
- **Our system**: Targets 15-20% annual return with 15% volatility

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     DATA FETCHING                            │
│  YFinance → S&P 500 Universe + Fundamentals + Prices        │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│                  FACTOR ANALYSIS                             │
│  Magic Formula: ROE (Quality) × Earnings Yield (Value)      │
│  → Rank 500+ stocks → Top 40 candidates                     │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│               PORTFOLIO OPTIMIZATION                         │
│  Skfolio: Mean-Variance / Max Sharpe / HRP                  │
│  → 20 positions with optimized weights                      │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│                 TRADING SIGNALS                              │
│  Ticker | Shares | Price | Cost | Weight | MF Rank          │
│  Output: trading_signals.csv                                 │
└─────────────────────────────────────────────────────────────┘
```

---

## 📁 Project Structure

```
quant-edge/
├── data/
│   ├── fetchers.py          # YFinance data fetching
│   └── cache/               # Cached data (gitignored)
│
├── factors/
│   ├── magic_formula.py     # Magic Formula implementation
│   └── __init__.py
│
├── portfolio/
│   ├── optimizer.py         # Skfolio portfolio optimization
│   └── __init__.py
│
├── run_system.py            # Main entry point
├── test_data_fetcher.py     # Data fetcher tests
├── test_magic_formula.py    # Factor library tests
│
├── requirements.txt
├── README.md
└── .gitignore
```

---

## 🧪 Testing

### Test Suite 1: Data Fetcher

```bash
python test_data_fetcher.py
```

**Tests**:
- S&P 500 universe fetching (500+ tickers)
- Price data fetching (OHLCV)
- Fundamental data (P/E, ROE, market cap, etc.)
- Caching and error handling

### Test Suite 2: Magic Formula

```bash
python test_magic_formula.py
```

**Tests**:
- ROE and Earnings Yield calculation
- Ranking logic
- Edge cases (negative earnings, missing data)
- Benchmark against known high-quality stocks

---

## 🚀 Usage Examples

### Example 1: Basic Run (Equal Weight)

```bash
python run_system.py
```

Simplest baseline - equal weight across top 20 Magic Formula stocks.

### Example 2: Maximum Sharpe Ratio (Recommended)

```bash
python run_system.py --method max_sharpe --positions 20 --capital 25000
```

Optimizes for best risk-adjusted return.

### Example 3: High Conviction (Fewer Positions)

```bash
python run_system.py --method max_sharpe --positions 10 --capital 25000
```

Concentrate capital in top 10 stocks.

### Example 4: Custom Capital & Filters

```bash
python run_system.py \
    --method hrp \
    --positions 30 \
    --capital 50000 \
    --min-market-cap 100000000 \
    --lookback-months 36
```

---

## 📈 Performance Monitoring

### Weekly Workflow

1. **Monday Morning**: Run system
   ```bash
   python run_system.py --method max_sharpe --capital 25000
   ```

2. **Review signals**: Open `trading_signals.csv`

3. **Execute trades**: Enter orders in BestBrokers

4. **Track performance**: Update `performance_log.csv` (manual for now)

### Rebalancing Strategy

- **Frequency**: Weekly during competition
- **Threshold**: Rebalance if portfolio drift > 10%
- **Transaction costs**: Currently ignored (BestBrokers has no fees)

---

## 🔧 Configuration Options

### Optimization Methods

| Method | Description | When to Use |
|--------|-------------|-------------|
| `equal_weight` | 1/N allocation | Baseline, simplest |
| `mean_variance` | Markowitz optimization | Balanced risk/return |
| `max_sharpe` | Maximum risk-adjusted return | **Recommended** |
| `hrp` | Hierarchical Risk Parity | High diversification |

### Key Parameters

```python
# Portfolio size
--positions 20              # 10-30 recommended

# Capital
--capital 25000             # Your starting capital

# Data lookback
--lookback-months 24        # 12-36 months for optimization

# Filters
--min-market-cap 50000000   # Min $50M market cap
```

---

## 📊 Understanding the Output

### Trading Signals CSV

```csv
ticker,weight,allocation_usd,current_price,shares_to_buy,actual_cost,roe,earnings_yield,magic_formula_rank
AAPL,0.06,1500.00,180.50,8,1444.00,45.2,5.8,12
MSFT,0.055,1375.00,350.25,3,1050.75,38.7,6.1,8
...
```

**Columns**:
- `ticker`: Stock symbol
- `weight`: Portfolio allocation (5% = 0.05)
- `allocation_usd`: Target dollar amount
- `current_price`: Latest closing price
- `shares_to_buy`: **Exact number of shares to buy**
- `actual_cost`: Real cost (shares × price)
- `roe`: Return on Equity (%)
- `earnings_yield`: 1/PE ratio (%)
- `magic_formula_rank`: Rank in Magic Formula (1 = best)

### Performance Metrics

Logged after optimization:

```
Expected Return: 18.5%      # Annualized
Volatility: 16.2%            # Annualized std dev
Sharpe Ratio: 0.94           # Risk-adjusted return
```

---

## 🛠️ Development & Extensions

### Phase 2: Enhancements (Post-Competition)

1. **Options Analysis**
   - SPY put/call volume and open interest
   - Dealer gamma exposure
   - Implied volatility surface

2. **Alternative Data**
   - Insider buying/selling
   - Short interest
   - Earnings surprises

3. **Risk Management**
   - Stop-loss rules
   - Position sizing by volatility
   - Sector exposure limits

4. **Live Trading Integration**
   - Interactive Brokers API
   - Alpaca API
   - Real-time execution

### Adding New Factors

```python
# factors/momentum.py

def calculate_momentum_score(prices: pd.DataFrame) -> pd.Series:
    """12-1 month momentum (skip most recent month)."""
    return_12m = prices.iloc[-252] / prices.iloc[-21] - 1
    return return_12m.rank(ascending=False)

# Combine with Magic Formula
combined_rank = (magic_formula_rank + momentum_rank) / 2
```

---

## 🧠 Theory & References

### Magic Formula

**Source**: Joel Greenblatt, *The Little Book That Beats the Market* (2006)

**Formula**:
```
Quality Rank = Rank by ROE (higher is better)
Value Rank = Rank by Earnings Yield (higher is better)
Final Score = Average(Quality Rank, Value Rank)
```

**Why it works**:
- Quality: High ROE = sustainable competitive advantage
- Value: High earnings yield = cheap relative to earnings
- Combined: High-quality companies at bargain prices

### Portfolio Optimization

**Modern Portfolio Theory (Markowitz, 1952)**:
- Maximize return for given risk
- Or minimize risk for given return
- Uses covariance matrix to find efficient frontier

**Maximum Sharpe Ratio**:
```
Sharpe = (Return - Risk_Free_Rate) / Volatility

Maximize Sharpe = Best risk-adjusted return
```

**Hierarchical Risk Parity**:
- Uses correlation structure
- Avoids relying on return forecasts
- More robust to estimation error

---

## 🐛 Troubleshooting

### Issue: "No stocks passed filters"

**Solution**: Lower minimum market cap
```bash
python run_system.py --min-market-cap 10000000
```

### Issue: YFinance rate limiting

**Solution**: Use cached data
```python
fetcher.get_fundamental_data(tickers, use_cache=True)
```

### Issue: Optimization fails

**Solution**: Fall back to equal weight
```bash
python run_system.py --method equal_weight
```

---

## 📜 License

MIT License - Free to use, modify, and distribute.

---

## 🤝 Contributing

This is a competition project, but post-competition:
- PRs welcome for new factors, optimizers, data sources
- Open issues for bugs or feature requests

---

## 📞 Contact

Built for BestBrokers Investment Competition
Team: quant-edge

**Next Competition Run**: Week 1 (Starting Capital: $25,000)

---

## ⚡ Performance Checklist

- [x] Data fetching (YFinance)
- [x] Magic Formula implementation
- [x] Portfolio optimization (Skfolio)
- [x] End-to-end pipeline
- [x] Test suites
- [ ] Live execution (manual for now)
- [ ] Performance tracking dashboard
- [ ] Options analysis (Phase 2)
- [ ] Multi-factor models (Phase 2)

---

**Last Updated**: 2024-10-18
**Status**: Production-ready for BestBrokers competition
**Next Milestone**: Week 1 execution → Performance monitoring
