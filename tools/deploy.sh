#!/bin/bash
# 一键构建 + 部署到 Cloudflare Pages
#   - 源文件是 奶蛙偷偷放屁.html，构建成 public/index.html
#   - Functions 在 functions/，KV 绑定写在 wrangler.toml
#   - 因为 wrangler.toml 里有 pages_build_output_dir，这里不再传目录参数
set -e
cd "$(dirname "$0")/.."
./tools/build.sh
npx --yes wrangler@4 pages deploy --branch=main --commit-dirty=true
