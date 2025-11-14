# Prepare Python distribution for bundling with Electron (Windows PowerShell)

Write-Host "🐍 Preparing Python distribution for Electron packaging..." -ForegroundColor Cyan

# Create python-dist directory
if (Test-Path python-dist) {
    Remove-Item -Recurse -Force python-dist
}
New-Item -ItemType Directory -Path python-dist | Out-Null

# Install Python dependencies using uv
Write-Host "📦 Installing Python dependencies..." -ForegroundColor Yellow
uv sync --no-dev

# Copy source code
Write-Host "📁 Copying source code..." -ForegroundColor Yellow
Copy-Item -Recurse src python-dist/
Copy-Item -Recurse data python-dist/
Copy-Item model_config.yml python-dist/
Copy-Item .env.example python-dist/.env

# Copy uv environment
Write-Host "🔧 Copying UV environment..." -ForegroundColor Yellow
if (Test-Path .venv) {
    Copy-Item -Recurse .venv python-dist/
}

# Create startup script
Write-Host "📝 Creating startup scripts..." -ForegroundColor Yellow

$batContent = @'
@echo off
set PYTHONPATH=%~dp0
.venv\Scripts\python.exe -m uvicorn finagent.main:app --host 127.0.0.1 --port 8000
'@

$batContent | Out-File -FilePath python-dist/start_server.bat -Encoding ASCII

Write-Host "✅ Python distribution prepared successfully!" -ForegroundColor Green
Write-Host "📂 Location: python-dist/" -ForegroundColor Green
