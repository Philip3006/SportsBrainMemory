import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))

from validate_visual_metadata import analyze  # noqa: E402


def write_note(root: Path, rel: str, **meta: str) -> None:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    frontmatter = "\n".join(["---", *[f"{key}: {value}" for key, value in meta.items()], "---", "# Note", ""])
    path.write_text(frontmatter, encoding="utf-8")


class VisualMetadataTests(unittest.TestCase):
    def test_valid_operational_metadata_passes_and_counts(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            write_note(root, "domains/TOP5.md", canonical="true", status="active", graph_domain="top5", graph_role="core")
            result = analyze(root)
            self.assertTrue(result["quality"]["ok"])
            self.assertEqual(result["graph_domain_counts"], {"top5": 1})
            self.assertEqual(result["graph_role_counts"], {"core": 1})

    def test_missing_operational_metadata_fails_closed(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            write_note(root, "domains/TOP5.md", canonical="true", status="active", graph_role="core")
            result = analyze(root)
            self.assertFalse(result["quality"]["ok"])
            self.assertEqual(result["quality"]["issues"][0]["code"], "MISSING_GRAPH_DOMAIN")

    def test_invalid_domain_and_role_fail(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            write_note(root, "domains/TOP5.md", canonical="true", status="active", graph_domain="sports", graph_role="anchor")
            result = analyze(root)
            self.assertFalse(result["quality"]["ok"])
            self.assertEqual({issue["code"] for issue in result["quality"]["issues"]}, {"INVALID_GRAPH_DOMAIN", "INVALID_GRAPH_ROLE"})

    def test_historical_and_template_leaves_are_not_required(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            write_note(root, "history/old.md", canonical="true", status="completed")
            write_note(root, "templates/template.md", canonical="true", status="retired")
            result = analyze(root)
            self.assertTrue(result["quality"]["ok"])
            self.assertEqual(result["canonical_operational_notes"], 0)
            self.assertEqual(result["canonical_operational_missing_visual_metadata"], [])

    def test_noncanonical_notes_may_remain_unclassified(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            write_note(root, "views/guide.md", canonical="false", status="current")
            result = analyze(root)
            self.assertTrue(result["quality"]["ok"])
            self.assertEqual(result["notes_with_graph_domain"], 0)


if __name__ == "__main__":
    unittest.main()
