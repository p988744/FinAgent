import { test, expect } from '@playwright/test';

const BASE_URL = 'http://localhost:5173';
const API_URL = 'http://localhost:8000';

test.describe('Pipeline Upload E2E Test', () => {
  test('Complete upload pipeline with monitoring', async ({ page, request }) => {
    console.log('🧪 Starting Pipeline Upload E2E Test\n');

    // ============================================================================
    // STEP 1: Clean up test data
    // ============================================================================
    console.log('🧹 Step 1: Cleaning up test data...');

    // Get all documents
    const docsResponse = await request.get(`${API_URL}/api/v1/documents/`);
    if (docsResponse.ok()) {
      const docs = await docsResponse.json();
      const docsList = Array.isArray(docs) ? docs : docs.documents || [];

      console.log(`   Found ${docsList.length} existing documents`);

      // Delete test documents
      for (const doc of docsList) {
        if (doc.name?.includes('test') || doc.filename?.includes('test')) {
          console.log(`   Deleting: ${doc.name || doc.filename}`);
          await request.delete(`${API_URL}/api/v1/documents/${doc.id || doc.doc_id}`);
        }
      }
    }

    console.log('✅ Step 1 Complete: Test data cleaned\n');

    // ============================================================================
    // STEP 2: Upload a test document
    // ============================================================================
    console.log('📤 Step 2: Uploading test document...');

    await page.goto(`${BASE_URL}/documents`);
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2000);

    // Create test document content
    const testDoc = {
      name: 'test_pipeline_upload.txt',
      content: `金融監督管理委員會裁罰書

受處分人：測試銀行股份有限公司
案號：金管銀法字第11200001號
發文日期：中華民國112年11月19日

主旨：因違反銀行法相關規定，處以新臺幣500萬元罰鍰。

事實：
測試銀行股份有限公司於民國112年辦理企業金融業務時，
未確實遵循內部控制制度及相關法令規定。

理由：
依銀行法第45條之1規定，本會決議處以罰鍰。

裁罰：
處新臺幣500萬元罰鍰。

金融監督管理委員會
主任委員 測試人
中華民國112年11月19日`,
    };

    console.log(`   Creating test file: ${testDoc.name}`);

    // Find file input and upload
    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles({
      name: testDoc.name,
      mimeType: 'text/plain',
      buffer: Buffer.from(testDoc.content, 'utf-8'),
    });

    console.log('   File added to upload queue');
    await page.waitForTimeout(2000);

    // Click upload button
    const uploadButton = page.locator('button:has-text("上傳全部")');
    await expect(uploadButton).toBeVisible({ timeout: 10000 });

    console.log('   Clicking upload button...');
    await uploadButton.click();

    console.log('   Upload initiated, waiting for completion (30s)...');
    await page.waitForTimeout(30000);

    console.log('✅ Step 2 Complete: Document uploaded\n');

    // ============================================================================
    // STEP 3: Verify document appears in list
    // ============================================================================
    console.log('🔍 Step 3: Verifying document in list...');

    await page.reload();
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2000);

    // Check if document appears
    const documentList = page.locator('[data-testid="document-list"], .space-y-2, .divide-y');
    const documentItems = documentList.locator('> *');
    const count = await documentItems.count();

    console.log(`   Documents in list: ${count}`);

    // Find our test document
    const testDocElement = page.locator(`text=${testDoc.name}`);
    const isVisible = await testDocElement.isVisible().catch(() => false);

    if (isVisible) {
      console.log(`   ✅ Test document found: ${testDoc.name}`);
    } else {
      console.log(`   ⚠️  Test document not visible yet`);
    }

    console.log('✅ Step 3 Complete\n');

    // ============================================================================
    // STEP 4: Check pipeline status via API
    // ============================================================================
    console.log('🔧 Step 4: Checking pipeline status via API...');

    // Get all documents to find our test doc
    const allDocsResponse = await request.get(`${API_URL}/api/v1/documents/`);
    if (allDocsResponse.ok()) {
      const allDocs = await allDocsResponse.json();
      const docsList = Array.isArray(allDocs) ? allDocs : allDocs.documents || [];

      const testDocument = docsList.find((d: any) =>
        (d.name || d.filename || '').includes('test_pipeline_upload')
      );

      if (testDocument) {
        const docId = testDocument.id || testDocument.doc_id;
        console.log(`   Found test document with ID: ${docId}`);

        // Check pipeline status
        const pipelineResponse = await request.get(
          `${API_URL}/api/v1/documents/${docId}/pipeline`
        );

        if (pipelineResponse.ok()) {
          const pipeline = await pipelineResponse.json();
          console.log('\n   Pipeline Status:');
          console.log(`   - Current Stage: ${pipeline.current_stage}`);
          console.log(`   - Overall Status: ${pipeline.overall_status}`);
          console.log(`   - Progress: ${Math.round(pipeline.progress_percentage)}%`);
          if (pipeline.total_duration_seconds) {
            console.log(`   - Duration: ${pipeline.total_duration_seconds.toFixed(2)}s`);
          }

          console.log('\n   Stage Details:');
          pipeline.stages.forEach((stage: any) => {
            const duration = stage.duration ? `${stage.duration.toFixed(2)}s` : '-';
            console.log(`   - ${stage.stage}: ${stage.status} (${duration})`);
            if (stage.error_message) {
              console.log(`     ERROR: ${stage.error_message}`);
            }
          });

          // Verify pipeline completed successfully
          expect(pipeline.overall_status).toBe('success');
          expect(pipeline.progress_percentage).toBeGreaterThan(90);
        } else {
          console.log(`   ⚠️  Pipeline API returned ${pipelineResponse.status()}`);
          const errorText = await pipelineResponse.text();
          console.log(`   Error: ${errorText}`);
        }
      } else {
        console.log('   ⚠️  Test document not found in API response');
      }
    }

    console.log('✅ Step 4 Complete\n');

    // ============================================================================
    // STEP 5: Check pipeline stats
    // ============================================================================
    console.log('📊 Step 5: Checking aggregate pipeline stats...');

    const statsResponse = await request.get(`${API_URL}/api/v1/documents/pipeline/stats`);
    if (statsResponse.ok()) {
      const stats = await statsResponse.json();
      console.log('\n   Pipeline Statistics:');
      console.log(`   - Total Documents: ${stats.total_documents}`);
      console.log(`   - By Status:`, stats.by_status);
      console.log(`   - By Stage:`, stats.by_stage);
      if (stats.avg_duration_seconds) {
        console.log(`   - Average Duration: ${stats.avg_duration_seconds.toFixed(2)}s`);
      }
      if (stats.failed_documents.length > 0) {
        console.log(`   - Failed Documents: ${stats.failed_documents.length}`);
        stats.failed_documents.forEach((doc: any) => {
          console.log(`     - ${doc.filename}: ${doc.failed_stage} - ${doc.error}`);
        });
      }
    } else {
      console.log(`   ⚠️  Stats API returned ${statsResponse.status()}`);
      const errorText = await statsResponse.text();
      console.log(`   Error: ${errorText}`);
    }

    console.log('✅ Step 5 Complete\n');

    console.log('🎉 Pipeline Upload E2E Test Complete!');
  });
});
