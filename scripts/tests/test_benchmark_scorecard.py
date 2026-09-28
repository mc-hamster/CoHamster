"""Guard report denominators, missing latency, and paired experiment identity."""
import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import benchmark_scorecard as scorecard
import benchmark_report as report


class ScorecardTests(unittest.TestCase):
    def test_suppression_and_errors_remain_in_accuracy_denominator(self):
        rows = [dict(correct=True, wasShown=True, latencyMilliseconds=100),
                dict(correct=False, wasShown=False, latencyMilliseconds=0),
                dict(correct=False, wasShown=False, latencyMilliseconds=500, error='failed')]
        m = scorecard.metrics(rows)
        self.assertEqual(m['accuracy'], 1/3)
        self.assertEqual(m['coverage'], 1/3)
        self.assertEqual(m['precision'], 1)
        self.assertEqual(m['errors'], 1)
        self.assertEqual(m['p95ms'], 100)

    def test_missing_output_is_not_zero_latency_or_perfect_precision(self):
        m = scorecard.metrics([dict(correct=False, wasShown=False, latencyMilliseconds=0)])
        self.assertIsNone(m['p50ms'])
        self.assertIsNone(m['precision'])
        self.assertEqual(m['accuracy'], 0)

    def test_nearest_rank_percentile(self):
        self.assertEqual(scorecard.percentile(list(range(1, 101)), .95), 95)
        self.assertIsNone(scorecard.percentile([], .95))

    def test_ideal_typing_savings_count_tab_and_keep_wrong_words(self):
        rows = [dict(correct=True, wasShown=True, latencyMilliseconds=100,
                     checkpoint=dict(typedCharacters=0, expectedWord='four')),
                dict(correct=False, wasShown=True, latencyMilliseconds=100,
                     checkpoint=dict(typedCharacters=0, expectedWord='five'))]
        m = scorecard.metrics(rows)
        self.assertEqual(m['oracleSavedWordCharacters'], 3)
        self.assertEqual(m['referenceWordCharacters'], 8)
        self.assertEqual(m['oracleWordKeystrokeReduction'], 3/8)
        self.assertEqual(m['correctFinalWithin500ms'], .5)

    def test_hygiene_union_does_not_double_count_output(self):
        m = scorecard.metrics([dict(correct=False, wasShown=True, shown='Sure, wow wow wow!!!!', latencyMilliseconds=1),
                               dict(correct=True, wasShown=True, shown='normal prose', latencyMilliseconds=1)])
        self.assertEqual(m['hygieneFlaggedOutputRate'], .5)
        self.assertEqual(m['hygieneFlags']['assistantPreface'], 1)
        self.assertEqual(m['hygieneFlags']['repeatedWord'], 1)
        self.assertEqual(m['hygieneFlags']['repeatedPunctuation'], 1)

    def test_comparison_rejects_changed_checkpoint_and_reference(self):
        key = ('a', 'none', 1, 0)
        before = {key: ('work', dict(correct=False, checkpoint={'prefix': 'A'}))}
        with self.assertRaises(ValueError):
            report.paired_delta(before, {}, 'none', 10)
        after = {key: ('work', dict(correct=True, checkpoint={'prefix': 'B'}))}
        with self.assertRaises(ValueError):
            report.paired_delta(before, after, 'none', 10)

    def test_bootstrap_pairs_phrases_and_preserves_direction(self):
        before, after = {}, {}
        for phrase in ['a', 'b']:
            for word in [1, 2]:
                key = (phrase, 'none', word, 0)
                before[key] = ('work', dict(correct=False, checkpoint={'prefix': str(word)}))
                after[key] = ('work', dict(correct=True, checkpoint={'prefix': str(word)}))
        d = report.paired_delta(before, after, 'none', 20)
        self.assertEqual(d, dict(deltaPP=100, lowPP=100, highPP=100))


if __name__ == '__main__':
    unittest.main()
