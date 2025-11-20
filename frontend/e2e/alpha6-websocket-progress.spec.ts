import { test, expect } from '@playwright/test'
import path from 'path'
import fs from 'fs'

test.describe('Alpha 6: WebSocket Upload with Progress Monitoring', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to documents page
    await page.goto('/documents')
    await page.waitForLoadState('networkidle')
  })

  test('should upload 10 documents with real-time progress monitoring', async ({ page }) => {
    // Verify we're on documents page
    await expect(page.locator('h1')).toContainText('文件管理')

    // Check initial state - should have 0 documents
    await expect(page.locator('text=沒有文件')).toBeVisible({ timeout: 5000 }).catch(() => {
      // If documents already exist, that's ok
    })

    // Prepare test files
    const testFiles = Array.from({ length: 10 }, (_, i) =>
      `/tmp/test_docs/test_doc_${i + 1}.txt`
    )

    // Verify test files exist
    for (const file of testFiles) {
      if (!fs.existsSync(file)) {
        throw new Error(`Test file not found: ${file}`)
      }
    }

    console.log('📂 Uploading 10 test documents...')

    // Upload all files
    const fileInput = page.locator('input[type="file"]')
    await fileInput.setInputFiles(testFiles)

    // Verify files added to queue
    await expect(page.locator('text=待上傳檔案 (10)')).toBeVisible({ timeout: 5000 })

    // Verify all 10 files listed
    for (let i = 1; i <= 10; i++) {
      await expect(page.locator(`text=test_doc_${i}.txt`)).toBeVisible()
    }

    // Click "Upload All" button
    const uploadButton = page.locator('button:has-text("上傳全部")')
    await expect(uploadButton).toBeVisible()
    await uploadButton.click()

    console.log('⏳ Monitoring upload progress...')

    // Monitor progress messages
    const progressMessages = [
      '上傳文件',
      '文件已儲存',
      '元數據已儲存',
      '正在建立向量索引',
      '分析文件內容',
      '索引完成',
      '上傳完成',
    ]

    // Wait for at least one progress message to appear
    await expect(
      page.locator('text=上傳文件').or(page.locator('text=文件已儲存'))
    ).toBeVisible({ timeout: 10000 })

    console.log('✅ Progress messages detected')

    // Wait for all uploads to complete (check for success icons)
    // Each file should show green checkmark
    await expect(async () => {
      const successIcons = await page.locator('svg.lucide-check-circle-2').count()
      expect(successIcons).toBe(10)
    }).toPass({ timeout: 120000 }) // 2 minutes max for 10 files

    console.log('✅ All 10 files uploaded successfully')

    // Verify chunk count is displayed for at least one file
    await expect(page.locator('text=個區塊').first()).toBeVisible({ timeout: 5000 })

    console.log('✅ Chunk counts displayed')

    // Verify success summary
    await expect(page.locator('text=成功: 10')).toBeVisible({ timeout: 5000 })

    console.log('✅ Success summary displayed')

    // Verify success notification
    await expect(page.locator('text=成功上傳 10 個文件')).toBeVisible({ timeout: 10000 })

    console.log('✅ Success notification displayed')

    // Wait for document list to refresh
    await page.waitForTimeout(2000)

    // Verify documents appear in the document list
    const documentList = page.locator('.bg-white.shadow.rounded-lg').nth(1) // Second card is document list

    // Check that at least 10 documents are now listed
    await expect(async () => {
      const docRows = await documentList.locator('[class*="grid"]').count()
      expect(docRows).toBeGreaterThanOrEqual(10)
    }).toPass({ timeout: 10000 })

    console.log('✅ Documents appear in document list')

    // Verify index status card shows correct counts
    const indexStatusCard = page.locator('text=索引狀態').locator('..')
    await expect(indexStatusCard.locator('text=10').first()).toBeVisible({ timeout: 5000 })

    console.log('✅ Index status updated')

    // Test progress bar visibility (at least one should have been visible during upload)
    // We can't easily verify this after the fact, but we can check success state

    // Click "Clear Completed" to clean up
    await page.locator('button:has-text("清除已完成")').click()

    // Verify upload queue is cleared
    await expect(page.locator('text=待上傳檔案')).not.toBeVisible({ timeout: 5000 })

    console.log('✅ Cleared completed uploads')
    console.log('🎉 All tests passed!')
  })

  test('should show progress messages in Traditional Chinese', async ({ page }) => {
    const testFile = '/tmp/test_docs/test_doc_1.txt'

    // Upload single file
    const fileInput = page.locator('input[type="file"]')
    await fileInput.setInputFiles([testFile])

    // Click upload
    await page.locator('button:has-text("上傳全部")').click()

    // Check for Traditional Chinese progress messages
    const chineseMessages = [
      '上傳文件',
      '文件已儲存',
      '元數據已儲存',
      '索引完成',
      '上傳完成',
    ]

    // At least one of these messages should appear
    let foundMessage = false
    for (const msg of chineseMessages) {
      const element = page.locator(`text=${msg}`)
      if (await element.isVisible({ timeout: 1000 }).catch(() => false)) {
        foundMessage = true
        console.log(`✅ Found message: ${msg}`)
        break
      }
    }

    expect(foundMessage).toBe(true)

    // Wait for completion
    await expect(page.locator('svg.lucide-check-circle-2')).toBeVisible({ timeout: 30000 })
  })

  test('should display chunk count after indexing', async ({ page }) => {
    const testFile = '/tmp/test_docs/test_doc_1.txt'

    // Upload single file
    const fileInput = page.locator('input[type="file"]')
    await fileInput.setInputFiles([testFile])

    await page.locator('button:has-text("上傳全部")').click()

    // Wait for upload to complete
    await expect(page.locator('svg.lucide-check-circle-2')).toBeVisible({ timeout: 30000 })

    // Verify chunk count is displayed
    await expect(page.locator('text=個區塊')).toBeVisible({ timeout: 5000 })

    console.log('✅ Chunk count displayed')
  })

  test('should handle multiple parallel uploads correctly', async ({ page }) => {
    const testFiles = Array.from({ length: 5 }, (_, i) =>
      `/tmp/test_docs/test_doc_${i + 1}.txt`
    )

    // Upload all files
    const fileInput = page.locator('input[type="file"]')
    await fileInput.setInputFiles(testFiles)

    // Click upload
    await page.locator('button:has-text("上傳全部")').click()

    // All files should show "uploading" state at some point
    await expect(page.locator('svg.lucide-loader-2').first()).toBeVisible({ timeout: 5000 })

    console.log('✅ Uploading state detected')

    // Wait for all to complete
    await expect(async () => {
      const successCount = await page.locator('svg.lucide-check-circle-2').count()
      expect(successCount).toBe(5)
    }).toPass({ timeout: 60000 })

    console.log('✅ All 5 files completed')

    // Verify success summary shows 5
    await expect(page.locator('text=成功: 5')).toBeVisible({ timeout: 5000 })
  })

  test('should update progress bar during upload', async ({ page }) => {
    const testFile = '/tmp/test_docs/test_doc_1.txt'

    // Upload single file
    const fileInput = page.locator('input[type="file"]')
    await fileInput.setInputFiles([testFile])

    await page.locator('button:has-text("上傳全部")').click()

    // Progress bar should be visible during upload
    const progressBar = page.locator('.bg-blue-600').first()

    // At some point, progress bar should be visible
    await expect(progressBar).toBeVisible({ timeout: 5000 })

    console.log('✅ Progress bar visible during upload')

    // Wait for completion
    await expect(page.locator('svg.lucide-check-circle-2')).toBeVisible({ timeout: 30000 })
  })

  test('should refresh document list after upload', async ({ page }) => {
    const testFile = '/tmp/test_docs/test_doc_1.txt'

    // Check initial document count
    const initialDocs = await page.locator('.bg-white.shadow.rounded-lg').nth(1).locator('[class*="grid"]').count().catch(() => 0)

    console.log(`Initial document count: ${initialDocs}`)

    // Upload file
    const fileInput = page.locator('input[type="file"]')
    await fileInput.setInputFiles([testFile])
    await page.locator('button:has-text("上傳全部")').click()

    // Wait for upload to complete
    await expect(page.locator('svg.lucide-check-circle-2')).toBeVisible({ timeout: 30000 })

    // Wait for document list to refresh
    await page.waitForTimeout(2000)

    // Document count should increase
    const finalDocs = await page.locator('.bg-white.shadow.rounded-lg').nth(1).locator('[class*="grid"]').count()

    console.log(`Final document count: ${finalDocs}`)

    expect(finalDocs).toBeGreaterThan(initialDocs)
  })
})
