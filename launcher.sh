#!/usr/bin/env bash

# Enable strict error handling
set -euo pipefail

echo "===================================================="
echo "   SOCIAL MEDIA SCRAPER - LAUNCHER v2.0"
echo "===================================================="
echo

# Function to check if running with sudo (equivalent to admin check)
check_permissions() {
    if [[ $EUID -eq 0 ]]; then
        echo "[WARNING] Running as root (sudo)."
        echo "[INFO] This may cause permission issues with pip."
        echo "[INFO] Consider running without sudo for better security."
        echo
    fi
}

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check permissions
check_permissions

# Check if Python is installed
if ! command_exists python3; then
    echo "[ERROR] Python not found. Please install Python 3.8-3.11 from https://python.org"
    echo "[WARNING] Python 3.13 has compatibility issues, use 3.8-3.11"
    read -p "Press any key to exit..."
    exit 1
fi

# Show Python version
PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2)
echo "[INFO] Python ${PYTHON_VERSION} detected"

# Create directory structure if it doesn't exist
mkdir -p src/utils
mkdir -p src/javascript
mkdir -p scrape/tiktok
mkdir -p scrape/instagram
mkdir -p scrape/facebook

echo "[INFO] Checking directory structure... OK"
echo

# Clean pip cache to avoid permission issues
echo "[INFO] Cleaning pip cache..."
python3 -m pip cache purge >/dev/null 2>&1 || true

# Create virtual environment if it doesn't exist
if [[ ! -d "venv" ]]; then
    echo "[INFO] Creating virtual environment..."
    python3 -m venv venv --clear
    if [[ $? -ne 0 ]]; then
        echo "[ERROR] Error creating virtual environment"
        read -p "Press any key to exit..."
        exit 1
    fi
fi

# Activate virtual environment
echo "[INFO] Activating virtual environment..."
if [[ -f "venv/bin/activate" ]]; then
    source venv/bin/activate
else
    echo "[ERROR] Could not find virtual environment activation script"
    read -p "Press any key to exit..."
    exit 1
fi

# Update pip in virtual environment
echo "[INFO] Updating pip..."
python -m pip install --upgrade pip setuptools wheel --no-cache-dir

# Configure pip to prefer precompiled wheels and avoid compilation
echo "[INFO] Configuring pip to use precompiled wheels..."
export PIP_PREFER_BINARY=1
export PIP_ONLY_BINARY=:all:

# Install basic dependencies first
echo "[INFO] Installing basic dependencies..."
python -m pip install --no-cache-dir colorama==0.4.6
python -m pip install --no-cache-dir tqdm==4.66.1
python -m pip install --no-cache-dir python-dotenv==1.0.0
python -m pip install --no-cache-dir fake-useragent==1.4.0

# Install network dependencies
echo "[INFO] Installing network dependencies..."
python -m pip install --no-cache-dir requests==2.31.0
python -m pip install --no-cache-dir urllib3==2.0.7

# Install scrapfly
echo "[INFO] Installing ScrapFly SDK..."
python -m pip install --no-cache-dir scrapfly-sdk==0.8.23

# Install parsing dependencies
echo "[INFO] Installing parsing dependencies..."
python -m pip install --no-cache-dir beautifulsoup4==4.12.2

# Install openpyxl for Excel
echo "[INFO] Installing OpenPyXL for Excel..."
python -m pip install --no-cache-dir openpyxl==3.1.2

# Attempt to install lxml with better options
echo "[INFO] Installing lxml (optional)..."
# Temporarily disable the variable to allow more flexibility with lxml
unset PIP_ONLY_BINARY

# Try to install with precompiled wheels first
if ! python -m pip install --no-cache-dir --prefer-binary lxml >/dev/null 2>&1; then
    echo "[INFO] Trying stable version of lxml..."
    if ! python -m pip install --no-cache-dir --prefer-binary lxml==4.9.2 >/dev/null 2>&1; then
        echo "[INFO] Trying more compatible version of lxml..."
        if ! python -m pip install --no-cache-dir --prefer-binary lxml==4.8.0 >/dev/null 2>&1; then
            echo "[INFO] Last attempt with very stable version..."
            if ! python -m pip install --no-cache-dir lxml==4.6.5 >/dev/null 2>&1; then
                echo "[WARNING] lxml could not be installed, but it's not critical."
                echo "[INFO] BeautifulSoup will work with the built-in html.parser."
            else
                echo "[OK] lxml 4.6.5 installed correctly"
            fi
        else
            echo "[OK] lxml 4.8.0 installed correctly"
        fi
    else
        echo "[OK] lxml 4.9.2 installed correctly"
    fi
else
    echo "[OK] lxml installed correctly"
fi

# Restore the configuration
export PIP_ONLY_BINARY=:all:

# Verify that critical dependencies are installed
echo "[INFO] Verifying installation..."
if python -c "import colorama, requests, openpyxl, bs4, scrapfly; print('[OK] All critical dependencies installed')" >/dev/null 2>&1; then
    : # Success, do nothing
else
    echo "[ERROR] Some critical dependencies are missing"
    echo "[INFO] Attempting to repair..."
    
    # Try to install essentials without specific versions
    python -m pip install colorama requests openpyxl beautifulsoup4 scrapfly-sdk tqdm python-dotenv fake-useragent --no-cache-dir --prefer-binary
    
    # Verify again
    if python -c "import colorama, requests, openpyxl, bs4, scrapfly; print('[OK] Repair successful')" >/dev/null 2>&1; then
        : # Success, do nothing
    else
        echo "[ERROR] Could not install all critical dependencies"
        echo "[INFO] Try running with sudo if permission issues persist"
        echo "[INFO] Or install build tools if the problem continues"
        read -p "Press any key to exit..."
        exit 1
    fi
fi

# Verify available parsers for BeautifulSoup
echo "[INFO] Verifying BeautifulSoup parsers..."
if python -c "from bs4 import BeautifulSoup; BeautifulSoup('<test></test>', 'html.parser'); print('[OK] html.parser available')" >/dev/null 2>&1; then
    : # Success, do nothing
fi

# Try to verify lxml parser (optional)
if python -c "from bs4 import BeautifulSoup; BeautifulSoup('<test></test>', 'lxml'); print('[OK] lxml parser available')" >/dev/null 2>&1; then
    : # Success, do nothing
else
    echo "[INFO] lxml parser not available (will use html.parser as fallback)"
fi

echo
echo "[INFO] Starting Social Media Scraper..."
echo

# Verify that the main file exists
if [[ ! -f "src/main_controller.py" ]]; then
    echo "[ERROR] File src/main_controller.py not found"
    echo "[INFO] Make sure all project files are present"
    read -p "Press any key to exit..."
    exit 1
fi

# Execute the main controller
python src/main_controller.py

if [[ $? -ne 0 ]]; then
    echo
    echo "[ERROR] Error executing the scraper"
    echo "[INFO] Check the logs above for more details"
    read -p "Press any key to continue..."
else
    echo
    echo "[SUCCESS] Scraper executed correctly"
fi

echo
echo "[INFO] Process completed. Press any key to exit."
read -p ""