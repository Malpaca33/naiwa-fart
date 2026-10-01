#!/usr/bin/env python3
"""从 4 宫格参考图提取旁观奶蛙精灵图。

源图为带 alpha 通道的 RGBA WebP，背景已是真透明，因此无需抠底，
只需按 alpha 边界把四宫格切成四张独立精灵图。
"""
import os

from PIL import Image

SRC = "/Users/mac/.dsh/attachments/v1/objects/e3/e39db2b2df9b73d0ac8e95ac129c6d3a3092fb1f94b6cda1950035a4c50724a6"
OUT = "/Users/mac/Documents/dsh/naiwa-fart/assets"
PAD = 6          # 裁剪后四周留白
ALPHA_MIN = 8    # 低于此 alpha 视为透明

os.makedirs(OUT, exist_ok=True)

im = Image.open(SRC).convert("RGBA")
W, H = im.size
print(f"源图: {W}x{H}, mode=RGBA（背景已是透明）")

quads = [
    ("tl", (0, 0, W // 2, H // 2), "羡慕"),
    ("tr", (W // 2, 0, W, H // 2), "认可"),
    ("bl", (0, H // 2, W // 2, H), "嫌弃"),
    ("br", (W // 2, H // 2, W, H), "惊吓"),
]

tiles = []
for key, box, label in quads:
    tile = im.crop(box)
    mask = tile.getchannel("A").point(lambda v: 255 if v >= ALPHA_MIN else 0)
    bbox = mask.getbbox()
    if bbox is None:
        print(f"  [{key}] 空图！")
        continue

    # 判断内容是否贴到切分边界（可能被切坏）
    l, t, r, b = bbox
    touches = []
    if l == 0:
        touches.append("左")
    if t == 0:
        touches.append("上")
    if r == tile.size[0]:
        touches.append("右")
    if b == tile.size[1]:
        touches.append("下")

    l = max(0, l - PAD)
    t = max(0, t - PAD)
    r = min(tile.size[0], r + PAD)
    b = min(tile.size[1], b + PAD)
    out = tile.crop((l, t, r, b))

    path = os.path.join(OUT, f"bys_{key}.png")
    out.save(path)
    flag = f"  ⚠ 贴边: {','.join(touches)}" if touches else ""
    print(f"  [{key}] {label}: {out.size[0]}x{out.size[1]}  -> {os.path.basename(path)}{flag}")
    tiles.append((key, out))

# 检查图：深色底 + 透明棋盘格底各一张
if tiles:
    gap = 40
    tw = sum(t.size[0] for _, t in tiles) + gap * (len(tiles) + 1)
    th = max(t.size[1] for _, t in tiles) + gap * 2

    dark = Image.new("RGB", (tw, th), (24, 30, 48))
    x = gap
    for _, t in tiles:
        dark.paste(t, (x, gap), t)
        x += t.size[0] + gap
    dark.save(os.path.join(OUT, "_check_dark.png"))

    # 棋盘格
    chk = Image.new("RGB", (tw, th), (255, 255, 255))
    cp = chk.load()
    for yy in range(th):
        for xx in range(tw):
            if ((xx // 16) + (yy // 16)) % 2:
                cp[xx, yy] = (205, 210, 220)
    x = gap
    for _, t in tiles:
        chk.paste(t, (x, gap), t)
        x += t.size[0] + gap
    chk.save(os.path.join(OUT, "_check_checker.png"))

    print("检查图 -> _check_dark.png / _check_checker.png")
