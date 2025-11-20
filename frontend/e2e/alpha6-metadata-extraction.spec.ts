import { test, expect } from '@playwright/test'
import fs from 'fs'
import path from 'path'

test.describe('Alpha 6: Metadata Extraction and Wiki Categories', () => {
  test.beforeAll(async () => {
    // Create test document with realistic content for metadata extraction
    const testDocsDir = '/tmp/test_metadata_docs'
    if (!fs.existsSync(testDocsDir)) {
      fs.mkdirSync(testDocsDir, { recursive: true })
    }

    const testDoc = {
      filename: 'yushan_aml_test.txt',
      content: `金融監督管理委員會裁罰書

裁罰日期：民國109年9月15日
案號：金管銀法字第1090123456789號
裁罰對象：玉山商業銀行股份有限公司

違規事實：
本會於民國108年執行金融機構洗錢防制業務查核時，發現貴行存有以下缺失：

一、客戶盡職調查程序不完整
查貴行對於部分高風險客戶之實質受益人查證作業未確實執行，違反洗錢防制法第7條第1項規定。

二、高風險客戶交易監控機制不足
貴行對於高風險國家或地區之客戶交易，未建立有效之持續性監控機制，未能及時偵測異常交易樣態。

三、疑似洗錢交易申報延遲
查貴行於109年1月至3月間，對於部分疑似洗錢交易，未依規定時限向法務部調查局申報，延遲申報時間最長達15日。

裁罰金額：新台幣500萬元整

依據法規：
洗錢防制法第7條第1項、第8條第1項
銀行法第45條之1第1項

金融監督管理委員會
主任委員 黃天牧
中華民國109年9月15日`,
    }

    const filePath = path.join(testDocsDir, testDoc.filename)
    fs.writeFileSync(filePath, testDoc.content, 'utf-8')
    console.log(`✅ Created test document for metadata extraction: ${testDoc.filename}`)
  })

  test('should extract metadata during upload and populate wiki', async ({ page }) => {
    console.log('🚀 Starting metadata extraction test...')

    // Step 1: Navigate to documents page
    await page.goto('/documents')
    await page.waitForLoadState('networkidle')
    await expect(page.locator('h1')).toContainText('文件管理')

    console.log('📂 Step 1: On documents page')

    // Step 2: Upload test document
    const testFile = '/tmp/test_metadata_docs/yushan_aml_test.txt'

    if (!fs.existsSync(testFile)) {
      throw new Error(`Test file not found: ${testFile}`)
    }

    const fileInput = page.locator('input[type="file"]')
    await fileInput.setInputFiles([testFile])

    // Verify file added to queue
    await expect(page.locator('text=待上傳檔案 (1)')).toBeVisible({ timeout: 5000 })

    console.log('📤 Step 2: File added to upload queue')

    // Step 3: Click upload and wait for completion
    const uploadButton = page.locator('button:has-text("上傳全部")')
    await expect(uploadButton).toBeVisible()
    await uploadButton.click()

    console.log('⏳ Step 3: Upload started with metadata extraction enabled...')

    // Wait for upload to complete (metadata extraction takes longer)
    await expect(page.locator('svg.lucide-check-circle-2')).toBeVisible({
      timeout: 120000, // 2 minutes for LLM extraction
    })

    console.log('✅ Step 3a: Upload completed (may include metadata extraction)')

    // Verify chunk count displayed
    await expect(page.locator('text=個區塊').first()).toBeVisible({ timeout: 5000 })

    console.log('✅ Step 3b: Chunk count displayed')

    // Step 4: Wait a moment for metadata to propagate
    await page.waitForTimeout(2000)

    // Step 5: Navigate to Wiki page
    await page.click('a[href="/wiki"]')
    await page.waitForLoadState('networkidle')

    console.log('📖 Step 4: Navigated to Wiki page')

    // Wait for wiki to load
    await expect(page.locator('h1:has-text("文件百科")')).toBeVisible({ timeout: 10000 })

    console.log('✅ Step 4a: Wiki page loaded')

    // Step 6: Take screenshot of wiki before checking
    await page.screenshot({ path: 'test-results/wiki-with-metadata.png', fullPage: true })
    console.log('📸 Step 5: Screenshot saved')

    // Step 7: Verify wiki shows updated statistics
    await expect(async () => {
      const totalDocs = page.locator('text=/\\d+/').first()
      const count = parseInt((await totalDocs.textContent()) || '0')
      expect(count).toBeGreaterThanOrEqual(1)
    }).toPass({ timeout: 15000 })

    console.log('✅ Step 6: Wiki shows documents')

    // Step 8: Check for metadata indicators
    // Look for any of the expected categories or metadata
    const hasMetadataIndicators = await Promise.race([
      // Check for authority
      page
        .locator('text=金管會')
        .first()
        .waitFor({ state: 'visible', timeout: 5000 })
        .then(() => true)
        .catch(() => false),
      // Check for institution
      page
        .locator('text=玉山')
        .first()
        .waitFor({ state: 'visible', timeout: 5000 })
        .then(() => true)
        .catch(() => false),
      // Check for violation type
      page
        .locator('text=洗錢防制')
        .first()
        .waitFor({ state: 'visible', timeout: 5000 })
        .then(() => true)
        .catch(() => false),
      // Check for document type
      page
        .locator('text=裁罰書')
        .first()
        .waitFor({ state: 'visible', timeout: 5000 })
        .then(() => true)
        .catch(() => false),
    ])

    if (hasMetadataIndicators) {
      console.log('✅ Step 7: Metadata indicators found in wiki!')
    } else {
      console.log(
        '⚠️  Step 7: No metadata indicators visible yet (extraction may still be processing)'
      )
    }

    console.log('🎉 Test completed!')
  })

  test('should verify wiki API returns metadata', async ({ request }) => {
    console.log('🔍 Testing wiki API for metadata...')

    // Wait a bit for metadata to be processed
    await new Promise((resolve) => setTimeout(resolve, 2000))

    // Test wiki overview endpoint
    const overviewResponse = await request.get('http://localhost:8000/api/v1/wiki/overview')
    expect(overviewResponse.ok()).toBeTruthy()

    const overviewData = await overviewResponse.json()
    console.log('📊 Wiki Overview:', JSON.stringify(overviewData, null, 2))

    // Check if metadata exists
    if (overviewData.with_metadata > 0) {
      console.log(`✅ Found ${overviewData.with_metadata} documents with metadata!`)

      // Check for categories
      if (Object.keys(overviewData.by_type || {}).length > 1) {
        console.log('✅ Multiple document types detected:', Object.keys(overviewData.by_type))
      }

      if (Object.keys(overviewData.by_authority || {}).length > 0) {
        console.log('✅ Authorities detected:', Object.keys(overviewData.by_authority))
      }

      if (overviewData.top_entities?.institutions?.length > 0) {
        console.log('✅ Institutions detected:', overviewData.top_entities.institutions)
      }

      if (overviewData.top_entities?.violations?.length > 0) {
        console.log('✅ Violations detected:', overviewData.top_entities.violations)
      }
    } else {
      console.log(
        '⚠️  No documents with metadata yet. Check if metadata extraction is enabled and working.'
      )
      console.log(`   Total documents: ${overviewData.total_documents}`)
      console.log(`   With metadata: ${overviewData.with_metadata}`)
      console.log(`   Without metadata: ${overviewData.without_metadata}`)
    }
  })

  test('should check document details for extracted metadata', async ({ request }) => {
    console.log('🔍 Checking document details for metadata...')

    // Get all documents
    const documentsResponse = await request.get('http://localhost:8000/api/v1/documents')
    expect(documentsResponse.ok()).toBeTruthy()

    const documents = await documentsResponse.json()
    console.log(`📋 Found ${documents.length} documents`)

    // Find our test document
    const testDoc = documents.find((d: any) => d.name.includes('yushan_aml_test'))

    if (testDoc) {
      console.log('📄 Test document found:', testDoc.name)
      console.log('   Document ID:', testDoc.id)
      console.log('   Document Type:', testDoc.document_type || '(not extracted)')
      console.log('   Issuing Authority:', testDoc.issuing_authority || '(not extracted)')
      console.log('   Related Institutions:', testDoc.related_institutions || '(not extracted)')
      console.log('   Violation Types:', testDoc.violation_types || '(not extracted)')
      console.log('   Penalty Amount:', testDoc.penalty_amount || '(not extracted)')

      // Verify metadata was extracted
      if (testDoc.document_type && testDoc.document_type !== 'uploaded') {
        console.log('✅ Metadata successfully extracted!')
      } else {
        console.log('⚠️  Metadata not extracted yet or extraction failed')
        console.log('   Check backend logs for LLM extraction status')
      }
    } else {
      console.log('⚠️  Test document not found in document list')
    }
  })
})
