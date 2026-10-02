import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import test from 'node:test';

const source = await readFile(new URL('../functions/api/leaderboard.js', import.meta.url), 'utf8');
const bootstrapUrl = new URL('../lib/leaderboard-bootstrap.js', import.meta.url).href;
const namedSource = `${source.replace("'../../lib/leaderboard-bootstrap.js'", JSON.stringify(bootstrapUrl))}\n//# sourceURL=leaderboard-under-test.js`;
const { onRequest } = await import(`data:text/javascript;base64,${Buffer.from(namedSource).toString('base64')}`);
const ids = [1, 2, 3].map((n) => `00000000-0000-4000-8000-${String(n).padStart(12, '0')}`);
const rows = ids.map((player_id, i) => ({ player_id, name: `Player ${i + 1}`, score: i < 2 ? 100 : 50 }));
const now = () => Math.floor(Date.now() / 1000);

function fixture({ snapshot = { rows: [], updatedAt: 0, retryAfter: 0, unavailable: false },
  failTop = false, failBatch = false, failCache = false, failMine = false } = {}) {
  let stored = snapshot;
  const calls = { top: 0, mine: [], batch: 0, writes: 0 };
  const cache = new Map();
  globalThis.caches = { default: {
    async match(key) {
      const entry = cache.get(key.url);
      return entry && entry.expires > now() ? entry.response.clone() : undefined;
    },
    async put(key, value) {
      const ttl = Number(value.headers.get('cache-control').match(/max-age=(\d+)/)[1]);
      cache.set(key.url, { response: value.clone(), expires: now() + ttl });
    },
  } };
  const env = {
    PLAY_COUNTER: {
      async get() { return stored; },
      async put(_key, value) {
        calls.writes++;
        if (failCache) throw new Error('KV unavailable');
        stored = JSON.parse(value);
      },
    },
    LEADERBOARD_DB: {
      prepare(sql) {
        let params = [];
        return {
          bind(...values) { params = values; return this; },
          async all() {
            calls.top++;
            if (failTop) throw new Error('D1_ERROR: exceeded free tier daily row read limit [7500]');
            return { results: rows };
          },
          async first() {
            if (sql.includes('leaderboard_runs')) return { started_at: now() - 10, submitted_at: null };
            if (failMine) throw new Error('D1 unavailable after successful save');
            calls.mine.push(params[0]);
            const row = rows.find((r) => r.player_id === params[0]);
            return row ? { ...row, rank: row.score === 100 ? 1 : 3 } : null;
          },
          async run() { return { meta: { changes: 1 } }; },
        };
      },
      async batch() {
        calls.batch++;
        if (failBatch) throw new Error('D1_ERROR: exceeded free tier daily row read limit [7500]');
        return [{ results: [{ score: 100 }], meta: { changes: 1 } }, { meta: { changes: 1 } }];
      },
    },
  };
  return {
    calls,
    get snapshot() { return stored; },
    async request(playerId, body) {
      const pending = [];
      const url = `https://naiwa-fart.pages.dev/api/leaderboard${playerId ? `?playerId=${playerId}` : ''}`;
      const request = new Request(url, body ? {
        method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify(body),
      } : undefined);
      const response = await onRequest({ request, env, waitUntil(promise) { pending.push(promise); } });
      await Promise.all(pending);
      return { status: response.status, data: await response.json(), headers: response.headers };
    },
  };
}

test('shared top ten is read once; equal scores share ranks; personal data stays separate', async () => {
  const f = fixture();
  const a = await f.request(ids[0]);
  const b = await f.request(ids[1]);
  const c = await f.request(ids[0]);
  assert.equal(a.status, 200);
  assert.deepEqual(a.data.top.map((r) => r.rank), [1, 1, 3]);
  assert.deepEqual(a.data.top.map((r) => r.mine), [true, false, false]);
  assert.deepEqual(b.data.top.map((r) => r.mine), [false, true, false]);
  assert.equal(c.data.mine.name, 'Player 1');
  assert.equal(f.calls.top, 1);
  assert.deepEqual(f.calls.mine, [ids[0], ids[1]]);
  assert.equal(f.calls.writes, 1);
  assert.equal(a.headers.get('cache-control'), 'no-store');
});

test('quota exhaustion keeps old top ten and stops database retries until daily reset', async () => {
  const f = fixture({ failTop: true, snapshot: {
    rows: rows.map((r, i) => ({ ...r, rank: i < 2 ? 1 : 3 })),
    updatedAt: now() - 3600, retryAfter: now() - 1, unavailable: false,
  } });
  const a = await f.request(ids[0]);
  const b = await f.request('00000000-0000-4000-8000-999999999999');
  assert.equal(a.status, 200);
  assert.equal(a.data.stale, true);
  assert.equal(a.data.mineStale, true);
  assert.equal(b.data.mineUnavailable, true);
  assert.equal(f.calls.top, 1);
  assert.equal(f.calls.mine.length, 0);
  assert.equal(f.snapshot.retryAfter % 86400, 0);
  assert.ok(f.snapshot.retryAfter > now());
});

test('a warm KV snapshot also works in a different edge location without querying D1', async () => {
  const f = fixture({ failTop: true, snapshot: {
    rows: rows.map((r, i) => ({ ...r, rank: i < 2 ? 1 : 3 })),
    updatedAt: now(), retryAfter: now() + 300, unavailable: false,
  } });
  const result = await f.request();
  assert.equal(result.status, 200);
  assert.equal(result.data.top.length, 3);
  assert.equal(f.calls.top, 0);
  assert.equal(f.calls.writes, 0);
});

test('after five minutes the next viewer refreshes the public snapshot', async (t) => {
  let clock = Date.now();
  t.mock.method(Date, 'now', () => clock);
  const f = fixture();
  const first = await f.request();
  clock += 301000;
  const second = await f.request();
  assert.equal(f.calls.top, 2);
  assert.ok(second.data.cachedAt > first.data.cachedAt);
});

test('cache write failure does not break a readable board', async () => {
  const f = fixture({ failCache: true });
  assert.equal((await f.request()).status, 200);
});

test('without a KV snapshot the bundled production snapshot keeps the board visible', async () => {
  const f = fixture({ failTop: true, snapshot: null });
  const result = await f.request();
  assert.equal(result.status, 200);
  assert.equal(result.data.top.length, 10);
  assert.equal(result.data.stale, true);
  assert.equal(result.data.top[0].name, '甜心奶璐酱');
});

test('successful score write is reported as saved even if the following board read fails', async () => {
  const f = fixture({ failTop: true, failMine: true });
  const result = await f.request(null, {
    action: 'submit', token: ids[2], playerId: ids[0], name: 'Player 1', score: 100,
  });
  assert.equal(result.status, 200);
  assert.equal(result.data.recorded, true);
  assert.equal(result.data.savedScore, 100);
  assert.equal(result.data.mineUnavailable, true);
  assert.equal(f.calls.batch, 1);
});

test('a failed score transaction is never reported as saved', async () => {
  const f = fixture({ failBatch: true });
  const result = await f.request(null, {
    action: 'submit', token: ids[2], playerId: ids[0], name: 'Player 1', score: 100,
  });
  assert.equal(result.status, 503);
  assert.equal(result.data.recorded, undefined);
  assert.equal(f.calls.top, 0);
});
