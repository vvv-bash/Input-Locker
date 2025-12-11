const { app, BrowserWindow, ipcMain, Tray, Menu, nativeImage } = require('electron');
const path = require('path');
const { spawn, exec } = require('child_process');

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
function startApiServer() {
  return new Promise((resolve, reject) => {
    const pythonPath = path.join(projectRoot, 'venv/bin/python');
    const apiScript = path.join(projectRoot, 'api/api_server.py');
    
    console.log('Starting API server...');
    console.log('Project root:', projectRoot);
    console.log('Python:', pythonPath);
    console.log('Script:', apiScript);
    
    // Check if files exist
    const fs = require('fs');
    if (!fs.existsSync(pythonPath)) {
      console.error('Python not found at:', pythonPath);
      reject(new Error('Python not found'));
      return;
    }
    if (!fs.existsSync(apiScript)) {
      console.error('API script not found at:', apiScript);
      reject(new Error('API script not found'));
      return;
    }
    
    // Use pkexec for elevated permissions to access input devices
    apiProcess = spawn('pkexec', [pythonPath, '-u', apiScript, '--host', '127.0.0.1', '--port', '8080'], {
      cwd: projectRoot,
      env: { 
        ...process.env, 
        PYTHONUNBUFFERED: '1',
        PYTHONPATH: projectRoot
      },
      stdio: ['ignore', 'pipe', 'pipe']
    });
    
    let serverStarted = false;
    let stdoutData = '';
    let stderrData = '';
    
    apiProcess.stdout.on('data', (data) => {
      const output = data.toString();
      stdoutData += output;
      console.log(`API stdout: ${output.trim()}`);
      // Check if uvicorn started successfully
      if (output.includes('Uvicorn running') || output.includes('Application startup complete')) {
        serverStarted = true;
        resolve();
      }
    });
    
    apiProcess.stderr.on('data', (data) => {
      const output = data.toString();
      stderrData += output;
      console.error(`API stderr: ${output.trim()}`);
    });
    
    apiProcess.on('error', (err) => {
      console.error('Failed to start API server:', err);
      reject(err);
    });
    
    apiProcess.on('close', (code) => {
      console.log(`API server exited with code ${code}`);
      if (stdoutData) console.log('API stdout was:', stdoutData);
      if (stderrData) console.log('API stderr was:', stderrData);
      if (!serverStarted && code !== 0) {
        reject(new Error(`API server exited with code ${code}`));
      }
    });
    
    // Fallback timeout - resolve anyway after 10 seconds (pkexec may show password dialog)
    setTimeout(() => {
      if (!serverStarted) {
        console.log('API server timeout - continuing anyway');
        console.log('Stdout so far:', stdoutData || 'none');
        console.log('Stderr so far:', stderrData || 'none');
        resolve();
      }
    }, 10000);
  });
}

function stopApiServer() {
  if (!apiProcess) return;
  
  console.log('Stopping API server...');
  
  // Call shutdown endpoint instead of killing (pkexec process can't be killed directly)
  const http = require('http');
  const req = http.request({
    hostname: '127.0.0.1',
    port: 8080,
    path: '/api/shutdown',
    method: 'POST',
    timeout: 1000
  }, (res) => {
    console.log('Shutdown request sent, status:', res.statusCode);
  });
  
  req.on('error', (e) => {
    console.log('Shutdown request error (may be already stopped):', e.message);
  });
  
  req.end();
  
  // Also try to kill via pkill as backup
  try {
    const { execSync } = require('child_process');
    execSync('pkill -9 -f "api_server.py" 2>/dev/null || true', { timeout: 1000 });
  } catch (e) {
    // Ignore errors
  }
  
  apiProcess = null;
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
