import Foundation
@testable import Cotabby

/// Test-only bridge from identical fixture inputs to each revision's own production rules.
/// The replay owns the engine and checker; this stateless type only adapts APIs that changed
/// between revisions. Keeping it separate makes the upstream transplant auditable.
@MainActor
enum ScorecardAdapter {
    static func request(_ checkpoint: PhrasePredictionScorer.Checkpoint, phrase: PhrasePredictionCorpus.Phrase,
                        condition: PhrasePredictionScorer.ContextCondition, settings: SuggestionSettingsSnapshot,
                        configuration: SuggestionConfiguration) -> SuggestionRequest {
        let scene = phrase.scenario!
        let context = CotabbyTestFixtures.focusedInputContext(applicationName: scene.applicationName,
            bundleIdentifier: scene.bundleIdentifier, precedingText: checkpoint.prefix, trailingText: "",
            windowTitle: scene.windowTitle, fieldPlaceholder: scene.fieldPlaceholder)
        var excerpt: String?
        if condition == .screen {
            #if SCORECARD_UPSTREAM
            let lines = (scene.screenText + "\n" + checkpoint.prefix).components(separatedBy: .newlines)
                .map { OCRTextHygiene.OCRLine(text: $0, confidence: 0.99) }
            let visual = VisualContextConfiguration.default
            let cleaned = OCRTextHygiene.clean(lines: lines, fieldText: checkpoint.prefix + " ", maxChars: visual.maxRecognizedCharacters)
            let normalized = PromptContextSanitizer.sanitizeOCR(cleaned, maxCharacters: visual.maxRecognizedCharacters)
            let bounded = PromptContextSanitizer.sanitize(normalized, maxCharacters: visual.maxSummaryCharacters)
            let letters = bounded.unicodeScalars.filter(CharacterSet.letters.contains).count
            if bounded.trimmingCharacters(in: .whitespacesAndNewlines).count >= visual.minRecognizedCharacterCount && letters >= 4 { excerpt = bounded }
            #else
            var lines = scene.screenText.components(separatedBy: .newlines).enumerated().map { index, text in
                OCRTextHygiene.OCRLine(text: text, confidence: 0.99,
                    boundingBox: CGRect(x: 0.12, y: max(0.3, 0.95 - Double(index) * 0.055), width: 0.78, height: 0.04))
            }
            lines += checkpoint.prefix.components(separatedBy: .newlines).map {
                OCRTextHygiene.OCRLine(text: $0, confidence: 0.99, boundingBox: CGRect(x: 0.12, y: 0.12, width: 0.78, height: 0.04))
            }
            let visual = VisualContextConfiguration.forEngine(settings.selectedEngine)
            excerpt = VisualContextExcerptSelector.select(lines: lines, fieldText: checkpoint.prefix,
                focusBounds: CGRect(x: 0.12, y: 0.05, width: 0.78, height: 0.15), maxCharacters: visual.maxSummaryCharacters)
            #endif
        }
        return SuggestionRequestFactory.buildRequest(context: context, settings: settings,
            configuration: configuration, visualContextSummary: excerpt).request
    }

    static func shown(_ text: String, prefix: String, checker: CurrentWordSpellChecker, final: Bool) -> String? {
        guard !text.isEmpty else { return nil }
        func assess(_ word: String) -> CompletionSeamGuard.SpellingAssessment {
            #if !SCORECARD_UPSTREAM
            if WordCompletionFallback.referenceWords(precedingText: prefix, trailingText: "", glossary: "")
                .contains(where: { $0.lowercased() == word.lowercased() }) { return .known }
            #endif
            if !checker.isTypo(word) { return .known }
            return checker.bestCorrection(for: word) == nil ? .uncorrectableTypo : .correctableTypo
        }
        #if SCORECARD_UPSTREAM
        if final {
            return CompletionSeamGuard.verdict(precedingText: prefix, completion: text, spellingAssessment: assess) == .allow ? text : nil
        }
        guard CompletionSeamGuard.allowsStreamedPartial(precedingText: prefix, completion: text),
              CompletionSeamGuard.streamedLeadingWordVerdict(precedingText: prefix, completion: text, spellingAssessment: assess) == .allow else { return nil }
        return text
        #else
        if case let .show(value, _) = CompletionSeamGuard.presentation(precedingText: prefix,
            completion: text, isFinal: final, spellingAssessment: assess) { return value }
        return nil
        #endif
    }
}
