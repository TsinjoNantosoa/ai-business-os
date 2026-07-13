import { test, expect } from '@playwright/test';

test.describe('AI BOS smoke', () => {
  test('demo CEO login reaches dashboard', async ({ page }) => {
    await page.goto('/login');
    await expect(page.getByRole('heading', { name: /Bienvenue|Welcome back/i })).toBeVisible();

    await page.getByRole('button', { name: /ceo@demo\.aibos\.io/i }).click();

    await expect(page).toHaveURL(/\/app\/dashboard/, { timeout: 15_000 });
    await expect(page.getByRole('heading', { name: /Tableau de bord|Dashboard/i })).toBeVisible();
  });

  test('protected route redirects to login when unauthenticated', async ({ page }) => {
    await page.goto('/app/dashboard');
    await expect(page).toHaveURL(/\/login/);
  });
});
