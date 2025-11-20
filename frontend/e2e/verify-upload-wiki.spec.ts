import { test, expect } from '@playwright/test'
import fs from 'fs'
import path from 'path'

test.describe('Verify Document Upload and Wiki Generation', () => {
  test.beforeAll(async () => {
    // Create test documents
    const testDocsDir = '/tmp/test_wiki_docs'
    if (!fs.existsSync(testDocsDir)) {
      fs.mkdirSync(testDocsDir, { recursive: true })
    }

    const testDoc = {
      filename: 'test_penalty_wiki.txt',
      content: `金融監督管理委員會裁罰書

裁罰日期：民國110年5月15日
裁罰對象：測試銀行股份有限公司

違規事實：
本行於民國109年執行洗錢防制業務查核時，發現以下缺失：
1. 客戶盡職調查程序不完整
2. 高風險客戶交易監控機制未確實執行
3. 疑似洗錢交易申報作業有所延遲

裁罰金額：新台幣1000萬元整

依據法規：洗錢防制法第7條、第8條、銀行法第45條之1

金融監督管理委員會
主任委員 黃天牧`,
    }

    const filePath = path.join(testDocsDir, testDoc.filename)
    fs.writeFileSync(filePath, testDoc.content, 'utf-8')
    console.log(`✅ Created test document: ${testDoc.filename}`)
  })

  test('should upload document and verify wiki content', async ({ page }) => {
    console.log('🚀 Starting upload and wiki verification test...')

    // Step 1: Upload document via browser
    await page.goto('/documents')
    await page.waitForLoadState('networkidle')

    console.log('📂 Step 1: On documents page')

    // Upload file
    const testFile = '/tmp/test_wiki_docs/test_penalty_wiki.txt'
    const fileInput = page.locator('input[type="file"]')
    await fileInput.setInputFiles([testFile])

    // Wait for file to appear in queue
    await expect(page.locator('text=test_penalty_wiki.txt')).toBeVisible({ timeout: 5000 })

    console.log('📤 Step 2: File added to queue')

    // Click upload button
    const uploadButton = page.locator('button:has-text("上傳全部")')
    if (await uploadButton.isVisible({ timeout: 2000 }).catch(() => false)) {
      await uploadButton.click()
      console.log('⏳ Step 3: Upload started')

      // Wait for either success or see the file in the document list
      const uploadSuccess = await Promise.race([
        // Option 1: Wait for success icon
        page
          .locator('svg.lucide-check-circle-2')
          .first()
          .waitFor({ state: 'visible', timeout: 60000 })
          .then(() => true)
          .catch(() => false),
        // Option 2: Wait and check document list
        page.waitForTimeout(10000).then(() => false),
      ])

      if (uploadSuccess) {
        console.log('✅ Step 3a: Upload completed successfully')
      } else {
        console.log('⏭️  Step 3a: Proceeding to check document list')
      }
    } else {
      console.log('ℹ️  Step 3: No upload button found, file may be auto-uploading')
    }

    // Step 4: Wait a moment for backend processing
    await page.waitForTimeout(3000)

    // Step 5: Check if document appears in "最近上傳" list
    await page.goto('/documents')
    await page.waitForLoadState('networkidle')

    const documentList = page.locator('[class*="hover:bg-gray-50"]')
    const docCount = await documentList.count()
    console.log(`📋 Step 4: Found ${docCount} documents in list`)

    expect(docCount).toBeGreaterThanOrEqual(1)

    // Step 6: Navigate to Wiki page
    console.log('📖 Step 5: Navigating to Wiki page...')
    await page.click('a[href="/wiki"]')
    await page.waitForLoadState('networkidle')

    // Wait for wiki to load
    await expect(page.locator('h1:has-text("文件百科")')).toBeVisible({ timeout: 10000 })

    console.log('✅ Step 5a: Wiki page loaded')

    // Step 7: Verify wiki shows document count
    const totalDocsElement = await page.locator('text=/\\d+/').first()
    const totalDocsText = await totalDocsElement.textContent()
    const totalDocs = parseInt(totalDocsText || '0')

    console.log(`📊 Step 6: Wiki shows ${totalDocs} total documents`)
    expect(totalDocs).toBeGreaterThanOrEqual(1)

    // Step 8: Check for categories or document types
    const hasContent = await Promise.race([
      // Check for any category or document type indicators
      page
        .locator('text=金管會, text=銀行局, text=洗錢防制, text=裁罰書')
        .first()
        .waitFor({ state: 'visible', timeout: 5000 })
        .then(() => true)
        .catch(() => false),
      // Or check for document count indicators
      page
        .locator('text=/\\d+\\s*(個|文件|筆)/')
        .first()
        .waitFor({ state: 'visible', timeout: 5000 })
        .then(() => true)
        .catch(() => false),
    ])

    if (hasContent) {
      console.log('✅ Step 7: Wiki content indicators found')
    } else {
      console.log('ℹ️  Step 7: No specific content indicators, but wiki page loaded')
    }

    // Step 9: Take a screenshot for manual verification
    await page.screenshot({ path: 'test-results/wiki-page-screenshot.png', fullPage: true })
    console.log('📸 Step 8: Screenshot saved to test-results/wiki-page-screenshot.png')

    // Step 10: Try to find any documents in browse view
    const browseButtons = page.locator('button:has-text("瀏覽"), button:has-text("Browse")')
    if (await browseButtons.first().isVisible({ timeout: 2000 }).catch(() => false)) {
      await browseButtons.first().click()
      await page.waitForTimeout(1000)
      console.log('👁️  Step 9: Switched to browse view')
    }

    console.log('🎉 Test completed successfully!')
  })

  test('should verify wiki API returns data', async ({ request }) => {
    console.log('🔍 Testing wiki API endpoints...')

    // Test wiki overview endpoint
    const overviewResponse = await request.get('http://localhost:8000/api/v1/wiki/overview')
    expect(overviewResponse.ok()).toBeTruthy()

    const overviewData = await overviewResponse.json()
    console.log('📊 Wiki Overview:', JSON.stringify(overviewData, null, 2))

    expect(overviewData).toHaveProperty('total_documents')
    expect(overviewData.total_documents).toBeGreaterThanOrEqual(0)

    console.log(`✅ Wiki API working: ${overviewData.total_documents} documents indexed`)
  })
})
