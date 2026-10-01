#!/usr/bin/env python3
"""第四轮改动：

  1. 超级大屁「慢放」：喷射从一帧炸完改为 1.4 秒持续涌出，横幅延长到 2.6 秒，
     并把奶蛋震晕 3 秒（晃悠 + 头顶转圈星星 + 怀疑度狂掉，期间抓不了你）
  2. 结算界面重做成奶蛙 / 奶蛋主题：两个角色立绘 + 大字突出「偷放屁时间 / 放屁量」
  3. ❓❗ 去掉白底圆牌直接显示，并夹住位置避免和顶部「排气量」得分板重叠
  4. 奶蛋灵敏度回收成可调配置，并整体调敏感（上一轮调太钝了）
"""
import io
import sys

HTML = "/Users/mac/Documents/dsh/naiwa-fart/奶蛙偷偷放屁.html"

with io.open(HTML, encoding="utf-8") as f:
    s = f.read()

R = []

# ---------- 1. 状态 + 灵敏度配置 ----------
R.append((
"""/* 超级大屁：每累计 MEGA_FART_STEP 毫升排气量自动爆一发 */
const MEGA_FART_STEP = 500;
let nextMegaFartAt = MEGA_FART_STEP;
let megaBanner = 0;          // 横幅计时
let shakeTime = 0;           // 屏幕震动计时
let shakePower = 0;
/* 奶蛋「迟钝」：进入抓现行后要先愣这么久才认得出，给玩家松手的窗口 */
const NPC_REACT_DELAY = 0.95;
let npcReactTimer = 0;""",
"""/* 超级大屁：每累计 MEGA_FART_STEP 毫升排气量自动爆一发 */
const MEGA_FART_STEP = 500;
let nextMegaFartAt = MEGA_FART_STEP;
let megaBanner = 0;          // 横幅计时
let megaFartTimer = 0;       // 慢放：剩余喷射时长
let shakeTime = 0;           // 屏幕震动计时
let shakePower = 0;
let fartSeconds = 0;         // 累计偷放屁时间（结算展示用）

/* ---- 奶蛋灵敏度总开关：想整体调难度，改这里就行 ---- */
const NPC_STUN_TIME = 3.0;   // 被超级大屁震晕的秒数
const NPC_TUNING = {
  patrolMin: 3.2, patrolMax: 6.0,        // 发呆巡逻间隔
  idleToSusMin: 0.85, idleToSusMax: 1.40, // 发呆 → 起疑
  susToWatchMin: 1.10, susToWatchMax: 1.70, // 起疑 → 抓现行
  reactDelay: 0.45,                       // 转身后愣多久才认得出（松手窗口）
  suspicionRate: 62,                      // 安静期怀疑度增速
};
let npcReactTimer = 0;
let npcStunTimer = 0;"""))

# ---------- 2. NPC 状态机加「震晕」 ----------
R.append((
"""const NPC_STATES = {
  IDLE: 'idle',
  SUSPICIOUS: 'suspicious',""",
"""const NPC_STATES = {
  IDLE: 'idle',
  STUNNED: 'stunned',
  SUSPICIOUS: 'suspicious',"""))

# ---------- 3. 统计偷放屁时间 ----------
R.append((
"""  // 2. Farting & Score
  if (isFarting) {
    const vent = 24 * dt;""",
"""  // 2. Farting & Score
  if (isFarting) {
    fartSeconds += dt;                 // 累计偷放屁时间，结算用
    const vent = 24 * dt;"""))

# ---------- 4. 震晕期间听不到、怀疑度回落 ----------
R.append((
"""    if (isCoverActive) {
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
    }""",
"""    if (isCoverActive || npcStunTimer > 0) {
      // 起风了 / 奶蛋被震晕：它什么都听不到，随便放，怀疑度还会回落
      suspicion = Math.max(0, suspicion - 16 * dt);
    } else {
      // 安静期：怀疑度上升
      suspicion += NPC_TUNING.suspicionRate * dt;
      if (npcState === NPC_STATES.IDLE && suspicion > 20) {
        npcState = NPC_STATES.SUSPICIOUS;
        npcStateTimer = NPC_TUNING.idleToSusMin;
        sounds.playWarning();
      }
    }"""))

# ---------- 5. NPC AI：震晕分支 + 灵敏度走配置 ----------
R.append((
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
  }""",
"""  // 4. 奶蛋 AI（灵敏度见 NPC_TUNING；被超级大屁震晕时整段跳过）
  if (npcStunTimer > 0) {
    npcStunTimer -= dt;
    npcState = NPC_STATES.STUNNED;
    suspicion = Math.max(0, suspicion - 26 * dt);
    if (npcStunTimer <= 0) {
      npcState = NPC_STATES.IDLE;
      nextNpcCheckTimer = NPC_TUNING.patrolMin;
    }
  } else if (npcState === NPC_STATES.IDLE) {
    nextNpcCheckTimer -= dt;
    if (nextNpcCheckTimer <= 0) {
      npcState = NPC_STATES.SUSPICIOUS;
      npcStateTimer = NPC_TUNING.idleToSusMin
                    + Math.random() * (NPC_TUNING.idleToSusMax - NPC_TUNING.idleToSusMin);
      sounds.playWarning();
    }
  } else if (npcState === NPC_STATES.SUSPICIOUS) {
    npcStateTimer -= dt;
    if (npcStateTimer <= 0) {
      npcState = NPC_STATES.WATCHING;
      npcStateTimer = NPC_TUNING.susToWatchMin
                    + Math.random() * (NPC_TUNING.susToWatchMax - NPC_TUNING.susToWatchMin);
      npcReactTimer = NPC_TUNING.reactDelay;
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
      nextNpcCheckTimer = NPC_TUNING.patrolMin
                        + Math.random() * (NPC_TUNING.patrolMax - NPC_TUNING.patrolMin);
    }
  }"""))

# ---------- 6. 超级大屁：慢放喷射 ----------
R.append((
"""  // 5.5 超级大屁：每累计 MEGA_FART_STEP 毫升自动爆一发
  if (score >= nextMegaFartAt) {
    nextMegaFartAt += MEGA_FART_STEP;
    triggerMegaFart();
  }""",
"""  // 5.5 超级大屁：每累计 MEGA_FART_STEP 毫升自动爆一发
  if (score >= nextMegaFartAt) {
    nextMegaFartAt += MEGA_FART_STEP;
    triggerMegaFart();
  }
  // 慢放：喷射持续 1.4 秒慢慢涌出，而不是一帧炸完
  if (megaFartTimer > 0) {
    megaFartTimer -= dt;
    const mx = width * 0.32 - 72;
    const my = height * 0.72 - 58;
    for (let i = 0; i < 3; i++) {
      spawnGreenFart(mx + (Math.random() - 0.5) * 190,
                     my + (Math.random() - 0.5) * 150);
    }
  }"""))

# ---------- 7. triggerMegaFart：慢放 + 震晕奶蛋 ----------
R.append((
"""/* 超级大屁：里程奖励 —— 大量排气、瞬间泄洪降压、屏幕震动 */
function triggerMegaFart() {
  megaBanner = 1.7;
  shakeTime = 0.55;
  shakePower = 14;
  gasLevel = Math.max(0, gasLevel - 22);   // 泄洪：一口气顶掉两成多胀气
  const px = width * 0.32 - 72;   // 往左下偏，别把玩家本体糊住
  const py = height * 0.72 - 58;
  for (let i = 0; i < 40; i++) {
    spawnGreenFart(px + (Math.random() - 0.5) * 190,
                   py + (Math.random() - 0.5) * 150);
  }
  sounds.playThunder();
  sounds.playFart(58, 0.5);
}""",
"""/* 超级大屁：里程奖励 —— 泄洪降压、慢放喷射、把奶蛋震晕 3 秒 */
function triggerMegaFart() {
  megaBanner = 2.6;        // 横幅展示久一点
  megaFartTimer = 1.4;     // 1.4 秒持续涌出（慢放）
  shakeTime = 0.8;
  shakePower = 15;
  gasLevel = Math.max(0, gasLevel - 22);   // 泄洪：一口气顶掉两成多胀气
  npcStunTimer = NPC_STUN_TIME;            // 奶蛋当场被震晕
  npcState = NPC_STATES.STUNNED;
  const px = width * 0.32 - 72;   // 往左下偏，别把玩家本体糊住
  const py = height * 0.72 - 58;
  for (let i = 0; i < 18; i++) {
    spawnGreenFart(px + (Math.random() - 0.5) * 190,
                   py + (Math.random() - 0.5) * 150);
  }
  sounds.playThunder();
  sounds.playFart(58, 0.5);
}"""))

# ---------- 8. render：震晕晃悠 ----------
R.append((
"""  const npcImg = npcState === NPC_STATES.WATCHING ? eggSide      // 侧身：真盯着玩家
               : npcState === NPC_STATES.SUSPICIOUS ? eggFront   // 正面：猛地转向你
               : eggBack;                                        // 背对：压根没在看你
  const npcBox = drawChar(npcImg, npcX, npcY, 232, 0.5, 0, 0);""",
"""  const npcImg = npcState === NPC_STATES.WATCHING ? eggSide      // 侧身：真盯着玩家
               : npcState === NPC_STATES.SUSPICIOUS ? eggFront   // 正面：猛地转向你
               : eggBack;                                        // 背对：压根没在看你
  let npcBox;
  if (npcState === NPC_STATES.STUNNED) {
    // 被超级大屁震晕：原地晃悠
    ctx.save();
    ctx.translate(npcX, npcY);
    ctx.rotate(Math.sin(Date.now() * 0.017) * 0.14);
    ctx.translate(-npcX, -npcY);
    npcBox = drawChar(eggBack, npcX, npcY, 232, 0.5, 0, 0);
    ctx.restore();
  } else {
    npcBox = drawChar(npcImg, npcX, npcY, 232, 0.5, 0, 0);
  }"""))

# ---------- 9. ❓❗ 去边框 + 避开得分板 + 震晕星星 ----------
R.append((
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
  }""",
"""  // 头顶提示符号：直接显示 emoji（不加边框），水平居中于奶蛋头顶。
  // 竖直方向夹在 SCOREBOARD_SAFE_Y 以下，避免和顶部的「排气量」得分板叠在一起。
  const npcTop = npcBox ? npcBox.y : npcY - 232;
  const GLYPH_HALF = 26;
  const SCOREBOARD_SAFE_Y = 96;   // 得分板下沿 + 余量（canvas 坐标）
  if (npcState === NPC_STATES.SUSPICIOUS || npcState === NPC_STATES.WATCHING) {
    const isCatch = npcState === NPC_STATES.WATCHING;
    const bob = Math.sin(Date.now() * 0.006) * 5;
    const gy = Math.max(npcTop - GLYPH_HALF + bob, SCOREBOARD_SAFE_Y);
    ctx.save();
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    ctx.font = "44px 'Apple Color Emoji','Segoe UI Emoji','Noto Color Emoji',sans-serif";
    ctx.shadowColor = isCatch ? "rgba(239,68,68,0.55)" : "rgba(234,179,8,0.55)";
    ctx.shadowBlur = 14;
    ctx.fillText(isCatch ? "❗" : "❓", npcX, gy);
    ctx.restore();
  }

  // 被震晕：头顶转圈的星星
  if (npcState === NPC_STATES.STUNNED) {
    ctx.save();
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    ctx.font = "26px 'Apple Color Emoji','Segoe UI Emoji','Noto Color Emoji',sans-serif";
    const t = Date.now() * 0.0042;
    const oy = Math.max(npcTop - 26, SCOREBOARD_SAFE_Y);
    for (let i = 0; i < 3; i++) {
      const a = t + i * (Math.PI * 2 / 3);
      ctx.fillText("💫", npcX + Math.cos(a) * 36, oy + Math.sin(a) * 9);
    }
    ctx.restore();
  }"""))

# ---------- 10. 结算界面：奶蛙/奶蛋主题 ----------
R.append((
"""      <div class="modal-icon" id="modal-icon">💀</div>
      <div class="modal-title" id="modal-title">被抓现行！社死！</div>
      <div class="modal-desc" id="modal-desc">你在安静时偷偷放屁，被同伴猛回头抓个正着！</div>
      <div class="modal-stats">
        <div>坚持时间: <span id="stat-time" style="color:#2563eb;">18s</span></div>
        <div>放屁量: <span id="stat-score" style="color:#10b981;">1,250</span> ml</div>
      </div>""",
"""      <div class="modal-cast">
        <img class="modal-char" id="modal-frog" alt="奶蛙">
        <img class="modal-char egg" id="modal-egg" alt="奶蛋">
      </div>
      <div class="modal-title" id="modal-title">被抓现行！社死！</div>
      <div class="modal-desc" id="modal-desc">你在安静时偷偷放屁，被同伴猛回头抓个正着！</div>
      <div class="modal-stats">
        <div class="modal-stat">
          <span class="modal-stat-label">偷放屁时间</span>
          <span class="modal-stat-value time" id="stat-time">0s</span>
        </div>
        <div class="modal-stat">
          <span class="modal-stat-label">放屁量</span>
          <span class="modal-stat-value ml" id="stat-score">0<em>ml</em></span>
        </div>
      </div>"""))

# ---------- 11. 结算界面样式 ----------
R.append((
"""    .modal-icon { font-size: 54px; margin-bottom: 8px; }
    .modal-title { font-size: 22px; font-weight: 900; color: #0f172a; margin-bottom: 6px; }
    .modal-desc { font-size: 14px; color: #64748b; margin-bottom: 18px; line-height: 1.5; }
    .modal-stats {
      background: #f8fafc;
      border-radius: 12px;
      padding: 10px 14px;
      margin-bottom: 20px;
      display: flex;
      justify-content: space-around;
      font-size: 13px;
      font-weight: 700;
      color: #334155;
    }""",
"""    /* 结算立绘：奶蛙 + 奶蛋 */
    .modal-cast {
      display: flex;
      align-items: flex-end;
      justify-content: center;
      gap: 10px;
      height: 112px;
      margin-bottom: 10px;
    }
    .modal-char { height: 100%; width: auto; object-fit: contain; }
    .modal-char.egg { height: 94%; }
    .modal-title { font-size: 22px; font-weight: 900; color: #0f172a; margin-bottom: 6px; }
    .modal-desc { font-size: 14px; color: #64748b; margin-bottom: 18px; line-height: 1.5; }
    .modal-stats {
      background: #f8fafc;
      border: 1.5px solid #e2e8f0;
      border-radius: 14px;
      padding: 12px 10px;
      margin-bottom: 20px;
      display: flex;
      justify-content: space-around;
      gap: 10px;
    }
    .modal-stat { flex: 1; text-align: center; }
    .modal-stat-label {
      display: block;
      font-size: 12px;
      font-weight: 800;
      color: #64748b;
      letter-spacing: 1px;
      margin-bottom: 5px;
    }
    .modal-stat-value {
      display: block;
      font-size: 27px;
      font-weight: 900;
      line-height: 1.15;
      font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
    }
    .modal-stat-value.time { color: #2563eb; }
    .modal-stat-value.ml { color: #10b981; }
    .modal-stat-value em { font-size: 13px; font-style: normal; color: #94a3b8; margin-left: 2px; }"""))

# ---------- 12. 元素引用换成新立绘 ----------
R.append((
"""const modalIcon = document.getElementById('modal-icon');""",
"""const modalFrog = document.getElementById('modal-frog');
const modalEgg = document.getElementById('modal-egg');"""))

# ---------- 13. gameOver：立绘 + 偷放屁时间 ----------
R.append((
"""  statTime.textContent = `${Math.floor(elapsedSeconds)}s`;
  statScore.textContent = Math.floor(score).toLocaleString();

  if (reason === 'exploded') {
    sounds.playExplode();""",
"""  statTime.textContent = `${fartSeconds.toFixed(1)}s`;
  statScore.innerHTML = `${Math.floor(score).toLocaleString()}<em>ml</em>`;
  // 结算立绘跟着结局走：炸了就用放屁形态，被抓就保持静态
  modalFrog.src = reason === 'exploded' ? spriteFart.src : spriteIdle.src;
  modalEgg.src = reason === 'exploded' ? eggSide.src : eggFront.src;

  if (reason === 'exploded') {
    sounds.playExplode();"""))

R.append((
"""    modalIcon.textContent = "💥";
    modalTitle.textContent = "惊天巨响！当场社死！";""",
"""    modalTitle.textContent = "惊天巨响！当场社死！";"""))

R.append((
"""  sounds.playCaught();
  modalIcon.textContent = "👀";
  modalTitle.textContent = "被同伴抓个正着！";""",
"""  sounds.playCaught();
  modalTitle.textContent = "被同伴抓个正着！";"""))

# ---------- 14. 重开重置 ----------
R.append((
"""  nextMegaFartAt = MEGA_FART_STEP;
  megaBanner = 0;
  shakeTime = 0;
  npcReactTimer = 0;""",
"""  nextMegaFartAt = MEGA_FART_STEP;
  megaBanner = 0;
  megaFartTimer = 0;
  shakeTime = 0;
  npcReactTimer = 0;
  npcStunTimer = 0;
  fartSeconds = 0;"""))

for i, (old, new) in enumerate(R, 1):
    n = s.count(old)
    if n != 1:
        print(f"[FAIL] 改动 #{i} 命中 {n} 次（应为 1）")
        sys.exit(1)
    s = s.replace(old, new)
    print(f"[ok] 改动 #{i}")

if "modalIcon" in s:
    print("[FAIL] modalIcon 仍有残留引用")
    sys.exit(1)
print("[ok] modalIcon 已彻底移除")

with io.open(HTML, "w", encoding="utf-8") as f:
    f.write(s)
print("写入完成 %.0f KB" % (len(s.encode("utf-8")) / 1024))
