/**
 * FinAgent Electron Preload Script
 *
 * Exposes safe, limited API to the renderer process.
 * This is the bridge between the isolated renderer and Node.js APIs.
 */

const { contextBridge, ipcRenderer } = require('electron');

// Expose protected methods that allow the renderer process to use
// ipcRenderer without exposing the entire object
contextBridge.exposeInMainWorld('electronAPI', {
  // Query operations
  submitQuery: (queryText) => ipcRenderer.invoke('query:submit', queryText),

  // Backend status
  getBackendStatus: () => ipcRenderer.invoke('backend:status'),

  // App info
  getAppInfo: () => ipcRenderer.invoke('app:info'),

  // Dialogs
  showError: (title, message) => ipcRenderer.invoke('dialog:error', title, message),

  // Platform info
  platform: process.platform,
  version: process.versions.electron
});

// Log preload completion
console.log('FinAgent preload script loaded');
