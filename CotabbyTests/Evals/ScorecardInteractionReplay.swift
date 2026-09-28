import Foundation
@testable import Cotabby

#if RUN_LLAMA_EVAL
/// Drives each revision's real coordinator using a small synthetic editor. The outer model
/// replay lends its engine; this runner owns short-lived fixture graphs and stops each one before
/// moving on. Only OS boundaries are fake, so debounce, cancellation, presentation, acceptance,
/// and active-tail reconciliation remain production behavior. No real application receives keys.
@MainActor
enum ScorecardInteractionReplay {
    static func run(engine: any SuggestionGenerating, apple: Bool,
                    phrases: [PhrasePredictionCorpus.Phrase], smoke: Bool) async throws -> [Trial] {
        var trials: [Trial] = []
        for repetition in 0..<(smoke ? 1 : 3) {
            for phrase in phrases {
                await engine.resetCachedGenerationContext()
                let checkpoint = PhrasePredictionScorer.checkpoints(for: phrase, mode: .word)[0]
                let editor = Editor(text: String(checkpoint.prefix.dropLast()), engine: engine, apple: apple)
                defer { editor.stop() }
                var trial = Trial(phraseID: phrase.id, repetition: repetition)
                let start = ContinuousClock.now
                var isBlocked = false
                let originalCallback = editor.overlay.onStateChange
                editor.overlay.onStateChange = { state in
                    originalCallback?(state)
                    guard case let .visible(text, _, _) = state else { return }
                    if isBlocked { trial.presentationsAfterBlockedFocus += 1; return }
                    if trial.firstVisibleMilliseconds == nil {
                        trial.firstVisibleMilliseconds = milliseconds(since: start)
                    }
                    if trial.firstCorrectMilliseconds == nil && PhrasePredictionScorer.isCorrect(shown: text, at: checkpoint) {
                        trial.firstCorrectMilliseconds = milliseconds(since: start)
                    }
                }
                _ = editor.coordinator.handleInputEvent(CotabbyTestFixtures.inputEvent(
                    kind: .textMutation, characters: String(checkpoint.prefix.suffix(1))))
                // Input callbacks precede AX publication in real editors. Model a fixed 10 ms
                // publication lag so neither revision receives a magically synchronous snapshot.
                try await Task.sleep(for: .milliseconds(10))
                editor.publish(checkpoint.prefix)
                try await Task.sleep(for: .milliseconds(1990))
                // Freeze response timing before acceptance: follow-on tails are not new answers
                // to the original keystroke and must not turn a missing answer into a late hit.
                editor.overlay.onStateChange = originalCallback
                var text = checkpoint.prefix
                for _ in 0..<3 {
                    guard let session = editor.state.activeSession,
                          case .visible = editor.overlay.state else { break }
                    let chunk = SuggestionSessionReconciler.nextAcceptanceChunk(from: session.remainingText)
                    guard !chunk.isEmpty else { break }
                    let expected = SuggestionSessionReconciler.insertionChunk(forAcceptedChunk: chunk, precedingText: text)
                    let before = editor.inserter.insertedChunks.count
                    trial.acceptanceAttempts += 1
                    let accepted = editor.coordinator.acceptCurrentSuggestion()
                    let inserted = editor.inserter.insertedChunks.dropFirst(before).joined()
                    if accepted { trial.accepted += 1 }
                    if (accepted && inserted != expected) || (!accepted && !inserted.isEmpty) {
                        trial.insertionMismatches += 1
                    }
                    if !accepted { break }
                    text += inserted
                    trial.insertedCharacters += inserted.count
                    try await Task.sleep(for: .milliseconds(10))
                    editor.publish(text)
                    editor.coordinator.reconcileActiveSession(with: editor.focus.snapshot)
                    try await Task.sleep(for: .milliseconds(110))
                }
                // Force fresh work, then move to a blocked field. This checks the stale-result
                // guards at the coordinator boundary, without claiming real AX delivery coverage.
                editor.coordinator.schedulePrediction()
                try await Task.sleep(for: .milliseconds(75))
                isBlocked = true
                editor.overlay.onStateChange = { state in
                    originalCallback?(state)
                    if case .visible = state { trial.presentationsAfterBlockedFocus += 1 }
                }
                editor.publish("", blocked: true)
                try await Task.sleep(for: .milliseconds(500))
                let insertCount = editor.inserter.insertedChunks.count
                trial.acceptedInBlockedField = editor.coordinator.acceptCurrentSuggestion()
                trial.insertedInBlockedField = editor.inserter.insertedChunks.count != insertCount
                editor.stop()
                trials.append(trial)
            }
        }
        await engine.resetCachedGenerationContext()
        return trials
    }

    /// Values survive the editor fixture and are written with the outer run's exact provenance.
    struct Trial: Codable {
        let phraseID: String
        let repetition: Int
        var firstVisibleMilliseconds: Double?
        var firstCorrectMilliseconds: Double?
        var acceptanceAttempts = 0
        var accepted = 0
        var insertedCharacters = 0
        var insertionMismatches = 0
        var presentationsAfterBlockedFocus = 0
        var acceptedInBlockedField = false
        var insertedInBlockedField = false
    }

    private static func milliseconds(since start: ContinuousClock.Instant) -> Double {
        let d = start.duration(to: .now).components
        return Double(d.seconds) * 1000 + Double(d.attoseconds) / 1e15
    }

    /// Owns one isolated coordinator graph, exposing only the OS doubles needed to drive it.
    /// Building this graph here avoids transplanting the fork's changed test factory upstream.
    /// Every collaborator is either retained here or by the coordinator for this trial's lifetime.
    @MainActor
    private final class Editor {
        let coordinator: SuggestionCoordinator
        let focus: RigFocusProvider
        let overlay = RigOverlayController()
        let inserter = RigInserter()
        let state = SuggestionInteractionState()
        let defaults: UserDefaults
        let suiteName = "CotabbyTests.scorecard.\(UUID().uuidString)"
        private var stopped = false

        init(text: String, engine: any SuggestionGenerating, apple: Bool) {
            defaults = UserDefaults(suiteName: suiteName)!
            let snapshot = CotabbyTestFixtures.focusedInputSnapshot(precedingText: text)
            focus = RigFocusProvider(snapshot: FocusSnapshot(applicationName: snapshot.applicationName,
                bundleIdentifier: snapshot.bundleIdentifier, capability: .supported, context: snapshot))
            let settings = CotabbyTestFixtures.settingsSnapshot(
                selectedEngine: apple ? .appleIntelligence : .llamaOpenSource, selectedWordCountPreset: .fourToSeven,
                isClipboardContextEnabled: false, isSurfaceContextEnabled: true, userName: "", responseLanguages: [],
                debounceMilliseconds: 50, isMultiLineEnabled: false, streamSuggestionsWhileGenerating: true,
                suppressCompletionsOnTypo: true, offerTypoCorrections: true)
            let permissions = RigPermissionProvider()
            permissions.screenRecordingGranted = false
            coordinator = SuggestionCoordinator(permissionManager: permissions,
                lowPowerModeProvider: RigLowPowerModeProvider(), focusModel: focus, inputMonitor: RigInputMonitor(),
                overlayController: overlay, suggestionInserter: inserter, suggestionEngine: engine,
                suggestionSettings: RigSettingsProvider(snapshot: settings), clipboardContextProvider: RigClipboardProvider(),
                clipboardRelevanceFilter: RigClipboardFilter(), visualContextCoordinator: RigVisualContextCoordinator(),
                interactionState: state, workController: SuggestionWorkController(), configuration: ScorecardRuntime.configuration,
                spellChecker: CurrentWordSpellChecker(), symSpellCorrector: SymSpellCorrector(preloadLanguage: nil),
                qualityMetricsStore: SuggestionQualityMetricsStore(userDefaults: defaults), userDefaults: defaults)
        }

        func publish(_ text: String, blocked: Bool = false) {
            let snapshot = CotabbyTestFixtures.focusedInputSnapshot(elementIdentifier: blocked ? "secure-field" : "field",
                precedingText: text, isSecure: blocked, focusChangeSequence: blocked ? 2 : 1)
            focus.snapshot = FocusSnapshot(applicationName: snapshot.applicationName, bundleIdentifier: snapshot.bundleIdentifier,
                capability: blocked ? .blocked("Synthetic secure field") : .supported, context: snapshot)
            focus.snapshotSubject.send(focus.snapshot)
        }

        func stop() {
            guard !stopped else { return }
            stopped = true
            coordinator.stop()
            defaults.removePersistentDomain(forName: suiteName)
        }
    }
}
#endif
