import { describe, expect, it } from 'vitest';
import { ApiError, MockModeError } from './client';

describe('ApiError', () => {
  it('exposes status and message', () => {
    const err = new ApiError(404, 'Not Found', { detail: 'missing' });
    expect(err.status).toBe(404);
    expect(err.statusText).toBe('Not Found');
    expect(err.body).toEqual({ detail: 'missing' });
    expect(err.message).toContain('404');
    expect(err.name).toBe('ApiError');
  });
});

describe('MockModeError', () => {
  it('includes path in message', () => {
    const err = new MockModeError('/api/v1/crm/contacts');
    expect(err.path).toBe('/api/v1/crm/contacts');
    expect(err.message).toContain('/api/v1/crm/contacts');
    expect(err.name).toBe('MockModeError');
  });
});
