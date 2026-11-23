"""CLI regression tests for opt-in failure status."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).with_name("analyzer.py")


class ExitStatusTests(unittest.TestCase):
    def run_cli(self, directory, *flags):
        return subprocess.run(
            [sys.executable, str(SCRIPT), str(directory), *flags],
            capture_output=True, text=True, check=False
        )

    def test_clean_tree_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "clean.py").write_text("pass\n", encoding="utf-8")
            result = self.run_cli(tmp, "--fail-on-findings", "--json")
            self.assertEqual(result.returncode, 0)
            self.assertEqual(json.loads(result.stdout)["findings"], [])

    def test_findings_fail_only_when_requested(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "bad.py").write_text("pass  \n", encoding="utf-8")
            self.assertEqual(self.run_cli(tmp).returncode, 0)
            result = self.run_cli(tmp, "--json", "--fail-on-findings")
            self.assertEqual(result.returncode, 1)
            self.assertTrue(json.loads(result.stdout)["findings"])

    def test_invalid_directory_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = self.run_cli(Path(tmp) / "missing", "--fail-on-findings")
            self.assertNotEqual(result.returncode, 0)


if __name__ == "__main__":
    unittest.main()
