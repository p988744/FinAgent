#!/bin/bash
# FinAgent Web UI Version Validator
# Usage: ./scripts/validate.sh <version>
# Example: ./scripts/validate.sh v0.1.0-alpha.1

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

if [ -z "$1" ]; then
    echo -e "${YELLOW}Usage: ./scripts/validate.sh <version>${NC}"
    echo ""
    echo "Available versions:"
    ls -1 scripts/validate_v*.sh 2>/dev/null | sed 's/scripts\/validate_/  /g' | sed 's/\.sh//g'
    echo ""
    echo "Example:"
    echo "  ./scripts/validate.sh v0.1.0-alpha.1"
    exit 1
fi

VERSION=$1
SCRIPT="./scripts/validate_${VERSION}.sh"

if [ ! -f "$SCRIPT" ]; then
    echo -e "${RED}Error: Validation script not found: $SCRIPT${NC}"
    echo ""
    echo "Available validation scripts:"
    ls -1 scripts/validate_v*.sh 2>/dev/null | sed 's/scripts\/validate_/  /g' | sed 's/\.sh//g'
    exit 1
fi

chmod +x "$SCRIPT"

echo -e "${GREEN}Running validation for ${VERSION}...${NC}"
echo ""

exec "$SCRIPT"
