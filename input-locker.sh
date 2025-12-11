#!/usr/bin/env bash
set -euo pipefail

# Wrapper to run Input Locker as a desktop application
# Supports both the new Electron UI and legacy PyQt6 UI

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Default to the new Electron UI
UI_MODE="electron"

# Parse arguments
for arg in "$@"; do
  case $arg in
    --legacy|--pyqt)
      UI_MODE="pyqt"
      shift
      ;;
    --help|-h)
      echo "Input Locker - Desktop Application"
      echo ""
      echo "Usage: input-locker [OPTIONS]"
      echo ""
      echo "Options:"
      echo "  --legacy, --pyqt  Use the legacy PyQt6 interface"
      echo "  --help, -h        Show this help"
      echo ""
      echo "By default, launches the modern Electron/React interface."
      exit 0
      ;;
  esac
done

if [ "$UI_MODE" == "electron" ]; then
  LAUNCHER="$SCRIPT_DIR/input-locker-electron.sh"
else
  LAUNCHER="$SCRIPT_DIR/input-locker.sh"
fi

if [ ! -x "$LAUNCHER" ]; then 
  echo "Launcher not found or not executable: $LAUNCHER" >&2
  exit 2
fi

if [ "$(id -u)" -eq 0 ]; then
  # When running as root, set DISPLAY/XAUTHORITY
  export DISPLAY=${DISPLAY:-:0}

  if [ -z "${XAUTHORITY:-}" ]; then
    user_from_who=$(who | awk '$2==":0" {print $1; exit}') || true
    if [ -n "$user_from_who" ] && [ -f "/home/$user_from_who/.Xauthority" ]; then
      export XAUTHORITY="/home/$user_from_who/.Xauthority"
    else
      for user_home in /home/*; do
        if [ -f "$user_home/.Xauthority" ]; then
          export XAUTHORITY="$user_home/.Xauthority"
          break
        fi
      done
    fi
  fi

  exec "$LAUNCHER" "$@"
fi

# Ensure DISPLAY/XAUTHORITY are set for GUI forwarding
export DISPLAY=${DISPLAY:-:0}
export XAUTHORITY=${XAUTHORITY:-$HOME/.Xauthority}

if command -v pkexec >/dev/null 2>&1 && [ -n "${DISPLAY:-}" ]; then
  exec pkexec --disable-internal-agent "$LAUNCHER" "$@"
elif command -v sudo >/dev/null 2>&1; then
  exec sudo --preserve-env=DISPLAY,XAUTHORITY "$LAUNCHER" "$@"
else
  echo "Error: Neither pkexec nor sudo available for privilege elevation" >&2
  exit 1
fi
  echo "sudo not found. Run the launcher as root:" >&2
  echo "  sudo $LAUNCHER" >&2
  exit 1
fi
