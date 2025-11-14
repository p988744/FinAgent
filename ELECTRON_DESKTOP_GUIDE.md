# FinAgent Desktop Application Guide

## Overview

FinAgent v0.0.2 introduces a cross-platform desktop application built with Electron, providing a modern graphical interface for the Taiwan Financial Legal Research Agent System.

## Architecture

### Hybrid Electron + Python Backend

```
┌─────────────────────────────────────────┐
│       Electron Desktop Application      │
├─────────────────────────────────────────┤
│  Main Process (Node.js)                 │
│  - Window management                    │
│  - Python FastAPI subprocess            │
│  - Health monitoring                    │
│  - IPC communication                    │
├─────────────────────────────────────────┤
│  Renderer Process (Browser)             │
│  - Modern UI with Traditional Chinese   │
│  - Query interface                      │
│  - Results display with citations       │
│  - Real-time status monitoring          │
└─────────────────────────────────────────┘
                 ↕ HTTP REST API
┌─────────────────────────────────────────┐
│    Python Backend (FastAPI)             │
│    - /api/v1/research/query/sync        │
│    - /health & /health/ready            │
│    - LangGraph agent orchestrator       │
│    - RAG retrieval with Chroma          │
└─────────────────────────────────────────┘
```

## Features

### v0.0.2 Features

✅ **Cross-Platform Support**
- Windows 10/11 (64-bit)
- macOS 10.13+ (Intel & Apple Silicon)

✅ **Modern UI**
- Traditional Chinese interface optimized for Taiwan users
- Clean, professional design
- Real-time backend status indicator
- Query examples for quick start

✅ **Python Backend Integration**
- Automatic Python subprocess management
- Health monitoring and auto-recovery
- Graceful shutdown handling

✅ **Research Capabilities**
- Full access to LangGraph multi-agent system
- RAG-based semantic search
- Citation tracking and display
- Confidence scoring

## Installation

### Prerequisites

#### For Development
- Node.js 18+ and npm
- Python 3.11+
- UV package manager
- Git

#### For End Users
- No prerequisites needed - all dependencies are bundled in the installer

### Development Setup

1. **Clone the repository**
```bash
git clone https://github.com/p988744/FinAgent.git
cd FinAgent
```

2. **Install Python dependencies**
```bash
uv sync
```

3. **Install Node.js dependencies**
```bash
npm install
```

4. **Configure environment**
```bash
cp .env.example .env
# Edit .env with your API keys and settings
```

5. **Run in development mode**
```bash
npm run dev
```

This starts both the Python backend and Electron frontend.

Alternatively, start them separately:
```bash
# Terminal 1: Start Python backend
uv run uvicorn finagent.main:app --reload --port 8000

# Terminal 2: Start Electron app
npm start
```

## Building for Production

### Build Scripts

The project includes automated build scripts for both platforms:

#### Linux/macOS

```bash
# Build for specific platform
./scripts/build-electron.sh win     # Windows only
./scripts/build-electron.sh mac     # macOS only
./scripts/build-electron.sh all     # All platforms

# Or use npm directly
npm run build:win
npm run build:mac
npm run build:all
```

#### Windows (PowerShell)

```powershell
# Prepare Python distribution
.\scripts\prepare-python-dist.ps1

# Build Electron app
npm run build:win
```

### Build Process

The build process consists of two phases:

1. **Python Distribution Preparation** (`scripts/prepare-python-dist.sh`)
   - Installs Python dependencies via UV
   - Copies source code and data files
   - Bundles virtual environment
   - Creates platform-specific startup scripts

2. **Electron Packaging** (via electron-builder)
   - Bundles Electron app
   - Includes Python distribution
   - Creates platform-specific installers
   - Signs and notarizes (if configured)

### Build Output

Build artifacts are created in the `dist/` directory:

**Windows:**
- `FinAgent-0.0.2-Setup.exe` - NSIS installer

**macOS:**
- `FinAgent-0.0.2-arm64.dmg` - Apple Silicon installer
- `FinAgent-0.0.2-x64.dmg` - Intel installer
- `FinAgent-0.0.2-arm64.zip` - Apple Silicon portable
- `FinAgent-0.0.2-x64.zip` - Intel portable

## Usage

### Starting the Application

**Development Mode:**
```bash
npm run dev
```

**Production (Installed App):**
- Windows: Launch from Start Menu or Desktop shortcut
- macOS: Launch from Applications folder

### Main Interface

The application consists of three main sections:

1. **Header**
   - Logo and application title
   - Backend connection status indicator
   - Green dot = Connected and ready
   - Gray dot = Connecting
   - Red dot = Connection error

2. **Query Section**
   - Text area for entering research queries in Traditional Chinese
   - Submit button (disabled until backend is ready)
   - Quick example queries for testing

3. **Results Section**
   - Welcome screen on first launch
   - Query results with formatted sections
   - Citations with source tracking
   - Confidence badges (高信心/中信心/低信心)

### Query Examples

Click on example queries or type your own:

- `玉山銀行洗錢防制裁罰` - AML penalties for E.SUN Bank
- `2020年金管會裁罰案件` - FSC enforcement actions in 2020
- `內線交易相關判決` - Insider trading case judgments

### Keyboard Shortcuts

- `Ctrl+Enter` (Windows) / `Cmd+Enter` (macOS) - Submit query
- Standard text editing shortcuts in query input

## Configuration

### Application Settings

Settings are stored in platform-specific locations:

- **Windows:** `%APPDATA%\finagent-desktop\`
- **macOS:** `~/Library/Application Support/finagent-desktop/`

### Python Backend Configuration

The Python backend uses the same configuration system as the CLI version:

1. `.env` file (bundled with the app)
2. SQLite database settings
3. `model_config.yml` for LLM presets

To modify configuration in production builds:

**Windows:**
```
C:\Users\[YourName]\AppData\Local\Programs\FinAgent\resources\python\.env
```

**macOS:**
```
/Applications/FinAgent.app/Contents/Resources/python/.env
```

### LLM Configuration

Support for multiple LLM providers:

**OpenAI (Default):**
```bash
LLM_API_KEY=sk-proj-xxx
LLM_BASE_URL=
LLM_MODEL=gpt-4o-mini
EMBEDDING_MODEL=text-embedding-3-small
```

**Ollama (Local):**
```bash
LLM_API_KEY=ollama
LLM_BASE_URL=http://localhost:11434/v1
LLM_MODEL=qwen2.5:7b
EMBEDDING_MODEL=bge-m3
```

## Troubleshooting

### Backend Not Starting

**Symptoms:** Red status indicator, "連接失敗" message

**Solutions:**

1. Check Python installation (bundled app should include this)
2. Verify port 8000 is not in use
3. Check logs:
   - Windows: `%USERPROFILE%\AppData\Roaming\finagent-desktop\logs\`
   - macOS: `~/Library/Logs/finagent-desktop/`

4. Try restarting the application

### Query Failures

**Symptoms:** Error message after submitting query

**Solutions:**

1. Verify backend status shows green
2. Check internet connection (for OpenAI API)
3. Verify API keys in configuration
4. Check vector DB is initialized (contains documents)

### Performance Issues

**Symptoms:** Slow query responses

**Solutions:**

1. First query is always slower (model loading)
2. Check system resources (RAM, CPU)
3. Consider using local LLM (Ollama) for better privacy and speed
4. Reduce document index size if needed

### Installation Issues

**Windows:**
- Run installer as Administrator if needed
- Check antivirus didn't quarantine files
- Verify minimum Windows 10 requirement

**macOS:**
- Check "Security & Privacy" settings if app won't open
- Run: `xattr -cr /Applications/FinAgent.app`
- Verify macOS 10.13+ requirement

## Development

### Project Structure

```
FinAgent/
├── electron/                    # Electron application
│   ├── main.js                 # Main process
│   ├── preload.js              # Preload script
│   ├── renderer/               # Renderer process
│   │   ├── index.html         # Main HTML
│   │   ├── styles/            # CSS stylesheets
│   │   │   └── main.css
│   │   └── js/                # JavaScript
│   │       └── app.js
│   └── build/                  # Build assets (icons)
├── src/finagent/               # Python backend
│   ├── api/                   # FastAPI routes
│   ├── agents/                # LangGraph agents
│   ├── document_processing/   # RAG pipeline
│   └── ...
├── scripts/                    # Build scripts
│   ├── build-electron.sh
│   ├── prepare-python-dist.sh
│   └── prepare-python-dist.ps1
├── package.json               # Node.js dependencies
├── pyproject.toml            # Python dependencies
└── README.md
```

### Adding Features

#### Frontend (Renderer)

1. Modify `electron/renderer/index.html` for UI changes
2. Update `electron/renderer/styles/main.css` for styling
3. Add logic in `electron/renderer/js/app.js`

#### Backend API

1. Add new routes in `src/finagent/api/routes/`
2. Expose via `window.electronAPI` in `electron/preload.js`
3. Add IPC handlers in `electron/main.js`

#### Main Process

1. Edit `electron/main.js` for window/subprocess management
2. Add IPC handlers for new features
3. Update security policies as needed

### Security Considerations

The application follows Electron security best practices:

- ✅ Context isolation enabled
- ✅ Node integration disabled in renderer
- ✅ Preload script for controlled API exposure
- ✅ Content Security Policy enforced
- ✅ Local-only backend (127.0.0.1)
- ✅ No remote module access

### Testing

**Python Backend:**
```bash
uv run pytest
```

**Electron App:**
```bash
# Manual testing
npm start

# Automated testing (future)
npm test
```

## Deployment

### Code Signing (Optional but Recommended)

#### Windows

1. Obtain a code signing certificate
2. Configure in `package.json`:
```json
"win": {
  "certificateFile": "path/to/cert.pfx",
  "certificatePassword": "password"
}
```

#### macOS

1. Join Apple Developer Program
2. Create signing certificates
3. Configure in `package.json`:
```json
"mac": {
  "identity": "Developer ID Application: Your Name (TEAM_ID)"
}
```

### Distribution

#### Direct Download
- Host installers on GitHub Releases
- Provide checksums for verification

#### Auto-Updates (Future)
- Configure electron-updater
- Host updates on S3 or GitHub

## Roadmap

### Planned Features (v0.0.3+)

- [ ] Auto-update functionality
- [ ] Multi-language support (English + 繁體中文)
- [ ] Query history panel
- [ ] Document management UI
- [ ] Configuration panel (avoid manual .env editing)
- [ ] Export results to PDF/Word
- [ ] Dark mode theme
- [ ] Windows ARM64 support
- [ ] Linux AppImage/Snap packages

### Known Limitations

1. **Platform Support:** Currently Windows and macOS only
2. **Configuration:** Requires manual .env editing
3. **Updates:** Manual download and reinstall
4. **Offline Mode:** Requires internet for OpenAI API

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Follow existing code style
4. Test on both platforms if possible
5. Submit a pull request

## License

[Add license information]

## Support

For issues and questions:
- GitHub Issues: https://github.com/p988744/FinAgent/issues
- Documentation: [docs/](docs/)

---

**Version:** 0.0.2
**Last Updated:** 2025-01-14
**Platform:** Windows 10+, macOS 10.13+
