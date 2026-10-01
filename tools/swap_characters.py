#!/usr/bin/env python3
"""换掉两个主角形象 + 绘制逻辑改为自适应宽高比。

改动：
  1. spriteIdle / spriteFart 换成新奶蛙素材（WebP base64）
  2. spriteNpc 换成奶蛋三视图 eggBack / eggSide / eggFront
  3. render() 里三个角色统一改为「目标高度 + 底部锚点」等比绘制，
     换任何尺寸的精灵图都不会被拉伸变形
  4. 监视者三态绑定三视图：背对(发呆) → 侧身(起疑) → 正面死盯(抓现行)
"""
import base64
import io
import os
import re
import sys

HTML = "/Users/mac/Documents/dsh/naiwa-fart/奶蛙偷偷放屁.html"
ASSETS = "/Users/mac/Documents/dsh/naiwa-fart/assets"


def uri(name):
    with open(os.path.join(ASSETS, f"{name}.webp"), "rb") as f:
        return "data:image/webp;base64," + base64.b64encode(f.read()).decode("ascii")


with io.open(HTML, encoding="utf-8") as f:
    s = f.read()

for key in ("NPC_STATES.WATCHING", "NPC_STATES.SUSPICIOUS", "spriteNpc"):
    if key not in s:
        print(f"[FAIL] 源文件缺少 {key}")
        sys.exit(1)


def sub_once(pattern, repl, label, flags=0):
    global s
    new, n = re.subn(pattern, repl, s, count=1, flags=flags)
    if n != 1:
        print(f"[FAIL] {label}: 命中 {n} 次")
        sys.exit(1)
    s = new
    print(f"[ok] {label}")


# ---- 1. 玩家两张精灵图换新 ----
sub_once(r'spriteIdle\.src = "data:image/png;base64,[^"]*";',
         f'spriteIdle.src = "{uri("player_idle")}";', "替换 spriteIdle（玩家静态）")
sub_once(r'spriteFart\.src = "data:image/png;base64,[^"]*";',
         f'spriteFart.src = "{uri("player_fart")}";', "替换 spriteFart（玩家放屁）")

# ---- 2. 监视者换成奶蛋三视图 ----
egg_decl = f"""/* 监视者「奶蛋」三视图：随怀疑度 背对 → 侧身 → 正面死盯 */
const eggBack = new Image();
eggBack.src = "{uri("egg_back")}";
const eggSide = new Image();
eggSide.src = "{uri("egg_side")}";
const eggFront = new Image();
eggFront.src = "{uri("egg_front")}";"""
sub_once(r'const spriteNpc = new Image\(\);\s*\n\s*spriteNpc\.src = "data:image/png;base64,[^"]*";',
         egg_decl, "替换 spriteNpc → 奶蛋三视图")

# ---- 3. 外部覆盖映射 ----
old_ov = """trySpriteOverride(spriteFart, "png1.png");
trySpriteOverride(spriteIdle, "png2.png");
trySpriteOverride(spriteNpc, "png3.png");
trySpriteOverride(bystanderSprites.disgust, "bys_disgust.png");
trySpriteOverride(bystanderSprites.approve, "bys_approve.png");
trySpriteOverride(bystanderSprites.envy, "bys_envy.png");
trySpriteOverride(bystanderSprites.shock, "bys_shock.png");"""
new_ov = """trySpriteOverride(spriteIdle, "player-idle.png");
trySpriteOverride(spriteFart, "player-fart.png");
trySpriteOverride(eggBack, "watcher-back.png");
trySpriteOverride(eggSide, "watcher-side.png");
trySpriteOverride(eggFront, "watcher-front.png");
trySpriteOverride(bystanderSprites.disgust, "bys_disgust.png");
trySpriteOverride(bystanderSprites.approve, "bys_approve.png");
trySpriteOverride(bystanderSprites.envy, "bys_envy.png");
trySpriteOverride(bystanderSprites.shock, "bys_shock.png");
/* 旧命名兼容：png2 = 玩家静态，png1 / png3 = 玩家放屁形态 */
trySpriteOverride(spriteIdle, "png2.png");
trySpriteOverride(spriteFart, "png1.png");
trySpriteOverride(spriteFart, "png3.png");"""
if s.count(old_ov) != 1:
    print("[FAIL] 覆盖映射块未命中")
    sys.exit(1)
s = s.replace(old_ov, new_ov)
print("[ok] 更新外部覆盖映射")

# ---- 4. 重写角色绘制段 ----
old_draw = """  // 1. Draw Player Milk Frog (1:1 High-Res 3D Sprite)
  const playerX = width * 0.33;
  const playerY = pondY - 20;

  if (isFarting) {
    // Farting Sprite (png1: 3D Squat Back View)
    const sw = 210;
    const sh = 256;
    ctx.save();
    // Wobble when farting
    const wx = (Math.random() - 0.5) * 3;
    const wy = (Math.random() - 0.5) * 2;
    ctx.drawImage(spriteFart, playerX - sw * 0.55 + wx, playerY - sh * 0.88 + wy, sw, sh);
    ctx.restore();

    // Spawn green fart particles from exact nozzle point
    const nozzleWorldX = playerX - 55 + wx;
    const nozzleWorldY = playerY - 45 + wy;
    if (Math.random() < 0.95) {
      spawnGreenFart(nozzleWorldX, nozzleWorldY);
    }
  } else {
    // Idle Sprite (png2: 3D 3/4 Side Profile Standing)
    let bellyScale = 1.0 + (gasLevel / 100) * 0.25;
    const sw = 190 * bellyScale;
    const sh = 260;
    ctx.save();
    let tremX = 0;
    if (gasLevel > 70) {
      tremX = Math.sin(Date.now() * 0.04) * ((gasLevel - 70) / 30 * 2.5);
      if (Math.random() < 0.16) spawnSweat(playerX - 20, playerY - 130);
    }
    ctx.drawImage(spriteIdle, playerX - sw * 0.52 + tremX, playerY - sh * 0.88, sw, sh);
    ctx.restore();
  }

  // 2. Draw Right Companion Milk Frog (1:1 High-Res 3D Sprite)
  const npcX = width * 0.76;
  const npcY = pondY - 18;
  const nw = 190;
  const nh = 260;
  ctx.drawImage(spriteNpc, npcX - nw * 0.5, npcY - nh * 0.88, nw, nh);

  // NPC Floating Alerts
  if (npcState === NPC_STATES.SUSPICIOUS) {
    ctx.fillStyle = "#eab308";
    ctx.font = "bold 32px sans-serif";
    ctx.textAlign = "center";
    ctx.fillText("❓", npcX, npcY - 145);
  } else if (npcState === NPC_STATES.WATCHING) {
    ctx.fillStyle = "#ef4444";
    ctx.font = "bold 36px sans-serif";
    ctx.textAlign = "center";
    ctx.fillText("❗", npcX, npcY - 148);
  }"""

new_draw = """  /* 统一角色绘制：按「目标高度 + 底边锚点」等比缩放。
     anchorX 是水平锚点（0=左缘对齐 cx，0.5=中心对齐，1=右缘对齐），
     精灵图换成任何尺寸都不会变形。 */
  const drawChar = (img, cx, baseY, targetH, anchorX, dx, dy) => {
    if (!img || !img.complete || !img.naturalWidth) return null;
    const w = targetH * (img.naturalWidth / img.naturalHeight);
    const x = cx - w * anchorX + (dx || 0);
    const y = baseY - targetH + (dy || 0);
    ctx.drawImage(img, x, y, w, targetH);
    return { x, y, w, h: targetH };
  };

  // 1. 左侧玩家奶蛙
  const playerX = width * 0.32;
  const playerY = pondY - 14;

  if (isFarting) {
    // 深蹲背身形态：本体偏在画面右侧、左侧是排气浓烟，故锚点右移
    const wx = (Math.random() - 0.5) * 3;
    const wy = (Math.random() - 0.5) * 2;
    const box = drawChar(spriteFart, playerX, playerY, 238, 0.58, wx, wy);
    if (box) {
      // 排气口落在精灵图左下侧（臀部位置）
      const nozzleWorldX = box.x + box.w * 0.24 + wx;
      const nozzleWorldY = box.y + box.h * 0.58 + wy;
      if (Math.random() < 0.95) spawnGreenFart(nozzleWorldX, nozzleWorldY);
    }
  } else {
    let tremX = 0;
    if (gasLevel > 70) {
      tremX = Math.sin(Date.now() * 0.04) * ((gasLevel - 70) / 30 * 2.5);
      if (Math.random() < 0.16) spawnSweat(playerX - 20, playerY - 130);
    }
    // 胀气越高整体等比撑大（不再横向拉伸，避免把新素材拉变形）
    const gasScale = 1.0 + (gasLevel / 100) * 0.07;
    drawChar(spriteIdle, playerX, playerY, 248 * gasScale, 0.5, tremX, 0);
  }

  // 2. 右侧监视者奶蛋：三态对应三视图（背对 → 侧身 → 正面死盯）
  const npcX = width * 0.76;
  const npcY = pondY - 12;
  const npcImg = npcState === NPC_STATES.WATCHING ? eggFront
               : npcState === NPC_STATES.SUSPICIOUS ? eggSide
               : eggBack;
  const npcBox = drawChar(npcImg, npcX, npcY, 232, 0.5, 0, 0);

  // 头顶提示符号（跟随奶蛋实际头顶位置）
  const npcTop = npcBox ? npcBox.y : npcY - 232;
  if (npcState === NPC_STATES.SUSPICIOUS) {
    ctx.fillStyle = "#eab308";
    ctx.font = "bold 32px sans-serif";
    ctx.textAlign = "center";
    ctx.fillText("❓", npcX, npcTop + 6);
  } else if (npcState === NPC_STATES.WATCHING) {
    ctx.fillStyle = "#ef4444";
    ctx.font = "bold 36px sans-serif";
    ctx.textAlign = "center";
    ctx.fillText("❗", npcX, npcTop + 4);
  }"""

if s.count(old_draw) != 1:
    print("[FAIL] 角色绘制段未命中")
    sys.exit(1)
s = s.replace(old_draw, new_draw)
print("[ok] 重写角色绘制段（自适应宽高比）")

with io.open(HTML, "w", encoding="utf-8") as f:
    f.write(s)

left = len(re.findall(r"spriteNpc", s))
print(f"\nspriteNpc 残留引用: {left} 处")
print("文件大小 %.0f KB" % (len(s.encode("utf-8")) / 1024))
