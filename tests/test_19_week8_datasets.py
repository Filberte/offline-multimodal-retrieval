"""Week 1 dataset provenance and demo packaging tests, TC-526 through TC-550."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from week8_delivery.datasets import DATASET_CONFIG, DEMO_QUERIES, DEMO_SELECTION, dataset_inventory, default_demo_selection, prepare_demo_dataset
from week8_delivery.models import DatasetSummary


def _synthetic_project(root: Path) -> None:
    base = root / "datasets" / "required_datasets"
    for key, config in DATASET_CONFIG.items():
        manifest = base / key / str(config["manifest"])
        manifest.parent.mkdir(parents=True, exist_ok=True)
        manifest.write_text("{}", encoding="utf-8")
    selected = default_demo_selection(root)
    for path in selected:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"demo")
    layouts = {
        "squad": (base / "squad/processed/contexts", ".txt", 200),
        "coco": (base / "coco/raw/images/val2017", ".jpg", 50),
        "rvl_cdip": (base / "rvl_cdip/raw/images/test", ".png", 50),
        "wikipedia": (base / "wikipedia/processed/articles", ".txt", 100),
    }
    for folder, suffix, expected in layouts.values():
        folder.mkdir(parents=True, exist_ok=True)
        current = len(tuple(folder.glob(f"*{suffix}")))
        for index in range(expected - current):
            (folder / f"synthetic_{index:04d}{suffix}").write_bytes(b"x")


class Week8DatasetTests(unittest.TestCase):
    def test_526_four_week_one_datasets_are_configured(self):
        self.assertEqual(set(DATASET_CONFIG), {"squad", "coco", "rvl_cdip", "wikipedia"})

    def test_527_squad_records_manager_approved_substitution(self):
        self.assertIn("替代", str(DATASET_CONFIG["squad"]["display_name"]))

    def test_528_coco_role_is_multimodal(self):
        self.assertIn("跨模态", str(DATASET_CONFIG["coco"]["role"]))

    def test_529_rvl_role_is_scanned_document(self):
        self.assertIn("扫描", str(DATASET_CONFIG["rvl_cdip"]["role"]))

    def test_530_wikipedia_role_is_long_document(self):
        self.assertIn("长文", str(DATASET_CONFIG["wikipedia"]["role"]))

    def test_531_demo_selection_uses_all_four_datasets(self):
        self.assertEqual(set(DEMO_SELECTION), set(DATASET_CONFIG))

    def test_532_demo_selection_has_twenty_two_files(self):
        self.assertEqual(sum(map(len, DEMO_SELECTION.values())), 22)

    def test_533_demo_contains_six_squad_files(self):
        self.assertEqual(len(DEMO_SELECTION["squad"]), 6)

    def test_534_demo_contains_four_wikipedia_files(self):
        self.assertEqual(len(DEMO_SELECTION["wikipedia"]), 4)

    def test_535_demo_contains_six_coco_files(self):
        self.assertEqual(len(DEMO_SELECTION["coco"]), 6)

    def test_536_demo_contains_six_rvl_files(self):
        self.assertEqual(len(DEMO_SELECTION["rvl_cdip"]), 6)

    def test_537_demo_queries_include_text(self):
        self.assertTrue(any(item["mode"] == "text" for item in DEMO_QUERIES))

    def test_538_demo_queries_include_image(self):
        self.assertTrue(any(item["mode"] == "image" for item in DEMO_QUERIES))

    def test_539_demo_queries_have_narration(self):
        self.assertTrue(all(item["narration"] for item in DEMO_QUERIES))

    def test_540_default_selection_returns_absolute_paths(self):
        with tempfile.TemporaryDirectory() as temp:
            self.assertTrue(all(path.is_absolute() for path in default_demo_selection(temp)))

    def test_541_inventory_returns_dataset_summary_objects(self):
        with tempfile.TemporaryDirectory() as temp:
            _synthetic_project(Path(temp))
            self.assertTrue(all(isinstance(item, DatasetSummary) for item in dataset_inventory(temp)))

    def test_542_inventory_reports_expected_counts(self):
        with tempfile.TemporaryDirectory() as temp:
            _synthetic_project(Path(temp))
            self.assertTrue(all(item.discovered_samples >= item.expected_samples for item in dataset_inventory(temp)))

    def test_543_inventory_reports_all_available(self):
        with tempfile.TemporaryDirectory() as temp:
            _synthetic_project(Path(temp))
            self.assertTrue(all(item.available for item in dataset_inventory(temp)))

    def test_544_inventory_detects_missing_manifest(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            _synthetic_project(root)
            (root / "datasets/required_datasets/coco/metadata/manifest.json").unlink()
            self.assertFalse(next(item for item in dataset_inventory(root) if item.key == "coco").available)

    def test_545_dataset_summary_serializes(self):
        with tempfile.TemporaryDirectory() as temp:
            _synthetic_project(Path(temp))
            self.assertIn("display_name", dataset_inventory(temp)[0].to_dict())

    def test_546_prepare_demo_copies_exact_selection(self):
        with tempfile.TemporaryDirectory() as temp:
            root, output = Path(temp) / "project", Path(temp) / "demo"
            _synthetic_project(root)
            self.assertEqual(prepare_demo_dataset(root, output)["total_files"], 22)

    def test_547_prepare_demo_writes_manifest(self):
        with tempfile.TemporaryDirectory() as temp:
            root, output = Path(temp) / "project", Path(temp) / "demo"
            _synthetic_project(root)
            prepare_demo_dataset(root, output)
            self.assertTrue((output / "week1_demo_manifest.json").is_file())

    def test_548_demo_manifest_is_valid_json(self):
        with tempfile.TemporaryDirectory() as temp:
            root, output = Path(temp) / "project", Path(temp) / "demo"
            _synthetic_project(root)
            prepare_demo_dataset(root, output)
            payload = json.loads((output / "week1_demo_manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(payload["total_files"], 22)

    def test_549_prepare_demo_fails_on_missing_source(self):
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaises(FileNotFoundError):
                prepare_demo_dataset(Path(temp) / "empty", Path(temp) / "demo")

    def test_550_demo_provenance_names_week_one(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "project"
            _synthetic_project(root)
            self.assertIn("Week 1", prepare_demo_dataset(root, Path(temp) / "demo")["provenance"])
