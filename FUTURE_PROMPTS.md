# QuantEdge - Future Development Prompts

This document contains ready-to-use prompts for extending the QuantEdge trading system in fresh Claude sessions. Copy the relevant section and paste it directly.

---

## 🎯 PROMPT 01: First-Time Setup

```
I have a quantitative trading system in D:\quant-edge\ built with:
- Data: YFinance (S&P 500 universe, fundamentals, prices)
- Factors: Magic Formula (Quality × Value)
- Portfolio: Skfolio optimization (mean-variance, max Sharpe, HRP)
- Pipeline: run_system.py generates trading signals

Read the README.md and show me:
1. Project structure summary
2. How to generate trading signals
3. Current test coverage status

Then run the complete test suite to verify everything works.
```

---

## 🚀 PROMPT 02: Generate Trading Signals

```
Run the QuantEdge trading system to generate this week's trading signals:

Requirements:
- Method: Maximum Sharpe Ratio optimization
- Positions: 20 stocks
- Capital: $25,000
- Output: trading_signals.csv

Steps:
1. Activate venv: D:\quant-edge\venv
2. Run: python run_system.py --method max_sharpe --positions 20 --capital 25000
3. Display the top 10 signals from trading_signals.csv
4. Summarize: expected return, volatility, Sharpe ratio

Also check if the data/cache/ is stale (>7 days old) and refresh if needed.
```

---

## 📊 PROMPT 03: Performance Tracking Dashboard

```
Build a performance tracking system for QuantEdge:

Create performance/tracker.py that:
1. Loads trading_signals.csv (historical trades)
2. Fetches actual price performance since trade date
3. Calculates:
   - Total portfolio return
   - Per-stock return contribution
   - Sharpe ratio vs benchmark (SPY)
   - Max drawdown
4. Outputs performance_report.csv and performance_summary.txt

Then create visualizations:
- Equity curve (portfolio value over time)
- Per-stock contribution chart
- Risk/return scatter plot

Use plotly for interactive charts (already installed).
Test on mock data if no real trades yet.
```

---

## 🔬 PROMPT 04: Add Momentum Factor

```
Extend QuantEdge with a momentum factor:

Create factors/momentum.py with:
- 12-1 month momentum (skip most recent month to avoid reversal)
- Calculate for all S&P 500 stocks
- Rank-based scoring (1 = best momentum)

Then create factors/multi_factor.py that combines:
- Magic Formula score (50% weight)
- Momentum score (50% weight)
- Final combined rank

Update run_system.py to:
- Add --factors flag: 'magic_formula' | 'momentum' | 'multi_factor'
- Default to 'magic_formula' for backward compatibility

Test the new factor on historical data and compare returns vs pure Magic Formula.
```

---

## 📈 PROMPT 05: Options Analysis Integration

```
Add SPY options analysis to QuantEdge:

Requirements:
- Use free data from Yahoo Finance (yfinance)
- Analyze SPY options chain (puts & calls)
- Calculate:
  1. Put/Call Open Interest ratio
  2. Put/Call Volume ratio
  3. Max pain level (price with most options expire worthless)
  4. Implied volatility skew

Create options/spy_analysis.py with:
- fetch_options_chain() → DataFrame of all options
- calculate_put_call_ratio() → float
- calculate_max_pain() → float (strike price)
- generate_options_signal() → 'bullish' | 'bearish' | 'neutral'

Then integrate into run_system.py:
- If options signal is 'bearish', reduce portfolio size to 50%
- If 'neutral', use 80% capital
- If 'bullish', use 100% capital

Document in README.md under "Options Analysis" section.
```

---

## 🤖 PROMPT 06: Automated Rebalancing

```
Build an automated rebalancing system:

Create portfolio/rebalancer.py that:
1. Loads current_holdings.csv (manually maintained for now)
2. Runs run_system.py to get new signals
3. Compares current vs target allocation
4. Generates rebalancing_trades.csv with:
   - Ticker
   - Action: BUY | SELL | HOLD
   - Shares to trade
   - Reason (e.g., "weight drift +5%")

Rebalancing rules:
- Only rebalance if weight drift > 10%
- Minimize turnover (transaction costs)
- Don't sell positions with <30 day hold (avoid short-term gains tax in real trading)

Add --rebalance flag to run_system.py:
python run_system.py --rebalance --current-holdings current_holdings.csv

Test with mock current_holdings.csv data.
```

---

## 🔍 PROMPT 07: Fundamental Data Deep Dive

```
Enhance the fundamental analysis in QuantEdge:

Extend data/fetchers.py to fetch additional metrics:
- Free Cash Flow / Market Cap
- Debt-to-Equity ratio
- Revenue Growth (YoY)
- Gross Margin
- Operating Margin
- Quick Ratio (liquidity)

Create factors/quality_score.py that calculates a composite quality score:
- ROE (30%)
- Operating Margin (20%)
- Debt-to-Equity (inverse, 20%)
- Revenue Growth (15%)
- Free Cash Flow Yield (15%)

Update factors/magic_formula.py to optionally use this enhanced quality score
instead of just ROE.

Add --quality-method flag: 'roe' | 'composite'
Test and compare performance.
```

---

## 📊 PROMPT 08: Sector Rotation Strategy

```
Add sector-aware portfolio construction:

Create factors/sector_rotation.py:
1. Calculate sector momentum (11 S&P sectors)
2. Rank sectors by 3-month, 6-month, 12-month returns
3. Identify top 3-4 "winning" sectors

Then modify portfolio/optimizer.py to:
- Add sector constraints
- Overweight top sectors (40% of portfolio)
- Underweight bottom sectors (10% of portfolio)
- Diversify within selected sectors using Magic Formula

Create visualization:
- Sector momentum heatmap (3m, 6m, 12m returns)
- Current portfolio sector breakdown pie chart

Test with:
python run_system.py --method max_sharpe --sector-rotation
```

---

## 🎯 PROMPT 09: Risk Management Layer

```
Add comprehensive risk management to QuantEdge:

Create risk/manager.py with:

Position-level risk:
- Max position size: 15% (configurable)
- Stop-loss: -10% from entry
- Take-profit: +30% from entry

Portfolio-level risk:
- Max total portfolio volatility: 18%
- Max drawdown limit: -15% (halt trading if hit)
- Sector concentration: max 30% per sector
- Correlation check: avoid highly correlated positions (>0.8)

Integration:
- Run risk checks AFTER optimization
- Adjust weights if constraints violated
- Log all risk adjustments to risk_log.csv

Add to run_system.py:
--max-volatility 18
--max-drawdown 15
--max-position-size 15

Test with aggressive portfolio (30 positions) and verify constraints enforced.
```

---

## 🔗 PROMPT 10: API Integration (Interactive Brokers)

```
Prepare QuantEdge for live trading with Interactive Brokers:

Create execution/ib_connector.py using ib_insync library:

Functions:
1. connect_ib() → IB connection
2. get_account_balance() → float
3. get_current_positions() → DataFrame
4. place_market_order(ticker, shares, action='BUY') → order confirmation
5. place_limit_order(ticker, shares, price, action='BUY') → order ID
6. cancel_order(order_id)

Create execution/dry_run.py for paper trading:
- Simulate order fills
- Track simulated portfolio
- Save to paper_trading_log.csv

Add --execution flag to run_system.py:
- 'dry_run': Log trades but don't execute
- 'paper': Execute on IB paper account
- 'live': Execute on real account (with confirmation)

Safety checks:
- Require --confirm-live flag for live trading
- Max daily loss limit
- Pre-flight validation

DO NOT execute live trades without explicit confirmation!
```

---

## 📈 PROMPT 11: Walk-Forward Optimization

```
Implement walk-forward backtesting:

Create backtest/walk_forward.py that:

1. Splits data into:
   - Training window: 12 months
   - Testing window: 1 month
   - Roll forward monthly

2. For each period:
   - Run Magic Formula on training data
   - Select top stocks
   - Optimize portfolio
   - Test on out-of-sample month
   - Record returns

3. Aggregate results:
   - Monthly returns
   - Sharpe ratio
   - Max drawdown
   - Win rate (% of months with positive return)

4. Compare optimization methods:
   - Equal weight
   - Mean-variance
   - Max Sharpe
   - HRP

Output:
- walk_forward_results.csv
- Best method recommendation
- Consistency metrics (mean, std, Sharpe across periods)

Run:
python backtest/walk_forward.py --start 2020-01-01 --end 2024-01-01
```

---

## 📊 PROMPT 12: Real-Time Dashboard

```
Build a live dashboard for QuantEdge:

Create dashboard/app.py using Plotly Dash:

Pages:
1. Home: Current portfolio summary
   - Total value, P&L today, P&L total
   - Top gainers/losers
   - Sector allocation pie chart

2. Signals: Latest trading signals
   - Table from trading_signals.csv
   - Highlighted: new positions vs holds

3. Performance: Historical performance
   - Equity curve
   - Drawdown chart
   - Rolling Sharpe ratio

4. Risk: Risk metrics
   - Current portfolio volatility
   - VaR (Value at Risk)
   - Correlation heatmap

5. Research: Factor analysis
   - Magic Formula rankings table
   - ROE vs Earnings Yield scatter plot

Launch:
python dashboard/app.py
# Opens localhost:8050

Use Plotly's dark theme for professional look.
Auto-refresh data every 5 minutes during market hours.
```

---

## 🧠 PROMPT 13: Machine Learning Enhancement

```
Add ML-based return prediction to QuantEdge:

Create ml/return_predictor.py using scikit-learn:

Features (from fundamentals + technical):
- ROE, P/E, P/B, Debt/Equity (fundamentals)
- 1m, 3m, 6m momentum (technical)
- 20-day volatility
- 50-day vs 200-day MA crossover

Target:
- Next month's return (classification: outperform vs underperform)

Models to test:
1. Random Forest
2. Gradient Boosting (XGBoost)
3. Logistic Regression (baseline)

Pipeline:
1. train_model(start, end) → trained model + accuracy metrics
2. predict_returns(model, current_data) → predicted returns
3. Combine with Magic Formula:
   - Magic Formula score (50% weight)
   - ML predicted return (50% weight)

Add --ml-enhanced flag to run_system.py

Deliverables:
- ml/models/ folder for saved models
- ml/backtest_ml.py for ML strategy backtest
- Comparison report: ML vs pure Magic Formula
```

---

## 🌐 PROMPT 14: Alternative Data Integration

```
Integrate alternative data sources:

Sources (all free):
1. FRED API (St. Louis Fed) - Economic indicators
   - Unemployment rate
   - 10-year Treasury yield
   - CPI (inflation)
   
2. SEC EDGAR - Insider transactions
   - Insider buying/selling by ticker
   
3. Reddit Sentiment (via PRAW)
   - r/wallstreetbets mentions
   - Sentiment score per ticker

Create data/alternative_data.py:

Functions:
- fetch_economic_indicators() → DataFrame
- fetch_insider_transactions(tickers) → DataFrame
- fetch_reddit_sentiment(tickers) → DataFrame

Integration:
- Add "macro_score" to run_system.py:
  - Bullish macro (low unemployment, low inflation) → 100% capital
  - Bearish macro → 50% capital, more defensive stocks

- Add "insider_filter" to factors:
  - Boost stocks with recent insider buying
  - Penalize stocks with insider selling

Test on historical data:
- Does insider buying predict future returns?
- Does macro timing improve risk-adjusted returns?
```

---

## 📝 PROMPT 15: Documentation & God's Eye View Quality

```
Audit QuantEdge for "God's Eye View" quality standard:

Tasks:

1. Code Quality Audit:
   - Run pylint on all .py files
   - Fix warnings/errors
   - Add type hints to all functions
   - Ensure docstrings follow Google style

2. Documentation:
   - Create docs/ folder
   - Write architecture.md explaining system design
   - Create api_reference.md for all modules
   - Add examples/ folder with notebooks

3. Testing:
   - Achieve >80% code coverage
   - Add unit tests for all modules
   - Add integration tests for end-to-end pipeline
   - Create pytest.ini config

4. Professional Touches:
   - Add LICENSE file (MIT)
   - Create CONTRIBUTING.md
   - Add badges to README (build status, coverage, version)
   - Create CHANGELOG.md

5. Deployment:
   - Docker container setup
   - Docker-compose for local dev
   - CI/CD pipeline (GitHub Actions)
   - Automated testing on push

Goal: Make QuantEdge look like a professional open-source project
comparable to God's Eye View OSINT tool.
```

---

## 🎓 PROMPT 16: Educational Content

```
Create educational materials for QuantEdge:

Deliverables:

1. Jupyter Notebook Tutorial (notebooks/01_getting_started.ipynb):
   - What is Magic Formula?
   - How to interpret Factor scores
   - Understanding portfolio optimization
   - Step-by-step example run

2. Jupyter Notebook Deep Dive (notebooks/02_advanced_strategies.ipynb):
   - Multi-factor models
   - Walk-forward optimization
   - Risk management techniques
   - Building your own factors

3. Video Script (docs/video_script.md):
   - 10-minute demo of QuantEdge
   - From data fetching to trade execution
   - Suitable for screen recording

4. Research Report Template (docs/research_template.md):
   - How to document new factor research
   - Backtesting methodology
   - Performance attribution

5. FAQ Document (docs/FAQ.md):
   - Common errors and solutions
   - Best practices
   - When to use each optimization method

Make all content beginner-friendly but technically rigorous.
```

---

## 🏆 PROMPT 17: Competition Wrapper

```
Build a BestBrokers-specific competition manager:

Create competition/bestbrokers.py:

Features:
1. Auto-login to BestBrokers (if API available, else manual)
2. Fetch current portfolio from platform
3. Compare with QuantEdge recommended allocation
4. Generate buy/sell list for rebalancing
5. Export in BestBrokers import format (if supported)

Create competition/leaderboard.py:
- Track your rank over time
- Compare returns vs other participants
- Identify strategy weaknesses (where you're losing)

Create competition/daily_report.py:
- Automated daily email/Slack message with:
  - Today's P&L
  - Current rank
  - Top performing positions
  - Underperforming positions
  - Action items (if any rebalancing needed)

Add:
python run_system.py --competition bestbrokers --auto-rebalance

Document in README under "BestBrokers Integration" section.
```

---

## 🚀 PROMPT 18: Performance Boost

```
Optimize QuantEdge for speed:

Profiling:
1. Run cProfile on run_system.py
2. Identify bottlenecks (likely: data fetching, optimization)

Optimizations:
1. Parallel data fetching:
   - Use concurrent.futures for multi-ticker fetching
   - Target: 10x speedup on universe fetch

2. Caching strategy:
   - Cache fundamental data (updates quarterly)
   - Cache price data (updates daily)
   - Use parquet instead of CSV (10x faster I/O)

3. Numba JIT compilation:
   - Compile factor calculations with @njit
   - Target: 5x speedup on Magic Formula calculation

4. Incremental updates:
   - Don't refetch entire universe daily
   - Only update changed data
   - Implement smart cache invalidation

Goal: Reduce full system run from ~5 minutes to <30 seconds.

Deliverables:
- Benchmark script: python benchmark.py
- Performance report: Before vs After metrics
- Updated README with performance specs
```

---

## 🔐 PROMPT 19: Production Security

```
Harden QuantEdge for production use:

Security Tasks:

1. Secrets Management:
   - Create .env.template
   - Use python-dotenv for API keys
   - Never commit secrets to git
   - Add pre-commit hook to scan for secrets

2. Input Validation:
   - Validate all CLI arguments
   - Sanitize ticker symbols (SQL injection risk if DB added)
   - Range checks on numerical inputs

3. Error Handling:
   - Graceful degradation (if yfinance fails, use cached data)
   - Retry logic with exponential backoff
   - Detailed error logging
   - User-friendly error messages

4. Logging & Monitoring:
   - Structured logging (JSON format)
   - Log rotation (don't fill disk)
   - Sensitive data redaction in logs
   - Add --log-file option

5. Access Control:
   - If deploying as web service, add authentication
   - Rate limiting on expensive operations
   - Audit trail for all trades

6. Data Integrity:
   - Checksums for cached data
   - Detect corrupted cache files
   - Atomic writes (no partial files)

Create security/audit.py to run security checks.
```

---

## 🌍 PROMPT 20: Multi-Market Expansion

```
Expand QuantEdge beyond U.S. equities:

Phase 1: International Equities
- Add support for:
  - European stocks (STOXX 600)
  - Asian markets (Nikkei 225, Hang Seng)
- Handle currency conversion
- Adjust for different market hours

Phase 2: Crypto
- Add cryptocurrency universe (Top 100 by market cap)
- Fetch from CoinGecko API (free)
- Calculate "crypto Magic Formula" (adapt metrics)
- Run 24/7 rebalancing (crypto never sleeps)

Phase 3: Forex
- Major currency pairs (EUR/USD, GBP/USD, etc.)
- Momentum-based strategies
- Risk management for leverage

Create:
- data/fetchers_intl.py for international data
- data/fetchers_crypto.py for cryptocurrency
- factors/magic_formula_crypto.py (adapted metrics)

Add:
python run_system.py --market us|eu|asia|crypto|forex

Deliverable:
- Multi-market dashboard showing all portfolios
- Correlation analysis across markets
- Risk-adjusted total portfolio (diversified across markets)
```

---

## 📚 Template for Custom Prompts

```
[TASK TITLE]

Context:
I have QuantEdge trading system at D:\quant-edge\
[Describe current state and what you want to add]

Requirements:
1. [Specific requirement 1]
2. [Specific requirement 2]
3. [etc.]

Deliverables:
- [File 1 to create/modify]
- [File 2 to create/modify]
- [Test script]
- [Updated documentation]

Acceptance Criteria:
- [How to verify it works]
- [Performance benchmarks if applicable]
- [Test coverage requirements]

Constraints:
- [Any limitations or requirements]
- [Backward compatibility needed?]
- [Timeline / deadline]
```

---

## 🎯 Priority Order (Next Steps)

If starting fresh after competition setup, I recommend this order:

1. **PROMPT 03**: Performance Tracking (critical for competition)
2. **PROMPT 06**: Automated Rebalancing (save manual work)
3. **PROMPT 02**: Weekly Signal Generation (actual usage)
4. **PROMPT 09**: Risk Management (protect capital)
5. **PROMPT 11**: Walk-Forward Optimization (validate strategy)
6. **PROMPT 04**: Add Momentum Factor (improve returns)
7. **PROMPT 12**: Real-Time Dashboard (professional presentation)
8. **PROMPT 15**: God's Eye View Quality (polish)

The rest are enhancements for post-competition scaling.

---

**Note**: Always test on historical data before real money!

**Last Updated**: 2024-10-18
**Version**: 1.0
**Status**: Ready for fresh sessions
