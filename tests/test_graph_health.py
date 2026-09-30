from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from graph_health import analyze, quality_issues


def note(root: Path, rel: str, body: str, *, canonical: bool = True, note_type: str = "domain") -> None:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    flag = "true" if canonical else "false"
    path.write_text(f"---\ntype: {note_type}\nstatus: active\ncanonical: {flag}\n---\n{body}\n", encoding="utf-8")


class GraphHealthTests(unittest.TestCase):
    def test_isolated_canonical_note_fails(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            note(root, "domains/isolated.md", "No links.")
            result = analyze(root)
            self.assertTrue(any(i["code"] == "ISOLATED_CANONICAL_NODES" for i in quality_issues(result)))

    def test_degree_one_canonical_note_fails(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            note(root, "domains/a.md", "[[domains/b]]")
            note(root, "domains/b.md", "[[domains/a]]")
            result = analyze(root)
            self.assertEqual(result["degree_one_canonical_count"], 2)
            self.assertTrue(any(i["code"] == "DEGREE_ONE_CANONICAL_NODES" for i in quality_issues(result)))

    def test_disconnected_canonical_components_fail(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            note(root, "domains/a.md", "[[domains/b]]")
            note(root, "domains/b.md", "[[domains/a]]")
            note(root, "domains/c.md", "[[domains/d]]")
            note(root, "domains/d.md", "[[domains/c]]")
            result = analyze(root)
            self.assertEqual(result["canonical_operational_components"], 2)
            self.assertTrue(any(i["code"] == "DISCONNECTED_CANONICAL_COMPONENTS" for i in quality_issues(result)))

    def test_moc_only_connectivity_fails(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            note(root, "domains/a.md", "[[mocs/Architecture]]")
            note(root, "mocs/Architecture.md", "[[domains/a]]", canonical=False, note_type="index")
            result = analyze(root)
            self.assertEqual(result["moc_only_canonical_count"], 1)
            self.assertTrue(any(i["code"] == "MOC_ONLY_CANONICAL" for i in quality_issues(result)))

    def test_broken_wikilink_fails(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            note(root, "domains/a.md", "[[missing-target]]")
            result = analyze(root)
            self.assertTrue(any(i["code"] == "BROKEN_WIKILINK" for i in quality_issues(result)))

    def test_excessive_allowlist_fails(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            note(root, "domains/a.md", "No links.")
            result = analyze(root)
            allowlist = {f"domains/allowed-{i}.md": "documented test exception" for i in range(11)}
            self.assertTrue(any(i["code"] == "EXCESSIVE_ALLOWLIST" for i in quality_issues(result, allowlist)))

    def test_historical_and_template_leaf_exceptions_are_not_operational_failures(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            note(root, "history/old.md", "Historical leaf.")
            note(root, "templates/example.md", "Template leaf.")
            result = analyze(root)
            self.assertEqual(result["canonical_operational_notes"], 0)
            self.assertEqual(quality_issues(result), [])


if __name__ == "__main__":
    unittest.main()
