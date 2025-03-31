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

# Clean old builds
rm -rf dist/ build/ *.egg-info

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

echo "Release complete: $VERSION"
