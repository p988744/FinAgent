#!/bin/bash
set -e

echo "=========================================="
echo "E2E Test: Duplicate File User Confirmation"
echo "=========================================="
echo ""

# Clean up previous test files
echo "Step 1: Cleaning up previous test files..."
rm -f data/documents/test_confirm*.txt
rm -f /tmp/test_confirm.txt
echo "✅ Cleanup complete"
echo ""

# Create a test file in /tmp
TEST_FILE="/tmp/test_confirm.txt"
cat > "$TEST_FILE" << 'EOF'
金融監督管理委員會 裁罰書

受處分人：測試確認銀行股份有限公司
案號：金管銀法字第1111111111號
裁罰日期：民國113年11月19日

違規事實：
測試用戶確認功能

裁罰內容：
罰鍰新臺幣50萬元整
EOF

echo "Step 2: Test file created at: $TEST_FILE"
echo ""

# Test 1: First upload (no duplicate) with default "ask" action
echo "=========================================="
echo "Test 1: First Upload (No Duplicate)"
echo "=========================================="
echo ""

RESPONSE=$(curl -s -X POST http://localhost:8000/api/v1/documents/upload-with-progress \
  -F "file=@$TEST_FILE" \
  -F "auto_index=false" \
  -F "extract_metadata=false")

STATUS=$(echo "$RESPONSE" | jq -r '.status // "normal"')
JOB_ID=$(echo "$RESPONSE" | jq -r '.job_id // "none"')

echo "Job ID: $JOB_ID"

# Normal upload should have job_id and message, but no status field
if [ "$JOB_ID" != "none" ] && [ "$JOB_ID" != "null" ]; then
  if [ "$STATUS" == "duplicate_detected" ]; then
    echo "❌ Unexpected duplicate detection on first upload!"
    echo "$RESPONSE" | jq .
    exit 1
  fi

  echo "✅ First upload initiated successfully"

  # Wait for upload to complete
  sleep 3

  # Verify file exists
  if [ -f "data/documents/test_confirm.txt" ]; then
    echo "✅ File created: test_confirm.txt"
  else
    echo "❌ File not created!"
    exit 1
  fi
else
  echo "❌ Upload failed - no job_id returned!"
  echo "$RESPONSE" | jq .
  exit 1
fi

echo ""

# Test 2: Upload same file with default "ask" action - should detect duplicate
echo "=========================================="
echo "Test 2: Duplicate Detection (action=ask)"
echo "=========================================="
echo ""

RESPONSE=$(curl -s -X POST http://localhost:8000/api/v1/documents/upload-with-progress \
  -F "file=@$TEST_FILE" \
  -F "auto_index=false" \
  -F "extract_metadata=false")

echo "Response:"
echo "$RESPONSE" | jq .
echo ""

STATUS=$(echo "$RESPONSE" | jq -r '.status')
MESSAGE=$(echo "$RESPONSE" | jq -r '.message')

if [ "$STATUS" != "duplicate_detected" ]; then
  echo "❌ Expected status 'duplicate_detected', got: $STATUS"
  exit 1
fi

echo "✅ Duplicate detected successfully"
echo "Message: $MESSAGE"
echo ""

# Verify duplicate_info is present
DUPLICATE_FILENAME=$(echo "$RESPONSE" | jq -r '.duplicate_info.filename')
DUPLICATE_SIZE=$(echo "$RESPONSE" | jq -r '.duplicate_info.size')

echo "Duplicate info:"
echo "  Filename: $DUPLICATE_FILENAME"
echo "  Size: $DUPLICATE_SIZE bytes"
echo ""

# Verify options are present
OPTION_VERSION=$(echo "$RESPONSE" | jq -r '.options.version')
OPTION_REPLACE=$(echo "$RESPONSE" | jq -r '.options.replace')
OPTION_SKIP=$(echo "$RESPONSE" | jq -r '.options.skip')

echo "Options provided:"
echo "  version: $OPTION_VERSION"
echo "  replace: $OPTION_REPLACE"
echo "  skip: $OPTION_SKIP"
echo ""

if [ "$OPTION_VERSION" == "null" ] || [ "$OPTION_REPLACE" == "null" ] || [ "$OPTION_SKIP" == "null" ]; then
  echo "❌ Options not properly returned!"
  exit 1
fi

echo "✅ All duplicate info and options present"
echo ""

# Test 3: Upload with duplicate_action=version
echo "=========================================="
echo "Test 3: User Chooses 'Create Version'"
echo "=========================================="
echo ""

RESPONSE=$(curl -s -X POST http://localhost:8000/api/v1/documents/upload-with-progress \
  -F "file=@$TEST_FILE" \
  -F "auto_index=false" \
  -F "extract_metadata=false" \
  -F "duplicate_action=version")

JOB_ID=$(echo "$RESPONSE" | jq -r '.job_id')
echo "Job ID: $JOB_ID"

# Wait for upload to complete
sleep 3

# Get upload progress
PROGRESS=$(curl -s "http://localhost:8000/api/v1/documents/upload-progress/$JOB_ID")
FILENAME=$(echo "$PROGRESS" | jq -r '.filename')
STAGE=$(echo "$PROGRESS" | jq -r '.stage')

echo "Filename: $FILENAME"
echo "Stage: $STAGE"

if [ "$FILENAME" != "test_confirm_v1.txt" ]; then
  echo "❌ Expected test_confirm_v1.txt, got $FILENAME"
  exit 1
fi

if [ ! -f "data/documents/test_confirm_v1.txt" ]; then
  echo "❌ Version file not created!"
  exit 1
fi

echo "✅ Version created successfully: test_confirm_v1.txt"
echo ""

# Test 4: Upload with duplicate_action=replace (treat as new file)
echo "=========================================="
echo "Test 4: User Chooses 'Treat as New File'"
echo "=========================================="
echo ""

# Modify the test file content
cat > "$TEST_FILE" << 'EOF'
金融監督管理委員會 裁罰書

受處分人：測試確認銀行股份有限公司（不同內容）
案號：金管銀法字第2222222222號
裁罰日期：民國113年11月19日

違規事實：
測試新檔案功能

裁罰內容：
罰鍰新臺幣200萬元整
EOF

RESPONSE=$(curl -s -X POST http://localhost:8000/api/v1/documents/upload-with-progress \
  -F "file=@$TEST_FILE" \
  -F "auto_index=false" \
  -F "extract_metadata=false" \
  -F "duplicate_action=replace")

JOB_ID=$(echo "$RESPONSE" | jq -r '.job_id')
echo "Job ID: $JOB_ID"

# Wait for upload to complete
sleep 3

# Get upload progress
PROGRESS=$(curl -s "http://localhost:8000/api/v1/documents/upload-progress/$JOB_ID")
FILENAME=$(echo "$PROGRESS" | jq -r '.filename')
STAGE=$(echo "$PROGRESS" | jq -r '.stage')

echo "Filename: $FILENAME"
echo "Stage: $STAGE"

# Should have unique ID suffix (8 chars UUID)
if [[ ! "$FILENAME" =~ ^test_confirm_[a-f0-9]{8}\.txt$ ]]; then
  echo "❌ Expected filename with UUID suffix (test_confirm_xxxxxxxx.txt), got $FILENAME"
  exit 1
fi

# Verify both original and new file exist
if [ ! -f "data/documents/test_confirm.txt" ]; then
  echo "❌ Original file should still exist!"
  exit 1
fi

if [ ! -f "data/documents/$FILENAME" ]; then
  echo "❌ New file not created!"
  exit 1
fi

echo "✅ New file created with unique ID: $FILENAME"
echo "✅ Original file preserved"
echo ""

# Test 5: Upload with duplicate_action=skip
echo "=========================================="
echo "Test 5: User Chooses 'Skip'"
echo "=========================================="
echo ""

RESPONSE=$(curl -s -X POST http://localhost:8000/api/v1/documents/upload-with-progress \
  -F "file=@$TEST_FILE" \
  -F "auto_index=false" \
  -F "extract_metadata=false" \
  -F "duplicate_action=skip")

JOB_ID=$(echo "$RESPONSE" | jq -r '.job_id')
echo "Job ID: $JOB_ID"

# Wait for processing
sleep 3

# Get upload progress
PROGRESS=$(curl -s "http://localhost:8000/api/v1/documents/upload-progress/$JOB_ID")
STAGE=$(echo "$PROGRESS" | jq -r '.stage')
ERROR=$(echo "$PROGRESS" | jq -r '.error')

echo "Stage: $STAGE"
echo "Error: $ERROR"

if [ "$STAGE" != "error" ]; then
  echo "❌ Expected stage 'error', got $STAGE"
  exit 1
fi

if [[ "$ERROR" != *"已跳過上傳"* ]]; then
  echo "❌ Expected skip error message, got: $ERROR"
  exit 1
fi

echo "✅ Upload skipped successfully"
echo ""

# Test 6: Multiple version creation
echo "=========================================="
echo "Test 6: Multiple Version Creation"
echo "=========================================="
echo ""

# Create v2
RESPONSE=$(curl -s -X POST http://localhost:8000/api/v1/documents/upload-with-progress \
  -F "file=@$TEST_FILE" \
  -F "auto_index=false" \
  -F "extract_metadata=false" \
  -F "duplicate_action=version")

JOB_ID=$(echo "$RESPONSE" | jq -r '.job_id')
sleep 3

PROGRESS=$(curl -s "http://localhost:8000/api/v1/documents/upload-progress/$JOB_ID")
FILENAME=$(echo "$PROGRESS" | jq -r '.filename')

echo "Created: $FILENAME"

if [ "$FILENAME" != "test_confirm_v2.txt" ]; then
  echo "❌ Expected test_confirm_v2.txt, got $FILENAME"
  exit 1
fi

# Create v3
RESPONSE=$(curl -s -X POST http://localhost:8000/api/v1/documents/upload-with-progress \
  -F "file=@$TEST_FILE" \
  -F "auto_index=false" \
  -F "extract_metadata=false" \
  -F "duplicate_action=version")

JOB_ID=$(echo "$RESPONSE" | jq -r '.job_id')
sleep 3

PROGRESS=$(curl -s "http://localhost:8000/api/v1/documents/upload-progress/$JOB_ID")
FILENAME=$(echo "$PROGRESS" | jq -r '.filename')

echo "Created: $FILENAME"

if [ "$FILENAME" != "test_confirm_v3.txt" ]; then
  echo "❌ Expected test_confirm_v3.txt, got $FILENAME"
  exit 1
fi

echo "✅ Multiple versions created successfully"
echo ""

# Verify all files exist
echo "=========================================="
echo "Summary: Files Created"
echo "=========================================="
echo ""

ls -lh data/documents/test_confirm*.txt

FILE_COUNT=$(ls -1 data/documents/test_confirm*.txt 2>/dev/null | wc -l | tr -d ' ')
echo ""
echo "Total files: $FILE_COUNT"

if [ "$FILE_COUNT" -ne 5 ]; then
  echo "❌ Expected 5 files, found $FILE_COUNT"
  exit 1
fi

echo "✅ All 5 files present"
echo ""

# Summary
echo "=========================================="
echo "Test Results Summary"
echo "=========================================="
echo ""
echo "✅ Test 1: First upload (no duplicate) - PASSED"
echo "✅ Test 2: Duplicate detection (ask) - PASSED"
echo "✅ Test 3: Create version - PASSED"
echo "✅ Test 4: Treat as new file (keep both) - PASSED"
echo "✅ Test 5: Skip upload - PASSED"
echo "✅ Test 6: Multiple versions - PASSED"
echo ""
echo "Files created:"
echo "  - test_confirm.txt (original)"
echo "  - test_confirm_v1.txt (versioned copy)"
echo "  - test_confirm_xxxxxxxx.txt (treated as new file with UUID)"
echo "  - test_confirm_v2.txt (versioned copy)"
echo "  - test_confirm_v3.txt (versioned copy)"
echo ""
echo "=========================================="
echo "All Tests Passed! ✅"
echo "=========================================="
