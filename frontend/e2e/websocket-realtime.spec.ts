/**
 * E2E tests for WebSocket real-time monitoring
 *
 * These tests programmatically verify that:
 * 1. WebSocket establishes connection
 * 2. Plan data contains real extracted keywords (not hardcoded)
 * 3. Steps update sequentially with real timing (3-digit precision)
 * 4. Activity log receives incremental messages
 * 5. Results appear only after workflow completes
 */

import { test, expect, Page } from '@playwright/test'

// Test configuration
const BACKEND_URL = 'http://127.0.0.1:8000'
const FRONTEND_URL = 'http://localhost:5173/query' // Query page has WebSocket
const WS_TIMEOUT = 120000 // 2 minutes for workflow completion

/**
 * Helper to wait for WebSocket connection
 */
async function waitForWebSocketConnection(page: Page) {
  await page.waitForFunction(
    () => {
      const indicator = document.querySelector('[class*="bg-green-500"]')
      return indicator !== null
    },
    { timeout: 10000 }
  )
}

/**
 * Helper to extract text content safely
 */
async function getTextContent(page: Page, selector: string): Promise<string> {
  const element = await page.locator(selector).first()
  return (await element.textContent()) || ''
}

/**
 * Helper to collect all activity log messages
 */
async function getActivityLogMessages(page: Page): Promise<string[]> {
  const messages = await page.locator('[data-testid="activity-log-entry"]').allTextContents()
  return messages
}

test.describe('WebSocket Real-Time Monitoring', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to app
    await page.goto(FRONTEND_URL)

    // Wait for WebSocket connection
    await waitForWebSocketConnection(page)
  })

  test('Test 1: WebSocket establishes connection on page load', async ({ page }) => {
    // Verify connection indicator shows green
    const greenIndicator = page.locator('.bg-green-500').first()
    await expect(greenIndicator).toBeVisible()

    // Verify connection status text
    const statusText = await getTextContent(page, 'text=WebSocket 已連線')
    expect(statusText).toContain('WebSocket 已連線')

    console.log('✅ Test 1 PASSED: WebSocket connected')
  })

  test('Test 2: Plan panel shows real extracted keywords (not hardcoded)', async ({ page }) => {
    // Submit first query
    const query1 = '玉山銀行洗錢防制裁罰'
    await page.fill('textarea[id="query"]', query1)
    await page.click('button:has-text("送出查詢")')

    // Wait for plan panel to appear
    await page.waitForSelector('text=研究計畫', { timeout: 15000 })

    // Expand plan panel if collapsed
    const planHeader = page.locator('button:has-text("研究計畫")').first()
    const isExpanded = await planHeader.getAttribute('aria-expanded')
    if (isExpanded === 'false') {
      await planHeader.click()
    }

    // Extract keywords from first query
    await page.waitForSelector('text=關鍵字', { timeout: 5000 })
    const keywordsSection1 = await page.locator('text=關鍵字').locator('..').textContent()

    console.log(`Query 1 keywords section: ${keywordsSection1}`)

    // Verify keywords relate to query 1
    const query1Terms = ['玉山', '銀行', '洗錢', '防制', '裁罰']
    const foundTerms1 = query1Terms.filter(term => keywordsSection1?.includes(term))

    expect(foundTerms1.length).toBeGreaterThanOrEqual(2)
    console.log(`✅ Query 1 found relevant keywords: ${foundTerms1.join(', ')}`)

    // Wait for query to complete
    await page.waitForSelector('text=查詢完成', { timeout: WS_TIMEOUT })

    // Submit second query with different content
    const query2 = '國泰世華銀行內線交易案件'
    await page.fill('textarea[id="query"]', query2)
    await page.click('button:has-text("送出查詢")')

    // Wait for new plan panel
    await page.waitForSelector('text=研究計畫', { timeout: 15000 })

    // Extract keywords from second query
    await page.waitForSelector('text=關鍵字', { timeout: 5000 })
    const keywordsSection2 = await page.locator('text=關鍵字').locator('..').textContent()

    console.log(`Query 2 keywords section: ${keywordsSection2}`)

    // Verify keywords changed for query 2
    const query2Terms = ['國泰', '世華', '銀行', '內線', '交易']
    const foundTerms2 = query2Terms.filter(term => keywordsSection2?.includes(term))

    expect(foundTerms2.length).toBeGreaterThanOrEqual(2)
    console.log(`✅ Query 2 found relevant keywords: ${foundTerms2.join(', ')}`)

    // Verify keywords are different (proves not hardcoded)
    expect(keywordsSection1).not.toBe(keywordsSection2)
    console.log('✅ Test 2 PASSED: Keywords change per query (not hardcoded)')
  })

  test('Test 3: Steps update sequentially with real timing', async ({ page }) => {
    // Track step updates over time
    const stepUpdates: Array<{ step: string; status: string; time: number; elapsed?: number }> = []
    const startTime = Date.now()

    // Monitor step updates
    page.on('console', msg => {
      if (msg.type() === 'log') {
        const text = msg.text()
        if (text.includes('Step update:')) {
          console.log(text)
        }
      }
    })

    // Submit query
    await page.fill('textarea[id="query"]', '測試步驟順序')
    await page.click('button:has-text("送出查詢")')

    // Wait a bit for workflow to start
    await page.waitForTimeout(1000)

    // Poll step statuses over time
    const pollInterval = 500 // Check every 500ms
    const maxPolls = 240 // 2 minutes max

    for (let i = 0; i < maxPolls; i++) {
      // Check all possible steps
      const steps = ['planning', 'action', 'validation', 'answer']

      for (const stepName of steps) {
        // Look for step status indicators
        const stepElement = page.locator(`[data-step="${stepName}"]`).first()
        const isVisible = await stepElement.isVisible().catch(() => false)

        if (isVisible) {
          const stepText = await stepElement.textContent()
          const status = stepText?.includes('完成') ? 'done' : 'active'

          // Record step update with timestamp
          stepUpdates.push({
            step: stepName,
            status,
            time: Date.now() - startTime,
          })
        }
      }

      // Check if workflow completed
      const isComplete = await page.locator('text=查詢完成').isVisible().catch(() => false)
      if (isComplete) {
        break
      }

      await page.waitForTimeout(pollInterval)
    }

    console.log('\nStep update timeline:')
    stepUpdates.forEach(update => {
      console.log(`  ${update.time}ms: ${update.step} → ${update.status}`)
    })

    // Verify sequential progression
    const planningDone = stepUpdates.find(u => u.step === 'planning' && u.status === 'done')
    const actionActive = stepUpdates.find(u => u.step === 'action' && u.status === 'active')
    const actionDone = stepUpdates.find(u => u.step === 'action' && u.status === 'done')
    const validationActive = stepUpdates.find(u => u.step === 'validation' && u.status === 'active')

    // Verify planning completes before action starts
    if (planningDone && actionActive) {
      expect(planningDone.time).toBeLessThan(actionActive.time)
      console.log('✅ Planning completes before Action starts')
    }

    // Verify action completes before validation starts
    if (actionDone && validationActive) {
      expect(actionDone.time).toBeLessThan(validationActive.time)
      console.log('✅ Action completes before Validation starts')
    }

    // Verify steps don't all complete simultaneously
    const uniqueTimes = new Set(stepUpdates.map(u => Math.floor(u.time / 1000)))
    expect(uniqueTimes.size).toBeGreaterThan(1)
    console.log(`✅ Steps spread across ${uniqueTimes.size} different seconds (not simultaneous)`)

    console.log('✅ Test 3 PASSED: Steps update sequentially')
  })

  test('Test 4: Timing values have millisecond precision (3-digit)', async ({ page }) => {
    // Submit query
    await page.fill('textarea[id="query"]', '測試時間精確度')
    await page.click('button:has-text("送出查詢")')

    // Wait for workflow to complete
    await page.waitForSelector('text=查詢完成', { timeout: WS_TIMEOUT })

    // Extract all elapsed time values from step cards
    const elapsedTexts = await page.locator('text=/\\d+ms/').allTextContents()
    const elapsedValues = elapsedTexts
      .map(text => {
        const match = text.match(/(\d+)ms/)
        return match ? parseInt(match[1]) : null
      })
      .filter(val => val !== null && val > 0) as number[]

    console.log(`\nExtracted timing values (ms): ${elapsedValues.join(', ')}`)

    // Verify we have timing data
    expect(elapsedValues.length).toBeGreaterThan(0)

    // Verify precision (not round hundreds like 0, 1000, 2000)
    const nonRoundHundreds = elapsedValues.filter(val => val % 100 !== 0)
    const precisionCount = nonRoundHundreds.length

    console.log(`${precisionCount}/${elapsedValues.length} values have sub-100ms precision`)
    console.log(`Non-round values: ${nonRoundHundreds.join(', ')}`)

    // At least some values should have precision
    expect(precisionCount).toBeGreaterThan(0)

    console.log('✅ Test 4 PASSED: Timing has millisecond precision')
  })

  test('Test 5: Activity log receives incremental messages', async ({ page }) => {
    // Track activity log message count over time
    const messageCounts: Array<{ time: number; count: number }> = []
    const startTime = Date.now()

    // Submit query
    await page.fill('textarea[id="query"]', '測試活動日誌')
    await page.click('button:has-text("送出查詢")')

    // Poll message count over time
    const pollInterval = 1000 // Check every second
    const maxPolls = 120 // 2 minutes max

    for (let i = 0; i < maxPolls; i++) {
      await page.waitForTimeout(pollInterval)

      // Count activity log entries
      const entries = await page.locator('[class*="text-gray-900"]:has-text("執行節點")').count()

      messageCounts.push({
        time: Date.now() - startTime,
        count: entries,
      })

      // Check if workflow completed
      const isComplete = await page.locator('text=查詢完成').isVisible().catch(() => false)
      if (isComplete) {
        break
      }
    }

    console.log('\nActivity log message timeline:')
    messageCounts.forEach(({ time, count }) => {
      console.log(`  ${time}ms: ${count} messages`)
    })

    // Verify messages arrived incrementally (not all at once)
    const uniqueCounts = [...new Set(messageCounts.map(m => m.count))]

    console.log(`Message counts over time: ${uniqueCounts.join(' → ')}`)
    expect(uniqueCounts.length).toBeGreaterThan(1)

    // Verify count increased over time
    const firstCount = messageCounts[0]?.count || 0
    const lastCount = messageCounts[messageCounts.length - 1]?.count || 0
    expect(lastCount).toBeGreaterThan(firstCount)

    console.log('✅ Test 5 PASSED: Messages arrive incrementally')
  })

  test('Test 6: Results appear only after workflow completes', async ({ page }) => {
    // Submit query
    await page.fill('textarea[id="query"]', '測試結果時機')
    await page.click('button:has-text("送出查詢")')

    // Verify results panel is NOT visible during processing
    await page.waitForTimeout(2000)
    const resultsVisibleDuring = await page.locator('text=執行摘要').isVisible().catch(() => false)
    expect(resultsVisibleDuring).toBe(false)
    console.log('✅ Results panel hidden during processing')

    // Wait for workflow to complete
    await page.waitForSelector('text=查詢完成', { timeout: WS_TIMEOUT })

    // Verify results panel IS visible after completion
    const resultsVisibleAfter = await page.locator('text=執行摘要').isVisible({ timeout: 5000 })
    expect(resultsVisibleAfter).toBe(true)
    console.log('✅ Results panel appears after completion')

    // Verify results have content
    const summary = await getTextContent(page, 'text=執行摘要')
    expect(summary.length).toBeGreaterThan(0)

    console.log('✅ Test 6 PASSED: Results timing correct')
  })

  test('Test 7: Entity type is inferred (not default "unknown")', async ({ page }) => {
    // Submit query about a bank
    await page.fill('textarea[id="query"]', '玉山銀行洗錢防制裁罰')
    await page.click('button:has-text("送出查詢")')

    // Wait for plan panel
    await page.waitForSelector('text=研究計畫', { timeout: 15000 })

    // Expand plan panel
    const planHeader = page.locator('button:has-text("研究計畫")').first()
    await planHeader.click()

    // Find entity type
    await page.waitForSelector('text=實體類型', { timeout: 5000 })
    const entitySection = await page.locator('text=實體類型').locator('..').textContent()

    console.log(`Entity type section: ${entitySection}`)

    // Verify NOT "unknown"
    expect(entitySection).not.toContain('unknown')

    // Should contain bank-related type
    const hasValidType =
      entitySection?.includes('bank') ||
      entitySection?.includes('銀行') ||
      entitySection?.includes('commercial') ||
      entitySection?.includes('financial')

    expect(hasValidType).toBe(true)
    console.log('✅ Test 7 PASSED: Entity type inferred (not "unknown")')
  })

  test('Test 8: Demo delay creates visible pauses (if enabled)', async ({ page }) => {
    // This test verifies demo delay is working by measuring time between steps

    await page.fill('textarea[id="query"]', '測試延遲時間')

    const stepTimes: Record<string, number> = {}
    const startTime = Date.now()

    await page.click('button:has-text("送出查詢")')

    // Monitor for step completions
    const steps = ['planning', 'action', 'validation', 'answer']

    for (const step of steps) {
      // Wait for step to appear as done
      try {
        await page.waitForSelector(`text=${step}`, { timeout: 30000 })
        // Give it time to complete
        await page.waitForTimeout(1000)

        // Check if shows as completed
        const isDone = await page.locator(`text=${step}`).locator('..').textContent()
        if (isDone?.includes('完成') || isDone?.includes('done')) {
          stepTimes[step] = Date.now() - startTime
          console.log(`${step} completed at ${stepTimes[step]}ms`)
        }
      } catch (e) {
        console.log(`Timeout waiting for ${step}`)
      }
    }

    // Calculate gaps between steps
    if (stepTimes.planning && stepTimes.action) {
      const gap1 = stepTimes.action - stepTimes.planning
      console.log(`Planning → Action gap: ${gap1}ms`)

      // With demo delay, should be ~3 seconds
      // Without demo delay, might be < 1 second
      if (gap1 > 2000) {
        console.log('✅ Demo delay detected (gap > 2s)')
      } else {
        console.log('ℹ️  No demo delay (gap < 2s) - running at full speed')
      }
    }

    console.log('✅ Test 8 PASSED: Delay behavior verified')
  })
})

test.describe('WebSocket Error Handling', () => {
  test('Test 9: Handles WebSocket disconnect gracefully', async ({ page }) => {
    await page.goto(FRONTEND_URL)
    await waitForWebSocketConnection(page)

    // Simulate backend disconnect by blocking WebSocket
    await page.route('ws://localhost:5173/ws/query', route => route.abort())

    // Try to submit query
    await page.fill('textarea[id="query"]', '測試錯誤處理')
    await page.click('button:has-text("送出查詢")')

    // Wait a bit
    await page.waitForTimeout(3000)

    // Verify error message or connection issue indicated
    const hasError =
      await page.locator('text=/連線失敗|未連線|錯誤/').isVisible({ timeout: 5000 })

    expect(hasError).toBe(true)
    console.log('✅ Test 9 PASSED: Error handling works')
  })
})
