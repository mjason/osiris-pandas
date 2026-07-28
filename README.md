# osiris-pandas

Typed pandas bindings for Osiris: localized names, declared call contracts, and
a package-owned Python backend that ships inside the wheel.

## Use

```toml
[project]
dependencies = ["osiris-pandas"]
```

```clojure
(module app.main)
(import osiris_pandas.core :refer [回看窗口 均值])

^{:doc "Rolling mean over a lookback window." :export true}
(defn ^Any 均线 [^Any 收盘价 ^Int 周期]
  (均值 (回看窗口 收盘价 :周期 周期)))
```

Every binding declares a call contract — effects, temporal reach, and data
alignment — so the compiler can check causality rather than trust the call.

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
