import { beforeEach, describe, expect, it, vi } from 'vitest';

const apiFetchMock = vi.hoisted(() => vi.fn());

vi.mock('./client', () => ({
  API_URL: 'http://localhost:8000',
  USE_MOCKS: false,
  apiFetch: apiFetchMock,
}));

import { exchangeOAuthCode, forgotPassword, resetPassword, verifyResetCode } from './services';


describe('password reset services', () => {
  beforeEach(() => apiFetchMock.mockReset());

  it('posts the email to forgot-password', async () => {
    apiFetchMock.mockResolvedValue({ status: 'ok', message: 'generic' });

    await forgotPassword('anyone@example.com');

    expect(apiFetchMock).toHaveBeenCalledWith('/api/v1/auth/forgot-password', {
      method: 'POST',
      body: JSON.stringify({ email: 'anyone@example.com' }),
    });
  });

  it('posts the email and code to verify-reset-code', async () => {
    apiFetchMock.mockResolvedValue({ status: 'ok' });

    await verifyResetCode('anyone@example.com', '123456');

    expect(apiFetchMock).toHaveBeenCalledWith('/api/v1/auth/verify-reset-code', {
      method: 'POST',
      body: JSON.stringify({ email: 'anyone@example.com', code: '123456' }),
    });
  });

  it('posts the email, code and new password to reset-password', async () => {
    apiFetchMock.mockResolvedValue({ status: 'ok' });

    await resetPassword('anyone@example.com', '123456', 'newpass99');

    expect(apiFetchMock).toHaveBeenCalledWith('/api/v1/auth/reset-password', {
      method: 'POST',
      body: JSON.stringify({
        email: 'anyone@example.com',
        code: '123456',
        newPassword: 'newpass99',
      }),
    });
  });

  it('exchanges a one-time OAuth code for the auth response', async () => {
    apiFetchMock.mockResolvedValue({ token: 'token', refreshToken: 'refresh', user: {} });

    await exchangeOAuthCode('one-time-oauth-code');

    expect(apiFetchMock).toHaveBeenCalledWith('/api/v1/auth/oauth/exchange', {
      method: 'POST',
      body: JSON.stringify({ code: 'one-time-oauth-code' }),
    });
  });
});
