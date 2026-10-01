#!/usr/bin/env python3
"""提取新角色素材：奶蛋三视图（右侧监视者）+ 玩家静态 / 放屁形态。

三张源图都是白底 JPG，需要泛洪抠底；奶蛋是同一角色的正/侧/背三视图，
按列空白自动切成三张。

抠底判据（只作用于与画面四边连通的区域）：
  1) 近白：三通道都接近 255
  2) 中性浅灰：饱和度极低且足够亮 —— 用来吃掉「排气姿势」底部那片灰色背景板
角色本体是黄/橙色（高饱和）或深色脚掌（低亮度），两者都不会被误伤。
"""
import os
from collections import deque

from PIL import Image, ImageFilter

OUT = "/Users/mac/Documents/dsh/naiwa-fart/assets/src"
os.makedirs(OUT, exist_ok=True)

SRC = {
    "fart": "/Users/mac/.dsh/attachments/v1/objects/8d/8d58e437244961244565a14d56c4ca29e0159b23bf5532310c6f386291d37a1e",
    "idle": "/Users/mac/.dsh/attachments/v1/objects/1a/1a78975fc530e56cd5f6eb9e028f2f45d2622978a2e4b1dce06af74f73edbba3",
    "egg":  "/Users/mac/.dsh/attachments/v1/objects/0d/0d0492f1f9de4a367a5e8dfe0a02a6a2d011e119461304acd695ebd27f05c0f0",
}

WHITE_TOL = 24     # 近白容差
GRAY_SAT = 20      # 「中性」的最大饱和度
GRAY_LUM = 140     # 「够亮」的最低亮度
ALPHA_MIN = 8


def knockout(img):
    img = img.convert("RGB")
    w, h = img.size
    px = img.load()

    def is_bg(x, y):
        r, g, b = px[x, y]
        if (255 - r) <= WHITE_TOL and (255 - g) <= WHITE_TOL and (255 - b) <= WHITE_TOL:
            return True
        mx, mn = (r, g, b), min(r, g, b)
        lum = (r * 299 + g * 587 + b * 114) // 1000
        return (max(mx) - mn) <= GRAY_SAT and lum >= GRAY_LUM

    bg = bytearray(w * h)
    dq = deque()

    def push(x, y):
        if is_bg(x, y) and not bg[y * w + x]:
            bg[y * w + x] = 1
            dq.append((x, y))

    for x in range(w):
        push(x, 0); push(x, h - 1)
    for y in range(h):
        push(0, y); push(w - 1, y)

    while dq:
        x, y = dq.popleft()
        if x + 1 < w: push(x + 1, y)
        if x - 1 >= 0: push(x - 1, y)
        if y + 1 < h: push(x, y + 1)
        if y - 1 >= 0: push(x, y - 1)

    alpha = Image.new("L", (w, h), 255)
    ap = alpha.load()
    for y in range(h):
        row = y * w
        for x in range(w):
            if bg[row + x]:
                ap[x, y] = 0
    alpha = alpha.filter(ImageFilter.GaussianBlur(0.5))
    out = img.convert("RGBA")
    out.putalpha(alpha)
    return out


def fill_vertical_holes(img, max_run=70):
    """把「同一列中被上下不透明像素夹住」的透明段补回不透明。

    用来救回奶蛋帽子上的白色绒边 —— 它和背景同为近白，泛洪会顺着绒边两端
    渗进去掏空它；但它在竖直方向上被黄色帽体夹住，据此可以还原。
    角色腿部之间的空隙向下开口、不会被夹住，因此不会误补。
    """
    a = img.getchannel("A").load()
    w, h = img.size
    filled = 0
    for x in range(w):
        y = 0
        while y < h:
            if a[x, y] < 128:
                start = y
                while y < h and a[x, y] < 128:
                    y += 1
                end = y
                if (start > 0 and end < h
                        and a[x, start - 1] >= 128 and a[x, end] >= 128
                        and (end - start) <= max_run):
                    for yy in range(start, end):
                        a[x, yy] = 255
                    filled += end - start
            else:
                y += 1
    return filled


def trim(img, pad=6):
    m = img.getchannel("A").point(lambda v: 255 if v >= ALPHA_MIN else 0)
    bb = m.getbbox()
    if bb is None:
        return img
    l, t, r, b = bb
    return img.crop((max(0, l - pad), max(0, t - pad),
                     min(img.width, r + pad), min(img.height, b + pad)))


def split_columns(img, min_gap=12):
    a = img.getchannel("A").point(lambda v: 255 if v >= ALPHA_MIN else 0)
    w, h = a.size
    px = a.load()
    occupied = [any(px[x, y] for y in range(0, h, 3)) for x in range(w)]
    spans, start = [], None
    for x, occ in enumerate(occupied):
        if occ and start is None:
            start = x
        elif not occ and start is not None:
            spans.append((start, x)); start = None
    if start is not None:
        spans.append((start, w))
    merged = []
    for s, e in spans:
        if merged and s - merged[-1][1] < min_gap:
            merged[-1] = (merged[-1][0], e)
        else:
            merged.append((s, e))
    return merged


results = {}

for key, name in (("fart", "player_fart"), ("idle", "player_idle")):
    ko = knockout(Image.open(SRC[key]))
    n = fill_vertical_holes(ko)
    im = trim(ko)
    im.save(f"{OUT}/{name}.png")
    results[name] = im
    print(f"{name}: 竖向补洞 {n} 像素")

egg = knockout(Image.open(SRC["egg"]))
n = fill_vertical_holes(egg)
print(f"奶蛋: 竖向补洞 {n} 像素")
egg = trim(egg)
cols = split_columns(egg)
print(f"奶蛋切出 {len(cols)} 视图: {cols}")
for i, (s, e) in enumerate(cols[:3]):
    piece = trim(egg.crop((max(0, s - 4), 0, min(egg.width, e + 4), egg.height)))
    name = ["egg_front", "egg_side", "egg_back"][i]
    piece.save(f"{OUT}/{name}.png")
    results[name] = piece

print()
for k, im in results.items():
    print(f"  {k:<13} {im.width:>4}x{im.height:<4} 宽高比 {im.width/im.height:.3f}")

# 检查奶蛋帽檐白边是否被抠穿（应完全不透明）
front = results["egg_front"]
ap = front.getchannel("A").load()
band_y = int(front.height * 0.30)
holes = sum(1 for x in range(front.width) if ap[x, band_y] < 128)
print(f"\n帽檐带 y={band_y} 透明像素数 = {holes} / {front.width}"
      f"  {'✅ 完好' if holes < front.width*0.15 else '⚠ 被抠穿'}")
