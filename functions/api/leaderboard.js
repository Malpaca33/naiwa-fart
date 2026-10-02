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

async function readBoard(db, playerId) {
  const top = await db.prepare(
    `SELECT player_id, score, RANK() OVER (ORDER BY score DESC) AS rank
     FROM leaderboard_scores ORDER BY score DESC, achieved_at ASC LIMIT 10`
  ).all();
  let mine = null;
  if (isUuid(playerId)) {
    const row = await db.prepare(
      'SELECT score, (SELECT COUNT(*) + 1 FROM leaderboard_scores WHERE score > s.score) AS rank FROM leaderboard_scores s WHERE player_id = ?'
    ).bind(playerId).first();
    if (row) mine = { score: row.score, rank: row.rank };
  }
  return {
    top: (top.results || []).map((row) => ({
      rank: row.rank,
      name: publicName(row.player_id),
      score: row.score,
      mine: row.player_id === playerId,
    })),
    mine,
  };
}

export async function onRequest(context) {
  const { request, env } = context;
  if (!env.LEADERBOARD_DB) return json({ error: '排行榜暂不可用' }, 503);
  try {
    if (request.method === 'GET') {
      const url = new URL(request.url);
      return json(await readBoard(env.LEADERBOARD_DB, url.searchParams.get('playerId')));
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
    if (body.action !== 'submit' || !isUuid(body.token) || !isUuid(body.playerId)
        || !Number.isSafeInteger(body.score) || body.score < 0 || body.score > 1000000) {
      return json({ error: '成绩格式错误' }, 400);
    }

    const run = await env.LEADERBOARD_DB.prepare(
      'SELECT started_at, submitted_at FROM leaderboard_runs WHERE token = ?'
    ).bind(body.token).first();
    if (!run || run.submitted_at !== null) return json({ error: '本局成绩已提交或已失效' }, 409);
    const now = Math.floor(Date.now() / 1000);
    const duration = now - run.started_at;
    // 游戏计分最高为起风时的 70 × 1.8 = 126 ml/s，宽限网络与整数计时误差。
    if (duration < 0 || duration > 3600 || body.score > Math.floor(126 * (duration + 3) + 20)) {
      return json({ error: '成绩与本局时长不符' }, 422);
    }
    const claimed = await env.LEADERBOARD_DB.prepare(
      'UPDATE leaderboard_runs SET submitted_at = unixepoch() WHERE token = ? AND submitted_at IS NULL'
    ).bind(body.token).run();
    if (claimed.meta.changes !== 1) return json({ error: '本局成绩已提交' }, 409);

    await env.LEADERBOARD_DB.prepare(
      `INSERT INTO leaderboard_scores (player_id, score, achieved_at) VALUES (?, ?, unixepoch())
       ON CONFLICT(player_id) DO UPDATE SET score = excluded.score, achieved_at = excluded.achieved_at
       WHERE excluded.score > leaderboard_scores.score`
    ).bind(body.playerId, body.score).run();
    return json(await readBoard(env.LEADERBOARD_DB, body.playerId));
  } catch (error) {
    console.error('leaderboard error', error);
    return json({ error: '排行榜暂不可用' }, 500);
  }
}
