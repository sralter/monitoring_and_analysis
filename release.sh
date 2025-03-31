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

# Add git tag
git tag "$VERSION"
git push origin "$VERSION"

# Clean previous builds
rm -rf dist/ build/ *.egg-info

# Generate changelog
if command -v git-cliff &> /dev/null && [ -f .gitcliff.toml ]; then
  git-cliff -o CHANGELOG.md
else
  echo "Skipping changelog generation: git-cliff not found or config missing."
fi

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

# Confirm latest version view
echo "View at:"
if [[ $TARGET == "1" ]]; then
  echo "https://test.pypi.org/project/pymaap/"
else
  echo "https://pypi.org/project/pymaap/"
fi

echo "Release complete: $VERSION"
