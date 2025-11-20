#!/bin/bash
set -e

echo "=== E2E Test: Log Display Feature ==="
echo ""

# 1. Upload a test document
echo "Step 1: Uploading test document..."
UPLOAD_RESPONSE=$(curl -s -X POST http://localhost:8000/api/v1/documents/upload-with-progress \
  -F "file=@data/documents/004_20120120_證券期貨局_前台証綜合證券股份有限公司、日盛證券股份有限公司、台新國際商業銀行.txt" \
  -F "auto_index=true" \
  -F "extract_metadata=false")

JOB_ID=$(echo "$UPLOAD_RESPONSE" | jq -r '.job_id')
echo "✅ Upload initiated. Job ID: $JOB_ID"
echo ""

# 2. Wait for upload to complete
echo "Step 2: Waiting for upload to complete..."
sleep 3

PROGRESS_RESPONSE=$(curl -s "http://localhost:8000/api/v1/documents/upload-progress/$JOB_ID")
DOC_ID=$(echo "$PROGRESS_RESPONSE" | jq -r '.document_id')
echo "✅ Upload complete. Document ID: $DOC_ID"
echo ""

# 3. Wait for Celery processing
echo "Step 3: Waiting for Celery processing (5 seconds)..."
sleep 5

# 4. Check pipeline status from API
echo "Step 4: Checking pipeline status from API..."
PIPELINE_RESPONSE=$(curl -s "http://localhost:8000/api/v1/documents/$DOC_ID/pipeline")

echo "Pipeline Status:"
echo "$PIPELINE_RESPONSE" | jq '{
  current_stage,
  overall_status,
  stages_count: (.stages | length)
}'
echo ""

# 5. Check if stages have logs
STAGES_WITH_LOGS=$(echo "$PIPELINE_RESPONSE" | jq '[.stages[] | select(.details.logs != null)] | length')
echo "Stages with logs: $STAGES_WITH_LOGS"
echo ""

# 6. Show first stage details
echo "Step 5: First stage details:"
echo "$PIPELINE_RESPONSE" | jq '.stages[0]'
echo ""

# 7. Check logs in first stage
if [ "$STAGES_WITH_LOGS" -gt 0 ]; then
  echo "Step 6: Logs from first stage:"
  echo "$PIPELINE_RESPONSE" | jq '.stages[0].details.logs[0:3]'
  echo "✅ LOGS FOUND IN API RESPONSE!"
else
  echo "❌ NO LOGS FOUND IN API RESPONSE"
  echo ""
  echo "Checking database directly..."
  sqlite3 data/finagent.db "SELECT doc_id, pipeline_stage, pipeline_status, LENGTH(pipeline_data) FROM documents WHERE doc_id='$DOC_ID';"
fi

echo ""
echo "=== Test Complete ==="
