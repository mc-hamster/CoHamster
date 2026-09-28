#!/usr/bin/env python3
"""Build and run a standalone local scorecard; combine two completed cards separately.

The campaign owns process lifetime, provenance, and report presentation. Swift owns all
prediction scoring. Build/signing helpers are shared with phrase_eval, not reimplemented.
"""
import argparse
import datetime
import hashlib
import json
import math
import pathlib
import plistlib
import re
import shutil
import subprocess
import sys
import time
import uuid
import xml.etree.ElementTree as ET

import phrase_eval as replay

ROOT = pathlib.Path(__file__).resolve().parents[1]
MODELS = {
    'apple': None,
    'nano': 'Qwen3.5-0.8B-Base.i1-Q6_K.gguf',
    'mini': 'Qwen3.5-2B-Base.i1-Q4_K_M.gguf',
    'base': 'gemma-4-E2B.i1-Q6_K.gguf',
    'pro': 'gemma-4-E4B.i1-Q4_K_M.gguf',
}
PORTABLE = ['ScorecardReplayTests.swift', 'ScorecardAdapter.swift', 'ScorecardRuntime.swift', 'ScorecardInteractionReplay.swift',
            'PhrasePredictionScoring.swift', 'PhrasePredictionScoringTests.swift']


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def command(*args, cwd=None):
    return subprocess.check_output(list(map(str, args)), cwd=cwd, text=True).strip()


def save(path, value):
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(json.dumps(value, indent=2) + '\n')
    temporary.replace(path)


def install_adapter(root):
    """Copy test files only. Never copy fork production sources into the upstream control."""
    if root == ROOT:
        return
    for name in PORTABLE:
        shutil.copy2(ROOT / 'CotabbyTests/Evals' / name, root / 'CotabbyTests/Evals' / name)
    shutil.copy2(ROOT / 'CotabbyTests/Fixtures/phrase-prediction-1337.json', root / 'CotabbyTests/Fixtures/phrase-prediction-1337.json')


def build(args):
    root = args.checkout.resolve()
    install_adapter(root)
    replay.ROOT, replay.DERIVED = root, root / 'build/DerivedData'
    output = root / 'build/scorecard-build'
    output.mkdir(parents=True, exist_ok=True)
    subprocess.run(['xcodegen', 'generate'], cwd=root, check=True)
    project = ['-workspace', args.workspace.resolve()] if args.workspace else ['-project', root / 'Cotabby.xcodeproj']
    replay.prepare_build_inputs(args.workspace, project, output, skip_build=False)
    flags = '$(inherited) RUN_LLAMA_EVAL' + (' SCORECARD_UPSTREAM' if args.upstream else '')
    replay.logged_command(['xcodebuild', 'build-for-testing', *project, '-scheme', 'Cotabby',
        '-configuration', 'Release', '-destination', 'platform=macOS', '-derivedDataPath', replay.DERIVED,
        'CODE_SIGNING_ALLOWED=NO', 'ENABLE_TESTABILITY=YES', 'ONLY_ACTIVE_ARCH=YES',
        'SWIFT_ACTIVE_COMPILATION_CONDITIONS=' + flags, '-skipPackageUpdates'], output / 'build.log')
    source = next((replay.DERIVED / 'Build/Products').glob('Cotabby_*.xctestrun'))
    save(output / 'build.json', {'source': replay.build_input_snapshot(args.workspace),
        'productSHA256': replay.build_product_fingerprint(source), 'xctestrun': str(source),
        'upstreamAdapter': args.upstream, 'workspace': str(args.workspace.resolve()) if args.workspace else None,
        'revision': command('git', 'rev-parse', 'HEAD', cwd=root)})


def run(args):
    root, output = args.checkout.resolve(), args.output.resolve()
    replay.ROOT, replay.DERIVED = root, root / 'build/DerivedData'
    build_record = json.loads((root / 'build/scorecard-build/build.json').read_text())
    workspace = pathlib.Path(build_record['workspace']) if build_record['workspace'] else None
    if replay.build_input_fingerprint(workspace) != build_record['source']['sourceSHA256']:
        raise ValueError('Source changed since scorecard build; rebuild first')
    source = pathlib.Path(build_record['xctestrun'])
    if replay.build_product_fingerprint(source) != build_record['productSHA256']:
        raise ValueError('Build products changed; rebuild first')
    model_path = args.models_dir / MODELS[args.model] if MODELS[args.model] else None
    if model_path and not model_path.is_file():
        raise ValueError(f'Missing model: {model_path}')
    output.mkdir(parents=True, exist_ok=False)
    manifest = {'schemaVersion': 1, 'startedUTC': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'label': args.label, 'model': args.model, 'smoke': args.smoke, 'build': build_record,
        'modelSHA256': sha(model_path) if model_path else None,
        'modelBytes': model_path.stat().st_size if model_path else None,
        'corpusSHA256': sha(root / 'CotabbyTests/Fixtures/phrase-prediction-1337.json'),
        'hardware': {k: command('sysctl', '-n', k) for k in ['hw.model', 'hw.memsize', 'hw.ncpu', 'machdep.cpu.brand_string']},
        'os': command('sw_vers'), 'power': command('pmset', '-g', 'batt'),
        'dependencyLocks': {str(path): json.loads(path.read_text()) for path in [
            root / 'Cotabby.xcodeproj/project.xcworkspace/xcshareddata/swiftpm/Package.resolved',
            *([workspace / 'xcshareddata/swiftpm/Package.resolved'] if workspace else [])] if path.is_file()},
        'status': 'running', 'checkout': str(root)}
    harness_files = [pathlib.Path(__file__), ROOT / 'scripts/benchmark_report.py', ROOT / 'scripts/phrase_eval.py',
                     ROOT / 'BENCHMARK_METHODOLOGY.md']
    manifest['harnessSHA256'] = {p.name: sha(p) for p in harness_files}
    manifest['localNativeDependencies'] = []
    if workspace:
        for ref in ET.parse(workspace / 'contents.xcworkspacedata').iter('FileRef'):
            location = ref.attrib.get('location', '')
            dependency = pathlib.Path(location.removeprefix('absolute:'))
            if location.startswith('absolute:') and (dependency / 'Package.swift').is_file():
                manifest['localNativeDependencies'].append({'path': str(dependency),
                    'revision': command('git', 'rev-parse', 'HEAD', cwd=dependency),
                    'status': command('git', 'status', '--short', cwd=dependency),
                    'diffSHA256': hashlib.sha256(command('git', 'diff', 'HEAD', cwd=dependency).encode()).hexdigest()})
    save(output / 'manifest.json', manifest)
    (output / 'adapter.patch').write_text(command('git', 'diff', 'HEAD', cwd=root) + '\n')
    # Include untracked adapter source, which git diff cannot capture.
    adapter = output / 'adapter-source'
    adapter.mkdir()
    for name in PORTABLE:
        shutil.copy2(root / 'CotabbyTests/Evals' / name, adapter / name)
    for path in harness_files:
        shutil.copy2(path, adapter / path.name)
    if workspace and (workspace.parent / 'native.patch').is_file():
        shutil.copy2(workspace.parent / 'native.patch', adapter / 'native.patch')
    try:
        products = source.parent
        with replay.sign_test_hosts(products, output) as host:
            configuration = plistlib.loads(source.read_bytes())
            assert replay.retarget_test_host(configuration, host) == 1
            staged_output = host.parent / 'results'
            staged_output.mkdir()
            environment = {'COTABBY_SCORECARD': '1', 'COTABBY_SCORECARD_MODEL': args.model,
                'COTABBY_SCORECARD_OUTPUT': str(staged_output), 'COTABBY_SCORECARD_SMOKE': str(int(args.smoke)),
                'COTABBY_PHRASE_WORD_COUNT': '4-7'}
            if model_path:
                environment['COTABBY_EVAL_MODEL_PATH'] = str(model_path.resolve())
            assert replay.inject_environment(configuration, environment) == 1
            prepared = products / f'Cotabby_scorecard-{uuid.uuid4().hex}.xctestrun'
            prepared.write_bytes(plistlib.dumps(configuration))
            try:
                # Swift journals outside Documents; the local progress reader also copies durable
                # records back so a killed host does not erase hours of completed predictions.
                replay.logged_command(['xcodebuild', 'test-without-building', '-xctestrun', prepared,
                    '-destination', 'platform=macOS', '-derivedDataPath', replay.DERIVED,
                    '-only-testing:CotabbyTests/ScorecardReplayTests/testScorecard',
                    '-only-testing:CotabbyTests/PhrasePredictionScoringTests',
                    '-parallel-testing-enabled', 'NO', '-test-timeouts-enabled', 'NO'],
                    output / 'test.log', Progress(staged_output, output))
            finally:
                prepared.unlink(missing_ok=True)
                shutil.copytree(staged_output, output, dirs_exist_ok=True)
        if not (output / 'complete').exists():
            raise ValueError('Test produced no completion marker; a skipped test is not a benchmark')
        summary = summarize(output)
        if model_path and pathlib.Path(summary['metadata']['model']).resolve() != model_path.resolve():
            raise ValueError('Engine loaded a different model than requested')
        if model_path and sha(model_path) != manifest['modelSHA256']:
            raise ValueError('Model bytes changed during the run')
        if replay.build_input_fingerprint(workspace) != build_record['source']['sourceSHA256']:
            raise ValueError('Source changed during the run')
        if replay.build_product_fingerprint(source) != build_record['productSHA256']:
            raise ValueError('Build products changed during the run')
        save(output / 'summary.json', summary)
        manifest['summarySHA256'] = sha(output / 'summary.json')
        manifest['journalSHA256'] = sha(output / 'observations.jsonl')
        manifest['status'] = 'complete'
    except BaseException as error:
        manifest['status'] = 'failed'
        manifest['error'] = str(error)
        raise
    finally:
        manifest['finishedUTC'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        manifest['powerAtFinish'] = command('pmset', '-g', 'batt')
        save(output / 'manifest.json', manifest)


class Progress:
    """Owned by one run; mirrors append-only evidence and reports progress without rescoring."""
    def __init__(self, source, output):
        self.source, self.output, self.count, self.position = source, output, 0, 0
        self.started = time.monotonic()

    def status(self):
        journal = self.source / 'observations.jsonl'
        if journal.exists():
            with journal.open('rb') as stream:
                stream.seek(self.position)
                data = stream.read()
            if data:
                with (self.output / journal.name).open('ab') as dest:
                    dest.write(data)
                self.position += len(data)
                self.count += data.count(b'\n')
        return f'Scorecard | {self.count} durable records | elapsed {replay.duration(time.monotonic() - self.started)}'


def percentile(values, p):
    values = sorted(values)
    return values[max(0, math.ceil(len(values) * p) - 1)] if values else None


def metrics(observations):
    shown = [o for o in observations if o['wasShown']]
    successful = [o['latencyMilliseconds'] for o in observations if o['latencyMilliseconds'] > 0 and not o.get('error')]
    word_rows = [o for o in observations if o.get('checkpoint', {}).get('typedCharacters') == 0]
    word_characters = sum(len(o['checkpoint']['expectedWord']) for o in word_rows)
    # An explicitly optimistic accounting model: an oracle accepts only correct full words,
    # one Tab replaces that word, spaces/punctuation are typed normally, and waiting is free.
    # It is derived from exact-match observations, not measured human productivity.
    saved = sum(max(0, len(o['checkpoint']['expectedWord']) - 1) for o in word_rows if o['correct'])
    # These are review flags, not semantic judgments. Ordinary prose can legitimately match
    # one of them; use identical fixed patterns on both revisions and retain raw examples.
    patterns = {
        'templateOrFence': r'```|<\|(?:im_start|im_end|endoftext|eot_id|start_header_id)\|>',
        'repeatedPunctuation': r'([^\w\s])\1{3,}',
        'repeatedWord': r'\b(\w+)(?:\s+\1){2,}\b',
        'assistantPreface': r"^\s*(?:sure[,!:.]|certainly[,!:.]|of course[,!:.]|as an ai\b|here(?:'s| is) (?:a|the) (?:continuation|completion|suggestion)\b)",
    }
    flags = [{key for key, pattern in patterns.items() if re.search(pattern, o.get('shown') or '', re.IGNORECASE)} for o in shown]
    return {'checkpoints': len(observations), 'correct': sum(o['correct'] for o in observations),
        'accuracy': sum(o['correct'] for o in observations) / len(observations) if observations else None,
        'coverage': len(shown) / len(observations) if observations else None,
        'precision': sum(o['correct'] for o in shown) / len(shown) if shown else None,
        'errors': sum(bool(o.get('error')) for o in observations),
        'p50ms': percentile(successful, .5), 'p95ms': percentile(successful, .95),
        'correctFinalWithin500ms': sum(o['correct'] and 0 < o['latencyMilliseconds'] <= 500 for o in observations) / len(observations) if observations else None,
        'oracleSavedWordCharacters': saved, 'referenceWordCharacters': word_characters,
        'oracleWordKeystrokeReduction': saved / word_characters if word_characters else None,
        'hygieneFlags': {key: sum(key in f for f in flags) for key in patterns},
        'hygieneFlaggedOutputRate': sum(bool(f) for f in flags) / len(shown) if shown else None}


def summarize(output):
    manifest = json.loads((output / 'manifest.json').read_text())
    rows = [json.loads(line) for line in (output / 'observations.jsonl').read_text().splitlines()]
    accuracy = [r['result'] for r in rows if r['stage'] == 'accuracy']
    corpus = json.loads((ROOT / 'CotabbyTests/Fixtures/phrase-prediction-1337.json').read_text())
    expected = 7 if manifest['smoke'] else 1337
    for condition in ['none', 'screen']:
        selected = [r for r in accuracy if r['condition'] == condition]
        if len(selected) != expected or len({r['phrase']['id'] for r in selected}) != expected:
            raise ValueError('Incomplete or duplicate accuracy journal')
        if not manifest['smoke'] and {r['phrase']['id'] for r in selected} != {p['id'] for p in corpus['phrases']}:
            raise ValueError('Wrong corpus selection')
        expected_checkpoints = sum(len(replay.WORD.findall(r['phrase']['text'])) - 1 for r in selected)
        if sum(len(r['observations']) for r in selected) != expected_checkpoints:
            raise ValueError('Incomplete checkpoint denominator')
        for r in selected:
            keys = [(o['checkpoint']['wordIndex'], o['checkpoint']['typedCharacters']) for o in r['observations']]
            if keys != [(i, 0) for i in range(1, len(replay.WORD.findall(r['phrase']['text'])))]:
                raise ValueError('Wrong or duplicate word checkpoints')
    expected_sample = 7 if manifest['smoke'] else 14
    partial = [r for r in rows if r['stage'] == 'partial']
    timing = [r for r in rows if r['stage'] == 'timing']
    cancellation = [r for r in rows if r['stage'] == 'cancellation']
    if len(partial) != expected_sample * 2 or len(timing) != expected_sample * 4 * (1 if manifest['smoke'] else 3) or len(cancellation) != expected_sample * 2:
        raise ValueError('Incomplete diagnostic stages')
    result = {'model': manifest['model'], 'label': manifest['label'], 'smoke': manifest['smoke'],
        'revision': manifest['build']['revision'], 'conditions': {}, 'partial': {}, 'timing': {}}
    for condition in ['none', 'screen']:
        selected = [r for r in accuracy if r['condition'] == condition]
        result['conditions'][condition] = metrics([o for r in selected for o in r['observations']])
        result['conditions'][condition]['categories'] = {category: metrics([o for r in selected
            if r['phrase']['category'] == category for o in r['observations']]) for category in replay.CATEGORIES}
        result['partial'][condition] = metrics([o for r in rows if r['stage'] == 'partial' and r['result']['condition'] == condition for o in r['result']['observations']])
        for prewarm in [False, True]:
            timing = [r for r in rows if r['stage'] == 'timing' and r['condition'] == condition and r['prewarmed'] == prewarm]
            key = condition + ('-prewarmed' if prewarm else '-reset')
            result['timing'][key] = {'trials': len(timing),
                'visibleTrials': sum(r.get('firstVisibleMilliseconds') is not None for r in timing),
                'correctTrials': sum(r.get('firstCorrectMilliseconds') is not None for r in timing),
                'firstVisibleP50ms': percentile([r['firstVisibleMilliseconds'] for r in timing if r.get('firstVisibleMilliseconds') is not None], .5),
                'firstVisibleP95ms': percentile([r['firstVisibleMilliseconds'] for r in timing if r.get('firstVisibleMilliseconds') is not None], .95),
                'usefulBy500ms': sum(r.get('firstCorrectMilliseconds', float('inf')) <= 500 for r in timing) / len(timing) if timing else None,
                'revisions': sum(r['revisions'] for r in timing), 'withdrawals': sum(r['withdrawn'] for r in timing)}
    result['contextLiftPP'] = 100 * (result['conditions']['screen']['accuracy'] - result['conditions']['none']['accuracy'])
    result['resources'] = json.loads((output / 'resources.json').read_text())
    result['metadata'] = json.loads((output / 'metadata.json').read_text())
    if result['metadata']['corpusSHA256'] != manifest['corpusSHA256']:
        raise ValueError('Executed corpus differs from planned corpus')
    interrupted = [r for r in cancellation if not r['completedBeforeCancel']]
    result['cancellation'] = {'trials': len(cancellation), 'completedBeforeCancel': len(cancellation) - len(interrupted),
        'interrupted': len(interrupted), 'latePartials': sum(r['latePartials'] for r in interrupted),
        'drainP50ms': percentile([r['drainMilliseconds'] for r in interrupted], .5),
        'drainP95ms': percentile([r['drainMilliseconds'] for r in interrupted], .95),
        'outcomes': {outcome: sum(r['outcome'] == outcome for r in interrupted) for outcome in sorted({r['outcome'] for r in interrupted})}}
    interactions = json.loads((output / 'interactions.json').read_text())
    if len(interactions) != (7 if manifest['smoke'] else 21):
        raise ValueError('Incomplete coordinator interaction sample')
    result['interactions'] = {'trials': len(interactions),
        'visibleTrials': sum(r.get('firstVisibleMilliseconds') is not None for r in interactions),
        'firstVisibleP50ms': percentile([r['firstVisibleMilliseconds'] for r in interactions if r.get('firstVisibleMilliseconds') is not None], .5),
        'firstVisibleP95ms': percentile([r['firstVisibleMilliseconds'] for r in interactions if r.get('firstVisibleMilliseconds') is not None], .95),
        'correctBy500ms': sum(r.get('firstCorrectMilliseconds', float('inf')) <= 500 for r in interactions) / len(interactions),
        **{key: sum(r[key] for r in interactions) for key in ['acceptanceAttempts', 'accepted', 'insertedCharacters',
            'insertionMismatches', 'presentationsAfterBlockedFocus', 'acceptedInBlockedField', 'insertedInBlockedField']}}
    return result


def campaign(args):
    """Sequential model campaign; finished runs are immutable and can be resumed at model boundaries."""
    from types import SimpleNamespace
    import benchmark_report
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    checkouts = {'fork': args.checkout.resolve()}
    if args.upstream_checkout:
        checkouts = {'upstream': args.upstream_checkout.resolve(), **checkouts}
    spec = {label: {model: str(output / f'{label}-{model}') for model in MODELS} for label in checkouts}
    save(output / 'report-spec.json', spec)
    report_dir = args.reports.resolve()
    report_dir.mkdir(parents=True, exist_ok=True)

    def render():
        completed = {label: {model: pathlib.Path(path) for model, path in models.items()
            if (pathlib.Path(path) / 'summary.json').is_file()
            and json.loads((pathlib.Path(path) / 'manifest.json').read_text())['status'] == 'complete'}
            for label, models in spec.items()}
        for label, models in completed.items():
            benchmark_report.standalone(label, models, report_dir / f'{label}.md')
        if 'upstream' in completed:
            benchmark_report.comparison(completed['upstream'], completed['fork'], report_dir / 'comparison.md')

    render()
    # Alternate revision order between models. There is never concurrent inference or a build
    # alongside a full run. Apple is last so GGUF campaigns do not inherit a newly loaded service.
    for index, model in enumerate(['nano', 'mini', 'base', 'pro', 'apple']):
        labels = list(checkouts)
        if index % 2:
            labels.reverse()
        for label in labels:
            path = pathlib.Path(spec[label][model])
            if path.exists():
                manifest, _ = benchmark_report.load_run(path)
                if manifest['build']['revision'] != command('git', 'rev-parse', 'HEAD', cwd=checkouts[label]):
                    raise ValueError('Cannot resume a campaign against a different revision')
                current = json.loads((checkouts[label] / 'build/scorecard-build/build.json').read_text())
                if current['productSHA256'] != manifest['build']['productSHA256']:
                    raise ValueError('Cannot resume a campaign with changed benchmark binaries')
                model_path = args.models_dir / MODELS[model] if MODELS[model] else None
                if model_path and sha(model_path) != manifest['modelSHA256']:
                    raise ValueError('Cannot resume a campaign with changed model bytes')
                print(f'Already complete: {label}/{model}', flush=True)
                continue
            print(f'Starting {label}/{model}: {path}', flush=True)
            try:
                run(SimpleNamespace(checkout=checkouts[label], output=path, label=label, model=model,
                    models_dir=args.models_dir, smoke=False))
            finally:
                render()
    print('All requested full-model report cards and comparison completed.', flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    subs = parser.add_subparsers(dest='action', required=True)
    b = subs.add_parser('build')
    b.add_argument('--checkout', type=pathlib.Path, default=ROOT)
    b.add_argument('--workspace', type=pathlib.Path)
    b.add_argument('--upstream', action='store_true')
    r = subs.add_parser('run')
    r.add_argument('--checkout', type=pathlib.Path, default=ROOT)
    r.add_argument('--output', type=pathlib.Path, required=True)
    r.add_argument('--label', required=True)
    r.add_argument('--model', choices=MODELS, required=True)
    r.add_argument('--models-dir', type=pathlib.Path, required=True)
    r.add_argument('--smoke', action='store_true')
    c = subs.add_parser('campaign')
    c.add_argument('--checkout', type=pathlib.Path, default=ROOT)
    c.add_argument('--upstream-checkout', type=pathlib.Path)
    c.add_argument('--models-dir', type=pathlib.Path, required=True)
    c.add_argument('--output', type=pathlib.Path, required=True)
    c.add_argument('--reports', type=pathlib.Path, required=True)
    args = parser.parse_args()
    {'build': build, 'run': run, 'campaign': campaign}[args.action](args)


if __name__ == '__main__':
    main()
