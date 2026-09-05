import path from 'path';
import { fileURLToPath } from 'url';
import { defineConfig, devices } from '@playwright/test';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const backendDir = path.resolve(__dirname, '../ai-bos-backend');

export default defineConfig({
  testDir: './e2e',
  // The E2E suite exercises shared server-side auth, rate-limit and demo state.
  // Run tests serially so one browser context cannot perturb another one.
  fullyParallel: false,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: 'list',
  use: {
    baseURL: 'http://localhost:5187',
    trace: 'on-first-retry',
    ...(process.env.PLAYWRIGHT_EXECUTABLE_PATH
      ? { launchOptions: { executablePath: process.env.PLAYWRIGHT_EXECUTABLE_PATH } }
      : {}),
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
  webServer: [
    {
      command: 'python -m uvicorn app.main:app --port 8000',
      cwd: backendDir,
      url: 'http://localhost:8000/health',
      env: {
        CORS_ORIGINS: 'http://localhost:5187',
      },
      reuseExistingServer: !process.env.CI,
      timeout: 120_000,
    },
    {
      command: 'npm run dev -- --host localhost --port 5187',
      cwd: __dirname,
      url: 'http://localhost:5187',
      env: {
        VITE_API_URL: 'http://localhost:8000',
        VITE_USE_MOCKS: 'false',
        VITE_AUTO_DEMO_LOGIN: 'false',
      },
      reuseExistingServer: false,
      timeout: 120_000,
    },
  ],
});
