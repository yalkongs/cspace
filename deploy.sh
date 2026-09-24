#!/bin/bash
# Build and publish generated files to the public GitHub Pages branch.
set -euo pipefail
cd "$(dirname "$0")"
python3 -B -m unittest discover -s build -p 'test_*.py'
node build/test-color-math.cjs
python3 -B build/build.py
if [[ "${1:-}" == "--build-only" ]]; then
  exit 0
fi
python3 -B build/publish.py
