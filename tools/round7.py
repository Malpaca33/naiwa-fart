#!/usr/bin/env python3
"""第七轮改动：

  1. 换装从「单个换衣按钮」改为四个纯文字选项：花肚兜 / Luke / 冰红茶 / 奶秘
     （四套素材全部内嵌；再点当前选项可回到原样）
  2. 结算新增称号：1000 胀气 / 2000 小臭屁 / 3800 浓醇 / 5000 屁王 /
     10000 根本没有这样的奶蛙
"""
import base64
import io
import os
import re
import sys

from PIL import Image

HTML = "/Users/mac/Documents/dsh/naiwa-fart/奶蛙偷偷放屁.html"
ASSETS = "/Users/mac/Documents/dsh/naiwa-fart/assets"
H = 360

SKINS = [
    ("floral", "花肚兜", "costume_floral"),
    ("luke",   "Luke",   "costume_luke"),
    ("tea",    "冰红茶", "costume_tea"),
    ("secret", "奶秘",   "costume_secret"),
]

uris = {}
for key, label, fname in SKINS:
    src = Image.open(f"{ASSETS}/src/{fname}.png").convert("RGBA")
    w = round(src.width * H / src.height)
    out = src.resize((w, H), Image.LANCZOS)
    p = f"{ASSETS}/{fname}.webp"
    out.save(p, "WEBP", quality=88, method=4)
    with open(p, "rb") as f:
        uris[key] = "data:image/webp;base64," + base64.b64encode(f.read()).decode("ascii")
    print(f"[ok] {label:<6} {w}x{H}  {os.path.getsize(p)/1024:.1f}KB")

with io.open(HTML, encoding="utf-8") as f:
    s = f.read()

R = []

# ---------- 1. 精灵声明：用四套换装替换掉原来那一份（避免重复内嵌） ----------
sprite_decl = "\n".join(
    f'const spriteSkin{key.capitalize()} = new Image();\n'
    f'spriteSkin{key.capitalize()}.src = "{uris[key]}";'
    for key, _, _ in SKINS
)
old_decl = re.compile(
    r'/\* 玩家「大花袄」形态（换衣按钮切换） \*/\n'
    r'const spriteIdleCostume = new Image\(\);\n'
    r'spriteIdleCostume\.src = "data:image/webp;base64,[^"]*";'
)
if len(old_decl.findall(s)) != 1:
    print("[FAIL] 未匹配到原 spriteIdleCostume 声明")
    sys.exit(1)
s = old_decl.sub(
    "/* 玩家换装形态（四个纯文字选项切换） */\n" + sprite_decl, s, count=1
)
print("[ok] 改动 #1 四套换装精灵已替换原单份声明")

# 用换装表替换掉原来那一个 costume 精灵，保持代码干净
R.append((
"""trySpriteOverride(spriteIdleCostume, "player-idle-costume.png");""",
"""trySpriteOverride(spriteSkinFloral, "skin-floral.png");
trySpriteOverride(spriteSkinLuke, "skin-luke.png");
trySpriteOverride(spriteSkinTea, "skin-tea.png");
trySpriteOverride(spriteSkinSecret, "skin-secret.png");"""))

# ---------- 2. 状态：activeSkin 取代 costumeOn ----------
R.append((
"""let costumeOn = false;      // 是否穿着大花袄""",
"""/* 换装：null = 原样；否则是 SKIN_SPRITES 里的键 */
const SKIN_SPRITES = {
  floral: spriteSkinFloral,
  luke: spriteSkinLuke,
  tea: spriteSkinTea,
  secret: spriteSkinSecret,
};
let activeSkin = null;"""))

# ---------- 3. 渲染时按 activeSkin 选形态 ----------
R.append((
"""    const idleImg = (costumeOn && spriteIdleCostume.complete && spriteIdleCostume.naturalWidth)
      ? spriteIdleCostume : spriteIdle;""",
"""    const skinImg = activeSkin ? SKIN_SPRITES[activeSkin] : null;
    const idleImg = (skinImg && skinImg.complete && skinImg.naturalWidth)
      ? skinImg : spriteIdle;"""))

# ---------- 4. HTML：四个文字选项 ----------
R.append((
"""    <button class="btn-skin" id="skin-btn">👗 换衣：换大花袄</button>""",
"""    <div class="skin-row" id="skin-row">
      <button class="skin-chip" data-skin="floral">花肚兜</button>
      <button class="skin-chip" data-skin="luke">Luke</button>
      <button class="skin-chip" data-skin="tea">冰红茶</button>
      <button class="skin-chip" data-skin="secret">奶秘</button>
    </div>"""))

# ---------- 5. CSS ----------
R.append((
"""    .btn-skin {
      margin-top: 10px;
      padding: 8px 20px;
      border-radius: 20px;
      background: #f1f5f9;
      border: 1.5px solid #cbd5e1;
      color: #334155;
      font-size: 13px;
      font-weight: 800;
      cursor: pointer;
      transition: all 0.15s ease;
    }
    .btn-skin.on {
      background: #fee2e2;
      border-color: #ef4444;
      color: #b91c1c;
    }""",
"""    /* 换装：纯文字选项 */
    .skin-row {
      display: flex;
      flex-wrap: wrap;
      justify-content: center;
      gap: 8px;
      margin-top: 10px;
    }
    .skin-chip {
      padding: 6px 15px;
      border-radius: 16px;
      background: #f1f5f9;
      border: 1.5px solid #cbd5e1;
      color: #334155;
      font-size: 13px;
      font-weight: 800;
      cursor: pointer;
      transition: all 0.15s ease;
    }
    .skin-chip.on {
      background: #dbeafe;
      border-color: #3b82f6;
      color: #1d4ed8;
    }"""))

# ---------- 6. 元素引用 ----------
R.append((
"""const skinBtn = document.getElementById('skin-btn');""",
"""const modalRank = document.getElementById('modal-rank');"""))

# ---------- 7. 事件：点选换装 ----------
R.append((
"""skinBtn.addEventListener('click', () => {
  sounds.init();                       // 借这次点击解锁音频上下文
  costumeOn = !costumeOn;
  skinBtn.classList.toggle('on', costumeOn);
  skinBtn.textContent = costumeOn ? "👗 换衣：换回原样" : "👗 换衣：换大花袄";
});""",
"""/* 换装：点某项即换，再点当前项回到原样 */
document.querySelectorAll('.skin-chip').forEach((btn) => {
  btn.addEventListener('click', () => {
    sounds.init();                     // 借这次点击解锁音频上下文
    const key = btn.dataset.skin;
    activeSkin = (activeSkin === key) ? null : key;
    document.querySelectorAll('.skin-chip').forEach((b) => {
      b.classList.toggle('on', b.dataset.skin === activeSkin);
    });
  });
});"""))

# ---------- 8. 结算称号 ----------
R.append((
"""/* 旁观奶蛙冒一句吐槽，累积着往上飘 */""",
"""/* 结算称号：按最终放屁量（ml）取最高达成档 */
const FART_TITLES = [
  { ml: 10000, label: '根本没有这样的奶蛙' },
  { ml: 5000, label: '屁王' },
  { ml: 3800, label: '浓醇' },
  { ml: 2000, label: '小臭屁' },
  { ml: 1000, label: '胀气' },
];
function fartTitle(ml) {
  for (const t of FART_TITLES) {
    if (ml >= t.ml) return t.label;
  }
  return null;
}

/* 旁观奶蛙冒一句吐槽，累积着往上飘 */"""))

R.append((
"""      <div class="modal-desc" id="modal-desc">你在安静时偷偷放屁，被同伴猛回头抓个正着！</div>""",
"""      <div class="modal-desc" id="modal-desc">你在安静时偷偷放屁，被同伴猛回头抓个正着！</div>
      <div class="modal-rank" id="modal-rank">称号 · 胀气</div>"""))

R.append((
"""    .modal-stats {
      background: #f8fafc;""",
"""    .modal-rank {
      display: inline-block;
      margin: 0 auto 16px;
      padding: 6px 22px;
      border-radius: 999px;
      background: linear-gradient(135deg, #fef3c7, #fde68a);
      border: 2px solid #f59e0b;
      color: #92400e;
      font-size: 18px;
      font-weight: 900;
      letter-spacing: 1px;
    }
    .modal-stats {
      background: #f8fafc;"""))

R.append((
"""  statTime.textContent = `${fartSeconds.toFixed(1)}s`;""",
"""  const title = fartTitle(Math.floor(score));
  if (title) {
    modalRank.textContent = '称号 · ' + title;
    modalRank.style.display = 'inline-block';
  } else {
    modalRank.style.display = 'none';
  }
  statTime.textContent = `${fartSeconds.toFixed(1)}s`;"""))

for i, (old, new) in enumerate(R, 1):
    n = s.count(old)
    if n != 1:
        print(f"[FAIL] 改动 #{i} 命中 {n} 次（应为 1）")
        sys.exit(1)
    s = s.replace(old, new)
    print(f"[ok] 改动 #{i}")

for dead in ("skinBtn", "costumeOn"):
    if dead in s:
        print(f"[warn] 仍有 {dead} 残留 {s.count(dead)} 处")

with io.open(HTML, "w", encoding="utf-8") as f:
    f.write(s)
print("写入完成 %.0f KB" % (len(s.encode("utf-8")) / 1024))
