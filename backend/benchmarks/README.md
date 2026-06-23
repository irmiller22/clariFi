# Performance benchmarks

Regression benchmarks for clariFi's hot paths (CSV parse, normalization, store
queries, and every analytics service) over a deterministic ~10k-transaction
dataset, plus an end-to-end upload→summary compute path.

## Running

```bash
make bench         # run the suite, write benchmarks/current.json
make bench-check   # run, then compare against benchmarks/baseline.json
```

`benchmarks/current.json` is git-ignored; `benchmarks/baseline.json` is committed
and is the gate.

## The regression gate

`compare.py` compares each benchmark's mean against the baseline and **fails when
any regresses beyond the tolerance** (default 25%, generous on purpose to absorb
shared-CI-runner noise). CI runs this on every push/PR (`.github/workflows/perf.yml`).

Absolute timings are not comparable across machines, so the gate **only enforces
when the baseline and the current run share a platform + Python minor version**.
On a mismatch it prints a warning and passes, prompting a re-baseline. This is why
a baseline committed from a laptop won't (falsely) fail or pass on the Linux CI
runner — it simply won't gate until a CI-generated baseline is committed.

## Bootstrapping & the ratchet (incremental-only improvement)

1. The committed baseline ships from a developer machine, so CI initially reports
   benchmarks informationally (platform mismatch → no gate).
2. To **activate the gate**: download the `benchmark-results` artifact from a CI
   run on `main`, save it as `benchmarks/baseline.json`, and commit it. Now CI runs
   on the same platform as the baseline and the gate is live.
3. To **ratchet**: when an intentional optimization lands and CI shows the new
   (faster) numbers, repeat step 2 to make the improved numbers the new baseline.

Because you only ever replace the baseline with an equal-or-faster run, the
recorded thresholds move in one direction — down. A later regression is measured
against the best number we've achieved, not a stale slow one.

## Not covered

Frontend performance is **not** benchmarked here — a green perf job covers backend
compute only.
