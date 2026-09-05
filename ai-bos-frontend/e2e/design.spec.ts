import { expect, test } from '@playwright/test';

test.describe('premium design shell', () => {
  test('public pages remain responsive', async ({ page }) => {
    for (const width of [1440, 768, 390]) {
      await page.setViewportSize({ width, height: 900 });
      for (const path of ['/', '/login', '/register']) {
        await page.goto(path);
        await expect(page.locator('body')).toBeVisible();
        const overflow = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
        expect(overflow, `${path} overflows at ${width}px`).toBeLessThanOrEqual(1);
      }
    }
    await page.setViewportSize({ width: 1440, height: 900 });
    await page.goto('/');
    await page.waitForTimeout(800);
    await page.screenshot({ path: 'test-results/review/landing.png', fullPage: true });
    await page.setViewportSize({ width: 390, height: 844 });
    await page.screenshot({ path: 'test-results/review/landing-mobile.png', fullPage: true });
  });

  test('core workspaces render inside the authenticated shell', async ({ page }) => {
    await page.goto('/login?demo=true');
    await page.getByRole('button', { name: /CEO/i }).click();
    await expect(page).toHaveURL(/\/app\/dashboard/);

    for (const path of ['/app/dashboard', '/app/copilot', '/app/inbox', '/app/crm/contacts', '/app/crm/pipeline', '/app/finance', '/app/workflows', '/app/agents', '/app/settings/profile']) {
      await page.goto(path);
      await expect(page.locator('#main-content')).toBeVisible();
    }

    await page.setViewportSize({ width: 1440, height: 900 });
    await page.goto('/app/dashboard');
    await expect(page.getByRole('heading', { name: /Tableau de bord|Dashboard/i })).toBeVisible({ timeout: 15_000 });
    await page.screenshot({ path: 'test-results/review/dashboard.png', fullPage: true });
    await page.goto('/app/crm/pipeline');
    await expect(page.locator('#main-content h1')).toBeVisible({ timeout: 15_000 });
    await page.screenshot({ path: 'test-results/review/pipeline.png', fullPage: true });

    await page.goto('/app/copilot');
    await expect(page.getByRole('button', { name: 'Ouvrir le Copilot' })).toHaveCount(0);
  });
});
