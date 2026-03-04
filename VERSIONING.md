# Versioning Guide

AiFood follows [Semantic Versioning](https://semver.org/) (semver): `MAJOR.MINOR.PATCH`

## Current Version

**v1.1.0** (2026-03-04)

See [VERSION](VERSION) file or [CHANGELOG.md](CHANGELOG.md) for details.

## Version Format

```
MAJOR.MINOR.PATCH
  │     │     │
  │     │     └─── Bug fixes (backwards compatible)
  │     └───────── New features (backwards compatible)
  └─────────────── Breaking changes (NOT backwards compatible)
```

### Examples

- `1.0.0` → `1.0.1`: Bug fix (patch)
- `1.0.0` → `1.1.0`: New feature (minor)
- `1.0.0` → `2.0.0`: Breaking change (major)

## Release Process

### Automated (Recommended)

Use the bump-version script:

```bash
# Patch release (bug fixes)
./scripts/bump-version.sh patch

# Minor release (new features)
./scripts/bump-version.sh minor

# Major release (breaking changes)
./scripts/bump-version.sh major
```

The script will:
1. Update `VERSION` file
2. Update all `package.json` files
3. Create git commit
4. Create annotated git tag
5. Prompt you to update `CHANGELOG.md`

### Manual Process

If you prefer manual control:

```bash
# 1. Update VERSION file
echo "1.2.0" > VERSION

# 2. Update package.json files
sed -i '' 's/"version": "1.1.0"/"version": "1.2.0"/' aifood-plugin/package.json
sed -i '' 's/"version": "1.1.0"/"version": "1.2.0"/' services/llm-gateway/package.json

# 3. Update CHANGELOG.md
# Add new section with changes

# 4. Commit changes
git add VERSION CHANGELOG.md aifood-plugin/package.json services/llm-gateway/package.json
git commit -m "chore: Release v1.2.0"

# 5. Create annotated tag
git tag -a v1.2.0 -m "Release v1.2.0"

# 6. Push to remote
git push origin main --tags
```

## CHANGELOG Format

Follow [Keep a Changelog](https://keepachangelog.com/) format:

```markdown
## [1.2.0] - 2026-03-15

### Added
- New feature A
- New feature B

### Changed
- Improved existing feature C

### Fixed
- Bug fix D
- Security fix E

### Removed
- Deprecated feature F
```

### Categories

- **Added**: New features
- **Changed**: Changes to existing functionality
- **Deprecated**: Soon-to-be removed features
- **Removed**: Removed features
- **Fixed**: Bug fixes
- **Security**: Security fixes

## Version Locations

Version numbers are maintained in:

1. **VERSION** - Single source of truth
2. **aifood-plugin/package.json** - Plugin version
3. **services/llm-gateway/package.json** - LLM Gateway version
4. **services/agent-api/package.json** - Agent API version (if exists)
5. **CHANGELOG.md** - Version history
6. **Git tags** - `v1.1.0`, `v1.2.0`, etc.

## Git Tags

### List all versions

```bash
git tag -l "v*"
```

### View tag details

```bash
git show v1.1.0
```

### Checkout specific version

```bash
git checkout v1.1.0
```

## GitHub Releases

After tagging, create a GitHub release:

```bash
# Using GitHub CLI
gh release create v1.1.0 --generate-notes

# Or manually at:
# https://github.com/San2k/aifood/releases/new
```

## Version History

| Version | Date | Description |
|---------|------|-------------|
| [1.1.0](https://github.com/San2k/aifood/releases/tag/v1.1.0) | 2026-03-04 | Production deployment, 7 tools, LLM Gateway |
| [1.0.0](https://github.com/San2k/aifood/releases/tag/v1.0.0) | 2026-03-02 | OpenClaw plugin architecture, FatSecret integration |
| 0.2.0 | 2026-02-28 | Photo recognition (archived) |
| 0.1.0 | 2026-02-20 | Initial MVP (archived) |

## Pre-release Versions

For beta/alpha releases, use:

```
1.2.0-beta.1
1.2.0-alpha.3
1.2.0-rc.1
```

Tag as:
```bash
git tag -a v1.2.0-beta.1 -m "Beta release 1.2.0-beta.1"
```

## Hotfix Process

For urgent production fixes:

```bash
# Create hotfix from tag
git checkout -b hotfix/1.1.1 v1.1.0

# Make fixes
git commit -m "fix: Critical bug fix"

# Update version to 1.1.1
./scripts/bump-version.sh patch

# Merge back to main
git checkout main
git merge hotfix/1.1.1

# Push
git push origin main --tags
```

## Deprecation Policy

When deprecating features:

1. Mark as deprecated in CHANGELOG
2. Add deprecation warnings in code
3. Keep for at least one MINOR version
4. Remove in next MAJOR version

Example:
- v1.1.0: Feature X deprecated
- v1.2.0: Feature X still available (with warnings)
- v2.0.0: Feature X removed

## Best Practices

1. **Always update CHANGELOG** before releasing
2. **Test thoroughly** before tagging
3. **Use annotated tags** (`git tag -a`) not lightweight tags
4. **Include migration guides** for breaking changes
5. **Document API changes** in release notes
6. **Sync versions** across all package.json files
7. **Tag after commit**, not before

## Related Files

- [VERSION](VERSION) - Current version number
- [CHANGELOG.md](CHANGELOG.md) - Full version history
- [scripts/bump-version.sh](scripts/bump-version.sh) - Automated version bumping
- [DEPLOYMENT_STATUS.md](DEPLOYMENT_STATUS.md) - Deployment information

## Questions?

- Check [Semantic Versioning](https://semver.org/)
- See [Keep a Changelog](https://keepachangelog.com/)
- Review existing [releases](https://github.com/San2k/aifood/releases)
