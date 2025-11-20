#!/bin/bash

# ================================================
# Wiki E2E Test Suite
# ================================================
# Tests all Wiki functionality and collects expected behaviors
# Date: 2025-11-20
# ================================================

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test counters
TESTS_PASSED=0
TESTS_FAILED=0

# API Base URL
API_BASE="http://localhost:8000/api/v1"

# Helper functions
print_header() {
    echo ""
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""
}

print_test() {
    echo -e "${YELLOW}TEST:${NC} $1"
}

print_pass() {
    echo -e "${GREEN}✅ PASS:${NC} $1"
    ((TESTS_PASSED++))
}

print_fail() {
    echo -e "${RED}❌ FAIL:${NC} $1"
    ((TESTS_FAILED++))
}

print_expected() {
    echo -e "${BLUE}📋 Expected:${NC} $1"
}

print_actual() {
    echo -e "${BLUE}📝 Actual:${NC} $1"
}

# Check if services are running
check_services() {
    print_header "Checking Services"

    # Check backend
    if curl -s -f "$API_BASE/wiki/overview" > /dev/null 2>&1; then
        print_pass "Backend is running on port 8000"
    else
        print_fail "Backend is NOT running on port 8000"
        echo "Please start the backend with: uv run uvicorn finagent.main:app --reload --port 8000"
        exit 1
    fi

    # Check frontend
    FRONTEND_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:5173")
    if [ "$FRONTEND_STATUS" -eq 200 ]; then
        print_pass "Frontend is running on port 5173"
    else
        print_fail "Frontend is NOT running on port 5173 (status: $FRONTEND_STATUS)"
        echo "Please start the frontend with: cd frontend && npm run dev"
        exit 1
    fi
}

# Test 1: Wiki Overview Endpoint
test_wiki_overview() {
    print_header "Test 1: Wiki Overview Endpoint"

    print_test "GET /api/v1/wiki/overview"
    RESPONSE=$(curl -s "$API_BASE/wiki/overview")

    # Check response structure
    TOTAL_DOCS=$(echo "$RESPONSE" | jq -r '.total_documents')
    TOTAL_CATS=$(echo "$RESPONSE" | jq -r '.total_categories')
    WITH_META=$(echo "$RESPONSE" | jq -r '.document_stats.with_metadata')
    AVG_CONF=$(echo "$RESPONSE" | jq -r '.document_stats.avg_confidence')

    print_expected "Response contains: total_documents, total_categories, document_stats, top_entities"
    print_actual "total_documents=$TOTAL_DOCS, total_categories=$TOTAL_CATS, with_metadata=$WITH_META, avg_confidence=$AVG_CONF"

    if [[ "$TOTAL_DOCS" =~ ^[0-9]+$ ]] && [ "$TOTAL_DOCS" -gt 0 ]; then
        print_pass "Total documents: $TOTAL_DOCS"
    else
        print_fail "Invalid total_documents: $TOTAL_DOCS"
    fi

    if [[ "$TOTAL_CATS" =~ ^[0-9]+$ ]] && [ "$TOTAL_CATS" -gt 0 ]; then
        print_pass "Total categories: $TOTAL_CATS"
    else
        print_fail "Invalid total_categories: $TOTAL_CATS"
    fi

    # Check top entities
    TOP_INST_COUNT=$(echo "$RESPONSE" | jq -r '.top_entities.institutions | length')
    TOP_VIOL_COUNT=$(echo "$RESPONSE" | jq -r '.top_entities.violations | length')
    TOP_AUTH_COUNT=$(echo "$RESPONSE" | jq -r '.top_entities.authorities | length')

    print_expected "Top entities should have institutions, violations, and authorities"
    print_actual "institutions=$TOP_INST_COUNT, violations=$TOP_VIOL_COUNT, authorities=$TOP_AUTH_COUNT"

    if [ "$TOP_INST_COUNT" -gt 0 ] && [ "$TOP_VIOL_COUNT" -gt 0 ] && [ "$TOP_AUTH_COUNT" -gt 0 ]; then
        print_pass "Top entities populated correctly"
    else
        print_fail "Top entities missing data"
    fi

    # Show sample top entity
    echo ""
    echo "Sample Top Institution:"
    echo "$RESPONSE" | jq -r '.top_entities.institutions[0] | "  - \(.name): \(.count) documents (\(.percentage)%)"'
    echo ""
}

# Test 2: Categories Endpoint
test_wiki_categories() {
    print_header "Test 2: Wiki Categories Endpoint"

    # Test each category type
    for TYPE in "authority" "institution" "violation" "doc_type"; do
        print_test "GET /api/v1/wiki/categories?type=$TYPE"

        RESPONSE=$(curl -s "$API_BASE/wiki/categories?type=$TYPE")

        CATEGORY_TYPE=$(echo "$RESPONSE" | jq -r '.category_type')
        TOTAL_COUNT=$(echo "$RESPONSE" | jq -r '.total_count')
        CATEGORIES_COUNT=$(echo "$RESPONSE" | jq -r '.categories | length')

        print_expected "category_type=$TYPE, total_count>0, categories array present"
        print_actual "category_type=$CATEGORY_TYPE, total_count=$TOTAL_COUNT, categories_count=$CATEGORIES_COUNT"

        if [ "$CATEGORY_TYPE" = "$TYPE" ] && [ "$TOTAL_COUNT" -gt 0 ] && [ "$CATEGORIES_COUNT" -gt 0 ]; then
            print_pass "Category type '$TYPE': $TOTAL_COUNT total, $CATEGORIES_COUNT returned"
        else
            print_fail "Category type '$TYPE' returned invalid data"
        fi

        # Show sample category
        if [ "$CATEGORIES_COUNT" -gt 0 ]; then
            echo ""
            echo "Sample category:"
            echo "$RESPONSE" | jq -r '.categories[0] | "  - ID: \(.id), Name: \(.name), Docs: \(.document_count), Keywords: \(.keywords[:3] | join(", "))"'
            echo ""
        fi
    done
}

# Test 3: Documents Listing Endpoint
test_wiki_documents() {
    print_header "Test 3: Wiki Documents Listing Endpoint"

    # Test 3.1: All documents
    print_test "GET /api/v1/wiki/documents (all documents)"

    RESPONSE=$(curl -s "$API_BASE/wiki/documents?limit=10&offset=0")

    TOTAL=$(echo "$RESPONSE" | jq -r '.total')
    LIMIT=$(echo "$RESPONSE" | jq -r '.limit')
    OFFSET=$(echo "$RESPONSE" | jq -r '.offset')
    DOCS_COUNT=$(echo "$RESPONSE" | jq -r '.documents | length')

    print_expected "total>0, limit=10, offset=0, documents array present"
    print_actual "total=$TOTAL, limit=$LIMIT, offset=$OFFSET, documents_count=$DOCS_COUNT"

    if [ "$TOTAL" -gt 0 ] && [ "$LIMIT" -eq 10 ] && [ "$OFFSET" -eq 0 ] && [ "$DOCS_COUNT" -gt 0 ]; then
        print_pass "All documents: total=$TOTAL, returned=$DOCS_COUNT"
    else
        print_fail "All documents returned invalid data"
    fi

    # Check document structure
    if [ "$DOCS_COUNT" -gt 0 ]; then
        DOC_ID=$(echo "$RESPONSE" | jq -r '.documents[0].doc_id')
        FILENAME=$(echo "$RESPONSE" | jq -r '.documents[0].filename')
        DOC_TYPE=$(echo "$RESPONSE" | jq -r '.documents[0].document_type')

        echo ""
        echo "Sample document:"
        echo "  - doc_id: $DOC_ID"
        echo "  - filename: $FILENAME"
        echo "  - document_type: $DOC_TYPE"
        echo ""

        # Save first doc_id for later tests
        FIRST_DOC_ID="$DOC_ID"
    fi

    # Test 3.2: Filtered by category
    print_test "GET /api/v1/wiki/documents?category_id=1 (filtered)"

    # Get a real category ID first
    CATEGORY_RESPONSE=$(curl -s "$API_BASE/wiki/categories?type=authority")
    FIRST_CAT_ID=$(echo "$CATEGORY_RESPONSE" | jq -r '.categories[0].id')
    FIRST_CAT_NAME=$(echo "$CATEGORY_RESPONSE" | jq -r '.categories[0].name')

    RESPONSE=$(curl -s "$API_BASE/wiki/documents?category_id=$FIRST_CAT_ID&limit=10&offset=0")

    FILTERED_TOTAL=$(echo "$RESPONSE" | jq -r '.total')
    FILTERED_COUNT=$(echo "$RESPONSE" | jq -r '.documents | length')

    print_expected "Filtered results for category '$FIRST_CAT_NAME'"
    print_actual "total=$FILTERED_TOTAL, documents_count=$FILTERED_COUNT"

    if [ "$FILTERED_TOTAL" -ge 0 ] && [ "$FILTERED_COUNT" -ge 0 ]; then
        print_pass "Filtered documents: category='$FIRST_CAT_NAME', total=$FILTERED_TOTAL"
    else
        print_fail "Filtered documents returned invalid data"
    fi

    # Test 3.3: Pagination
    print_test "GET /api/v1/wiki/documents?limit=5&offset=5 (pagination)"

    RESPONSE=$(curl -s "$API_BASE/wiki/documents?limit=5&offset=5")

    PAGE_LIMIT=$(echo "$RESPONSE" | jq -r '.limit')
    PAGE_OFFSET=$(echo "$RESPONSE" | jq -r '.offset')
    PAGE_DOCS_COUNT=$(echo "$RESPONSE" | jq -r '.documents | length')

    print_expected "limit=5, offset=5, documents array"
    print_actual "limit=$PAGE_LIMIT, offset=$PAGE_OFFSET, documents_count=$PAGE_DOCS_COUNT"

    if [ "$PAGE_LIMIT" -eq 5 ] && [ "$PAGE_OFFSET" -eq 5 ]; then
        print_pass "Pagination works correctly"
    else
        print_fail "Pagination returned incorrect limit/offset"
    fi
}

# Test 4: Document Detail Endpoint
test_wiki_document_detail() {
    print_header "Test 4: Wiki Document Detail Endpoint"

    # Get a document ID first
    RESPONSE=$(curl -s "$API_BASE/wiki/documents?limit=1&offset=0")
    DOC_ID=$(echo "$RESPONSE" | jq -r '.documents[0].doc_id')

    if [ -z "$DOC_ID" ] || [ "$DOC_ID" = "null" ]; then
        print_fail "No documents available for testing"
        return
    fi

    # Test 4.1: Document without content
    print_test "GET /api/v1/wiki/document/$DOC_ID?include_content=false"

    DETAIL_RESPONSE=$(curl -s "$API_BASE/wiki/document/$DOC_ID?include_content=false")

    DETAIL_DOC_ID=$(echo "$DETAIL_RESPONSE" | jq -r '.doc_id')
    DETAIL_FILENAME=$(echo "$DETAIL_RESPONSE" | jq -r '.filename')
    DETAIL_CONTENT=$(echo "$DETAIL_RESPONSE" | jq -r '.full_content')

    print_expected "doc_id=$DOC_ID, filename present, full_content=null"
    print_actual "doc_id=$DETAIL_DOC_ID, filename=$DETAIL_FILENAME, full_content=$DETAIL_CONTENT"

    if [ "$DETAIL_DOC_ID" = "$DOC_ID" ] && [ "$DETAIL_CONTENT" = "null" ]; then
        print_pass "Document detail (without content) works correctly"
    else
        print_fail "Document detail (without content) returned unexpected data"
    fi

    # Test 4.2: Document with content
    print_test "GET /api/v1/wiki/document/$DOC_ID?include_content=true"

    CONTENT_RESPONSE=$(curl -s "$API_BASE/wiki/document/$DOC_ID?include_content=true")

    CONTENT_DOC_ID=$(echo "$CONTENT_RESPONSE" | jq -r '.doc_id')
    CONTENT_TEXT=$(echo "$CONTENT_RESPONSE" | jq -r '.full_content')
    CONTENT_LENGTH=$(echo "$CONTENT_TEXT" | wc -c)

    print_expected "doc_id=$DOC_ID, full_content present and not null"
    print_actual "doc_id=$CONTENT_DOC_ID, content_length=$CONTENT_LENGTH chars"

    if [ "$CONTENT_DOC_ID" = "$DOC_ID" ] && [ "$CONTENT_TEXT" != "null" ] && [ "$CONTENT_LENGTH" -gt 0 ]; then
        print_pass "Document detail (with content) works correctly"
        echo ""
        echo "Content preview (first 200 chars):"
        echo "$CONTENT_TEXT" | head -c 200
        echo "..."
        echo ""
    else
        print_fail "Document detail (with content) returned no content"
    fi
}

# Test 5: Metadata Quality
test_metadata_quality() {
    print_header "Test 5: Metadata Extraction Quality"

    # Get documents with metadata
    RESPONSE=$(curl -s "$API_BASE/wiki/documents?limit=20&offset=0")
    DOCS_WITH_TYPE=$(echo "$RESPONSE" | jq -r '[.documents[] | select(.document_type != null)] | length')
    DOCS_WITH_AUTHORITY=$(echo "$RESPONSE" | jq -r '[.documents[] | select(.issuing_authority != null)] | length')
    DOCS_WITH_DATE=$(echo "$RESPONSE" | jq -r '[.documents[] | select(.date != null)] | length')
    DOCS_WITH_INSTITUTIONS=$(echo "$RESPONSE" | jq -r '[.documents[] | select(.related_institutions | length > 0)] | length')
    DOCS_WITH_VIOLATIONS=$(echo "$RESPONSE" | jq -r '[.documents[] | select(.violation_types | length > 0)] | length')
    TOTAL_SAMPLE=$(echo "$RESPONSE" | jq -r '.documents | length')

    print_expected "High percentage of documents should have extracted metadata"
    print_actual "Sample size: $TOTAL_SAMPLE documents"
    echo "  - With document_type: $DOCS_WITH_TYPE ($(echo "scale=1; $DOCS_WITH_TYPE * 100 / $TOTAL_SAMPLE" | bc)%)"
    echo "  - With issuing_authority: $DOCS_WITH_AUTHORITY ($(echo "scale=1; $DOCS_WITH_AUTHORITY * 100 / $TOTAL_SAMPLE" | bc)%)"
    echo "  - With date: $DOCS_WITH_DATE ($(echo "scale=1; $DOCS_WITH_DATE * 100 / $TOTAL_SAMPLE" | bc)%)"
    echo "  - With institutions: $DOCS_WITH_INSTITUTIONS ($(echo "scale=1; $DOCS_WITH_INSTITUTIONS * 100 / $TOTAL_SAMPLE" | bc)%)"
    echo "  - With violations: $DOCS_WITH_VIOLATIONS ($(echo "scale=1; $DOCS_WITH_VIOLATIONS * 100 / $TOTAL_SAMPLE" | bc)%)"

    # Consider metadata quality good if >50% have key fields
    if [ "$DOCS_WITH_TYPE" -gt "$((TOTAL_SAMPLE / 2))" ] && [ "$DOCS_WITH_INSTITUTIONS" -gt 0 ]; then
        print_pass "Metadata extraction quality is good"
    else
        print_fail "Metadata extraction quality needs improvement"
    fi

    # Show a well-extracted document example
    echo ""
    echo "Example well-extracted document:"
    echo "$RESPONSE" | jq -r '.documents[] | select(.document_type != null and (.related_institutions | length > 0)) | "\n  Filename: \(.filename)\n  Type: \(.document_type)\n  Authority: \(.issuing_authority // "N/A")\n  Date: \(.date // "N/A")\n  Institutions: \(.related_institutions | join(", "))\n  Violations: \(.violation_types | join(", "))\n  Confidence: \(.extraction_confidence * 100 | floor)%" | .[0:500]' | head -20
}

# Test 6: Confidence Scores
test_confidence_scores() {
    print_header "Test 6: Extraction Confidence Scores"

    RESPONSE=$(curl -s "$API_BASE/wiki/documents?limit=50&offset=0")

    HIGH_CONF=$(echo "$RESPONSE" | jq -r '[.documents[] | select(.extraction_confidence >= 0.8)] | length')
    MED_CONF=$(echo "$RESPONSE" | jq -r '[.documents[] | select(.extraction_confidence >= 0.5 and .extraction_confidence < 0.8)] | length')
    LOW_CONF=$(echo "$RESPONSE" | jq -r '[.documents[] | select(.extraction_confidence < 0.5)] | length')
    NO_CONF=$(echo "$RESPONSE" | jq -r '[.documents[] | select(.extraction_confidence == null)] | length')
    TOTAL_SAMPLE=$(echo "$RESPONSE" | jq -r '.documents | length')

    print_expected "Distribution of confidence scores across documents"
    print_actual "Sample size: $TOTAL_SAMPLE documents"
    echo "  - High confidence (≥0.8): $HIGH_CONF"
    echo "  - Medium confidence (0.5-0.8): $MED_CONF"
    echo "  - Low confidence (<0.5): $LOW_CONF"
    echo "  - No confidence score: $NO_CONF"

    if [ "$HIGH_CONF" -gt 0 ] || [ "$MED_CONF" -gt 0 ]; then
        print_pass "Confidence scores are being calculated"
    else
        print_fail "No confidence scores found"
    fi

    # Calculate average confidence
    AVG_CONF=$(echo "$RESPONSE" | jq -r '[.documents[].extraction_confidence | select(. != null)] | add / length')
    echo ""
    echo "Average confidence score: $(echo "scale=2; $AVG_CONF * 100" | bc)%"
    echo ""
}

# Test 7: Frontend Integration (Basic)
test_frontend_access() {
    print_header "Test 7: Frontend Page Access"

    # Test main page
    print_test "GET http://localhost:5173/ (Frontend homepage)"

    HOMEPAGE_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:5173/")

    print_expected "HTTP 200 OK"
    print_actual "HTTP $HOMEPAGE_STATUS"

    if [ "$HOMEPAGE_STATUS" -eq 200 ]; then
        print_pass "Frontend homepage accessible"
    else
        print_fail "Frontend homepage returned status $HOMEPAGE_STATUS"
    fi

    # Note: We can't test React Router routes via curl since they're client-side
    echo ""
    echo "📝 Note: Full frontend routing test requires browser/Playwright"
    echo "   Manual test: Open http://localhost:5173/wiki in browser"
    echo ""
}

# Main execution
main() {
    print_header "Wiki E2E Test Suite - Started"
    echo "Testing all Wiki functionality and collecting expected behaviors"
    echo "Date: $(date)"
    echo ""

    # Run all tests
    check_services
    test_wiki_overview
    test_wiki_categories
    test_wiki_documents
    test_wiki_document_detail
    test_metadata_quality
    test_confidence_scores
    test_frontend_access

    # Print summary
    print_header "Test Summary"
    echo -e "${GREEN}Tests Passed: $TESTS_PASSED${NC}"
    echo -e "${RED}Tests Failed: $TESTS_FAILED${NC}"
    echo ""

    TOTAL_TESTS=$((TESTS_PASSED + TESTS_FAILED))
    if [ $TOTAL_TESTS -gt 0 ]; then
        SUCCESS_RATE=$(echo "scale=1; $TESTS_PASSED * 100 / $TOTAL_TESTS" | bc)
        echo "Success Rate: ${SUCCESS_RATE}%"
    fi

    echo ""
    if [ $TESTS_FAILED -eq 0 ]; then
        echo -e "${GREEN}🎉 All tests passed!${NC}"
        exit 0
    else
        echo -e "${RED}⚠️  Some tests failed. Please review the output above.${NC}"
        exit 1
    fi
}

# Run main function
main
