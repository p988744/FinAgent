import { test, expect } from '@playwright/test'

test.describe('Alpha.1 - Navigation & Core Layout', () => {
  test('should load home page', async ({ page }) => {
    await page.goto('/')
    await expect(page).toHaveTitle(/FinAgent/)
  })

  test('should display sidebar navigation', async ({ page }) => {
    await page.goto('/')
    const sidebar = page.locator('aside, nav').first()
    await expect(sidebar).toBeVisible()
  })

  test('should navigate to Query page', async ({ page }) => {
    await page.goto('/')
    await page.click('text=查詢')
    await expect(page.locator('h1')).toContainText('法律研究查詢')
  })

  test('should navigate to Documents page', async ({ page }) => {
    await page.goto('/')
    await page.click('text=文件')
    await expect(page.locator('h1')).toContainText('文件管理')
  })

  test('should navigate to Configuration page', async ({ page }) => {
    await page.goto('/')
    await page.click('text=設定')
    await expect(page.locator('h1')).toContainText('系統設定')
  })

  test('should have responsive layout', async ({ page }) => {
    await page.goto('/')
    // Check that main content area exists
    const main = page.locator('main')
    await expect(main).toBeVisible()
  })
})
