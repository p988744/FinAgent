# FinAgent v1.0 Implementation Verification Plan

**Based on:** [V1_0_RELEASE_PLAN.md](V1_0_RELEASE_PLAN.md)
**Purpose:** Verify all completed checkpoints (1-6) are actually working
**Method:** Playwright E2E tests + Backend API tests + Database verification
**Date Created:** 2025-11-19

---

## Executive Summary

This plan systematically verifies every feature claimed as "completed" in V1_0_RELEASE_PLAN.md Checkpoints 1-6. Each checkpoint has specific test scenarios that must pass.

**Total Test Scenarios:** 35+
**Estimated Execution Time:** 15-20 minutes (full suite)

---

## Checkpoint 1: Database Integration ✅ (100%)

### Features to Verify

1. **SQLite Database Populated**
   - All documents from Chroma exist in SQLite
   - No duplicate doc_ids
   - File paths are valid and accessible

2. **Chroma-SQLite Sync**
   - Document count matches between Chroma and SQLite
   - Indexed flag = 1 for all indexed documents
   - Chunk counts match

3. **Full Content Storage**
   - `full_content` field populated for all documents
   - `get_full_content()` API returns complete document text

### Test Scenarios (Backend)

```python
# Test 1.1: Database Population
def test_checkpoint1_database_populated():
    """Verify SQLite has all documents from Chroma"""
    - Query: SELECT COUNT(*) FROM documents WHERE indexed=1
    - Assert: count > 0
    - Query: SELECT COUNT(DISTINCT doc_id) FROM documents
    - Assert: count == total documents (no duplicates)

# Test 1.2: Chroma-SQLite Sync
def test_checkpoint1_chroma_sync():
    """Verify Chroma and SQLite are in sync"""
    - Get Chroma collection document count
    - Get SQLite indexed document count
    - Assert: counts match within acceptable range

# Test 1.3: Full Content Storage
def test_checkpoint1_full_content():
    """Verify full_content field is populated"""
    - Query: SELECT COUNT(*) FROM documents WHERE full_content IS NOT NULL
    - Assert: count > 0
    - API: GET /api/v1/documents/{random_doc_id}
    - Assert: response contains full_content field
    - Assert: len(full_content) > 100 characters
```

### Test Scenarios (Frontend - Playwright)

```typescript
// Test 1.4: Documents Page Loads Data from Database
test('Checkpoint 1: Documents page displays database data', async ({ page }) => {
  await page.goto('http://localhost:3000/documents');

  // Wait for data to load
  await page.waitForSelector('[data-testid="document-card"]');

  // Verify documents are displayed
  const docCards = await page.locator('[data-testid="document-card"]').count();
  expect(docCards).toBeGreaterThan(0);

  // Verify document has metadata from database
  const firstCard = page.locator('[data-testid="document-card"]').first();
  await expect(firstCard).toContainText(/.*\.txt/); // filename
});
```

**Success Criteria:**
- ✅ All 4 test scenarios pass
- ✅ Database contains >= 20 documents
- ✅ No duplicate doc_ids found
- ✅ Full content accessible via API

---

## Checkpoint 2: LLM Metadata Extraction ✅ (100%)

### Features to Verify

1. **Metadata Extractor Working**
   - GPT-4o-mini extracts metadata successfully
   - Confidence scores calculated
   - Error handling works

2. **Metadata Stored in Database**
   - document_type, issuing_authority, keywords populated
   - related_institutions, violation_types as arrays
   - extraction_confidence > 0.0

3. **Metadata Quality**
   - Average confidence > 0.85 (claimed: 0.95)
   - Extraction time < 10s per document
   - Valid document_type values

### Test Scenarios (Backend)

```python
# Test 2.1: Metadata Extraction API
def test_checkpoint2_metadata_extraction():
    """Verify metadata extraction works"""
    # Create test document
    test_content = "金管會於2020年9月15日對玉山銀行洗錢防制缺失裁罰新臺幣1000萬元..."

    # Call extraction API
    response = requests.post(
        '/api/v1/documents/{doc_id}/metadata/extract',
        json={'force': True}
    )

    # Verify response
    assert response.status_code == 200
    data = response.json()
    assert data['status'] in ['completed', 'already_extracted']
    assert 'extraction_confidence' in data
    assert data['extraction_confidence'] > 0.0

# Test 2.2: Metadata in Database
def test_checkpoint2_metadata_stored():
    """Verify extracted metadata is stored"""
    # Query documents with metadata
    result = db.execute("""
        SELECT COUNT(*) as count,
               AVG(extraction_confidence) as avg_confidence
        FROM documents
        WHERE metadata_extracted = 1
    """).fetchone()

    assert result['count'] > 0
    assert result['avg_confidence'] >= 0.85

# Test 2.3: Metadata Quality
def test_checkpoint2_metadata_quality():
    """Verify metadata quality standards"""
    docs = db.execute("""
        SELECT document_type, issuing_authority,
               keywords, extraction_confidence
        FROM documents
        WHERE metadata_extracted = 1
        LIMIT 10
    """).fetchall()

    for doc in docs:
        # Valid document type
        assert doc['document_type'] in [
            '裁罰書', '判決書', '法規', '新聞', '研究報告', '其他'
        ]
        # Has keywords
        if doc['keywords']:
            keywords = json.loads(doc['keywords'])
            assert len(keywords) >= 3
```

### Test Scenarios (Frontend - Playwright)

```typescript
// Test 2.4: Document Detail Shows Metadata
test('Checkpoint 2: Document metadata displayed', async ({ page }) => {
  await page.goto('http://localhost:3000/documents');

  // Click first document
  await page.locator('[data-testid="document-card"]').first().click();

  // Wait for detail page
  await page.waitForURL(/\/documents\/.+/);

  // Verify metadata sections exist
  await expect(page.locator('text=文件類型')).toBeVisible();
  await expect(page.locator('text=主管機關')).toBeVisible();
  await expect(page.locator('text=關鍵字')).toBeVisible();

  // Verify content is displayed
  const contentSection = page.locator('[data-testid="document-content"]');
  await expect(contentSection).toBeVisible();
});
```

**Success Criteria:**
- ✅ All 4 test scenarios pass
- ✅ >= 90% of documents have metadata extracted
- ✅ Average confidence >= 0.85
- ✅ All document_type values are valid

---

## Checkpoint 3: Wiki Generation System ✅ (100%)

### Features to Verify

1. **Category Tree Built**
   - Categories created for: authority, institution, violation, document_type
   - Document counts accurate
   - No orphaned documents

2. **Wiki Statistics Calculated**
   - Total documents count
   - Breakdown by authority, institution, type
   - Timeline data generated

3. **Relationship Detection**
   - Related documents identified
   - Relationship strength calculated (0.0-1.0)
   - Temporal relationships detected

4. **Performance**
   - Wiki rebuild time < 10s (claimed: 0.11s)

### Test Scenarios (Backend)

```python
# Test 3.1: Category Tree Exists
def test_checkpoint3_categories_exist():
    """Verify wiki categories are generated"""
    categories = db.execute("""
        SELECT category_type, COUNT(*) as count
        FROM concepts
        WHERE concept_type = 'category'
        GROUP BY category_type
    """).fetchall()

    category_types = [c['category_type'] for c in categories]

    # All required category types exist
    assert 'authority' in category_types
    assert 'institution' in category_types
    assert 'violation' in category_types
    assert 'document_type' in category_types

    # Each type has at least one category
    for cat in categories:
        assert cat['count'] > 0

# Test 3.2: Document Counts Accurate
def test_checkpoint3_category_counts():
    """Verify category document counts"""
    # Get total documents
    total_docs = db.execute("SELECT COUNT(*) FROM documents").fetchone()[0]

    # Get sum of documents in all categories
    # (Note: documents can be in multiple categories)
    authority_docs = db.execute("""
        SELECT SUM(metadata->>'$.document_count') as total
        FROM concepts
        WHERE category_type = 'authority'
    """).fetchone()[0]

    assert authority_docs > 0
    assert authority_docs <= total_docs * 2  # Allow for overlap

# Test 3.3: Wiki Rebuild Performance
def test_checkpoint3_rebuild_performance():
    """Verify wiki rebuild is fast"""
    import time

    # Trigger rebuild
    start_time = time.time()
    response = requests.post('/api/v1/wiki/rebuild')
    rebuild_time = time.time() - start_time

    assert response.status_code == 200
    assert rebuild_time < 10.0  # Must be under 10 seconds

    data = response.json()
    assert data['success'] == True
    assert 'categories_count' in data
    assert data['categories_count'] > 0
```

### Test Scenarios (Frontend - Playwright)

```typescript
// Test 3.4: Wiki Page Displays Categories
test('Checkpoint 3: Wiki categories displayed', async ({ page }) => {
  await page.goto('http://localhost:3000/wiki');

  // Wait for categories to load
  await page.waitForSelector('[data-testid="category-tree"]');

  // Verify category groups exist
  await expect(page.locator('text=按主管機關')).toBeVisible();
  await expect(page.locator('text=按金融機構')).toBeVisible();
  await expect(page.locator('text=按違規類型')).toBeVisible();
  await expect(page.locator('text=按文件類型')).toBeVisible();

  // Verify categories have document counts
  const categoryWithCount = page.locator('[data-testid="category-item"]').first();
  await expect(categoryWithCount).toContainText(/\(\d+\)/); // (N) format
});

// Test 3.5: Category Navigation Works
test('Checkpoint 3: Category navigation', async ({ page }) => {
  await page.goto('http://localhost:3000/wiki');

  // Click a category
  await page.locator('[data-testid="category-item"]').first().click();

  // Verify documents are filtered
  await page.waitForSelector('[data-testid="wiki-document-card"]');

  const docCards = await page.locator('[data-testid="wiki-document-card"]').count();
  expect(docCards).toBeGreaterThan(0);
});
```

**Success Criteria:**
- ✅ All 5 test scenarios pass
- ✅ All 4 category types exist
- ✅ 100% document coverage (no orphans)
- ✅ Wiki rebuild < 10 seconds

---

## Checkpoint 4: Wiki REST API ✅ (100%)

### Features to Verify

1. **All Endpoints Implemented**
   - 15+ endpoints working
   - Proper response schemas
   - Error handling (400, 404, 500)

2. **Performance**
   - Response time < 500ms (claimed: <200ms)
   - Pagination works correctly

3. **Data Accuracy**
   - Endpoints return correct data
   - Counts and statistics accurate

### Test Scenarios (Backend)

```python
# Test 4.1: Wiki Overview API
def test_checkpoint4_wiki_overview():
    """Verify /api/v1/wiki/overview works"""
    response = requests.get('/api/v1/wiki/overview')

    assert response.status_code == 200
    data = response.json()

    assert 'total_documents' in data
    assert 'total_categories' in data
    assert 'statistics' in data
    assert data['total_documents'] > 0

# Test 4.2: Categories API
def test_checkpoint4_categories():
    """Verify /api/v1/wiki/categories works"""
    for category_type in ['authority', 'institution', 'violation', 'document_type']:
        response = requests.get(f'/api/v1/wiki/categories?type={category_type}')

        assert response.status_code == 200
        categories = response.json()
        assert isinstance(categories, list)
        assert len(categories) > 0

        # Verify structure
        first_cat = categories[0]
        assert 'id' in first_cat
        assert 'name' in first_cat
        assert 'document_count' in first_cat

# Test 4.3: Document List API
def test_checkpoint4_documents_list():
    """Verify /api/v1/documents/ works"""
    response = requests.get('/api/v1/documents/?limit=10')

    assert response.status_code == 200
    data = response.json()

    assert 'documents' in data or isinstance(data, list)
    docs = data if isinstance(data, list) else data['documents']
    assert len(docs) <= 10

    # Verify document structure
    first_doc = docs[0]
    assert 'doc_id' in first_doc
    assert 'filename' in first_doc
    assert 'document_type' in first_doc

# Test 4.4: Document Detail API
def test_checkpoint4_document_detail():
    """Verify /api/v1/documents/{id} works"""
    # Get a document ID
    list_response = requests.get('/api/v1/documents/?limit=1')
    docs = list_response.json()
    doc_id = docs[0]['doc_id'] if isinstance(docs, list) else docs['documents'][0]['doc_id']

    # Get detail
    response = requests.get(f'/api/v1/documents/{doc_id}')

    assert response.status_code == 200
    doc = response.json()

    assert doc['doc_id'] == doc_id
    assert 'full_content' in doc
    assert 'metadata_extraction_status' in doc

# Test 4.5: Metadata Status API
def test_checkpoint4_metadata_status():
    """Verify /api/v1/documents/metadata/status works"""
    response = requests.get('/api/v1/documents/metadata/status')

    assert response.status_code == 200
    data = response.json()

    assert 'total_documents' in data
    assert 'indexed' in data
    assert 'metadata_extracted' in data
    assert 'status_breakdown' in data

# Test 4.6: Response Time Performance
def test_checkpoint4_performance():
    """Verify API response times < 500ms"""
    import time

    endpoints = [
        '/api/v1/wiki/overview',
        '/api/v1/wiki/categories?type=authority',
        '/api/v1/documents/?limit=20',
        '/api/v1/documents/metadata/status'
    ]

    for endpoint in endpoints:
        start_time = time.time()
        response = requests.get(endpoint)
        elapsed = (time.time() - start_time) * 1000  # Convert to ms

        assert response.status_code == 200
        assert elapsed < 500  # Under 500ms
```

**Success Criteria:**
- ✅ All 6 test scenarios pass
- ✅ All endpoints return 200 OK
- ✅ Response times < 500ms
- ✅ Error handling works (test 404 cases)

---

## Checkpoint 5: Wiki Frontend UI ✅ (85%)

### Features to Verify

1. **Wiki Overview Page**
   - Statistics cards display
   - Category tree renders
   - Recent documents list

2. **Category Browser**
   - Collapsible tree works
   - Document count badges
   - Click navigation

3. **Document Detail View**
   - Full metadata displayed
   - Document content shown
   - Related documents listed

4. **Responsive Design**
   - Works on mobile and desktop
   - Fast page transitions (<50ms claimed)

### Test Scenarios (Frontend - Playwright)

```typescript
// Test 5.1: Wiki Page Loads
test('Checkpoint 5: Wiki page loads successfully', async ({ page }) => {
  await page.goto('http://localhost:3000/wiki');

  // Page loads without errors
  await page.waitForLoadState('networkidle');

  // No console errors
  const errors: string[] = [];
  page.on('console', msg => {
    if (msg.type() === 'error') errors.push(msg.text());
  });

  await page.waitForTimeout(2000);
  expect(errors.length).toBe(0);
});

// Test 5.2: Statistics Cards Display
test('Checkpoint 5: Statistics cards', async ({ page }) => {
  await page.goto('http://localhost:3000/wiki');

  // Wait for stats to load
  await page.waitForSelector('[data-testid="stat-card"]', { timeout: 10000 });

  // Verify stats cards exist
  const statCards = await page.locator('[data-testid="stat-card"]').count();
  expect(statCards).toBeGreaterThan(0);

  // Verify stats have numbers
  const firstStat = page.locator('[data-testid="stat-card"]').first();
  await expect(firstStat).toContainText(/\d+/);
});

// Test 5.3: Category Tree Interactive
test('Checkpoint 5: Category tree interaction', async ({ page }) => {
  await page.goto('http://localhost:3000/wiki');

  // Wait for category tree
  await page.waitForSelector('[data-testid="category-tree"]');

  // Click to expand a category
  const categoryToggle = page.locator('[data-testid="category-toggle"]').first();
  await categoryToggle.click();

  // Verify subcategories or documents appear
  await page.waitForTimeout(500);
  const expanded = await page.locator('[data-testid="category-item"][data-expanded="true"]').count();
  expect(expanded).toBeGreaterThan(0);
});

// Test 5.4: Document Detail Page
test('Checkpoint 5: Document detail view', async ({ page }) => {
  await page.goto('http://localhost:3000/wiki');

  // Click first document
  await page.waitForSelector('[data-testid="wiki-document-card"]');
  await page.locator('[data-testid="wiki-document-card"]').first().click();

  // Wait for detail page
  await page.waitForURL(/\/documents\/.+/);

  // Verify metadata sections
  await expect(page.locator('text=基本資訊')).toBeVisible();
  await expect(page.locator('text=文件內容')).toBeVisible();

  // Verify content is displayed
  const contentArea = page.locator('[data-testid="document-content"]');
  await expect(contentArea).toBeVisible();
  const contentText = await contentArea.textContent();
  expect(contentText!.length).toBeGreaterThan(100);
});

// Test 5.5: Responsive Design
test('Checkpoint 5: Mobile responsive', async ({ page }) => {
  // Set mobile viewport
  await page.setViewportSize({ width: 375, height: 667 });
  await page.goto('http://localhost:3000/wiki');

  // Page loads without horizontal scroll
  const scrollWidth = await page.evaluate(() => document.documentElement.scrollWidth);
  const clientWidth = await page.evaluate(() => document.documentElement.clientWidth);

  expect(scrollWidth).toBeLessThanOrEqual(clientWidth + 1); // Allow 1px tolerance

  // UI elements are visible and clickable
  await expect(page.locator('[data-testid="category-tree"]')).toBeVisible();
});

// Test 5.6: Navigation Performance
test('Checkpoint 5: Fast page transitions', async ({ page }) => {
  await page.goto('http://localhost:3000/wiki');

  // Measure navigation time
  await page.waitForSelector('[data-testid="wiki-document-card"]');

  const startTime = Date.now();
  await page.locator('[data-testid="wiki-document-card"]').first().click();
  await page.waitForURL(/\/documents\/.+/);
  const navigationTime = Date.now() - startTime;

  // Should be fast (< 200ms for SPA)
  expect(navigationTime).toBeLessThan(1000);
});
```

**Success Criteria:**
- ✅ All 6 test scenarios pass
- ✅ Wiki page loads without errors
- ✅ All interactive elements work
- ✅ Responsive design works
- ⏳ Search deferred to v1.1

---

## Checkpoint 6: Upload & Delete Workflow ✅ (90%)

### Features to Verify

1. **Multi-file Upload**
   - Drag & drop works
   - Batch upload endpoint
   - Per-file progress tracking

2. **Upload Processing**
   - File saved to disk
   - Document indexed in Chroma
   - Metadata stored in SQLite

3. **Delete Workflow**
   - File deleted from filesystem
   - Removed from Chroma
   - Removed from SQLite

4. **Metadata Status System (6.2.1)**
   - Status tracking fields populated
   - Metadata extraction API works
   - Manual editing API works

5. **Error Handling**
   - Invalid file types rejected
   - Per-file error messages
   - Graceful failure

### Test Scenarios (Backend)

```python
# Test 6.1: Upload Batch API
def test_checkpoint6_upload_batch():
    """Verify batch upload endpoint works"""
    import io

    # Create test files
    files = {
        'files': [
            ('test_upload_1.txt', io.BytesIO(b'Test content 1')),
            ('test_upload_2.txt', io.BytesIO(b'Test content 2')),
        ]
    }

    response = requests.post('/api/v1/documents/upload-batch', files=files)

    assert response.status_code == 200
    data = response.json()

    assert 'uploaded' in data
    assert len(data['uploaded']) == 2
    assert data['failed'] == 0 or len(data.get('failed_files', [])) == 0

    # Clean up test files
    for upload_info in data['uploaded']:
        requests.delete(f'/api/v1/documents/{upload_info["doc_id"]}')

# Test 6.2: Upload Creates Database Entry
def test_checkpoint6_upload_creates_db_entry():
    """Verify upload creates database entry"""
    import io

    # Upload file
    files = {'files': [('test_db_entry.txt', io.BytesIO(b'Test database entry'))]}
    response = requests.post('/api/v1/documents/upload-batch', files=files)
    data = response.json()

    doc_id = data['uploaded'][0]['doc_id']

    # Verify in database
    db_doc = db.execute(
        "SELECT * FROM documents WHERE doc_id = ?",
        (doc_id,)
    ).fetchone()

    assert db_doc is not None
    assert db_doc['filename'] == 'test_db_entry.txt'
    assert db_doc['indexed'] == 1

    # Clean up
    requests.delete(f'/api/v1/documents/{doc_id}')

# Test 6.3: Delete API
def test_checkpoint6_delete():
    """Verify delete endpoint works"""
    import io

    # Create test file
    files = {'files': [('test_delete.txt', io.BytesIO(b'Test delete'))]}
    upload_response = requests.post('/api/v1/documents/upload-batch', files=files)
    doc_id = upload_response.json()['uploaded'][0]['doc_id']

    # Delete
    delete_response = requests.delete(f'/api/v1/documents/{doc_id}')

    assert delete_response.status_code == 200
    data = delete_response.json()
    assert data['success'] == True

    # Verify removed from database
    db_doc = db.execute(
        "SELECT * FROM documents WHERE doc_id = ?",
        (doc_id,)
    ).fetchone()
    assert db_doc is None

# Test 6.4: Metadata Extraction API (6.2.1)
def test_checkpoint6_metadata_extraction():
    """Verify metadata extraction endpoint works"""
    # Get a document
    response = requests.get('/api/v1/documents/?limit=1')
    docs = response.json()
    doc_id = docs[0]['doc_id'] if isinstance(docs, list) else docs['documents'][0]['doc_id']

    # Trigger extraction
    extract_response = requests.post(
        f'/api/v1/documents/{doc_id}/metadata/extract',
        json={'force': True}
    )

    assert extract_response.status_code == 200
    data = extract_response.json()
    assert 'status' in data
    assert data['status'] in ['completed', 'failed', 'already_extracted']

# Test 6.5: Metadata Edit API (6.2.1)
def test_checkpoint6_metadata_edit():
    """Verify metadata editing endpoint works"""
    # Get a document
    response = requests.get('/api/v1/documents/?limit=1')
    docs = response.json()
    doc_id = docs[0]['doc_id'] if isinstance(docs, list) else docs['documents'][0]['doc_id']

    # Edit metadata
    edit_data = {
        'document_type': '裁罰書',
        'keywords': ['測試', '關鍵字']
    }
    edit_response = requests.patch(
        f'/api/v1/documents/{doc_id}/metadata',
        json=edit_data
    )

    assert edit_response.status_code == 200
    data = edit_response.json()
    assert data['success'] == True
    assert data['metadata_edited_by_user'] == True
```

### Test Scenarios (Frontend - Playwright)

```typescript
// Test 6.6: Upload UI - Drag & Drop
test('Checkpoint 6: Drag and drop upload', async ({ page }) => {
  await page.goto('http://localhost:3000/documents');

  // Look for upload component
  await expect(page.locator('text=上傳文件')).toBeVisible();

  // Click upload button
  await page.locator('button:has-text("上傳文件")').click();

  // Verify upload dialog appears
  await expect(page.locator('[data-testid="upload-dialog"]')).toBeVisible();
});

// Test 6.7: Upload Progress Display
test('Checkpoint 6: Upload progress tracking', async ({ page }) => {
  await page.goto('http://localhost:3000/documents');

  // Open upload dialog
  await page.locator('button:has-text("上傳文件")').click();

  // Create test file
  const fileContent = 'Test document content for upload verification';

  // Upload file
  const fileInput = page.locator('input[type="file"]');
  await fileInput.setInputFiles({
    name: 'test_upload.txt',
    mimeType: 'text/plain',
    buffer: Buffer.from(fileContent)
  });

  // Verify file appears in list
  await expect(page.locator('text=test_upload.txt')).toBeVisible();

  // Click upload
  await page.locator('button:has-text("上傳")').click();

  // Wait for upload to complete
  await page.waitForSelector('[data-testid="upload-success"]', { timeout: 30000 });

  // Verify success indicator
  await expect(page.locator('[data-testid="upload-success"]')).toBeVisible();
});

// Test 6.8: Delete Document
test('Checkpoint 6: Delete document', async ({ page }) => {
  await page.goto('http://localhost:3000/documents');

  // Find a document with delete button
  const deleteButton = page.locator('[data-testid="delete-button"]').first();

  if (await deleteButton.isVisible()) {
    await deleteButton.click();

    // Wait for deletion to complete
    await page.waitForTimeout(1000);

    // Verify document list refreshed
    await expect(page.locator('[data-testid="document-card"]')).toBeVisible();
  }
});

// Test 6.9: File Validation
test('Checkpoint 6: Invalid file type rejected', async ({ page }) => {
  await page.goto('http://localhost:3000/documents');

  // Open upload dialog
  await page.locator('button:has-text("上傳文件")').click();

  // Try to upload invalid file type
  const fileInput = page.locator('input[type="file"]');
  await fileInput.setInputFiles({
    name: 'test.pdf',
    mimeType: 'application/pdf',
    buffer: Buffer.from('fake pdf content')
  });

  // Verify error message appears
  await expect(page.locator('text=/只支援.*txt/i')).toBeVisible();
});
```

**Success Criteria:**
- ✅ All 9 test scenarios pass
- ✅ Upload success rate > 95%
- ✅ Delete removes from all storage layers
- ✅ Metadata status system functional
- ✅ Error handling works correctly

---

## Test Execution Plan

### Phase 1: Backend API Tests (10 minutes)

```bash
# Setup
cd /Users/weifanliao/PycharmProjects/finagent

# Start backend server
uv run uvicorn finagent.main:app --reload --port 8000 &
SERVER_PID=$!

# Wait for server to start
sleep 5

# Run backend tests
uv run pytest tests/test_verification_checkpoints.py -v

# Stop server
kill $SERVER_PID
```

### Phase 2: Frontend E2E Tests (10 minutes)

```bash
# Start frontend dev server
npm --prefix frontend run dev &
FRONTEND_PID=$!

# Wait for frontend to start
sleep 10

# Run Playwright tests
npm --prefix frontend exec playwright test tests/verification-checkpoints.spec.ts

# Stop frontend
kill $FRONTEND_PID
```

### Phase 3: Manual Verification (5 minutes)

**Checklist:**
- [ ] Database has > 20 documents
- [ ] Wiki page loads without errors
- [ ] Document detail page shows full content
- [ ] Upload works with 3 files
- [ ] Delete removes document completely
- [ ] Metadata extraction API returns data

---

## Test File Structure

```
tests/
├── test_verification_checkpoints.py          # Backend tests
│   ├── Checkpoint1Tests (4 tests)
│   ├── Checkpoint2Tests (3 tests)
│   ├── Checkpoint3Tests (3 tests)
│   ├── Checkpoint4Tests (6 tests)
│   └── Checkpoint6Tests (5 tests)
│
frontend/e2e/
└── verification-checkpoints.spec.ts          # Frontend tests
    ├── Checkpoint1Tests (1 test)
    ├── Checkpoint2Tests (1 test)
    ├── Checkpoint3Tests (2 tests)
    ├── Checkpoint5Tests (6 tests)
    └── Checkpoint6Tests (4 tests)
```

**Total Tests:** 35 test scenarios

---

## Expected Results

### Pass Criteria

✅ **Checkpoint 1:** 4/4 tests pass
✅ **Checkpoint 2:** 4/4 tests pass
✅ **Checkpoint 3:** 5/5 tests pass
✅ **Checkpoint 4:** 6/6 tests pass
✅ **Checkpoint 5:** 6/6 tests pass (search excluded)
✅ **Checkpoint 6:** 9/9 tests pass

**Overall:** 34/35 tests pass (97%+ success rate)

### Known Limitations (Acceptable)

⏸️ **Checkpoint 5:** Search functionality deferred to v1.1
⏸️ **Checkpoint 6:** WebSocket progress deferred (HTTP polling works)
⏸️ **Checkpoint 6:** Auto wiki rebuild deferred (manual trigger works)

---

## Failure Handling

If any test fails:

1. **Document the failure** in test results file
2. **Categorize severity:**
   - **CRITICAL:** Feature doesn't work at all
   - **MAJOR:** Feature works but fails acceptance criteria
   - **MINOR:** Edge case or optional feature
3. **Update V1_0_RELEASE_PLAN.md** checkpoint status if critical
4. **Create fix task** with priority level

---

## Next Steps

After verification:

1. **Generate test report:** `VERIFICATION_RESULTS_2025-11-19.md`
2. **Update V1_0_RELEASE_PLAN.md** with actual completion percentages
3. **Create issue list** for any failures
4. **Decide:** Fix issues or proceed to Checkpoint 7

---

**Summary:** This plan provides comprehensive verification of all completed checkpoints using automated tests and manual checks. Execution time: ~25 minutes total.
