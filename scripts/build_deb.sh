#!/usr/bin/env bash
# Formicx Debian Package Build Script
set -e

echo "=== Building Formicx Debian Package ==="
dpkg-buildpackage -us -uc -b

echo "=== Debian package build complete ==="
ls -lh ../formicx_*.deb
