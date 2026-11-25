import tempfile
import unittest
from pathlib import Path

from analyzer import analyze, iter_source_paths
from unittest.mock import patch


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


class TraversalTests(unittest.TestCase):
    def test_prunes_before_descending(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            def fake_walk(path, *, topdown, followlinks):
                self.assertTrue(topdown)
                self.assertFalse(followlinks)
                dirs = ['node_modules', 'generated', 'src']
                yield str(root), dirs, ['z.py']
                self.assertEqual(dirs, ['src'])
                yield str(root / 'src'), [], ['a.py']
            with patch('analyzer.os.walk', side_effect=fake_walk):
                self.assertEqual(list(iter_source_paths(root, {'node_modules', 'generated'})),
                                 [root / 'src' / 'a.py', root / 'z.py'])

    def test_nested_exclusions_and_order(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for name in ('z.py', 'src/a.py', 'src/generated/b.py', 'src/node_modules/c.py'):
                path = root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text('x  ', encoding='utf-8')
            report = analyze(root, exclude_dirs=['generated'])
            self.assertEqual(report['files_scanned'], 2)
            self.assertEqual([f['file'] for f in report['findings'] if f['rule'] == 'trailing-whitespace'],
                             ['src/a.py', 'z.py'])


if __name__ == '__main__':
    unittest.main()
