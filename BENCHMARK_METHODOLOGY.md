# Cotabby benchmark report-card methodology

Version 1, September 26, 2026. This procedure produces **one standalone report card** for a
revision. Comparing two cards is an additional operation; future releases need only one card.
Implementation: `scripts/benchmark_scorecard.py`, `ScorecardReplayTests`, `ScorecardAdapter`,
`ScorecardRuntime`, and the existing `PhrasePredictionScoring` rules.

## Evaluation identity

Record the Git commit, all build input hashes, test/app binary fingerprint, dependency revisions
and patches, model filename/SHA-256/bytes, fixture SHA-256, adapter source, build configuration,
macOS version/build, chip, RAM, power source, and effective generation settings. A model name
alone is insufficient. Apple Intelligence is identified as `SystemLanguageModel.default` plus
the OS build; its private asset version and sampling seed are not exposed by this app's engine.
Never substitute llama when evaluating Apple Intelligence. Unavailable means unavailable.

For the initial comparison, upstream is FuJacob/cotabby `ec466b680625ad6cebdae43a8ae81dc8676e70a0`
(remote default branch HEAD checked September 26); fork is
`f31abbd59970a86fc5184d1b6b7525a4d7854c16`. Additional changes are evaluation code only. Upstream
retains its own app/runtime behavior and dependency selection; the fork retains its pinned,
patched CotabbyInference workspace. Record both native revisions: runtime differences are part
of the product comparison, not evidence of a model-only improvement.
Both full runs use isolated checkouts. The primary working directory holds the harness and
reports; ordinary app development there does not change the compiled comparison sources.

| Report label | Actual model file/backend |
|---|---|
| Apple Intelligence | Apple Foundation Models through the evaluated revision's engine |
| Cotabby Nano | Qwen3.5-0.8B-Base.i1-Q6_K.gguf |
| Cotabby Mini | Qwen3.5-2B-Base.i1-Q4_K_M.gguf |
| Cotabby Base | gemma-4-E2B.i1-Q6_K.gguf |
| Cotabby Pro | gemma-4-E4B.i1-Q4_K_M.gguf |

Upstream calls these four GGUFs `tabby-2-*`. Labels are unified in the cards; file hashes must
still match between versions. Results describe this machine and corpus, not all Macs or users.

## Common controls

- Release build, testability enabled, one engine and one inference worker at a time.
- Same Mac, OS, model bytes, 4–7 word requested completion length, single-line output, and seed
  42 for llama. Product sampling defaults remain intact and are recorded. Seed control does not
  promise bit-identical GPU output. Apple runs are stochastic.
- Fixed app/window/field metadata. No clipboard, user profile, custom rules, or personal text.
- Typo suppression and correction offers enabled. A correction offer is not an appended next
  word and counts as no prediction in this model-only benchmark. Local fallback word completion
  and coordinator tail reuse are outside this replay.
- Confidence/argmax developer overrides reset to each revision's product defaults in the test
  process's volatile argument domain. No persistent user preferences are changed.
- Reset generation context before each phrase/condition; retain it as the reference prefix grows.
  Alternate none/screen condition order by phrase. Use the same phrase/checkpoint order for both
  revisions. Alternate version order between models when collecting a comparison.
- Keep the machine plugged in. Record power state and any known competing workload. Do not
  interpret these uncontrolled desktop measurements as isolated laboratory energy measurements.
- Use `caffeinate -i` around the campaign to prevent idle system sleep. Closing the lid or
  explicitly sleeping the Mac can still interrupt a run; do not treat sleep-distorted timings as
  ordinary interactive latency.
- Smoke runs test seven phrases (one per category), then a full run evaluates all 1,337. Smoke
  results are never silently substituted for a full card. Completed model runs can be retained
  between campaign attempts; interrupted single-model runs are restarted in a new directory.

## Prediction accuracy: the 1337 corpus

Use the exact checked-in `CotabbyTests/Fixtures/phrase-prediction-1337.json`: 1,337 synthetic
English scenarios, 191 in each of seven categories. Word mode supplies the first word and
predicts subsequent words at their boundaries: **7,437 checkpoints per context condition**,
**14,874 per model/revision**, **148,740 for the initial ten combinations**.

Every phrase is run twice. `none` includes the existing draft and surface metadata but no screen
excerpt. `screen` adds that phrase's synthetic OCR transcription. It includes unrelated interface
content and a typed-field echo. Only the already typed prefix reaches inference; future reference
words and correctness labels are retained exclusively by the scorer. Answer facts/individual
words may appear naturally in the screen fixture; the complete target sentence may not.

Each revision applies its own production OCR cleanup/bounding, request construction, prompting,
normalization, and final display guard. Upstream's adapter mirrors `ScreenshotContextGenerator`
cleanup/sanitization; the fork invokes its geometry-aware excerpt selector with fixed rectangles.
The selected engine's context budget applies. Thus context lift includes differences in selection
and prompting, not just the model's reading ability. No screenshot capture or Vision recognition
is performed. Screens are synthetic transcriptions, not real screenshots or private user data.

The next input always advances through the reference text regardless of output. This prevents
an early wrong suggestion from changing later model inputs.

| Metric | Definition |
|---|---|
| Next-word accuracy | Correct complete next words / **all** checkpoints, including suppressions and errors |
| Coverage | Nonempty, display-eligible output / all checkpoints |
| Precision when shown | Correct next words / shown outputs; undefined if nothing is shown |
| Context lift | Screen accuracy minus no-screen accuracy, in percentage points |
| Errors | Inference exceptions; recorded as misses, not removed from accuracy |
| Final latency p50/p95 | Nearest-rank quantiles of successful generated requests, including final display guard and request construction; excludes pre-generation gates and errors |
| Correct final output by 500 ms | Correct final outputs with latency ≤500 ms / all checkpoints; not streaming or keyboard-to-pixel latency |
| Ideal word keystroke reduction | Sum of `word length − 1 Tab` for correct boundary predictions / reference word characters; assumes perfect acceptance decisions and free waiting |

Matching ignores case, terminal punctuation, and curly/straight apostrophe differences.
Internal apostrophes/hyphens and word boundaries remain significant. Plausible synonyms are
misses. This is intended-word prediction, not a semantic quality rating or user acceptance rate.
The ideal typing calculation excludes spaces, punctuation, and the supplied first word. It is an
optimistic word-level accounting model derived from accuracy, not measured user productivity or
the coordinator's actual chunk insertion behavior. Unicode word lengths use Python code points;
the synthetic English corpus should not be used to generalize this estimate to other scripts.

Report each condition and each category separately. This corpus has been used during fork
development: it is a known benchmark, **not a fresh held-out evaluation**. Do not use its scores
alone to claim generalization. Report phrase-paired uncertainty for version deltas, rather than
treating adjacent checkpoints as independent examples.

## Partial words and streaming responsiveness

Diagnostic sample: first two canonical IDs in each category (14 phrases), frozen before outputs
are examined. Partial-word tests score every nonzero character offset in each subsequent word,
with both context conditions. This is a subset, not 1,337-phrase character-mode coverage.

Streaming tests use the first scored word boundary in each of those phrases, both contexts,
three repetitions, and reset versus prewarmed generation context: **168 trials/model/revision**.
The clock starts before request construction. Record first display-eligible text, first correct
complete next word, final output, non-prefix revisions, and final withdrawals. Report missing
visible/correct outputs as missing, not zero milliseconds. Deadline success uses **all trials**
as the denominator. Prewarm time is outside the measured generation interval.

Engine cancellation: one additional trial per sampled phrase/context (28), reset cache, streaming
enabled, request cancellation after 100 ms. Count requests already finished separately; measure
task drain p50/p95 and partial callbacks after cancellation only for interrupted requests. Record
the returned/cancelled/error outcome. This cannot establish coordinator stale-result safety.

These measurements stop at a production display-rule decision. They exclude keyboard delivery,
adaptive debounce, Accessibility polling, coordinator scheduling, overlay layout, animation,
and screen compositor timing. Label them **engine/display-rule latency**, never keystroke-to-pixel
latency. A reset cache is not a cold operating-system file cache or a rebooted Apple model service.

## Startup and resources

Record elapsed manager preparation for GGUF (including its production warmup). For Apple this
only measures engine/availability construction: Apple loads its model lazily in a system service,
so it is not comparable to GGUF model load time. The first accuracy request separately includes
whatever first-use work the engine performs. No claim of cold disk-cache timing is made.
Model hashing happens before launch and may warm the filesystem cache. Do not describe manager
preparation in these runs as cold disk loading.

`getrusage(RUSAGE_SELF)` records peak resident memory for the XCTest host and CPU seconds over
the replay. It includes harness and application overhead. Apple Intelligence's out-of-process
service memory/CPU/GPU work is **excluded**; do not rank Apple versus GGUF efficiency using these
host-only values. CPU time is not energy. Battery drain, system-wide watts/joules, idle app cost,
and isolated GPU utilization need a separate measurement setup and must remain unmeasured here.
RSS also is not a total unified-memory/GPU-allocation measurement for the GGUF backend.

## Synthetic editor interaction

`ScorecardInteractionReplay` drives each revision's actual coordinator with the real selected
engine and shared fake focus, permission, overlay, and insertion boundaries. Seven fixed first
phrases (one per category), three repetitions: **21 trials**. No screen context in this layer.
The last prefix character is delivered as input; the field snapshot is published 10 ms later.
Configured debounce is 50 ms, streaming is enabled, and presentation is observed for two seconds.
Record first presented output and first intended next word, with missing outputs retained in the
deadline denominator. This includes coordinator behavior but not live AX or compositor timing.

After the observation window, accept up to three offered word chunks at 120 ms spacing. Compare
the recorded insertion against that revision's predicted insertion chunk, publish each synthetic
edit after 10 ms, and reconcile the tail. These accepts check mechanics, not semantic usefulness
or human acceptance. Then schedule new work and switch after 75 ms to a blocked secure-field
snapshot. Observe 500 ms and attempt acceptance: count any presentation, acceptance, or insertion
after the blocked transition. Trials with no offered suggestion are not successful insertion tests;
the card shows the number of attempts. This small deterministic scenario cannot establish real
cross-app insertion or security guarantees.

## Other scorecard dimensions

Retain raw/generated and shown output, suppression reasons, prompts, and selected context for
auditing malformed output. Fixed output-hygiene regexes in `benchmark_scorecard.metrics` count
visible code fences/control tokens, four repeated punctuation characters, three adjacent repeated
words, and a narrow set of assistant-style prefaces. Report counts and the union of flagged outputs
divided by shown outputs. Flags may overlap and legitimate writing can match them: these are
review cues, not confirmed failures or semantic judgments. Rules are frozen before the full runs.
A blinded naturalness/usefulness review requires human ratings and
is not inferred from exact-match scores. Likewise, actual acceptance rate, net user keystrokes
saved, real cross-app insertion correctness, and live focus-change safety require
a live typing experiment. Explicitly mark those unmeasured in these cards;
do not invent rates from the 1337 prefix replay. Automated tests or old runs from other revisions
do not count as new live scorecard measurements.

## Reproduction

Prepare the evaluated revision's documented dependencies. For this fork:

```sh
scripts/prepare_cotabby_workspace.sh
python3 scripts/benchmark_scorecard.py build \
  --workspace build/cotabby-dependencies/Cotabby.xcworkspace
python3 scripts/benchmark_scorecard.py run --label fork --model nano \
  --models-dir '/absolute/path/to/LlamaRuntime' \
  --output build/eval/scorecards/new-run/fork-nano
```

Run the same command for `apple`, `mini`, `base`, and `pro`, using distinct output directories.
Add `--smoke` for validation only. For upstream, use an isolated checkout and add `--checkout`
to both commands and `--upstream` to build. The tool transplants only the portable tests/scorer
and identical corpus, regenerates the Xcode project, and retains adapter sources in each run.
It does not change upstream production Swift files. Build output is always checkout-local
`build/DerivedData`; never build concurrently in the same checkout.

For one full five-model card, run:

```sh
caffeinate -i python3 scripts/benchmark_scorecard.py campaign \
  --models-dir '/absolute/path/to/LlamaRuntime' \
  --output build/eval/scorecards/new-run \
  --reports benchmarks/scorecards/new-run
```

Add `--upstream-checkout /absolute/path/to/prepared/upstream` for the initial ten-run comparison.
The campaign alternates version order between models and writes `fork.md`, `upstream.md`, and
`comparison.md` after each completed model. For a standalone future run it writes only `fork.md`.
Regenerate cards without inference using `python3 scripts/benchmark_report.py --spec
build/eval/scorecards/new-run/report-spec.json --output benchmarks/scorecards/new-run`.

The runner rejects changed source/binaries and missing models. It stages an ad-hoc-signed test
host under `/private/tmp`, preserves an append-only journal, and requires both successful XCTest
execution and a completion marker. A completed report may contain model inference failures;
those are measured failures, retained in the denominator. A launch/build failure produces no
valid card. Capture the entire run directory for audit; compact summaries can be committed.

After all runs and checks finish, remove each used checkout's `build/DerivedData` and verify its
absence. Keep journals, manifests, summaries, and methodology. Do not overwrite historical cards.
