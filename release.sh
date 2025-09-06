#!/bin/bash
set -e

# Script to release a new version of py-micro-plumberd
# Usage: ./release.sh <version>
# Example: ./release.sh 0.1.8

if [ -z "$1" ]; then
    echo "Usage: $0 <version>"
    echo "Example: $0 0.1.8"
    echo ""
    echo "Current tags:"
    git tag --list 'v*' --sort=-v:refname | head -5
    exit 1
fi

VERSION=$1

# Ensure working directory is clean
if [ -n "$(git status --porcelain)" ]; then
    echo "Error: Working directory is not clean. Commit or stash changes first."
    exit 1
fi

echo "Creating release v$VERSION..."

# Create and push tag
git tag -a "v$VERSION" -m "Release version $VERSION"
echo "Created tag v$VERSION"

echo ""
echo "To publish this release:"
echo "1. Push the tag: git push origin v$VERSION"
echo "2. GitHub Actions will automatically build and publish to PyPI"
echo ""
echo "To cancel this release:"
echo "  git tag -d v$VERSION"