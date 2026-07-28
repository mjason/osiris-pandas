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
