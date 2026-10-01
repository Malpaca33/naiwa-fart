#!/bin/bash
# 构建：把源文件复制成部署用的 index.html，并带上 App 图标与 manifest
set -e
cd "$(dirname "$0")/.."
mkdir -p public
cp 奶蛙偷偷放屁.html public/index.html
# 图标：跳过 _ 开头的中间产物（如 _master.png）
for f in assets/appicon/*.png; do
  case "$(basename "$f")" in _*) continue;; esac
  cp "$f" public/
done
cp assets/appicon/manifest.webmanifest public/
echo "已生成 public/index.html  ($(wc -c < public/index.html | tr -d ' ') bytes)"
