/**
 * 玩家人次计数器（Cloudflare Pages Function）
 *
 *   GET  /api/plays  → 只读取当前人次
 *   POST /api/plays  → 人次 +1 并返回新值
 *
 * 数据存在 KV 命名空间 PLAY_COUNTER 的 total 键里。
 * 计数口径是「人次」：每打开一次页面算一次。
 */
export async function onRequest(context) {
  const { request, env } = context;
  const KEY = 'total';

  const json = (body, status = 200) =>
    new Response(JSON.stringify(body), {
      status,
      headers: {
        'content-type': 'application/json; charset=utf-8',
        'cache-control': 'no-store',
      },
    });

  try {
    let total = parseInt((await env.PLAY_COUNTER.get(KEY)) || '0', 10);
    if (!Number.isFinite(total) || total < 0) total = 0;

    if (request.method === 'POST') {
      total += 1;
      await env.PLAY_COUNTER.put(KEY, String(total));
    }
    return json({ total });
  } catch (err) {
    return json({ total: null, error: String(err) }, 500);
  }
}
