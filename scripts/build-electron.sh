#!/bin/bash
# Build Electron application for cross-platform distribution

set -e

echo "🚀 Building FinAgent Electron Application..."

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js first."
    exit 1
fi

# Check if npm is installed
if ! command -v npm &> /dev/null; then
    echo "❌ npm is not installed. Please install npm first."
    exit 1
fi

# Install npm dependencies
echo "📦 Installing npm dependencies..."
npm install

# Prepare Python distribution
echo "🐍 Preparing Python distribution..."
./scripts/prepare-python-dist.sh

# Build Electron app
echo "🔨 Building Electron application..."

# Check for platform argument
PLATFORM=${1:-all}

case $PLATFORM in
    win|windows)
        echo "Building for Windows..."
        npm run build:win
        ;;
    mac|macos)
        echo "Building for macOS..."
        npm run build:mac
        ;;
    all)
        echo "Building for all platforms..."
        npm run build:all
        ;;
    *)
        echo "❌ Unknown platform: $PLATFORM"
        echo "Usage: ./scripts/build-electron.sh [win|mac|all]"
        exit 1
        ;;
esac

echo ""
echo "✅ Build complete!"
echo "📂 Distribution files are in: dist/"
echo ""
echo "To test the application, run:"
echo "  npm start"
