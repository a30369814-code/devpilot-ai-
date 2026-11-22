import tempfile
import unittest
from pathlib import Path

from analyzer import analyze


class AnalyzerTests(unittest.TestCase):
    def test_detects_findings_and_skips_dependencies(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'example.py').write_text('print(1)  \n\tprint(2)', encoding='utf-8')
            (root / 'node_modules').mkdir()
            (root / 'node_modules' / 'bad.js').write_text('x  ', encoding='utf-8')
            report = analyze(root)
            self.assertEqual(report['files_scanned'], 1)
            self.assertEqual({x['rule'] for x in report['findings']},
                             {'trailing-whitespace', 'python-tab', 'missing-final-newline'})

    def test_clean_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / 'ok.py').write_text('print(1)\n', encoding='utf-8')
            self.assertEqual(analyze(Path(tmp))['findings'], [])

    def test_missing_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):
                analyze(Path(tmp) / 'missing')


if __name__ == '__main__':
    unittest.main()
