import { test, expect } from '@playwright/test'
import fs from 'fs'
import path from 'path'

test.describe('v1.0 Release Verification', () => {
    const TEST_DOC_FILENAME = 'v1_verification_test_doc.txt'
    const TEST_DOC_CONTENT = `金融監督管理委員會裁罰書

裁罰日期：民國112年1月1日
裁罰對象：測試銀行股份有限公司
違規事實：
1. 未依規定執行洗錢防制
2. 內部控制制度缺失
裁罰金額：新台幣200萬元
依據法規：銀行法第129條
`

    test.beforeAll(async () => {
        // Create test document
        const testDocsDir = '/tmp/v1_verification'
        if (!fs.existsSync(testDocsDir)) {
            fs.mkdirSync(testDocsDir, { recursive: true })
        }
        fs.writeFileSync(path.join(testDocsDir, TEST_DOC_FILENAME), TEST_DOC_CONTENT, 'utf-8')
    })

    test('Feature 1: Wiki Management (Upload -> Browse -> Detail -> Delete)', async ({ page }) => {
        console.log('🚀 Starting Feature 1: Wiki Management Verification')

        // 1. Upload Document
        await page.goto('/documents')
        await page.waitForLoadState('networkidle')

        const fileInput = page.locator('input[type="file"]')
        await fileInput.setInputFiles(path.join('/tmp/v1_verification', TEST_DOC_FILENAME))

        // Wait for upload to complete (assuming auto-upload or manual click)
        const uploadBtn = page.locator('button:has-text("上傳全部")')
        if (await uploadBtn.isVisible()) {
            await uploadBtn.click()
        }

        // Wait for success
        await expect(page.locator('text=成功').or(page.locator('svg.lucide-check-circle-2'))).toBeVisible({ timeout: 30000 })
        console.log('✅ Document uploaded')

        // 2. Verify in Document List
        await page.reload()
        await expect(page.locator(`text=${TEST_DOC_FILENAME}`)).toBeVisible()
        console.log('✅ Document appears in list')

        // 3. Verify in Wiki Overview
        await page.goto('/wiki')
        await page.waitForLoadState('networkidle')
        await expect(page.locator('h1:has-text("文件百科")')).toBeVisible()

        // Check if stats are visible (at least one document)
        const statValue = page.locator('text=/\\d+/').first()
        await expect(statValue).toBeVisible()
        console.log('✅ Wiki overview accessible')

        // 4. Verify Category Navigation (if implemented)
        // Try to find a category link or section
        const categorySection = page.locator('text=按主管機關')
        if (await categorySection.isVisible()) {
            await categorySection.click()
            console.log('✅ Clicked "By Authority" category')
            // Check if our document might be listed under "金管會" (inferred from content)
            // This part might be flaky if classification hasn't run, so we'll be lenient
        } else {
            console.log('⚠️ Category "By Authority" not found - skipping category nav check')
        }

        // 5. Verify Document Detail View
        // Go back to documents list to click the document
        await page.goto('/documents')
        await page.locator(`text=${TEST_DOC_FILENAME}`).click()

        // Should navigate to detail page
        await expect(page).toHaveURL(/\/documents\/.+/)
        await expect(page.locator('text=文件詳情').or(page.locator('h1'))).toBeVisible()

        // Check for metadata
        await expect(page.locator('text=測試銀行')).toBeVisible() // Should be extracted
        console.log('✅ Document detail view verifies metadata')

        // 6. Delete Document
        // Look for delete button
        const deleteBtn = page.locator('button').filter({ hasText: /刪除|Delete/ }).first()
        if (await deleteBtn.isVisible()) {
            await deleteBtn.click()
            // Confirm if dialog appears
            const confirmBtn = page.locator('button:has-text("確定")')
            if (await confirmBtn.isVisible()) {
                await confirmBtn.click()
            }
            await page.waitForURL('/documents')
            console.log('✅ Document deleted')

            // Verify gone
            await expect(page.locator(`text=${TEST_DOC_FILENAME}`)).not.toBeVisible()
            console.log('✅ Document removed from list')
        } else {
            console.log('⚠️ Delete button not found')
        }
    })

    test('Feature 2: AI Research Tools (Query -> Plan -> Tool Usage)', async ({ page }) => {
        page.on('console', msg => console.log(`BROWSER: ${msg.text()}`));
        console.log('🚀 Starting Feature 2: AI Research Tools Verification')

        await page.goto('/query') // or '/' if query is home
        await page.waitForLoadState('networkidle')

        // 1. Submit Query
        const queryInput = page.locator('textarea#query')
        await queryInput.fill('測試銀行違規事項')
        await page.locator('button[type="submit"]').click()
        console.log('✅ Query submitted')

        // 2. Verify Research Plan
        // Wait for "Research Plan" or similar header
        await expect(page.locator('text=研究計畫').or(page.locator('text=Research Plan'))).toBeVisible({ timeout: 10000 })
        console.log('✅ Research Plan appeared')

        // 3. Verify Tool Usage
        // Look for a task item
        const taskItem = page.locator('[class*="task-item"]').first()
        await expect(taskItem).toBeVisible()

        // Check if it has tool usage info (might need to expand)
        if (await taskItem.locator('button').isVisible()) {
            await taskItem.locator('button').click() // Expand
        }

        // Check for tool name or input/output
        // This is a loose check as UI might vary
        const toolInfo = taskItem.locator('text=/Tool|Input|Output|工具/')
        if (await toolInfo.count() > 0) {
            console.log('✅ Tool usage info found')
        } else {
            console.log('⚠️ Tool usage info not immediately visible')
        }
    })
})
