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
(import osiris_pandas.core :refer [窗口均值 横向求和 按条件取值 大于])

^{:doc "Rolling mean of a series." :export true}
(defn ^Any 均线 [^Any 序列 ^Int 周期] (窗口均值 序列 周期))
```

Every binding declares a call contract — effects, temporal reach, and data
alignment — so the compiler can check causality rather than trust the call.
The temporal claims are about data dependency only: a rolling reducer reads
`[t-window+1, t]`, a shift reads `periods` rows back, everything else reads the
current row. `:availability` is always `:immediate`; when a value becomes
available is a question about your domain, not about pandas.

## Surface

39 bindings, each with an English canonical name and a Chinese localized name:

| Group | Bindings |
| --- | --- |
| Rolling | `rolling-sum` `rolling-mean` `rolling-min` `rolling-max` `rolling-median` `rolling-std` `rolling-correlation` |
| Along the order | `shift` `diff` `pct-change` `ewm-mean` |
| Missing data | `is-missing` `fill-missing` `forward-fill` |
| Selection | `where` `in-values` `contains-any` |
| Arithmetic | `add` `subtract` `multiply` `divide` `absolute` `log1p` `as-integer` `elementwise-max` `elementwise-min` |
| Comparison | `greater-than` `greater-equal` `less-than` `less-equal` `equal` `not-equal` |
| Logical | `logical-and` `logical-or` `logical-not` |
| Across series | `row-sum` `row-mean` `row-max` `row-min` |

Domain concepts belong in your own package: build a lookback type, a trading
calendar, or a factor vocabulary on top of these.

## Build

The backend is authored as a `~python` provider inside `src/osiris_pandas/core.osr`
and relocated into the distribution-private runtime package at build time, so the
wheel is self-contained.

```sh
uv build                 # wheel + sdist into dist/
```

`.python-version` pins 3.11 because `osiris_build` requires the build interpreter
to match `targetPython`, and a library should be built at the oldest version it
supports.

## Status

The three packaging fixes this package needs are not in a released `osiris-lang`
yet, so `[tool.uv.sources]` points at a local compiler checkout and CI only runs
once a release carries them:

- `osiris_build` rejected PEP 440 post releases, and `pandas` pulls in
  `python-dateutil 2.9.0.post0`, so the wheel could not be built at all;
- extension discovery counted a venv's `lib64 -> lib` symlink twice and reported
  every installed extension as a duplicate of itself, so the wheel could not be
  consumed on Linux;
- `uv`'s cache keys omitted the Python build backend's own sources, so fixing it
  was invisible to dependent projects.

Once released: drop `[tool.uv.sources]`, raise the `osiris-lang` lower bound to
that version, and tag `v0.1.0`.
