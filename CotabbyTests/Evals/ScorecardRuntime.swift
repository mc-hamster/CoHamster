import Foundation
@testable import Cotabby

#if RUN_LLAMA_EVAL
/// One replay owns this local runtime configuration. Product sampling defaults are preserved
/// while seed and model path are explicit; no saved model selection is changed.
@MainActor
enum ScorecardRuntime {
    static let seed: UInt32 = 42

    /// Copy product tuning while fixing only the sampling seed. Both eval suites share this so
    /// an A/B run compares prompt/cache changes without a different random sequence per case.
    static var configuration: SuggestionConfiguration {
        let defaults = SuggestionConfiguration.standard
        return SuggestionConfiguration(
            maxPredictionTokens: defaults.maxPredictionTokens, debounceMilliseconds: defaults.debounceMilliseconds,
            temperature: defaults.temperature, topK: defaults.topK, topP: defaults.topP, minP: defaults.minP,
            repetitionPenalty: defaults.repetitionPenalty, randomSeed: seed,
            maxPrefixWords: defaults.maxPrefixWords, maxPrefixCharacters: defaults.maxPrefixCharacters,
            maxPrefixWordsFoundationModel: defaults.maxPrefixWordsFoundationModel,
            maxPrefixCharactersFoundationModel: defaults.maxPrefixCharactersFoundationModel,
            maxSuffixCharacters: defaults.maxSuffixCharacters, llamaPromptTokenBudget: defaults.llamaPromptTokenBudget,
            defaultUserName: defaults.defaultUserName,
            // Share the explicit harness length with the typing replay; otherwise a 4–7-word
            // campaign silently measures streaming with the older 12–20-word default.
            defaultWordCountPreset: ProcessInfo.processInfo.environment["COTABBY_PHRASE_WORD_COUNT"]
                .flatMap(SuggestionWordCountPreset.init(rawValue:)) ?? defaults.defaultWordCountPreset,
            focusPollIntervalMilliseconds: defaults.focusPollIntervalMilliseconds
        )
    }

    static func makeManager() throws -> LlamaRuntimeManager {
        guard let path = ProcessInfo.processInfo.environment["COTABBY_EVAL_MODEL_PATH"], !path.isEmpty else {
            return LlamaRuntimeManager()
        }
        guard path.hasPrefix("/"), FileManager.default.fileExists(atPath: path) else {
            throw NSError(domain: "ScorecardRuntime", code: 1, userInfo: [
                NSLocalizedDescriptionKey: "COTABBY_EVAL_MODEL_PATH must name an existing absolute GGUF path: \(path)"
            ])
        }
        let url = URL(fileURLWithPath: path)
        let defaults = LlamaRuntimeConfiguration.default
        return LlamaRuntimeManager(
            configuration: LlamaRuntimeConfiguration(
                runtimeDirectoryPath: url.deletingLastPathComponent().path,
                preferredModelNames: [url.lastPathComponent],
                contextWindowTokens: defaults.contextWindowTokens,
                batchSize: defaults.batchSize,
                gpuLayerCount: defaults.gpuLayerCount
            ),
            runtimeLocator: BundledRuntimeLocator()
        )
    }
}
#endif
