"""Compare a pytest-benchmark JSON run against a committed baseline.

Absolute timings aren't comparable across machines, so this gates **only** when
the baseline and the current run share a platform + Python minor version. On a
mismatch it reports informationally and exits 0, prompting a re-baseline from
the target environment (see benchmarks/README.md for the ratchet process).

Exit status: 1 if any benchmark's mean regressed beyond the tolerance, else 0.
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any

DEFAULT_TOLERANCE = 0.25  # 25% — generous, to absorb shared-runner noise.


def _load(path: str) -> dict[str, Any]:
    with open(path) as f:
        return json.load(f)


def _means(data: dict[str, Any]) -> dict[str, float]:
    return {b["name"]: b["stats"]["mean"] for b in data["benchmarks"]}


def _platform(data: dict[str, Any]) -> tuple[str, str]:
    info = data.get("machine_info", {})
    python_minor = ".".join(str(info.get("python_version", "")).split(".")[:2])
    return (str(info.get("system", "")), python_minor)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("baseline")
    parser.add_argument("current")
    parser.add_argument("--tolerance", type=float, default=DEFAULT_TOLERANCE)
    args = parser.parse_args()

    baseline = _load(args.baseline)
    current = _load(args.current)

    if _platform(baseline) != _platform(current):
        print(
            f"⚠ baseline platform {_platform(baseline)} != current {_platform(current)}; "
            "skipping the regression gate. Re-baseline from this environment to enable it."
        )
        return 0

    base, cur = _means(baseline), _means(current)
    tolerance = args.tolerance
    regressions: list[tuple[str, float]] = []

    for name in sorted(cur):
        if name not in base:
            print(f"  NEW     {name}: {cur[name] * 1000:.2f}ms (no baseline)")
            continue
        ratio = cur[name] / base[name]
        delta_pct = (ratio - 1) * 100
        label = "REGRESS" if ratio > 1 + tolerance else ("better" if ratio < 1 else "ok")
        print(
            f"  {label:7} {name}: {cur[name] * 1000:.2f}ms "
            f"vs {base[name] * 1000:.2f}ms ({delta_pct:+.1f}%)"
        )
        if ratio > 1 + tolerance:
            regressions.append((name, delta_pct))

    if regressions:
        print(f"\n✗ {len(regressions)} benchmark(s) regressed beyond {tolerance * 100:.0f}%:")
        for name, delta_pct in regressions:
            print(f"   - {name}: {delta_pct:+.1f}%")
        return 1

    print(f"\n✓ no regressions beyond {tolerance * 100:.0f}%")
    return 0


if __name__ == "__main__":
    sys.exit(main())
