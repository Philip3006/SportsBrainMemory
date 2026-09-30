from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from validate_operational_memory import validate


class OperationalMemoryTests(unittest.TestCase):
    def test_current_operational_surface_is_valid(self):
        result = validate(ROOT)
        self.assertEqual(result["errors"], 0, result["issues"])

    def test_broken_current_link_is_an_error(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "_meta").mkdir()
            (root / "_meta" / "MEMORY_V2.json").write_text('{"source_main_sha":"1234567890123456789012345678901234567890"}\n')
            (root / "00_HOME.md").write_text("---\ntype: generated-view\nstatus: current\n---\n[[missing-note]]\n")
            (root / "CURRENT_STATE.md").write_text("1234567890123456789012345678901234567890\n")
            result = validate(root)
            self.assertTrue(any(issue["code"] == "BROKEN_WIKILINK" for issue in result["issues"]))


if __name__ == "__main__":
    unittest.main()
