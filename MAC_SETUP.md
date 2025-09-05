# Mac Setup Instructions

This project now supports both Windows and Mac operating systems. Below are the instructions for running the Social Media Scraper on Mac.

## Prerequisites

1. **Python 3.8-3.11**: Install from [python.org](https://python.org)
   - **Note**: Python 3.13 has compatibility issues, use versions 3.8-3.11
   - On Mac, you can also use Homebrew: `brew install python@3.11`

2. **Terminal**: Use the built-in Terminal app or any terminal emulator

## Quick Start

### Option 1: Full Setup and Launch (Recommended)
```bash
./launcher.sh
```
This script will:
- Check Python installation
- Create virtual environment
- Install all dependencies
- Launch the scraper

### Option 2: Manual Virtual Environment Management
```bash
# Activate virtual environment
./activate_venv.sh

# Run the scraper manually
python src/main_controller.py

# Deactivate when done
./deactivate_venv.sh
```

## File Equivalents

| Windows File | Mac File | Purpose |
|-------------|----------|---------|
| `launcher.bat` | `launcher.sh` | Main setup and launch script |
| `venv\Scripts\activate.bat` | `activate_venv.sh` | Activate virtual environment |
| `venv\Scripts\deactivate.bat` | `deactivate_venv.sh` | Deactivate virtual environment |

## Troubleshooting

### Permission Issues
If you get permission errors:
```bash
chmod +x *.sh
```

### Python Not Found
Make sure Python 3 is installed and accessible:
```bash
python3 --version
```

If `python3` is not found, you may need to install it or create a symlink.

### Virtual Environment Issues
If the virtual environment gets corrupted:
```bash
rm -rf venv
./launcher.sh
```

### Dependencies Installation Issues
The launcher script will try multiple versions of problematic packages (like lxml). If issues persist:

1. Make sure you have Xcode Command Line Tools:
   ```bash
   xcode-select --install
   ```

2. For M1/M2 Macs, some packages may need Rosetta or native ARM builds.

## Differences from Windows Version

1. **Shebang**: Scripts use `#!/usr/bin/env bash` for portability
2. **Path separators**: Use `/` instead of `\`
3. **Virtual environment structure**: `venv/bin/` instead of `venv\Scripts\`
4. **Error handling**: Uses bash `set -euo pipefail` for strict error handling
5. **Command availability**: Uses `command -v` instead of Windows-specific checks

## Security Notes

- The scripts avoid running with sudo/root privileges when possible
- Virtual environment is used to isolate dependencies
- No hardcoded absolute paths (portable across different Mac users)

## Compatibility

- **macOS Version**: Works on macOS 10.14+ (Mojave and later)
- **Processor**: Compatible with both Intel and Apple Silicon (M1/M2) Macs
- **Shell**: Compatible with bash and zsh (default macOS shells)