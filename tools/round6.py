#!/usr/bin/env python3
"""第六轮改动：

  1. 顶部标题「奶蛙偷偷放屁」与静音键整行去掉（状态栏、排气量随之上移）
  2. 背景换纯白空白；去掉起风时的白色风线
  3. 起风频率调慢、间隔拉长
  4. 旁观奶蛙四句台词改为「累积上飘」，不再只闪一次
  5. 超级大屁横幅退场改为「放大 + 变淡」
  6. 底部加「换衣」按钮，切换大花袄形态（内嵌新素材）
"""
import base64
import io
import os
import re
import sys

from PIL import Image

HTML = "/Users/mac/Documents/dsh/naiwa-fart/奶蛙偷偷放屁.html"
ASSETS = "/Users/mac/Documents/dsh/naiwa-fart/assets"

# ---------- 0. 导出大花袄素材并转 base64 ----------
src = Image.open(f"{ASSETS}/src/player_idle_costume.png").convert("RGBA")
H = 360
w = round(src.width * H / src.height)
costume = src.resize((w, H), Image.LANCZOS)
costume_path = f"{ASSETS}/player_idle_costume.webp"
costume.save(costume_path, "WEBP", quality=88, method=4)
with open(costume_path, "rb") as f:
    COSTUME_URI = "data:image/webp;base64," + base64.b64encode(f.read()).decode("ascii")
print(f"[ok] 大花袄素材 {w}x{H}  {os.path.getsize(costume_path)/1024:.1f}KB")

with io.open(HTML, encoding="utf-8") as f:
    s = f.read()

R = []

# ---------- 1. 去掉标题行 + 静音键 ----------
R.append((
"""  <div class="hud-header">
    <div class="hud-top-row">
      <div class="hud-title">
        <span>奶蛙偷偷放屁</span>
      </div>
      <button class="sound-toggle-btn" id="sound-btn">🔊 音效开</button>
    </div>

    <!-- Enlarged Soundwave Visualizer (放大，其他都不要) -->""",
"""  <div class="hud-header">
    <!-- Enlarged Soundwave Visualizer (放大，其他都不要) -->"""))

R.append((
"""const soundBtn = document.getElementById('sound-btn');
""", ""))

R.append((
"""soundBtn.addEventListener('click', () => {
  sounds.init();
  const on = sounds.toggle();
  soundBtn.textContent = on ? "🔊 音效开" : "🔇 静音中";
  soundBtn.style.color = on ? "#0f172a" : "#ef4444";
});
""", ""))

# ---------- 2. 背景纯白 ----------
R.append((
"""      background: linear-gradient(180deg, #e0f2fe 0%, #bae6fd 60%, #7dd3fc 100%);""",
"""      background: #ffffff;"""))

# 地平线在纯白底上改成极淡的灰，只用来「托住」角色
R.append((
"""  ctx.strokeStyle = "rgba(125, 170, 205, 0.55)";
  ctx.lineWidth = 2.5;
  ctx.beginPath();
  ctx.moveTo(0, pondY);
  ctx.lineTo(width, pondY);
  ctx.stroke();""",
"""  ctx.strokeStyle = "rgba(15, 23, 42, 0.10)";
  ctx.lineWidth = 2;
  ctx.beginPath();
  ctx.moveTo(0, pondY);
  ctx.lineTo(width, pondY);
  ctx.stroke();"""))

# ---------- 3. 排气量上移 ----------
R.append((
"""    .scoreboard-container {
      position: absolute;
      top: 14px;""",
"""    .scoreboard-container {
      position: absolute;
      top: 6px;"""))

# ---------- 4. 去掉风线 ----------
R.append((
"""  // 起风了：横扫的风线 —— 提示这段时间奶蛋什么都听不到，可以随便放
  if (isCoverActive) {
    ctx.save();
    ctx.strokeStyle = "rgba(255, 255, 255, 0.62)";
    ctx.lineWidth = 2.5;
    ctx.lineCap = "round";
    const t = Date.now() * 0.32;
    for (let i = 0; i < 6; i++) {
      const yy = ((i * 73 + t * 0.5) % (height * 0.95));
      const xx = ((t * 1.6 + i * 211) % (width + 200)) - 200;
      ctx.beginPath();
      ctx.moveTo(xx, yy);
      ctx.lineTo(xx + 86, yy + 13);
      ctx.stroke();
    }
    ctx.restore();
  }

""", ""))

# ---------- 5. 起风频率调慢 ----------
R.append((
"""      nextCoverEventTimer = 2.2 + Math.random() * 3.0;""",
"""      nextCoverEventTimer = 7.0 + Math.random() * 6.0;   // 起风间隔拉长"""))

R.append((
"""      coverEventTimer = 2.8 + Math.random() * 1.8;""",
"""      coverEventTimer = 2.4 + Math.random() * 1.6;       // 单次起风时长略短"""))

R.append((
"""let nextCoverEventTimer = 2.5;""",
"""let nextCoverEventTimer = 7.0;"""))

R.append((
"""  nextCoverEventTimer = 2.0;""",
"""  nextCoverEventTimer = 7.0;"""))

# ---------- 6. 旁观奶蛙四句台词：累积上飘 ----------
R.append((
"""const BYSTANDER_RAGE_ML = 800;   // 单次放屁量破 800：惊吓升级成狂暴
const BYSTANDER_HOLD = 1.5;      // 松手后维持表情的秒数，再回到「嫌弃」""",
"""const BYSTANDER_RAGE_ML = 800;   // 单次放屁量破 800：惊吓升级成狂暴
const BYSTANDER_HOLD = 1.5;      // 松手后维持表情的秒数，再回到「嫌弃」
/* 四档对应的吐槽台词：换档时冒一句，同档位每隔一段时间再补一句，
   全部累积着往上飘，不是只闪一次 */
const BYSTANDER_LINES = {
  disgust: '太少了',
  approve: '屁真多',
  envy: '你放屁好厉害啊',
  shock: '根本没有这样的屁',
};
const BYSTANDER_LINE_INTERVAL = 1.5;   // 同档位补字的间隔（秒）
let bystanderTexts = [];
let bystanderLineTimer = 0;"""))

R.append((
"""let npcReactTimer = 0;
let npcStunTimer = 0;""",
"""let npcReactTimer = 0;
let npcStunTimer = 0;
let costumeOn = false;      // 是否穿着大花袄"""))

# 换档时冒字 + 同档位补字
R.append((
"""  if (bt !== bystanderTier) {
    bystanderTier = bt;
    bystanderPop = 1.0;
  }
  if (bystanderPop > 0) bystanderPop = Math.max(0, bystanderPop - dt * 1.6);""",
"""  if (bt !== bystanderTier) {
    bystanderTier = bt;
    bystanderPop = 1.0;
    pushBystanderLine(BYSTANDER_TIERS[bt].key);
    bystanderLineTimer = BYSTANDER_LINE_INTERVAL;
  }
  if (bystanderPop > 0) bystanderPop = Math.max(0, bystanderPop - dt * 1.6);

  // 同档位持续补字，让吐槽一条条累积着飘上去
  if (isFarting && bystanderHold > 0) {
    bystanderLineTimer -= dt;
    if (bystanderLineTimer <= 0) {
      bystanderLineTimer = BYSTANDER_LINE_INTERVAL;
      pushBystanderLine(BYSTANDER_TIERS[bystanderTier].key);
    }
  }"""))

# 飘字推进（放在 isPlaying 早退之前，结算后也让它飘完）
R.append((
"""  // 纯视觉计时器即使结算了也要继续走完，否则震动和横幅会卡住
  if (megaBanner > 0) megaBanner = Math.max(0, megaBanner - dt);
  if (shakeTime > 0) shakeTime = Math.max(0, shakeTime - dt);""",
"""  // 纯视觉计时器即使结算了也要继续走完，否则震动和横幅会卡住
  if (megaBanner > 0) megaBanner = Math.max(0, megaBanner - dt);
  if (shakeTime > 0) shakeTime = Math.max(0, shakeTime - dt);
  for (let i = bystanderTexts.length - 1; i >= 0; i--) {
    const bt2 = bystanderTexts[i];
    bt2.life -= dt * 0.48;
    bt2.y -= bt2.vy * dt;
    if (bt2.life <= 0) bystanderTexts.splice(i, 1);
  }"""))

# 生成飘字的函数
R.append((
"""/* 超级大屁：里程奖励 —— 泄洪降压、慢放喷射、把奶蛋震晕 3 秒 */""",
"""/* 旁观奶蛙冒一句吐槽，累积着往上飘 */
function pushBystanderLine(key) {
  const text = BYSTANDER_LINES[key];
  if (!text) return;
  bystanderTexts.push({
    text: text,
    x: width * 0.47 + (Math.random() - 0.5) * 46,
    y: height * 0.70,
    life: 1.0,
    vy: 30 + Math.random() * 20,
  });
  if (bystanderTexts.length > 16) bystanderTexts.shift();
}

/* 超级大屁：里程奖励 —— 泄洪降压、慢放喷射、把奶蛋震晕 3 秒 */"""))

# ---------- 7. 渲染：飘字取代原来的单个标签 ----------
R.append((
"""      // 换档瞬间冒一个反应标签（约 1 秒后淡出）
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
""", ""))

R.append((
"""  // 5. 超级大屁横幅
  if (megaBanner > 0) {
    ctx.save();
    ctx.globalAlpha = Math.min(1, megaBanner / 0.45);
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    ctx.font = "900 34px 'PingFang SC','Microsoft YaHei',sans-serif";
    ctx.lineWidth = 7;
    ctx.strokeStyle = "rgba(15, 23, 42, 0.9)";
    ctx.strokeText("💨 超级大屁！", width * 0.5, height * 0.28);
    ctx.fillStyle = "#86efac";
    ctx.fillText("💨 超级大屁！", width * 0.5, height * 0.28);
    ctx.restore();
  }""",
"""  // 5. 旁观奶蛙的累积吐槽（一条条往上飘）
  for (const bt2 of bystanderTexts) {
    ctx.save();
    ctx.globalAlpha = Math.max(0, Math.min(1, bt2.life * 1.7));
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    ctx.font = "900 19px 'PingFang SC','Microsoft YaHei',sans-serif";
    ctx.lineWidth = 5.5;
    ctx.strokeStyle = "rgba(255, 255, 255, 0.95)";
    ctx.strokeText(bt2.text, bt2.x, bt2.y);
    ctx.fillStyle = "#0f172a";
    ctx.fillText(bt2.text, bt2.x, bt2.y);
    ctx.restore();
  }

  // 6. 超级大屁横幅：先正常显示，退场时一边放大一边变淡
  if (megaBanner > 0) {
    const FADE = 1.0;                                   // 退场时长
    const k = megaBanner > FADE ? 1 : Math.max(0, megaBanner / FADE);
    ctx.save();
    ctx.globalAlpha = k;
    ctx.translate(width * 0.5, height * 0.28);
    ctx.scale(1 + (1 - k) * 0.9, 1 + (1 - k) * 0.9);    // 放大到 1.9 倍
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    ctx.font = "900 34px 'PingFang SC','Microsoft YaHei',sans-serif";
    ctx.lineWidth = 7;
    ctx.strokeStyle = "rgba(15, 23, 42, 0.9)";
    ctx.strokeText("💨 超级大屁！", 0, 0);
    ctx.fillStyle = "#86efac";
    ctx.fillText("💨 超级大屁！", 0, 0);
    ctx.restore();
  }"""))

# ---------- 8. 换衣：内嵌素材 ----------
R.append((
"""/* 监视者「奶蛋」三视图：随怀疑度 背对 → 侧身 → 正面死盯 */""",
f"""/* 玩家「大花袄」形态（换衣按钮切换） */
const spriteIdleCostume = new Image();
spriteIdleCostume.src = "{COSTUME_URI}";

/* 监视者「奶蛋」三视图：随怀疑度 背对 → 侧身 → 正面死盯 */"""))

R.append((
"""trySpriteOverride(spriteIdle, "player-idle.png");""",
"""trySpriteOverride(spriteIdle, "player-idle.png");
trySpriteOverride(spriteIdleCostume, "player-idle-costume.png");"""))

# 渲染时按开关选形态
R.append((
"""    // 胀气越高整体等比撑大（不再横向拉伸，避免把新素材拉变形）
    const gasScale = 1.0 + (gasLevel / 100) * 0.07;
    drawChar(spriteIdle, playerX, playerY, 248 * gasScale, 0.5, tremX, 0);""",
"""    // 胀气越高整体等比撑大（不再横向拉伸，避免把新素材拉变形）
    const gasScale = 1.0 + (gasLevel / 100) * 0.07;
    const idleImg = (costumeOn && spriteIdleCostume.complete && spriteIdleCostume.naturalWidth)
      ? spriteIdleCostume : spriteIdle;
    drawChar(idleImg, playerX, playerY, 248 * gasScale, 0.5, tremX, 0);"""))

# ---------- 9. 换衣按钮 ----------
R.append((
"""    <div class="controls-hint">按住屏幕或空格键排气 • 松手立刻憋住伪装</div>""",
"""    <button class="btn-skin" id="skin-btn">👗 换衣：换大花袄</button>
    <div class="controls-hint">按住屏幕或空格键排气 • 松手立刻憋住伪装</div>"""))

R.append((
"""    .btn-restart {""",
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
    }
    .btn-restart {"""))

R.append((
"""const restartBtn = document.getElementById('restart-btn');""",
"""const restartBtn = document.getElementById('restart-btn');
const skinBtn = document.getElementById('skin-btn');"""))

R.append((
"""restartBtn.addEventListener('click', () => {""",
"""skinBtn.addEventListener('click', () => {
  sounds.init();                       // 借这次点击解锁音频上下文
  costumeOn = !costumeOn;
  skinBtn.classList.toggle('on', costumeOn);
  skinBtn.textContent = costumeOn ? "👗 换衣：换回原样" : "👗 换衣：换大花袄";
});

restartBtn.addEventListener('click', () => {"""))

for i, (old, new) in enumerate(R, 1):
    if old == new:
        print(f"[skip] #{i} 占位")
        continue
    n = s.count(old)
    if n != 1:
        print(f"[FAIL] 改动 #{i} 命中 {n} 次（应为 1）")
        sys.exit(1)
    s = s.replace(old, new)
    print(f"[ok] 改动 #{i}")

# soundBtn 的监听已删，这里把残留的 skin 监听顺序修正：skinBtn 块里引用了已删除的 soundBtn 行
if "soundBtn" in s:
    print("[FAIL] soundBtn 仍有残留")
    sys.exit(1)
print("[ok] soundBtn 已彻底移除")

with io.open(HTML, "w", encoding="utf-8") as f:
    f.write(s)
print("写入完成 %.0f KB" % (len(s.encode("utf-8")) / 1024))
