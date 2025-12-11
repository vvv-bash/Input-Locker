#!/bin/bash
# Input Locker - Quick Install Script
# Run: curl -fsSL https://raw.githubusercontent.com/your-repo/input-locker/main/install.sh | sudo bash
set -e

echo "╔════════════════════════════════════════════════════════════╗"
echo "║           INPUT LOCKER - Quick Installer                   ║"
echo "║   Lock: Ctrl+Alt+L  |  Unlock: ↑↑↓↓Enter                  ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "❌ Please run as root: sudo bash install.sh"
    exit 1
fi

# Detect OS / package manager
if [ -f /etc/debian_version ]; then
    PKG_MANAGER="apt"      # Debian, Ubuntu, Linux Mint, Pop!_OS, etc.
elif [ -f /etc/redhat-release ]; then
    PKG_MANAGER="dnf"      # Fedora, RHEL, Rocky, AlmaLinux, etc.
elif command -v pacman >/dev/null 2>&1; then
    PKG_MANAGER="pacman"   # Arch, Manjaro, EndeavourOS, etc.
else
    echo "❌ Unsupported OS. This script supports Debian/Ubuntu, Fedora/RHEL-like and Arch/Manjaro."
    exit 1
fi

echo "📦 Installing system dependencies..."

if [ "$PKG_MANAGER" = "apt" ]; then
    apt update
    apt install -y python3 python3-venv python3-pip xdotool policykit-1
    
    # Install Node.js 18+ if not available
    if ! command -v node &> /dev/null || [ $(node -v | cut -d'.' -f1 | tr -d 'v') -lt 18 ]; then
        echo "📦 Installing Node.js 18..."
        curl -fsSL https://deb.nodesource.com/setup_18.x | bash -
        apt install -y nodejs
    fi
elif [ "$PKG_MANAGER" = "dnf" ]; then
    dnf install -y python3 python3-pip xdotool polkit nodejs npm
elif [ "$PKG_MANAGER" = "pacman" ]; then
    pacman -Sy --noconfirm python python-pip nodejs npm polkit xdotool
fi

echo "📁 Setting up application directory..."
APP_DIR="/opt/input-locker"
mkdir -p "$APP_DIR"

# If this script is run from within the source directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ -f "$SCRIPT_DIR/requirements.txt" ]; then
    echo "📋 Copying files from source directory..."
    cp -r "$SCRIPT_DIR"/* "$APP_DIR/"
fi

cd "$APP_DIR"

# Create Python virtual environment
echo "🐍 Creating Python virtual environment..."
python3 -m venv venv
./venv/bin/pip install --upgrade pip
./venv/bin/pip install -r requirements.txt

# Install Node.js dependencies
echo "📦 Installing Node.js dependencies..."
cd "$APP_DIR/web-ui"
npm install --legacy-peer-deps

# Build the UI
echo "🔨 Building web UI..."
npm run build

# Set permissions
echo "🔐 Setting permissions..."
chmod +x "$APP_DIR/input-locker.sh"
chmod -R 755 "$APP_DIR"

# Create symlink
ln -sf "$APP_DIR/input-locker.sh" /usr/bin/input-locker

# Create desktop entry
cat > /usr/share/applications/input-locker.desktop << 'EOF'
[Desktop Entry]
Name=Input Locker
Comment=Lock and unlock input devices (keyboard, mouse, touchpad)
Exec=/opt/input-locker/input-locker.sh
Icon=input-locker
Terminal=false
Type=Application
Categories=Utility;System;Security;
Keywords=lock;keyboard;mouse;touchpad;input;security;child;
StartupNotify=true
EOF

# Create icon
mkdir -p /usr/share/icons/hicolor/256x256/apps
cat > /usr/share/icons/hicolor/256x256/apps/input-locker.svg << 'EOF'
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 256 256">
  <rect width="256" height="256" rx="40" fill="#1976d2"/>
  <rect x="68" y="90" width="120" height="90" rx="10" fill="white"/>
  <circle cx="128" cy="70" r="35" fill="none" stroke="white" stroke-width="12"/>
  <circle cx="128" cy="130" r="12" fill="#1976d2"/>
  <rect x="122" y="130" width="12" height="30" fill="#1976d2"/>
</svg>
EOF

# Update caches
gtk-update-icon-cache -f /usr/share/icons/hicolor 2>/dev/null || true
update-desktop-database /usr/share/applications 2>/dev/null || true

echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║              ✅ Installation Complete!                      ║"
echo "╠════════════════════════════════════════════════════════════╣"
echo "║  To run:  input-locker  (or from application menu)         ║"
echo "║                                                            ║"
echo "║  🔒 Lock:    Ctrl + Alt + L                                ║"
echo "║  🔓 Unlock:  ↑ ↑ ↓ ↓ Enter                                 ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
