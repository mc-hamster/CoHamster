# Upstream versus fork benchmark comparison

Deltas are **fork minus upstream**. Positive accuracy is better; negative latency is faster. Same installed GGUF bytes and corpus; each version retains its own production prompt/runtime/display behavior.

95% intervals use 2,000 paired, category-stratified phrase bootstrap resamples (seed 1337). They describe corpus sampling uncertainty conditional on these runs; they do not capture Apple stochasticity or all machine/thermal timing variation. This known development corpus is not held out.

| Model | Context | Upstream accuracy | Fork accuracy | Difference (pp) | 95% interval (pp) | Final p95 delta (ms) | Coverage delta (pp) |
|---|---|---:|---:|---:|---:|---:|---:|
| Apple Intelligence | none | 23.8% | 24.4% | +0.56 | [-0.15, +1.26] | 38.5 | -0.08 |
| Apple Intelligence | screen | 25.0% | 26.9% | +1.88 | [+1.01, +2.72] | -18.2 | -0.09 |
| Cotabby Nano | none | 28.1% | 31.0% | +2.90 | [+2.22, +3.61] | 16.7 | +0.04 |
| Cotabby Nano | screen | 33.1% | 37.5% | +4.42 | [+3.70, +5.14] | 11.8 | +0.11 |
| Cotabby Mini | none | 30.3% | 34.6% | +4.29 | [+3.61, +4.99] | 63.3 | -0.01 |
| Cotabby Mini | screen | 38.3% | 41.3% | +2.94 | [+2.29, +3.57] | 43.2 | +0.09 |
| Cotabby Base | none | 28.2% | 33.7% | +5.49 | [+4.74, +6.27] | 70.5 | +0.00 |
| Cotabby Base | screen | 36.0% | 43.4% | +7.40 | [+6.56, +8.25] | 48.5 | -0.01 |
| Cotabby Pro | none | 28.3% | 34.0% | +5.67 | [+4.96, +6.45] | 138.4 | +0.01 |
| Cotabby Pro | screen | 37.0% | 43.9% | +6.94 | [+6.09, +7.80] | 94.5 | +0.00 |

## Partial words and ideal typing savings

Partial-word results use the 14-phrase diagnostic sample. Ideal typing savings use full-corpus word predictions with perfect acceptance choices and free waiting; they are not observed productivity.

| Model | Context | Partial accuracy upstream → fork | Ideal word keystroke reduction upstream → fork |
|---|---|---:|---:|
| Apple Intelligence | none | 44.4% → 52.2% | 16.0% → 16.6% |
| Apple Intelligence | screen | 45.3% → 49.6% | 18.8% → 20.0% |
| Cotabby Nano | none | 2.6% → 85.3% | 15.7% → 18.5% |
| Cotabby Nano | screen | 3.9% → 94.0% | 20.1% → 23.7% |
| Cotabby Mini | none | 1.3% → 87.1% | 17.7% → 21.2% |
| Cotabby Mini | screen | 2.2% → 93.5% | 23.9% → 26.6% |
| Cotabby Base | none | 1.3% → 88.8% | 16.8% → 20.4% |
| Cotabby Base | screen | 0.9% → 93.5% | 22.5% → 27.5% |
| Cotabby Pro | none | 0.0% → 85.8% | 17.3% → 20.3% |
| Cotabby Pro | screen | 0.0% → 93.5% | 23.6% → 28.1% |

## Output hygiene flags

Percentage of shown outputs matching fixed review patterns. False positives are possible; these are neither human ratings nor confirmed defect rates.

| Model | Context | Upstream | Fork |
|---|---|---:|---:|
| Apple Intelligence | none | 0.0% | 0.0% |
| Apple Intelligence | screen | 0.1% | 0.0% |
| Cotabby Nano | none | 0.0% | 0.0% |
| Cotabby Nano | screen | 0.0% | 0.0% |
| Cotabby Mini | none | 0.0% | 0.0% |
| Cotabby Mini | screen | 0.0% | 0.0% |
| Cotabby Base | none | 0.0% | 0.0% |
| Cotabby Base | screen | 0.0% | 0.0% |
| Cotabby Pro | none | 0.0% | 0.0% |
| Cotabby Pro | screen | 0.0% | 0.0% |

## Streaming comparison

First-visible medians are conditional on a displayed result. Correct-by-deadline percentages include missing and wrong predictions in their denominator. Same 14 phrases, three repetitions.

| Model | Context / cache | First-visible p50 upstream → fork (ms) | Correct by 500 ms upstream → fork |
|---|---|---:|---:|
| Apple Intelligence | none-reset | 455.4 → 455.1 | 7.1% → 14.3% |
| Apple Intelligence | none-prewarmed | 553.8 → 532.5 | 0.0% → 0.0% |
| Apple Intelligence | screen-reset | 521.0 → 502.9 | 0.0% → 2.4% |
| Apple Intelligence | screen-prewarmed | 558.3 → 579.6 | 0.0% → 0.0% |
| Cotabby Nano | none-reset | 38.8 → 69.2 | 14.3% → 35.7% |
| Cotabby Nano | none-prewarmed | 38.6 → 44.5 | 14.3% → 35.7% |
| Cotabby Nano | screen-reset | 55.8 → 85.6 | 14.3% → 42.9% |
| Cotabby Nano | screen-prewarmed | 55.9 → 47.1 | 14.3% → 42.9% |
| Cotabby Mini | none-reset | 72.3 → 172.1 | 21.4% → 35.7% |
| Cotabby Mini | none-prewarmed | 72.6 → 104.5 | 21.4% → 35.7% |
| Cotabby Mini | screen-reset | 122.1 → 200.7 | 35.7% → 57.1% |
| Cotabby Mini | screen-prewarmed | 123.2 → 102.4 | 35.7% → 57.1% |
| Cotabby Base | none-reset | 112.6 → 169.5 | 14.3% → 28.6% |
| Cotabby Base | none-prewarmed | 108.3 → 99.9 | 14.3% → 28.6% |
| Cotabby Base | screen-reset | 185.1 → 226.2 | 35.7% → 50.0% |
| Cotabby Base | screen-prewarmed | 176.9 → 104.9 | 28.6% → 50.0% |
| Cotabby Pro | none-reset | 201.4 → 302.6 | 14.3% → 28.6% |
| Cotabby Pro | none-prewarmed | 71.3 → 171.0 | 14.3% → 28.6% |
| Cotabby Pro | screen-reset | 331.1 → 398.5 | 14.3% → 47.6% |
| Cotabby Pro | screen-prewarmed | 72.3 → 173.2 | 35.7% → 50.0% |

## Host memory and cancellation

Host peak RSS includes the test harness and excludes Apple model services. Cancellation p95 includes only requests still running at 100 ms; already completed requests are excluded.

| Model | Host peak RSS upstream → fork (MiB) | Cancellation drain p95 upstream → fork (ms) |
|---|---:|---:|
| Apple Intelligence | 121.6 → 112.4 | 0.3 → 0.3 |
| Cotabby Nano | 875.3 → 927.9 | 7.0 → 8.9 |
| Cotabby Mini | 1490.7 → 1547.9 | 18.9 → 59.3 |
| Cotabby Base | 3959.1 → 3981.2 | 84.7 → 71.6 |
| Cotabby Pro | 5459.0 → 5446.2 | 210.6 → 165.8 |

## Synthetic editor interaction

Actual coordinator with fake OS boundaries, 21 pauses per model, no screen context. Timings include configured debounce and simulated field publication; they are not live AX/pixel measurements.

| Model | Presentation p50 upstream → fork (ms) | Correct by 500 ms upstream → fork | Insertion mismatches upstream → fork | Blocked-field inserted trials upstream → fork |
|---|---:|---:|---:|---:|
| Apple Intelligence | 737.1 → 708.8 | 0.0% → 0.0% | 0 → 0 | 0 → 0 |
| Cotabby Nano | 115.4 → 113.4 | 28.6% → 28.6% | 0 → 0 | 0 → 0 |
| Cotabby Mini | 131.9 → 130.0 | 28.6% → 28.6% | 0 → 0 | 0 → 0 |
| Cotabby Base | 150.3 → 160.1 | 14.3% → 14.3% | 0 → 0 | 0 → 0 |
| Cotabby Pro | 192.1 → 202.2 | 14.3% → 14.3% | 0 → 0 | 0 → 0 |

[Upstream report card](upstream.md) · [Fork report card](fork.md) · [Methodology](../../../BENCHMARK_METHODOLOGY.md)

Full standalone cards retain errors, partial-word diagnostics, streaming deadline success, process-resource limitations, category detail, and evidence identity. No composite winner is assigned.
