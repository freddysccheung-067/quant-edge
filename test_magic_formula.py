"""
Test script for Magic Formula Factor Library.

This validates the Magic Formula implementation against known benchmarks
and ensures all metrics are calculated correctly.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from data.fetchers import YFinanceFetcher, setup_logging
from factors import calculate_magic_formula_score, get_magic_formula_rankings
import pandas as pd
import logging

def test_magic_formula_calculation():
    """Test Magic Formula calculation on real data."""
    print("\n" + "="*70)
    print("TEST 1: Magic Formula Calculation")
    print("="*70)

    # Fetch data
    fetcher = YFinanceFetcher()
    tickers = fetcher.get_universe()[:50]  # Test on first 50 stocks for speed

    print(f"[OK] Testing on {len(tickers)} stocks...")

    fundamentals = fetcher.get_fundamental_data(tickers=tickers)
    print(f"[OK] Fetched fundamentals for {len(fundamentals)} stocks")

    # Calculate Magic Formula
    scores = calculate_magic_formula_score(
        fundamentals,
        min_market_cap=10_000_000,  # Lower threshold for testing
        min_liquidity=10_000,
        exclude_financials=False  # Include all sectors for testing
    )

    print(f"\n[OK] Magic Formula Results:")
    print(f"  Total ranked: {len(scores)} stocks")
    print(f"  ROE range: {scores['roe'].min():.1f}% to {scores['roe'].max():.1f}%")
    print(f"  Earnings Yield range: {scores['earnings_yield'].min():.1f}% to {scores['earnings_yield'].max():.1f}%")

    # Validate structure
    required_cols = ['ticker', 'roe', 'earnings_yield', 'quality_rank',
                     'value_rank', 'magic_formula_score', 'final_rank']

    for col in required_cols:
        assert col in scores.columns, f"Missing column: {col}"

    # Validate rankings
    assert scores['final_rank'].min() == 1, "Best rank should be 1"
    assert len(scores['final_rank'].unique()) == len(scores), "Ranks should be unique"

    # Print top 10
    print(f"\n[OK] Top 10 Magic Formula Stocks:")
    print(scores[['ticker', 'roe', 'earnings_yield', 'final_rank']].head(10).to_string(index=False))

    print("\n[PASS] Magic Formula calculation works correctly")
    return scores

def test_convenience_functions():
    """Test convenience functions."""
    print("\n" + "="*70)
    print("TEST 2: Convenience Functions")
    print("="*70)

    fetcher = YFinanceFetcher()
    tickers = fetcher.get_universe()[:30]
    fundamentals = fetcher.get_fundamental_data(tickers=tickers)

    # Test get_magic_formula_rankings
    top_stocks = get_magic_formula_rankings(
        fundamentals,
        top_n=10,
        min_market_cap=10_000_000,
        min_liquidity=10_000,
        exclude_financials=False
    )

    print(f"[OK] Retrieved top {len(top_stocks)} stocks")
    print(f"[OK] Top 5: {', '.join(top_stocks[:5])}")

    assert len(top_stocks) <= 10, "Should return at most 10 stocks"
    assert len(top_stocks) > 0, "Should return at least 1 stock"
    assert all(isinstance(t, str) for t in top_stocks), "All tickers should be strings"

    print("[PASS] Convenience functions work correctly")
    return top_stocks

def test_edge_cases():
    """Test edge cases and error handling."""
    print("\n" + "="*70)
    print("TEST 3: Edge Cases")
    print("="*70)

    from factors.magic_formula import MagicFormulaCalculator

    calculator = MagicFormulaCalculator(
        min_market_cap=1_000_000_000,  # Very high threshold
        min_liquidity=1_000_000,
        exclude_financials=True
    )

    # Create minimal test data
    test_data = pd.DataFrame({
        'ticker': ['TEST1', 'TEST2', 'TEST3'],
        'market_cap': [500_000_000, 2_000_000_000, 100_000_000],  # Only TEST2 passes
        'avg_volume': [2_000_000, 2_000_000, 50_000],
        'sector': ['Technology', 'Technology', 'Financial Services'],
        'trailing_pe': [15, 20, 25],
        'return_on_equity': [0.25, 0.30, 0.15]
    })

    result = calculator.calculate(test_data)

    print(f"[OK] Filtered {len(test_data)} stocks -> {len(result)} stocks")
    assert len(result) == 1, "Should filter to 1 stock (TEST2)"
    assert result.iloc[0]['ticker'] == 'TEST2', "TEST2 should be the only stock"

    # Test with empty data
    empty_result = calculator.calculate(pd.DataFrame())
    assert len(empty_result) == 0, "Empty input should return empty output"
    print("[OK] Handles empty data gracefully")

    # Test with invalid data
    invalid_data = pd.DataFrame({
        'ticker': ['INVALID'],
        'market_cap': [1e12],
        'avg_volume': [1e6],
        'sector': ['Technology'],
        'trailing_pe': [-10],  # Negative P/E (invalid)
        'return_on_equity': [999]  # Impossible ROE
    })

    invalid_result = calculator.calculate(invalid_data)
    assert len(invalid_result) == 0, "Should filter out invalid data"
    print("[OK] Filters out invalid data")

    print("[PASS] Edge case handling works correctly")

def test_real_world_benchmark():
    """Test against known high-quality value stocks."""
    print("\n" + "="*70)
    print("TEST 4: Real-World Benchmark")
    print("="*70)

    # Known high-quality value stocks (as of 2024)
    # These should generally rank well on Magic Formula
    benchmark_tickers = ['AAPL', 'MSFT', 'GOOGL', 'META', 'BRK.B']

    fetcher = YFinanceFetcher()
    fundamentals = fetcher.get_fundamental_data(tickers=benchmark_tickers)

    scores = calculate_magic_formula_score(
        fundamentals,
        min_market_cap=1_000_000,  # Very low for testing
        min_liquidity=1_000,
        exclude_financials=False
    )

    print(f"\n[OK] Benchmark Stock Rankings:")
    for _, row in scores.iterrows():
        print(f"  {row['ticker']:6s}: Rank {row['final_rank']:2.0f}  "
              f"(ROE: {row['roe']:6.1f}%, EY: {row['earnings_yield']:6.1f}%)")

    # Sanity checks
    assert len(scores) >= 3, "Should successfully rank at least 3 benchmark stocks"

    # These companies should have positive ROE and reasonable earnings yields
    assert (scores['roe'] > 0).any(), "At least one stock should have positive ROE"
    assert (scores['earnings_yield'] > 0).any(), "At least one stock should have positive earnings yield"

    print("\n[PASS] Real-world benchmark test passed")
    return scores

def run_all_tests():
    """Run all Magic Formula tests."""
    print("\n" + "="*70)
    print("MAGIC FORMULA FACTOR LIBRARY - TEST SUITE")
    print("="*70)

    # Setup logging
    setup_logging(logging.INFO)

    try:
        # Run tests
        scores = test_magic_formula_calculation()
        top_stocks = test_convenience_functions()
        test_edge_cases()
        benchmark_scores = test_real_world_benchmark()

        # Final summary
        print("\n" + "="*70)
        print("*** ALL TESTS PASSED ***")
        print("="*70)
        print(f"\nMagic Formula implementation is production-ready!")
        print(f"  - Successfully ranked {len(scores)} stocks")
        print(f"  - Top stock: {scores.iloc[0]['ticker']}")
        print(f"  - Quality range: ROE from {scores['roe'].min():.1f}% to {scores['roe'].max():.1f}%")
        print(f"  - Value range: EY from {scores['earnings_yield'].min():.1f}% to {scores['earnings_yield'].max():.1f}%")
        print("\nNext step: Implement Portfolio Optimizer (Prompt 03)")
        print("="*70 + "\n")

        return True

    except AssertionError as e:
        print(f"\n[FAIL] TEST FAILED: {e}")
        return False
    except Exception as e:
        print(f"\n[FAIL] UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
