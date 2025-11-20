#!/bin/bash
# FinAgent Web UI v0.1.0-alpha.5 Validation Script
# This script validates that all alpha.5 deliverables are complete

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT"

PASS=0
FAIL=0

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "=========================================="
echo "FinAgent Web UI v0.1.0-alpha.5 Validation"
echo "=========================================="
echo ""

check() {
    local name="$1"
    local cmd="$2"

    if eval "$cmd" > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} $name"
        PASS=$((PASS + 1))
    else
        echo -e "${RED}✗${NC} $name"
        FAIL=$((FAIL + 1))
    fi
}

check_pattern() {
    local name="$1"
    local file="$2"
    local pattern="$3"

    if grep -q "$pattern" "$file" 2>/dev/null; then
        echo -e "${GREEN}✓${NC} $name"
        PASS=$((PASS + 1))
    else
        echo -e "${RED}✗${NC} $name"
        FAIL=$((FAIL + 1))
    fi
}

echo "=== Backend Documents API Checks ==="
echo ""

# Documents API endpoints
check "Documents route file exists" "test -f src/finagent/api/routes/documents.py"
check_pattern "POST /upload endpoint" "src/finagent/api/routes/documents.py" "async def upload_document"
check_pattern "GET / (list) endpoint" "src/finagent/api/routes/documents.py" "async def list_documents"
check_pattern "GET /status endpoint" "src/finagent/api/routes/documents.py" "async def get_index_status"
check_pattern "GET /{id} endpoint" "src/finagent/api/routes/documents.py" "async def get_document"
check_pattern "GET /{id}/content endpoint" "src/finagent/api/routes/documents.py" "async def get_document_content"
check_pattern "DELETE /{id} endpoint" "src/finagent/api/routes/documents.py" "async def delete_document"
check_pattern "POST /{id}/reindex endpoint" "src/finagent/api/routes/documents.py" "async def reindex_single_document"
check_pattern "POST /reindex-all endpoint" "src/finagent/api/routes/documents.py" "async def reindex_all_documents"
check_pattern "POST /{id}/versions endpoint" "src/finagent/api/routes/documents.py" "async def upload_new_version"
check_pattern "GET /{id}/versions endpoint" "src/finagent/api/routes/documents.py" "async def get_version_history"

# Integration with existing services
check_pattern "Uses DocumentMetadataStore" "src/finagent/api/routes/documents.py" "DocumentMetadataStore"
check_pattern "Uses DocumentIndexer" "src/finagent/api/routes/documents.py" "DocumentIndexer"
check_pattern "Uses DocumentLoader" "src/finagent/api/routes/documents.py" "DocumentLoader"
check_pattern "Uses ChineseTextChunker" "src/finagent/api/routes/documents.py" "ChineseTextChunker"
check_pattern "File upload with UploadFile" "src/finagent/api/routes/documents.py" "UploadFile"
check_pattern "Version tracking" "src/finagent/api/routes/documents.py" "_document_versions"

# Pydantic models
check_pattern "DocumentResponse class" "src/finagent/api/routes/documents.py" "class DocumentResponse"
check_pattern "DocumentVersion class" "src/finagent/api/routes/documents.py" "class DocumentVersion"
check_pattern "IndexStatus class" "src/finagent/api/routes/documents.py" "class IndexStatus"
check_pattern "ReindexProgress class" "src/finagent/api/routes/documents.py" "class ReindexProgress"

# Backend imports
check "Backend documents API imports successfully" "uv run python -c 'from finagent.api.routes.documents import router'"

echo ""
echo "=== Frontend Documents Components ==="
echo ""

# TypeScript types
check "Documents types file exists" "test -f frontend/src/types/documents.ts"
check_pattern "DocumentResponse interface" "frontend/src/types/documents.ts" "interface DocumentResponse"
check_pattern "DocumentVersion interface" "frontend/src/types/documents.ts" "interface DocumentVersion"
check_pattern "IndexStatus interface" "frontend/src/types/documents.ts" "interface IndexStatus"
check_pattern "ReindexProgress interface" "frontend/src/types/documents.ts" "interface ReindexProgress"
check_pattern "DocumentContent interface" "frontend/src/types/documents.ts" "interface DocumentContent"

# UI Components
check "DocumentUpload component exists" "test -f frontend/src/components/documents/DocumentUpload.tsx"
check "DocumentList component exists" "test -f frontend/src/components/documents/DocumentList.tsx"
check "IndexStatusCard component exists" "test -f frontend/src/components/documents/IndexStatusCard.tsx"
check "VersionHistoryModal component exists" "test -f frontend/src/components/documents/VersionHistoryModal.tsx"
check "ContentViewerModal component exists" "test -f frontend/src/components/documents/ContentViewerModal.tsx"

# DocumentUpload features
check_pattern "DocumentUpload drag and drop" "frontend/src/components/documents/DocumentUpload.tsx" "handleDrop"
check_pattern "DocumentUpload file validation" "frontend/src/components/documents/DocumentUpload.tsx" "\.txt"
check_pattern "DocumentUpload loading state" "frontend/src/components/documents/DocumentUpload.tsx" "isUploading"

# DocumentList features
check_pattern "DocumentList shows documents" "frontend/src/components/documents/DocumentList.tsx" "documents.map"
check_pattern "DocumentList status badges" "frontend/src/components/documents/DocumentList.tsx" "getStatusBadge"
check_pattern "DocumentList delete button" "frontend/src/components/documents/DocumentList.tsx" "onDelete"
check_pattern "DocumentList reindex button" "frontend/src/components/documents/DocumentList.tsx" "onReindex"
check_pattern "DocumentList version display" "frontend/src/components/documents/DocumentList.tsx" "doc.version"
check_pattern "DocumentList chunk count" "frontend/src/components/documents/DocumentList.tsx" "chunk_count"

# IndexStatusCard features
check_pattern "IndexStatusCard shows total documents" "frontend/src/components/documents/IndexStatusCard.tsx" "total_documents"
check_pattern "IndexStatusCard shows indexed count" "frontend/src/components/documents/IndexStatusCard.tsx" "indexed_documents"
check_pattern "IndexStatusCard shows pending count" "frontend/src/components/documents/IndexStatusCard.tsx" "pending_documents"
check_pattern "IndexStatusCard shows total chunks" "frontend/src/components/documents/IndexStatusCard.tsx" "total_chunks"
check_pattern "IndexStatusCard reindex all button" "frontend/src/components/documents/IndexStatusCard.tsx" "onReindexAll"

# VersionHistoryModal features
check_pattern "VersionHistoryModal shows versions" "frontend/src/components/documents/VersionHistoryModal.tsx" "versions.map"
check_pattern "VersionHistoryModal upload new version" "frontend/src/components/documents/VersionHistoryModal.tsx" "onUploadNewVersion"

# ContentViewerModal features
check_pattern "ContentViewerModal shows content" "frontend/src/components/documents/ContentViewerModal.tsx" "content.content"
check_pattern "ContentViewerModal shows size" "frontend/src/components/documents/ContentViewerModal.tsx" "size_chars"

# DocumentsPage integration
check_pattern "DocumentsPage uses DocumentUpload" "frontend/src/pages/DocumentsPage.tsx" "<DocumentUpload"
check_pattern "DocumentsPage uses DocumentList" "frontend/src/pages/DocumentsPage.tsx" "<DocumentList"
check_pattern "DocumentsPage uses IndexStatusCard" "frontend/src/pages/DocumentsPage.tsx" "<IndexStatusCard"
check_pattern "DocumentsPage uses VersionHistoryModal" "frontend/src/pages/DocumentsPage.tsx" "<VersionHistoryModal"
check_pattern "DocumentsPage uses ContentViewerModal" "frontend/src/pages/DocumentsPage.tsx" "<ContentViewerModal"
check_pattern "DocumentsPage fetches documents" "frontend/src/pages/DocumentsPage.tsx" "fetch.*API_BASE"
check_pattern "DocumentsPage fetches status" "frontend/src/pages/DocumentsPage.tsx" "fetchIndexStatus"
check_pattern "DocumentsPage handles upload" "frontend/src/pages/DocumentsPage.tsx" "handleUpload"
check_pattern "DocumentsPage handles delete" "frontend/src/pages/DocumentsPage.tsx" "handleDelete"
check_pattern "DocumentsPage handles reindex" "frontend/src/pages/DocumentsPage.tsx" "handleReindex"
check_pattern "DocumentsPage handles reindex all" "frontend/src/pages/DocumentsPage.tsx" "handleReindexAll"
check_pattern "DocumentsPage handles view content" "frontend/src/pages/DocumentsPage.tsx" "handleViewContent"
check_pattern "DocumentsPage handles view versions" "frontend/src/pages/DocumentsPage.tsx" "handleViewVersions"
check_pattern "DocumentsPage handles upload new version" "frontend/src/pages/DocumentsPage.tsx" "handleUploadNewVersion"
check_pattern "DocumentsPage shows success messages" "frontend/src/pages/DocumentsPage.tsx" "showSuccess"
check_pattern "DocumentsPage shows error messages" "frontend/src/pages/DocumentsPage.tsx" "showError"

echo ""
echo "=== Build and Compile Checks ==="
echo ""

check "Frontend builds successfully" "npm --prefix frontend run build"
check "TypeScript compilation passes" "cd frontend && npx tsc --noEmit"

echo ""
echo "=========================================="
echo "VALIDATION SUMMARY"
echo "=========================================="
echo ""
echo -e "Passed: ${GREEN}$PASS${NC}"
echo -e "Failed: ${RED}$FAIL${NC}"
TOTAL=$((PASS + FAIL))
echo "Total:  $TOTAL"
echo ""

if [ $FAIL -eq 0 ]; then
    echo -e "${GREEN}✓ All alpha.5 validations passed!${NC}"
    echo ""
    echo "Next steps:"
    echo "1. Test with actual backend (uv run uvicorn finagent.main:app)"
    echo "2. Manual E2E testing:"
    echo "   - Upload a .txt document"
    echo "   - View document in list with metadata"
    echo "   - Check index status card"
    echo "   - View document content"
    echo "   - Reindex single document"
    echo "   - Reindex all documents"
    echo "   - View version history"
    echo "   - Upload new version"
    echo "   - Delete document with confirmation"
    echo "3. Commit changes to feature/web-ui-alpha.5 branch"
    echo "4. Create PR to develop branch"
    echo "5. Tag as v0.1.0-alpha.5"
    echo "6. Begin alpha.6 implementation"
    exit 0
else
    echo -e "${RED}✗ $FAIL validation(s) failed${NC}"
    echo ""
    echo "Please fix the failing checks before proceeding."
    exit 1
fi
