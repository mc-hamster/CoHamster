# September 26, 2026 scorecards

- [Current upstream Cotabby](upstream.md)
- [Our fork](fork.md)
- [Upstream versus fork](comparison.md)
- [Repeatable methodology](../../../BENCHMARK_METHODOLOGY.md)

All ten model/revision runs completed successfully between September 26 and 27, 2026.
The cards contain 148,740 next-word predictions: 1,337 scenarios and 7,437 predictions per
context condition, for each of five models on each revision. There were zero inference errors.
Smoke tests and the interrupted instrumentation preflight are excluded.

The fork improves measured next-word accuracy for every model and context condition. Its
GGUF gains range from 2.90 to 7.40 percentage points, with higher p95 final-response latency
in every GGUF condition. Apple's no-context gain is small and its paired uncertainty interval
crosses zero. This is a known development corpus, and Apple generation is stochastic.

Within the fork, Nano has the lowest measured latency, Mini has the highest no-context
accuracy (34.6%), and Pro has the highest context-enabled accuracy (43.9%). Base is close
to Pro with context (43.4%) at substantially lower median latency (179 versus 282 ms).
These rankings describe this corpus and this Mac; the cards also show streaming and category
results so model selection need not rely on a single aggregate score.

The report JSON files preserve compact metrics and provenance. Detailed synthetic prompts,
completions, journals, test logs, and adapter source stay under
`build/eval/scorecards/2026-09-26/full-v1/`. Preserve that directory when archiving the experiment;
it is ignored by Git and contains the evidence needed for raw-output audits and rerendering.
Model weights are neither copied into the reports nor included in Git.

The comparison uses Apple Intelligence and the same Nano, Mini, Base, and Pro GGUF files on
both revisions. Upstream: `ec466b680625ad6cebdae43a8ae81dc8676e70a0`.
Fork: `f31abbd59970a86fc5184d1b6b7525a4d7854c16`.

Future runs can generate just one five-model card; comparison is optional. See the methodology
for build, campaign, rendering, evidence preservation, and DerivedData cleanup commands.

Validation checked all completion markers, summary and journal hashes, 1,337 unique phrases
in each condition, common harness/corpus/hardware/OS identity, and matching model bytes across
revisions. Each of the ten app-hosted test runs passed its benchmark and 15 scorer tests.
The diagnostic suite additionally contains 4,640 partial-word checkpoints, 1,680 streaming
trials, 280 cancellation trials, and 210 synthetic editor trials. All 630 attempted synthetic
acceptances succeeded with zero insertion mismatches or blocked-field insertions. These
exercise the real coordinator with fake OS boundaries; they do not establish live cross-app
reliability, user acceptance, or energy efficiency.

The primary checkout's preflight DerivedData and both isolated checkouts' DerivedData were
removed after validation, and their absence was verified. Benchmark evidence and dependency
sources were retained. Rebuild before starting a future campaign.
