"""Week 8 contribution lineage tests, TC-501 through TC-525."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from week8_delivery.lineage import default_lineage, validate_lineage
from week8_delivery.models import WeekContribution


def _materialize(root: Path, *, omit: str | None = None) -> None:
    for item in default_lineage():
        for relative in item.source_paths:
            if relative != omit:
                (root / relative).mkdir(parents=True, exist_ok=True)
        for relative in item.evidence_paths:
            if relative != omit:
                path = root / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("evidence", encoding="utf-8")


class Week8LineageTests(unittest.TestCase):
    def test_501_lineage_contains_eight_weeks(self):
        self.assertEqual(len(default_lineage()), 8)

    def test_502_lineage_starts_at_week_one(self):
        self.assertEqual(default_lineage()[0].week, 1)

    def test_503_lineage_ends_at_week_eight(self):
        self.assertEqual(default_lineage()[-1].week, 8)

    def test_504_lineage_week_numbers_are_continuous(self):
        self.assertEqual([item.week for item in default_lineage()], list(range(1, 9)))

    def test_505_each_week_has_focus(self):
        self.assertTrue(all(item.focus for item in default_lineage()))

    def test_506_each_week_has_product_value(self):
        self.assertTrue(all(item.product_value for item in default_lineage()))

    def test_507_each_week_has_source_path(self):
        self.assertTrue(all(item.source_paths for item in default_lineage()))

    def test_508_each_week_has_evidence_path(self):
        self.assertTrue(all(item.evidence_paths for item in default_lineage()))

    def test_509_week_one_feeds_week_two(self):
        self.assertEqual(default_lineage()[0].feeds_week, 2)

    def test_510_week_seven_feeds_week_eight(self):
        self.assertEqual(default_lineage()[6].feeds_week, 8)

    def test_511_week_eight_is_terminal(self):
        self.assertIsNone(default_lineage()[-1].feeds_week)

    def test_512_week_one_mentions_required_datasets(self):
        self.assertIn("datasets/required_datasets", default_lineage()[0].source_paths)

    def test_513_week_two_uses_parser_package(self):
        self.assertTrue(any("week2_parser" in path for path in default_lineage()[1].source_paths))

    def test_514_week_three_uses_embedding_package(self):
        self.assertTrue(any("week3_embedding" in path for path in default_lineage()[2].source_paths))

    def test_515_week_four_uses_retrieval_package(self):
        self.assertTrue(any("week4_retrieval" in path for path in default_lineage()[3].source_paths))

    def test_516_week_five_uses_flutter_application(self):
        self.assertTrue(any("offline_retrieval_ui" in path for path in default_lineage()[4].source_paths))

    def test_517_week_six_uses_integration_package(self):
        self.assertTrue(any("week6_integration" in path for path in default_lineage()[5].source_paths))

    def test_518_week_seven_uses_release_package(self):
        self.assertTrue(any("week7_release" in path for path in default_lineage()[6].source_paths))

    def test_519_week_eight_uses_delivery_package(self):
        self.assertTrue(any("week8_delivery" in path for path in default_lineage()[7].source_paths))

    def test_520_contribution_serializes_to_dictionary(self):
        self.assertEqual(default_lineage()[0].to_dict()["week"], 1)

    def test_521_contribution_is_immutable(self):
        with self.assertRaises(Exception):
            default_lineage()[0].week = 2  # type: ignore[misc]

    def test_522_validation_passes_materialized_chain(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            _materialize(root)
            self.assertTrue(validate_lineage(root)["all_contributions_present"])

    def test_523_validation_detects_missing_source(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            _materialize(root, omit=default_lineage()[3].source_paths[0])
            self.assertFalse(validate_lineage(root)["all_contributions_present"])

    def test_524_validation_detects_missing_evidence(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            _materialize(root, omit=default_lineage()[5].evidence_paths[0])
            self.assertFalse(validate_lineage(root)["all_contributions_present"])

    def test_525_week_contribution_type_is_explicit(self):
        self.assertIsInstance(default_lineage()[0], WeekContribution)
