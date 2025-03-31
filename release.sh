#!/bin/bash

set -e  # Exit on error

# Prompt for version tag (e.g., v0.1.4)
read -p "Enter new version tag (e.g., v0.1.4): " VERSION

# Confirm destination
read -p "Upload to (1) TestPyPI or (2) PyPI? [1/2]: " TARGET

if [[ -z $VERSION ]]; then
  echo "Version tag is required."
  exit 1
fi

# Clean old builds
rm -rf dist/ build/ *.egg-info

# Generate changelog
echo "Generating changelog..."
git-cliff -t "$VERSION" -o CHANGELOG.md

# Commit changelog if it changed
if ! git diff --quiet CHANGELOG.md; then
  git add CHANGELOG.md
  git commit -m "docs: update changelog for $VERSION"
fi

# Add git tag & push
git tag "$VERSION"
git push origin "$VERSION"
git push  # In case changelog commit was added

# Build the package
echo "Building package..."
python -m build

# Upload
if [[ $TARGET == "1" ]]; then
  echo "Uploading to TestPyPI..."
  python -m twine upload --repository testpypi dist/*
else
  echo "Uploading to PyPI..."
  python -m twine upload dist/*
fi

# Create GitHub release (requires GitHub CLI)
if command -v gh &> /dev/null; then
  echo "Creating GitHub release..."
  gh release create "$VERSION" --notes-file CHANGELOG.md
else
  echo "GitHub CLI (gh) not found. Skipping GitHub release creation."
fi

echo "Release complete: $VERSION"