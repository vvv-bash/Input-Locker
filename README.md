# 🔐 Input Locker

<div align="center">

![Input Locker Logo](https://img.shields.io/badge/Input-Locker-1976d2?style=for-the-badge&logo=linux&logoColor=white)

**A powerful, modern input device locker for Linux systems**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=flat-square)](https://opensource.org/licenses/MIT)
[![Platform](https://img.shields.io/badge/Platform-Linux-orange?style=flat-square&logo=linux)](https://www.linux.org/)
[![Python](https://img.shields.io/badge/Python-3.8+-blue?style=flat-square&logo=python)](https://www.python.org/)
[![Node.js](https://img.shields.io/badge/Node.js-18+-green?style=flat-square&logo=node.js)](https://nodejs.org/)
[![Electron](https://img.shields.io/badge/Electron-28+-9feaf9?style=flat-square&logo=electron)](https://www.electronjs.org/)

[Features](#-features) • [Installation](#-installation) • [Usage](#-usage) • [Use Cases](#-use-cases) • [Configuration](#%EF%B8%8F-configuration) • [API](#-api-reference) • [Contributing](#-contributing)

---

</div>

## 📋 Overview

**Input Locker** is a comprehensive solution for temporarily locking input devices (keyboard, mouse, touchpad, touchscreen) on Linux systems. Built with a modern tech stack combining Python backend with an Electron + React frontend, it provides both a beautiful GUI interface and powerful hotkey-based controls.

Whether you need to clean your keyboard, prevent accidental inputs during presentations, create a child-safe environment, or focus without distractions, Input Locker has you covered.

---

## ✨ Features

### Core Functionality
- 🔒 **Instant Lock/Unlock** - Lock all input devices with `Ctrl+Alt+L`
- 🎮 **Pattern Unlock** - Unlock with the memorable pattern `↑↑↓↓Enter`
- 👆 **Touchscreen Exclusion** - Automatically excludes touchscreens from blocking
- ⏱️ **Timer-based Locking** - Set auto-unlock timers (1-60 minutes)

### Security Profiles
| Profile | Description | Blocked Devices |
|---------|-------------|-----------------|
| 🎯 **Focus Mode** | Block all except mouse | Keyboard, Touchpad, Touchscreen |
| 👶 **Child Lock** | Complete device lockdown | All input devices |
| 🎮 **Gaming Mode** | Prevent touchpad interference | Touchpad only |
| 📊 **Presentation** | Prevent accidental typing | Keyboard only |

### User Interface
- 🌙 **Dark/Light Theme** - Automatic theme detection with manual override
- 📊 **Real-time Statistics** - Track blocked events and usage time
- 📱 **Modern UI** - Beautiful Material Design interface
- 🔔 **System Tray** - Minimize to tray for background operation
- 📜 **Activity Log** - Track all lock/unlock events

### Technical Features
- ⚡ **Low Resource Usage** - Minimal CPU and memory footprint
- 🔌 **WebSocket Support** - Real-time UI updates
- 🐧 **Native Linux Integration** - Uses evdev for direct device access
- 🔐 **Secure** - Requires root privileges only for device access

---

## 🚀 Installation

### Prerequisites

- **Operating System**: Debian 11+, Ubuntu 20.04+, Linux Mint 20+, Fedora 38+, Arch/Manjaro, or compatible
- **Python**: 3.8 or higher
- **Display Server**: X11 or Wayland

> **Wayland notes**
>
> Input Locker trabaja directamente con los dispositivos de `/dev/input/*` usando `evdev`, por lo que el bloqueo de teclado/ratón funciona tanto en X11 como en Wayland siempre que el usuario tenga permisos de lectura sobre esos dispositivos (normalmente ejecutando la aplicación como root o a través de `pkexec`). No es necesario ningún portal específico del compositor.
>
> En entornos Wayland (GNOME, KDE Plasma, etc.) lo que sí cambia es el comportamiento de algunas ventanas emergentes o notificaciones; si ves problemas visuales, comprueba los logs desde **Logs** o la nueva página de **Diagnostics**.

### Supported distros & install methods

| Distro family                          | Examples                               | Recommended install method                           |
|----------------------------------------|----------------------------------------|------------------------------------------------------|
| **Debian‑based**                       | Debian, Ubuntu, Linux Mint, Pop!_OS   | `.deb` package **or** `packaging/install.sh` script  |
| **Fedora / RHEL‑based**                | Fedora, RHEL, Rocky, AlmaLinux        | `packaging/install.sh` or manual steps in `INSTALL.md` |
| **Arch‑based**                         | Arch, Manjaro, EndeavourOS            | `packaging/install.sh` or manual steps in `INSTALL.md` |
| **Other compatible Linux distros**     | Any with Python 3.8+, Node 18+, polkit | Manual install section (adapt package manager)       |

### Method 1: Debian/Ubuntu Package (Recommended)

```bash
# Download the latest release
wget https://github.com/yourusername/input-locker/releases/latest/download/input-locker_2.0.0_amd64.deb

# Install the package
sudo dpkg -i input-locker_2.0.0_amd64.deb

# Fix any missing dependencies
sudo apt-get install -f
```

### Method 2: Quick Install Script (Debian/Ubuntu)

```bash
# Clone the repository
git clone https://github.com/yourusername/input-locker.git
cd input-locker

# Run the installer
sudo bash packaging/install.sh
```

### Method 3: Manual Installation (all distros)

<details>
<summary>Click to expand manual installation steps</summary>

```bash
# 1. Install system dependencies

# Debian / Ubuntu / Linux Mint
sudo apt update
sudo apt install -y python3 python3-venv python3-pip policykit-1

# Fedora (dnf)
sudo dnf install -y python3 python3-virtualenv python3-pip polkit

# Arch / Manjaro (pacman)
sudo pacman -S --needed python python-virtualenv python-pip polkit

# 2. Clone the repository
git clone https://github.com/yourusername/input-locker.git
sudo mv input-locker /opt/

# 3. Create Python virtual environment
cd /opt/input-locker
sudo python3 -m venv venv
sudo ./venv/bin/pip install -r requirements.txt

# 4. Set permissions
sudo chmod +x /opt/input-locker/input-locker.sh

# 5. Create symlink (optional)
sudo ln -sf /opt/input-locker/input-locker.sh /usr/bin/input-locker
```

</details>

### Method 4: Development Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/input-locker.git
cd input-locker

# Setup Python environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Setup Node.js environment
cd web-ui
npm install --legacy-peer-deps

# Run in development mode (requires root)
sudo npm run electron:dev
```

---

## 🎮 Usage

### Starting the Application

```bash
# From terminal (GUI will open)
input-locker

# Or from the application menu
# Look for "Input Locker" in Utilities/System

# Direct execution
/opt/input-locker/input-locker.sh
```

### Keyboard Shortcuts

| Action | Shortcut | Description |
|--------|----------|-------------|
| **Lock All** | `Ctrl + Alt + L` | Instantly locks all input devices (except touchscreen) |
| **Unlock** | `↑ ↑ ↓ ↓ Enter` | Pattern unlock - works even when devices are locked |

### Using the GUI

1. **Dashboard** - View device status, apply profiles, set timers
2. **Device List** - See all detected input devices and their status
3. **Quick Actions** - One-click lock/unlock buttons
4. **Timer** - Set auto-unlock duration
5. **Settings** - Configure theme, hotkeys, and behavior

### Command-Line Interface

```bash
# Lock all devices (API must be running)
curl -X POST http://127.0.0.1:8080/api/devices/block-all

# Unlock all devices
curl -X POST http://127.0.0.1:8080/api/devices/unblock-all

# Lock specific device types
curl -X POST http://127.0.0.1:8080/api/devices/lock-by-types \
  -H "Content-Type: application/json" \
  -d '{"types": ["keyboard", "touchpad"]}'

# Get device list
curl http://127.0.0.1:8080/api/devices/list

# Set timer (5 minutes)
curl -X POST http://127.0.0.1:8080/api/timer/set \
  -H "Content-Type: application/json" \
  -d '{"minutes": 5}'
```

---

## 💡 Use Cases

### 🧹 Keyboard Cleaning

**Problem**: Need to clean your keyboard without triggering random key presses.

**Solution**:
```
1. Press Ctrl+Alt+L to lock all devices
2. Clean your keyboard thoroughly
3. Press ↑↑↓↓Enter to unlock
```

### 👶 Child Safety / Toddler Mode

**Problem**: Your toddler loves pressing buttons on your computer.

**Solution**:
```
1. Open Input Locker
2. Select "Child Lock" profile
3. All inputs are now blocked
4. Use the touchscreen (if available) or pattern to unlock
```

**Pro tip**: Set a timer so you don't forget to unlock!

### 📊 Presentations

**Problem**: Accidentally pressing keys during a presentation is embarrassing.

**Solution**:
```
1. Select "Presentation" profile (blocks keyboard only)
2. Use mouse/pointer freely
3. No accidental typing on slides!
```

### 🎮 Gaming

**Problem**: Touchpad interference while gaming on a laptop.

**Solution**:
```
1. Select "Gaming Mode" profile
2. Touchpad is disabled
3. Keyboard and mouse work normally
4. No more accidental cursor movements!
```

### 🎯 Focus / Deep Work

**Problem**: Keyboard distractions while reading or thinking.

**Solution**:
```
1. Select "Focus Mode" profile
2. Only mouse remains active
3. Can't accidentally type or switch windows
4. Perfect for reading documentation or code review
```

### 🐱 Cat on Keyboard

**Problem**: Your cat loves walking across your keyboard.

**Solution**:
```
1. Quick Ctrl+Alt+L when you see the cat approaching
2. Let them enjoy the warm keyboard
3. ↑↑↓↓Enter when they're done
```

### 🔒 Security / Privacy

**Problem**: Need to step away briefly but don't want to lock the entire screen.

**Solution**:
```
1. Lock input devices with Ctrl+Alt+L
2. Screen stays visible (great for monitoring)
3. Nobody can interact with your computer
4. Return and unlock with the pattern
```

### 🏥 Kiosk / Public Terminal

**Problem**: Need to prevent keyboard access on a public display.

**Solution**:
```
1. Start Input Locker on boot
2. Apply "Focus Mode" or "Child Lock" profile
3. Only touchscreen interaction allowed (if applicable)
4. Administrators can unlock with pattern
```

### 📺 Media Center / HTPC

**Problem**: Want to control your media center only via remote/touchscreen.

**Solution**:
```
1. Lock keyboard and mouse with Input Locker
2. Use remote control or touchscreen for navigation
3. No accidental inputs from kids or pets
```

---

## ⚙️ Configuration

### Settings File

Configuration is stored in `~/.config/input-locker/settings.json`:

```json
{
  "hotkey": ["Ctrl", "Alt", "L"],
  "emergencyPattern": ["Up", "Up", "Down", "Down", "Enter"],
  "autoBlockOnStart": false,
  "showNotifications": true,
  "allowTouchscreenUnlock": true,
  "theme": "system"
}
```

### Available Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `hotkey` | array | `["Ctrl", "Alt", "L"]` | Lock hotkey combination |
| `emergencyPattern` | array | `["Up", "Up", "Down", "Down", "Enter"]` | Unlock pattern |
| `autoBlockOnStart` | boolean | `false` | Auto-lock when app starts |
| `showNotifications` | boolean | `true` | Show system notifications |
| `allowTouchscreenUnlock` | boolean | `true` | Allow touchscreen when locked |
| `theme` | string | `"system"` | `"light"`, `"dark"`, or `"system"` |

### Environment Variables

```bash
# Custom API port
export INPUT_LOCKER_PORT=8080

# Debug mode
export INPUT_LOCKER_DEBUG=1

# Custom config directory
export INPUT_LOCKER_CONFIG_DIR=/path/to/config
```

---

## 📡 API Reference

Input Locker exposes a REST API on `http://127.0.0.1:8080` for integration with other tools.

### Endpoints

#### Health Check
```http
GET /api/health
```
Returns: `{"success": true, "data": {"status": "ok"}}`

#### Device Management

```http
GET /api/devices/list
```
Returns list of all detected input devices.

**Response Example:**
```json
{
  "success": true,
  "data": [
    {
      "id": "/dev/input/event3",
      "path": "/dev/input/event3",
      "name": "Logitech USB Receiver",
      "type": "keyboard",
      "blocked": false
    },
    {
      "id": "/dev/input/event4",
      "path": "/dev/input/event4",
      "name": "Logitech USB Receiver Mouse",
      "type": "mouse",
      "blocked": false
    }
  ]
}
```

```http
POST /api/devices/block-all
```
Locks all input devices (except touchscreens).

```http
POST /api/devices/unblock-all
```
Unlocks all input devices.

```http
POST /api/devices/lock-by-types
Content-Type: application/json

{"types": ["keyboard", "mouse", "touchpad", "touchscreen"]}
```
Locks only specified device types.

#### Timer

```http
POST /api/timer/set
Content-Type: application/json

{"minutes": 5}
```
Sets auto-unlock timer.

```http
POST /api/timer/cancel
```
Cancels active timer.

```http
GET /api/timer/status
```
Returns timer status.

**Response Example:**
```json
{
  "success": true,
  "data": {
    "active": true,
    "remainingSeconds": 245,
    "totalSeconds": 300
  }
}
```

#### Statistics

```http
GET /api/stats
```
Returns usage statistics.

```http
GET /api/system/status
```
Returns system status.

**Response Example:**
```json
{
  "success": true,
  "data": {
    "running": true,
    "activeBlocks": 3,
    "connectedDevices": 5,
    "uptime": 3600
  }
}
```

### WebSocket Events

Connect to `ws://127.0.0.1:8080/socket.io/` for real-time updates:

| Event | Description |
|-------|-------------|
| `device_update` | Device status changed |
| `status_update` | System status changed |
| `timer_update` | Timer status changed |

---

## 🏗️ Architecture

```
input-locker/
├── api/                      # Python Backend
│   ├── api_server.py        # FastAPI REST server
│   ├── _internal.py         # Core blocking logic
│   └── simple_blocker.py    # Device grabbing implementation
├── src/                      # Python Core Modules
│   ├── core/
│   │   ├── device_manager.py    # Device detection & classification
│   │   ├── config_manager.py    # Configuration handling
│   │   └── hotkey_handler.py    # Hotkey detection
│   └── utils/
│       ├── logger.py            # Logging utilities
│       └── privileges.py        # Root privilege handling
├── web-ui/                   # Electron + React Frontend
│   ├── src/
│   │   ├── pages/
│   │   │   └── Dashboard/       # Main dashboard UI
│   │   ├── components/          # Reusable UI components
│   │   ├── services/            # API client
│   │   └── context/             # React context providers
│   ├── electron/
│   │   └── main.cjs             # Electron main process
│   └── dist/                    # Built frontend
├── packaging/                # Distribution files
│   ├── build-deb.sh            # Debian package builder
│   ├── install.sh              # Quick installer
│   └── INSTALL.md              # Installation guide
├── config/                   # Default configuration
├── requirements.txt          # Python dependencies
└── README.md                 # This file
```

### Technology Stack

| Component | Technology |
|-----------|------------|
| **Backend** | Python 3.8+, FastAPI, uvicorn |
| **Device Access** | evdev (Linux input subsystem) |
| **Frontend** | React 18, TypeScript, Vite |
| **UI Framework** | Material-UI v5 |
| **Desktop** | Electron 28 |
| **Real-time** | Socket.IO |
| **Animations** | Framer Motion |

### How It Works

1. **Device Detection**: On startup, scans `/dev/input/` for input devices
2. **Classification**: Uses device capabilities and names to classify as keyboard, mouse, touchpad, or touchscreen
3. **Hotkey Listener**: Runs a background thread monitoring for `Ctrl+Alt+L`
4. **Device Grabbing**: Uses evdev's `grab()` to exclusively capture device input
5. **Pattern Detection**: While locked, monitors grabbed keyboards for the unlock pattern
6. **Touchscreen Exclusion**: Devices with multi-touch capabilities are automatically skipped

---

## 🔧 Troubleshooting

### Application won't start

```bash
# Check if port is in use
lsof -i :8080

# Kill existing processes
pkill -9 -f api_server
pkill -9 -f electron
```

### Lock doesn't work

```bash
# Verify running as root
sudo input-locker

# Check device permissions
ls -la /dev/input/event*

# Add user to input group (requires logout)
sudo usermod -a -G input $USER
```

### Unlock pattern not working

Make sure you're pressing the keys in sequence:
1. `↑` (Up arrow)
2. `↑` (Up arrow)
3. `↓` (Down arrow)
4. `↓` (Down arrow)
5. `Enter`

Each key must be pressed within 3 seconds of the previous one.

### GUI not displaying correctly

```bash
# Check DISPLAY variable
echo $DISPLAY

# Set if needed
export DISPLAY=:0
```

### Dependencies missing

```bash
# Debian / Ubuntu / Linux Mint
sudo apt install python3 python3-venv python3-pip nodejs npm policykit-1 xdotool

# Fedora / RHEL / Rocky / AlmaLinux
sudo dnf install python3 python3-pip nodejs npm polkit xdotool

# Arch / Manjaro
sudo pacman -Sy --needed python python-virtualenv python-pip nodejs npm polkit xdotool
```

### Building the .deb package

```bash
cd /opt/input-locker/packaging
sudo ./build-deb.sh
```

---

## 🛡️ Security Considerations

1. **Root Privileges**: The application requires root to access `/dev/input` devices. It uses `pkexec` for secure privilege escalation.

2. **Pattern Security**: The unlock pattern `↑↑↓↓Enter` is simple by design. For security-critical applications, consider the screen locker instead.

3. **API Access**: The API only binds to `127.0.0.1` (localhost) and is not accessible from the network.

4. **No Sensitive Data**: Input Locker doesn't capture, store, or transmit any keystrokes or input data.

---

## 📝 Changelog

### v1.0.0 (2024-12-10)
- ✨ Initial release
- 🔒 Hotkey lock (Ctrl+Alt+L)
- 🎮 Pattern unlock (↑↑↓↓Enter)
- 👆 Touchscreen exclusion
- 📊 Security profiles (Focus, Child Lock, Gaming, Presentation)
- ⏱️ Timer-based locking
- 🎨 Modern React UI with dark/light theme
- 📦 Debian package support

---

## 🤝 Contributing

Contributions are welcome! Please read our contributing guidelines before submitting PRs.

```bash
# Fork the repository
git clone https://github.com/yourusername/input-locker.git
cd input-locker

# Create a feature branch
git checkout -b feature/amazing-feature

# Make your changes and test
npm run electron:dev

# Commit and push
git commit -m "Add amazing feature"
git push origin feature/amazing-feature

# Open a Pull Request
```

### Development Commands

```bash
# Run in development mode
cd web-ui && sudo npm run electron:dev

# Build for production
npm run build

# Build Debian package
cd packaging && sudo ./build-deb.sh

# Run Python tests
./venv/bin/pytest

# Lint TypeScript
cd web-ui && npm run lint
```

---

## ❓ FAQ

**Q: Does this work on Wayland?**
A: Yes. Input Locker trabaja directamente con los dispositivos de `/dev/input/*` usando `evdev`, así que el bloqueo de teclado/ratón funciona tanto en X11 como en Wayland siempre que ejecutes la app con permisos suficientes (root/pkexec) para leer esos dispositivos. La ventana de la UI se ejecuta normalmente sobre X11/XWayland o el backend de Wayland que use tu entorno de escritorio.

**Q: Can I change the unlock pattern?**
A: Yes, modify the `emergencyPattern` setting in the configuration file.

**Q: Does it work with Bluetooth keyboards?**
A: Yes, all input devices that appear in `/dev/input/` are supported.

**Q: Is this a replacement for screen locking?**
A: No, Input Locker is for temporary input blocking. For security, use your system's screen locker.

**Q: Can I use this on a server without a GUI?**
A: The API server can run headless. Use the REST API for control.

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

```
MIT License

Copyright (c) 2025 Input Locker

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

## 🙏 Acknowledgments

- [evdev](https://python-evdev.readthedocs.io/) - Python bindings for Linux input subsystem
- [FastAPI](https://fastapi.tiangolo.com/) - Modern Python web framework
- [Electron](https://www.electronjs.org/) - Cross-platform desktop apps
- [Material-UI](https://mui.com/) - React UI component library
- [Framer Motion](https://www.framer.com/motion/) - Animation library
- [Socket.IO](https://socket.io/) - Real-time communication

---

<div align="center">

**Made with ❤️ for the Linux community**

[⭐ Star this repo](https://github.com/vvv-bash/Input-Locker) • [🐛 Report Bug](https://github.com/vvv-bash/Input-Locker/issues) • [💡 Request Feature](https://github.com/vvv-bash/Input-Locker/issues)

</div>

