# 🎯 MASTER EXECUTION GUIDE: Multi-Agent Build Strategy

## Overview

You now have **3 rigorous, institutional-grade implementation prompts** ready to execute in parallel across multiple Claude Code CLI sessions.

Each prompt is **self-contained** and can be delegated to a separate CLI instance. This parallel execution strategy lets you build faster while keeping each session focused on its specific domain.

---

## ⚡ Parallel Execution Strategy

### Session Allocation

**Session 1 (Current)**: **Coordination & Integration**
- Your role: Orchestrate the build
- Monitor progress from other sessions
- Integrate completed modules
- Handle cross-module dependencies
- Final system testing

**Session 2**: **PROMPT-05-BACKTESTING.txt**
- Build: Institutional-grade backtesting engine
- Output: `backtesting/` module (8 files, ~1,550 lines)
- Est. time: 2-3 hours
- Dependencies: Existing data fetcher, factor models
- **Blocker**: None - can start immediately

**Session 3**: **PROMPT-06-OPTIONS-MICROSTRUCTURE.txt**
- Build: Dealer positioning analytics
- Output: `options/` module (8 files, ~2,300 lines)
- Est. time: 3-4 hours
- Dependencies: None (standalone)
- **Blocker**: None - can start immediately

**Session 4**: **PROMPT-03-PERFORMANCE-TRACKING.txt**
- Build: Performance tracking system
- Output: `tracking/` module (9 files, ~2,450 lines)
- Est. time: 2-3 hours
- Dependencies: None (database-driven)
- **Blocker**: None - can start immediately

---

## 🚀 Execution Workflow

### Phase 1: Launch Parallel Sessions (Day 1, Morning)

**Step 1**: Open 3 new Claude Code CLI sessions

```powershell
# Terminal 1 (Backtesting)
cd D:\quant-edge
claude

# Terminal 2 (Options Analytics)
cd D:\quant-edge
claude

# Terminal 3 (Performance Tracking)
cd D:\quant-edge
claude
```

**Step 2**: Paste prompts into respective sessions

- **Terminal 1**: Paste entire `prompts/PROMPT-05-BACKTESTING.txt`
- **Terminal 2**: Paste entire `prompts/PROMPT-06-OPTIONS-MICROSTRUCTURE.txt`
- **Terminal 3**: Paste entire `prompts/PROMPT-03-PERFORMANCE-TRACKING.txt`

**Step 3**: Monitor each session's `/tasks` output
- Each Claude will start building immediately
- They work independently (no conflicts)
- You can check progress periodically

---

### Phase 2: Integration (Day 1, Evening)

Once all 3 sessions complete (check `/tasks` status):

**Step 1**: Pull all changes
```powershell
cd D:\quant-edge
git pull origin main
```

**Step 2**: Verify module structure
```
quant-edge/
├── backtesting/         ✅ From Session 2
│   ├── engine.py
│   ├── strategies.py
│   └── ...
├── options/             ✅ From Session 3
│   ├── data/
│   ├── analytics/
│   └── ...
├── tracking/            ✅ From Session 4
│   ├── database/
│   ├── logger/
│   └── ...
```

**Step 3**: Run integration tests
```powershell
# Test backtesting
python test_backtester.py

# Test options analytics
python test_options_engine.py

# Test performance tracking
python test_tracking.py
```

**Step 4**: Test end-to-end workflow
```powershell
# Generate signals with options overlay
python run_system.py --method max_sharpe --positions 20

# Run backtest
python examples/run_backtest.py

# Track performance
python examples/track_performance.py
```

---

### Phase 3: Post-Integration Refinement (Day 2)

After integration, bring one session back for final polish:

**PROMPT**: Final Integration & Testing
```
I have successfully built 3 major modules in parallel:

1. ✅ backtesting/ - Institutional-grade backtesting engine
2. ✅ options/ - Options market microstructure analytics  
3. ✅ tracking/ - Performance tracking system

NOW: Wire them together into one cohesive system.

TASKS:
1. Modify run_system.py to incorporate options signals
   - Fetch dealer gamma positioning
   - Adjust equity exposure based on regime
   - Log signals to tracking database

2. Add backtest integration to tracking
   - Import backtest results into tracking.db
   - Generate comparison reports (backtest vs live)

3. Create master dashboard
   - Live performance vs backtest expectations
   - Dealer gamma overlay on equity curve
   - Alert panel showing all warnings

4. End-to-end smoke test
   - Run full pipeline: data → signals → backtest → track
   - Verify all modules communicate correctly
   - Generate sample reports

5. Documentation
   - Update START-HERE.md with new modules
   - Create WORKFLOWS.md showing common tasks
   - Document data dependencies between modules

DELIVERABLE: Fully integrated system ready for competition trading.
```

---

## 📋 Monitoring Progress

### Check Session Status

Each Claude Code session has `/tasks` command:
```bash
/tasks
```
Output shows:
- Running tasks
- Completed tasks  
- Failed tasks
- Estimated time remaining

### Check Git Status

From your coordination session:
```powershell
cd D:\quant-edge
git fetch origin
git log --oneline --all --graph -n 20
```

Each session will commit its work when complete.

---

## 🔄 Handling Failures

**If a session fails or gets stuck:**

1. **Don't restart from scratch** - Sessions resume from their last state
2. **Check the error** in session output
3. **Provide targeted fix** instead of full re-prompt
4. **Save progress** - Even partial work is valuable

**If sessions have conflicts (unlikely but possible):**
- All sessions work in separate directories (`backtesting/`, `options/`, `tracking/`)
- No file overlap = no merge conflicts
- If one does occur: prioritize the session that finished first

---

## 📦 Expected Deliverables by Session

### Session 2 (Backtesting) Outputs:
```
backtesting/
├── __init__.py
├── engine.py                      # 800 lines - Core engine
├── strategies.py                  # 200 lines - Strategy adapters
├── walk_forward.py                # 150 lines - WF validation
test_backtester.py                 # 300 lines
examples/run_backtest.py           # 100 lines
docs/BACKTESTING.md                # Documentation
```

**Verification:**
```powershell
python examples/run_backtest.py
# Should output: Full 10-year backtest with tearsheet
```

---

### Session 3 (Options) Outputs:
```
options/
├── __init__.py
├── data/
│   ├── fetchers.py               # 300 lines - Data pipeline
├── analytics/
│   ├── greeks.py                 # 400 lines - BSM Greeks
│   ├── dealer_positioning.py     # 500 lines - Dealer analysis
├── signals/
│   ├── gamma_regime.py           # 250 lines - Signal gen
├── visualization/
│   ├── gamma_chart.py            # 300 lines - Charts
test_options_engine.py             # 400 lines
examples/run_options_analysis.py   # 150 lines
docs/OPTIONS_MICROSTRUCTURE.md     # Documentation
```

**Verification:**
```powershell
python examples/run_options_analysis.py
# Should output: Dealer gamma analysis + dashboard.png
```

---

### Session 4 (Tracking) Outputs:
```
tracking/
├── __init__.py
├── database/
│   ├── schema.sql                # Database schema
│   ├── models.py                 # 300 lines - ORM
├── logger/
│   ├── trade_logger.py           # 200 lines
│   ├── portfolio_logger.py       # 200 lines
├── metrics/
│   ├── calculator.py             # 350 lines
├── alerts/
│   ├── threshold_monitor.py      # 200 lines
├── reports/
│   ├── daily_report.py           # 400 lines
test_tracking.py                   # 400 lines
examples/track_performance.py      # 100 lines
examples/log_trade.py              # 50 lines
```

**Verification:**
```powershell
python examples/track_performance.py
# Should output: Daily report HTML + metrics
```

---

## 🎯 Success Criteria

**You'll know the build is complete when:**

✅ All 3 modules have passing tests
✅ `run_system.py` generates signals with options overlay
✅ `examples/run_backtest.py` produces institutional tearsheet
✅ `examples/track_performance.py` logs portfolio state
✅ All code committed to GitHub
✅ README updated with new features
✅ You can run the full pipeline end-to-end

---

## 📊 Timeline Estimate

**Optimistic (all sessions succeed first try):**
- Day 1 Morning: Launch 3 parallel sessions (15 min)
- Day 1 Afternoon: Sessions complete (3-4 hours)
- Day 1 Evening: Integration testing (2 hours)
- Day 2: Final polish and documentation (2 hours)
- **Total: 1.5 days**

**Realistic (some debugging needed):**
- Day 1-2: Parallel build (6-8 hours total)
- Day 3: Integration + fixes (4 hours)
- Day 4: Testing + docs (2 hours)
- **Total: 3-4 days**

**Conservative (multiple iterations):**
- Week 1: Core builds (Days 1-3)
- Week 1: Integration (Days 4-5)
- Week 2: Testing + competition prep (Days 6-7)
- **Total: 7 days**

**You have 14 days to competition → Even conservative schedule leaves 7 days buffer for strategy refinement!**

---

## 🚦 Next Steps RIGHT NOW

1. **Decide**: Do you want to run parallel sessions or sequential?
   - **Parallel** = Faster (1-2 days) but requires monitoring 3 terminals
   - **Sequential** = Slower (4-5 days) but simpler

2. **If parallel**: Open 3 new Claude Code CLI sessions now

3. **If sequential**: Which module do you want first?
   - **Backtesting** = Validate strategy before live trading (recommended)
   - **Options** = Your unique edge (most complex)
   - **Tracking** = Essential for competition (simplest)

---

## 💡 Pro Tips

**Terminal Management:**
- Use Windows Terminal tabs (Ctrl+Shift+T for new tab)
- Label each tab: "Backtesting", "Options", "Tracking", "Coordination"
- Pin this guide in a separate window for reference

**Git Strategy:**
- Each session commits its own work
- Coordination session pulls and integrates
- Use feature branches if you want extra safety:
  ```powershell
  git checkout -b feature/backtesting
  git checkout -b feature/options
  git checkout -b feature/tracking
  ```

**Communication Between Sessions:**
- Sessions can't talk to each other directly
- Use Git as the communication layer
- Commit early, commit often
- Pull frequently in coordination session

---

**Ready to launch? Let me know how you want to proceed!** 🚀
