import tempfile
import subprocess
import sys
import unittest
from pathlib import Path

from analyzer import analyze, iter_source_paths, render_html
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


class SkippedFileTests(unittest.TestCase):
    def test_skip_reasons_and_pruned_directories(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'ok.py').write_text('x = 1\n', encoding='utf-8')
            (root / 'image.bin').write_bytes(b'abc')
            (root / 'invalid.py').write_bytes(b'\xff')
            (root / 'large.py').write_bytes(b'x' * 1000001)
            (root / 'node_modules').mkdir()
            (root / 'node_modules' / 'ignored.py').write_text('x', encoding='utf-8')
            report = analyze(root)
            self.assertEqual(report['files_scanned'], 1)
            self.assertEqual(report['skipped_files'], {
                'symlink': 0, 'not_regular_file': 0, 'unsupported_extension': 1,
                'too_large': 1, 'unreadable': 1,
            })

    def test_empty_directory_has_zero_counts(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(sum(analyze(Path(tmp))['skipped_files'].values()), 0)


class HtmlReportTests(unittest.TestCase):
    def test_escapes_untrusted_filenames(self):
        report = {'files_scanned': 1, 'findings': [
            {'file': '<script>alert(1)</script>.py', 'line': 1, 'rule': 'python-tab'}
        ], 'skipped_files': {'unreadable': 2}}
        output = render_html(report)
        self.assertNotIn('<script>', output)
        self.assertIn('&lt;script&gt;', output)
        self.assertIn('unreadable', output)
        self.assertIn('Files scanned: 1', output)

    def test_empty_report(self):
        output = render_html({'files_scanned': 0, 'findings': [], 'skipped_files': {}})
        self.assertIn('No findings', output)
        self.assertIn('<html lang="en">', output)

    def test_cli_html_and_exit_status(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / 'bad.py').write_text('x  ', encoding='utf-8')
            command = [sys.executable, str(Path(__file__).with_name('analyzer.py')), tmp]
            result = subprocess.run(command + ['--html', '--fail-on-findings'],
                                    capture_output=True, text=True)
            self.assertEqual(result.returncode, 1)
            self.assertIn('trailing-whitespace', result.stdout)
            conflict = subprocess.run(command + ['--html', '--json'],
                                      capture_output=True, text=True)
            self.assertEqual(conflict.returncode, 2)


if __name__ == '__main__':
    unittest.main()
