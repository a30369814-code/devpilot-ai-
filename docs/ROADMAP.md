# DevPilot AI roadmap

## MVP — read-only local analysis
- [x] Detect trailing whitespace, Python tabs, and missing final newlines
- [x] Exclude dependency and build folders
- [x] Human-readable and JSON reports
- [x] Standard-library unit tests
- [x] GitHub Actions CI for Python tests
- [x] Opt-in failing exit status for CI
- [x] Usage and limitations guide

## Next
- [x] Configurable rules and exclusions
- [ ] Prune excluded directories (implementation pending CI)
- [ ] Add skipped-file reporting
- [ ] HTML report with accessible design
- [ ] Optional GitHub PR integration (read-only first)
- [ ] Optional AI suggestions with explicit opt-in and cost limits

No automatic code edits, credential scanning, or AI provider integration exist yet.
