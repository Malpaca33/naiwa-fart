import bootstrapSnapshot from '../../lib/leaderboard-bootstrap.js';

const json = (body, status = 200) => new Response(JSON.stringify(body), {
  status,
  headers: {
    'content-type': 'application/json; charset=utf-8',
    'cache-control': 'no-store',
    'x-content-type-options': 'nosniff',
  },
});

const isUuid = (value) => typeof value === 'string'
  && /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(value);

function publicName(playerId) {
  return `奶家人 ${playerId.slice(0, 6).toUpperCase()}`;
}

function cleanName(value) {
  if (typeof value !== 'string') return null;
  const name = value.trim().replace(/\s+/g, ' ');
  return /^[\p{L}\p{N}_ -]{1,12}$/u.test(name) ? name : null;
}

const TOP_KEY = 'leaderboard:top:v1';
const TOP_TTL = 300;
const MINE_TTL = 60;
const nowSeconds = () => Math.floor(Date.now() / 1000);
const quotaExceeded = (error) => /7500|free tier|daily.*limit|exceeded.*(?:read|write)/i.test(String(error));
const nextQuotaReset = () => (Math.floor(nowSeconds() / 86400) + 1) * 86400;

function cacheKey(context, suffix) {
  return new Request(`${new URL(context.request.url).origin}/__leaderboard-cache/v1/${suffix}`);
}

async function readEdge(context, suffix) {
  try {
    const hit = await globalThis.caches?.default.match(cacheKey(context, suffix));
    return hit ? await hit.json() : null;
  } catch (_) { return null; }
}

function background(context, promise) {
  // 缓存失败不能改变已经保存成绩的结果。
  context.waitUntil(promise.catch((error) => console.error('leaderboard cache error', error)));
}

function writeEdge(context, suffix, value, ttl) {
  if (!globalThis.caches?.default) return;
  background(context, globalThis.caches.default.put(cacheKey(context, suffix), new Response(JSON.stringify(value), {
    headers: { 'content-type': 'application/json', 'cache-control': `public, max-age=${Math.max(1, ttl)}` },
  })));
}

function validSnapshot(value) {
  return value && Array.isArray(value.rows) && value.rows.length <= 10
    && Number.isSafeInteger(value.updatedAt) && Number.isSafeInteger(value.retryAfter)
    && value.rows.every((row) => typeof row.name === 'string'
      && (isUuid(row.player_id) || (row.player_id === null && row.name.length > 0))
      && Number.isSafeInteger(row.score) && row.score >= 0 && Number.isSafeInteger(row.rank) && row.rank > 0);
}

async function readTop(context) {
  const { env } = context;
  const edge = await readEdge(context, 'top');
  let snapshot = validSnapshot(edge) ? edge : null;
  if (!snapshot && env.PLAY_COUNTER) {
    try {
      const stored = await env.PLAY_COUNTER.get(TOP_KEY, { type: 'json', cacheTtl: 60 });
      if (validSnapshot(stored)) snapshot = stored;
    } catch (error) { console.error('leaderboard snapshot read error', error); }
  }
  // 首次部署时 D1 和 KV 均已达到当日额度，保留已导出的真实榜单作为最后备用。
  if (!snapshot && validSnapshot(bootstrapSnapshot)) snapshot = bootstrapSnapshot;
  if (!snapshot || snapshot.retryAfter <= nowSeconds()) {
    try {
      // 使用现有排序索引只取十条；并列名次在十条记录中计算，不再扫描全榜。
      const top = await env.LEADERBOARD_DB.prepare(
        'SELECT player_id, name, score FROM leaderboard_scores ORDER BY score DESC, achieved_at ASC LIMIT 10'
      ).all();
      let rank = 1;
      const rows = (top.results || []).map((row, index, all) => {
        if (index === 0 || row.score !== all[index - 1].score) rank = index + 1;
        return { ...row, rank };
      });
      snapshot = { rows, updatedAt: nowSeconds(), retryAfter: nowSeconds() + TOP_TTL, unavailable: false };
    } catch (error) {
      if (!snapshot) throw error;
      snapshot = { ...snapshot, unavailable: true,
        retryAfter: quotaExceeded(error) ? nextQuotaReset() : nowSeconds() + TOP_TTL };
      console.error('leaderboard refresh error', error);
    }
    if (env.PLAY_COUNTER) background(context, env.PLAY_COUNTER.put(TOP_KEY, JSON.stringify(snapshot)));
  }
  const ttl = Math.min(TOP_TTL, Math.max(1, snapshot.retryAfter - nowSeconds()));
  // 不重新写入已命中的边缘缓存，避免每次浏览都产生缓存写操作。
  if (!edge || edge !== snapshot) writeEdge(context, 'top', snapshot, ttl);
  return snapshot;
}

async function readMine(context, playerId, snapshot, force) {
  if (!isUuid(playerId)) return { mine: null, mineUnavailable: false };
  if (!force) {
    const cached = await readEdge(context, `mine/${playerId}`);
    if (cached) return { ...cached,
      mineUnavailable: cached.mineUnavailable || Boolean(!cached.mine && snapshot?.unavailable),
      mineStale: Boolean(cached.mine && snapshot?.unavailable) };
  }
  if (snapshot?.unavailable && !force) {
    const row = snapshot.rows.find((entry) => entry.player_id === playerId);
    return { mine: row ? { name: row.name || publicName(playerId), score: row.score, rank: row.rank } : null,
      mineUnavailable: !row, mineStale: Boolean(row) };
  }
  try {
    const row = await context.env.LEADERBOARD_DB.prepare(
      'SELECT name, score, (SELECT COUNT(*) + 1 FROM leaderboard_scores WHERE score > s.score) AS rank FROM leaderboard_scores s WHERE player_id = ?'
    ).bind(playerId).first();
    const value = { mine: row ? { name: row.name || publicName(playerId), score: row.score, rank: row.rank } : null,
      mineUnavailable: false };
    writeEdge(context, `mine/${playerId}`, value, MINE_TTL);
    return value;
  } catch (error) {
    console.error('leaderboard personal rank error', error);
    const value = { mine: null, mineUnavailable: true };
    writeEdge(context, `mine/${playerId}`, value, MINE_TTL);
    return value;
  }
}

async function readBoard(context, playerId, { saved = false } = {}) {
  let snapshot;
  try { snapshot = await readTop(context); }
  catch (error) {
    if (!saved) throw error;
    // 写入已经成功，随后无法读取排名时仍返回成功，不能误报“成绩未上传”。
    console.error('leaderboard read after save error', error);
    return { top: [], mine: null, mineUnavailable: true, topUnavailable: true };
  }
  const personal = await readMine(context, playerId, snapshot, saved);
  return {
    top: snapshot.rows.map((row) => ({
      rank: row.rank,
      name: row.name || publicName(row.player_id),
      score: row.score,
      mine: row.player_id === playerId,
    })),
    ...personal,
    cachedAt: snapshot.updatedAt,
    stale: Boolean(snapshot.unavailable),
  };
}

export async function onRequest(context) {
  const { request, env } = context;
  if (!env.LEADERBOARD_DB) return json({ error: '排行榜暂不可用' }, 503);
  try {
    if (request.method === 'GET') {
      const url = new URL(request.url);
      return json(await readBoard(context, url.searchParams.get('playerId')));
    }
    if (request.method !== 'POST') return json({ error: '不支持此请求' }, 405);

    if (Number(request.headers.get('content-length')) > 512) {
      return json({ error: '请求过长' }, 413);
    }
    const body = await request.json().catch(() => null);
    if (!body || typeof body !== 'object') return json({ error: '请求格式错误' }, 400);

    if (body.action === 'start') {
      if (Math.random() < 0.02) {
        await env.LEADERBOARD_DB.prepare(
          'DELETE FROM leaderboard_runs WHERE started_at < unixepoch() - 86400'
        ).run();
      }
      const token = crypto.randomUUID();
      await env.LEADERBOARD_DB.prepare(
        'INSERT INTO leaderboard_runs (token, started_at) VALUES (?, unixepoch())'
      ).bind(token).run();
      return json({ token });
    }
    if (body.action === 'rename') {
      const name = cleanName(body.name);
      if (!isUuid(body.playerId) || !name) return json({ error: '名字只能用 1～12 个字、字母或数字' }, 400);
      await env.LEADERBOARD_DB.prepare(
        'UPDATE leaderboard_scores SET name = ? WHERE player_id = ?'
      ).bind(name, body.playerId).run();
      return json({ ...await readBoard(context, body.playerId, { saved: true }), nameSaved: true });
    }
    if (body.action !== 'submit' || !isUuid(body.token) || !isUuid(body.playerId)
        || !cleanName(body.name) || !Number.isSafeInteger(body.score)
        || body.score < 0 || body.score > 1000000) {
      return json({ error: '成绩格式错误' }, 400);
    }

    const run = await env.LEADERBOARD_DB.prepare(
      'SELECT started_at, submitted_at FROM leaderboard_runs WHERE token = ?'
    ).bind(body.token).first();
    if (!run || run.submitted_at !== null) return json({ error: '本局成绩已提交或已失效' }, 409);
    const now = Math.floor(Date.now() / 1000);
    const duration = now - run.started_at;
    // 游戏计分最高为起风时的 70 × 1.8 = 126 ml/s，宽限网络与整数计时误差。
    if (duration < 0 || duration > 86400) return json({ error: '本局开局记录已过期' }, 422);
    if (body.score > Math.floor(126 * (duration + 3) + 20)) {
      return json({ error: '成绩超过本局登记时长允许值' }, 422);
    }
    // 成绩写入与令牌消耗放进同一个事务；写入失败时令牌仍能重试。
    const saved = await env.LEADERBOARD_DB.batch([
      env.LEADERBOARD_DB.prepare(
      `INSERT INTO leaderboard_scores (player_id, name, score, achieved_at)
       SELECT ?, ?, ?, unixepoch() FROM leaderboard_runs WHERE token = ? AND submitted_at IS NULL
       ON CONFLICT(player_id) DO UPDATE SET
         name = excluded.name,
         achieved_at = CASE WHEN excluded.score > leaderboard_scores.score THEN excluded.achieved_at ELSE leaderboard_scores.achieved_at END,
         score = MAX(leaderboard_scores.score, excluded.score)
       RETURNING score`
      ).bind(body.playerId, cleanName(body.name), body.score, body.token),
      env.LEADERBOARD_DB.prepare(
        'UPDATE leaderboard_runs SET submitted_at = unixepoch() WHERE token = ? AND submitted_at IS NULL'
      ).bind(body.token),
    ]);
    if (saved[1].meta.changes !== 1) return json({ error: '本局成绩已提交' }, 409);
    return json({ ...await readBoard(context, body.playerId, { saved: true }), recorded: true,
      savedScore: saved[0].results[0].score });
  } catch (error) {
    console.error('leaderboard error', error);
    return json({ error: quotaExceeded(error)
      ? '数据库今日额度已用完，请北京时间早上 8 点恢复后重试'
      : '排行榜暂不可用' }, 503);
  }
}
