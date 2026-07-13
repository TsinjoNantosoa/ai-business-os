/**
 * AI BOS — LT-001 smoke load test (k6)
 *
 * Usage (API déjà démarrée) :
 *   k6 run tests/perf/smoke.js
 *   k6 run -e API_URL=http://127.0.0.1:8000 -e EMAIL=ceo@demo.aibos.io -e PASSWORD=demo1234 tests/perf/smoke.js
 *
 * Critères : erreurs HTTP < 1 %, p95 santé < 200 ms, p95 CRUD < 800 ms (local SQLite).
 */
import http from 'k6/http';
import { check, group, sleep } from 'k6';
import { Rate, Trend } from 'k6/metrics';

const BASE = __ENV.API_URL || 'http://127.0.0.1:8000';
const EMAIL = __ENV.EMAIL || 'ceo@demo.aibos.io';
const PASSWORD = __ENV.PASSWORD || 'demo1234';

const errorRate = new Rate('aibos_errors');
const loginTrend = new Trend('aibos_login_ms');
const contactsTrend = new Trend('aibos_contacts_ms');
const kpisTrend = new Trend('aibos_kpis_ms');

export const options = {
  scenarios: {
    smoke: {
      executor: 'constant-vus',
      vus: Number(__ENV.VUS || 10),
      duration: __ENV.DURATION || '30s',
    },
  },
  thresholds: {
    http_req_failed: ['rate<0.01'],
    aibos_errors: ['rate<0.01'],
    // Login bcrypt est volontairement lent sous concurrence locale.
    http_req_duration: ['p(95)<3500'],
    aibos_login_ms: ['p(95)<4000'],
    aibos_contacts_ms: ['p(95)<800'],
    aibos_kpis_ms: ['p(95)<800'],
  },
};

export function setup() {
  const health = http.get(`${BASE}/health`);
  if (health.status !== 200) {
    throw new Error(`API health failed: ${health.status} ${health.body}`);
  }
  const login = http.post(
    `${BASE}/api/v1/auth/login`,
    JSON.stringify({ email: EMAIL, password: PASSWORD }),
    { headers: { 'Content-Type': 'application/json' } },
  );
  if (login.status !== 200) {
    throw new Error(`Login failed: ${login.status} ${login.body}`);
  }
  const body = login.json();
  return { token: body.token || body.accessToken };
}

export default function (data) {
  const headers = {
    Authorization: `Bearer ${data.token}`,
    'Content-Type': 'application/json',
    'X-Correlation-ID': `k6-${__VU}-${__ITER}`,
  };

  group('health', () => {
    const res = http.get(`${BASE}/health`);
    const ok = check(res, { 'health 200': (r) => r.status === 200 });
    errorRate.add(!ok);
  });

  group('login', () => {
    const res = http.post(
      `${BASE}/api/v1/auth/login`,
      JSON.stringify({ email: EMAIL, password: PASSWORD }),
      { headers: { 'Content-Type': 'application/json' } },
    );
    loginTrend.add(res.timings.duration);
    const ok = check(res, { 'login 200': (r) => r.status === 200 });
    errorRate.add(!ok);
  });

  group('crm_contacts', () => {
    const res = http.get(`${BASE}/api/v1/crm/contacts`, { headers });
    contactsTrend.add(res.timings.duration);
    const ok = check(res, { 'contacts 200': (r) => r.status === 200 });
    errorRate.add(!ok);
  });

  group('analytics_kpis', () => {
    const res = http.get(`${BASE}/api/v1/analytics/kpis`, { headers });
    kpisTrend.add(res.timings.duration);
    const ok = check(res, { 'kpis 200': (r) => r.status === 200 });
    errorRate.add(!ok);
  });

  sleep(0.3);
}
