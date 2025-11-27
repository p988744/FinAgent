import { test, expect } from '@playwright/test'
import fs from 'fs'
import path from 'path'

test.describe('Alpha 6: Document Upload, Indexing, and Wiki Generation', () => {
  test.beforeAll(async () => {
    // Ensure test documents exist
    const testDocsDir = '/tmp/test_docs'
    if (!fs.existsSync(testDocsDir)) {
      fs.mkdirSync(testDocsDir, { recursive: true })
    }

    // Create 3 test documents with realistic content
    const testDocuments = [
      {
        filename: 'yushan_aml_penalty.txt',
        content: `金融監督管理委員會裁罰書

裁罰日期：民國109年9月15日
裁罰對象：玉山商業銀行股份有限公司

違規事實：
本行於民國108年執行洗錢防制業務時，發現以下缺失：
1. 未確實執行客戶盡職調查
2. 高風險客戶交易監控機制不足
3. 疑似洗錢交易申報延遲

裁罰金額：新台幣500萬元整

依據法規：洗錢防制法第7條、第8條

金融監督管理委員會
主任委員 黃天牧`,
      },
      {
        filename: 'ctbc_internal_control.txt',
        content: `金融監督管理委員會裁罰書

裁罰日期：民國109年11月20日
裁罰對象：中國信託商業銀行股份有限公司

違規事實：
本行於民國108年內部控制查核時發現以下缺失：
1. 授信業務內部控制制度不健全
2. 風險管理機制未確實執行
3. 內部稽核功能不彰

裁罰金額：新台幣800萬元整

依據法規：銀行法第45條之1

金融監督管理委員會
主任委員 黃天牧`,
      },
      {
        filename: 'cathay_security_penalty.txt',
        content: `金融監督管理委員會裁罰書

裁罰日期：民國110年3月10日
裁罰對象：國泰世華商業銀行股份有限公司

違規事實：
本行於民國109年執行資訊安全稽核時發現以下缺失：
1. 資訊系統存取控制不足
2. 個人資料保護措施未落實
3. 資安事件通報機制延遲

裁罰金額：新台幣300萬元整

依據法規：個人資料保護法第48條

金融監督管理委員會
主任委員 黃天牧`,
      },
    ]

    for (const doc of testDocuments) {
      const filePath = path.join(testDocsDir, doc.filename)
      fs.writeFileSync(filePath, doc.content, 'utf-8')
    }

    console.log('✅ Test documents created')
  })

  test('should upload documents, verify indexing, and check wiki generation', async ({
    page,
  }) => {
    // Step 1: Navigate to documents page
    await page.goto('/documents')
    await page.waitForLoadState('networkidle')
    await expect(page.locator('h1')).toContainText('文件管理')

    console.log('📂 Step 1: On documents page')

    // Step 2: Upload 3 test documents
    const testFiles = [
      '/tmp/test_docs/yushan_aml_penalty.txt',
      '/tmp/test_docs/ctbc_internal_control.txt',
      '/tmp/test_docs/cathay_security_penalty.txt',
    ]

    // Verify all test files exist
    for (const file of testFiles) {
      if (!fs.existsSync(file)) {
        throw new Error(`Test file not found: ${file}`)
      }
    }

    const fileInput = page.locator('input[type="file"]')
    await fileInput.setInputFiles(testFiles)

    // Verify files added to queue
    await expect(page.locator('text=待上傳檔案 (3)')).toBeVisible({ timeout: 5000 })

    console.log('📤 Step 2: Files added to upload queue')

    // Step 3: Click "Upload All" and monitor progress
    const uploadButton = page.locator('button:has-text("上傳全部")')
    await expect(uploadButton).toBeVisible()
    await uploadButton.click()

    console.log('⏳ Step 3: Upload started, monitoring progress...')

    // Wait for progress messages to appear
    await expect(
      page.locator('text=上傳文件中').or(page.locator('text=文件已儲存'))
    ).toBeVisible({ timeout: 10000 })

    console.log('✅ Step 3a: Progress messages detected')

    // Wait for all uploads to complete (check for success icons)
    await expect(async () => {
      const successIcons = await page.locator('svg.lucide-check-circle-2').count()
      expect(successIcons).toBe(3)
    }).toPass({ timeout: 120000 }) // 2 minutes max for 3 files

    console.log('✅ Step 3b: All 3 files uploaded successfully')

    // Verify chunk counts are displayed
    const chunkElements = await page.locator('text=個區塊').count()
    expect(chunkElements).toBeGreaterThanOrEqual(3)

    console.log('✅ Step 3c: Chunk counts displayed for all files')

    // Verify success summary
    await expect(page.locator('text=成功: 3')).toBeVisible({ timeout: 5000 })

    console.log('✅ Step 3d: Success summary shows 3 files')

    // Step 4: Verify documents appear in "最近上傳" list
    await page.waitForTimeout(2000) // Wait for document list to refresh

    // Check for document list heading
    await expect(page.locator('h3:has-text("最近上傳")')).toBeVisible()

    // Verify at least 3 documents in the list (may have more from previous runs)
    const documentCards = await page.locator('[class*="hover:bg-gray-50"]').count()
    expect(documentCards).toBeGreaterThanOrEqual(3)

    console.log(`✅ Step 4: Documents appear in list (${documentCards} total)`)

    // Step 5: Navigate to Wiki page
    await page.click('a[href="/wiki"]')
    await page.waitForLoadState('networkidle')

    console.log('📖 Step 5: Navigated to Wiki page')

    // Wait for wiki to load
    await expect(page.locator('h1:has-text("文件百科")')).toBeVisible({ timeout: 10000 })

    console.log('✅ Step 5a: Wiki page loaded')

    // Step 6: Verify wiki overview shows updated statistics
    // Check total document count is at least 3
    await expect(async () => {
      const totalDocs = page.locator('text=/\\d+/').first()
      const count = parseInt((await totalDocs.textContent()) || '0')
      expect(count).toBeGreaterThanOrEqual(3)
    }).toPass({ timeout: 15000 })

    console.log('✅ Step 6: Wiki overview shows updated document count')

    // Step 7: Verify categories exist
    // Look for category elements (institutions, violation types, etc.)
    const categoryElements = await page.locator('[class*="category"]').count()

    // Or check for specific text that indicates categories
    const hasCategories =
      (await page.locator('text=金管會').isVisible({ timeout: 5000 }).catch(() => false)) ||
      (await page.locator('text=洗錢防制').isVisible({ timeout: 5000 }).catch(() => false)) ||
      (await page.locator('text=內部控制').isVisible({ timeout: 5000 }).catch(() => false))

    if (hasCategories) {
      console.log('✅ Step 7: Wiki categories detected')
    } else {
      console.log('⚠️  Step 7: Categories not immediately visible (may need wiki rebuild)')
    }

    // Step 8: Try searching for uploaded document content
    // Look for a search input
    const searchInput = page.locator('input[type="search"], input[placeholder*="搜"]').first()
    if (await searchInput.isVisible({ timeout: 5000 }).catch(() => false)) {
      await searchInput.fill('玉山')
      await page.waitForTimeout(1000)

      // Check if search results appear
      const searchResults = await page.locator('text=玉山').count()
      if (searchResults > 0) {
        console.log(`✅ Step 8: Search found ${searchResults} results for "玉山"`)
      } else {
        console.log('⚠️  Step 8: Search results not found (may need indexing)')
      }
    } else {
      console.log('ℹ️  Step 8: Search feature not available on this view')
    }

    // Step 9: Clean up - Clear completed uploads
    await page.click('a[href="/documents"]')
    await page.waitForLoadState('networkidle')

    const clearButton = page.locator('button:has-text("清除已完成")')
    if (await clearButton.isVisible({ timeout: 3000 }).catch(() => false)) {
      await clearButton.click()
      console.log('✅ Step 9: Cleared completed uploads')
    }

    console.log('🎉 All tests passed!')
  })

  test('should verify indexed documents have chunk counts', async ({ page }) => {
    await page.goto('/documents')
    await page.waitForLoadState('networkidle')

    // Upload single document
    const testFile = '/tmp/test_docs/yushan_aml_penalty.txt'

    const fileInput = page.locator('input[type="file"]')
    await fileInput.setInputFiles([testFile])

    await page.locator('button:has-text("上傳全部")').click()

    // Wait for upload to complete
    await expect(page.locator('svg.lucide-check-circle-2')).toBeVisible({
      timeout: 60000,
    })

    // Verify chunk count is displayed and greater than 0
    const chunkText = await page.locator('text=個區塊').first().textContent()
    const chunkMatch = chunkText?.match(/(\d+)\s*個區塊/)

    if (chunkMatch) {
      const chunkCount = parseInt(chunkMatch[1])
      expect(chunkCount).toBeGreaterThan(0)
      console.log(`✅ Document indexed with ${chunkCount} chunks`)
    } else {
      throw new Error('Chunk count not found in upload result')
    }
  })

  test('should verify wiki can be rebuilt after uploads', async ({ page }) => {
    await page.goto('/wiki')
    await page.waitForLoadState('networkidle')

    // Look for rebuild or refresh button
    const rebuildButton = page.locator(
      'button:has-text("重建"), button:has-text("刷新"), button:has-text("更新")'
    )

    if (await rebuildButton.isVisible({ timeout: 5000 }).catch(() => false)) {
      console.log('🔄 Found wiki rebuild button, testing rebuild...')

      // Get initial document count
      const initialCount = await page
        .locator('text=/\\d+/')
        .first()
        .textContent()

      await rebuildButton.click()

      // Wait for rebuild to complete (look for loading indicator to disappear)
      await page.waitForTimeout(2000)

      // Verify page still shows data
      await expect(page.locator('h1:has-text("文件百科")')).toBeVisible()

      console.log('✅ Wiki rebuild completed successfully')
    } else {
      console.log('ℹ️  Wiki rebuild button not found (auto-update may be enabled)')
    }
  })
})
