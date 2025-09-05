#!/usr/bin/env bash

# Script to deactivate Python virtual environment on Mac/Linux
# This is equivalent to venv\Scripts\deactivate.bat on Windows

# Check if we're in a virtual environment
if [[ -z "$VIRTUAL_ENV" ]]; then
    echo "[INFO] No virtual environment is currently active"
    exit 0
fi

echo "[INFO] Deactivating virtual environment: $(basename $VIRTUAL_ENV)"

# The deactivate function should be available when venv is active
if command -v deactivate >/dev/null 2>&1; then
    deactivate
    echo "[OK] Virtual environment deactivated"
else
    echo "[WARNING] deactivate function not found"
    echo "[INFO] You may need to close this terminal session"
fi

# FOR MAC