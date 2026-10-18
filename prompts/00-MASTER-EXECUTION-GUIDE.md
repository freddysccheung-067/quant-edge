# 🎯 MASTER EXECUTION GUIDE: QuantEdge

## Overview

You now have **5 one-shot prompts** that can be executed independently and in parallel. Each is self-contained with full specifications, code examples, and success criteria.

## ⚡ Parallel Execution Strategy

### Option 1: Single Developer (14-day sprint)
Execute prompts **sequentially** in order:

```
Day 1-2:   Prompt 01 (Data Fetcher)         [Foundation]
Day 3-4:   Prompt 02 (Factor Library)       [Depends on 01]
Day 5-6:   Prompt 03 (Backtrader Strategy)  [Depends on 01+02]
Day 7-9:   Prompt 04 (Signal Generator)     [Depends on 01+02]
Day 10-11: Prompt 05 (Performance Analytics)[Depends on 03]
Day 12-14: Integration, testing, launch
```

**Total estimated time**: 15-18 hours of focused coding + 4-6 hours testing/integration

### Option 2: Team of 3-5 Developers (1-week sprint)

**Day 1-2**: Parallel execution
- Developer A: Prompt 01 (Data Fetcher)
- Developer B: Prompt 02 (Factor Library) - mock data initially
- Developer C: Prompt 03 (Backtrader Strategy) - mock data initially
- Developer D: Prompt 04 (Signal Generator) - mock data initially
- Developer E: Prompt 05 (Performance Analytics) - mock data initially

**Day 3-4**: Integration
- Connect all modules
- Replace mock data with real data
- End-to-end testing

**Day 5-7**: Competition prep
- Full backtest validation
- Live signal testing
- Documentation
- Launch

### Option 3: AI-Assisted (Claude Opus + Computer Use)

Use Claude with computer use capability to execute each prompt:

```bash
# Pass each prompt file to Claude sequentially
claude execute D:\quant-edge\prompts\01-DATA-FETCHER.md
claude execute D:\quant-edge\prompts\02-FACTOR-LIBRARY.md
claude execute D:\quant-edge\prompts\03-BACKTRADER-STRATEGY.md
claude execute D:\quant-edge\prompts\04-SIGNAL-GENERATOR.md
claude execute D:\quant-edge\prompts\05-PERFORMANCE-ANALYTICS.md
```

**Total time**: 6-8 hours with AI assistance

## 📋 Prompt Dependency Graph

```
01-DATA-FETCHER.md
    ↓
    ├─→ 02-FACTOR-LIBRARY.md
    │       ↓
    │       ├─→ 03-BACKTRADER-STRATEGY.md
    │       │       ↓
    │       │       └─→ 05-PERFORMANCE-ANALYTICS.md
    │       │
    │       └─→ 04-SIGNAL-GENERATOR.md
```

**Critical Path**: 01 → 02 → 03 → 05  
**Parallel Path**: 04 can run as soon as 02 is complete

## ✅ Implementation Checklist

### Pre-Implementation
- [ ] Python 3.11+ installed
- [ ] Virtual environment created
- [ ] Git repository initialized
- [ ] Dependencies installed (`pip install -r requirements.txt`)

### Prompt 01: Data Fetcher (Priority 1 - Foundation)
**Files**: `data/fetchers/yfinance_fetcher.py`, `data/fetchers/cache.py`

- [ ] S&P 500 ticker list scraping works
- [ ] 5-year price data fetched in <2 minutes
- [ ] Fundamental data includes all 8 required fields
- [ ] Cache reduces subsequent fetches to <5 seconds
- [ ] Handles ticker failures gracefully (>90% success rate)
- [ ] Data quality validation passes

**Validation Command**:
```python
from data.fetchers import DataFetcher
fetcher = DataFetcher()
tickers = fetcher.get_universe()
prices = fetcher.get_price_data('2019-01-01', '2024-10-01')
fundamentals = fetcher.get_fundamental_data()
print(f"Tickers: {len(tickers)}, Prices shape: {prices.shape}, Fundamentals shape: {fundamentals.shape}")
```

### Prompt 02: Factor Library (Priority 2 - Alpha Source)
**Files**: `factors/value.py`, `factors/quality.py`, `factors/composite.py`

- [ ] ROE calculated for >400 stocks
- [ ] Earnings Yield calculated for >400 stocks
- [ ] Magic Formula ranking works
- [ ] Top-ranked stocks have ROE > 15%, EY > 5%
- [ ] No inf or -inf values in output
- [ ] Runs in <2 seconds for 500 stocks

**Validation Command**:
```python
from factors.composite import magic_formula_score
scored = magic_formula_score(fundamentals)
print(scored.head(20))
print(f"Data completeness: {(~scored['magic_rank'].isna()).sum() / len(scored) * 100:.1f}%")
```

### Prompt 03: Backtrader Strategy (Priority 3 - Proof of Concept)
**Files**: `strategies/magic_formula.py`, `backtesting/backtrader_engine.py`

- [ ] Backtest runs 2019-2024 without errors
- [ ] Rebalances every 30 days correctly
- [ ] Holds exactly 15 positions at each rebalance
- [ ] Commission (0.1%) applied correctly
- [ ] Sharpe ratio > 0.8, max drawdown < 25%
- [ ] Trade log shows all entries/exits

**Validation Command**:
```python
python run_backtest.py
# Verify metrics printed match expectations
```

### Prompt 04: Signal Generator (Priority 4 - Live Trading)
**Files**: `execution/signal_generator.py`, `execution/portfolio_tracker.py`, `run_signals.py`

- [ ] Generates signals in <30 seconds
- [ ] Color-coded terminal output works
- [ ] Portfolio.csv tracks positions correctly
- [ ] Can export signals to CSV
- [ ] Handles missing price data gracefully
- [ ] Shows P&L for current positions

**Validation Command**:
```bash
python run_signals.py --show-portfolio
python run_signals.py --date 2024-10-18
python run_signals.py --export signals.csv
```

### Prompt 05: Performance Analytics (Priority 5 - Analysis)
**Files**: `backtesting/performance.py`

- [ ] Calculates Sharpe, Sortino, Calmar ratios
- [ ] Generates equity curve plot
- [ ] Generates drawdown plot
- [ ] Monthly returns heatmap works
- [ ] Benchmark comparison (vs SPY) works
- [ ] Runs in <5 seconds for 5 years of data

**Validation Command**:
```python
from backtesting.performance import PerformanceReport
report = PerformanceReport(portfolio_values, benchmark_values)
report.print_report()
report.plot_all(save_path='D:/quant-edge/results/performance')
```

## 🔧 Integration Testing

Once all prompts are complete:

### Test 1: End-to-End Backtest
```bash
python run_backtest.py
```
**Expected**: Backtest completes, shows performance metrics, Sharpe > 0.8

### Test 2: Live Signal Generation
```bash
python run_signals.py
```
**Expected**: Shows BUY/SELL/HOLD signals for today

### Test 3: Portfolio Tracking
```bash
python run_signals.py --execute
python run_signals.py --show-portfolio
```
**Expected**: Portfolio.csv updated, shows current positions and P&L

### Test 4: Performance Analysis
```python
from backtesting.performance import PerformanceReport
# Load backtest results
report = PerformanceReport(portfolio_values)
report.print_report()
report.plot_all()
```
**Expected**: Full performance metrics, 4 plots generated

## 🚨 Common Issues & Fixes

### Issue 1: yfinance Rate Limiting
**Symptom**: Slow data fetching, timeouts  
**Fix**: Add `time.sleep(0.1)` between ticker fetches, increase timeout to 10s

### Issue 2: Missing Fundamental Data
**Symptom**: Many NaN values in fundamentals  
**Fix**: Use alternative fields (e.g., P/E instead of EBIT), increase minimum threshold

### Issue 3: Backtest Not Rebalancing
**Symptom**: Strategy holds same positions forever  
**Fix**: Check `rebalance_days` parameter, verify `should_rebalance()` logic

### Issue 4: Signals Don't Match Backtest
**Symptom**: Live signals differ from backtest  
**Fix**: Ensure using same fundamental data, check date alignment

### Issue 5: Plots Don't Display
**Symptom**: `plt.show()` does nothing  
**Fix**: Use `plt.savefig()` instead, or set `MPLBACKEND=TkAgg`

## 📊 Success Metrics

### Phase 1: MVP (Week 2)
- [ ] All 5 prompts implemented
- [ ] Backtest runs 2019-2024
- [ ] Sharpe ratio > 0.8
- [ ] Max drawdown < 25%
- [ ] Live signals generate daily
- [ ] Can track portfolio

### Competition Launch (Day 14)
- [ ] Final backtest validated
- [ ] Paper traded 2-3 days
- [ ] Signal generation automated
- [ ] Tracking spreadsheet ready
- [ ] Risk rules documented
- [ ] **First trades executed**

### Post-Competition (Month 2)
- [ ] Real performance tracked
- [ ] Lessons learned documented
- [ ] Refactoring begun
- [ ] Code quality improved
- [ ] Tests added

## 🎓 Learning Objectives

By completing these prompts, you will:
1. Build a production-grade quantitative trading system
2. Understand factor investing (value, quality, momentum)
3. Master Backtrader framework
4. Learn performance analytics (Sharpe, Sortino, drawdown)
5. Experience real trading with skin in the game

## 🚀 Execution Commands

```bash
# Setup
cd D:\quant-edge
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt

# Execute prompts (pass each to Claude or human developer)
# 01: Implement data fetcher
# 02: Implement factor library
# 03: Implement backtrader strategy
# 04: Implement signal generator
# 05: Implement performance analytics

# Integration
python run_backtest.py        # Validate strategy
python run_signals.py          # Generate today's signals
python run_signals.py --execute # Execute trades

# Competition
# Daily: python run_signals.py
# Weekly: python run_signals.py --show-portfolio
```

## 🏁 Final Launch Checklist

**T-3 days**:
- [ ] All modules tested
- [ ] Backtest results acceptable
- [ ] Signal generation works

**T-2 days**:
- [ ] Paper trading started
- [ ] Tracking spreadsheet ready
- [ ] Execution process documented

**T-1 day**:
- [ ] Final backtest run
- [ ] Risk rules reviewed
- [ ] Portfolio initialized

**Launch Day**:
- [ ] Generate signals: `python run_signals.py`
- [ ] Review signals
- [ ] Execute trades in BestBrokers
- [ ] Update portfolio: `python run_signals.py --execute`
- [ ] Document trades

---

**YOU ARE NOW READY TO BUILD QUANTEDGE.**

Each prompt is self-contained. Execute them in order or parallel based on your team size. The competition starts in 14 days. Let's build something incredible.
