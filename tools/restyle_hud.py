#!/usr/bin/env python3
"""HUD 调整：
  1. 去掉两张状态卡的静态标题（⚠️肚肚胀气值 / 👀同伴怀疑度）
  2. 动态徽标改成「大图标 + 大字」（17px），不再用小字
  3. SCORE → 排气量，放大，末尾加单位 ml
"""
import io
import sys

HTML = "/Users/mac/Documents/dsh/naiwa-fart/奶蛙偷偷放屁.html"

with io.open(HTML, encoding="utf-8") as f:
    s = f.read()

REPL = [
    # ---- 1. 状态卡样式：去掉标题行的小字排版，徽标放大 ----
    ("""    .stat-label-row {
      display: flex;
      justify-content: space-between;
      align-items: center;
      font-size: 12px;
      font-weight: 800;
      color: #334155;
      margin-bottom: 6px;
    }
    .stat-status-badge {
      font-size: 11px;
      font-weight: 800;
      padding: 1px 6px;
      border-radius: 6px;
    }""",
     """    /* 状态区只用大图标 / 大字表达，不放小字说明 */
    .stat-label-row {
      display: flex;
      justify-content: center;
      align-items: center;
      min-height: 26px;
      margin-bottom: 7px;
    }
    .stat-status-badge {
      font-size: 17px;
      font-weight: 900;
      line-height: 1.2;
      padding: 3px 12px;
      border-radius: 9px;
      letter-spacing: 0.5px;
      white-space: nowrap;
    }"""),

    # ---- 2. 胀气卡：删静态标题 ----
    ("""        <div class="stat-label-row">
          <span>⚠️ 肚肚胀气值</span>
          <span class="stat-status-badge" id="gas-badge" style="background:#fef3c7; color:#b45309;">2格 (40%)</span>
        </div>""",
     """        <div class="stat-label-row">
          <span class="stat-status-badge" id="gas-badge" style="background:#fef3c7; color:#b45309;">⚠️ 40%</span>
        </div>"""),

    # ---- 3. 怀疑度卡：删静态标题 ----
    ("""        <div class="stat-label-row">
          <span>👀 同伴怀疑度</span>
          <span class="stat-status-badge" id="sus-badge" style="background:#f1f5f9; color:#475569;">发呆中</span>
        </div>""",
     """        <div class="stat-label-row">
          <span class="stat-status-badge" id="sus-badge" style="background:#f1f5f9; color:#475569;">😴 发呆中</span>
        </div>"""),

    # ---- 4. 计分板：SCORE → 排气量 + 单位 ----
    ("""      <div class="score-badge">
        <span class="score-title">SCORE</span>
        <span class="score-value" id="score-val">000000</span>
      </div>""",
     """      <div class="score-badge">
        <span class="score-title">排气量</span>
        <span class="score-value" id="score-val">000000</span>
        <span class="score-unit">ml</span>
      </div>"""),

    # ---- 5. 计分板样式：放大 ----
    ("""    .score-badge {
      background: rgba(15, 23, 42, 0.82);
      backdrop-filter: blur(8px);
      border: 2px solid #38bdf8;
      border-radius: 999px;
      padding: 4px 18px;
      box-shadow: 0 4px 14px rgba(0, 0, 0, 0.25);
      display: flex;
      align-items: center;
      gap: 8px;
    }
    .score-title {
      font-size: 11px;
      font-weight: 800;
      color: #94a3b8;
      letter-spacing: 1px;
    }
    .score-value {
      font-size: 18px;
      font-weight: 900;
      color: #38bdf8;
      font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
      letter-spacing: 1px;
    }""",
     """    .score-badge {
      background: rgba(15, 23, 42, 0.85);
      backdrop-filter: blur(8px);
      border: 2.5px solid #38bdf8;
      border-radius: 999px;
      padding: 6px 22px;
      box-shadow: 0 5px 18px rgba(0, 0, 0, 0.28);
      display: flex;
      align-items: baseline;
      gap: 9px;
    }
    .score-title {
      font-size: 16px;
      font-weight: 900;
      color: #cbd5e1;
      letter-spacing: 1.5px;
    }
    .score-value {
      font-size: 30px;
      font-weight: 900;
      color: #38bdf8;
      font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
      letter-spacing: 1px;
      line-height: 1.1;
    }
    .score-unit {
      font-size: 15px;
      font-weight: 800;
      color: #94a3b8;
      letter-spacing: 0.5px;
    }"""),

    # ---- 6. 胀气徽标文案：带大图标，去掉冗余「N格」 ----
    ("""    gasBadge.textContent = `5格 (危急 100%)`;""",
     """    gasBadge.textContent = `💥 危急 100%`;"""),

    ("""    gasBadge.textContent = `${activeGasBlocks}格 (${gasPercent}%)`;""",
     """    gasBadge.textContent = `⚠️ ${gasPercent}%`;"""),
]

for i, (old, new) in enumerate(REPL, 1):
    n = s.count(old)
    if n != 1:
        print(f"[FAIL] 替换 #{i} 命中 {n} 次（应为 1）")
        sys.exit(1)
    s = s.replace(old, new)
    print(f"[ok] 替换 #{i}")

with io.open(HTML, "w", encoding="utf-8") as f:
    f.write(s)
print("写入完成 %.0f KB" % (len(s.encode("utf-8")) / 1024))
