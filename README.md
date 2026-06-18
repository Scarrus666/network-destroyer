# Network Scanner & Stress Tester

A macOS network discovery and stress testing tool with a native GUI. Discover devices across multiple networks and perform ICMP flood attacks for network testing purposes.

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![Platform](https://img.shields.io/badge/Platform-macOS-lightgrey.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

## ⚠️ Legal Disclaimer

**This tool is for educational and authorized testing purposes only.**

- Only use on networks and devices you **own** or have **explicit written permission** to test
- Unauthorized network attacks are **illegal** in most jurisdictions
- The developer assumes **no liability** for misuse or damages
- Using this tool against networks/devices without permission may result in criminal charges

## Features

- 🔍 **Multi-Network Discovery** - Automatically detects all accessible networks
- 🎯 **Selective Targeting** - Attack specific devices, entire networks, or everything
- 🏠 **Multiple Scan Profiles** - Smart, Home, Business, and Full network scans
- 🔐 **Automatic Privilege Escalation** - Prompts for admin password on launch
- 🎨 **Native macOS GUI** - Dark-themed interface with real-time logging
- 📊 **Visual Network Tree** - See all discovered networks and devices
- ⚡ **Multi-threaded** - Fast scanning with 50 concurrent workers
- 🛑 **Instant Stop** - Kill all attacks with one click

## Requirements

- **macOS** (tested on macOS 15 Sequoia & macOS 12 Monterey)
- **Python 3.8+** with Tkinter support
- **Administrator privileges** (required for ICMP flood)

### Installing Python with Tkinter

```bash
# Install Python via Homebrew
brew install python@3.14

# Install Tkinter support
brew install python-tk@3.14
```

## Installation

### Option 1: Run from Source

```bash
# Clone the repository
git clone https://github.com/Scarrus666/network-destroyer.git
cd network-scanner

# Run with sudo (required for full functionality)
sudo python3 netdestroy.py
```

### Option 2: Build macOS App

```bash
# Install PyInstaller
pip3 install pyinstaller

# Build the app
pyinstaller --onedir --windowed --name "NetworkScanner" netdestroy.py

# Move to Applications folder
sudo cp -r dist/NetworkScanner.app /Applications/
```

Now you can launch it from your Applications folder or Dock!

### Option 3: Create DMG Installer

```bash
# Build the app first (see above)
pyinstaller --onedir --windowed --name "NetworkScanner" netdestroy.py

# Create a folder for DMG
mkdir -p dist/dmg
cp -r dist/NetworkScanner.app dist/dmg/

# Create a symlink to Applications folder
ln -s /Applications dist/dmg/Applications

# Create DMG
hdiutil create -volname "NetworkScanner" \
  -srcfolder dist/dmg \
  -ov -format UDZO \
  dist/NetworkScanner.dmg
```

## Usage

### 1. Launch the App
- Double-click `NetworkScanner.app` in Applications
- Enter your admin password when prompted

### 2. Discover Networks
Choose a scan profile:
- **🔍 Smart Scan** - Direct interfaces + 7 most common gateways (fastest)
- **🏠 Home** - 30+ common home router ranges
- **🏢 Business** - 25+ business/enterprise ranges  
- **🌍 Full Scan** - 70+ network ranges (most thorough, slowest)

### 3. Select Targets
- Click individual devices to select them (Cmd+Click for multiple)
- Select an entire network to target all devices on it
- Or click "Attack ALL" to target everything

### 4. Attack
- **Attack ALL** - Flood every discovered device
- **Attack Selected** - Only flood devices you've selected
- **Attack Network** - Flood all devices on the selected network

### 5. Stop
- Click "Stop All Attacks" to immediately terminate all floods
- Attacks continue running until stopped

## Scan Profiles

| Profile | Networks | Speed | Use Case |
|---------|----------|-------|----------|
| Smart Scan | ~7 | ⚡ Fast | Most situations, finds directly connected + common gateways |
| Home | ~30 | 🏃 Medium | Home networks with less common router configurations |
| Business | ~25 | 🏃 Medium | Office/enterprise environments |
| Full Scan | ~70 | 🐢 Slow | Unknown networks, maximum discovery |

### Smart Scan Gateway List
```
192.168.0.1, 192.168.1.1, 192.168.2.1, 192.168.10.1,
192.168.100.1, 10.0.0.1, 10.0.1.1
```

### Home Scan Additional Gateways
Adds: `192.168.3.1` through `192.168.254.1`, `10.0.10.1`, `172.20.10.1`, and more

### Business Scan Gateways
Covers common enterprise ranges: `10.x.x.x`, `172.16.x.x`, `172.31.x.x` (AWS)

## How It Works

### Network Discovery Phase
1. Checks directly connected interfaces via `ipconfig`
2. Pings gateway addresses based on selected profile
3. Builds list of all accessible networks

### Device Scanning Phase
1. Scans all IPs (1-254) on each discovered network
2. Uses 3 ping attempts per IP for reliability
3. 50 concurrent threads for speed
4. Results displayed in real-time tree view

### Attack Phase
1. Launches ICMP flood (`ping -f`) on selected targets
2. Requires root privileges for flood mode
3. Falls back to rapid ping (`ping -i 0.1`) for non-root
4. All attacks run concurrently

## Troubleshooting

### App asks for password but doesn't launch
- Ensure Python has Tkinter support: `python3 -c "import tkinter"`
- Check console for errors: run from terminal first

### No networks found
- Try a different scan profile (Home or Full)
- Ensure you're connected to a network
- Check firewall settings

### Attacks stop immediately
- Run as root/admin (required for ICMP flood)
- Some devices may have ICMP flood protection

### "ModuleNotFoundError: No module named '_tkinter'"
```bash
brew install python-tk@3.14
```

## Compilation Issues

### "externally-managed-environment" error
```bash
# Use a virtual environment
python3 -m venv venv
source venv/bin/activate
pip install pyinstaller
pyinstaller --onedir --windowed --name "NetworkScanner" netdestroy.py
```

### PyInstaller deprecation warning
macOS apps must use `--onedir` mode (`.app` bundles), not `--onefile`. This is a macOS security requirement.

## Technical Details

- **Language**: Python 3
- **GUI Framework**: Tkinter (ttk)
- **Attack Method**: ICMP Flood (`ping -f`)
- **Concurrency**: ThreadPoolExecutor (50 workers)
- **Privilege Escalation**: AppleScript (`osascript`)
- **Build Tool**: PyInstaller
- **Minimum macOS**: 10.14 (Mojave)

## Project Structure

```
network-scanner/
├── netdestroy.py          # Main application
├── README.md             # This file
├── requirements.txt      # Python dependencies
└── build/                # Build artifacts (gitignored)
    └── dist/
        └── NetworkScanner.app
```

## Dependencies

All dependencies are from Python standard library except:
- **PyInstaller** (build only) - For creating macOS .app bundle

No external Python packages required at runtime!

## Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Submit a pull request

## Roadmap

- [ ] ARP scanning for better device discovery
- [ ] MAC address vendor lookup
- [ ] Device hostname resolution
- [ ] Custom network range input
- [ ] Export scan results
- [ ] Attack intensity control
- [ ] Multiple attack methods (UDP, TCP SYN)

## License

MIT License - See LICENSE file for details

## Author

[Your Name]

## Acknowledgments

- Inspired by network administration tools
- Built for educational purposes
- macOS privilege escalation via AppleScript

---

**Remember**: With great power comes great responsibility. Only test networks you own! 🛡️