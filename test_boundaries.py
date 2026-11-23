"""Regression tests for read-only scanning boundaries."""
import tempfile
import unittest
from pathlib import Path

from analyzer import MAX_FILE_BYTES, analyze


class AnalyzerBoundaryTests(unittest.TestCase):
    def test_skips_nested_dependency_folders(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "src").mkdir()
            (root / "src" / "ok.py").write_text("pass\n", encoding="utf-8")
            (root / "src" / "node_modules").mkdir()
            (root / "src" / "node_modules" / "bad.js").write_text("bad  ", encoding="utf-8")
            report = analyze(root)
            self.assertEqual(report["files_scanned"], 1)
            self.assertEqual(report["findings"], [])

    def test_skips_large_and_invalid_utf8_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "large.py").write_bytes(b"x" * (MAX_FILE_BYTES + 1))
            (root / "invalid.py").write_bytes(b"\\xff\\xfe".decode("unicode_escape").encode("latin1"))
            report = analyze(root)
            self.assertEqual(report["files_scanned"], 0)
            self.assertEqual(report["findings"], [])

    def test_ignores_symlinked_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / "target.py"
            target.write_text("pass\n", encoding="utf-8")
            link = root / "alias.py"
            try:
                link.symlink_to(target)
            except (OSError, NotImplementedError):
                self.skipTest("Symlink creation unavailable")
            report = analyze(root)
            self.assertEqual(report["files_scanned"], 1)
            self.assertEqual(report["findings"], [])


if __name__ == "__main__":
    unittest.main()
