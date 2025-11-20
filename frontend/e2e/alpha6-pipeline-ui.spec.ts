import { test, expect } from '@playwright/test';
import path from 'path';
import fs from 'fs';

const API_URL = 'http://localhost:8000';

test.describe('Pipeline UI Integration', () => {
  test('should show pipeline modal and track upload progress', async ({ page, request }) => {
    // STEP 1: Create test file
    console.log('\n📝 Step 1: Creating test file...');
    const testFilePath = '/tmp/test_pipeline_ui.txt';
    const testContent = `金融監督管理委員會裁罰書
案號：金管銀法字第1100001234號
受處分人：測試銀行股份有限公司

事實：
本行於民國110年1月1日進行金融檢查時，發現受處分人有下列缺失：
1. 內部控制制度執行不力
2. 洗錢防制措施未落實

理由：
受處分人違反銀行法第45條之1規定，應依同法第129條規定處罰。

主文：
處新臺幣200萬元罰鍰。

中華民國110年3月15日
金融監督管理委員會
`;
    fs.writeFileSync(testFilePath, testContent);
    console.log(`  ✅ Test file created: ${testFilePath}`);

    // STEP 2: Clean up old test documents
    console.log('\n🗑️  Step 2: Cleaning up old test documents...');
    const docsResponse = await request.get(`${API_URL}/api/v1/documents/`);
    if (docsResponse.ok()) {
      const docs = await docsResponse.json();
      for (const doc of docs) {
        if (doc.filename?.startsWith('test_pipeline_')) {
          console.log(`  🗑️  Deleting: ${doc.filename}`);
          await request.delete(`${API_URL}/api/v1/documents/${doc.doc_id}`);
        }
      }
    }

    // STEP 3: Navigate to documents page
    console.log('\n📄 Step 3: Navigating to documents page...');
    await page.goto('/documents');
    await page.waitForLoadState('networkidle');
    await expect(page.locator('h1')).toContainText('文件管理');
    console.log('  ✅ Documents page loaded');

    // STEP 4: Upload test document
    console.log('\n📤 Step 4: Uploading test document...');
    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles([testFilePath]);
    console.log('  ✅ File selected');

    // Wait for file to be added to the upload queue
    await expect(page.locator('text=test_pipeline_ui.txt')).toBeVisible({ timeout: 5000 });
    console.log('  ✅ File added to upload queue');

    // Click "Upload All" button
    const uploadAllButton = page.locator('button:has-text("上傳全部")');
    await expect(uploadAllButton).toBeVisible({ timeout: 5000 });
    await uploadAllButton.click();
    console.log('  ✅ Upload started');

    // Wait for upload to complete (check for success icon)
    await expect(page.locator('svg.lucide-check-circle-2').first()).toBeVisible({ timeout: 30000 });
    console.log('  ✅ Upload complete');

    // Wait a bit for document to be fully indexed
    await page.waitForTimeout(3000);

    // STEP 5: Navigate to document list (might be in a different section)
    console.log('\n🔍 Step 5: Finding uploaded document in list...');
    // Refresh the documents list
    await page.reload();
    await page.waitForLoadState('networkidle');
    const docRow = page.locator('div').filter({ hasText: 'test_pipeline_ui.txt' }).first();
    expect(await docRow.isVisible()).toBeTruthy();

    // STEP 5: Click "View Pipeline" button (Activity icon)
    console.log('\n⚡ Step 5: Opening pipeline modal...');
    const pipelineButton = docRow.locator('button[title="查看處理流程"]');
    await pipelineButton.click();

    // Wait for modal to open
    await page.waitForSelector('h3:has-text("處理流程監控")', { timeout: 5000 });
    console.log('  ✅ Pipeline modal opened');

    // STEP 6: Verify modal content
    console.log('\n📊 Step 6: Verifying pipeline modal content...');

    // Check for filename in modal
    await expect(page.locator('text=test_pipeline_ui.txt')).toBeVisible();
    console.log('  ✅ Filename displayed');

    // Check for progress section
    await expect(page.locator('h4:has-text("整體進度")')).toBeVisible();
    console.log('  ✅ Progress section visible');

    // Check for timeline section
    await expect(page.locator('h3:has-text("處理時間軸")')).toBeVisible();
    console.log('  ✅ Timeline section visible');

    // Check for at least one stage in timeline (uploaded stage should always exist)
    const uploadedStage = page.locator('text=已上傳').first();
    await expect(uploadedStage).toBeVisible();
    console.log('  ✅ "已上傳" stage visible in timeline');

    // Check for progress percentage
    const progressText = page.locator('text=/\\d+%/');
    await expect(progressText).toBeVisible();
    const progressValue = await progressText.textContent();
    console.log(`  ✅ Progress percentage: ${progressValue}`);

    // Check for status badges
    const statusBadges = page.locator('[class*="rounded-full"][class*="text-xs"]');
    const badgeCount = await statusBadges.count();
    expect(badgeCount).toBeGreaterThan(0);
    console.log(`  ✅ Found ${badgeCount} status badges`);

    // STEP 7: Verify pipeline data via API
    console.log('\n🔌 Step 7: Verifying pipeline data via API...');

    // Get doc_id from the uploaded document
    const docsListResponse = await request.get(`${API_URL}/api/v1/documents/`);
    const docsList = await docsListResponse.json();
    const uploadedDoc = docsList.find((d: any) => d.filename === 'test_pipeline_ui.txt');
    expect(uploadedDoc).toBeTruthy();
    const docId = uploadedDoc.doc_id;
    console.log(`  📝 Document ID: ${docId}`);

    // Fetch pipeline status from API
    const pipelineResponse = await request.get(`${API_URL}/api/v1/documents/${docId}/pipeline`);
    expect(pipelineResponse.ok()).toBeTruthy();
    const pipelineData = await pipelineResponse.json();

    console.log(`  📊 Pipeline Status:`);
    console.log(`     - Current Stage: ${pipelineData.current_stage}`);
    console.log(`     - Overall Status: ${pipelineData.overall_status}`);
    console.log(`     - Progress: ${pipelineData.progress_percentage}%`);
    console.log(`     - Total Duration: ${pipelineData.total_duration_seconds?.toFixed(2)}s`);
    console.log(`     - Stages: ${pipelineData.stages.length}`);

    // Verify pipeline structure
    expect(pipelineData).toHaveProperty('doc_id');
    expect(pipelineData).toHaveProperty('filename');
    expect(pipelineData).toHaveProperty('current_stage');
    expect(pipelineData).toHaveProperty('overall_status');
    expect(pipelineData).toHaveProperty('progress_percentage');
    expect(pipelineData).toHaveProperty('stages');
    expect(Array.isArray(pipelineData.stages)).toBeTruthy();
    expect(pipelineData.stages.length).toBeGreaterThan(0);

    // Verify at least "uploaded" stage exists
    const uploadedStageData = pipelineData.stages.find((s: any) => s.stage === 'uploaded');
    expect(uploadedStageData).toBeTruthy();
    expect(uploadedStageData.status).toBe('success');
    console.log('  ✅ "uploaded" stage found with success status');

    // STEP 8: Close modal
    console.log('\n❌ Step 8: Closing pipeline modal...');
    const closeButton = page.locator('button:has-text("關閉")').last();
    await closeButton.click();

    // Verify modal is closed
    await page.waitForSelector('h3:has-text("處理流程監控")', { state: 'hidden', timeout: 2000 });
    console.log('  ✅ Modal closed successfully');

    // STEP 9: Test auto-refresh behavior
    console.log('\n🔄 Step 9: Testing auto-refresh (if document still processing)...');

    // If document is still in progress, test auto-refresh
    if (pipelineData.overall_status === 'in_progress') {
      // Re-open modal
      await pipelineButton.click();
      await page.waitForSelector('h3:has-text("處理流程監控")');

      // Look for auto-refresh indicator
      const autoRefreshIndicator = page.locator('text=自動更新中');
      if (await autoRefreshIndicator.isVisible()) {
        console.log('  ✅ Auto-refresh indicator visible');

        // Wait a bit to see if progress updates
        await page.waitForTimeout(3000);
        console.log('  ⏳ Waited 3 seconds for potential updates');
      } else {
        console.log('  ⏭️  Document already complete - auto-refresh stopped');
      }

      // Close modal again
      await closeButton.click();
    } else {
      console.log('  ⏭️  Document complete - skipping auto-refresh test');
    }

    console.log('\n✅ All tests passed!');
  });

  test('should handle documents without pipeline data gracefully', async ({ page, request }) => {
    console.log('\n🧪 Testing graceful handling of missing pipeline data...');

    await page.goto('/documents');
    await page.waitForLoadState('networkidle');

    // Try to open pipeline modal for a document that might not have pipeline data
    const docRows = page.locator('div').filter({ hasText: /\.txt/ });
    const rowCount = await docRows.count();

    if (rowCount > 0) {
      const firstRow = docRows.first();
      const pipelineButton = firstRow.locator('button[title="查看處理流程"]');

      if (await pipelineButton.isVisible()) {
        await pipelineButton.click();

        // Modal should open even if data load fails
        await page.waitForSelector('h3:has-text("處理流程監控")', { timeout: 5000 });

        // Either show loading or error or data
        const loading = page.locator('text=載入流程狀態中');
        const error = page.locator('text=錯誤');
        const timeline = page.locator('h3:has-text("處理時間軸")');

        const hasLoading = await loading.isVisible().catch(() => false);
        const hasError = await error.isVisible().catch(() => false);
        const hasTimeline = await timeline.isVisible().catch(() => false);

        expect(hasLoading || hasError || hasTimeline).toBeTruthy();
        console.log('  ✅ Modal handles data loading gracefully');

        // Close modal
        const closeButton = page.locator('button:has-text("關閉")').last();
        await closeButton.click();
      } else {
        console.log('  ⏭️  No pipeline button found - test skipped');
      }
    } else {
      console.log('  ⏭️  No documents found - test skipped');
    }

    console.log('✅ Graceful handling test complete');
  });
});
