# Electron Module Loading Debug Findings

## Issue Summary

The Electron desktop app fails to start with error:
```
TypeError: Cannot read properties of undefined (reading 'whenReady')
    at Object.<anonymous> (/Users/weifanliao/PycharmProjects/finagent/electron/main.js:252:5)
```

## Root Cause Analysis

### Key Finding: `process.type` is `undefined`

When running ANY JavaScript file with the Electron binary (`./node_modules/.bin/electron script.js`), **`process.type` remains `undefined`** instead of being set to `"browser"` (main process) or `"renderer"` (renderer process).

This is highly abnormal and indicates that Electron is NOT properly initializing its runtime environment.

### Test Results

#### Test 1: Simple Electron App
```javascript
const { app } = require('electron')
app.whenReady().then(() => console.log('Ready!'))
```

**Result:**
- `TypeError: Cannot read properties of undefined (reading 'whenReady')`
- `process.type`: `undefined`
- `require('electron')` returns: STRING (path to binary) instead of OBJECT (Electron API)

#### Test 2: Electron Module Type Check
```javascript
const electronModule = require('electron');
console.log(typeof electronModule); // "string"
console.log(process.type); // undefined
```

**Expected:**
- `typeof electronModule`: `"object"`
- `process.type`: `"browser"`
- `electronModule.app`: Should exist

**Actual:**
- `typeof electronModule`: `"string"`
- `process.type`: `undefined`
- `electronModule` value: `/Users/weifanliao/PycharmProjects/finagent/node_modules/electron/dist/Electron.app/Contents/MacOS/Electron`

### What This Means

When `require('electron')` returns a STRING instead of the Electron API object, it means Node.js is loading the `electron` npm package's `index.js` file, which is designed to return the path to the Electron binary for CLI use.

However, when code runs **inside** the Electron runtime (main or renderer process), `require('electron')` should be intercepted by Electron and return the actual Electron API object, not the path string.

The fact that it's NOT being intercepted indicates **Electron is not properly running the JavaScript code in its runtime context**.

## Diagnostic Commands

### Versions
```bash
./node_modules/.bin/electron --version
# v18.18.2 (Electron 28.2.0's bundled Chromium version)

electron --version
# electron: command not found (not in PATH - this is expected)
```

### Binary Check
```bash
file ./node_modules/electron/dist/Electron.app/Contents/MacOS/Electron
# Mach-O 64-bit executable arm64 (correct for Apple Silicon)
```

### Module Export
```bash
node -p "require('./node_modules/electron')"
# /Users/weifanliao/PycharmProjects/finagent/node_modules/electron/dist/Electron.app/Contents/MacOS/Electron
# (This is correct when run from Node.js)
```

## Attempted Fixes

1. ✅ **Fixed package.json scripts** - Used explicit path `./node_modules/.bin/electron` instead of just `electron`
2. ✅ **Reinstalled electron@28.2.0** - Removed and reinstalled, no change
3. ✅ **Clean reinstall of all node_modules** - Removed everything and reinstalled, no change
4. ✅ **Wrapped IPC handlers in function** - Moved to `app.whenReady()` callback, no change
5. ✅ **Added backend health check** - Tried to skip Python startup if already running, no change

## Hypotheses

### Hypothesis 1: Electron Binary Corruption
The Electron.app bundle might be corrupted or missing critical resources.

**Evidence:**
- Binary exists and reports correct version
- Binary is correct architecture (arm64)
- Package reinstall doesn't fix it

**Likelihood:** Low

### Hypothesis 2: macOS Security/Quarantine
macOS might be blocking Electron from running properly due to quarantine flags.

**Evidence:**
- App is not signed
- Downloaded via npm (not App Store)

**Test:**
```bash
xattr -lr ./node_modules/electron/dist/Electron.app
```

**Likelihood:** Medium

### Hypothesis 3: Electron 28.x Breaking Change
Electron 28 might have changed how it initializes or how `require('electron')` works.

**Evidence:**
- Version in package.json is 28.2.0
- Error stack trace shows `l._load (node:electron/js2c/asar_bundle:2:13642)` which means ASAR is involved
- `process.type` undefined is very unusual

**Likelihood:** High

### Hypothesis 4: ASAR Bundle Issue
The Electron internal ASAR bundle might not be loading correctly.

**Evidence:**
- Stack trace references `asar_bundle`
- Electron's internal module loader might be broken

**Likelihood:** High

## Next Steps to Try

1. **Check for macOS quarantine flags**
   ```bash
   xattr -d com.apple.quarantine ./node_modules/electron/dist/Electron.app
   ```

2. **Try downgrading to Electron 27 or 26**
   ```bash
   npm install electron@27.0.0
   ```

3. **Try running with electron-quick-start template**
   ```bash
   git clone https://github.com/electron/electron-quick-start
   cd electron-quick-start
   npm install && npm start
   ```
   If this works, compare package.json and structure

4. **Check ASAR extraction**
   ```bash
   npx asar extract ./node_modules/electron/dist/Electron.app/Contents/Resources/electron.asar /tmp/electron_extracted
   ls -la /tmp/electron_extracted
   ```

5. **Try different Node.js version**
   Current: v24.8.0
   Electron 28 expects: ~18.x (which it bundles)

   Might be a conflict between system Node and bundled Node

6. **Check Console.app logs**
   macOS might be logging why Electron is failing to initialize

## Environment

- **macOS Version:** Darwin 25.2.0
- **Architecture:** arm64 (Apple Silicon)
- **Node.js:** v24.8.0
- **npm:** 11.6.0
- **Electron:** 28.2.0 (installed), v18.18.2 (binary reports)
- **Working Directory:** `/Users/weifanliao/PycharmProjects/finagent`

## Conclusion

This is NOT a bug in the FinAgent code. This is a **fundamental Electron runtime initialization failure**. The Electron binary is not properly setting up its JavaScript runtime environment, which prevents `require('electron')` from working as expected.

This needs to be fixed before the desktop app can run. The Python backend works fine - this is purely an Electron issue.

---

**Created:** 2025-11-14
**Status:** Under Investigation
**Related Issue:** #10
