# 奶蛙偷偷放屁

一款竖屏 H5 反应类小游戏。玩家扮演一只憋着屁的奶蛙，长按按钮偷偷排气，同时提防旁边的「奶蛋」。

## 在线试玩

https://naiwa-fart.pages.dev

手机浏览器打开即可。iPhone 用 Safari 可以「添加到主屏幕」，装成 App 使用。

## 玩法

- 顶部声浪区显示环境噪音。噪音大时起风，此时排气最安全。
- 长按按钮排气，排气量就是得分。
- 胀气值满 100%，当场爆炸社死。
- 被奶蛋抓现行，同样结束。
- 奶蛋转身后要愣 0.45 秒才认得出。这 0.45 秒就是你的松手窗口。
- 每累计 500 毫升排气量，自动爆一个超级大屁，把奶蛋震晕 3 秒。
- 排气量攒到 3000 毫升，画面会被自己的绿烟糊死。

## 技术特点

- **单文件，零依赖**。精灵图内嵌为 base64，音效用 Web Audio 实时合成。
- **没有构建步骤**。源文件双击就能玩，离线可用。
- 全部逻辑在一个 HTML 文件里，约 1700 行。
- 计数后端用 Cloudflare Pages Functions。数据存在 KV 里，不引第三方统计。

## 本地运行

直接双击 `奶蛙偷偷放屁.html` 即可。

调试计数接口时需要本地服务：

```bash
python3 -m http.server 8878 --directory public
```

## 部署

```bash
./tools/deploy.sh
```

脚本做两件事：把源文件复制成 `public/index.html`，然后推送到 Cloudflare Pages。

源文件 `奶蛙偷偷放屁.html` 是唯一真源。`public/index.html` 是构建产物，不要直接改。

## 目录结构

```text
naiwa-fart/
├── 奶蛙偷偷放屁.html        # 唯一真源
├── HANDOVER.md              # 完整交接文档
├── README.md
├── public/                  # 构建产物，交给 Cloudflare
├── functions/api/plays.js   # 计数接口
├── wrangler.toml            # Pages 配置与 KV 绑定
├── assets/
│   ├── appicon/             # App 图标与 manifest
│   ├── src/                 # 抠好的原始素材
│   └── *.webp               # 内嵌用的压缩素材
├── tools/                   # 构建、部署、素材处理脚本
└── preview/                 # 各阶段实机截图
```

## 可调参数

调难度和手感时，只改这几处。

### 奶蛋灵敏度

搜 `NPC_TUNING`：

```js
const NPC_TUNING = {
  patrolMin: 3.2, patrolMax: 6.0,          // 发呆巡逻间隔（秒）
  idleToSusMin: 0.85, idleToSusMax: 1.40,  // 发呆 → 起疑
  susToWatchMin: 1.10, susToWatchMax: 1.70,// 起疑 → 抓现行
  reactDelay: 0.45,                        // 转身后愣多久才认得出
  suspicionRate: 62,                       // 安静期怀疑度增速
};
```

数值越大越警觉。

### 核心节奏

| 常量 | 当前值 | 含义 |
| --- | --- | --- |
| 胀气增速 | 3.8 / 秒 | |
| 排气速度 | 24 / 秒 | |
| 基础计分 | 70 毫升 / 秒 | |
| 掩护期倍率 | 1.8 | 计分乘数 |
| 起风间隔 | 7 到 13 秒 | 随机 |
| `MEGA_FART_STEP` | 500 毫升 | 超级大屁的触发间隔 |
| `NPC_STUN_TIME` | 3.0 秒 | 震晕奶蛋的时长 |
| `GREEN_FOG_FULL_ML` | 3000 毫升 | 绿烟完全遮住画面的阈值 |

### 称号

搜 `FART_TITLES`。数组必须按毫升从大到小排列。

| 排气量 | 称号 |
| --- | --- |
| 233 | 静音 |
| 666 | 气微 |
| 2026 | 闷雷 |
| 4399 | 人间大炮 |
| 8888 | 单人乐队 |
| 19988 | 真の屁王 |
| 54321 | 虚空屁神 |
| 88001 | 根本没有这样的屁 |

## 换素材

页面地址后加 `?custom=1`，程序就会去同级目录探测同名文件。默认不探测，否则线上每次加载会多出 12 个 404 请求。

可覆盖的文件名：

```text
player-idle.png      玩家静态        player-fart.png      玩家放屁
skin-floral.png      花肚兜          skin-luke.png        Luke
skin-tea.png         冰红茶          skin-secret.png      奶秘
watcher-back.png     奶蛋背对        watcher-side.png     奶蛋侧身
watcher-front.png    奶蛋正面
bys_disgust.png      旁观嫌弃        bys_approve.png      旁观认可
bys_envy.png         旁观羡慕        bys_shock.png        旁观惊吓
```

确认满意后再内嵌，流程见 `HANDOVER.md` 第六章。

## App 图标

图标分五种尺寸，适配 iOS 与安卓两套机制。

| 文件 | 用途 |
| --- | --- |
| `icon-180.png` | iOS「添加到主屏幕」 |
| `icon-192.png` | 安卓 |
| `icon-512.png` | 安卓与浏览器 |
| `icon-maskable-512.png` | 安卓自适应图标，内容收在安全区内 |
| `favicon-32.png` | 浏览器标签页 |

`apple-touch-icon` **必须是不透明、无圆角的正方形**。iOS 会把透明区渲染成黑色，然后再套一次圆角遮罩。透明圆角只会让四角多出一圈黑边。

## 文档

- `HANDOVER.md` —— 完整交接文档，含代码架构、常见改动流程、20 个实际踩过的坑。

## 许可

暂未指定。
