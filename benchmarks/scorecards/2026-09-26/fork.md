# fork benchmark report card

**Status: complete for the measured scope.**

Release, one inference worker, 4–7 requested words. Each completed model: 1,337 English scenarios, 7,437 word predictions per context condition. Exact intended-word match; plausible alternatives are misses.

Methodology: [BENCHMARK_METHODOLOGY.md](../../../BENCHMARK_METHODOLOGY.md). These are engine/request/display-rule measurements on a known development corpus.

## Prediction accuracy

| Model | No context | With context | Context lift (pp) | Coverage none / screen | Precision none / screen | Errors none / screen |
|---|---:|---:|---:|---:|---:|---:|
| Apple Intelligence | 24.4% | 26.9% | +2.51 | 99.9% / 99.9% | 24.4% / 27.0% | 0 / 0 |
| Cotabby Nano | 31.0% | 37.5% | +6.49 | 100.0% / 100.0% | 31.0% / 37.5% | 0 / 0 |
| Cotabby Mini | 34.6% | 41.3% | +6.70 | 100.0% / 100.0% | 34.6% / 41.3% | 0 / 0 |
| Cotabby Base | 33.7% | 43.4% | +9.67 | 100.0% / 100.0% | 33.7% / 43.4% | 0 / 0 |
| Cotabby Pro | 34.0% | 43.9% | +9.90 | 100.0% / 100.0% | 34.0% / 43.9% | 0 / 0 |

## Final prediction latency

Successful generated requests only; suppressions before inference and errors are excluded from latency, but retained in accuracy. This includes request construction and final display eligibility, not debounce, Accessibility, OCR capture, or screen presentation.

| Model | No context p50 / p95 (ms) | With context p50 / p95 (ms) |
|---|---:|---:|
| Apple Intelligence | 466.5 / 558.4 | 507.9 / 597.7 |
| Cotabby Nano | 78.1 / 124.5 | 63.1 / 130.4 |
| Cotabby Mini | 161.1 / 285.9 | 130.9 / 312.3 |
| Cotabby Base | 221.5 / 344.9 | 179.2 / 388.8 |
| Cotabby Pro | 352.5 / 586.7 | 281.6 / 703.1 |

## Useful output and ideal typing savings

Deadline success counts correct **final** output within 500 ms over every word checkpoint. Ideal typing savings assume an oracle accepts only correct next words, one Tab replaces each word, and waiting is free. Spaces/punctuation and the supplied first word are excluded. This is an optimistic, untimed word-character model—not observed acceptance or productivity.

| Model | Correct final by 500 ms, none / screen | Ideal word keystroke reduction, none / screen |
|---|---:|---:|
| Apple Intelligence | 18.1% / 12.2% | 16.6% / 20.0% |
| Cotabby Nano | 31.0% / 37.5% | 18.5% / 23.7% |
| Cotabby Mini | 34.5% / 41.2% | 21.2% / 26.6% |
| Cotabby Base | 33.7% / 43.3% | 20.4% / 27.5% |
| Cotabby Pro | 31.8% / 40.2% | 20.3% / 28.1% |

## Streaming responsiveness

14 fixed phrases × two contexts × three repetitions × reset/prewarmed cache. Missing outputs remain in deadline-success denominators. p50/p95 are conditional on visible output. A cache reset does not mean a cold OS/model service.

| Model | Context / cache | Visible / trials | First visible p50 / p95 (ms) | Correct by 500 ms | Revisions / withdrawals |
|---|---|---:|---:|---:|---:|
| Apple Intelligence | none-reset | 42/42 | 455.1 / 557.2 | 14.3% | 0 / 0 |
| Apple Intelligence | none-prewarmed | 42/42 | 532.5 / 633.2 | 0.0% | 0 / 0 |
| Apple Intelligence | screen-reset | 42/42 | 502.9 / 572.7 | 2.4% | 0 / 0 |
| Apple Intelligence | screen-prewarmed | 42/42 | 579.6 / 635.8 | 0.0% | 0 / 0 |
| Cotabby Nano | none-reset | 42/42 | 69.2 / 72.3 | 35.7% | 0 / 0 |
| Cotabby Nano | none-prewarmed | 42/42 | 44.5 / 46.9 | 35.7% | 0 / 0 |
| Cotabby Nano | screen-reset | 42/42 | 85.6 / 101.0 | 42.9% | 0 / 0 |
| Cotabby Nano | screen-prewarmed | 42/42 | 47.1 / 51.9 | 42.9% | 0 / 0 |
| Cotabby Mini | none-reset | 42/42 | 172.1 / 222.8 | 35.7% | 0 / 0 |
| Cotabby Mini | none-prewarmed | 42/42 | 104.5 / 156.0 | 35.7% | 0 / 0 |
| Cotabby Mini | screen-reset | 42/42 | 200.7 / 318.4 | 57.1% | 0 / 0 |
| Cotabby Mini | screen-prewarmed | 42/42 | 102.4 / 173.1 | 57.1% | 0 / 0 |
| Cotabby Base | none-reset | 42/42 | 169.5 / 235.1 | 28.6% | 0 / 0 |
| Cotabby Base | none-prewarmed | 42/42 | 99.9 / 126.9 | 28.6% | 0 / 0 |
| Cotabby Base | screen-reset | 42/42 | 226.2 / 292.5 | 50.0% | 0 / 0 |
| Cotabby Base | screen-prewarmed | 42/42 | 104.9 / 132.1 | 50.0% | 0 / 0 |
| Cotabby Pro | none-reset | 42/42 | 302.6 / 444.6 | 28.6% | 0 / 0 |
| Cotabby Pro | none-prewarmed | 42/42 | 171.0 / 234.5 | 28.6% | 0 / 0 |
| Cotabby Pro | screen-reset | 42/42 | 398.5 / 562.2 | 47.6% | 0 / 0 |
| Cotabby Pro | screen-prewarmed | 42/42 | 173.2 / 222.8 | 50.0% | 0 / 0 |

## Output hygiene review flags

Fixed patterns flag visible code/template markers, repeated punctuation or words, and assistant-style prefaces. These can include legitimate text and require review; this is not a human-rated quality score.

| Model | Context | Shown outputs flagged | Template/fence | Repeated punctuation | Repeated word | Assistant preface |
|---|---|---:|---:|---:|---:|---:|
| Apple Intelligence | none | 0.0% | 0 | 0 | 0 | 0 |
| Apple Intelligence | screen | 0.0% | 0 | 0 | 0 | 0 |
| Cotabby Nano | none | 0.0% | 0 | 0 | 0 | 0 |
| Cotabby Nano | screen | 0.0% | 0 | 0 | 0 | 0 |
| Cotabby Mini | none | 0.0% | 0 | 0 | 0 | 0 |
| Cotabby Mini | screen | 0.0% | 0 | 0 | 0 | 0 |
| Cotabby Base | none | 0.0% | 0 | 0 | 0 | 0 |
| Cotabby Base | screen | 0.0% | 0 | 0 | 0 | 0 |
| Cotabby Pro | none | 0.0% | 0 | 0 | 0 | 0 |
| Cotabby Pro | screen | 0.0% | 0 | 0 | 0 | 0 |

## Partial-word diagnostic sample

First two phrases per category, every nonzero character offset. Separate from full-corpus next-word accuracy.

| Model | Checkpoints per condition | No context | With context |
|---|---:|---:|---:|
| Apple Intelligence | 232 | 52.2% | 49.6% |
| Cotabby Nano | 232 | 85.3% | 94.0% |
| Cotabby Mini | 232 | 87.1% | 93.5% |
| Cotabby Base | 232 | 88.8% | 93.5% |
| Cotabby Pro | 232 | 85.8% | 93.5% |

## Startup and process resources

Peak RSS includes the app-hosted test harness. CPU seconds cover the full replay. **Apple service memory/CPU and GPU work are excluded**, so these are not cross-backend efficiency rankings. Apple initialization is availability/engine construction; GGUF preparation includes model load/warmup.

| Model | Preparation (ms) | Host peak RSS (MiB) | Host CPU seconds | Run wall seconds |
|---|---:|---:|---:|---:|
| Apple Intelligence | 0.6 | 112.4 | 183.4 | 7640.4 |
| Cotabby Nano | 436.9 | 927.9 | 312.4 | 1209.0 |
| Cotabby Mini | 534.8 | 1547.9 | 370.8 | 2508.1 |
| Cotabby Base | 782.3 | 3981.2 | 393.9 | 3229.4 |
| Cotabby Pro | 1038.1 | 5446.2 | 431.2 | 5241.5 |

## Engine cancellation

Request cancellation at 100 ms, one trial per diagnostic phrase/context. Already completed requests are excluded from drain quantiles. This measures engine cancellation, not stale insertion prevention by the coordinator.

| Model | Interrupted / trials | Already finished | Drain p50 / p95 (ms) | Partial callbacks after cancellation | Interrupted outcomes |
|---|---:|---:|---:|---:|---|
| Apple Intelligence | 28/28 | 0 | 0.2 / 0.3 | 0 | {"cancelled": 28} |
| Cotabby Nano | 27/28 | 1 | 1.7 / 8.9 | 18 | {"cancelled": 27} |
| Cotabby Mini | 28/28 | 0 | 32.4 / 59.3 | 0 | {"cancelled": 28} |
| Cotabby Base | 28/28 | 0 | 39.8 / 71.6 | 0 | {"cancelled": 28} |
| Cotabby Pro | 28/28 | 0 | 71.8 / 165.8 | 0 | {"cancelled": 28} |

## Synthetic editor / production coordinator

Seven prefixes × three repetitions; no screen context, 50 ms configured debounce, 10 ms simulated field publication lag, 2-second observation window. The real coordinator receives input and drives presentation and up to three rapid acceptance commands; OS focus/overlay/insertion are test doubles. Acceptances exercise insertion mechanics, not human preference or reference-text agreement.

| Model | Visible / trials | Input-to-presentation p50 / p95 (ms) | Correct by 500 ms | Accepted / attempts | Insertion mismatches | Blocked-field presentation / acceptance / insertion |
|---|---:|---:|---:|---:|---:|---:|
| Apple Intelligence | 21/21 | 708.8 / 965.6 | 0.0% | 63/63 | 0 | 0 / 0 / 0 |
| Cotabby Nano | 21/21 | 113.4 / 129.9 | 28.6% | 63/63 | 0 | 0 / 0 / 0 |
| Cotabby Mini | 21/21 | 130.0 / 141.2 | 28.6% | 63/63 | 0 | 0 / 0 / 0 |
| Cotabby Base | 21/21 | 160.1 / 176.5 | 14.3% | 63/63 | 0 | 0 / 0 / 0 |
| Cotabby Pro | 21/21 | 202.2 / 237.9 | 14.3% | 63/63 | 0 | 0 / 0 / 0 |

## Category detail

| Model | Category | No context | With context |
|---|---|---:|---:|
| Apple Intelligence | conversation | 23.6% | 29.1% |
| Apple Intelligence | science | 34.0% | 33.5% |
| Apple Intelligence | entertainment | 22.1% | 24.3% |
| Apple Intelligence | work | 25.2% | 25.3% |
| Apple Intelligence | technology | 16.8% | 18.2% |
| Apple Intelligence | everyday | 28.8% | 31.9% |
| Apple Intelligence | travel | 21.0% | 27.1% |
| Cotabby Nano | conversation | 33.3% | 42.8% |
| Cotabby Nano | science | 45.4% | 46.2% |
| Cotabby Nano | entertainment | 26.5% | 33.4% |
| Cotabby Nano | work | 29.6% | 36.8% |
| Cotabby Nano | technology | 26.0% | 31.5% |
| Cotabby Nano | everyday | 27.7% | 37.1% |
| Cotabby Nano | travel | 29.4% | 35.9% |
| Cotabby Mini | conversation | 35.5% | 48.3% |
| Cotabby Mini | science | 47.0% | 49.2% |
| Cotabby Mini | entertainment | 30.0% | 38.2% |
| Cotabby Mini | work | 33.3% | 38.6% |
| Cotabby Mini | technology | 29.7% | 33.4% |
| Cotabby Mini | everyday | 32.6% | 42.2% |
| Cotabby Mini | travel | 34.5% | 40.5% |
| Cotabby Base | conversation | 33.6% | 50.7% |
| Cotabby Base | science | 45.2% | 46.6% |
| Cotabby Base | entertainment | 30.6% | 42.3% |
| Cotabby Base | work | 31.3% | 41.2% |
| Cotabby Base | technology | 28.2% | 33.1% |
| Cotabby Base | everyday | 34.0% | 45.6% |
| Cotabby Base | travel | 33.5% | 45.6% |
| Cotabby Pro | conversation | 34.6% | 50.7% |
| Cotabby Pro | science | 45.1% | 49.2% |
| Cotabby Pro | entertainment | 31.4% | 42.3% |
| Cotabby Pro | work | 32.3% | 41.6% |
| Cotabby Pro | technology | 28.9% | 34.3% |
| Cotabby Pro | everyday | 33.0% | 46.2% |
| Cotabby Pro | travel | 33.5% | 44.6% |

## Unmeasured dimensions

Actual user acceptance and net typing saved; blinded usefulness/naturalness; live keyboard-to-overlay latency; real cross-app insertion and focus-change safety; cancellation during real typing; system energy/battery drain; idle app cost. These require separate experiments and are not inferred from model-only accuracy.

## Provenance

- **Apple Intelligence:** revision `f31abbd59970a86fc5184d1b6b7525a4d7854c16`; model SHA-256 `Apple system model: private asset hash unavailable`; corpus `b41c8089a58ae1e0ee84b95ac9283cf71db4e713e25bd8fed47220be69d8b0f6`; evidence `/Users/jmcasler/Documents/GitHub/mchamster/cotabby/build/eval/scorecards/2026-09-26/full-v1/fork-apple`.
- **Cotabby Nano:** revision `f31abbd59970a86fc5184d1b6b7525a4d7854c16`; model SHA-256 `febd85051361ccb34d0925744c819f9ae0724117e8f946a2852dd0edfa90a5a1`; corpus `b41c8089a58ae1e0ee84b95ac9283cf71db4e713e25bd8fed47220be69d8b0f6`; evidence `/Users/jmcasler/Documents/GitHub/mchamster/cotabby/build/eval/scorecards/2026-09-26/full-v1/fork-nano`.
- **Cotabby Mini:** revision `f31abbd59970a86fc5184d1b6b7525a4d7854c16`; model SHA-256 `e3daa3f6e5ed8de264fc6e4128713ae1eb0c2649ad69b83f97bfc6a6ddca3da8`; corpus `b41c8089a58ae1e0ee84b95ac9283cf71db4e713e25bd8fed47220be69d8b0f6`; evidence `/Users/jmcasler/Documents/GitHub/mchamster/cotabby/build/eval/scorecards/2026-09-26/full-v1/fork-mini`.
- **Cotabby Base:** revision `f31abbd59970a86fc5184d1b6b7525a4d7854c16`; model SHA-256 `20f49b221691c71d955e1d5a840b6e26329db4a5e1626f702fa4226e80a9c629`; corpus `b41c8089a58ae1e0ee84b95ac9283cf71db4e713e25bd8fed47220be69d8b0f6`; evidence `/Users/jmcasler/Documents/GitHub/mchamster/cotabby/build/eval/scorecards/2026-09-26/full-v1/fork-base`.
- **Cotabby Pro:** revision `f31abbd59970a86fc5184d1b6b7525a4d7854c16`; model SHA-256 `687f4cce47eac6ccfc595fd9517215fb964e5e5be17d4774b25b8add401d6d3c`; corpus `b41c8089a58ae1e0ee84b95ac9283cf71db4e713e25bd8fed47220be69d8b0f6`; evidence `/Users/jmcasler/Documents/GitHub/mchamster/cotabby/build/eval/scorecards/2026-09-26/full-v1/fork-pro`.

Hardware: {"hw.model": "MacBookPro18,4", "hw.memsize": "34359738368", "hw.ncpu": "10", "machdep.cpu.brand_string": "Apple M1 Max"}.

OS: ProductName:		macOS; ProductVersion:		27.0; BuildVersion:		26A428.

Power at launch: Now drawing from 'AC Power';  -InternalBattery-0 (id=24903779)	80%; AC attached; not charging present: true.
