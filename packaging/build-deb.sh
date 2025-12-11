#!/bin/bash
# Build script for Input Locker .deb package
set -e

VERSION="2.0.0"
PACKAGE_NAME="input-locker_${VERSION}_amd64"
BUILD_DIR="/opt/input-locker/packaging"
PKG_DIR="$BUILD_DIR/$PACKAGE_NAME"
SOURCE_DIR="/opt/input-locker"

echo "🔨 Building Input Locker v${VERSION} .deb package..."

# Clean previous build
rm -rf "$PKG_DIR"
mkdir -p "$PKG_DIR/DEBIAN"
mkdir -p "$PKG_DIR/opt/input-locker"
mkdir -p "$PKG_DIR/usr/share/applications"
mkdir -p "$PKG_DIR/usr/share/icons/hicolor/256x256/apps"
mkdir -p "$PKG_DIR/usr/bin"

# Copy DEBIAN control files
echo "📋 Creating control files..."

cat > "$PKG_DIR/DEBIAN/control" << 'EOF'
Package: input-locker
Version: 2.0.0
Section: utils
Priority: optional
Architecture: amd64
Depends: python3 (>= 3.8), python3-venv, python3-pip, nodejs (>= 18.0.0), npm, policykit-1, xdotool
Maintainer: Input Locker Team <admin@inputlocker.local>
Description: Input Device Locker for Linux
 A modern application to lock and unlock input devices (keyboard, mouse,
 touchpad, touchscreen) on Linux systems. Features include:
  - Lock all input devices with Ctrl+Alt+L
  - Unlock with pattern ↑↑↓↓Enter
  - Security profiles (Focus, Child Lock, Gaming, Presentation)
  - Timer-based auto-unlock
  - Modern web-based UI with Electron
  - Touchscreen exclusion support
Homepage: https://github.com/input-locker/input-locker
EOF

cat > "$PKG_DIR/DEBIAN/postinst" << 'POSTINST'
#!/bin/bash
set -e

APP_DIR="/opt/input-locker"

echo "🔧 Setting up Input Locker..."

# Create Python virtual environment
if [ ! -d "$APP_DIR/venv" ]; then
    echo "📦 Creating Python virtual environment..."
    python3 -m venv "$APP_DIR/venv"
fi

# Install Python dependencies
echo "📦 Installing Python dependencies..."
"$APP_DIR/venv/bin/pip" install --upgrade pip
"$APP_DIR/venv/bin/pip" install -r "$APP_DIR/requirements.txt"

# Install Node.js dependencies and build
if [ -d "$APP_DIR/web-ui" ]; then
    echo "📦 Installing Node.js dependencies..."
    cd "$APP_DIR/web-ui"
    npm install --legacy-peer-deps
    
    echo "🔨 Building web UI..."
    npm run build 2>/dev/null || true
fi

# Set proper permissions
echo "🔐 Setting permissions..."
chmod +x "$APP_DIR/input-locker.sh"
chmod -R 755 "$APP_DIR"

# Update icon cache
gtk-update-icon-cache -f /usr/share/icons/hicolor 2>/dev/null || true

# Update desktop database  
update-desktop-database /usr/share/applications 2>/dev/null || true

echo ""
echo "✅ Input Locker installed successfully!"
echo ""
echo "Usage:"
echo "  - Run from menu: Input Locker"
echo "  - Run from terminal: input-locker"
echo "  - Lock: Ctrl+Alt+L"
echo "  - Unlock: ↑↑↓↓Enter"
echo ""

exit 0
POSTINST

cat > "$PKG_DIR/DEBIAN/prerm" << 'PRERM'
#!/bin/bash
set -e

echo "🗑️ Removing Input Locker..."

# Stop any running instances
pkill -9 -f "input-locker" 2>/dev/null || true
pkill -9 -f "api_server.py" 2>/dev/null || true

echo "✅ Input Locker stopped"

exit 0
PRERM

chmod 755 "$PKG_DIR/DEBIAN/postinst"
chmod 755 "$PKG_DIR/DEBIAN/prerm"

# Copy application files
echo "📁 Copying application files..."

# Copy Python API
cp -r "$SOURCE_DIR/api" "$PKG_DIR/opt/input-locker/"
cp -r "$SOURCE_DIR/src" "$PKG_DIR/opt/input-locker/"
cp -r "$SOURCE_DIR/config" "$PKG_DIR/opt/input-locker/"
cp "$SOURCE_DIR/requirements.txt" "$PKG_DIR/opt/input-locker/"
cp "$SOURCE_DIR/settings.json" "$PKG_DIR/opt/input-locker/" 2>/dev/null || true

# Copy web-ui (without node_modules and venv)
mkdir -p "$PKG_DIR/opt/input-locker/web-ui"
cp -r "$SOURCE_DIR/web-ui/src" "$PKG_DIR/opt/input-locker/web-ui/"
cp -r "$SOURCE_DIR/web-ui/electron" "$PKG_DIR/opt/input-locker/web-ui/"
cp -r "$SOURCE_DIR/web-ui/public" "$PKG_DIR/opt/input-locker/web-ui/" 2>/dev/null || true
cp "$SOURCE_DIR/web-ui/package.json" "$PKG_DIR/opt/input-locker/web-ui/"
cp "$SOURCE_DIR/web-ui/package-lock.json" "$PKG_DIR/opt/input-locker/web-ui/" 2>/dev/null || true
cp "$SOURCE_DIR/web-ui/vite.config.ts" "$PKG_DIR/opt/input-locker/web-ui/"
cp "$SOURCE_DIR/web-ui/tsconfig.json" "$PKG_DIR/opt/input-locker/web-ui/"
cp "$SOURCE_DIR/web-ui/tsconfig.node.json" "$PKG_DIR/opt/input-locker/web-ui/" 2>/dev/null || true
cp "$SOURCE_DIR/web-ui/index.html" "$PKG_DIR/opt/input-locker/web-ui/"

# Copy pre-built dist if exists
if [ -d "$SOURCE_DIR/web-ui/dist" ]; then
    cp -r "$SOURCE_DIR/web-ui/dist" "$PKG_DIR/opt/input-locker/web-ui/"
fi

# Remove __pycache__ directories
find "$PKG_DIR" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find "$PKG_DIR" -type f -name "*.pyc" -delete 2>/dev/null || true

# Create launcher script
cat > "$PKG_DIR/opt/input-locker/input-locker.sh" << 'LAUNCHER'
#!/bin/bash
# Input Locker - Launch Script
# Locks input devices with Ctrl+Alt+L, unlock with ↑↑↓↓Enter

APP_DIR="/opt/input-locker"
cd "$APP_DIR/web-ui"

# Check if running as root or with pkexec
if [ "$EUID" -ne 0 ]; then
    exec pkexec --disable-internal-agent "$0" "$@"
fi

# Set display for GUI
export DISPLAY="${DISPLAY:-:0}"
export XAUTHORITY="${XAUTHORITY:-$HOME/.Xauthority}"

# Find Xauthority if not set
if [ ! -f "$XAUTHORITY" ]; then
    for user_home in /home/*; do
        if [ -f "$user_home/.Xauthority" ]; then
            export XAUTHORITY="$user_home/.Xauthority"
            break
        fi
    done
fi

# Kill any existing instances
pkill -9 -f "electron.*input-locker" 2>/dev/null || true
pkill -9 -f "api_server.py" 2>/dev/null || true
sleep 1

# Run Electron app
exec npm run electron -- --no-sandbox
LAUNCHER

chmod +x "$PKG_DIR/opt/input-locker/input-locker.sh"

# Create symlink script
cat > "$PKG_DIR/usr/bin/input-locker" << 'BINSCRIPT'
#!/bin/bash
exec /opt/input-locker/input-locker.sh "$@"
BINSCRIPT

chmod +x "$PKG_DIR/usr/bin/input-locker"

# Create .desktop file
cat > "$PKG_DIR/usr/share/applications/input-locker.desktop" << 'DESKTOP'
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
StartupWMClass=input-locker
DESKTOP

# Create a simple icon (SVG)
cat > "$PKG_DIR/usr/share/icons/hicolor/256x256/apps/input-locker.svg" << 'ICON'
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 256 256">
  <rect width="256" height="256" rx="40" fill="#1976d2"/>
  <rect x="68" y="90" width="120" height="90" rx="10" fill="white"/>
  <circle cx="128" cy="70" r="35" fill="none" stroke="white" stroke-width="12"/>
  <circle cx="128" cy="130" r="12" fill="#1976d2"/>
  <rect x="122" y="130" width="12" height="30" fill="#1976d2"/>
</svg>
ICON

# Build the package
echo "📦 Building .deb package..."
cd "$BUILD_DIR"
dpkg-deb --build "$PACKAGE_NAME"

if [ -f "$BUILD_DIR/${PACKAGE_NAME}.deb" ]; then
    echo ""
    echo "✅ Package built successfully!"
    echo "📦 Package: $BUILD_DIR/${PACKAGE_NAME}.deb"
    
    # Create portable tar.gz archive of the package directory
    echo "📦 Creating portable tar.gz archive..."
    tar -czf "${PACKAGE_NAME}.tar.gz" "$PACKAGE_NAME"
    echo "📦 Archive: $BUILD_DIR/${PACKAGE_NAME}.tar.gz"
    echo ""
    echo "To install on another machine:"
    echo "  sudo dpkg -i ${PACKAGE_NAME}.deb"
    echo "  sudo apt-get install -f  # Fix dependencies if needed"
    echo ""
    
    # Show package info
    dpkg-deb --info "$BUILD_DIR/${PACKAGE_NAME}.deb"
else
    echo "❌ Failed to build package"
    exit 1
fi
