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



class ConfigurationTests(unittest.TestCase):
    def test_select_single_rule(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'bad.py').write_text('x = 1  ', encoding='utf-8')
            report = analyze(root, rules=['missing-final-newline'])
            self.assertEqual([f['rule'] for f in report['findings']], ['missing-final-newline'])

    def test_extra_exclusions_preserve_defaults(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for name in ('generated', 'node_modules'):
                (root / name).mkdir()
                (root / name / 'bad.py').write_text('x  ', encoding='utf-8')
            (root / 'ok.py').write_text('x = 1\n', encoding='utf-8')
            self.assertEqual(analyze(root, exclude_dirs=['generated'])['files_scanned'], 1)

    def test_unknown_rule(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):
                analyze(Path(tmp), rules=['unknown'])

    def test_empty_rule_selection(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'bad.py').write_text('x  ', encoding='utf-8')
            self.assertEqual(analyze(root, rules=[])['findings'], [])


if __name__ == '__main__':
    unittest.main()
