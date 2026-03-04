# Scripts

Automated scripts for AiFood project management.

## Version Management

### bump-version.sh

Автоматическое обновление версии проекта (Semantic Versioning).

**Usage:**
```bash
# Bug fix (1.1.0 → 1.1.1)
./scripts/bump-version.sh patch

# New feature (1.1.0 → 1.2.0)
./scripts/bump-version.sh minor

# Breaking change (1.1.0 → 2.0.0)
./scripts/bump-version.sh major
```

**What it does:**
1. Updates `VERSION` file
2. Updates all `package.json` files
3. Creates git commit
4. Creates annotated git tag (`v1.2.0`)
5. Prompts you to update `CHANGELOG.md`

**After running:**
```bash
# 1. Edit CHANGELOG.md with actual changes
vim CHANGELOG.md

# 2. Review changes
git show

# 3. Push to remote
git push origin main --tags

# 4. Create GitHub release (optional)
gh release create v1.2.0 --generate-notes
```

## Other Scripts

More scripts will be added here for:
- Deployment automation
- Database migrations
- Testing and CI/CD
- Production health checks

## See Also

- [VERSIONING.md](../VERSIONING.md) - Complete versioning guide
- [CHANGELOG.md](../CHANGELOG.md) - Version history
- [DEPLOYMENT_STATUS.md](../DEPLOYMENT_STATUS.md) - Production status
