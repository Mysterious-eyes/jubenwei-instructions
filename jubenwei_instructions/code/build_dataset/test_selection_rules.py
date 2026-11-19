"""Regression checks for current text exclusion and explicit historical archives."""
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from build_dataset.selection_rules import (
    CURRENT_POLICY, LEGACY_POLICY, policy_from_report, select_source,
    select_source_for_policy, selection_summary,
)
from verify_release import verify_training_instance


def pair(text, tag='n'):
    return [text, f'<ju><xj><sbj><{tag}>{text}</{tag}></sbj></xj></ju>']


class SentenceSelectionTests(unittest.TestCase):
    def test_all_matching_source_occurrences_are_removed(self):
        selected, indices, excluded = select_source([pair('甲'), pair('甲'), pair('乙'), pair('甲')], [pair('甲')])
        self.assertEqual(selected, [pair('乙')])
        self.assertEqual(indices, [3])
        self.assertEqual([r['source_row_1based'] for r in excluded], [1, 2, 4])

    def test_test_multiplicity_does_not_limit_exclusion(self):
        selected, indices, _ = select_source([pair('甲'), pair('甲'), pair('甲'), pair('乙')], [pair('甲'), pair('甲')])
        self.assertEqual((selected, indices), ([pair('乙')], [4]))

    def test_test_multiplicity_can_exceed_source_multiplicity(self):
        selected, _, _ = select_source([pair('甲'), pair('乙')], [pair('甲'), pair('甲')])
        self.assertEqual(selected, [pair('乙')])

    def test_xml_annotation_does_not_change_text_membership(self):
        selected, indices, _ = select_source([pair('子', 'n'), pair('子', 'r'), pair('乙')], [pair('子', 'r')])
        self.assertEqual((selected, indices), ([pair('乙')], [3]))

    def test_xml_layout_does_not_change_text_membership(self):
        formatted = ['甲', '<ju>\n<xj><sbj><n>甲</n></sbj></xj>\n</ju>']
        self.assertEqual(select_source([pair('甲'), pair('乙')], [formatted])[0], [pair('乙')])

    def test_shared_clause_is_retained(self):
        longer = ['甲乙', '<ju><xj><n>甲</n></xj><xj><n>乙</n></xj></ju>']
        selected, indices, _ = select_source([pair('甲'), longer], [pair('甲')])
        self.assertEqual((selected, indices), ([longer], [2]))

    def test_whitespace_is_ignored_but_punctuation_remains(self):
        source = [pair('甲乙'), pair('甲 \t乙'), pair('甲乙。'), pair('丙')]
        selected, indices, _ = select_source(source, [pair('甲\n乙')])
        self.assertEqual((selected, indices), ([source[2], source[3]], [3, 4]))

    def test_case_is_preserved(self):
        selected, indices, _ = select_source([pair('A'), pair('a'), pair('乙')], [pair('A')])
        self.assertEqual((selected, indices), ([pair('a'), pair('乙')], [2, 3]))

    def test_training_duplicates_and_order_are_retained(self):
        source = [pair('乙'), pair('甲'), pair('乙'), pair('丙')]
        selected, indices, _ = select_source(source, [pair('甲')])
        self.assertEqual((selected, indices), ([source[0], source[2], source[3]], [1, 3, 4]))

    def test_missing_test_sentence_fails(self):
        with self.assertRaises(ValueError):
            select_source([pair('甲'), pair('乙')], [pair('丙')])

    def test_empty_training_result_fails(self):
        with self.assertRaises(ValueError):
            select_source([pair('甲'), pair('甲')], [pair('甲')])

    def test_legacy_consumes_only_one_matching_record(self):
        source = [pair('甲'), pair('甲'), pair('甲', 'r'), pair('乙')]
        selected, indices, excluded = select_source_for_policy(source, [pair('甲')], LEGACY_POLICY)
        self.assertEqual((selected, indices), (source[1:], [2, 3, 4]))
        self.assertEqual(excluded, [{'source_row_1based': 1, 'test_row_1based': 1, 'reason': 'selected_test_record'}])

    def test_legacy_requires_annotation_and_multiplicity(self):
        with self.assertRaises(ValueError):
            select_source_for_policy([pair('甲'), pair('乙')], [pair('甲'), pair('甲')], LEGACY_POLICY)
        with self.assertRaises(ValueError):
            select_source_for_policy([pair('甲'), pair('乙')], [pair('甲', 'r')], LEGACY_POLICY)

    def test_default_policy_is_current(self):
        source, test = [pair('甲'), pair('甲'), pair('乙')], [pair('甲')]
        self.assertEqual(select_source_for_policy(source, test), select_source(source, test))

    def test_missing_and_unknown_report_policies_are_rejected(self):
        for report in [{}, {'selected_source_records': 3816}, {'selection_policy': 'unknown'}]:
            with self.assertRaises(ValueError):
                policy_from_report(report)
        with self.assertRaises(ValueError):
            select_source_for_policy([pair('甲'), pair('乙')], [pair('甲')], 'unknown')

    def test_new_partition_conserves_removed_rows_not_reference_multiplicity(self):
        source, test = [pair('甲'), pair('甲'), pair('乙')], [pair('甲')]
        selected, _, excluded = select_source(source, test)
        info = selection_summary(source, test, selected, excluded, CURRENT_POLICY)
        self.assertEqual(info['excluded_test_sentence_records'], 2)
        self.assertEqual(info['reference_records'], 1)
        self.assertEqual(info['remaining_whole_sentence_overlap'], 0)
        self.assertTrue(info['source_partition_conserved'])
        self.assertNotIn('record_multiset_conserved', info)

    def test_shared_clause_diagnostic_is_not_an_exclusion(self):
        longer = ['甲乙', '<ju><xj><n>甲</n></xj><xj><n>乙</n></xj></ju>']
        source, test = [pair('甲'), longer], [pair('甲')]
        selected, _, excluded = select_source(source, test)
        info = selection_summary(source, test, selected, excluded, CURRENT_POLICY)
        self.assertEqual(info['remaining_shared_clause_overlap'], 1)
        self.assertFalse(info['exclude_shared_clauses'])


class TrainingReportVersionTests(unittest.TestCase):
    def check_policy(self, policy):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            source, reference = [pair('甲'), pair('甲'), pair('乙')], [pair('甲')]
            selected, indices, excluded = select_source_for_policy(source, reference, policy)
            def save(name, data):
                path = base / name
                path.write_text(json.dumps(data, ensure_ascii=False), encoding='utf-8')
                return path
            source_path, reference_path = save('source.json', source), save('reference.json', reference)
            sample = {'instruction': 'test', 'input': '', 'output': 'test'}
            save('training_source.json', selected)
            save('integrated_data.json', [sample] * 12)
            save('learn_tag_1.json', [sample] * 54)
            save('learn_tag_2.json', [sample] * 53)
            save('overall_1.json', [{'instruction': 'test', 'input': '', 'output': '<think>test</think>' + row[1]} for row in selected])
            save('split_report.json', {
                **selection_summary(source, reference, selected, excluded, policy),
                'source_sha256': hashlib.sha256(source_path.read_bytes()).hexdigest(),
                'reference_sha256': hashlib.sha256(reference_path.read_bytes()).hexdigest(),
                'selected_source_rows_1based': indices, 'excluded_records': excluded,
                'integrated_records': 12, 'requested_per_task': 1,
                'task_counts': {f'aux_{i}.json': {'generated': 1, 'sampled': 1} for i in range(12)},
            })
            result = verify_training_instance(source_path, reference_path, base, expected_policy=policy)
            self.assertEqual(result['training_selection_policy'], policy)
            self.assertEqual(result['training_instance_records'], len(selected) + 119)
            other = LEGACY_POLICY if policy == CURRENT_POLICY else CURRENT_POLICY
            with self.assertRaises(ValueError):
                verify_training_instance(source_path, reference_path, base, expected_policy=other)

    def test_current_report_verifies(self):
        self.check_policy(CURRENT_POLICY)

    def test_legacy_report_verifies_without_imposing_zero_text_overlap(self):
        self.check_policy(LEGACY_POLICY)


if __name__ == '__main__':
    unittest.main()
