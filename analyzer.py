"""Dependency-free, read-only checks for local source trees."""
import argparse
import json
import os
import sys
from pathlib import Path

SKIP_DIRS = {'.git', '.venv', 'venv', 'node_modules', '__pycache__', 'dist', 'build'}
TEXT_EXTENSIONS = {'.py', '.js', '.ts', '.tsx', '.jsx', '.json', '.md', '.html', '.css'}
MAX_FILE_BYTES = 1_000_000
RULES = frozenset({'trailing-whitespace', 'python-tab', 'missing-final-newline'})


def iter_source_paths(root: Path, skip_dirs):
    """Prune excluded directories before descent; preserve sorted path order."""
    paths = []
    for directory, dirs, files in os.walk(root, topdown=True, followlinks=False):
        dirs[:] = [name for name in dirs if name not in skip_dirs]
        paths.extend(Path(directory) / name for name in files if name not in skip_dirs)
    yield from sorted(paths)


def analyze(root: Path, *, rules=None, exclude_dirs=()) -> dict:
    """Report basic hygiene findings without modifying any files."""
    active_rules = RULES if rules is None else frozenset(rules)
    if active_rules - RULES:
        raise ValueError('Unknown rules: ' + ', '.join(sorted(active_rules - RULES)))
    skip_dirs = SKIP_DIRS.union(exclude_dirs)
    root = root.resolve()
    if not root.is_dir():
        raise ValueError(f'Not a directory: {root}')
    findings = []
    scanned = 0
    for path in iter_source_paths(root, skip_dirs):
        if not path.is_file() or path.is_symlink() or path.suffix.lower() not in TEXT_EXTENSIONS:
            continue
        try:
            if path.stat().st_size > MAX_FILE_BYTES:
                continue
            content = path.read_text(encoding='utf-8')
        except (OSError, UnicodeError):
            continue
        scanned += 1
        relative = path.relative_to(root).as_posix()
        for line_number, line in enumerate(content.splitlines(), 1):
            if 'trailing-whitespace' in active_rules and line.rstrip(' \t') != line:
                findings.append({'file': relative, 'line': line_number, 'rule': 'trailing-whitespace'})
            if 'python-tab' in active_rules and '\t' in line and path.suffix == '.py':
                findings.append({'file': relative, 'line': line_number, 'rule': 'python-tab'})
        if 'missing-final-newline' in active_rules and content and not content.endswith('\n'):
            findings.append({'file': relative, 'line': len(content.splitlines()), 'rule': 'missing-final-newline'})
    return {'root': str(root), 'files_scanned': scanned, 'findings': findings}


def main() -> None:
    parser = argparse.ArgumentParser(description='Read-only source hygiene analyzer')
    parser.add_argument('path', nargs='?', default='.', help='Directory to inspect')
    parser.add_argument('--json', action='store_true', help='Output JSON')
    parser.add_argument('--fail-on-findings', action='store_true',
                        help='Exit with status 1 when any findings are detected')
    parser.add_argument('--rule', action='append', choices=sorted(RULES),
                        help='Enable only this rule; repeat to select multiple rules')
    parser.add_argument('--exclude-dir', action='append', default=[],
                        help='Additional directory name to skip; repeat as needed')
    args = parser.parse_args()
    try:
        result = analyze(Path(args.path), rules=args.rule, exclude_dirs=args.exclude_dir)
    except ValueError as exc:
        parser.error(str(exc))
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"Scanned {result['files_scanned']} files; {len(result['findings'])} findings")
        for item in result['findings']:
            print(f"{item['file']}:{item['line']}: {item['rule']}")
    if args.fail_on_findings and result['findings']:
        sys.exit(1)


if __name__ == '__main__':
    main()
