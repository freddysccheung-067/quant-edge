"""
Test script for Data Fetcher module.

This script validates that the YFinanceFetcher works correctly with
a small subset of data before running on the full universe.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from data.fetchers import YFinanceFetcher, setup_logging
import logging

def test_universe_fetching():
    """Test S&P 500 universe fetching."""
    print("\n" + "="*70)
    print("TEST 1: Fetching S&P 500 Universe")
    print("="*70)

    fetcher = YFinanceFetcher()
    tickers = fetcher.get_universe()

    print(f"[OK] Fetched {len(tickers)} tickers")
    print(f"[OK] Sample tickers: {', '.join(tickers[:10])}")

    # Test is flexible to handle both full S&P 500 and fallback list
    assert len(tickers) >= 100, f"Expected >=100 tickers, got {len(tickers)}"
    assert 'AAPL' in tickers, "AAPL should be in universe"
    assert 'MSFT' in tickers, "MSFT should be in universe"

    if len(tickers) < 400:
        print(f"[WARN] Using fallback universe ({len(tickers)} tickers) - Wikipedia fetch may have failed")

    print("[PASS] Universe fetching works")
    return tickers

def test_price_fetching(tickers):
    """Test price data fetching for a small subset."""
    print("\n" + "="*70)
    print("TEST 2: Fetching Price Data (10 tickers, 1 year)")
    print("="*70)

    fetcher = YFinanceFetcher()
    test_tickers = tickers[:10]

    prices = fetcher.get_price_data(
        start_date='2023-01-01',
        end_date='2024-01-01',
        tickers=test_tickers,
        use_cache=False  # Force fresh fetch for test
    )

    print(f"[OK] Shape: {prices.shape}")
    print(f"[OK] Columns: {list(prices.columns)}")
    print(f"[OK] Date range: {prices.index.min()} to {prices.index.max()}")
    print(f"[OK] Missing data: {prices.isna().sum().sum()} cells")

    assert prices.shape[0] > 200, "Expected >200 trading days in a year"
    assert prices.shape[1] >= 8, f"Expected >=8 successful tickers out of 10"

    # Test caching
    print("\n  Testing cache...")
    prices_cached = fetcher.get_price_data(
        start_date='2023-01-01',
        end_date='2024-01-01',
        tickers=test_tickers,
        use_cache=True,
        show_progress=False
    )

    assert prices_cached.equals(prices), "Cached data should match fresh data"
    print("  [OK] Cache working correctly")

    print("[PASS] Price fetching works")
    return prices

def test_fundamental_fetching(tickers):
    """Test fundamental data fetching."""
    print("\n" + "="*70)
    print("TEST 3: Fetching Fundamental Data (10 tickers)")
    print("="*70)

    fetcher = YFinanceFetcher()
    test_tickers = tickers[:10]

    fundamentals = fetcher.get_fundamental_data(
        tickers=test_tickers,
        use_cache=False
    )

    print(f"[OK] Shape: {fundamentals.shape}")
    print(f"[OK] Columns: {list(fundamentals.columns)[:5]}...")
    print(f"\nData completeness by field:")

    for col in fundamentals.columns[:10]:
        completeness = fundamentals[col].notna().sum() / len(fundamentals)
        print(f"  {col:25s}: {completeness:6.1%}")

    # Validate quality
    is_valid, metrics = fetcher.validate_data_quality(fundamentals, min_completeness=0.70)
    print(f"\n[OK] Overall completeness: {metrics['overall']:.1%}")
    print(f"[OK] Quality check: {'PASS' if is_valid else 'FAIL'}")

    assert fundamentals.shape[0] >= 8, "Expected >=8 successful tickers"
    assert 'market_cap' in fundamentals.columns, "market_cap should be present"
    assert 'trailing_pe' in fundamentals.columns, "trailing_pe should be present"

    print("[PASS] Fundamental fetching works")
    return fundamentals

def test_error_handling():
    """Test error handling with invalid tickers."""
    print("\n" + "="*70)
    print("TEST 4: Error Handling")
    print("="*70)

    fetcher = YFinanceFetcher()

    # Test with invalid tickers
    invalid_tickers = ['INVALID123', 'FAKE456', 'AAPL']  # Mix of invalid and valid

    prices = fetcher.get_price_data(
        start_date='2023-01-01',
        end_date='2024-01-01',
        tickers=invalid_tickers,
        use_cache=False,
        show_progress=False
    )

    print(f"[OK] Handled invalid tickers gracefully")
    print(f"[OK] Valid columns: {list(prices.columns)}")

    assert 'AAPL' in prices.columns, "Valid ticker should succeed"
    assert 'INVALID123' not in prices.columns, "Invalid ticker should be skipped"

    print("[PASS] Error handling works")

def run_all_tests():
    """Run all tests."""
    print("\n" + "="*70)
    print("QUANTEDGE DATA FETCHER - TEST SUITE")
    print("="*70)

    # Setup logging
    setup_logging(logging.INFO)

    try:
        # Run tests
        tickers = test_universe_fetching()
        prices = test_price_fetching(tickers)
        fundamentals = test_fundamental_fetching(tickers)
        test_error_handling()

        # Final summary
        print("\n" + "="*70)
        print("*** ALL TESTS PASSED ***")
        print("="*70)
        print(f"\nData Fetcher is production-ready!")
        print(f"  - Universe: {len(tickers)} tickers")
        print(f"  - Price data: {prices.shape[0]} days x {prices.shape[1]} stocks")
        print(f"  - Fundamentals: {fundamentals.shape[0]} stocks x {fundamentals.shape[1]} fields")
        print("\nNext step: Implement Factor Library (Prompt 02)")
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
