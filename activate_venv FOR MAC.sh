#!/usr/bin/env bash

# Script to activate Python virtual environment on Mac/Linux
# This is equivalent to venv\Scripts\activate.bat on Windows

# Set the virtual environment path
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VIRTUAL_ENV="${SCRIPT_DIR}/venv"

# Check if virtual environment exists
if [[ ! -d "$VIRTUAL_ENV" ]]; then
    echo "[ERROR] Virtual environment not found at: $VIRTUAL_ENV"
    echo "[INFO] Run launcher.sh first to create the virtual environment"
    exit 1
fi

# Check if activation script exists
if [[ ! -f "$VIRTUAL_ENV/bin/activate" ]]; then
    echo "[ERROR] Virtual environment activation script not found"
    echo "[INFO] Virtual environment may be corrupted. Re-run launcher.sh"
    exit 1
fi

# Activate the virtual environment
echo "[INFO] Activating virtual environment..."
source "$VIRTUAL_ENV/bin/activate"

if [[ "$VIRTUAL_ENV" != "" ]]; then
    echo "[OK] Virtual environment activated: $(basename $VIRTUAL_ENV)"
    echo "[INFO] Python path: $(which python)"
    echo "[INFO] Python version: $(python --version)"
    echo
    echo "To deactivate the virtual environment, run: deactivate"
    echo "Or run: source deactivate_venv.sh"
else
    echo "[ERROR] Failed to activate virtual environment"
    exit 1
fi

# FOR MAC