const { app, BrowserWindow, ipcMain, Tray, Menu, nativeImage } = require('electron');
const path = require('path');

// Keep references to prevent garbage collection
let mainWindow = null;
let tray = null;
let apiProcess = null;

// Check if running in development (explicitly set via environment variable)
const isDev = process.env.ELECTRON_DEV === 'true';

// Project root is two levels up from electron/ folder (web-ui/electron -> web-ui -> input-locker)
const projectRoot = path.resolve(__dirname, '../..');

// Debug paths
console.log('__dirname:', __dirname);
console.log('Project root resolved to:', projectRoot);

// API Server management
// In v3, the API/backend is expected to be managed externally (e.g. systemd).
// The Electron app no longer starts it via pkexec to avoid password prompts.
function startApiServer() {
  console.log('Assuming API server is managed externally (no pkexec spawn).');
  return Promise.resolve();
}

function stopApiServer() {
  // No-op: backend lifecycle is handled by systemd or the admin.
}

function createWindow() {
  // Create the browser window with glassmorphic style
  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    minWidth: 1000,
    minHeight: 700,
    title: 'Input Locker',
    icon: path.join(__dirname, '../public/icon.png'),
    frame: true,
    transparent: false,
    backgroundColor: '#0a1929',
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.join(__dirname, 'preload.cjs')
    }
  });

  // Load the app - always load from dist in production
  const distPath = path.join(__dirname, '../dist/index.html');
  
  // Check if we should use dev server (only if explicitly set)
  if (process.env.ELECTRON_DEV === 'true') {
    mainWindow.loadURL('http://localhost:3000');
    mainWindow.webContents.openDevTools();
  } else {
    console.log('Loading from:', distPath);
    mainWindow.loadFile(distPath);
  }

  // Hide menu bar
  mainWindow.setMenuBarVisibility(false);

  // Handle window close - quit the app
  mainWindow.on('close', () => {
    stopApiServer();
    app.quit();
  });

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

function createTray() {
  const iconPath = path.join(__dirname, '../public/icon.png');
  
  try {
    const icon = nativeImage.createFromPath(iconPath);
    tray = new Tray(icon.resize({ width: 22, height: 22 }));
  } catch (e) {
    // Create a simple icon if file not found
    tray = new Tray(nativeImage.createEmpty());
  }
  
  const contextMenu = Menu.buildFromTemplate([
    { 
      label: 'Show Input Locker', 
      click: () => {
        if (mainWindow) {
          mainWindow.show();
          mainWindow.focus();
        }
      }
    },
    { type: 'separator' },
    { 
      label: 'Lock All Devices', 
      click: () => {
        if (mainWindow) {
          mainWindow.webContents.send('quick-action', 'lock-all');
        }
      }
    },
    { 
      label: 'Unlock All Devices', 
      click: () => {
        if (mainWindow) {
          mainWindow.webContents.send('quick-action', 'unlock-all');
        }
      }
    },
    { type: 'separator' },
    { 
      label: 'Quit', 
      click: () => {
        tray = null;
        stopApiServer();
        app.quit();
      }
    }
  ]);
  
  tray.setToolTip('Input Locker');
  tray.setContextMenu(contextMenu);
  
  tray.on('click', () => {
    if (mainWindow) {
      if (mainWindow.isVisible()) {
        mainWindow.hide();
      } else {
        mainWindow.show();
        mainWindow.focus();
      }
    }
  });
}

// App lifecycle
app.whenReady().then(async () => {
  console.log('Electron app ready');
  
  // Start API server first and wait for it
  try {
    await startApiServer();
    console.log('API server started successfully');
  } catch (err) {
    console.error('API server failed to start:', err.message);
    // Continue anyway - the UI can show connection error
  }
  
  createWindow();
  // Tray disabled - app closes when window closes
  // createTray();
  
  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
    }
  });
});

app.on('window-all-closed', () => {
  stopApiServer();
  // Force exit after a short delay to ensure shutdown request is sent
  setTimeout(() => {
    console.log('Force exiting...');
    process.exit(0);
  }, 500);
});

app.on('before-quit', () => {
  stopApiServer();
});

// IPC handlers for communication with renderer
ipcMain.handle('get-app-path', () => {
  return app.getAppPath();
});

ipcMain.handle('is-dev', () => {
  return isDev;
});
