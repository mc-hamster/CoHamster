#!/usr/bin/env python3
"""Render standalone scorecards and an optional paired comparison from frozen run evidence."""
import argparse
import json
from pathlib import Path
import random

from benchmark_scorecard import MODELS, percentile, sha

NAMES = {'apple': 'Apple Intelligence', **{k: 'Cotabby ' + k.title() for k in MODELS if k != 'apple'}}


def number(value, digits=1):
    return '—' if value is None else f'{value:.{digits}f}'


def pct(value):
    return '—' if value is None else f'{100 * value:.1f}%'


def load_run(path):
    manifest = json.loads((path / 'manifest.json').read_text())
    if manifest['status'] != 'complete' or manifest['smoke']:
        raise ValueError(f'Not a completed full run: {path}')
    if manifest.get('summarySHA256') != sha(path / 'summary.json'):
        raise ValueError('Summary fingerprint changed or missing')
    summary = json.loads((path / 'summary.json').read_text())
    if summary['smoke'] or summary['model'] != manifest['model']:
        raise ValueError('Mismatched summary identity')
    return manifest, summary


def standalone(label, runs, output):
    completed = {model: load_run(path) for model, path in runs.items()}
    missing = [NAMES[m] for m in MODELS if m not in completed]
    lines = [f'# {label} benchmark report card', '',
        '**Status: ' + ('in progress. Missing: ' + ', '.join(missing) if missing else 'complete for the measured scope') + '.**', '',
        'Release, one inference worker, 4–7 requested words. Each completed model: 1,337 English scenarios, '
        '7,437 word predictions per context condition. Exact intended-word match; plausible alternatives are misses.', '',
        'Methodology: [BENCHMARK_METHODOLOGY.md](../../../BENCHMARK_METHODOLOGY.md). '
        'These are engine/request/display-rule measurements on a known development corpus.', '',
        '## Prediction accuracy', '',
        '| Model | No context | With context | Context lift (pp) | Coverage none / screen | Precision none / screen | Errors none / screen |',
        '|---|---:|---:|---:|---:|---:|---:|']
    for model in MODELS:
        if model not in completed:
            lines.append(f'| {NAMES[model]} | pending | pending | — | — | — | — |')
            continue
        _, s = completed[model]
        a, b = (s['conditions'][c] for c in ['none', 'screen'])
        lines.append(f"| {NAMES[model]} | {pct(a['accuracy'])} | {pct(b['accuracy'])} | {s['contextLiftPP']:+.2f} | "
                     f"{pct(a['coverage'])} / {pct(b['coverage'])} | {pct(a['precision'])} / {pct(b['precision'])} | {a['errors']} / {b['errors']} |")
    lines += ['', '## Final prediction latency', '',
        'Successful generated requests only; suppressions before inference and errors are excluded from latency, '
        'but retained in accuracy. This includes request construction and final display eligibility, '
        'not debounce, Accessibility, OCR capture, or screen presentation.', '',
        '| Model | No context p50 / p95 (ms) | With context p50 / p95 (ms) |', '|---|---:|---:|']
    for model, (_, s) in completed.items():
        a, b = (s['conditions'][c] for c in ['none', 'screen'])
        lines.append(f"| {NAMES[model]} | {number(a['p50ms'])} / {number(a['p95ms'])} | {number(b['p50ms'])} / {number(b['p95ms'])} |")
    lines += ['', '## Useful output and ideal typing savings', '',
        'Deadline success counts correct **final** output within 500 ms over every word checkpoint. '
        'Ideal typing savings assume an oracle accepts only correct next words, one Tab replaces each word, '
        'and waiting is free. Spaces/punctuation and the supplied first word are excluded. '
        'This is an optimistic, untimed word-character model—not observed acceptance or productivity.', '',
        '| Model | Correct final by 500 ms, none / screen | Ideal word keystroke reduction, none / screen |', '|---|---:|---:|']
    for model, (_, s) in completed.items():
        a, b = (s['conditions'][c] for c in ['none', 'screen'])
        lines.append(f"| {NAMES[model]} | {pct(a.get('correctFinalWithin500ms'))} / {pct(b.get('correctFinalWithin500ms'))} | "
            f"{pct(a.get('oracleWordKeystrokeReduction'))} / {pct(b.get('oracleWordKeystrokeReduction'))} |")
    lines += ['', '## Streaming responsiveness', '',
        '14 fixed phrases × two contexts × three repetitions × reset/prewarmed cache. '
        'Missing outputs remain in deadline-success denominators. p50/p95 are conditional on visible output. '
        'A cache reset does not mean a cold OS/model service.', '',
        '| Model | Context / cache | Visible / trials | First visible p50 / p95 (ms) | Correct by 500 ms | Revisions / withdrawals |',
        '|---|---|---:|---:|---:|---:|']
    for model, (_, s) in completed.items():
        for key, t in s['timing'].items():
            lines.append(f"| {NAMES[model]} | {key} | {t['visibleTrials']}/{t['trials']} | "
                f"{number(t['firstVisibleP50ms'])} / {number(t['firstVisibleP95ms'])} | {pct(t['usefulBy500ms'])} | {t['revisions']} / {t['withdrawals']} |")
    lines += ['', '## Output hygiene review flags', '',
        'Fixed patterns flag visible code/template markers, repeated punctuation or words, and assistant-style '
        'prefaces. These can include legitimate text and require review; this is not a human-rated quality score.', '',
        '| Model | Context | Shown outputs flagged | Template/fence | Repeated punctuation | Repeated word | Assistant preface |',
        '|---|---|---:|---:|---:|---:|---:|']
    for model, (_, s) in completed.items():
        for condition, m in s['conditions'].items():
            f = m['hygieneFlags']
            lines.append(f"| {NAMES[model]} | {condition} | {pct(m['hygieneFlaggedOutputRate'])} | "
                f"{f['templateOrFence']} | {f['repeatedPunctuation']} | {f['repeatedWord']} | {f['assistantPreface']} |")
    lines += ['', '## Partial-word diagnostic sample', '',
        'First two phrases per category, every nonzero character offset. Separate from full-corpus next-word accuracy.', '',
        '| Model | Checkpoints per condition | No context | With context |', '|---|---:|---:|---:|']
    for model, (_, s) in completed.items():
        a, b = (s['partial'][c] for c in ['none', 'screen'])
        lines.append(f"| {NAMES[model]} | {a['checkpoints']} | {pct(a['accuracy'])} | {pct(b['accuracy'])} |")
    lines += ['', '## Startup and process resources', '',
        'Peak RSS includes the app-hosted test harness. CPU seconds cover the full replay. '
        '**Apple service memory/CPU and GPU work are excluded**, so these are not cross-backend efficiency rankings. '
        'Apple initialization is availability/engine construction; GGUF preparation includes model load/warmup.', '',
        '| Model | Preparation (ms) | Host peak RSS (MiB) | Host CPU seconds | Run wall seconds |', '|---|---:|---:|---:|---:|']
    for model, (_, s) in completed.items():
        r = s['resources']
        lines.append(f"| {NAMES[model]} | {number(float(s['metadata']['loadMilliseconds']))} | "
            f"{number(r['processPeakRSSBytes']/1024**2)} | {number(r['processCPUSeconds'])} | {number(r['wallSeconds'])} |")
    lines += ['', '## Engine cancellation', '',
        'Request cancellation at 100 ms, one trial per diagnostic phrase/context. '
        'Already completed requests are excluded from drain quantiles. This measures engine cancellation, '
        'not stale insertion prevention by the coordinator.', '',
        '| Model | Interrupted / trials | Already finished | Drain p50 / p95 (ms) | Partial callbacks after cancellation | Interrupted outcomes |',
        '|---|---:|---:|---:|---:|---|']
    for model, (_, s) in completed.items():
        c = s['cancellation']
        lines.append(f"| {NAMES[model]} | {c['interrupted']}/{c['trials']} | {c['completedBeforeCancel']} | "
            f"{number(c['drainP50ms'])} / {number(c['drainP95ms'])} | {c['latePartials']} | {json.dumps(c['outcomes'])} |")
    lines += ['', '## Synthetic editor / production coordinator', '',
        'Seven prefixes × three repetitions; no screen context, 50 ms configured debounce, 10 ms simulated '
        'field publication lag, 2-second observation window. The real coordinator receives input and drives '
        'presentation and up to three rapid acceptance commands; OS focus/overlay/insertion are test doubles. '
        'Acceptances exercise insertion mechanics, not human preference or reference-text agreement.', '',
        '| Model | Visible / trials | Input-to-presentation p50 / p95 (ms) | Correct by 500 ms | Accepted / attempts | Insertion mismatches | Blocked-field presentation / acceptance / insertion |',
        '|---|---:|---:|---:|---:|---:|---:|']
    for model, (_, s) in completed.items():
        i = s['interactions']
        lines.append(f"| {NAMES[model]} | {i['visibleTrials']}/{i['trials']} | "
            f"{number(i['firstVisibleP50ms'])} / {number(i['firstVisibleP95ms'])} | {pct(i['correctBy500ms'])} | "
            f"{i['accepted']}/{i['acceptanceAttempts']} | {i['insertionMismatches']} | "
            f"{i['presentationsAfterBlockedFocus']} / {i['acceptedInBlockedField']} / {i['insertedInBlockedField']} |")
    lines += ['', '## Category detail', '', '| Model | Category | No context | With context |', '|---|---|---:|---:|']
    for model, (_, s) in completed.items():
        for category, a in s['conditions']['none']['categories'].items():
            b = s['conditions']['screen']['categories'][category]
            lines.append(f"| {NAMES[model]} | {category} | {pct(a['accuracy'])} | {pct(b['accuracy'])} |")
    lines += ['', '## Unmeasured dimensions', '',
        'Actual user acceptance and net typing saved; blinded usefulness/naturalness; live keyboard-to-overlay latency; '
        'real cross-app insertion and focus-change safety; cancellation during real typing; system energy/battery drain; idle app cost. '
        'These require separate experiments and are not inferred from model-only accuracy.', '', '## Provenance', '']
    for model, (manifest, _) in completed.items():
        lines += [f"- **{NAMES[model]}:** revision `{manifest['build']['revision']}`; model SHA-256 "
            f"`{manifest['modelSHA256'] or 'Apple system model: private asset hash unavailable'}`; "
            f"corpus `{manifest['corpusSHA256']}`; evidence `{runs[model]}`."]
    if completed:
        m = next(iter(completed.values()))[0]
        lines += ['', 'Hardware: ' + json.dumps(m['hardware']) + '.', '', 'OS: ' + m['os'].replace('\n', '; ') + '.', '',
                  'Power at launch: ' + m['power'].replace('\n', '; ') + '.']
    output.write_text('\n'.join(lines) + '\n')
    output.with_suffix('.json').write_text(json.dumps({model: {'manifest': m, 'summary': s}
        for model, (m, s) in completed.items()}, indent=2) + '\n')


def paired_rows(path):
    manifest = json.loads((path / 'manifest.json').read_text())
    if manifest.get('journalSHA256') != sha(path / 'observations.jsonl'):
        raise ValueError('Raw journal fingerprint changed or missing')
    rows = {}
    for line in (path / 'observations.jsonl').open():
        r = json.loads(line)
        if r['stage'] != 'accuracy':
            continue
        p = r['result']
        for o in p['observations']:
            key = (p['phrase']['id'], p['condition'], o['checkpoint']['wordIndex'], o['checkpoint']['typedCharacters'])
            if key in rows:
                raise ValueError('Duplicate checkpoint')
            rows[key] = (p['phrase']['category'], o)
    return rows


def paired_delta(before, after, condition, repetitions=2000):
    if before.keys() != after.keys():
        raise ValueError('Checkpoint selections differ')
    phrases = {}
    for key, (category, old) in before.items():
        if key[1] != condition:
            continue
        new = after[key][1]
        if old['checkpoint'] != new['checkpoint']:
            raise ValueError('Checkpoint reference/prefix changed')
        item = phrases.setdefault(key[0], [category, 0, 0])
        item[1] += int(new['correct']) - int(old['correct'])
        item[2] += 1
    strata = {}
    for category, difference, n in phrases.values():
        strata.setdefault(category, []).append((difference, n))
    rng = random.Random(1337)
    samples = []
    for _ in range(repetitions):
        total, n = 0, 0
        for rows in strata.values():
            for difference, size in rng.choices(rows, k=len(rows)):
                total += difference
                n += size
        samples.append(100 * total / n)
    return {'deltaPP': 100 * sum(p[1] for p in phrases.values()) / sum(p[2] for p in phrases.values()),
            'lowPP': percentile(samples, .025), 'highPP': percentile(samples, .975)}


def comparison(before_runs, after_runs, output):
    lines = ['# Upstream versus fork benchmark comparison', '',
        'Deltas are **fork minus upstream**. Positive accuracy is better; negative latency is faster. '
        'Same installed GGUF bytes and corpus; each version retains its own production prompt/runtime/display behavior.', '',
        '95% intervals use 2,000 paired, category-stratified phrase bootstrap resamples (seed 1337). '
        'They describe corpus sampling uncertainty conditional on these runs; they do not capture Apple stochasticity '
        'or all machine/thermal timing variation. This known development corpus is not held out.', '',
        '| Model | Context | Upstream accuracy | Fork accuracy | Difference (pp) | 95% interval (pp) | Final p95 delta (ms) | Coverage delta (pp) |',
        '|---|---|---:|---:|---:|---:|---:|---:|']
    results = {}
    for model in MODELS:
        if model not in before_runs or model not in after_runs:
            lines.append(f'| {NAMES[model]} | both | pending | pending | — | — | — | — |')
            continue
        bm, b = load_run(before_runs[model])
        am, a = load_run(after_runs[model])
        for field in ['corpusSHA256', 'modelSHA256', 'hardware', 'os', 'harnessSHA256']:
            if bm[field] != am[field]:
                raise ValueError(f'Cannot compare {model}: different {field}')
        old, new = paired_rows(before_runs[model]), paired_rows(after_runs[model])
        results[model] = {}
        for condition in ['none', 'screen']:
            interval = paired_delta(old, new, condition)
            results[model][condition] = interval
            x, y = b['conditions'][condition], a['conditions'][condition]
            latency = y['p95ms'] - x['p95ms'] if y['p95ms'] is not None and x['p95ms'] is not None else None
            lines.append(f"| {NAMES[model]} | {condition} | {pct(x['accuracy'])} | {pct(y['accuracy'])} | "
                f"{interval['deltaPP']:+.2f} | [{interval['lowPP']:+.2f}, {interval['highPP']:+.2f}] | "
                f"{number(latency)} | {100*(y['coverage']-x['coverage']):+.2f} |")
    lines += ['', '## Partial words and ideal typing savings', '',
        'Partial-word results use the 14-phrase diagnostic sample. Ideal typing savings use full-corpus '
        'word predictions with perfect acceptance choices and free waiting; they are not observed productivity.', '',
        '| Model | Context | Partial accuracy upstream → fork | Ideal word keystroke reduction upstream → fork |',
        '|---|---|---:|---:|']
    for model in MODELS:
        if model not in before_runs or model not in after_runs:
            continue
        _, b = load_run(before_runs[model]); _, a = load_run(after_runs[model])
        for condition in ['none', 'screen']:
            lines.append(f"| {NAMES[model]} | {condition} | {pct(b['partial'][condition]['accuracy'])} → {pct(a['partial'][condition]['accuracy'])} | "
                f"{pct(b['conditions'][condition].get('oracleWordKeystrokeReduction'))} → {pct(a['conditions'][condition].get('oracleWordKeystrokeReduction'))} |")
    lines += ['', '## Output hygiene flags', '',
        'Percentage of shown outputs matching fixed review patterns. False positives are possible; '
        'these are neither human ratings nor confirmed defect rates.', '',
        '| Model | Context | Upstream | Fork |', '|---|---|---:|---:|']
    for model in MODELS:
        if model not in before_runs or model not in after_runs:
            continue
        _, b = load_run(before_runs[model]); _, a = load_run(after_runs[model])
        for condition in ['none', 'screen']:
            lines.append(f"| {NAMES[model]} | {condition} | {pct(b['conditions'][condition]['hygieneFlaggedOutputRate'])} | {pct(a['conditions'][condition]['hygieneFlaggedOutputRate'])} |")
    lines += ['', '## Streaming comparison', '',
        'First-visible medians are conditional on a displayed result. Correct-by-deadline percentages '
        'include missing and wrong predictions in their denominator. Same 14 phrases, three repetitions.', '',
        '| Model | Context / cache | First-visible p50 upstream → fork (ms) | Correct by 500 ms upstream → fork |',
        '|---|---|---:|---:|']
    for model in MODELS:
        if model not in before_runs or model not in after_runs:
            continue
        _, b = load_run(before_runs[model]); _, a = load_run(after_runs[model])
        for key, x in b['timing'].items():
            y = a['timing'][key]
            lines.append(f"| {NAMES[model]} | {key} | {number(x['firstVisibleP50ms'])} → {number(y['firstVisibleP50ms'])} | "
                f"{pct(x['usefulBy500ms'])} → {pct(y['usefulBy500ms'])} |")
    lines += ['', '## Host memory and cancellation', '',
        'Host peak RSS includes the test harness and excludes Apple model services. Cancellation p95 '
        'includes only requests still running at 100 ms; already completed requests are excluded.', '',
        '| Model | Host peak RSS upstream → fork (MiB) | Cancellation drain p95 upstream → fork (ms) |',
        '|---|---:|---:|']
    for model in MODELS:
        if model not in before_runs or model not in after_runs:
            continue
        _, b = load_run(before_runs[model]); _, a = load_run(after_runs[model])
        lines.append(f"| {NAMES[model]} | {number(b['resources']['processPeakRSSBytes']/1024**2)} → {number(a['resources']['processPeakRSSBytes']/1024**2)} | "
            f"{number(b['cancellation']['drainP95ms'])} → {number(a['cancellation']['drainP95ms'])} |")
    lines += ['', '## Synthetic editor interaction', '',
        'Actual coordinator with fake OS boundaries, 21 pauses per model, no screen context. '
        'Timings include configured debounce and simulated field publication; they are not live AX/pixel measurements.', '',
        '| Model | Presentation p50 upstream → fork (ms) | Correct by 500 ms upstream → fork | Insertion mismatches upstream → fork | Blocked-field inserted trials upstream → fork |',
        '|---|---:|---:|---:|---:|']
    for model in MODELS:
        if model not in before_runs or model not in after_runs:
            continue
        _, b = load_run(before_runs[model]); _, a = load_run(after_runs[model])
        x, y = b['interactions'], a['interactions']
        lines.append(f"| {NAMES[model]} | {number(x['firstVisibleP50ms'])} → {number(y['firstVisibleP50ms'])} | "
            f"{pct(x['correctBy500ms'])} → {pct(y['correctBy500ms'])} | {x['insertionMismatches']} → {y['insertionMismatches']} | "
            f"{x['insertedInBlockedField']} → {y['insertedInBlockedField']} |")
    lines += ['', '[Upstream report card](upstream.md) · [Fork report card](fork.md) · '
        '[Methodology](../../../BENCHMARK_METHODOLOGY.md)', '',
        'Full standalone cards retain errors, partial-word diagnostics, streaming deadline success, '
        'process-resource limitations, category detail, and evidence identity. No composite winner is assigned.']
    output.write_text('\n'.join(lines) + '\n')
    output.with_suffix('.json').write_text(json.dumps(results, indent=2) + '\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--spec', type=Path, required=True, help='JSON mapping labels to model/run-directory mappings')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    spec = json.loads(args.spec.read_text())
    args.output.mkdir(parents=True, exist_ok=True)
    runs = {}
    for label, models in spec.items():
        runs[label] = {model: Path(path).resolve() for model, path in models.items()
            if (Path(path) / 'summary.json').is_file() and json.loads((Path(path) / 'manifest.json').read_text())['status'] == 'complete'}
        standalone(label, runs[label], args.output / f'{label}.md')
    if 'upstream' in runs and 'fork' in runs:
        comparison(runs['upstream'], runs['fork'], args.output / 'comparison.md')


if __name__ == '__main__':
    main()
