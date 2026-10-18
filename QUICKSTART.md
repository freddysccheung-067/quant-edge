# ⚡ QUICKSTART GUIDE
## Get Trading Signals in 2 Minutes

### Step 1: Activate Environment
```bash
cd D:\quant-edge
venv\Scripts\activate
```

### Step 2: Generate Signals (Choose One)

**Option A: Fastest (Equal Weight)**
```bash
python run_system.py
```
- Simplest: Equal weight top 20 stocks
- No optimization, instant results
- Good baseline strategy

**Option B: Recommended (Maximum Sharpe)**
```bash
python run_system.py --method max_sharpe --positions 20 --capital 25000
```
- Best risk-adjusted returns
- ~2-3 minutes runtime
- **This is what you want for competition**

**Option C: Conservative (Fewer Positions)**
```bash
python run_system.py --method max_sharpe --positions 10 --capital 25000
```
- High conviction (top 10 stocks only)
- Lower diversification, higher concentration

### Step 3: Execute Trades

1. Open `trading_signals.csv`
2. You'll see something like this:

```
ticker  shares  price   cost      weight  MF_rank
AAPL    8       180.50  1,444.00  6.0%    12
MSFT    3       350.25  1,050.75  5.5%    8
...
```

3. **BUY the exact number of shares listed**
4. Enter orders in BestBrokers

### Done! 🎉

---

## Weekly Workflow (Competition Mode)

### Monday Morning Routine

1. **Generate fresh signals**:
   ```bash
   cd D:\quant-edge
   venv\Scripts\activate
   python run_system.py --method max_sharpe --positions 20 --capital 25000
   ```

2. **Review changes**:
   - Compare new `trading_signals.csv` with last week
   - Identify: new buys, sells, holds

3. **Rebalance** (if weight drift > 10%):
   - Sell positions no longer in top 20
   - Buy new positions
   - Adjust sizes for weight drift

4. **Track performance** (manual for now):
   - Record portfolio value in Excel
   - Note any major news affecting holdings

---

## Understanding Your Signals

### Key Columns in trading_signals.csv

| Column | Meaning | What to Do |
|--------|---------|------------|
| `ticker` | Stock symbol | The stock to buy |
| `shares_to_buy` | Exact shares | **THIS IS YOUR BUY ORDER** |
| `current_price` | Latest price | Reference only |
| `actual_cost` | Real cost | How much you'll spend |
| `weight` | Portfolio % | Target allocation |
| `magic_formula_rank` | Quality rank | Lower = better (1 is best) |
| `roe` | Return on Equity | Higher = more profitable company |
| `earnings_yield` | Inverse P/E | Higher = cheaper valuation |

### Example Signal Interpretation

```
AAPL: 8 shares, $1,444 cost, 6% weight, Rank #12
```

**Translation**: 
- Buy 8 shares of Apple
- It will cost ~$1,444
- Apple should be 6% of your portfolio
- Apple ranks #12 in Magic Formula (very good quality + value)
- ROE: 45.2% (excellent profitability)
- Earnings Yield: 5.8% (reasonable valuation)

---

## Troubleshooting

### "Module not found" error
```bash
# Make sure venv is activated
cd D:\quant-edge
venv\Scripts\activate

# Reinstall if needed
pip install -r requirements.txt
```

### "No stocks passed filters"
```bash
# Lower the market cap threshold
python run_system.py --min-market-cap 10000000
```

### "YFinance rate limiting"
```bash
# Wait 5 minutes and try again
# Or use cached data (won't be as fresh)
```

### Need help?
- Read `README.md` for full documentation
- Check `FUTURE_PROMPTS.md` for extensions
- Run tests: `python test_data_fetcher.py`

---

## Next Steps After First Run

1. ✅ **Week 1**: Execute signals, track performance manually
2. ✅ **Week 2**: Rebalance if needed, keep records
3. 📊 **Week 3**: Build performance tracker (PROMPT 03 in FUTURE_PROMPTS.md)
4. 🤖 **Week 4**: Automate rebalancing (PROMPT 06)

---

## Emergency Recovery

If something breaks:

```bash
# 1. Fresh virtual environment
cd D:\quant-edge
rmdir /s venv
python -m venv venv
venv\Scripts\activate

# 2. Reinstall everything
pip install -r requirements.txt

# 3. Run tests
python test_data_fetcher.py
python test_magic_formula.py

# 4. If tests pass, generate signals
python run_system.py --method max_sharpe
```

---

## Competition Deadlines

- **Start Date**: [Your competition start date]
- **Capital**: $25,000 USD
- **Rebalancing**: Weekly (Monday mornings)
- **End Date**: [Your competition end date]

---

## Performance Expectations

Based on historical Magic Formula results:

| Metric | Expected |
|--------|----------|
| Annual Return | 15-20% |
| Volatility | 15-18% |
| Sharpe Ratio | 0.8-1.2 |
| Max Drawdown | -15% to -20% |
| Win Rate | 60-65% |

Your actual results may vary!

---

## Quick Reference: CLI Flags

```bash
--method {equal_weight,mean_variance,max_sharpe,hrp}
    Optimization method (default: equal_weight)

--positions N
    Number of positions (default: 20)

--capital AMOUNT
    Starting capital in USD (default: 25000)

--lookback-months N
    Historical data window (default: 24)

--min-market-cap AMOUNT
    Minimum market cap filter (default: 50000000)

--output FILE
    Output file name (default: trading_signals.csv)

--no-backtest
    Skip backtest step (faster)

--log-level {DEBUG,INFO,WARNING,ERROR}
    Logging verbosity (default: INFO)
```

---

**Last Updated**: 2024-10-18  
**Status**: PRODUCTION READY ✅  
**Next Run**: Monday Morning

---

**🎯 Your Action Item Right Now:**

```bash
cd D:\quant-edge
venv\Scripts\activate
python run_system.py --method max_sharpe --positions 20 --capital 25000
```

Then execute the trades! Good luck! 🚀
