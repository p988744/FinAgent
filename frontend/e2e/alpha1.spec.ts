import { test, expect } from '@playwright/test'

test.describe('v0.1.0-alpha.1: Infrastructure Validation', () => {
  test('should load the application', async ({ page }) => {
    await page.goto('/')
    await expect(page).toHaveTitle(/FinAgent/)
  })

  test('should display main layout with navigation', async ({ page }) => {
    await page.goto('/')

    // Check header
    await expect(page.locator('header')).toBeVisible()
    await expect(page.getByText('FinAgent')).toBeVisible()
    await expect(page.getByText('金融法律研究代理系統')).toBeVisible()

    // Check sidebar navigation
    await expect(page.getByRole('link', { name: '查詢' })).toBeVisible()
    await expect(page.getByRole('link', { name: '設定' })).toBeVisible()
    await expect(page.getByRole('link', { name: '模型' })).toBeVisible()
    await expect(page.getByRole('link', { name: '文件' })).toBeVisible()
  })

  test('should navigate to all pages', async ({ page }) => {
    await page.goto('/')

    // Default redirect to query page
    await expect(page).toHaveURL('/query')
    await expect(page.getByText('法律研究查詢')).toBeVisible()

    // Navigate to config page
    await page.click('text=設定')
    await expect(page).toHaveURL('/config')
    await expect(page.getByText('系統設定')).toBeVisible()

    // Navigate to models page
    await page.click('text=模型')
    await expect(page).toHaveURL('/models')
    await expect(page.getByText('模型管理')).toBeVisible()

    // Navigate to documents page
    await page.click('text=文件')
    await expect(page).toHaveURL('/documents')
    await expect(page.getByText('文件管理')).toBeVisible()
  })

  test('should highlight active navigation item', async ({ page }) => {
    await page.goto('/query')

    // Query link should be highlighted
    const queryLink = page.getByRole('link', { name: '查詢' })
    await expect(queryLink).toHaveClass(/bg-blue-50/)

    // Navigate to config
    await page.click('text=設定')
    const configLink = page.getByRole('link', { name: '設定' })
    await expect(configLink).toHaveClass(/bg-blue-50/)

    // Query link should no longer be highlighted
    await expect(queryLink).not.toHaveClass(/bg-blue-50/)
  })

  test('should show placeholder content for unimplemented features', async ({ page }) => {
    await page.goto('/query')
    await expect(page.getByText('alpha.2')).toBeVisible()

    await page.goto('/config')
    await expect(page.getByText('alpha.3')).toBeVisible()

    await page.goto('/models')
    await expect(page.getByText('alpha.4')).toBeVisible()

    await page.goto('/documents')
    await expect(page.getByText('alpha.5')).toBeVisible()
  })
})
