"""Pandas primitives with explicit, causal window semantics.

Every rolling reducer reads `[t-window+1, t]` and never a future row. That is
what lets the Osiris declarations state a temporal reach the compiler can check,
and it is the only opinion this module holds. Nothing here knows about trading
sessions, factors, or any other domain.

Each function is a thin, typed spelling of a pandas or numpy operation. Where
pandas would silently accept a nonsensical argument, these raise instead, so a
mistake surfaces at the call rather than as a quietly wrong column.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd


def _positive_int(value: int, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError(f"{name} must be a positive integer, got {value!r}")
    return value


def _window(window: int, min_periods: int | None) -> tuple[int, int]:
    window = _positive_int(window, "window")
    if min_periods is None:
        min_periods = window
    min_periods = _positive_int(min_periods, "min_periods")
    if min_periods > window:
        raise ValueError("min_periods cannot exceed window")
    return window, min_periods


def _rolling(values: pd.Series, window: int, min_periods: int | None) -> Any:
    window, min_periods = _window(window, min_periods)
    return values.rolling(window=window, min_periods=min_periods, center=False)


# Rolling reducers over [t-window+1, t].


def rolling_sum(values: pd.Series, window: int, min_periods: int | None = None) -> pd.Series:
    return _rolling(values, window, min_periods).sum()


def rolling_mean(values: pd.Series, window: int, min_periods: int | None = None) -> pd.Series:
    return _rolling(values, window, min_periods).mean()


def rolling_min(values: pd.Series, window: int, min_periods: int | None = None) -> pd.Series:
    return _rolling(values, window, min_periods).min()


def rolling_max(values: pd.Series, window: int, min_periods: int | None = None) -> pd.Series:
    return _rolling(values, window, min_periods).max()


def rolling_median(values: pd.Series, window: int, min_periods: int | None = None) -> pd.Series:
    return _rolling(values, window, min_periods).median()


def rolling_std(
    values: pd.Series, window: int, ddof: int = 1, min_periods: int | None = None
) -> Any:
    if isinstance(ddof, bool) or not isinstance(ddof, int) or ddof < 0:
        raise ValueError(f"ddof must be a non-negative integer, got {ddof!r}")
    return _rolling(values, window, min_periods).std(ddof=ddof)


def rolling_correlation(
    left: pd.Series, right: pd.Series, window: int, min_periods: int | None = None
) -> Any:
    if not left.index.equals(right.index):
        raise ValueError("correlated series must have identical labelled indexes")
    return _rolling(left, window, min_periods).corr(right)


def ewm_mean(values: pd.Series, span: int) -> pd.Series:
    span = _positive_int(span, "span")
    return values.ewm(span=span, adjust=False).mean()


# Shifting along the ordered axis. Negative periods would read the future.


def shift(values: pd.Series, periods: int = 1) -> pd.Series:
    if isinstance(periods, bool) or not isinstance(periods, int) or periods < 0:
        raise ValueError(f"periods must be a non-negative integer, got {periods!r}")
    return values.shift(periods)


def diff(values: pd.Series, periods: int = 1) -> pd.Series:
    return values - shift(values, periods)


def pct_change(values: pd.Series, periods: int = 1) -> pd.Series:
    return values / shift(values, periods) - 1


# Missing data.


def is_missing(values: Any) -> Any:
    return pd.isna(values)


def fill_missing(values: Any, replacement: Any = 0) -> Any:
    return values.fillna(replacement)


def forward_fill(values: Any) -> Any:
    return values.ffill()


# Row-wise selection and membership.


def where(condition: pd.Series, true_value: Any, false_value: Any) -> pd.Series:
    """Row-wise choice that keeps the condition's index."""
    result = pd.Series(true_value, index=condition.index)
    return result.where(condition, false_value)


def in_values(values: pd.Series, candidates: Any) -> pd.Series:
    return values.isin(list(candidates))


def contains_any(values: pd.Series, needles: Any) -> pd.Series:
    needles = list(needles)
    if not needles:
        return pd.Series(False, index=values.index)
    pattern = "|".join(pd.Series(needles, dtype="string").str.replace(
        r"([.^$*+?()\[\]{}|\\])", r"\\\1", regex=True
    ))
    return values.str.contains(pattern, na=False, regex=True)


# Elementwise arithmetic and comparison. These exist so a declaration can carry
# a checked contract, not because pandas lacks the operator.


def add(left: Any, right: Any) -> Any:
    return left + right


def subtract(left: Any, right: Any) -> Any:
    return left - right


def multiply(left: Any, right: Any) -> Any:
    return left * right


def divide(left: Any, right: Any) -> Any:
    return left / right


def absolute(values: Any) -> Any:
    return abs(values)


def log1p(values: Any) -> Any:
    return np.log1p(values)


def as_integer(values: Any) -> Any:
    return values.astype("Int64")


def elementwise_max(left: Any, right: Any) -> Any:
    return np.maximum(left, right)


def elementwise_min(left: Any, right: Any) -> Any:
    return np.minimum(left, right)


def greater_than(left: Any, right: Any) -> Any:
    return left > right


def greater_equal(left: Any, right: Any) -> Any:
    return left >= right


def less_than(left: Any, right: Any) -> Any:
    return left < right


def less_equal(left: Any, right: Any) -> Any:
    return left <= right


def equal(left: Any, right: Any) -> Any:
    return left == right


def not_equal(left: Any, right: Any) -> Any:
    return left != right


def logical_and(left: Any, right: Any) -> Any:
    return left & right


def logical_or(left: Any, right: Any) -> Any:
    return left | right


def logical_not(value: Any) -> Any:
    return ~value


# Across several aligned series, row by row.


def _align(values: tuple[Any, ...]) -> pd.DataFrame:
    series = next((value for value in values if isinstance(value, pd.Series)), None)
    if series is None:
        raise ValueError("at least one argument must be a Series")
    columns = [
        value if isinstance(value, pd.Series) else pd.Series(value, index=series.index)
        for value in values
    ]
    return pd.concat(columns, axis=1)


def row_sum(*values: Any) -> pd.Series:
    return _align(values).sum(axis=1, skipna=True)


def row_mean(*values: Any) -> pd.Series:
    return _align(values).mean(axis=1, skipna=True)


def row_max(*values: Any) -> pd.Series:
    return _align(values).max(axis=1, skipna=True)


def row_min(*values: Any) -> pd.Series:
    return _align(values).min(axis=1, skipna=True)
