import { test, expect } from '@playwright/test'
import fs from 'fs'

/**
 * This test explores the Documents and Wiki pages to collect unimplemented tasks.
 * It checks for:
 * - Missing UI elements
 * - Broken functionality
 * - Incomplete features
 * - TODO comments in rendered UI
 */

test.describe('Collect Unimplemented Tasks', () => {
  const findings: string[] = []

  test.afterAll(async () => {
    // Write findings to a file
    const report = `# UI Unimplemented Tasks Report
Generated: ${new Date().toISOString()}

## Summary
Found ${findings.length} potential issues/unimplemented features

## Findings

${findings.map((f, i) => `### ${i + 1}. ${f}`).join('\n\n')}
`

    fs.writeFileSync('test-results/unimplemented-tasks.md', report)
    console.log('\n📋 Report saved to test-results/unimplemented-tasks.md')
    console.log(`Found ${findings.length} items`)
  })

  test('explore documents page for unimplemented features', async ({ page }) => {
    console.log('🔍 Exploring Documents page...')

    await page.goto('/documents')
    await page.waitForLoadState('networkidle')

    // Check if page loaded
    const heading = await page.locator('h1').textContent()
    console.log(`📄 Page heading: ${heading}`)

    // Take screenshot
    await page.screenshot({
      path: 'test-results/documents-page-full.png',
      fullPage: true,
    })

    // Check for metadata status indicators
    const hasMetadataStatus = await page
      .locator('text=/metadata/i, text=/元數據/i')
      .count()
    if (hasMetadataStatus === 0) {
      findings.push(
        '**Documents Page - Missing Metadata Status Indicators**\n' +
          '- No visible metadata extraction status (pending/processing/completed/failed)\n' +
          '- Users cannot see if metadata has been extracted\n' +
          '- Expected: Status badges like "✅ Metadata: Extracted" or "⏳ Metadata: Pending"'
      )
      console.log('❌ No metadata status indicators found')
    } else {
      console.log(`✅ Found ${hasMetadataStatus} metadata-related elements`)
    }

    // Check for re-extract button
    const hasReextractButton = await page
      .locator('button:has-text("重新提取"), button:has-text("Re-extract")')
      .count()
    if (hasReextractButton === 0) {
      findings.push(
        '**Documents Page - Missing Re-extract Metadata Button**\n' +
          '- No button to trigger metadata re-extraction for individual documents\n' +
          '- Users cannot retry failed extractions\n' +
          '- Expected: "重新提取元數據" button on each document card'
      )
      console.log('❌ No re-extract button found')
    } else {
      console.log(`✅ Found ${hasReextractButton} re-extract buttons`)
    }

    // Check for batch operations
    const hasBatchOperations = await page
      .locator('button:has-text("批次"), button:has-text("Batch")')
      .count()
    if (hasBatchOperations === 0) {
      findings.push(
        '**Documents Page - Missing Batch Operations**\n' +
          '- No batch re-extraction functionality\n' +
          '- Users cannot process multiple documents at once\n' +
          '- Expected: "批次重新提取" button to extract metadata for multiple pending documents'
      )
      console.log('❌ No batch operations found')
    } else {
      console.log(`✅ Found ${hasBatchOperations} batch operation buttons`)
    }

    // Check for metadata editor/view
    const hasMetadataEditor = await page
      .locator('button:has-text("編輯元數據"), button:has-text("Edit Metadata")')
      .count()
    if (hasMetadataEditor === 0) {
      findings.push(
        '**Documents Page - Missing Metadata Editor**\n' +
          '- No UI to view/edit document metadata\n' +
          '- Users cannot manually correct extraction errors\n' +
          '- Expected: Modal or detail page showing:\n' +
          '  - document_type (裁罰書/判決書/etc.)\n' +
          '  - issuing_authority (金管會/中央銀行/etc.)\n' +
          '  - related_institutions\n' +
          '  - violation_types\n' +
          '  - Edit and Save buttons'
      )
      console.log('❌ No metadata editor found')
    } else {
      console.log(`✅ Found ${hasMetadataEditor} metadata edit buttons`)
    }

    // Check for extraction confidence score
    const hasConfidenceScore = await page
      .locator('text=/confidence|信心|置信/i')
      .count()
    if (hasConfidenceScore === 0) {
      findings.push(
        '**Documents Page - Missing Extraction Confidence Score**\n' +
          '- No display of metadata extraction confidence\n' +
          '- Users cannot judge extraction quality\n' +
          '- Expected: Confidence score (0.0-1.0) or percentage shown for each document'
      )
      console.log('❌ No confidence score display found')
    } else {
      console.log(`✅ Found ${hasConfidenceScore} confidence-related elements`)
    }

    // Check for extraction error messages
    const hasErrorDisplay = await page
      .locator('.text-red, .error, [class*="error"]')
      .count()
    console.log(
      `ℹ️  Found ${hasErrorDisplay} potential error display elements (may be for upload errors)`
    )

    // Check document list for status columns
    const documentCards = await page.locator('[class*="hover:bg-gray"]').count()
    console.log(`📊 Found ${documentCards} document cards`)

    if (documentCards > 0) {
      // Check first document card structure
      const firstCard = page.locator('[class*="hover:bg-gray"]').first()
      const cardHtml = await firstCard.innerHTML()

      // Check for indexed status
      if (!cardHtml.includes('indexed') && !cardHtml.includes('索引')) {
        findings.push(
          '**Documents Page - Missing Indexed Status Display**\n' +
            '- Document cards do not show if document is indexed (searchable)\n' +
            '- Users cannot distinguish indexed vs non-indexed documents\n' +
            '- Expected: Badge showing "✅ 已索引" or "Indexed"'
        )
        console.log('❌ No indexed status in document cards')
      }

      // Check for metadata extraction status
      if (!cardHtml.includes('metadata') && !cardHtml.includes('元數據')) {
        findings.push(
          '**Documents Page - Missing Metadata Status in Document Cards**\n' +
            '- Document cards do not show metadata extraction status\n' +
            '- Users cannot see pending/processing/completed/failed state\n' +
            '- Expected: Status badge like "⏳ 元數據: 待處理" or "✅ 元數據: 已提取"'
        )
        console.log('❌ No metadata status in document cards')
      }
    }

    // Check for metadata monitor/dashboard
    const hasMonitorDashboard = await page
      .locator('text=/監控|monitor|dashboard|儀表板/i')
      .count()
    if (hasMonitorDashboard === 0) {
      findings.push(
        '**Documents Page - Missing Metadata Extraction Monitor**\n' +
          '- No dashboard showing extraction progress across all documents\n' +
          '- Users cannot see overall extraction status\n' +
          '- Expected: Dashboard card showing:\n' +
          '  - Total documents: X\n' +
          '  - Indexed: Y\n' +
          '  - Metadata extracted: Z\n' +
          '  - Pending: A\n' +
          '  - Processing: B\n' +
          '  - Failed: C'
      )
      console.log('❌ No metadata monitor dashboard found')
    } else {
      console.log(`✅ Found ${hasMonitorDashboard} monitor-related elements`)
    }
  })

  test('explore wiki page for unimplemented features', async ({ page }) => {
    console.log('🔍 Exploring Wiki page...')

    await page.goto('/wiki')
    await page.waitForLoadState('networkidle')

    // Check if page loaded
    const heading = await page.locator('h1').textContent()
    console.log(`📖 Page heading: ${heading}`)

    // Take screenshot
    await page.screenshot({ path: 'test-results/wiki-page-full.png', fullPage: true })

    // Check for category breakdown
    const hasCategoryBreakdown = await page
      .locator('text=/by type|by authority|按類型|按機關/i')
      .count()
    if (hasCategoryBreakdown === 0) {
      findings.push(
        '**Wiki Page - Missing Category Breakdown UI**\n' +
          '- No visual breakdown by document type, authority, institution, violation\n' +
          '- Users cannot explore documents by category\n' +
          '- Expected: Category cards showing:\n' +
          '  - 依文件類型: 裁罰書 (50), 判決書 (30), 法規 (20)\n' +
          '  - 依發文機關: 金管會 (60), 中央銀行 (25), 公平會 (15)\n' +
          '  - 依相關機構: 玉山銀行 (10), 中國信託 (8)\n' +
          '  - 依違規類型: 洗錢防制 (15), 內部控制 (12)'
      )
      console.log('❌ No category breakdown found')
    } else {
      console.log(`✅ Found ${hasCategoryBreakdown} category-related elements`)
    }

    // Check for metadata extraction statistics
    const hasExtractionStats = await page
      .locator('text=/extracted|提取|extraction/i')
      .count()
    if (hasExtractionStats === 0) {
      findings.push(
        '**Wiki Page - Missing Metadata Extraction Statistics**\n' +
          '- No display of how many documents have metadata vs without\n' +
          '- Users cannot see extraction progress\n' +
          '- Expected: Stats card showing:\n' +
          '  - Total documents: 100\n' +
          '  - With metadata: 45\n' +
          '  - Without metadata: 55\n' +
          '  - Extraction coverage: 45%'
      )
      console.log('❌ No extraction statistics found')
    } else {
      console.log(`✅ Found ${hasExtractionStats} extraction-related elements`)
    }

    // Check for search/filter functionality
    const hasSearchFilter = await page
      .locator('input[type="search"], input[placeholder*="搜"], input[placeholder*="Search"]')
      .count()
    console.log(`🔍 Found ${hasSearchFilter} search inputs`)

    if (hasSearchFilter === 0) {
      findings.push(
        '**Wiki Page - Missing Search/Filter Functionality**\n' +
          '- No search box to filter wiki entries\n' +
          '- Users cannot quickly find specific categories or topics\n' +
          '- Expected: Search input to filter by category name, institution, violation type'
      )
    }

    // Check for clickable categories
    const hasClickableCategories = await page
      .locator('button[class*="category"], a[class*="category"]')
      .count()
    if (hasClickableCategories === 0) {
      findings.push(
        '**Wiki Page - Missing Clickable Category Navigation**\n' +
          '- Categories are not clickable/interactive\n' +
          '- Users cannot drill down into specific categories\n' +
          '- Expected: Click "金管會" → Show all documents from 金管會\n' +
          '- Expected: Click "洗錢防制" → Show all documents about AML violations'
      )
      console.log('❌ No clickable categories found')
    } else {
      console.log(`✅ Found ${hasClickableCategories} clickable category elements`)
    }

    // Check for timeline/date filtering
    const hasTimelineFilter = await page
      .locator('text=/timeline|時間軸|year|年份|date range|日期範圍/i')
      .count()
    if (hasTimelineFilter === 0) {
      findings.push(
        '**Wiki Page - Missing Timeline/Date Filtering**\n' +
          '- No way to filter documents by date range or year\n' +
          '- Users cannot see trends over time\n' +
          '- Expected: Timeline showing document counts by year/quarter'
      )
      console.log('❌ No timeline filter found')
    } else {
      console.log(`✅ Found ${hasTimelineFilter} timeline-related elements`)
    }

    // Check for visualization/charts
    const hasCharts = await page.locator('svg, canvas, [class*="chart"]').count()
    console.log(`📊 Found ${hasCharts} potential chart elements`)

    if (hasCharts === 0) {
      findings.push(
        '**Wiki Page - Missing Data Visualizations**\n' +
          '- No charts or graphs showing wiki statistics\n' +
          '- Users have to read numbers instead of visual insights\n' +
          '- Expected: Charts showing:\n' +
          '  - Pie chart: Document distribution by type\n' +
          '  - Bar chart: Top institutions by document count\n' +
          '  - Line chart: Documents over time'
      )
    }

    // Check for empty state handling
    const bodyText = await page.locator('body').textContent()
    if (bodyText?.includes('No data') || bodyText?.includes('沒有資料')) {
      findings.push(
        '**Wiki Page - Showing Empty State**\n' +
          '- Wiki is showing "no data" message\n' +
          '- This could mean:\n' +
          '  1. No documents uploaded yet\n' +
          '  2. Documents uploaded but metadata not extracted\n' +
          '  3. Bug in wiki aggregation logic\n' +
          '- Action needed: Upload documents with metadata extraction enabled'
      )
      console.log('⚠️  Wiki showing empty state')
    }

    // Check for metadata quality indicators
    const hasQualityIndicators = await page
      .locator('text=/quality|quality|品質|準確/i')
      .count()
    if (hasQualityIndicators === 0) {
      findings.push(
        '**Wiki Page - Missing Metadata Quality Indicators**\n' +
          '- No indication of extraction quality or confidence\n' +
          '- Users cannot identify low-quality extractions\n' +
          '- Expected: Quality indicators showing:\n' +
          '  - Average confidence score\n' +
          '  - Number of low-confidence extractions\n' +
          '  - User edit count'
      )
      console.log('❌ No quality indicators found')
    } else {
      console.log(`✅ Found ${hasQualityIndicators} quality-related elements`)
    }
  })

  test('check for API response errors', async ({ page, request }) => {
    console.log('🔍 Checking API responses...')

    // Test documents API
    try {
      const docsResponse = await request.get('http://localhost:8000/api/v1/documents')
      if (!docsResponse.ok()) {
        findings.push(
          `**API Error - Documents Endpoint**\n` +
            `- Status: ${docsResponse.status()}\n` +
            `- URL: /api/v1/documents\n` +
            `- This will prevent documents from loading in UI`
        )
        console.log(`❌ Documents API returned ${docsResponse.status()}`)
      } else {
        const data = await docsResponse.json()
        console.log(`✅ Documents API working (${data.length} documents)`)

        // Check if documents have metadata status fields
        if (data.length > 0) {
          const firstDoc = data[0]
          if (!('metadata_extraction_status' in firstDoc)) {
            findings.push(
              `**API Response - Missing Metadata Status Fields**\n` +
                `- Documents API does not return metadata_extraction_status\n` +
                `- Frontend cannot display metadata extraction state\n` +
                `- Need to update DocumentResponse model to include:\n` +
                `  - metadata_extracted\n` +
                `  - metadata_extraction_status\n` +
                `  - metadata_last_extracted_at\n` +
                `  - metadata_edited_by_user`
            )
            console.log('❌ Documents missing metadata status fields')
          } else {
            console.log('✅ Documents include metadata status fields')
          }
        }
      }
    } catch (e) {
      findings.push(
        `**API Error - Documents Endpoint Unreachable**\n` +
          `- Error: ${e}\n` +
          `- Backend may not be running\n` +
          `- Check if server is running on port 8000`
      )
      console.log(`❌ Documents API error: ${e}`)
    }

    // Test wiki API
    try {
      const wikiResponse = await request.get('http://localhost:8000/api/v1/wiki/overview')
      if (!wikiResponse.ok()) {
        findings.push(
          `**API Error - Wiki Endpoint**\n` +
            `- Status: ${wikiResponse.status()}\n` +
            `- URL: /api/v1/wiki/overview\n` +
            `- This will prevent wiki from loading`
        )
        console.log(`❌ Wiki API returned ${wikiResponse.status()}`)
      } else {
        const data = await wikiResponse.json()
        console.log(
          `✅ Wiki API working (${data.total_documents} total, ${data.with_metadata} with metadata)`
        )

        // Check for metadata extraction stats
        if (data.with_metadata === 0 && data.total_documents > 0) {
          findings.push(
            `**Data Issue - No Documents with Metadata**\n` +
              `- Total documents: ${data.total_documents}\n` +
              `- With metadata: 0\n` +
              `- Wiki categories will be empty\n` +
              `- Action needed:\n` +
              `  1. Enable metadata extraction in uploads (extract_metadata=true)\n` +
              `  2. Run batch metadata extraction for existing documents\n` +
              `  3. Wait for LLM extraction to complete`
          )
          console.log('⚠️  No documents have metadata extracted')
        }
      }
    } catch (e) {
      findings.push(
        `**API Error - Wiki Endpoint Unreachable**\n` +
          `- Error: ${e}\n` +
          `- Backend may not be running`
      )
      console.log(`❌ Wiki API error: ${e}`)
    }

    // Test metadata status API (if implemented)
    try {
      const metadataStatusResponse = await request.get(
        'http://localhost:8000/api/v1/documents/metadata/status'
      )
      if (metadataStatusResponse.status() === 404) {
        findings.push(
          `**API Not Implemented - Metadata Status Endpoint**\n` +
            `- Endpoint: GET /api/v1/documents/metadata/status\n` +
            `- Returns: 404 Not Found\n` +
            `- This endpoint is needed for metadata extraction monitoring\n` +
            `- Implementation needed in src/finagent/api/routes/documents.py`
        )
        console.log('❌ Metadata status API not implemented (404)')
      } else if (metadataStatusResponse.ok()) {
        console.log('✅ Metadata status API implemented')
      }
    } catch (e) {
      console.log(`ℹ️  Could not check metadata status API: ${e}`)
    }
  })

  test('check browser console for errors', async ({ page }) => {
    console.log('🔍 Checking browser console...')

    const consoleErrors: string[] = []
    const consoleWarnings: string[] = []

    page.on('console', (msg) => {
      if (msg.type() === 'error') {
        consoleErrors.push(msg.text())
      } else if (msg.type() === 'warning') {
        consoleWarnings.push(msg.text())
      }
    })

    page.on('pageerror', (error) => {
      consoleErrors.push(`Page error: ${error.message}`)
    })

    // Visit both pages
    await page.goto('/documents')
    await page.waitForLoadState('networkidle')
    await page.waitForTimeout(2000)

    await page.goto('/wiki')
    await page.waitForLoadState('networkidle')
    await page.waitForTimeout(2000)

    if (consoleErrors.length > 0) {
      findings.push(
        `**Browser Console Errors**\n` +
          `- Found ${consoleErrors.length} console errors\n` +
          `- Errors:\n` +
          consoleErrors.map((e) => `  - ${e}`).join('\n')
      )
      console.log(`❌ Found ${consoleErrors.length} console errors`)
    } else {
      console.log('✅ No console errors found')
    }

    if (consoleWarnings.length > 0) {
      console.log(`⚠️  Found ${consoleWarnings.length} console warnings`)
    }
  })
})
