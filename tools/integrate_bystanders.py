#!/usr/bin/env python3
"""把旁观奶蛙（4 种反应表情）接入《奶蛙偷偷放屁》单文件。

做四件事：
  1. 内嵌 4 张 WebP 精灵图（base64）
  2. 补上外部同名文件覆盖机制（方便替换建模）
  3. 加 BYSTANDER_TIERS 档位状态机，按累计放屁量升档
  4. 在 render() 前景中下方画出旁观奶蛙，换档时冒反应标签
"""
import base64
import io
import os
import sys

HTML = "/Users/mac/Documents/dsh/naiwa-fart/奶蛙偷偷放屁.html"
ASSETS = "/Users/mac/Documents/dsh/naiwa-fart/assets"

# 升档顺序由用户指定：嫌弃 → 认可 → 羡慕 → 惊吓
TIERS = [
    ("disgust", "嫌弃", 0),
    ("approve", "认可", 250),
    ("envy", "羡慕", 750),
    ("shock", "惊吓", 1600),
]


def data_uri(name):
    p = os.path.join(ASSETS, f"bys_{name}.webp")
    with open(p, "rb") as f:
        return "data:image/webp;base64," + base64.b64encode(f.read()).decode("ascii")


with io.open(HTML, encoding="utf-8") as f:
    s = f.read()

edits = []

# ---------- 1 + 2. 精灵图声明 + 外部覆盖机制 ----------
sprite_lines = []
for key, zh, _ in TIERS:
    sprite_lines.append(f'bystanderSprites.{key}.src = "{data_uri(key)}";')

sprite_block = """/* ==========================================================================
   Bystander Sprites (旁观奶蛙 · 四种反应表情)
   升档顺序：""" + " → ".join(zh for _, zh, _ in TIERS) + """
   ========================================================================== */
const bystanderSprites = {
""" + "\n".join(f"  {k}: new Image()," for k, _, _ in TIERS) + """
};
""" + "\n".join(sprite_lines) + """

/* 同级目录下放同名文件即可覆盖内嵌精灵图（文件不存在时自动忽略，方便替换建模） */
function trySpriteOverride(img, url) {
  const probe = new Image();
  probe.onload = () => { img.src = url; };
  probe.src = url;
}
trySpriteOverride(spriteFart, "png1.png");
trySpriteOverride(spriteIdle, "png2.png");
trySpriteOverride(spriteNpc, "png3.png");
""" + "\n".join(f'trySpriteOverride(bystanderSprites.{k}, "bys_{k}.png");' for k, _, _ in TIERS) + """

"""

edits.append((
    "/* ==========================================================================\n"
    "   UI Setup & Grid Elements\n"
    "   ========================================================================== */",
    sprite_block + "/* ==========================================================================\n"
    "   UI Setup & Grid Elements\n"
    "   ========================================================================== */",
))

# ---------- 3. 档位状态机 ----------
tier_table = "\n".join(
    f"  {{ ml: {ml}, key: '{k}', label: '{zh}' }}," for k, zh, ml in TIERS
)
state_block = """/* 旁观奶蛙反应档位：按累计放屁量（排气量 ml）升档 */
const BYSTANDER_TIERS = [
""" + tier_table + """
];
let bystanderTier = 0;
let bystanderPop = 0;      // 换档弹跳 / 标签计时

"""

edits.append(("const NPC_STATES = {", state_block + "const NPC_STATES = {"))

# ---------- 4. update() 里算档位 ----------
edits.append((
    "  // 6. Update UI (Grids & Score)\n  updateHUDGrids();\n}",
    """  // 6. Bystander reaction tier（按累计放屁量升档）
  let bt = 0;
  for (let i = 0; i < BYSTANDER_TIERS.length; i++) {
    if (score >= BYSTANDER_TIERS[i].ml) bt = i;
  }
  if (bt !== bystanderTier) {
    bystanderTier = bt;
    bystanderPop = 1.0;
  }
  if (bystanderPop > 0) bystanderPop = Math.max(0, bystanderPop - dt * 1.6);

  // 7. Update UI (Grids & Score)
  updateHUDGrids();
}""",
))

# ---------- 5. render() 里画旁观奶蛙 ----------
draw_block = """  // 3. Draw Bystander Milk Frog (旁观奶蛙，站在画面前景中下方)
  {
    const tier = BYSTANDER_TIERS[bystanderTier];
    const img = bystanderSprites[tier.key];
    if (img && img.complete && img.naturalWidth) {
      const ratio = img.naturalWidth / img.naturalHeight;
      const pop = bystanderPop > 0 ? 1 + Math.sin(bystanderPop * Math.PI) * 0.16 : 1;
      const bh = Math.min(150, height * 0.34) * pop;
      const bw = bh * ratio;
      const bx = width * 0.47;
      const baseY = height * 0.99;
      const bob = Math.sin(Date.now() * 0.003) * 3;

      ctx.drawImage(img, bx - bw / 2, baseY - bh + bob, bw, bh);

      // 换档瞬间冒一个反应标签（约 1 秒后淡出）
      if (bystanderPop > 0.45) {
        const a = Math.min(1, (bystanderPop - 0.45) / 0.3);
        const tagY = baseY - bh - 16;
        ctx.save();
        ctx.globalAlpha = a;
        ctx.font = "bold 15px sans-serif";
        ctx.textAlign = "center";
        const tw = ctx.measureText(tier.label).width;
        ctx.fillStyle = "#0f172a";
        ctx.beginPath();
        if (ctx.roundRect) {
          ctx.roundRect(bx - tw / 2 - 12, tagY - 18, tw + 24, 27, 13);
        } else {
          ctx.rect(bx - tw / 2 - 12, tagY - 18, tw + 24, 27);
        }
        ctx.fill();
        ctx.fillStyle = "#ffffff";
        ctx.fillText(tier.label, bx, tagY + 1);
        ctx.restore();
      }
    }
  }

  // 4. Green Fart Smoke and Sweat
  updateAndDrawParticles();"""

edits.append((
    "  // 3. Green Fart Smoke and Sweat\n  updateAndDrawParticles();",
    draw_block,
))

# ---------- 6. restart() 重置 ----------
edits.append((
    "  npcState = NPC_STATES.IDLE;\n  nextNpcCheckTimer = 4.0;",
    "  npcState = NPC_STATES.IDLE;\n  nextNpcCheckTimer = 4.0;\n"
    "  bystanderTier = 0;\n  bystanderPop = 0;",
))

for i, (old, new) in enumerate(edits, 1):
    n = s.count(old)
    if n != 1:
        print(f"[FAIL] 编辑 #{i} 命中 {n} 次（应为 1）")
        sys.exit(1)
    s = s.replace(old, new)
    print(f"[ok] 编辑 #{i}")

with io.open(HTML, "w", encoding="utf-8") as f:
    f.write(s)
print("写入完成，文件大小 %.0f KB" % (len(s.encode("utf-8")) / 1024))
