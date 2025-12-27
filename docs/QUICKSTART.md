# Development & Release Guide

## Quick Start

```bash
pip install pre-commit
pre-commit install
git checkout dev
git checkout -b feature/my-feature
# Make changes, commit, push, create PR
```

## Branch Strategy

- **dev**: Development, merges from features
- **staging**: Release candidate, runs E2E tests, auto-assigns version
- **main**: Production, auto-creates GitHub Release

## Workflow

1. Create feature branch from `dev`
2. Commit with conventional messages (`feat:`, `fix:`, etc.)
3. Push and create PR
4. Pre-commit hooks run automatically (format, lint, secrets)
5. GitHub Actions run tests
6. Merge after approval
7. Repeat until ready for release

## Releasing

```bash
# When dev is stable
git checkout dev
git checkout -b release/prepare
git push origin release/prepare

# Create PR: release/prepare → staging
# GitHub Actions: runs E2E tests
# If pass: auto-generates release notes, assigns version
# Merge to staging

# Create PR: staging → main
# Merge to main
# Auto-creates GitHub Release with version tag
```

## Commit Message Format

```
type(scope): description

feat:     New feature (bumps MINOR)
fix:      Bug fix (bumps PATCH)
feat!:    Breaking change (bumps MAJOR)
```

Examples:
- `feat: add portfolio tracking` → v1.1.0
- `fix: correct order matching` → v1.0.1
- `feat!: change API port` → v2.0.0

## Pre-commit Hooks

Run automatically on every commit:
- End-of-file fixer
- Trailing whitespace
- YAML validation
- Python formatting (black)
- Python linting (ruff)
- Secrets detection
- Shell linting
- Markdown linting

Manual run: `pre-commit run --all-files`

## Testing

**Local** (no Docker):
```bash
pytest tests/test_grpc_integration.py -v
```

**Full stack** (with Docker):
```bash
docker-compose up -d
pytest tests/test_e2e_full_stack.py -v
docker-compose down
```

## Protection Rules

**dev, staging, main**: Require PR review, status checks pass, no force push

## Troubleshooting

**Pre-commit fails?**
```bash
pre-commit run --all-files  # See what failed
black .                      # Fix formatting
ruff check . --fix          # Fix linting
git add . && git commit     # Try again
```

**Can't merge PR?**
- Check GitHub Actions logs (Checks tab)
- Fix issues and push fixes
- PR auto-updates

**Wrong branch?**
```bash
git branch -D wrong-branch
git checkout -b correct-branch
git push origin correct-branch
```
