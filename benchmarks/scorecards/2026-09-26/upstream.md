# upstream benchmark report card

**Status: complete for the measured scope.**

Release, one inference worker, 4–7 requested words. Each completed model: 1,337 English scenarios, 7,437 word predictions per context condition. Exact intended-word match; plausible alternatives are misses.

Methodology: [BENCHMARK_METHODOLOGY.md](../../../BENCHMARK_METHODOLOGY.md). These are engine/request/display-rule measurements on a known development corpus.

## Prediction accuracy

| Model | No context | With context | Context lift (pp) | Coverage none / screen | Precision none / screen | Errors none / screen |
|---|---:|---:|---:|---:|---:|---:|
| Apple Intelligence | 23.8% | 25.0% | +1.20 | 99.9% / 100.0% | 23.9% / 25.0% | 0 / 0 |
| Cotabby Nano | 28.1% | 33.1% | +4.98 | 100.0% / 99.9% | 28.1% / 33.1% | 0 / 0 |
| Cotabby Mini | 30.3% | 38.3% | +8.04 | 100.0% / 99.9% | 30.3% / 38.4% | 0 / 0 |
| Cotabby Base | 28.2% | 36.0% | +7.76 | 100.0% / 100.0% | 28.2% / 36.0% | 0 / 0 |
| Cotabby Pro | 28.3% | 37.0% | +8.63 | 100.0% / 100.0% | 28.3% / 37.0% | 0 / 0 |

## Final prediction latency

Successful generated requests only; suppressions before inference and errors are excluded from latency, but retained in accuracy. This includes request construction and final display eligibility, not debounce, Accessibility, OCR capture, or screen presentation.

| Model | No context p50 / p95 (ms) | With context p50 / p95 (ms) |
|---|---:|---:|
| Apple Intelligence | 460.7 / 519.9 | 524.0 / 615.9 |
| Cotabby Nano | 74.3 / 107.9 | 79.2 / 118.6 |
| Cotabby Mini | 150.4 / 222.6 | 178.8 / 269.1 |
| Cotabby Base | 178.8 / 274.3 | 147.7 / 340.3 |
| Cotabby Pro | 286.7 / 448.3 | 235.2 / 608.6 |

## Useful output and ideal typing savings

Deadline success counts correct **final** output within 500 ms over every word checkpoint. Ideal typing savings assume an oracle accepts only correct next words, one Tab replaces each word, and waiting is free. Spaces/punctuation and the supplied first word are excluded. This is an optimistic, untimed word-character model—not observed acceptance or productivity.

| Model | Correct final by 500 ms, none / screen | Ideal word keystroke reduction, none / screen |
|---|---:|---:|
| Apple Intelligence | 18.2% / 7.2% | 16.0% / 18.8% |
| Cotabby Nano | 28.1% / 33.1% | 15.7% / 20.1% |
| Cotabby Mini | 30.3% / 38.3% | 17.7% / 23.9% |
| Cotabby Base | 28.2% / 35.9% | 16.8% / 22.5% |
| Cotabby Pro | 28.1% / 35.7% | 17.3% / 23.6% |

## Streaming responsiveness

14 fixed phrases × two contexts × three repetitions × reset/prewarmed cache. Missing outputs remain in deadline-success denominators. p50/p95 are conditional on visible output. A cache reset does not mean a cold OS/model service.

| Model | Context / cache | Visible / trials | First visible p50 / p95 (ms) | Correct by 500 ms | Revisions / withdrawals |
|---|---|---:|---:|---:|---:|
| Apple Intelligence | none-reset | 42/42 | 455.4 / 549.4 | 7.1% | 0 / 0 |
| Apple Intelligence | none-prewarmed | 42/42 | 553.8 / 642.3 | 0.0% | 0 / 0 |
| Apple Intelligence | screen-reset | 42/42 | 521.0 / 617.0 | 0.0% | 0 / 0 |
| Apple Intelligence | screen-prewarmed | 42/42 | 558.3 / 655.4 | 0.0% | 0 / 0 |
| Cotabby Nano | none-reset | 42/42 | 38.8 / 40.9 | 14.3% | 0 / 0 |
| Cotabby Nano | none-prewarmed | 42/42 | 38.6 / 40.5 | 14.3% | 0 / 0 |
| Cotabby Nano | screen-reset | 42/42 | 55.8 / 60.8 | 14.3% | 0 / 0 |
| Cotabby Nano | screen-prewarmed | 42/42 | 55.9 / 60.7 | 14.3% | 0 / 0 |
| Cotabby Mini | none-reset | 42/42 | 72.3 / 83.7 | 21.4% | 0 / 0 |
| Cotabby Mini | none-prewarmed | 42/42 | 72.6 / 83.5 | 21.4% | 0 / 0 |
| Cotabby Mini | screen-reset | 42/42 | 122.1 / 137.0 | 35.7% | 0 / 0 |
| Cotabby Mini | screen-prewarmed | 42/42 | 123.2 / 137.4 | 35.7% | 0 / 0 |
| Cotabby Base | none-reset | 42/42 | 112.6 / 167.6 | 14.3% | 0 / 0 |
| Cotabby Base | none-prewarmed | 42/42 | 108.3 / 162.2 | 14.3% | 0 / 0 |
| Cotabby Base | screen-reset | 42/42 | 185.1 / 220.5 | 35.7% | 0 / 0 |
| Cotabby Base | screen-prewarmed | 42/42 | 176.9 / 215.3 | 28.6% | 0 / 0 |
| Cotabby Pro | none-reset | 42/42 | 201.4 / 291.3 | 14.3% | 0 / 0 |
| Cotabby Pro | none-prewarmed | 42/42 | 71.3 / 108.2 | 14.3% | 0 / 0 |
| Cotabby Pro | screen-reset | 42/42 | 331.1 / 405.9 | 14.3% | 0 / 0 |
| Cotabby Pro | screen-prewarmed | 42/42 | 72.3 / 106.5 | 35.7% | 0 / 0 |

## Output hygiene review flags

Fixed patterns flag visible code/template markers, repeated punctuation or words, and assistant-style prefaces. These can include legitimate text and require review; this is not a human-rated quality score.

| Model | Context | Shown outputs flagged | Template/fence | Repeated punctuation | Repeated word | Assistant preface |
|---|---|---:|---:|---:|---:|---:|
| Apple Intelligence | none | 0.0% | 0 | 0 | 0 | 0 |
| Apple Intelligence | screen | 0.1% | 0 | 0 | 1 | 3 |
| Cotabby Nano | none | 0.0% | 0 | 0 | 0 | 0 |
| Cotabby Nano | screen | 0.0% | 0 | 0 | 0 | 0 |
| Cotabby Mini | none | 0.0% | 0 | 0 | 0 | 0 |
| Cotabby Mini | screen | 0.0% | 0 | 0 | 1 | 0 |
| Cotabby Base | none | 0.0% | 0 | 0 | 0 | 0 |
| Cotabby Base | screen | 0.0% | 0 | 0 | 0 | 0 |
| Cotabby Pro | none | 0.0% | 0 | 0 | 0 | 0 |
| Cotabby Pro | screen | 0.0% | 0 | 0 | 0 | 0 |

## Partial-word diagnostic sample

First two phrases per category, every nonzero character offset. Separate from full-corpus next-word accuracy.

| Model | Checkpoints per condition | No context | With context |
|---|---:|---:|---:|
| Apple Intelligence | 232 | 44.4% | 45.3% |
| Cotabby Nano | 232 | 2.6% | 3.9% |
| Cotabby Mini | 232 | 1.3% | 2.2% |
| Cotabby Base | 232 | 1.3% | 0.9% |
| Cotabby Pro | 232 | 0.0% | 0.0% |

## Startup and process resources

Peak RSS includes the app-hosted test harness. CPU seconds cover the full replay. **Apple service memory/CPU and GPU work are excluded**, so these are not cross-backend efficiency rankings. Apple initialization is availability/engine construction; GGUF preparation includes model load/warmup.

| Model | Preparation (ms) | Host peak RSS (MiB) | Host CPU seconds | Run wall seconds |
|---|---:|---:|---:|---:|
| Apple Intelligence | 0.6 | 121.6 | 171.0 | 7697.6 |
| Cotabby Nano | 343.9 | 875.3 | 225.2 | 1284.0 |
| Cotabby Mini | 439.8 | 1490.7 | 250.7 | 2670.2 |
| Cotabby Base | 759.7 | 3959.1 | 284.6 | 2566.5 |
| Cotabby Pro | 836.3 | 5459.0 | 310.5 | 4166.0 |

## Engine cancellation

Request cancellation at 100 ms, one trial per diagnostic phrase/context. Already completed requests are excluded from drain quantiles. This measures engine cancellation, not stale insertion prevention by the coordinator.

| Model | Interrupted / trials | Already finished | Drain p50 / p95 (ms) | Partial callbacks after cancellation | Interrupted outcomes |
|---|---:|---:|---:|---:|---|
| Apple Intelligence | 28/28 | 0 | 0.2 / 0.3 | 0 | {"cancelled": 28} |
| Cotabby Nano | 14/28 | 14 | 2.0 / 7.0 | 9 | {"cancelled": 14} |
| Cotabby Mini | 28/28 | 0 | 4.7 / 18.9 | 12 | {"cancelled": 28} |
| Cotabby Base | 28/28 | 0 | 14.5 / 84.7 | 10 | {"cancelled": 28} |
| Cotabby Pro | 28/28 | 0 | 104.9 / 210.6 | 0 | {"cancelled": 28} |

## Synthetic editor / production coordinator

Seven prefixes × three repetitions; no screen context, 50 ms configured debounce, 10 ms simulated field publication lag, 2-second observation window. The real coordinator receives input and drives presentation and up to three rapid acceptance commands; OS focus/overlay/insertion are test doubles. Acceptances exercise insertion mechanics, not human preference or reference-text agreement.

| Model | Visible / trials | Input-to-presentation p50 / p95 (ms) | Correct by 500 ms | Accepted / attempts | Insertion mismatches | Blocked-field presentation / acceptance / insertion |
|---|---:|---:|---:|---:|---:|---:|
| Apple Intelligence | 21/21 | 737.1 / 818.6 | 0.0% | 63/63 | 0 | 0 / 0 / 0 |
| Cotabby Nano | 21/21 | 115.4 / 121.9 | 28.6% | 63/63 | 0 | 0 / 0 / 0 |
| Cotabby Mini | 21/21 | 131.9 / 145.4 | 28.6% | 63/63 | 0 | 0 / 0 / 0 |
| Cotabby Base | 21/21 | 150.3 / 170.9 | 14.3% | 63/63 | 0 | 0 / 0 / 0 |
| Cotabby Pro | 21/21 | 192.1 / 214.4 | 14.3% | 63/63 | 0 | 0 / 0 / 0 |

## Category detail

| Model | Category | No context | With context |
|---|---|---:|---:|
| Apple Intelligence | conversation | 22.3% | 22.4% |
| Apple Intelligence | science | 35.5% | 32.3% |
| Apple Intelligence | entertainment | 22.0% | 23.9% |
| Apple Intelligence | work | 23.8% | 23.8% |
| Apple Intelligence | technology | 15.8% | 20.9% |
| Apple Intelligence | everyday | 26.7% | 27.7% |
| Apple Intelligence | travel | 21.4% | 24.4% |
| Cotabby Nano | conversation | 27.3% | 36.2% |
| Cotabby Nano | science | 41.9% | 44.7% |
| Cotabby Nano | entertainment | 22.3% | 29.7% |
| Cotabby Nano | work | 28.1% | 33.3% |
| Cotabby Nano | technology | 25.5% | 28.1% |
| Cotabby Nano | everyday | 24.9% | 29.8% |
| Cotabby Nano | travel | 26.9% | 30.6% |
| Cotabby Mini | conversation | 30.4% | 42.2% |
| Cotabby Mini | science | 45.0% | 47.3% |
| Cotabby Mini | entertainment | 26.0% | 36.2% |
| Cotabby Mini | work | 30.1% | 35.9% |
| Cotabby Mini | technology | 26.1% | 31.4% |
| Cotabby Mini | everyday | 27.2% | 40.3% |
| Cotabby Mini | travel | 27.7% | 36.3% |
| Cotabby Base | conversation | 29.3% | 40.9% |
| Cotabby Base | science | 41.0% | 41.7% |
| Cotabby Base | entertainment | 24.8% | 34.8% |
| Cotabby Base | work | 25.3% | 35.0% |
| Cotabby Base | technology | 23.0% | 27.2% |
| Cotabby Base | everyday | 27.1% | 39.0% |
| Cotabby Base | travel | 27.6% | 34.5% |
| Cotabby Pro | conversation | 29.6% | 40.8% |
| Cotabby Pro | science | 40.9% | 43.8% |
| Cotabby Pro | entertainment | 22.9% | 34.6% |
| Cotabby Pro | work | 28.4% | 34.7% |
| Cotabby Pro | technology | 23.9% | 30.2% |
| Cotabby Pro | everyday | 25.2% | 38.8% |
| Cotabby Pro | travel | 28.0% | 36.9% |

## Unmeasured dimensions

Actual user acceptance and net typing saved; blinded usefulness/naturalness; live keyboard-to-overlay latency; real cross-app insertion and focus-change safety; cancellation during real typing; system energy/battery drain; idle app cost. These require separate experiments and are not inferred from model-only accuracy.

## Provenance

- **Apple Intelligence:** revision `ec466b680625ad6cebdae43a8ae81dc8676e70a0`; model SHA-256 `Apple system model: private asset hash unavailable`; corpus `b41c8089a58ae1e0ee84b95ac9283cf71db4e713e25bd8fed47220be69d8b0f6`; evidence `/Users/jmcasler/Documents/GitHub/mchamster/cotabby/build/eval/scorecards/2026-09-26/full-v1/upstream-apple`.
- **Cotabby Nano:** revision `ec466b680625ad6cebdae43a8ae81dc8676e70a0`; model SHA-256 `febd85051361ccb34d0925744c819f9ae0724117e8f946a2852dd0edfa90a5a1`; corpus `b41c8089a58ae1e0ee84b95ac9283cf71db4e713e25bd8fed47220be69d8b0f6`; evidence `/Users/jmcasler/Documents/GitHub/mchamster/cotabby/build/eval/scorecards/2026-09-26/full-v1/upstream-nano`.
- **Cotabby Mini:** revision `ec466b680625ad6cebdae43a8ae81dc8676e70a0`; model SHA-256 `e3daa3f6e5ed8de264fc6e4128713ae1eb0c2649ad69b83f97bfc6a6ddca3da8`; corpus `b41c8089a58ae1e0ee84b95ac9283cf71db4e713e25bd8fed47220be69d8b0f6`; evidence `/Users/jmcasler/Documents/GitHub/mchamster/cotabby/build/eval/scorecards/2026-09-26/full-v1/upstream-mini`.
- **Cotabby Base:** revision `ec466b680625ad6cebdae43a8ae81dc8676e70a0`; model SHA-256 `20f49b221691c71d955e1d5a840b6e26329db4a5e1626f702fa4226e80a9c629`; corpus `b41c8089a58ae1e0ee84b95ac9283cf71db4e713e25bd8fed47220be69d8b0f6`; evidence `/Users/jmcasler/Documents/GitHub/mchamster/cotabby/build/eval/scorecards/2026-09-26/full-v1/upstream-base`.
- **Cotabby Pro:** revision `ec466b680625ad6cebdae43a8ae81dc8676e70a0`; model SHA-256 `687f4cce47eac6ccfc595fd9517215fb964e5e5be17d4774b25b8add401d6d3c`; corpus `b41c8089a58ae1e0ee84b95ac9283cf71db4e713e25bd8fed47220be69d8b0f6`; evidence `/Users/jmcasler/Documents/GitHub/mchamster/cotabby/build/eval/scorecards/2026-09-26/full-v1/upstream-pro`.

Hardware: {"hw.model": "MacBookPro18,4", "hw.memsize": "34359738368", "hw.ncpu": "10", "machdep.cpu.brand_string": "Apple M1 Max"}.

OS: ProductName:		macOS; ProductVersion:		27.0; BuildVersion:		26A428.

Power at launch: Now drawing from 'AC Power';  -InternalBattery-0 (id=24903779)	80%; AC attached; not charging present: true.
