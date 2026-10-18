"""
Factor Library Module

This module contains implementations of quantitative factors for stock selection.
Each factor is designed to be composable, tested, and production-ready.

Available Factors:
    - Magic Formula (Quality + Value combined)
    - Individual quality metrics (ROE, ROIC, Operating Margin)
    - Individual value metrics (P/E, P/B, EV/EBITDA)
"""

from .magic_formula import (
    MagicFormulaCalculator,
    calculate_magic_formula_score,
    get_magic_formula_rankings
)

__all__ = [
    'MagicFormulaCalculator',
    'calculate_magic_formula_score',
    'get_magic_formula_rankings',
]
