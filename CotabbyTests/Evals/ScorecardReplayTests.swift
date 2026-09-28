import CryptoKit
import Darwin
import XCTest
@testable import Cotabby

/// Portable, opt-in scorecard runner. One XCTest invocation owns one engine and a durable
/// journal. The Python campaign owns builds and model order; the existing 1337 scorer owns
/// correctness. SCORECARD_UPSTREAM selects only API adapters, never replacement product rules.
/// No editor, saved preference, installed app, or remote inference endpoint is mutated here.
@MainActor
final class ScorecardReplayTests: XCTestCase {
    func testScorecard() async throws {
        #if RUN_LLAMA_EVAL
        let env = ProcessInfo.processInfo.environment
        try XCTSkipUnless(env["COTABBY_SCORECARD"] == "1", "Use scripts/benchmark_scorecard.py")
        let output = URL(fileURLWithPath: try XCTUnwrap(env["COTABBY_SCORECARD_OUTPUT"]))
        let apple = env["COTABBY_SCORECARD_MODEL"] == "apple"
        let smoke = env["COTABBY_SCORECARD_SMOKE"] == "1"
        let url = try XCTUnwrap(Bundle(for: Self.self).url(forResource: "phrase-prediction-1337", withExtension: "json"))
        let data = try Data(contentsOf: url)
        let corpus = try JSONDecoder().decode(PhrasePredictionCorpus.self, from: data)
        try corpus.validate()
        let defaults = UserDefaults.standard
        let oldDomain = defaults.volatileDomain(forName: UserDefaults.argumentDomain)
        var domain = oldDomain
        domain[LlamaSuggestionEngine.confidenceFloorOverrideKey] = NSNumber(value: LlamaSuggestionEngine.defaultConfidenceFloor)
        domain[LlamaSuggestionEngine.argmaxStopDisabledKey] = false
        defaults.setVolatileDomain(domain, forName: UserDefaults.argumentDomain)
        defer { defaults.setVolatileDomain(oldDomain, forName: UserDefaults.argumentDomain) }

        let loadStart = ContinuousClock.now
        let manager: LlamaRuntimeManager?
        let engine: any SuggestionGenerating
        if apple {
            manager = nil
            let availability = FoundationModelAvailabilityService()
            guard availability.isAvailable else {
                throw NSError(domain: "Scorecard", code: 1, userInfo: [NSLocalizedDescriptionKey: availability.userVisibleMessage])
            }
            if #available(macOS 26.0, *) {
                engine = FoundationModelSuggestionEngine(availabilityService: availability)
            } else { throw XCTSkip("Apple Intelligence requires macOS 26") }
        } else {
            let runtime = try ScorecardRuntime.makeManager()
            manager = runtime
            try await runtime.prepare()
            engine = LlamaSuggestionEngine(runtimeManager: runtime)
        }
        defer { manager?.shutdownSync(timeoutSeconds: 5) }
        let loadMilliseconds = Self.milliseconds(since: loadStart)
        let settings = CotabbyTestFixtures.settingsSnapshot(
            selectedEngine: apple ? .appleIntelligence : .llamaOpenSource,
            selectedWordCountPreset: .fourToSeven, isClipboardContextEnabled: false,
            isSurfaceContextEnabled: true, userName: "", responseLanguages: [],
            isMultiLineEnabled: false, suppressCompletionsOnTypo: true, offerTypoCorrections: true
        )
        let checker = CurrentWordSpellChecker()
        let configuration = ScorecardRuntime.configuration
        let journalURL = output.appendingPathComponent("observations.jsonl")
        guard !FileManager.default.fileExists(atPath: journalURL.path) else {
            throw NSError(domain: "Scorecard", code: 2, userInfo: [NSLocalizedDescriptionKey: "Refusing to overwrite a journal"])
        }
        FileManager.default.createFile(atPath: journalURL.path, contents: nil)
        let journal = try FileHandle(forWritingTo: journalURL)
        defer { try? journal.close() }
        let encoder = JSONEncoder()
        encoder.outputFormatting = [.sortedKeys]
        func append<T: Encodable>(_ value: T) throws {
            try journal.write(contentsOf: encoder.encode(value) + Data([10]))
            try journal.synchronize()
        }
        let metadata: [String: String] = [
            "engine": apple ? "apple" : "llama", "os": ProcessInfo.processInfo.operatingSystemVersionString,
            "corpusSHA256": SHA256.hash(data: data).map { String(format: "%02x", $0) }.joined(),
            "wordCount": "4-7", "seed": apple ? "not controllable through production Apple engine" : "42",
            "model": manager?.diagnostics.modelFilePath ?? "Apple SystemLanguageModel.default",
            "loadMilliseconds": String(loadMilliseconds), "smoke": String(smoke),
            "configuration": String(describing: configuration),
            "confidenceFloor": String(LlamaSuggestionEngine.resolvedConfidenceFloor()),
            "stopAtArgmaxEOG": String(LlamaSuggestionEngine.resolvedStopAtArgmaxEOG())
        ]
        try encoder.encode(metadata).write(to: output.appendingPathComponent("metadata.json"), options: .atomic)
        let categories = Array(Set(corpus.phrases.map(\.category))).sorted()
        // Fixed selection, chosen by ID before seeing model output. These diagnostic subsets are
        // not independent held-out data and never replace the full 1337 accuracy denominator.
        let sample = categories.flatMap { category in corpus.phrases.filter { $0.category == category }.prefix(smoke ? 1 : 2) }
        let accuracy = smoke ? sample : corpus.phrases
        let resourceStart = Self.resources()
        for (index, phrase) in accuracy.enumerated() {
            for condition in PhrasePredictionReplayPlan.conditions(at: index, mode: .paired) {
                await engine.resetCachedGenerationContext()
                var observations: [PhrasePredictionObservation] = []
                for checkpoint in PhrasePredictionScorer.checkpoints(for: phrase, mode: .word) {
                    let record = try await observe(checkpoint, phrase: phrase, condition: condition, engine: engine,
                        checker: checker, settings: settings, configuration: configuration, streaming: false)
                    observations.append(record.observation)
                }
                try append(ScorecardPhraseRecord(stage: "accuracy", result: .init(phrase: phrase, observations: observations, condition: condition)))
            }
            if index % 10 == 0 { print("SCORECARD accuracy \(index + 1)/\(accuracy.count)") }
        }
        for (index, phrase) in sample.enumerated() {
            for condition in PhrasePredictionReplayPlan.conditions(at: index, mode: .paired) {
                await engine.resetCachedGenerationContext()
                var observations: [PhrasePredictionObservation] = []
                for checkpoint in PhrasePredictionScorer.checkpoints(for: phrase, mode: .character) where checkpoint.typedCharacters > 0 {
                    let record = try await observe(checkpoint, phrase: phrase, condition: condition, engine: engine,
                        checker: checker, settings: settings, configuration: configuration, streaming: false)
                    observations.append(record.observation)
                }
                try append(ScorecardPhraseRecord(stage: "partial", result: .init(phrase: phrase, observations: observations, condition: condition)))
                let checkpoint = try XCTUnwrap(PhrasePredictionScorer.checkpoints(for: phrase, mode: .word).first)
                for repetition in 0..<(smoke ? 1 : 3) {
                    for prewarmed in [false, true] {
                        await engine.resetCachedGenerationContext()
                        if prewarmed {
                            let request = ScorecardAdapter.request(checkpoint, phrase: phrase, condition: condition, settings: settings, configuration: configuration)
                            await engine.prewarm(for: request)
                        }
                        var record = try await observe(checkpoint, phrase: phrase, condition: condition, engine: engine,
                            checker: checker, settings: settings, configuration: configuration, streaming: true)
                        record.stage = "timing"; record.phraseID = phrase.id; record.condition = condition.rawValue
                        record.prewarmed = prewarmed; record.repetition = repetition
                        try append(record)
                    }
                }
                await engine.resetCachedGenerationContext()
                let cancellationRequest = ScorecardAdapter.request(checkpoint, phrase: phrase,
                    condition: condition, settings: settings, configuration: configuration)
                var ended = false
                var cancellationRequested = false
                var latePartials = 0
                let work = Task { @MainActor in
                    defer { ended = true }
                    do {
                        _ = try await engine.generateSuggestion(for: cancellationRequest, onPartial: { _ in
                            if cancellationRequested { latePartials += 1 }
                        })
                        return "returned"
                    } catch is CancellationError { return "cancelled" }
                    catch SuggestionClientError.cancelled { return "cancelled" }
                    catch { return "error: " + error.localizedDescription }
                }
                try await Task.sleep(for: .milliseconds(100))
                let completedBeforeCancel = ended
                cancellationRequested = true
                let cancelStart = ContinuousClock.now
                work.cancel()
                let outcome = await work.value
                try append(ScorecardCancellationRecord(phraseID: phrase.id, condition: condition.rawValue,
                    completedBeforeCancel: completedBeforeCancel, drainMilliseconds: Self.milliseconds(since: cancelStart),
                    latePartials: latePartials, outcome: outcome))
            }
        }
        let interactions = try await ScorecardInteractionReplay.run(engine: engine, apple: apple,
            phrases: categories.compactMap { category in corpus.phrases.first { $0.category == category } }, smoke: smoke)
        try encoder.encode(interactions).write(to: output.appendingPathComponent("interactions.json"), options: .atomic)
        let end = Self.resources()
        let resources = ["processPeakRSSBytes": end["rss"]!,
                         "processCPUSeconds": end["cpu"]! - resourceStart["cpu"]!,
                         "wallSeconds": Self.milliseconds(since: loadStart) / 1000]
        try encoder.encode(resources).write(to: output.appendingPathComponent("resources.json"), options: .atomic)
        // Completion is written only after every planned phrase and diagnostic has been journaled.
        try Data("complete\n".utf8).write(to: output.appendingPathComponent("complete"), options: .atomic)
        #else
        throw XCTSkip("Build with RUN_LLAMA_EVAL")
        #endif
    }

    #if RUN_LLAMA_EVAL
    private func observe(_ checkpoint: PhrasePredictionScorer.Checkpoint, phrase: PhrasePredictionCorpus.Phrase,
                         condition: PhrasePredictionScorer.ContextCondition, engine: any SuggestionGenerating,
                         checker: CurrentWordSpellChecker, settings: SuggestionSettingsSnapshot,
                         configuration: SuggestionConfiguration, streaming: Bool) async throws -> ScorecardTimingRecord {
        let gate = TypoGate.resolve(precedingText: checkpoint.prefix,
            settings: .init(suppressCompletionsOnTypo: true, offerTypoCorrections: true, automaticallyFixTypos: false),
            isTypo: { checker.isTypo($0) }, bestCorrection: { checker.bestCorrection(for: $0) })
        if !SuggestionRequestFactory.shouldGenerateSuggestion(for: checkpoint.prefix) || gate != .proceed {
            return .init(observation: .init(checkpoint: checkpoint, raw: "", shown: nil,
                suppression: "pre-generation-or-typo-gate", latencyMilliseconds: 0, error: nil))
        }
        let start = ContinuousClock.now
        let request = ScorecardAdapter.request(checkpoint, phrase: phrase, condition: condition, settings: settings, configuration: configuration)
        // Render the diagnostic copy after stopping the clock. Apple's engine renders these
        // channels itself; rendering them twice inside the clock would inflate only its timing.
        func recordedPrompt() -> String {
            settings.selectedEngine == .appleIntelligence
                ? "INSTRUCTIONS:\n" + FoundationModelPromptRenderer.sessionInstructions(for: request)
                    + "\nPROMPT:\n" + FoundationModelPromptRenderer.prompt(for: request)
                : request.prompt
        }
        var firstVisible: Double?
        var firstCorrect: Double?
        var revisions = 0
        var previous: String?
        func consider(_ result: SuggestionResult, final: Bool) -> String? {
            let shown = ScorecardAdapter.shown(result.text, prefix: checkpoint.prefix, checker: checker, final: final)
            if let shown, !shown.isEmpty {
                if firstVisible == nil { firstVisible = Self.milliseconds(since: start) }
                if firstCorrect == nil && PhrasePredictionScorer.isCorrect(shown: shown, at: checkpoint) {
                    firstCorrect = Self.milliseconds(since: start)
                }
                if let previous, !shown.hasPrefix(previous) { revisions += 1 }
                previous = shown
            }
            return shown
        }
        do {
            let result: SuggestionResult
            if streaming {
                result = try await engine.generateSuggestion(for: request, onPartial: { _ = consider($0, final: false) })
            } else { result = try await engine.generateSuggestion(for: request) }
            try Task.checkCancellation()
            let shown = consider(result, final: true)
            let elapsed = Self.milliseconds(since: start)
            return .init(observation: .init(checkpoint: checkpoint, raw: result.rawText, shown: shown,
                suppression: shown == nil ? "normalizer-or-display-guard" : nil,
                latencyMilliseconds: elapsed, error: nil,
                screenExcerpt: request.visualContextSummary, prompt: recordedPrompt()),
                firstVisibleMilliseconds: firstVisible, firstCorrectMilliseconds: firstCorrect,
                revisions: revisions, withdrawn: previous != nil && shown == nil)
        } catch is CancellationError { throw CancellationError() }
        catch {
            let elapsed = Self.milliseconds(since: start)
            return .init(observation: .init(checkpoint: checkpoint, raw: "", shown: nil, suppression: nil,
                latencyMilliseconds: elapsed, error: error.localizedDescription,
                screenExcerpt: request.visualContextSummary, prompt: recordedPrompt()),
                firstVisibleMilliseconds: firstVisible, firstCorrectMilliseconds: firstCorrect,
                revisions: revisions, withdrawn: previous != nil)
        }
    }

    private static func milliseconds(since start: ContinuousClock.Instant) -> Double {
        let d = start.duration(to: .now).components
        return Double(d.seconds) * 1000 + Double(d.attoseconds) / 1e15
    }

    private static func resources() -> [String: Double] {
        var usage = rusage()
        getrusage(RUSAGE_SELF, &usage)
        return ["rss": Double(usage.ru_maxrss), "cpu": Double(usage.ru_utime.tv_sec + usage.ru_stime.tv_sec)
            + Double(usage.ru_utime.tv_usec + usage.ru_stime.tv_usec) / 1e6]
    }
    #endif
}

/// Journal envelopes live for one observation/phrase. Separate records let the campaign retain
/// completed work after interruption without confusing a partial journal with a finished run.
private struct ScorecardPhraseRecord: Encodable {
    let stage: String
    let result: PhrasePredictionReport.PhraseResult
}

private struct ScorecardTimingRecord: Encodable {
    var stage = "observation"
    var phraseID = ""
    var condition = ""
    var prewarmed = false
    var repetition = 0
    let observation: PhrasePredictionObservation
    var firstVisibleMilliseconds: Double? = nil
    var firstCorrectMilliseconds: Double? = nil
    var revisions = 0
    var withdrawn = false
}

/// A cancellation trial distinguishes a request already finished at 100 ms from one actually
/// interrupted. The replay owns its task and measures drain/callbacks, not coordinator behavior.
private struct ScorecardCancellationRecord: Encodable {
    let stage = "cancellation"
    let phraseID: String
    let condition: String
    let completedBeforeCancel: Bool
    let drainMilliseconds: Double
    let latePartials: Int
    let outcome: String
}
