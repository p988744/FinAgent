#!/bin/bash
set -e

echo "=========================================="
echo "E2E Test: Duplicate Document Handling"
echo "=========================================="
echo ""

# Clean up previous test files
echo "Step 1: Cleaning up previous test files..."
rm -f data/documents/test_duplicate*.txt
echo "✅ Cleanup complete"
echo ""

# Create a test file in /tmp (not in documents directory)
TEST_FILE="/tmp/test_duplicate.txt"
cat > "$TEST_FILE" << 'EOF'
金融監督管理委員會 裁罰書

受處分人：測試銀行股份有限公司
案號：金管銀法字第1234567890號
裁罰日期：民國113年11月19日

違規事實：
測試用違規內容

裁罰內容：
罰鍰新臺幣100萬元整
EOF

echo "Step 2: Test file created at: $TEST_FILE"
echo ""

# Upload the same file 4 times
echo "Step 3: Uploading the same file 4 times..."
echo ""

declare -a JOB_IDS=()
declare -a DOC_IDS=()
declare -a FILENAMES=()

for i in {1..4}; do
  echo "Upload #$i:"

  # Upload file
  RESPONSE=$(curl -s -X POST http://localhost:8000/api/v1/documents/upload-with-progress \
    -F "file=@$TEST_FILE" \
    -F "auto_index=false" \
    -F "extract_metadata=false")

  JOB_ID=$(echo "$RESPONSE" | jq -r '.job_id')
  JOB_IDS+=("$JOB_ID")

  echo "  Job ID: $JOB_ID"

  # Wait for upload to complete
  sleep 3

  # Get upload progress
  PROGRESS=$(curl -s "http://localhost:8000/api/v1/documents/upload-progress/$JOB_ID")

  FILENAME=$(echo "$PROGRESS" | jq -r '.filename')
  STAGE=$(echo "$PROGRESS" | jq -r '.stage')
  DOC_ID=$(echo "$PROGRESS" | jq -r '.document_id')

  FILENAMES+=("$FILENAME")
  DOC_IDS+=("$DOC_ID")

  echo "  Filename: $FILENAME"
  echo "  Stage: $STAGE"
  echo "  Doc ID: $DOC_ID"

  if [ "$STAGE" != "complete" ]; then
    echo "  ❌ Upload not complete! Stage: $STAGE"
    exit 1
  fi

  echo "  ✅ Upload complete"
  echo ""
done

# Verify files on disk
echo "Step 4: Verifying files on disk..."
echo ""

echo "Expected files:"
echo "  1. test_duplicate.txt (original)"
echo "  2. test_duplicate_v1.txt"
echo "  3. test_duplicate_v2.txt"
echo "  4. test_duplicate_v3.txt"
echo ""

echo "Actual files:"
ls -1 data/documents/test_duplicate*.txt | sort

echo ""

FILE_COUNT=$(ls -1 data/documents/test_duplicate*.txt 2>/dev/null | wc -l | tr -d ' ')

if [ "$FILE_COUNT" -ne 4 ]; then
  echo "❌ Expected 4 files, found $FILE_COUNT"
  exit 1
fi

echo "✅ File count correct: 4 files"
echo ""

# Check file naming
echo "Step 5: Verifying file naming pattern..."
echo ""

if [ ! -f "data/documents/test_duplicate.txt" ]; then
  echo "❌ Original file not found: test_duplicate.txt"
  exit 1
fi
echo "✅ Original file exists: test_duplicate.txt"

if [ ! -f "data/documents/test_duplicate_v1.txt" ]; then
  echo "❌ Version 1 not found: test_duplicate_v1.txt"
  exit 1
fi
echo "✅ Version 1 exists: test_duplicate_v1.txt"

if [ ! -f "data/documents/test_duplicate_v2.txt" ]; then
  echo "❌ Version 2 not found: test_duplicate_v2.txt"
  exit 1
fi
echo "✅ Version 2 exists: test_duplicate_v2.txt"

if [ ! -f "data/documents/test_duplicate_v3.txt" ]; then
  echo "❌ Version 3 not found: test_duplicate_v3.txt"
  exit 1
fi
echo "✅ Version 3 exists: test_duplicate_v3.txt"

echo ""

# Verify database entries
echo "Step 6: Verifying database entries..."
echo ""

for i in {0..3}; do
  DOC_ID="${DOC_IDS[$i]}"
  EXPECTED_FILENAME="${FILENAMES[$i]}"

  echo "Document #$((i+1)): $DOC_ID"

  # Query database
  DB_FILENAME=$(sqlite3 data/finagent.db "SELECT filename FROM documents WHERE doc_id='$DOC_ID';")

  if [ "$DB_FILENAME" != "$EXPECTED_FILENAME" ]; then
    echo "  ❌ Filename mismatch!"
    echo "     Expected: $EXPECTED_FILENAME"
    echo "     Found: $DB_FILENAME"
    exit 1
  fi

  echo "  Filename: $DB_FILENAME"
  echo "  ✅ Database entry correct"
  echo ""
done

# Verify content is identical
echo "Step 7: Verifying all files have identical content..."
echo ""

ORIGINAL_HASH=$(md5 -q "data/documents/test_duplicate.txt")
V1_HASH=$(md5 -q "data/documents/test_duplicate_v1.txt")
V2_HASH=$(md5 -q "data/documents/test_duplicate_v2.txt")
V3_HASH=$(md5 -q "data/documents/test_duplicate_v3.txt")

echo "File hashes:"
echo "  Original: $ORIGINAL_HASH"
echo "  Version 1: $V1_HASH"
echo "  Version 2: $V2_HASH"
echo "  Version 3: $V3_HASH"
echo ""

if [ "$ORIGINAL_HASH" != "$V1_HASH" ] || [ "$ORIGINAL_HASH" != "$V2_HASH" ] || [ "$ORIGINAL_HASH" != "$V3_HASH" ]; then
  echo "❌ File contents are not identical!"
  exit 1
fi

echo "✅ All files have identical content"
echo ""

# Test edge case: upload with different content but same name
echo "Step 8: Testing different content with same filename..."
echo ""

# Modify the test file
cat > "$TEST_FILE" << 'EOF'
金融監督管理委員會 裁罰書

受處分人：測試銀行股份有限公司（修改版）
案號：金管銀法字第9999999999號
裁罰日期：民國113年11月19日

違規事實：
測試用違規內容（已修改）

裁罰內容：
罰鍰新臺幣200萬元整
EOF

# Upload modified file
RESPONSE=$(curl -s -X POST http://localhost:8000/api/v1/documents/upload-with-progress \
  -F "file=@$TEST_FILE" \
  -F "auto_index=false" \
  -F "extract_metadata=false")

JOB_ID=$(echo "$RESPONSE" | jq -r '.job_id')
echo "Upload modified file - Job ID: $JOB_ID"

sleep 3

PROGRESS=$(curl -s "http://localhost:8000/api/v1/documents/upload-progress/$JOB_ID")
FILENAME=$(echo "$PROGRESS" | jq -r '.filename')
STAGE=$(echo "$PROGRESS" | jq -r '.stage')

echo "  Filename: $FILENAME"
echo "  Stage: $STAGE"

if [ "$FILENAME" != "test_duplicate_v4.txt" ]; then
  echo "❌ Expected test_duplicate_v4.txt, got $FILENAME"
  exit 1
fi

echo "✅ Modified content correctly saved as version 4"
echo ""

# Verify v4 has different content
V4_HASH=$(md5 -q "data/documents/test_duplicate_v4.txt")
echo "Version 4 hash: $V4_HASH"

if [ "$V4_HASH" = "$ORIGINAL_HASH" ]; then
  echo "❌ Version 4 should have different content!"
  exit 1
fi

echo "✅ Version 4 has different content (as expected)"
echo ""

# Summary
echo "=========================================="
echo "Test Summary"
echo "=========================================="
echo ""
echo "✅ All tests passed!"
echo ""
echo "Results:"
echo "  - Total uploads: 5"
echo "  - Original file: test_duplicate.txt"
echo "  - Version 1: test_duplicate_v1.txt (same content)"
echo "  - Version 2: test_duplicate_v2.txt (same content)"
echo "  - Version 3: test_duplicate_v3.txt (same content)"
echo "  - Version 4: test_duplicate_v4.txt (different content)"
echo ""
echo "Database entries:"
for i in {0..4}; do
  if [ $i -lt ${#DOC_IDS[@]} ]; then
    echo "  - ${DOC_IDS[$i]}: ${FILENAMES[$i]}"
  fi
done
echo ""

# Cleanup
echo "Step 9: Cleanup (optional - comment out to keep test files)"
# Uncomment to clean up test files:
# rm -f data/documents/test_duplicate*.txt
# for doc_id in "${DOC_IDS[@]}"; do
#   sqlite3 data/finagent.db "DELETE FROM documents WHERE doc_id='$doc_id';"
# done
echo "Test files kept for inspection"
echo ""

echo "=========================================="
echo "E2E Test Complete! ✅"
echo "=========================================="
