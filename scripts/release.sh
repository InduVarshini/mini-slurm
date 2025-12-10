#!/bin/bash
# Release script for mini-slurm
# Usage: ./scripts/release.sh [test|prod]

set -e

REPO_TYPE=${1:-test}

if [ "$REPO_TYPE" != "test" ] && [ "$REPO_TYPE" != "prod" ]; then
    echo "Usage: $0 [test|prod]"
    echo "  test: Upload to TestPyPI (default)"
    echo "  prod: Upload to PyPI"
    exit 1
fi

echo "=========================================="
echo "mini-slurm Release Script"
echo "=========================================="
echo ""

# Check if build tools are installed
if ! command -v python &> /dev/null; then
    echo "Error: python not found"
    exit 1
fi

echo "Step 1: Checking build tools..."
python -m pip install --quiet --upgrade build twine
echo "✓ Build tools ready"
echo ""

# Clean previous builds
echo "Step 2: Cleaning previous builds..."
rm -rf dist/ build/ *.egg-info src/*.egg-info
echo "✓ Cleaned"
echo ""

# Build packages
echo "Step 3: Building distribution packages..."
python -m build
echo "✓ Build complete"
echo ""

# Check if dist files exist
if [ ! -d "dist" ] || [ -z "$(ls -A dist)" ]; then
    echo "Error: No distribution files found in dist/"
    exit 1
fi

echo "Distribution files:"
ls -lh dist/
echo ""

# Upload
if [ "$REPO_TYPE" == "test" ]; then
    echo "Step 4: Uploading to TestPyPI..."
    echo "Repository: https://test.pypi.org/"
    echo ""
    echo "When prompted:"
    echo "  Username: __token__"
    echo "  Password: <your-testpypi-api-token>"
    echo ""
    read -p "Press Enter to continue..."
    python -m twine upload --repository testpypi dist/*
    echo ""
    echo "✓ Uploaded to TestPyPI"
    echo ""
    echo "To test installation:"
    echo "  pip install --index-url https://test.pypi.org/simple/ mini-slurm"
else
    echo "Step 4: Uploading to PyPI..."
    echo "Repository: https://pypi.org/"
    echo ""
    echo "⚠️  WARNING: This will upload to the PRODUCTION PyPI repository!"
    echo ""
    echo "When prompted:"
    echo "  Username: __token__"
    echo "  Password: <your-pypi-api-token>"
    echo ""
    read -p "Press Enter to continue (Ctrl+C to cancel)..."
    python -m twine upload dist/*
    echo ""
    echo "✓ Uploaded to PyPI"
    echo ""
    echo "Package URL: https://pypi.org/project/mini-slurm/"
fi

echo ""
echo "=========================================="
echo "Release complete!"
echo "=========================================="
