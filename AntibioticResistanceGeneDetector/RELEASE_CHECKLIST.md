# Release Checklist

## Version Bump Steps
- Update `VERSION` file to new version (e.g., `0.1.2` for stable, `0.1.2-rc1` for release candidate)
- Add new section to `CHANGELOG.md` with changes

## RC-Tagging Steps
- Create a git tag with pattern `vX.Y.Z-rcN` (e.g., `v0.1.2-rc1`)
- Push tag to GitHub to trigger TestPyPI workflow

## Stable Tagging Steps
- Create a git tag with pattern `vX.Y.Z` (e.g., `v0.1.2`)
- Push tag to GitHub to trigger production PyPI workflow

## Pre-Release Validation Instructions
- Ensure all tests pass locally (`pytest -q`)
- Run pre-release validation workflow on all platforms
- Confirm CLI tool works after pip install

## TestPyPI Verification Checklist
- Confirm TestPyPI workflow passes
- Install from TestPyPI: `pip install --index-url https://test.pypi.org/simple/ --no-deps arg-res-detector`
- Run `arg_res_detector --version` and a sample detection
- Check output files and CLI help

## Production PyPI Publishing Checklist
- Confirm PyPI workflow passes
- Install from PyPI: `pip install arg-res-detector`
- Run `arg_res_detector --version` and a sample detection
- Check output files and CLI help

## Post-Release Tasks
- Update `CHANGELOG.md` for next version
- Verify documentation and README badges
- Test CLI tool on fresh environment
- Announce release if desired
