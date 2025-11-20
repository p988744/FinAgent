import { test, expect } from '@playwright/test';

test('debug pipeline import error', async ({ page }) => {
  // Listen for console errors
  const errors: string[] = [];
  page.on('console', msg => {
    if (msg.type() === 'error') {
      errors.push(msg.text());
      console.error('❌ Console Error:', msg.text());
    }
  });

  // Listen for page errors
  page.on('pageerror', error => {
    console.error('❌ Page Error:', error.message);
    console.error('Stack:', error.stack);
  });

  console.log('\n🔍 Navigating to documents page...');
  try {
    await page.goto('http://localhost:5173/documents', { timeout: 10000 });
  } catch (e) {
    console.error('Failed to load page:', e);
  }

  // Wait a bit for errors to appear
  await page.waitForTimeout(3000);

  console.log('\n📋 All Console Errors:', errors.length);

  // Take screenshot
  await page.screenshot({ path: '/tmp/debug-screenshot.png', fullPage: true });
  console.log('\n📸 Screenshot saved to /tmp/debug-screenshot.png');

  // Get page content
  console.log('\n📄 Page title:', await page.title());

  // Check if React root rendered
  const rootElement = await page.locator('#root');
  const hasContent = await rootElement.evaluate(el => el.innerHTML.length > 100);
  console.log('🌲 Root element has content:', hasContent);

  // Try to get network errors
  console.log('\n🌐 Checking for failed requests...');
});
