#!/bin/bash
echo "PRAXIS Data Submission Tool"
echo "============================"
DIR="$(cd "$(dirname "$0")" && pwd)"
python3 "$DIR/collector/submit.py" "$@"
