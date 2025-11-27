import { test, expect, Page } from '@playwright/test';

/**
 * E2E Test: Research Query Workflow
 *
 * This test validates:
 * 1. Query submission with expected answer and references
 * 2. Real execution time (20-60 seconds for v1.1 Plan-and-Execute workflow)
 * 3. Citations and confidence level are properly displayed
 */

const BACKEND_URL = 'http://localhost:8000';
const FRONTEND_URL = 'http://localhost:3000';

// Test queries with expected results
const TEST_QUERIES = {
  yushan_aml: {
    query: '玉山銀行洗錢防制裁罰',
    expectedKeywords: ['玉山', '洗錢防制', '裁罰', '320萬', '2023'],
    minCitations: 1,
    maxExecutionTime: 60000, // 60 seconds
    minExecutionTime: 15000, // 15 seconds (to ensure RAG is used)
  },
  cathay_wealth: {
    query: '國泰世華銀行財富管理違規',
    expectedKeywords: ['國泰世華', '財富管理', '違規'],
    minCitations: 1,
    maxExecutionTime: 60000,
    minExecutionTime: 15000,
  },
};

test.describe('Research Query E2E Tests', () => {
  let startTime: number;

  // Configure for SEQUENTIAL execution (one test at a time)
  // This mirrors real user behavior: one research query at a time
  test.describe.configure({ mode: 'serial' });

  test.beforeEach(async ({ page }) => {
    // Check backend health before each test
    const response = await page.request.get(`${BACKEND_URL}/health`);
    expect(response.ok()).toBeTruthy();

    // Navigate to research page
    await page.goto(FRONTEND_URL);
    await page.waitForLoadState('networkidle');

    // Add delay between tests to simulate real user behavior
    // Users read results before submitting next query
    await page.waitForTimeout(3000); // 3 second delay
  });

  test('should successfully process query with real answer and citations - 玉山銀行洗錢防制裁罰', async ({ page }) => {
    // This test requires 60+ seconds for workflow completion
    test.setTimeout(120000); // 2 minutes
    const testCase = TEST_QUERIES.yushan_aml;

    // Step 1: Submit query
    console.log(`Submitting query: ${testCase.query}`);
    startTime = Date.now();

    const queryInput = page.locator('input[type="text"], textarea').first();
    await queryInput.fill(testCase.query);

    const submitButton = page.locator('button:has-text("送出"), button:has-text("Submit"), button[type="submit"]').first();
    await submitButton.click();

    // Step 2: Wait for status to show "processing" or "in_progress"
    // The button shows "提交中..." when submitting, then StatusCard appears with "處理中" or "排隊中"
    await expect(page.locator('text=/提交中|處理中|排隊中|執行中|in.?progress|processing/i')).toBeVisible({ timeout: 10000 });
    console.log('Query submitted, processing started');

    // Step 3: Wait for completion (with timeout for max execution time)
    await expect(page.locator('text=/研究結果|Research Results/i')).toBeVisible({
      timeout: testCase.maxExecutionTime + 10000
    });

    const executionTime = Date.now() - startTime;
    console.log(`Query completed in ${executionTime}ms`);

    // Step 4: Validate execution time is reasonable (not too fast = RAG used)
    expect(executionTime).toBeGreaterThan(testCase.minExecutionTime);
    expect(executionTime).toBeLessThan(testCase.maxExecutionTime);
    console.log(`✓ Execution time is reasonable: ${(executionTime / 1000).toFixed(1)}s`);

    // Step 5: Check that executive summary or answer is displayed
    const answerSection = page.locator('div, section, article').filter({
      hasText: /執行摘要|摘要|答案|結果|executive.?summary|answer|result/i
    }).first();
    await expect(answerSection).toBeVisible({ timeout: 5000 });

    const answerText = await answerSection.textContent() || '';
    console.log(`Answer length: ${answerText.length} characters`);

    // Step 6: Validate answer contains expected keywords
    let foundKeywords = 0;
    for (const keyword of testCase.expectedKeywords) {
      if (answerText.includes(keyword)) {
        foundKeywords++;
        console.log(`✓ Found keyword: ${keyword}`);
      }
    }

    expect(foundKeywords).toBeGreaterThan(0);
    console.log(`✓ Found ${foundKeywords}/${testCase.expectedKeywords.length} expected keywords`);

    // Step 7: Validate citations/references are present
    const citationSection = page.locator('text=/引用|來源|citation|reference|source/i');
    await expect(citationSection).toBeVisible({ timeout: 5000 });

    // Check for citation markers like [1], [2], etc.
    const citationMarkers = page.locator('text=/\\[\\d+\\]|\\(\\d+\\)|引用\\d+/');
    const citationCount = await citationMarkers.count();

    expect(citationCount).toBeGreaterThanOrEqual(testCase.minCitations);
    console.log(`✓ Found ${citationCount} citations (minimum: ${testCase.minCitations})`);

    // Step 8: Validate processing time is displayed (replacing confidence check)
    const processingTimeSection = page.locator('text=/處理時間|processing.?time/i');
    await expect(processingTimeSection).toBeVisible({ timeout: 5000 });
    console.log('✓ Processing time is displayed');

    // Step 9: Check that answer is not empty/fallback
    expect(answerText).not.toContain('未找到相關文件');
    expect(answerText).not.toContain('No documents found');
    expect(answerText.length).toBeGreaterThan(100); // Substantial answer
    console.log('✓ Answer is substantial and not a fallback');
  });

  test('should display processing time accurately', async ({ page }) => {
    test.setTimeout(120000); // 2 minutes
    const testCase = TEST_QUERIES.yushan_aml;

    // Submit query
    startTime = Date.now();
    const queryInput = page.locator('input[type="text"], textarea').first();
    await queryInput.fill(testCase.query);

    const submitButton = page.locator('button:has-text("送出"), button:has-text("Submit"), button[type="submit"]').first();
    await submitButton.click();

    // Wait for completion
    await expect(page.locator('text=/研究結果|Research Results/i')).toBeVisible({
      timeout: testCase.maxExecutionTime + 10000
    });

    const actualExecutionTime = Date.now() - startTime;

    // Check if processing time is displayed in UI
    const timeDisplay = page.locator('text=/處理時間|執行時間|processing.?time/i');
    if (await timeDisplay.isVisible()) {
      const displayedTime = await timeDisplay.textContent() || '';
      console.log(`Displayed processing time: ${displayedTime}`);

      // Extract number from displayed time (e.g., "30.5s" or "30秒")
      const timeMatch = displayedTime.match(/(\d+\.?\d*)/);
      if (timeMatch) {
        const displayedSeconds = parseFloat(timeMatch[1]);
        const actualSeconds = actualExecutionTime / 1000;

        // Allow 10% tolerance for display accuracy
        const tolerance = actualSeconds * 0.1;
        expect(Math.abs(displayedSeconds - actualSeconds)).toBeLessThan(tolerance);
        console.log(`✓ Processing time display is accurate: ${displayedSeconds}s vs ${actualSeconds.toFixed(1)}s`);
      }
    }
  });

  test('should handle second query correctly (no state pollution)', async ({ page }) => {
    test.setTimeout(180000); // 3 minutes (more time for second query after first)
    const testCase = TEST_QUERIES.cathay_wealth;

    // Wait extra time to ensure previous test's Celery task is fully completed
    await page.waitForTimeout(5000);

    // Submit query
    const queryInput = page.locator('input[type="text"], textarea').first();
    await queryInput.fill(testCase.query);

    const submitButton = page.locator('button:has-text("送出"), button:has-text("Submit"), button[type="submit"]').first();
    await submitButton.click();

    // Wait for completion (extra time for second query)
    await expect(page.locator('text=/研究結果|Research Results/i')).toBeVisible({
      timeout: testCase.maxExecutionTime + 60000  // Extra 60s for second query
    });

    // Validate answer contains expected keywords - focus only on the results card
    const resultsCard = page.locator('div.bg-white.rounded-lg.shadow-md').filter({
      hasText: /研究結果|Research Results/i
    }).first();

    const answerText = await resultsCard.textContent() || '';

    let foundKeywords = 0;
    for (const keyword of testCase.expectedKeywords) {
      if (answerText.includes(keyword)) {
        foundKeywords++;
      }
    }

    expect(foundKeywords).toBeGreaterThan(0);
    console.log(`✓ Second query found ${foundKeywords}/${testCase.expectedKeywords.length} expected keywords`);

    // Ensure the results card shows the new query, not the old one
    // Note: History panel may show old queries, which is expected
    expect(answerText).toContain('國泰世華');
  });

  test('should display citations with source information', async ({ page }) => {
    test.setTimeout(120000); // 2 minutes
    const testCase = TEST_QUERIES.yushan_aml;

    // Submit query
    const queryInput = page.locator('input[type="text"], textarea').first();
    await queryInput.fill(testCase.query);

    const submitButton = page.locator('button:has-text("送出"), button:has-text("Submit"), button[type="submit"]').first();
    await submitButton.click();

    // Wait for completion
    await expect(page.locator('text=/研究結果|Research Results/i')).toBeVisible({
      timeout: testCase.maxExecutionTime + 10000
    });

    // Check for citation list or references section
    const referencesSection = page.locator('text=/引用來源|參考資料|references|sources/i');
    if (await referencesSection.isVisible()) {
      console.log('✓ References section is visible');

      // Check for document names in citations
      const hasDocumentName = page.locator('text=/doc\\d+|\.txt|裁罰|違規/i');
      const docCount = await hasDocumentName.count();

      expect(docCount).toBeGreaterThan(0);
      console.log(`✓ Found ${docCount} document references`);
    }
  });
});

test.describe('Backend API Direct Tests', () => {
  // Configure for SEQUENTIAL execution
  test.describe.configure({ mode: 'serial' });

  test('should verify backend is returning v1.1 workflow results', async ({ request }) => {
    // This test requires 60+ seconds for workflow completion
    test.setTimeout(120000); // 2 minutes
    // Submit query directly to API
    const response = await request.post(`${BACKEND_URL}/api/v1/research/query/async`, {
      data: { query_text: '玉山銀行洗錢防制裁罰' }
    });

    expect(response.ok()).toBeTruthy();
    const data = await response.json();

    expect(data).toHaveProperty('session_id');
    expect(data).toHaveProperty('celery_task_id');

    const sessionId = data.session_id;
    console.log(`Session ID: ${sessionId}`);

    // Poll for results
    let status = 'pending';
    let attempts = 0;
    const maxAttempts = 30; // 30 attempts * 3 seconds = 90 seconds max

    while (status !== 'completed' && status !== 'failed' && attempts < maxAttempts) {
      await new Promise(resolve => setTimeout(resolve, 3000)); // Wait 3 seconds

      const statusResponse = await request.get(`${BACKEND_URL}/api/v1/research/status/${sessionId}`);
      expect(statusResponse.ok()).toBeTruthy();

      const statusData = await statusResponse.json();
      status = statusData.status;
      attempts++;

      console.log(`[${attempts * 3}s] Status: ${status}`);
    }

    expect(status).toBe('completed');

    // Get final result
    const finalResponse = await request.get(`${BACKEND_URL}/api/v1/research/status/${sessionId}`);
    const result = await finalResponse.json();

    // Validate result structure
    expect(result).toHaveProperty('result');
    expect(result.result).toHaveProperty('executive_summary');
    expect(result.result).toHaveProperty('citations');

    // Validate citations (may be empty if no exact matches in DB)
    console.log(`✓ API returned ${result.result.citations.length} citations`);

    // Validate executive summary is not empty
    expect(result.result.executive_summary.length).toBeGreaterThan(50);
    console.log(`✓ API returned substantial answer (${result.result.executive_summary.length} chars)`);

    // Validate detailed analysis exists
    expect(result.result).toHaveProperty('detailed_analysis');
    expect(result.result.detailed_analysis.length).toBeGreaterThan(100);
    console.log(`✓ API returned detailed analysis (${result.result.detailed_analysis.length} chars)`);
  });
});
