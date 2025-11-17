/**
 * FinAgent Electron Main Process
 *
 * Manages the application window, Python backend subprocess,
 * and coordinates communication between frontend and backend.
 */

const { app, BrowserWindow, ipcMain, dialog } = require('electron');
const path = require('path');
const { spawn } = require('child_process');
const axios = require('axios');
const log = require('electron-log');
const Store = require('electron-store');

// Configure logging
log.transports.file.level = 'info';
log.transports.console.level = 'debug';

// Persistent storage for user settings
const store = new Store();

// Global references
let mainWindow = null;
let pythonProcess = null;
const PYTHON_PORT = 8000;
const BACKEND_URL = `http://localhost:${PYTHON_PORT}`;
const MAX_STARTUP_WAIT = 30000; // 30 seconds

/**
 * Create the main application window
 */
function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    minWidth: 1000,
    minHeight: 700,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      nodeIntegration: false,
      contextIsolation: true,
      enableRemoteModule: false
    },
    show: false, // Show after Python backend is ready
    backgroundColor: '#1e1e1e'
  });

  // Load the frontend
  const isDev = process.argv.includes('--dev');
  if (isDev) {
    mainWindow.loadFile(path.join(__dirname, 'renderer', 'index.html'));
    mainWindow.webContents.openDevTools();
  } else {
    mainWindow.loadFile(path.join(__dirname, 'renderer', 'index.html'));
  }

  // Show window when ready
  mainWindow.once('ready-to-show', () => {
    mainWindow.show();
  });

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

/**
 * Start the Python FastAPI backend as a subprocess
 */
async function startPythonBackend() {
  return new Promise((resolve, reject) => {
    log.info('Starting Python backend...');

    // Determine Python executable path
    const isDev = process.argv.includes('--dev');
    let pythonCommand, pythonArgs;

    if (isDev) {
      // Development: Use uv to run from source
      pythonCommand = 'uv';
      pythonArgs = [
        'run',
        'uvicorn',
        'finagent.main:app',
        '--host', '127.0.0.1',
        '--port', String(PYTHON_PORT),
        '--log-level', 'info'
      ];
    } else {
      // Production: Use bundled Python runtime
      const pythonDir = path.join(process.resourcesPath, 'python');
      if (process.platform === 'win32') {
        pythonCommand = path.join(pythonDir, 'Scripts', 'uvicorn.exe');
      } else {
        pythonCommand = path.join(pythonDir, 'bin', 'uvicorn');
      }
      pythonArgs = [
        'finagent.main:app',
        '--host', '127.0.0.1',
        '--port', String(PYTHON_PORT),
        '--log-level', 'info'
      ];
    }

    log.info(`Python command: ${pythonCommand} ${pythonArgs.join(' ')}`);

    // Spawn Python process
    pythonProcess = spawn(pythonCommand, pythonArgs, {
      cwd: isDev ? path.join(__dirname, '..') : process.resourcesPath,
      env: { ...process.env }
    });

    // Log Python output
    pythonProcess.stdout.on('data', (data) => {
      const message = data.toString().trim();
      log.info(`[Python] ${message}`);

      // Check for startup success message
      if (message.includes('Uvicorn running') || message.includes('Application startup complete')) {
        log.info('Python backend started successfully');
        resolve();
      }
    });

    pythonProcess.stderr.on('data', (data) => {
      const message = data.toString().trim();
      log.error(`[Python Error] ${message}`);
    });

    pythonProcess.on('error', (error) => {
      log.error(`Failed to start Python backend: ${error.message}`);
      reject(error);
    });

    pythonProcess.on('exit', (code, signal) => {
      log.warn(`Python backend exited with code ${code}, signal ${signal}`);
      pythonProcess = null;
    });

    // Fallback: Wait for health check to pass
    setTimeout(async () => {
      const isReady = await checkBackendHealth();
      if (isReady) {
        resolve();
      } else {
        reject(new Error('Python backend failed to start within timeout'));
      }
    }, 5000);
  });
}

/**
 * Check if Python backend is healthy and ready
 */
async function checkBackendHealth(maxRetries = 10) {
  for (let i = 0; i < maxRetries; i++) {
    try {
      const response = await axios.get(`${BACKEND_URL}/health/ready`, {
        timeout: 2000
      });

      if (response.data.status === 'ready') {
        log.info('Backend health check passed');
        return true;
      }
    } catch (error) {
      log.debug(`Health check attempt ${i + 1}/${maxRetries} failed`);
    }

    // Wait before retry
    await new Promise(resolve => setTimeout(resolve, 1000));
  }

  log.error('Backend health check failed after max retries');
  return false;
}

/**
 * Stop the Python backend gracefully
 */
function stopPythonBackend() {
  if (pythonProcess) {
    log.info('Stopping Python backend...');
    pythonProcess.kill('SIGTERM');

    // Force kill if not stopped after 5 seconds
    setTimeout(() => {
      if (pythonProcess) {
        log.warn('Force killing Python backend');
        pythonProcess.kill('SIGKILL');
      }
    }, 5000);
  }
}

/**
 * IPC Handlers Setup
 */
function setupIpcHandlers() {
  // Submit research query
  ipcMain.handle('query:submit', async (event, queryText) => {
    try {
      log.info(`Submitting query: ${queryText}`);
      const response = await axios.post(`${BACKEND_URL}/api/v1/research/query/sync`, {
        text: queryText,
        filters: {}
      });
      return { success: true, data: response.data };
    } catch (error) {
      log.error(`Query submission failed: ${error.message}`);
      return { success: false, error: error.message };
    }
  });

  // Check backend status
  ipcMain.handle('backend:status', async () => {
    try {
      const response = await axios.get(`${BACKEND_URL}/health/ready`, {
        timeout: 2000
      });
      return { success: true, data: response.data };
    } catch (error) {
      return { success: false, error: error.message };
    }
  });

  // Get application info
  ipcMain.handle('app:info', () => {
    return {
      version: app.getVersion(),
      name: app.getName(),
      platform: process.platform,
      arch: process.arch
    };
  });

  // Show error dialog
  ipcMain.handle('dialog:error', async (event, title, message) => {
    await dialog.showMessageBox(mainWindow, {
      type: 'error',
      title: title,
      message: message,
      buttons: ['OK']
    });
  });
}

/**
 * App Lifecycle
 */

app.whenReady().then(async () => {
  // Setup IPC handlers first
  setupIpcHandlers();
  try {
    // Check if backend is already running
    log.info('Checking if backend is already running...');
    const alreadyRunning = await checkBackendHealth();

    if (!alreadyRunning) {
      // Start Python backend if not already running
      log.info('Backend not running, starting it now...');
      await startPythonBackend();

      // Wait for backend to be ready
      const isReady = await checkBackendHealth();
      if (!isReady) {
        throw new Error('Backend failed health check');
      }
    } else {
      log.info('Backend is already running, skipping startup');
    }

    // Create window
    createWindow();

    log.info('Application started successfully');
  } catch (error) {
    log.error(`Application startup failed: ${error.message}`);

    dialog.showErrorBox(
      'Startup Error',
      `Failed to start FinAgent: ${error.message}\n\nPlease check the logs for details.`
    );

    app.quit();
  }
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) {
    createWindow();
  }
});

app.on('before-quit', () => {
  stopPythonBackend();
});

// Handle uncaught exceptions
process.on('uncaughtException', (error) => {
  log.error(`Uncaught exception: ${error.message}`, error);
});

process.on('unhandledRejection', (reason, promise) => {
  log.error('Unhandled rejection at:', promise, 'reason:', reason);
});
