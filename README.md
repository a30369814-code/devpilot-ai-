# DevPilot AI

A lightweight, read-only source hygiene analyzer for developers. The current MVP uses deterministic Python rules, not an AI model.

## Quick start

Requires Python 3.12 (the version used in CI). No third-party packages are needed.

```sh
git clone https://github.com/a30369814-code/devpilot-ai-.git
cd devpilot-ai-
python analyzer.py .
```

Scan another project by passing its directory, for example `python analyzer.py "/path/to/project"`.

## Reports and CI

```sh
python analyzer.py . --json
python analyzer.py . --fail-on-findings
python analyzer.py . --json --fail-on-findings
```

The JSON report includes the root directory, number of scanned files, and findings with relative file paths, line numbers and rule identifiers. Exit status is 0 by default, 1 for findings when explicitly requested, and 2 for invalid command-line arguments or a missing directory.

## Current checks

- Trailing spaces and tabs.
- Tabs anywhere in Python source lines (a basic heuristic, not a syntax check).
- Missing final newline.

The scanner checks common source and documentation extensions, skips common dependency/build directories, symbolic-link files, files larger than 1 MB, and files it cannot decode as UTF-8. It does not edit files. It is not a security scanner; only scan directories you are authorized to inspect. Reports may reveal local paths and filenames.

## Testing

```sh
python -m unittest -v
```

GitHub Actions runs syntax checks, unit tests and a JSON smoke test. See [workflow history](https://github.com/a30369814-code/devpilot-ai-/actions).

## Development

- [Roadmap](docs/ROADMAP.md)
- [Progress log](docs/PROGRESS.md)

Planned features include configurable rules, accessible HTML reports and optional AI suggestions. These are not implemented yet.
