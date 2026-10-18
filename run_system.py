"""
QuantEdge Trading System - End-to-End Pipeline

This script runs the complete quantitative trading system:
    1. Fetch S&P 500 universe
    2. Get fundamental data
    3. Calculate Magic Formula scores
    4. Optimize portfolio allocation
    5. Generate trading signals
    6. Output actionable recommendations

This is the main entry point for generating trading signals for the
BestBrokers competition or any other portfolio.

Usage:
    python run_system.py --method max_sharpe --positions 20 --capital 25000

Author: quant-edge Team
Date: 2024-10-18
"""

import sys
import argparse
import logging
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd

# Add project root
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from data.fetchers import YFinanceFetcher, setup_logging
from factors import calculate_magic_formula_score, get_magic_formula_rankings
from portfolio import optimize_portfolio, construct_equal_weight_portfolio, backtest_portfolio


def run_trading_system(
    method: str = 'equal_weight',
    positions: int = 20,
    capital: float = 25000.0,
    lookback_months: int = 24,
    min_market_cap: float = 50_000_000,
    output_file: str = 'trading_signals.csv',
    backtest: bool = True
):
    """
    Run the complete quantitative trading system.

    Args:
        method: Portfolio optimization method
        positions: Target number of positions
        capital: Initial capital to allocate
        lookback_months: Months of historical data to use
        min_market_cap: Minimum market cap filter
        output_file: Output file for trading signals
        backtest: Whether to run backtest
    """
    logger.info("="*70)
    logger.info("QUANTEDGE TRADING SYSTEM - PRODUCTION RUN")
    logger.info("="*70)
    logger.info(f"Configuration:")
    logger.info(f"  Method: {method}")
    logger.info(f"  Positions: {positions}")
    logger.info(f"  Capital: ${capital:,.2f}")
    logger.info(f"  Lookback: {lookback_months} months")
    logger.info(f"  Min Market Cap: ${min_market_cap:,.0f}")

    # =================================================================
    # STEP 1: Data Fetching
    # =================================================================
    logger.info("\n" + "="*70)
    logger.info("STEP 1: Data Fetching")
    logger.info("="*70)

    fetcher = YFinanceFetcher()

    # Get universe
    tickers = fetcher.get_universe()
    logger.info(f"[OK] Fetched universe: {len(tickers)} tickers")

    # Get fundamental data
    fundamentals = fetcher.get_fundamental_data(tickers=tickers)
    logger.info(f"[OK] Fetched fundamentals: {len(fundamentals)} stocks")

    # =================================================================
    # STEP 2: Factor Analysis (Magic Formula)
    # =================================================================
    logger.info("\n" + "="*70)
    logger.info("STEP 2: Factor Analysis (Magic Formula)")
    logger.info("="*70)

    scores = calculate_magic_formula_score(
        fundamentals,
        min_market_cap=min_market_cap,
        min_liquidity=100_000,
        exclude_financials=True
    )

    logger.info(f"[OK] Ranked {len(scores)} stocks by Magic Formula")
    logger.info(f"  Top stock: {scores.iloc[0]['ticker']}")
    logger.info(f"  ROE range: {scores['roe'].min():.1f}% to {scores['roe'].max():.1f}%")

    # Select top candidates (2x target positions for optimization)
    top_candidates = scores.head(positions * 2)['ticker'].tolist()
    logger.info(f"[OK] Selected top {len(top_candidates)} candidates for optimization")

    # =================================================================
    # STEP 3: Portfolio Optimization
    # =================================================================
    logger.info("\n" + "="*70)
    logger.info("STEP 3: Portfolio Optimization")
    logger.info("="*70)

    # Fetch price data for optimization
    end_date = datetime.now()
    start_date = end_date - timedelta(days=lookback_months*30)

    logger.info(f"Fetching price data: {start_date.date()} to {end_date.date()}")

    prices = fetcher.get_price_data(
        start_date=start_date.strftime('%Y-%m-%d'),
        end_date=end_date.strftime('%Y-%m-%d'),
        tickers=top_candidates
    )

    logger.info(f"[OK] Price data: {len(prices)} days × {len(prices.columns)} stocks")

    # Run optimization
    if method == 'equal_weight':
        # Simple equal-weight for baseline
        weights = construct_equal_weight_portfolio(top_candidates, n_positions=positions)
        metrics = {'return': 0, 'volatility': 0, 'sharpe': 0}  # Calculate these properly
    else:
        # Advanced optimization
        weights, metrics = optimize_portfolio(
            prices,
            method=method,
            target_positions=positions
        )

    logger.info(f"[OK] Portfolio optimized: {len(weights)} positions")
    logger.info(f"  Expected Return: {metrics['return']*100:.1f}%")
    logger.info(f"  Volatility: {metrics['volatility']*100:.1f}%")
    logger.info(f"  Sharpe Ratio: {metrics['sharpe']:.2f}")

    # =================================================================
    # STEP 4: Generate Trading Signals
    # =================================================================
    logger.info("\n" + "="*70)
    logger.info("STEP 4: Generate Trading Signals")
    logger.info("="*70)

    # Get current prices
    current_prices = prices.iloc[-1]

    # Calculate position sizes
    signals = []
    for ticker, weight in sorted(weights.items(), key=lambda x: x[1], reverse=True):
        allocation = capital * weight
        price = current_prices[ticker]
        shares = int(allocation / price)
        actual_cost = shares * price

        # Get fundamental metrics for this stock
        stock_data = scores[scores['ticker'] == ticker]
        if len(stock_data) > 0:
            roe = stock_data.iloc[0]['roe']
            ey = stock_data.iloc[0]['earnings_yield']
            mf_rank = stock_data.iloc[0]['final_rank']
        else:
            roe, ey, mf_rank = 0, 0, 999

        signals.append({
            'ticker': ticker,
            'weight': weight,
            'allocation_usd': allocation,
            'current_price': price,
            'shares_to_buy': shares,
            'actual_cost': actual_cost,
            'roe': roe,
            'earnings_yield': ey,
            'magic_formula_rank': mf_rank
        })

    signals_df = pd.DataFrame(signals)

    # Save to CSV
    output_path = project_root / output_file
    signals_df.to_csv(output_path, index=False, float_format='%.2f')
    logger.info(f"[OK] Trading signals saved to: {output_path}")

    # Display signals
    logger.info(f"\n{'='*70}")
    logger.info("TRADING SIGNALS - ACTIONABLE RECOMMENDATIONS")
    logger.info(f"{'='*70}")
    logger.info(f"Total Capital: ${capital:,.2f}")
    logger.info(f"Total Allocated: ${signals_df['actual_cost'].sum():,.2f}")
    logger.info(f"Cash Remaining: ${capital - signals_df['actual_cost'].sum():,.2f}\n")

    print("\n" + "="*70)
    print("📊 TRADING SIGNALS")
    print("="*70)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"Strategy: Magic Formula + {method.upper()}")
    print(f"Capital: ${capital:,.0f}")
    print("\n" + "-"*70)
    print(f"{'Ticker':<8} {'Shares':>7} {'Price':>10} {'Cost':>12} {'Weight':>8} {'MF Rank':>8}")
    print("-"*70)

    for _, row in signals_df.iterrows():
        print(f"{row['ticker']:<8} {row['shares_to_buy']:>7.0f} "
              f"${row['current_price']:>9.2f} ${row['actual_cost']:>11,.0f} "
              f"{row['weight']*100:>7.1f}% {row['magic_formula_rank']:>8.0f}")

    print("-"*70)
    print(f"{'TOTAL':<8} {signals_df['shares_to_buy'].sum():>7.0f} "
          f"{'':>10} ${signals_df['actual_cost'].sum():>11,.0f} "
          f"{signals_df['weight'].sum()*100:>7.1f}%")
    print("="*70)

    # =================================================================
    # STEP 5: Backt (optional)
    # =================================================================
    if backtest and method != 'equal_weight':
        logger.info("\n" + "="*70)
        logger.info("STEP 5: Backtest")
        logger.info("="*70)

        # Use last 12 months for backtest
        backtest_start = end_date - timedelta(days=365)

        results = backtest_portfolio(
            weights,
            prices,
            initial_capital=capital,
            start_date=backtest_start.strftime('%Y-%m-%d')
        )

        # Save backtest results
        backtest_file = output_path.parent / f"backtest_{datetime.now().strftime('%Y%m%d')}.csv"
        results.to_csv(backtest_file)
        logger.info(f"[OK] Backtest results saved to: {backtest_file}")

    # =================================================================
    # FINAL SUMMARY
    # =================================================================
    logger.info("\n" + "="*70)
    logger.info("*** SYSTEM RUN COMPLETE ***")
    logger.info("="*70)
    logger.info(f"Generated {len(signals)} trading signals")
    logger.info(f"Output saved to: {output_path}")
    logger.info(f"\nNext steps:")
    logger.info(f"  1. Review signals in {output_file}")
    logger.info(f"  2. Execute trades in BestBrokers platform")
    logger.info(f"  3. Re-run weekly for rebalancing signals")
    logger.info("="*70 + "\n")

    return signals_df, metrics


def main():
    """Command-line interface."""
    parser = argparse.ArgumentParser(
        description="QuantEdge Trading System - Generate trading signals",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    parser.add_argument(
        '--method',
        choices=['equal_weight', 'mean_variance', 'max_sharpe', 'hrp'],
        default='equal_weight',
        help="Portfolio optimization method"
    )

    parser.add_argument(
        '--positions',
        type=int,
        default=20,
        help="Target number of positions"
    )

    parser.add_argument(
        '--capital',
        type=float,
        default=25000.0,
        help="Initial capital in USD"
    )

    parser.add_argument(
        '--lookback-months',
        type=int,
        default=24,
        help="Months of historical data for optimization"
    )

    parser.add_argument(
        '--min-market-cap',
        type=float,
        default=50_000_000,
        help="Minimum market cap filter"
    )

    parser.add_argument(
        '--output',
        default='trading_signals.csv',
        help="Output file for trading signals"
    )

    parser.add_argument(
        '--no-backtest',
        action='store_true',
        help="Skip backtest step"
    )

    parser.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default='INFO',
        help="Logging level"
    )

    args = parser.parse_args()

    # Setup logging
    setup_logging(getattr(logging, args.log_level))

    # Run system
    try:
        signals, metrics = run_trading_system(
            method=args.method,
            positions=args.positions,
            capital=args.capital,
            lookback_months=args.lookback_months,
            min_market_cap=args.min_market_cap,
            output_file=args.output,
            backtest=not args.no_backtest
        )

        return 0

    except Exception as e:
        logger.error(f"System error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
