#!/usr/bin/env bash

# Cross-platform launcher script
# Automatically detects OS and runs the appropriate launcher

echo "===================================================="
echo "   SOCIAL MEDIA SCRAPER - CROSS-PLATFORM LAUNCHER"
echo "===================================================="
echo

# Detect operating system
OS="$(uname -s)"
case "${OS}" in
    Darwin*)
        echo "[INFO] macOS detected"
        SCRIPT="./launcher.sh"
        ;;
    Linux*)
        echo "[INFO] Linux detected"
        SCRIPT="./launcher.sh"
        ;;
    CYGWIN*|MINGW32*|MSYS*|MINGW*)
        echo "[INFO] Windows detected (running in Unix-like environment)"
        SCRIPT="./launcher.sh"
        ;;
    *)
        echo "[WARNING] Unknown OS: ${OS}"
        echo "[INFO] Attempting to use Unix-style launcher"
        SCRIPT="./launcher.sh"
        ;;
esac

# Check if script exists and is executable
if [[ ! -f "$SCRIPT" ]]; then
    echo "[ERROR] Launcher script not found: $SCRIPT"
    echo "[INFO] Make sure all launcher files are present"
    exit 1
fi

if [[ ! -x "$SCRIPT" ]]; then
    echo "[INFO] Making launcher script executable..."
    chmod +x "$SCRIPT"
fi

echo "[INFO] Running launcher: $SCRIPT"
echo

# Execute the appropriate launcher
exec "$SCRIPT"