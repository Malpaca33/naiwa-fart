#!/usr/bin/env python3
"""第五轮改动：

  1. 超级大屁期间奶蛙「调头朝右」对着奶蛋喷（整只水平镜像，烟改朝右飞）
  2. 起风期间奶蛋完全不察觉：不转头、不进起疑/抓现行
  3. ❓❗ 再放大三档（44px → 66px）
  4. 底下旁观奶蛙改为按「单次放屁量」变脸，阈值 100 / 300 / 500，破 800 进狂暴
  5. 场景换成室内：木地板 + 两张椅子（原池塘与荷叶移除）
"""
import io
import sys

HTML = "/Users/mac/Documents/dsh/naiwa-fart/奶蛙偷偷放屁.html"

with io.open(HTML, encoding="utf-8") as f:
    s = f.read()

R = []

# ---------- 1. 粒子加方向参数（默认朝左） ----------
R.append((
"""function spawnGreenFart(x, y) {
  const angle = Math.PI * 0.95 + (Math.random() - 0.5) * 0.8;""",
"""/* dir: -1 = 朝左喷（默认），+1 = 朝右喷（超级大屁调头对着奶蛋） */
function spawnGreenFart(x, y, dir) {
  const d = (dir === undefined) ? -1 : dir;
  const baseAngle = d < 0 ? Math.PI * 0.95 : Math.PI * 0.05;
  const angle = baseAngle + (Math.random() - 0.5) * 0.8;"""))

# ---------- 2. 旁观奶蛙：改为按单次放屁量升档 ----------
R.append((
"""/* 旁观奶蛙反应档位：按累计放屁量（排气量 ml）升档 */
const BYSTANDER_TIERS = [
  { ml: 0, key: 'disgust', label: '嫌弃' },
  { ml: 250, key: 'approve', label: '认可' },
  { ml: 750, key: 'envy', label: '羡慕' },
  { ml: 1600, key: 'shock', label: '惊吓' },
];
let bystanderTier = 0;
let bystanderPop = 0;      // 换档弹跳 / 标签计时""",
"""/* 旁观奶蛙反应档位：按「单次放屁量」升档（一泡屁从按下开始重新计） */
const BYSTANDER_TIERS = [
  { ml: 0, key: 'disgust', label: '嫌弃' },
  { ml: 100, key: 'approve', label: '认可' },
  { ml: 300, key: 'envy', label: '羡慕' },
  { ml: 500, key: 'shock', label: '惊吓' },
];
const BYSTANDER_RAGE_ML = 800;   // 单次放屁量破 800：惊吓升级成狂暴
const BYSTANDER_HOLD = 1.5;      // 松手后维持表情的秒数，再回到「嫌弃」
let bystanderTier = 0;
let bystanderPop = 0;      // 换档弹跳 / 标签计时
let bystanderHold = 0;
let fartVolume = 0;        // 本次放屁已经放了多少 ml"""))

# ---------- 3. startFart 重置单次放屁量 ----------
R.append((
"""  if (!isFarting) {
    isFarting = true;
    fartBtn.classList.add('active');""",
"""  if (!isFarting) {
    isFarting = true;
    fartVolume = 0;          // 新的一泡屁，从头开始算
    bystanderHold = BYSTANDER_HOLD;
    fartBtn.classList.add('active');"""))

# ---------- 4. 累计单次放屁量 ----------
R.append((
"""    // 「只要一放屁就计量」：基础 70ml/s，按下即开始涨，起风掩护期再乘 1.8。
    // 用浮点累加、显示时才取整，避免高刷屏下某些帧四舍五入成 0 而看着卡住不动。
    score += 70 * dt * (isCoverActive ? 1.8 : 1);""",
"""    // 「只要一放屁就计量」：基础 70ml/s，按下即开始涨，起风掩护期再乘 1.8。
    // 用浮点累加、显示时才取整，避免高刷屏下某些帧四舍五入成 0 而看着卡住不动。
    const gain = 70 * dt * (isCoverActive ? 1.8 : 1);
    score += gain;
    fartVolume += gain;      // 单次放屁量：旁观奶蛙据此变脸"""))

# ---------- 5. 起风期间奶蛋完全不察觉 ----------
R.append((
"""  } else if (npcState === NPC_STATES.IDLE) {
    nextNpcCheckTimer -= dt;
    if (nextNpcCheckTimer <= 0) {
      npcState = NPC_STATES.SUSPICIOUS;""",
"""  } else if (isCoverActive) {
    // 起风了：风声盖过一切，奶蛋根本不会转头扫描察觉，老老实实背对着
    npcState = NPC_STATES.IDLE;
    npcStateTimer = 0;
    npcReactTimer = 0;
    nextNpcCheckTimer = Math.max(nextNpcCheckTimer, 1.6);
  } else if (npcState === NPC_STATES.IDLE) {
    nextNpcCheckTimer -= dt;
    if (nextNpcCheckTimer <= 0) {
      npcState = NPC_STATES.SUSPICIOUS;"""))

# ---------- 6. 超级大屁：喷射改朝右 ----------
R.append((
"""  // 慢放：喷射持续 1.4 秒慢慢涌出，而不是一帧炸完
  if (megaFartTimer > 0) {
    megaFartTimer -= dt;
    const mx = width * 0.32 - 72;
    const my = height * 0.72 - 58;
    for (let i = 0; i < 3; i++) {
      spawnGreenFart(mx + (Math.random() - 0.5) * 190,
                     my + (Math.random() - 0.5) * 150);
    }
  }""",
"""  // 慢放：喷射持续 1.4 秒慢慢涌出，而不是一帧炸完。
  // 奶蛙已调头朝右，烟往奶蛋方向飞（dir = +1）。
  if (megaFartTimer > 0) {
    megaFartTimer -= dt;
    const mx = width * 0.32 + 64;
    const my = height * 0.72 - 58;
    for (let i = 0; i < 3; i++) {
      spawnGreenFart(mx + (Math.random() - 0.5) * 150,
                     my + (Math.random() - 0.5) * 150, 1);
    }
  }"""))

R.append((
"""  const px = width * 0.32 - 72;   // 往左下偏，别把玩家本体糊住
  const py = height * 0.72 - 58;
  for (let i = 0; i < 18; i++) {
    spawnGreenFart(px + (Math.random() - 0.5) * 190,
                   py + (Math.random() - 0.5) * 150);
  }""",
"""  const px = width * 0.32 + 64;   // 朝右偏，对着奶蛋喷
  const py = height * 0.72 - 58;
  for (let i = 0; i < 18; i++) {
    spawnGreenFart(px + (Math.random() - 0.5) * 150,
                   py + (Math.random() - 0.5) * 150, 1);
  }"""))

# ---------- 7. 旁观奶蛙档位逻辑 ----------
R.append((
"""  // 6. Bystander reaction tier（按累计放屁量升档）
  let bt = 0;
  for (let i = 0; i < BYSTANDER_TIERS.length; i++) {
    if (score >= BYSTANDER_TIERS[i].ml) bt = i;
  }
  if (bt !== bystanderTier) {
    bystanderTier = bt;
    bystanderPop = 1.0;
  }
  if (bystanderPop > 0) bystanderPop = Math.max(0, bystanderPop - dt * 1.6);""",
"""  // 6. Bystander reaction tier（按「单次放屁量」升档，松手 1.5 秒后回到嫌弃）
  let bt = 0;
  for (let i = 0; i < BYSTANDER_TIERS.length; i++) {
    if (fartVolume >= BYSTANDER_TIERS[i].ml) bt = i;
  }
  if (isFarting) {
    bystanderHold = BYSTANDER_HOLD;
  } else if (bystanderHold > 0) {
    bystanderHold -= dt;
  } else {
    bt = 0;                       // 收工，回到嫌弃
    fartVolume = 0;
  }
  if (bt !== bystanderTier) {
    bystanderTier = bt;
    bystanderPop = 1.0;
  }
  if (bystanderPop > 0) bystanderPop = Math.max(0, bystanderPop - dt * 1.6);"""))

# ---------- 8. ❓❗ 再放大三档 ----------
R.append((
"""  const GLYPH_HALF = 26;
  const SCOREBOARD_SAFE_Y = 96;   // 得分板下沿 + 余量（canvas 坐标）""",
"""  const GLYPH_HALF = 38;
  const SCOREBOARD_SAFE_Y = 108;  // 得分板下沿 + 余量（canvas 坐标）"""))

R.append((
"""    ctx.font = "44px 'Apple Color Emoji','Segoe UI Emoji','Noto Color Emoji',sans-serif";""",
"""    ctx.font = "66px 'Apple Color Emoji','Segoe UI Emoji','Noto Color Emoji',sans-serif";"""))

# ---------- 9. 场景：木地板取代水面 ----------
R.append((
"""  const pondY = height * 0.72;

  // Water Surface
  ctx.fillStyle = "#38bdf8";
  ctx.fillRect(0, pondY, width, height - pondY);

  // Water Ripples
  ctx.fillStyle = "rgba(255, 255, 255, 0.28)";
  for (let i = 0; i < 4; i++) {
    const wy = pondY + 16 + i * 28;
    ctx.fillRect(20 + (i * 35) % 80, wy, width - 60, 3);
  }""",
"""  // 沿用这条线作为「地面线」，角色的定位代码全部不用动
  const pondY = height * 0.72;

  // 木地板
  const floorGrad = ctx.createLinearGradient(0, pondY, 0, height);
  floorGrad.addColorStop(0, "#d9b98e");
  floorGrad.addColorStop(1, "#b58c60");
  ctx.fillStyle = floorGrad;
  ctx.fillRect(0, pondY, width, height - pondY);

  // 横向板缝
  ctx.strokeStyle = "rgba(112, 80, 48, 0.30)";
  ctx.lineWidth = 2;
  for (let i = 1; i <= 3; i++) {
    const ly = pondY + (height - pondY) * (i / 4);
    ctx.beginPath();
    ctx.moveTo(0, ly);
    ctx.lineTo(width, ly);
    ctx.stroke();
  }
  // 纵向板缝（近大远小，做出一点纵深）
  ctx.strokeStyle = "rgba(112, 80, 48, 0.16)";
  for (let i = 0; i <= 5; i++) {
    const lx = (i / 5) * width;
    ctx.beginPath();
    ctx.moveTo(lx, pondY);
    ctx.lineTo(lx + (lx - width / 2) * 0.26, height);
    ctx.stroke();
  }
  // 踢脚线
  ctx.fillStyle = "rgba(255, 255, 255, 0.55)";
  ctx.fillRect(0, pondY, width, 5);"""))

# ---------- 10. 两张椅子取代荷叶 ----------
R.append((
"""  // Giant Lotus Leaves
  // Player Leaf
  ctx.fillStyle = "#22c55e";
  ctx.beginPath();
  ctx.ellipse(width * 0.33, pondY + 16, width * 0.27, 34, 0, 0, Math.PI * 2);
  ctx.fill();
  ctx.strokeStyle = "#15803d";
  ctx.lineWidth = 3.5;
  ctx.stroke();

  // NPC Leaf
  ctx.fillStyle = "#16a34a";
  ctx.beginPath();
  ctx.ellipse(width * 0.76, pondY + 18, width * 0.24, 30, 0, 0, Math.PI * 2);
  ctx.fill();
  ctx.strokeStyle = "#166534";
  ctx.lineWidth = 3.5;
  ctx.stroke();""",
"""  // 两把椅子（摆在两个角色之间的空档里，不被挡住）
  drawChair(width * 0.105, pondY + 30, 0.95, "#4f7c8a", "#3a5d68");
  drawChair(width * 0.525, pondY + 30, 0.95, "#b4694c", "#8c4e37");"""))

# ---------- 11. CSS 背景换成室内墙面 ----------
R.append((
"""      background: linear-gradient(180deg, #e0f2fe 0%, #bae6fd 60%, #7dd3fc 100%);""",
"""      background: linear-gradient(180deg, #fbf3e6 0%, #f2e5d1 55%, #e8d7be 100%);"""))

# ---------- 12. 重开重置 ----------
R.append((
"""  bystanderTier = 0;
  bystanderPop = 0;""",
"""  bystanderTier = 0;
  bystanderPop = 0;
  bystanderHold = 0;
  fartVolume = 0;"""))

for i, (old, new) in enumerate(R, 1):
    n = s.count(old)
    if n != 1:
        print(f"[FAIL] 改动 #{i} 命中 {n} 次（应为 1）")
        sys.exit(1)
    s = s.replace(old, new)
    print(f"[ok] 改动 #{i}")

# ---------- 13. 插入椅子绘制helper ----------
helpers = """/* 圆角矩形路径（老浏览器没有 ctx.roundRect 时手动兜底） */
function roundRectPath(x, y, w, h, r) {
  ctx.beginPath();
  if (ctx.roundRect) { ctx.roundRect(x, y, w, h, r); return; }
  ctx.moveTo(x + r, y);
  ctx.arcTo(x + w, y, x + w, y + h, r);
  ctx.arcTo(x + w, y + h, x, y + h, r);
  ctx.arcTo(x, y + h, x, y, r);
  ctx.arcTo(x, y, x + w, y, r);
  ctx.closePath();
}

/* 背景里的一把椅子：靠背贴墙、四条腿落在地面线上 */
function drawChair(cx, baseY, scale, seatColor, frameColor) {
  const w = 64 * scale;
  const legH = 42 * scale;
  const seatH = 9 * scale;
  const seatY = baseY - legH;
  const backTop = seatY - 50 * scale;
  const legW = 6.5 * scale;

  ctx.save();
  // 落地软影
  ctx.fillStyle = "rgba(70, 48, 28, 0.16)";
  ctx.beginPath();
  ctx.ellipse(cx, baseY + 2, w * 0.62, 7 * scale, 0, 0, Math.PI * 2);
  ctx.fill();

  // 后腿（略短，撑出纵深）
  ctx.fillStyle = frameColor;
  ctx.fillRect(cx - w * 0.34, seatY + seatH, legW * 0.85, legH * 0.66);
  ctx.fillRect(cx + w * 0.34 - legW * 0.85, seatY + seatH, legW * 0.85, legH * 0.66);

  // 靠背
  roundRectPath(cx - w / 2, backTop, w, seatY - backTop + 6 * scale, 9 * scale);
  ctx.fill();

  // 靠背内衬一道浅色，避免整块死板
  ctx.fillStyle = seatColor;
  roundRectPath(cx - w / 2 + 9 * scale, backTop + 11 * scale,
                w - 18 * scale, (seatY - backTop) - 24 * scale, 6 * scale);
  ctx.fill();

  // 前腿
  ctx.fillStyle = frameColor;
  ctx.fillRect(cx - w * 0.42, seatY + seatH - 2 * scale, legW, legH + 2 * scale);
  ctx.fillRect(cx + w * 0.42 - legW, seatY + seatH - 2 * scale, legW, legH + 2 * scale);

  // 座面
  ctx.fillStyle = seatColor;
  roundRectPath(cx - w / 2 - 2 * scale, seatY, w + 4 * scale, seatH + 5 * scale, 5 * scale);
  ctx.fill();
  ctx.restore();
}

function render() {"""

if s.count("function render() {") != 1:
    print("[FAIL] render 锚点不唯一")
    sys.exit(1)
s = s.replace("function render() {", helpers, 1)
print("[ok] 改动 #13 插入椅子绘制 helper")

with io.open(HTML, "w", encoding="utf-8") as f:
    f.write(s)
print("写入完成 %.0f KB" % (len(s.encode("utf-8")) / 1024))
