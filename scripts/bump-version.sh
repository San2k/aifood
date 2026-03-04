#!/bin/bash

# AiFood Version Bump Script
# Usage: ./scripts/bump-version.sh [major|minor|patch]

set -e

VERSION_FILE="VERSION"
CHANGELOG="CHANGELOG.md"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get current version
CURRENT_VERSION=$(cat $VERSION_FILE | tr -d '\n')
echo -e "${YELLOW}Current version: $CURRENT_VERSION${NC}"

# Parse version
IFS='.' read -r -a version_parts <<< "$CURRENT_VERSION"
MAJOR="${version_parts[0]}"
MINOR="${version_parts[1]}"
PATCH="${version_parts[2]}"

# Determine bump type
BUMP_TYPE=${1:-patch}

case $BUMP_TYPE in
  major)
    MAJOR=$((MAJOR + 1))
    MINOR=0
    PATCH=0
    ;;
  minor)
    MINOR=$((MINOR + 1))
    PATCH=0
    ;;
  patch)
    PATCH=$((PATCH + 1))
    ;;
  *)
    echo -e "${RED}Invalid bump type: $BUMP_TYPE${NC}"
    echo "Usage: $0 [major|minor|patch]"
    exit 1
    ;;
esac

NEW_VERSION="$MAJOR.$MINOR.$PATCH"
echo -e "${GREEN}New version: $NEW_VERSION${NC}"

# Ask for confirmation
read -p "Bump version to $NEW_VERSION? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${RED}Aborted${NC}"
    exit 1
fi

# Update VERSION file
echo $NEW_VERSION > $VERSION_FILE
echo -e "${GREEN}✓ Updated VERSION file${NC}"

# Update package.json files
echo "Updating package.json files..."

# AiFood Plugin
if [ -f "aifood-plugin/package.json" ]; then
    sed -i '' "s/\"version\": \".*\"/\"version\": \"$NEW_VERSION\"/" aifood-plugin/package.json
    echo -e "${GREEN}✓ Updated aifood-plugin/package.json${NC}"
fi

# LLM Gateway
if [ -f "services/llm-gateway/package.json" ]; then
    sed -i '' "s/\"version\": \".*\"/\"version\": \"$NEW_VERSION\"/" services/llm-gateway/package.json
    echo -e "${GREEN}✓ Updated services/llm-gateway/package.json${NC}"
fi

# Agent API
if [ -f "services/agent-api/package.json" ]; then
    sed -i '' "s/\"version\": \".*\"/\"version\": \"$NEW_VERSION\"/" services/agent-api/package.json
    echo -e "${GREEN}✓ Updated services/agent-api/package.json${NC}"
fi

# Update CHANGELOG.md header
DATE=$(date +%Y-%m-%d)
CHANGELOG_HEADER="## [Unreleased]

### Added
-

### Changed
-

### Fixed
-

## [$NEW_VERSION] - $DATE"

# Insert new section after "## [Unreleased]" or before first version
if grep -q "## \[Unreleased\]" $CHANGELOG; then
    # Replace existing Unreleased section
    sed -i '' "/## \[Unreleased\]/,/## \[.*\]/{ /## \[Unreleased\]/!{ /## \[.*\]/!d; }; }" $CHANGELOG
fi

# Prepare for manual CHANGELOG edit
echo -e "${YELLOW}Please update CHANGELOG.md with changes for v$NEW_VERSION${NC}"

# Git operations
echo -e "\n${YELLOW}Creating git commit and tag...${NC}"

# Stage changes
git add VERSION CHANGELOG.md aifood-plugin/package.json services/*/package.json

# Commit
git commit -m "chore: Bump version to $NEW_VERSION

- Updated VERSION file
- Updated package.json files
- See CHANGELOG.md for details"

# Create annotated tag
git tag -a "v$NEW_VERSION" -m "Release v$NEW_VERSION"

echo -e "\n${GREEN}✓ Version bumped to $NEW_VERSION${NC}"
echo -e "${GREEN}✓ Git commit and tag created${NC}"
echo -e "\n${YELLOW}Next steps:${NC}"
echo "1. Update CHANGELOG.md with actual changes"
echo "2. Review changes: git show"
echo "3. Push to remote: git push origin main --tags"
echo "4. Create GitHub release: gh release create v$NEW_VERSION --generate-notes"
