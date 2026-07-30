# osiris-pandas

Make pandas pleasant to use from Osiris. Nothing here knows about any domain:
no trading sessions, no factors, no lookback abstractions — just typed, checked
spellings of pandas operations, with localized names and a Python backend that
ships inside the wheel.

## Use

```toml
[project]
dependencies = ["osiris-pandas"]
```

```clojure
(module app.main)
(import osiris-pandas.core :refer [缺失值替换 去空白 转小写 去重计数])

^{:doc "How many distinct entries a hand-typed text column really has."
  :export true}
(defn ^Any 规整后计数 [^Any 文本列]
  (去重计数 (转小写 (去空白 (缺失值替换 文本列 "")))))
```

Every binding declares a call contract — effects, temporal reach, and data
alignment — so the compiler can check causality rather than trust the call.
The temporal claims are about data dependency only: a rolling reducer reads
`[t-window+1, t]`, a shift reads `periods` rows back, everything else reads the
current row. `:availability` is always `:immediate`; when a value becomes
available is a question about your domain, not about pandas.

## Surface

112 bindings, each with an English canonical name and a Chinese localized name.
The groups below correspond to the nine contract shapes the module declares —
the shape is what the compiler checks, so it is worth knowing which one you are
reaching for.

| Shape | Reads | Bindings |
| --- | --- | --- |
| Row-wise | the current row | arithmetic, comparison, logic, text, calendar fields, `where`, `clip`, `round-to`, `between`, missing-data tests, row-wise aggregation across series |
| Rolling | `[t-window+1, t]` | `rolling-sum` `rolling-mean` `rolling-min` `rolling-max` `rolling-median` `rolling-std` `rolling-correlation` |
| Shifted | `periods` rows back | `shift` `diff` `pct-change` |
| Cumulative | every earlier row | `cumulative-sum` `cumulative-product` `cumulative-max` `cumulative-min` `expanding-*` |
| Forward-looking | later rows only | `back-fill` |
| Whole column | every row, later ones included | `rank` `percent-rank` `interpolate` `duplicated` |
| Reduction | every row, yields one value | `series-sum` `series-mean` `series-quantile` `series-count` … |
| Grouped | other rows of the same key | `group-sum` `group-mean` `group-rank` `group-size` … |
| Reshaping | builds or rearranges a frame | `to-frame` `column` `merge-frames` `pivot` `sort-by` `group-aggregate` … |

The temporal claim is the point. `rank` and `back-fill` both read rows that come
later, so both declare an unbounded future; a pipeline that must stay causal can
be checked rather than reviewed by eye.

Domain concepts belong in your own package: build a lookback type, a trading
calendar, or a factor vocabulary on top of these.

## Build

The backend is an ordinary Python file, `src/osiris-pandas/backend/primitives.py`,
named by `py/embed` from `core.osr`. The compiler relocates its content into the
distribution-private runtime package at build time, so the wheel stays
self-contained while the source remains a real `.py` — readable by your editor,
your type checker, and `python -m unittest tests.test_primitives`, with no build
step in between.

## Tests

Two layers, each testing what the other cannot:

```sh
python -m unittest tests.test_primitives   # the Python backend, directly
osr build && pytest dist/tests             # the bindings, from the Osiris side
```

The Osiris tests live in `src/tests/pandas_test.osr`, written with
[osiris-test](https://github.com/mjason/osiris-test)'s `deftest`/`testing`/`is`.
They compile with the project like any other module and land in `dist/tests/`,
where pytest collects them by its ordinary naming convention. `[tool.osiris]
wheel-exclude` in `pyproject.toml` keeps them out of the wheel; the sdist keeps
them, because it is the buildable form of the project.

## Build

```sh
uv build                 # wheel + sdist into dist/
```

`.python-version` pins 3.11 because `osiris_build` requires the build interpreter
to match `targetPython`, and a library should be built at the oldest version it
supports.
