# Changelog

All notable changes to DataMind will be documented in this file.

## [Unreleased]

### Added
- MIT LICENSE (Copyright (c) 2026 Vikas Valvi)
- .gitattributes for line ending normalization
- .editorconfig for consistent editor settings
- .github/workflows/ci.yml for CI on Python 3.11 and 3.12
- .pre-commit-config.yaml with Ruff hooks
- Makefile with setup, run, test, lint, clean targets
- Dockerfile for containerized deployment
- .dockerignore for Docker builds
- CONTRIBUTING.md with development guidelines
- `datamind` command entry point via [project.scripts]
- [project.urls] section in pyproject.toml

### Changed
- .gitignore: Added *.egg-info/, .kilo/, .agents/skills/, *.pyc
- pyproject.toml: Updated author to Vikas Valvi
- pyproject.toml: Changed ruff target-version from py312 to py311
- README.md: DATAMIND_STORAGE_ROOT → DATAMIND_STORAGE_DIR
- README.md: Removed hardcoded test count
- .env.example: Documented all variables, removed "Proposed / M0" wording
- All text files normalized from CRLF to LF (batch/PowerShell scripts kept as CRLF)

### Fixed
- Recreated datamind/storage/ package (database, repositories, experiment_repos, artifacts, locks)
- DatasetRepository now validates project existence before creating dataset
- SplitRepository raises FileNotFoundError if manifest file is missing (data leak protection)
- environment_json now captured in service layer, not repository
- Fixed relative paths in scripts to work from scripts/ directory
- Scripts now use `python -m streamlit` for portability
- Pruned stale git worktree from deleted .kilo directory

### Moved
- scripts/run.bat (from start_datamind.bat)
- scripts/run.ps1 (from start_datamind.ps1)
- scripts/setup.ps1 (from setup_datamind.ps1)
- examples/demo_m2.py (from scripts/)
- examples/demo_m3_mvp.py (from scripts/)
- examples/demo_m4_export.py (from scripts/)
- examples/demo_m5.py (from scripts/)
- docs/ARCHITECTURE.md (from root)
- docs/internal/PRD.md (from root)
- docs/internal/PROJECT_STATE.md (from root)

### Deleted
- datamind.egg-info/ (build artifacts)
- .kilo/ (git worktree directory)
- docs/screenshots/phase3/snapshot01.txt
- .agents/skills/ui-ux-pro-max/ (external skill directory)
- start_datamind_simple.bat and .ps1 (duplicates)
- STARTUP_GUIDE.md (merged into docs/SETUP_WINDOWS.md)
