# DEVELOPMENT_GUIDE.md

Development workflow and branch strategy for hft-trading-app.

## Quick Start

```bash
# Clone repo
git clone <repo-url>
cd hft-trading-app

# Setup pre-commit
pip install pre-commit
pre-commit install

# Start development
git checkout -b feature/my-feature dev
```

## Branch Strategy

### `main` (Production)

- **Protected**: No direct commits
- **Merges from**: `staging` only
- **When to use**: Final production releases
- **Auto-actions**: Create GitHub Release, tag version, push Docker images

### `staging` (Pre-Production)

- **Protected**: PR review required, E2E tests must pass
- **Merges from**: `dev` only
- **When to use**: Release candidates, final testing
- **Auto-actions**: Run full E2E test suite, generate release notes

### `dev` (Development)

- **Protected**: PR review required
- **Merges from**: Feature branches
- **When to use**: Active development, feature integration
- **Auto-actions**: Run pre-commit, unit tests, build Docker images

### `feature/*` (Feature Development)

- **Not protected**: Can be force-pushed
- **Merges to**: `dev` only
- **When to use**: Individual feature development
- **Naming**: `feature/my-feature`, `fix/bug-name`, `hotfix/urgent-issue`

## Development Workflow

### 1. Start a New Feature

```bash
# Ensure dev is up to date
git checkout dev
git pull origin dev

# Create feature branch
git checkout -b feature/my-awesome-feature

# Work on feature
echo "new code" >> src/file.py
git add .
git commit -m "feat: add awesome feature"

# Pre-commit hooks run automatically
# Fix any issues reported

# Push branch
git push origin feature/my-awesome-feature
```

### 2. Create Pull Request

On GitHub:
- Base: `dev`
- Head: `feature/my-awesome-feature`
- Add description of changes
- Assign reviewers

Automated checks run:
- ✓ Pre-commit hooks
- ✓ Python unit tests
- ✓ Docker image builds

### 3. Code Review & Merge

- Reviewer approves changes
- Merge to `dev`
- GitHub deletes feature branch

### 4. Prepare Release (Staging)

When dev is stable enough for release:

```bash
git checkout dev
git pull origin dev
git checkout -b release/prepare-release
git push origin release/prepare-release
```

Create PR: `release/prepare-release` → `staging`

Automated actions on `staging`:
- ✓ Pre-commit hooks
- ✓ Unit tests
- ✓ Build Docker images
- ✓ Run full E2E tests
- ✓ Auto-generate release notes
- ✓ Auto-assign version (semantic versioning)

If all pass: Merge to `staging`

### 5. Release to Production (main)

Create PR: `staging` → `main`

Automated actions on `main`:
- ✓ Create GitHub Release
- ✓ Tag with version
- ✓ Push Docker images to registry

After merge:
- GitHub Release created automatically
- Version tagged: `v1.2.3`
- Docker images available for download

## Commit Message Format

Follow conventional commits for auto-versioning:

```
type(scope): description

body (optional)

footer (optional)
```

### Types

- `feat`: New feature (MINOR version bump)
- `fix`: Bug fix (PATCH version bump)
- `feat!`: Breaking change (MAJOR version bump)
- `docs`: Documentation changes
- `style`: Code style changes (no logic change)
- `refactor`: Code refactoring
- `test`: Test additions/changes
- `chore`: Build, CI, dependencies

### Examples

```bash
# Feature (bumps MINOR)
git commit -m "feat: add order cancellation support"

# Bug fix (bumps PATCH)
git commit -m "fix: correct latency calculation"

# Breaking change (bumps MAJOR)
git commit -m "feat!: change gRPC API port from 50051 to 50052"

# With scope
git commit -m "feat(matching): add iceberg order support"

# With body
git commit -m "fix(engine): fix memory leak in order pool

The order pool was not returning memory to OS when orders were cancelled.
Now using proper cleanup on deallocation."
```

## Pre-commit Hooks

### Automatic Fixes

These hooks automatically fix issues:
- End-of-file fixer
- Trailing whitespace
- Python formatting (black)
- Python linting (ruff) with `--fix`

### Requires Fix

These hooks require manual fixes:
- YAML validation
- Secrets detection
- Shell script linting
- Markdown linting

### Run Manually

```bash
# Check all files
pre-commit run --all-files

# Check specific file
pre-commit run --files src/myfile.py

# Run specific hook
pre-commit run black
```

## Testing

### Python Tests (Local, Fast)

```bash
# From ml-trading-app-py
pytest tests/test_grpc_integration.py -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html
```

### C++ Tests (Local, Fast)

```bash
# From ml-trading-app-cpp
cd build
ctest --output-on-failure
```

### Full Stack E2E Tests (Docker, Slower)

```bash
# Start all services
docker-compose up -d

# Wait for health checks
docker-compose ps

# Run E2E tests
pytest tests/test_e2e_full_stack.py -v -s

# View logs
docker-compose logs -f hft-engine
docker-compose logs -f hft-backend

# Stop services
docker-compose down
```

## Troubleshooting

### Pre-commit Fails on Commit

```bash
# See what failed
pre-commit run --all-files

# Fix issues
black .
ruff check . --fix

# Try commit again
git commit -m "feat: my feature"
```

### Can't Merge to `dev`

- Check PR status checks (green checkmarks)
- View GitHub Actions logs for details
- Fix failing tests/linting in feature branch
- Push fixes
- PR automatically updates

### Can't Merge to `staging`

- E2E tests failed - check `docker-compose logs`
- Pre-commit failed - fix and push
- Wait for E2E tests to complete
- PR will auto-update when checks pass

### Docker Images Won't Build

```bash
# Check what's wrong
docker build -f Dockerfile.prod -t test:latest .

# Common issues:
# - Base image not found
# - Dependency not installed
# - Syntax error in Dockerfile
```

## Release Notes Format

Auto-generated from commits:

```markdown
## Version 1.2.3 (2024-12-13)

### Features
- Add concurrent order support
- Implement portfolio tracking
- Add risk limit enforcement

### Bug Fixes
- Fix order cancellation race condition
- Improve latency measurement accuracy
- Handle network timeouts gracefully

### Internal
- Update dependencies
- Refactor logging system
- Clean up error handling
```

## Protected Branches

### `main`
- Required reviewers: 1
- Required status checks: All
- Dismiss stale reviews: On update
- Require branches up to date: Yes
- Allow force push: No
- Allow deletions: No

### `staging`
- Required reviewers: 1
- Required status checks: All (including E2E)
- Dismiss stale reviews: On update
- Require branches up to date: Yes
- Allow force push: No
- Allow deletions: No

### `dev`
- Required reviewers: 1
- Required status checks: All
- Dismiss stale reviews: On update
- Require branches up to date: Yes
- Allow force push: No
- Allow deletions: No

## CI/CD Pipeline Status

View automated checks:
1. Click on PR
2. Look for "Checks" tab
3. See status of each check:
   - Pre-commit hooks
   - Python tests
   - Docker builds
   - E2E tests (if on staging)

## Deployment Flow

```
feature branch
    ↓ (PR review + merge)
dev branch
    ↓ (All checks pass)
release/prepare-release
    ↓ (PR review + E2E tests pass)
staging branch
    ↓ (Manual PR to main)
main branch
    ↓ (Auto-actions)
GitHub Release
Docker Hub images
```

## FAQ

**Q: How do I update my feature branch with latest dev changes?**

```bash
git fetch origin
git rebase origin/dev
git push origin feature/my-feature --force-with-lease
```

**Q: Can I merge to main directly?**

No, main is protected. Only merges from `staging` are allowed.

**Q: How do I skip pre-commit hooks?**

Don't. They're there to prevent issues. Fix what they report instead.

**Q: How often are versions auto-bumped?**

Only when merging to `staging`. The version is determined by commit messages since the last release.

**Q: Can I have multiple releases per day?**

Yes. Each merge to `staging` → `main` creates a new release with a new version number.

---

**Last Updated**: December 13, 2024
**Version**: 1.0.0
