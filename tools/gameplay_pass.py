#!/usr/bin/env python3
"""一批玩法 / 表现改动：

  1. 奶蛋头顶 ❓❗ 放大 + 居中（白底圆牌 + 上下浮动）
  2. 抓现行「扫描框」（视锥）整体上移，并上下扫动
  3. 排气量实时平滑累加（浮点累加，显示取整），一放屁就计量
  4. 奶蛋变迟钝：巡逻间隔拉长、进入抓现行后先愣一下才认得出
  5. 超级大屁：每累计 500ml 自动爆一发（泄洪 + 震动 + 横幅）
  6. 屁烟粒子直接生在精灵图自带的尾气范围内，两团烟合成一团
  7. 起风视觉提示 + 憋不住爆炸演出 + 结算改「放屁量」
"""
import io
import sys

HTML = "/Users/mac/Documents/dsh/naiwa-fart/奶蛙偷偷放屁.html"

with io.open(HTML, encoding="utf-8") as f:
    s = f.read()

R = []

# ---------- 1. 新增状态 ----------
R.append((
"""let greenFartParticles = [];
let sweatDrops = [];""",
"""let greenFartParticles = [];
let sweatDrops = [];

/* 超级大屁：每累计 MEGA_FART_STEP 毫升排气量自动爆一发 */
const MEGA_FART_STEP = 500;
let nextMegaFartAt = MEGA_FART_STEP;
let megaBanner = 0;          // 横幅计时
let shakeTime = 0;           // 屏幕震动计时
let shakePower = 0;
/* 奶蛋「迟钝」：进入抓现行后要先愣这么久才认得出，给玩家松手的窗口 */
const NPC_REACT_DELAY = 0.95;
let npcReactTimer = 0;"""))

# ---------- 2. 视觉计时器在游戏结束后仍要走（爆炸震动/横幅） ----------
R.append((
"""function update(dt) {
  if (!isPlaying) return;

  elapsedSeconds += dt;""",
"""function update(dt) {
  // 纯视觉计时器即使结算了也要继续走完，否则震动和横幅会卡住
  if (megaBanner > 0) megaBanner = Math.max(0, megaBanner - dt);
  if (shakeTime > 0) shakeTime = Math.max(0, shakeTime - dt);

  if (!isPlaying) return;

  elapsedSeconds += dt;"""))

# ---------- 3. 计分：一放屁就计量 + 浮点平滑累加 ----------
R.append((
"""    // Score calculation
    if (isCoverActive) {
      // Safe cover: +100 score/sec, +combo
      score += Math.round(120 * dt);
      suspicion = Math.max(0, suspicion - 16 * dt);
    } else {
      // Danger quiet: +20 score/sec, rapid suspicion gain
      score += Math.round(20 * dt);
      suspicion += 62 * dt;
      if (npcState === NPC_STATES.IDLE && suspicion > 20) {
        npcState = NPC_STATES.SUSPICIOUS;
        npcStateTimer = 0.8;
        sounds.playWarning();
      }
    }""",
"""    // 「只要一放屁就计量」：基础 70ml/s，按下即开始涨，起风掩护期再乘 1.8。
    // 用浮点累加、显示时才取整，避免高刷屏下某些帧四舍五入成 0 而看着卡住不动。
    score += 70 * dt * (isCoverActive ? 1.8 : 1);

    if (isCoverActive) {
      // 起风了：奶蛋什么都听不到，随便放，怀疑度还会回落
      suspicion = Math.max(0, suspicion - 16 * dt);
    } else {
      // 安静期：怀疑度上升（奶蛋迟钝，涨得比原来慢）
      suspicion += 48 * dt;
      if (npcState === NPC_STATES.IDLE && suspicion > 20) {
        npcState = NPC_STATES.SUSPICIOUS;
        npcStateTimer = 1.3;
        sounds.playWarning();
      }
    }"""))

# ---------- 4. 奶蛋变迟钝 ----------
R.append((
"""  // 4. NPC AI
  if (npcState === NPC_STATES.IDLE) {
    nextNpcCheckTimer -= dt;
    if (nextNpcCheckTimer <= 0) {
      npcState = NPC_STATES.SUSPICIOUS;
      npcStateTimer = 0.9 + Math.random() * 0.5;
      sounds.playWarning();
    }
  } else if (npcState === NPC_STATES.SUSPICIOUS) {
    npcStateTimer -= dt;
    if (npcStateTimer <= 0) {
      npcState = NPC_STATES.WATCHING;
      npcStateTimer = 1.3 + Math.random() * 0.7;
    }
  } else if (npcState === NPC_STATES.WATCHING) {
    if (isFarting) {
      gameOver('caught');
      return;
    }
    npcStateTimer -= dt;
    if (npcStateTimer <= 0) {
      npcState = NPC_STATES.IDLE;
      nextNpcCheckTimer = 3.5 + Math.random() * 3.5;
    }
  }""",
"""  // 4. 奶蛋 AI（迟钝版：巡逻间隔更长、转身更慢、认出来之前还要愣一下）
  if (npcState === NPC_STATES.IDLE) {
    nextNpcCheckTimer -= dt;
    if (nextNpcCheckTimer <= 0) {
      npcState = NPC_STATES.SUSPICIOUS;
      npcStateTimer = 1.3 + Math.random() * 0.8;
      sounds.playWarning();
    }
  } else if (npcState === NPC_STATES.SUSPICIOUS) {
    npcStateTimer -= dt;
    if (npcStateTimer <= 0) {
      npcState = NPC_STATES.WATCHING;
      npcStateTimer = 1.6 + Math.random() * 0.9;
      npcReactTimer = NPC_REACT_DELAY;
    }
  } else if (npcState === NPC_STATES.WATCHING) {
    if (npcReactTimer > 0) npcReactTimer -= dt;
    if (isFarting && npcReactTimer <= 0) {
      gameOver('caught');
      return;
    }
    npcStateTimer -= dt;
    if (npcStateTimer <= 0) {
      npcState = NPC_STATES.IDLE;
      nextNpcCheckTimer = 5.0 + Math.random() * 4.5;
    }
  }"""))

# ---------- 5. 超级大屁触发 ----------
R.append((
"""  // 6. Bystander reaction tier（按累计放屁量升档）""",
"""  // 5.5 超级大屁：每累计 MEGA_FART_STEP 毫升自动爆一发
  if (score >= nextMegaFartAt) {
    nextMegaFartAt += MEGA_FART_STEP;
    triggerMegaFart();
  }

  // 6. Bystander reaction tier（按累计放屁量升档）"""))

# ---------- 6. 超级大屁函数 ----------
R.append((
"""function updateAndDrawParticles() {""",
"""/* 超级大屁：里程奖励 —— 大量排气、瞬间泄洪降压、屏幕震动 */
function triggerMegaFart() {
  megaBanner = 1.7;
  shakeTime = 0.55;
  shakePower = 14;
  gasLevel = Math.max(0, gasLevel - 22);   // 泄洪：一口气顶掉两成多胀气
  const px = width * 0.32;
  const py = height * 0.72 - 70;
  for (let i = 0; i < 48; i++) {
    spawnGreenFart(px + (Math.random() - 0.5) * 230,
                   py + (Math.random() - 0.5) * 170);
  }
  sounds.playThunder();
  sounds.playFart(58, 0.5);
}

function updateAndDrawParticles() {"""))

# ---------- 7. render 起手：屏幕震动 ----------
R.append((
"""function render() {
  ctx.clearRect(0, 0, width, height);

  const pondY = height * 0.72;""",
"""function render() {
  ctx.clearRect(0, 0, width, height);

  // 屏幕震动（超级大屁 / 爆炸社死）
  ctx.save();
  if (shakeTime > 0) {
    const k = Math.min(1, shakeTime / 0.55);
    ctx.translate((Math.random() - 0.5) * shakePower * k,
                  (Math.random() - 0.5) * shakePower * k);
  }

  const pondY = height * 0.72;"""))

# ---------- 8. 起风视觉 ----------
R.append((
"""  // Water Ripples
  ctx.fillStyle = "rgba(255, 255, 255, 0.28)";
  for (let i = 0; i < 4; i++) {
    const wy = pondY + 16 + i * 28;
    ctx.fillRect(20 + (i * 35) % 80, wy, width - 60, 3);
  }""",
"""  // Water Ripples
  ctx.fillStyle = "rgba(255, 255, 255, 0.28)";
  for (let i = 0; i < 4; i++) {
    const wy = pondY + 16 + i * 28;
    ctx.fillRect(20 + (i * 35) % 80, wy, width - 60, 3);
  }

  // 起风了：横扫的风线 —— 提示这段时间奶蛋什么都听不到，可以随便放
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
  }"""))

# ---------- 9. 视锥：上移 + 上下扫描 ----------
R.append((
"""  // NPC Watching Vision Cone
  if (npcState === NPC_STATES.WATCHING) {
    ctx.save();
    ctx.fillStyle = "rgba(239, 68, 68, 0.18)";
    ctx.beginPath();
    ctx.moveTo(width * 0.74, pondY - 70);
    ctx.lineTo(width * 0.35 + 40, pondY - 140);
    ctx.lineTo(width * 0.35 + 40, pondY + 30);
    ctx.closePath();
    ctx.fill();
    ctx.restore();
  }""",
"""  // 奶蛋抓现行的「扫描框」：整体上移，并像探照灯那样上下扫动
  if (npcState === NPC_STATES.WATCHING) {
    const sweep = Math.sin(Date.now() * 0.0024) * 48;
    ctx.save();
    ctx.fillStyle = "rgba(239, 68, 68, 0.20)";
    ctx.beginPath();
    ctx.moveTo(width * 0.74, pondY - 120 + sweep * 0.28);
    ctx.lineTo(width * 0.33, pondY - 200 + sweep);
    ctx.lineTo(width * 0.33, pondY - 12 + sweep);
    ctx.closePath();
    ctx.fill();
    ctx.restore();
  }"""))

# ---------- 10. 屁烟与图片尾气合并 ----------
R.append((
"""    const box = drawChar(spriteFart, playerX, playerY, 238, 0.58, wx, wy);
    if (box) {
      // 排气口落在精灵图左下侧（臀部位置）
      const nozzleWorldX = box.x + box.w * 0.24 + wx;
      const nozzleWorldY = box.y + box.h * 0.58 + wy;
      if (Math.random() < 0.95) spawnGreenFart(nozzleWorldX, nozzleWorldY);
    }""",
"""    const box = drawChar(spriteFart, playerX, playerY, 238, 0.58, wx, wy);
    if (box) {
      // 粒子直接生在「精灵图里已经画好的那团尾气」范围上，新烟与自带的尾气
      // 叠成一团持续翻滚的浓烟，而不是在屁股边上另起一坨分家的云。
      const sx = 0.03 + Math.random() * 0.27;   // 尾气横向范围
      const sy = 0.48 + Math.random() * 0.28;   // 尾气纵向范围
      const px = box.x + box.w * sx + wx;
      const py = box.y + box.h * sy + wy;
      spawnGreenFart(px, py);
      spawnGreenFart(px, py);
    }"""))

# ---------- 11. ❓❗ 放大居中 ----------
R.append((
"""  // 头顶提示符号（跟随奶蛋实际头顶位置）
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
  }""",
"""  // 头顶提示符号：加大 + 水平居中于奶蛋头顶，配白底圆牌保证浅色天空上也看得清
  const npcTop = npcBox ? npcBox.y : npcY - 232;
  if (npcState === NPC_STATES.SUSPICIOUS || npcState === NPC_STATES.WATCHING) {
    const isCatch = npcState === NPC_STATES.WATCHING;
    const bob = Math.sin(Date.now() * 0.006) * 5;
    const badgeY = npcTop - 34 + bob;
    ctx.save();
    ctx.beginPath();
    ctx.arc(npcX, badgeY, 31, 0, Math.PI * 2);
    ctx.fillStyle = "rgba(255, 255, 255, 0.94)";
    ctx.fill();
    ctx.lineWidth = 4.5;
    ctx.strokeStyle = isCatch ? "#ef4444" : "#eab308";
    ctx.stroke();
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    ctx.font = "42px 'Apple Color Emoji','Segoe UI Emoji','Noto Color Emoji',sans-serif";
    ctx.fillText(isCatch ? "❗" : "❓", npcX, badgeY + 3);
    ctx.restore();
  }"""))

# ---------- 12. render 收尾：超级大屁横幅 + 恢复震动位移 ----------
R.append((
"""  // 4. Green Fart Smoke and Sweat
  updateAndDrawParticles();
}""",
"""  // 4. Green Fart Smoke and Sweat
  updateAndDrawParticles();

  // 5. 超级大屁横幅
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
  }

  ctx.restore();   // 结束屏幕震动位移
}"""))

# ---------- 13. 计分板实时取整 ----------
R.append((
"""  scoreVal.textContent = String(score).padStart(6, '0');""",
"""  scoreVal.textContent = String(Math.floor(score)).padStart(6, '0');"""))

# ---------- 14. 结算：爆炸演出 + 放屁量 ----------
R.append((
"""  statTime.textContent = `${Math.floor(elapsedSeconds)}s`;
  statScore.textContent = score.toLocaleString();

  if (reason === 'exploded') {
    sounds.playExplode();
    modalIcon.textContent = "💥";
    modalTitle.textContent = "惊天巨响！当场社死！";
    modalDesc.textContent = "肚子胀气达到 100%，终于没憋住炸出了轰天动地的巨响！";
  } else {
    sounds.playCaught();
    modalIcon.textContent = "👀";
    modalTitle.textContent = "被同伴抓个正着！";
    modalDesc.textContent = "你在安静时偷放被同伴猛回头抓现行！眼神对视的瞬间彻底石化！";
  }

  endModal.style.display = 'flex';""",
"""  statTime.textContent = `${Math.floor(elapsedSeconds)}s`;
  statScore.textContent = Math.floor(score).toLocaleString();

  if (reason === 'exploded') {
    sounds.playExplode();
    // 憋不住的终局：先把这一下炸给玩家看，再弹结算面板
    shakeTime = 0.9;
    shakePower = 24;
    const bx = width * 0.32;
    const by = height * 0.72 - 70;
    for (let i = 0; i < 90; i++) {
      spawnGreenFart(bx + (Math.random() - 0.5) * 240,
                     by + (Math.random() - 0.5) * 210);
    }
    modalIcon.textContent = "💥";
    modalTitle.textContent = "惊天巨响！当场社死！";
    modalDesc.textContent = "肚子胀气达到 100%，终于没憋住炸出了轰天动地的巨响！";
    setTimeout(() => { endModal.style.display = 'flex'; }, 850);
    return;
  }

  sounds.playCaught();
  modalIcon.textContent = "👀";
  modalTitle.textContent = "被同伴抓个正着！";
  modalDesc.textContent = "你在安静时偷放被同伴猛回头抓现行！眼神对视的瞬间彻底石化！";

  endModal.style.display = 'flex';"""))

# ---------- 15. 结算文案改「放屁量」 ----------
R.append((
"""        <div>总得分: <span id="stat-score" style="color:#10b981;">1,250</span></div>""",
"""        <div>放屁量: <span id="stat-score" style="color:#10b981;">1,250</span> ml</div>"""))

# ---------- 16. 重开时重置新状态 ----------
R.append((
"""  bystanderTier = 0;
  bystanderPop = 0;""",
"""  bystanderTier = 0;
  bystanderPop = 0;
  nextMegaFartAt = MEGA_FART_STEP;
  megaBanner = 0;
  shakeTime = 0;
  npcReactTimer = 0;"""))

for i, (old, new) in enumerate(R, 1):
    n = s.count(old)
    if n != 1:
        print(f"[FAIL] 改动 #{i} 命中 {n} 次（应为 1）")
        sys.exit(1)
    s = s.replace(old, new)
    print(f"[ok] 改动 #{i}")

with io.open(HTML, "w", encoding="utf-8") as f:
    f.write(s)
print("写入完成 %.0f KB" % (len(s.encode("utf-8")) / 1024))
