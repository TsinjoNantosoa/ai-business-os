import { expect, test } from '@playwright/test';

test.describe('AI BOS official branding', () => {
  test('public brand stays sharp and responsive', async ({ page }) => {
    for (const width of [1920, 1440, 1366, 1024, 768, 390]) {
      await page.setViewportSize({ width, height: 900 });
      await page.goto('/');
      const headerLogo = page.locator('header img[src*="ai-bos-wordmark"]').first();
      await expect(headerLogo).toBeVisible();
      expect(await headerLogo.evaluate((image: HTMLImageElement) => image.naturalWidth)).toBeGreaterThan(0);
      expect(await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth)).toBeLessThanOrEqual(1);
    }

    for (const path of ['/login', '/register', '/forgot-password']) {
      await page.goto(path);
      await expect(page.locator('picture:visible img[src*="ai-bos-"]').first()).toBeVisible();
      await expect(page).toHaveTitle(/AI BOS/);
    }

    await page.evaluate(() => localStorage.setItem('aibos-theme', JSON.stringify({ state: { mode: 'light' }, version: 0 })));
    await page.goto('/forgot-password');
    await expect(page.locator('html')).not.toHaveClass(/dark/);
    await expect(page.getByRole('img', { name: 'AI BOS' })).toBeVisible();
  });

  test('application shell and Copilot share the official icon', async ({ page }) => {
    await page.goto('/login?demo=true');
    await page.getByRole('button', { name: /CEO/i }).click();
    await expect(page).toHaveURL(/\/app\/dashboard/);

    const sidebarBrand = page.getByRole('link', { name: 'AI BOS — Tableau de bord' });
    await expect(sidebarBrand).toBeVisible();
    await expect(sidebarBrand.locator('img[src*="ai-bos-wordmark"]')).toBeVisible();

    await page.getByRole('button', { name: 'Réduire la barre latérale' }).click();
    await expect(sidebarBrand.locator('img[src*="ai-bos-icon"]')).toBeVisible();

    await page.setViewportSize({ width: 390, height: 844 });
    await page.goto('/app/dashboard');
    await expect(page.locator('header img[src*="ai-bos-wordmark"]')).toBeVisible();
    expect(await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth)).toBeLessThanOrEqual(1);
    await page.getByRole('button', { name: 'Ouvrir le menu' }).click();
    await expect(sidebarBrand).toBeVisible();

    await page.setViewportSize({ width: 1440, height: 900 });
    await page.goto('/app/copilot');
    await expect(page.locator('#main-content picture:visible img[src*="ai-bos-icon"]').first()).toBeVisible();
  });

  test('favicon and manifest assets are available', async ({ page, request }) => {
    await page.goto('/');
    await expect(page).toHaveTitle('AI BOS — Business Operating System');
    for (const path of ['/favicon.ico', '/brand/favicon-32x32.png', '/manifest.webmanifest']) {
      const response = await request.get(path);
      expect(response.ok(), `${path} should be available`).toBeTruthy();
    }
  });
});
