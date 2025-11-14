#!/bin/bash
# Prepare Python distribution for bundling with Electron

set -e

echo "🐍 Preparing Python distribution for Electron packaging..."

# Create python-dist directory
rm -rf python-dist
mkdir -p python-dist

# Install Python dependencies using uv
echo "📦 Installing Python dependencies..."
uv sync --no-dev

# Copy source code
echo "📁 Copying source code..."
cp -r src python-dist/
cp -r data python-dist/
cp model_config.yml python-dist/
cp .env.example python-dist/.env

# Copy uv environment
echo "🔧 Copying UV environment..."
if [ -d ".venv" ]; then
    cp -r .venv python-dist/
fi

# Create startup script for different platforms
echo "📝 Creating startup scripts..."

# Windows startup script
cat > python-dist/start_server.bat << 'EOF'
@echo off
set PYTHONPATH=%~dp0
.venv\Scripts\python.exe -m uvicorn finagent.main:app --host 127.0.0.1 --port 8000
EOF

# macOS/Linux startup script
cat > python-dist/start_server.sh << 'EOF'
#!/bin/bash
export PYTHONPATH="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
.venv/bin/python -m uvicorn finagent.main:app --host 127.0.0.1 --port 8000
EOF

chmod +x python-dist/start_server.sh

echo "✅ Python distribution prepared successfully!"
echo "📂 Location: python-dist/"
