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


def rolling_sum(
    values: pd.Series, window: int, min_periods: int | None = None
) -> pd.Series:
    return _rolling(values, window, min_periods).sum()


def rolling_mean(
    values: pd.Series, window: int, min_periods: int | None = None
) -> pd.Series:
    return _rolling(values, window, min_periods).mean()


def rolling_min(
    values: pd.Series, window: int, min_periods: int | None = None
) -> pd.Series:
    return _rolling(values, window, min_periods).min()


def rolling_max(
    values: pd.Series, window: int, min_periods: int | None = None
) -> pd.Series:
    return _rolling(values, window, min_periods).max()


def rolling_median(
    values: pd.Series, window: int, min_periods: int | None = None
) -> pd.Series:
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
    pattern = "|".join(
        pd.Series(needles, dtype="string").str.replace(
            r"([.^$*+?()\[\]{}|\\])", r"\\\1", regex=True
        )
    )
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


# Whole-series reductions. These leave the row axis entirely, so their
# declarations say `preserves-length false` and `reshapes true`.


def series_sum(values: pd.Series) -> Any:
    return values.sum()


def series_mean(values: pd.Series) -> Any:
    return values.mean()


def series_min(values: pd.Series) -> Any:
    return values.min()


def series_max(values: pd.Series) -> Any:
    return values.max()


def series_median(values: pd.Series) -> Any:
    return values.median()


def series_std(values: pd.Series, ddof: int = 1) -> Any:
    if isinstance(ddof, bool) or not isinstance(ddof, int) or ddof < 0:
        raise ValueError(f"ddof must be a non-negative integer, got {ddof!r}")
    return values.std(ddof=ddof)


def series_count(values: pd.Series) -> int:
    return int(values.count())


def series_nunique(values: pd.Series) -> int:
    return int(values.nunique())


def series_quantile(values: pd.Series, q: float) -> Any:
    if not isinstance(q, (int, float)) or isinstance(q, bool) or not 0.0 <= q <= 1.0:
        raise ValueError(f"q must be between 0 and 1, got {q!r}")
    return values.quantile(q)


def series_any(values: pd.Series) -> bool:
    return bool(values.any())


def series_all(values: pd.Series) -> bool:
    return bool(values.all())


# Reading the whole column while keeping one value per row. `rank` looks at
# later rows, which is why its declaration admits an unbounded future.


def rank(
    values: pd.Series, method: str = "average", ascending: bool = True
) -> pd.Series:
    if method not in ("average", "min", "max", "first", "dense"):
        raise ValueError(f"unsupported rank method {method!r}")
    if not isinstance(ascending, bool):
        raise ValueError(f"ascending must be a boolean, got {ascending!r}")
    return values.rank(method=method, ascending=ascending)


def percent_rank(values: pd.Series, ascending: bool = True) -> pd.Series:
    if not isinstance(ascending, bool):
        raise ValueError(f"ascending must be a boolean, got {ascending!r}")
    return values.rank(pct=True, ascending=ascending)


# Cumulative and expanding reductions read every earlier row and no later one.


def cumulative_sum(values: pd.Series) -> pd.Series:
    return values.cumsum()


def cumulative_product(values: pd.Series) -> pd.Series:
    return values.cumprod()


def cumulative_max(values: pd.Series) -> pd.Series:
    return values.cummax()


def cumulative_min(values: pd.Series) -> pd.Series:
    return values.cummin()


def _expanding(values: pd.Series, min_periods: int) -> Any:
    return values.expanding(min_periods=_positive_int(min_periods, "min_periods"))


def expanding_sum(values: pd.Series, min_periods: int = 1) -> pd.Series:
    return _expanding(values, min_periods).sum()


def expanding_mean(values: pd.Series, min_periods: int = 1) -> pd.Series:
    return _expanding(values, min_periods).mean()


def expanding_min(values: pd.Series, min_periods: int = 1) -> pd.Series:
    return _expanding(values, min_periods).min()


def expanding_max(values: pd.Series, min_periods: int = 1) -> pd.Series:
    return _expanding(values, min_periods).max()


def expanding_std(values: pd.Series, min_periods: int = 2, ddof: int = 1) -> Any:
    if isinstance(ddof, bool) or not isinstance(ddof, int) or ddof < 0:
        raise ValueError(f"ddof must be a non-negative integer, got {ddof!r}")
    return _expanding(values, min_periods).std(ddof=ddof)


# Numeric shaping. All row-wise.


def clip(values: Any, lower: Any = None, upper: Any = None) -> Any:
    if lower is None and upper is None:
        raise ValueError("clip needs a lower bound, an upper bound, or both")
    return values.clip(lower=lower, upper=upper)


def round_to(values: Any, digits: int = 0) -> Any:
    if isinstance(digits, bool) or not isinstance(digits, int):
        raise ValueError(f"digits must be an integer, got {digits!r}")
    return values.round(digits)


def floor(values: Any) -> Any:
    return np.floor(values)


def ceiling(values: Any) -> Any:
    return np.ceil(values)


def power(left: Any, right: Any) -> Any:
    return left**right


def modulo(left: Any, right: Any) -> Any:
    return left % right


def floor_divide(left: Any, right: Any) -> Any:
    return left // right


def sign(values: Any) -> Any:
    return np.sign(values)


def square_root(values: Any) -> Any:
    return np.sqrt(values)


def between(
    values: pd.Series, lower: Any, upper: Any, inclusive: str = "both"
) -> pd.Series:
    if inclusive not in ("both", "neither", "left", "right"):
        raise ValueError(f"unsupported inclusive mode {inclusive!r}")
    return values.between(lower, upper, inclusive=inclusive)


# Missing data and duplicates. `drop_missing` and `drop_duplicates` change the
# row count, which their declarations state.


def back_fill(values: Any) -> Any:
    return values.bfill()


def drop_missing(values: pd.Series) -> pd.Series:
    return values.dropna()


def interpolate(values: pd.Series, method: str = "linear") -> pd.Series:
    if method not in ("linear", "nearest", "pad"):
        raise ValueError(f"unsupported interpolation method {method!r}")
    return values.interpolate(method=method, limit_direction="forward")


def duplicated(values: pd.Series, keep: str = "first") -> pd.Series:
    if keep not in ("first", "last"):
        raise ValueError(f"unsupported keep mode {keep!r}")
    return values.duplicated(keep=keep)


def drop_duplicates(values: pd.Series, keep: str = "first") -> pd.Series:
    if keep not in ("first", "last"):
        raise ValueError(f"unsupported keep mode {keep!r}")
    return values.drop_duplicates(keep=keep)


def replace_values(values: pd.Series, mapping: Any) -> pd.Series:
    return values.replace(dict(mapping))


# Text. Every one of these is `.str` on a text column.


def lower_case(values: pd.Series) -> pd.Series:
    return values.str.lower()


def upper_case(values: pd.Series) -> pd.Series:
    return values.str.upper()


def strip_text(values: pd.Series) -> pd.Series:
    return values.str.strip()


def starts_with(values: pd.Series, prefix: str) -> pd.Series:
    return values.str.startswith(prefix, na=False)


def ends_with(values: pd.Series, suffix: str) -> pd.Series:
    return values.str.endswith(suffix, na=False)


def text_length(values: pd.Series) -> pd.Series:
    return values.str.len()


def text_slice(values: pd.Series, start: int, stop: int) -> pd.Series:
    return values.str.slice(start, stop)


def text_replace(values: pd.Series, old: str, new: str) -> pd.Series:
    return values.str.replace(old, new, regex=False)


def text_concat(left: pd.Series, right: Any) -> pd.Series:
    return left.str.cat(right, na_rep="")


# Calendar fields. `to_datetime` parses; the rest read a parsed column.


def to_datetime(values: Any) -> pd.Series:
    return pd.to_datetime(values)


def year(values: pd.Series) -> pd.Series:
    return values.dt.year


def month(values: pd.Series) -> pd.Series:
    return values.dt.month


def day(values: pd.Series) -> pd.Series:
    return values.dt.day


def weekday(values: pd.Series) -> pd.Series:
    return values.dt.weekday


def day_of_year(values: pd.Series) -> pd.Series:
    return values.dt.dayofyear


def date_difference(left: pd.Series, right: pd.Series) -> pd.Series:
    return (left - right).dt.days


# Grouped transforms. Each returns one value per input row, computed within the
# row's group, so the row axis survives but the value depends on other rows of
# the same key — which is why these declare an entity axis and an unbounded
# reach in both directions.


def _grouped(values: pd.Series, keys: Any) -> Any:
    if isinstance(keys, pd.Series):
        if not values.index.equals(keys.index):
            raise ValueError("grouped series must have identical labelled indexes")
        return values.groupby(keys, sort=False)
    return values.groupby(list(keys), sort=False)


def group_sum(values: pd.Series, keys: Any) -> pd.Series:
    return _grouped(values, keys).transform("sum")


def group_mean(values: pd.Series, keys: Any) -> pd.Series:
    return _grouped(values, keys).transform("mean")


def group_min(values: pd.Series, keys: Any) -> pd.Series:
    return _grouped(values, keys).transform("min")


def group_max(values: pd.Series, keys: Any) -> pd.Series:
    return _grouped(values, keys).transform("max")


def group_std(values: pd.Series, keys: Any) -> pd.Series:
    return _grouped(values, keys).transform("std")


def group_size(values: pd.Series, keys: Any) -> pd.Series:
    return _grouped(values, keys).transform("size")


def group_rank(values: pd.Series, keys: Any, ascending: bool = True) -> pd.Series:
    if not isinstance(ascending, bool):
        raise ValueError(f"ascending must be a boolean, got {ascending!r}")
    return _grouped(values, keys).rank(method="average", ascending=ascending)


def group_percent_rank(
    values: pd.Series, keys: Any, ascending: bool = True
) -> pd.Series:
    if not isinstance(ascending, bool):
        raise ValueError(f"ascending must be a boolean, got {ascending!r}")
    return _grouped(values, keys).rank(pct=True, ascending=ascending)


def group_cumulative_sum(values: pd.Series, keys: Any) -> pd.Series:
    return _grouped(values, keys).cumsum()


def group_shift(values: pd.Series, keys: Any, periods: int = 1) -> pd.Series:
    if isinstance(periods, bool) or not isinstance(periods, int) or periods < 0:
        raise ValueError(f"periods must be a non-negative integer, got {periods!r}")
    return _grouped(values, keys).shift(periods)


# Reshaping across columns. These build or consume a frame, so they reshape.


def to_frame(names: Any, columns: Any) -> pd.DataFrame:
    names = list(names)
    columns = list(columns)
    if len(names) != len(columns):
        raise ValueError("to_frame needs one name per column")
    return pd.DataFrame(dict(zip(names, columns)))


def column(frame: pd.DataFrame, name: str) -> pd.Series:
    if name not in frame.columns:
        raise KeyError(f"no column named {name!r}")
    return frame[name]


def with_column(frame: pd.DataFrame, name: str, values: Any) -> pd.DataFrame:
    return frame.assign(**{name: values})


def select_columns(frame: pd.DataFrame, names: Any) -> pd.DataFrame:
    names = list(names)
    missing = [name for name in names if name not in frame.columns]
    if missing:
        raise KeyError(f"no column named {missing[0]!r}")
    return frame[names]


def merge_frames(
    left: pd.DataFrame, right: pd.DataFrame, on: Any, how: str = "left"
) -> pd.DataFrame:
    if how not in ("left", "right", "inner", "outer"):
        raise ValueError(f"unsupported join {how!r}")
    return left.merge(right, on=list(on), how=how)


def concat_rows(frames: Any) -> pd.DataFrame:
    frames = list(frames)
    if not frames:
        raise ValueError("concat_rows needs at least one frame")
    return pd.concat(frames, axis=0, ignore_index=True)


def pivot(frame: pd.DataFrame, index: str, columns: str, values: str) -> pd.DataFrame:
    return frame.pivot(index=index, columns=columns, values=values)


def sort_by(frame: pd.DataFrame, names: Any, ascending: bool = True) -> pd.DataFrame:
    if not isinstance(ascending, bool):
        raise ValueError(f"ascending must be a boolean, got {ascending!r}")
    return frame.sort_values(list(names), ascending=ascending)


def group_aggregate(
    frame: pd.DataFrame, keys: Any, name: str, how: str
) -> pd.DataFrame:
    if how not in ("sum", "mean", "min", "max", "std", "count", "median"):
        raise ValueError(f"unsupported aggregation {how!r}")
    return frame.groupby(list(keys), sort=False)[name].agg(how).reset_index()
