/**
 * AI BOS — LT-002 login burst (k6)
 *
 *   k6 run --vus 50 --duration 1m tests/perf/login_burst.js
 */
import http from 'k6/http';
import { check, sleep } from 'k6';

const BASE = __ENV.API_URL || 'http://127.0.0.1:8000';
const EMAIL = __ENV.EMAIL || 'ceo@demo.aibos.io';
const PASSWORD = __ENV.PASSWORD || 'demo1234';

export const options = {
  stages: [
    { duration: '15s', target: 20 },
    { duration: '30s', target: 50 },
    { duration: '15s', target: 0 },
  ],
  thresholds: {
    http_req_failed: ['rate<0.05'],
    http_req_duration: ['p(95)<4000'],
  },
};

export default function () {
  const res = http.post(
    `${BASE}/api/v1/auth/login`,
    JSON.stringify({ email: EMAIL, password: PASSWORD }),
    { headers: { 'Content-Type': 'application/json' } },
  );
  check(res, { 'login 200': (r) => r.status === 200 });
  sleep(0.2);
}
