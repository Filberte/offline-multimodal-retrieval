"""Week 7 文档合同、章节覆盖与断链审计测试，共 35 项。"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from week7_release.documentation import (
    audit_documentation,
    default_documentation_manifest,
    local_markdown_links,
    markdown_headings,
)
from week7_release.models import DocumentationAudit, DocumentationEntry


class Week7DocumentationTests(unittest.TestCase):
    def test_371_entry_requires_markdown_extension(self):
        with self.assertRaisesRegex(ValueError, r"\.md"):
            DocumentationEntry("docs/file.txt", "Title", "Users")

    def test_372_entry_requires_title(self):
        with self.assertRaisesRegex(ValueError, "title"):
            DocumentationEntry("docs/file.md", " ", "Users")

    def test_373_entry_requires_audience(self):
        with self.assertRaisesRegex(ValueError, "audience"):
            DocumentationEntry("docs/file.md", "Title", " ")

    def test_374_entry_serializes_headings_as_list(self):
        payload = DocumentationEntry("docs/file.md", "Title", "Users", ("One",)).to_dict()
        self.assertEqual(payload["required_headings"], ["One"])

    def test_375_extracts_level_one_heading(self):
        self.assertEqual(markdown_headings("# Title"), ("Title",))

    def test_376_extracts_multiple_heading_levels(self):
        self.assertEqual(markdown_headings("# A\n## B\n### C"), ("A", "B", "C"))

    def test_377_strips_optional_closing_hashes(self):
        self.assertEqual(markdown_headings("## Heading ##"), ("Heading",))

    def test_378_ignores_hash_without_space(self):
        self.assertEqual(markdown_headings("#Not a heading"), ())

    def test_379_ignores_fenced_code_headings(self):
        self.assertEqual(markdown_headings("```md\n# Fake\n```\n# Real"), ("Real",))

    def test_380_extracts_relative_markdown_link(self):
        self.assertEqual(local_markdown_links("[Guide](GUIDE.md)"), ("GUIDE.md",))

    def test_381_excludes_https_link(self):
        self.assertEqual(local_markdown_links("[Web](https://example.test)"), ())

    def test_382_excludes_anchor_only_link(self):
        self.assertEqual(local_markdown_links("[Section](#section)"), ())

    def test_383_excludes_mailto_link(self):
        self.assertEqual(local_markdown_links("[Mail](mailto:test@example.test)"), ())

    def test_384_decodes_percent_encoded_space(self):
        self.assertEqual(local_markdown_links("[File](My%20File.md)"), ("My File.md",))

    def test_385_strips_fragment_from_file_link(self):
        self.assertEqual(local_markdown_links("[Part](GUIDE.md#part)"), ("GUIDE.md",))

    def test_386_ignores_markdown_image_link(self):
        self.assertEqual(local_markdown_links("![Image](asset.png)"), ())

    def test_387_empty_audit_has_zero_completeness(self):
        audit = DocumentationAudit(0, 0)
        self.assertEqual((audit.passed, audit.completeness_percent), (False, 0.0))

    def test_388_complete_audit_passes(self):
        self.assertTrue(DocumentationAudit(2, 2).passed)

    def test_389_missing_file_fails_audit(self):
        self.assertFalse(DocumentationAudit(1, 0, ("x",)).passed)

    def test_390_missing_heading_fails_audit(self):
        self.assertFalse(DocumentationAudit(1, 1, (), ("x#y",)).passed)

    def test_391_broken_link_fails_audit(self):
        self.assertFalse(DocumentationAudit(1, 1, (), (), ("x->y",)).passed)

    def test_392_completeness_rounds_to_two_decimals(self):
        self.assertEqual(DocumentationAudit(3, 2).completeness_percent, 66.67)

    def test_393_audit_reports_missing_file_path(self):
        with tempfile.TemporaryDirectory() as directory:
            spec = DocumentationEntry("docs/x.md", "x", "users")
            self.assertEqual(audit_documentation(Path(directory), (spec,)).missing_files, ("docs/x.md",))

    def test_394_audit_reports_required_heading(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "docs").mkdir()
            (root / "docs/x.md").write_text("# Title", encoding="utf-8")
            spec = DocumentationEntry("docs/x.md", "x", "users", ("Required",))
            self.assertIn("#Required", audit_documentation(root, (spec,)).missing_headings[0])

    def test_395_heading_match_is_case_insensitive(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "x.md").write_text("## INSTALL", encoding="utf-8")
            spec = DocumentationEntry("x.md", "x", "users", ("Install",))
            self.assertTrue(audit_documentation(root, (spec,)).passed)

    def test_396_audit_reports_broken_relative_link(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "x.md").write_text("# X\n[Missing](missing.md)", encoding="utf-8")
            spec = DocumentationEntry("x.md", "x", "users")
            self.assertEqual(len(audit_documentation(root, (spec,)).broken_links), 1)

    def test_397_audit_accepts_existing_sibling_link(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "x.md").write_text("# X\n[Other](other.md)", encoding="utf-8")
            (root / "other.md").write_text("# Other", encoding="utf-8")
            spec = DocumentationEntry("x.md", "x", "users")
            self.assertTrue(audit_documentation(root, (spec,)).passed)

    def test_398_audit_accepts_parent_directory_link(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "docs").mkdir()
            (root / "NOTICE").write_text("notice", encoding="utf-8")
            (root / "docs/x.md").write_text("[Notice](../NOTICE)", encoding="utf-8")
            spec = DocumentationEntry("docs/x.md", "x", "users")
            self.assertTrue(audit_documentation(root, (spec,)).passed)

    def test_399_audit_counts_only_present_expected_documents(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "one.md").touch()
            specs = (DocumentationEntry("one.md", "1", "u"), DocumentationEntry("two.md", "2", "u"))
            self.assertEqual(audit_documentation(root, specs).present, 1)

    def test_400_audit_serialization_uses_lists(self):
        payload = DocumentationAudit(1, 0, ("x",), ("y",), ("z",)).to_dict()
        self.assertEqual(payload["missing_files"], ["x"])

    def test_401_default_manifest_has_eight_documents(self):
        self.assertEqual(len(default_documentation_manifest()), 8)

    def test_402_default_manifest_paths_are_unique(self):
        paths = [item.path for item in default_documentation_manifest()]
        self.assertEqual(len(paths), len(set(paths)))

    def test_403_default_manifest_covers_end_users_and_maintainers(self):
        audiences = {item.audience for item in default_documentation_manifest()}
        self.assertTrue({"End users", "Maintainers"}.issubset(audiences))

    def test_404_default_manifest_every_document_has_required_headings(self):
        self.assertTrue(all(item.required_headings for item in default_documentation_manifest()))

    def test_405_current_release_documentation_contract_passes(self):
        root = Path(__file__).resolve().parents[1]
        audit = audit_documentation(root, default_documentation_manifest())
        self.assertTrue(audit.passed, audit.to_dict())


if __name__ == "__main__":
    unittest.main()
