# hft-trading-app Release Management

## Branch Strategy

```
main (production)
  ↑ (merge from prod after release)
  
staging (pre-production)
  ↑ (merge from dev, runs integration tests)
  
dev (development)
  ↑ (merges from feature branches)
  
feature/* (feature branches)
```

## Release Cycle

### 1. Development Phase (dev branch)

- All feature work happens here
- Pre-commit hooks run automatically
- PR required before merge
- When feature complete, create release candidate

### 2. Staging Phase (staging branch)

**Trigger**: Create PR from `dev` → `staging`

**Automated Checks**:
- ✓ Pre-commit hooks (format, lint, secrets)
- ✓ Unit tests pass
- ✓ Build Docker images
- ✓ Run full stack E2E tests

**If All Pass**:
- ✓ Auto-generate release notes
- ✓ Auto-assign version number (semantic versioning)
- ✓ Create release tag
- ✓ Ready for production

**If Any Fail**:
- ✗ Blocked - fix issues and reopen PR
- ✗ No merge until all checks pass

### 3. Production Phase (main branch)

**Trigger**: Create PR from `staging` → `main`

**Requirements**:
- ✓ All E2E tests passed on staging
- ✓ Release notes generated
- ✓ Version assigned
- ✓ Code review approval

**On Merge to Main**:
- ✓ Tag commit with version: `v1.2.3`
- ✓ Push Docker images to registry with version tag
- ✓ Create GitHub Release with notes
- ✓ Lock main branch (only merges, no direct commits)

## Version Numbering

Semantic Versioning: `MAJOR.MINOR.PATCH`

Examples:
- `0.0.1` - Initial release
- `0.1.0` - Minor feature added
- `1.0.0` - Major release
- `1.0.1` - Patch/bug fix

### Auto-Increment Rules

- **PATCH**: Bug fixes, minor updates → `v1.0.0` to `v1.0.1`
- **MINOR**: New features → `v1.0.1` to `v1.1.0`
- **MAJOR**: Breaking changes → `v1.1.0` to `v2.0.0`

Determined by commit messages:
- `fix:` → PATCH
- `feat:` → MINOR
- `feat!:` or `BREAKING CHANGE:` → MAJOR

## Release Notes Auto-Generation

Generated from commit messages between releases:

```markdown
## Version 1.2.3 (2024-12-13)

### Features
- Add concurrent order support
- Implement portfolio tracking

### Bug Fixes
- Fix order cancellation race condition
- Improve latency measurement

### Internal
- Update dependencies
- Refactor logging system

### Commits
- 123abc4 feat: Add concurrent order support
- 456def7 fix: Order cancellation race condition
```

## Protection Rules

### Pre-commit Hooks (Required)

Every commit must pass:
- ✓ End-of-file fixer
- ✓ Trailing whitespace
- ✓ YAML validation
- ✓ Python formatting (black)
- ✓ Python linting (ruff)
- ✓ Secrets detection
- ✓ Shell script linting
- ✓ Markdown linting

### Branch Protection

**dev branch**:
- Require PR review (1 approval)
- Require status checks pass
- Allow force push (for feature rebase)

**staging branch**:
- Require PR review (1 approval)
- Require status checks pass
- Require E2E tests pass
- No force push

**main branch**:
- Require PR review (1 approval)
- Require status checks pass
- No force push
- Lock for direct commits

## Usage Examples

### Starting a New Feature

```bash
git checkout dev
git pull origin dev
git checkout -b feature/my-feature

# Work on feature...
git add .
git commit -m "feat: add new feature"
git push origin feature/my-feature

# Create PR: feature/my-feature → dev
# After review/approval, merge to dev
```

### Preparing Release

```bash
# Ensure dev is ready
git checkout dev
git pull origin dev

# Create release candidate
git checkout -b release/v1.2.3

# Version bump (if manual needed)
# Usually auto-detected from commits

git commit -m "chore: prepare v1.2.3 release"
git push origin release/v1.2.3

# Create PR: release/v1.2.3 → staging
# GitHub Actions auto-generates release notes
# Creates version tag
```

### Releasing to Production

```bash
# After staging tests pass
# Create PR: staging → main
# On merge:
# - Tag: v1.2.3
# - Push Docker images: v1.2.3
# - Create GitHub Release
```

## Automation Files

- `.github/workflows/release.yml` - Release automation
- `.github/workflows/test.yml` - Test automation
- `scripts/bump-version.sh` - Version bumping
- `scripts/generate-release-notes.sh` - Release notes generation
- `scripts/tag-and-push.sh` - Git tagging and Docker push

## Troubleshooting

### Pre-commit Hooks Fail

```bash
# Run manually to see issues
pre-commit run --all-files --config .pre-commit/.pre-commit-config.yaml

# Fix issues
black .
ruff check . --fix
# Commit fixes
```

### Can't Merge to Staging

```bash
# Check E2E test output
docker-compose logs hft-engine
docker-compose logs hft-backend

# Fix issues, commit, push
git push origin dev
```

### Version Already Exists

```bash
# Delete local and remote tag
git tag -d v1.2.3
git push origin --delete v1.2.3

# Try release again
```

## Checklist for Release

- [ ] All features merged to dev
- [ ] PR: dev → staging created
- [ ] Pre-commit hooks pass
- [ ] Unit tests pass
- [ ] E2E tests pass
- [ ] Docker images build
- [ ] Release notes generated
- [ ] Version assigned
- [ ] PR: staging → main created
- [ ] Code review approval
- [ ] Merge to main
- [ ] Docker images pushed
- [ ] GitHub Release created
- [ ] Announce release

---

**Release Manager**: CI/CD Pipeline
**Last Updated**: December 13, 2024
**Version**: 1.0.0
