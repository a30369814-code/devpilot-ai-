"""Dependency-free, read-only checks for local source trees."""
import argparse
import json
from pathlib import Path

SKIP_DIRS = {'.git', '.venv', 'venv', 'node_modules', '__pycache__', 'dist', 'build'}
TEXT_EXTENSIONS = {'.py', '.js', '.ts', '.tsx', '.jsx', '.json', '.md', '.html', '.css'}
MAX_FILE_BYTES = 1_000_000


def analyze(root: Path) -> dict:
    """Report basic hygiene findings without modifying any files."""
    root = root.resolve()
    if not root.is_dir():
        raise ValueError(f'Not a directory: {root}')
    findings = []
    scanned = 0
    for path in sorted(root.rglob('*')):
        if any(part in SKIP_DIRS for part in path.relative_to(root).parts):
            continue
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
            if line.rstrip(' \t') != line:
                findings.append({'file': relative, 'line': line_number, 'rule': 'trailing-whitespace'})
            if '\t' in line and path.suffix == '.py':
                findings.append({'file': relative, 'line': line_number, 'rule': 'python-tab'})
        if content and not content.endswith('\n'):
            findings.append({'file': relative, 'line': len(content.splitlines()), 'rule': 'missing-final-newline'})
    return {'root': str(root), 'files_scanned': scanned, 'findings': findings}


def main() -> None:
    parser = argparse.ArgumentParser(description='Read-only source hygiene analyzer')
    parser.add_argument('path', nargs='?', default='.', help='Directory to inspect')
    parser.add_argument('--json', action='store_true', help='Output JSON')
    args = parser.parse_args()
    try:
        result = analyze(Path(args.path))
    except ValueError as exc:
        parser.error(str(exc))
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"Scanned {result['files_scanned']} files; {len(result['findings'])} findings")
        for item in result['findings']:
            print(f"{item['file']}:{item['line']}: {item['rule']}")


if __name__ == '__main__':
    main()
