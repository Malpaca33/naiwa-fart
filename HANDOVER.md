# 奶蛙偷偷放屁 · 项目交接文档

本文档面向接手开发的工程师或 AI Agent。读完本文，你应该能在不破坏现有功能的前提下增加新特性。

## 一、项目概况

### 1.1 这是什么

一款竖屏 H5 反应类小游戏。玩家扮演一只憋着屁的奶蛙，长按按钮偷偷排气。右侧的「奶蛋」负责监视。排气量就是得分。

游戏没有倒计时，只有两种结局：胀气值满 100% 当场爆炸社死，或者被奶蛋抓现行。

### 1.2 技术栈

- 原生 HTML5、Canvas 2D、Web Audio API
- 零外部依赖，零构建工具
- 精灵图以 base64 内嵌，音效实时合成
- 部署在 Cloudflare Pages，计数后端用 Pages Functions 加 KV

### 1.3 在线地址

```
游戏    https://naiwa-fart.pages.dev
计数接口 https://naiwa-fart.pages.dev/api/plays
```

Cloudflare 账号：`malpaca56@gmail.com`，Account ID `382c61e706ae9562bdaccb5b00a05374`。

## 二、快速上手

### 2.1 本地运行

直接双击 `奶蛙偷偷放屁.html` 即可。文件自包含，离线可玩。

带计数接口调试时，需要一个本地服务：

```bash
python3 -m http.server 8878 --directory public
```

### 2.2 构建与部署

```bash
./tools/deploy.sh
```

这个脚本做两件事：把源文件复制成 `public/index.html`，然后调 `wrangler pages deploy` 推送。

源文件是 `奶蛙偷偷放屁.html`。**它是唯一真源**。`public/index.html` 是构建产物，不要直接改。

因为 `wrangler.toml` 里写了 `pages_build_output_dir`，部署命令**不要**再传目录参数。

### 2.3 目录结构

```
naiwa-fart/
├── 奶蛙偷偷放屁.html        # 唯一真源，单文件游戏
├── public/
│   ├── index.html           # 构建产物（由 build.sh 生成）
│   └── _headers             # Cloudflare Pages 响应头
├── functions/api/plays.js   # 计数接口（Pages Function）
├── wrangler.toml            # Pages 配置与 KV 绑定
├── assets/
│   ├── *.webp               # 内嵌用的压缩素材
│   └── src/*.png            # 抠好的原始素材
├── tools/
│   ├── build.sh             # 复制源文件到 public/
│   ├── deploy.sh            # 构建 + 部署
│   └── round*.py            # 历史改动脚本（仅存档）
├── preview/*.png            # 各阶段实机截图
└── .bak_*.html              # 历史版本备份
```

## 三、代码架构

### 3.1 单文件布局

`奶蛙偷偷放屁.html` 约 1700 行。用注释分隔线划分区块，搜索区块名可以快速定位：

| 区块 | 搜索关键字 | 作用 |
| --- | --- | --- |
| 样式 | `<style>` | 全部 CSS |
| 界面 | `<div id="game-container">` | 全部 HTML |
| 音效 | `Sound Engine` | Web Audio 合成器 |
| 玩家素材 | `Load 1:1 True 3D Sprites` | 玩家两张精灵图 |
| 换装素材 | `玩家换装形态` | 四套换装 |
| 旁观素材 | `Bystander Sprites` | 旁观奶蛙四种表情 |
| 监视者素材 | `监视者「奶蛋」三视图` | 奶蛋正侧背 |
| 界面绑定 | `UI Setup & Grid Elements` | DOM 元素引用 |
| 画布 | `Canvas Setup` | 画布尺寸与适配 |
| 状态 | `Game State` | 全部状态变量 |
| 输入 | `Input Handling` | 按钮与键盘 |
| 粒子 | `Particle System` | 绿烟与汗滴 |
| 主循环 | `Game Loop` | update 与 render |
| 结算 | `End Game` | gameOver 与重开 |

### 3.2 核心状态

状态变量全部集中声明，位于 `Game State` 区块。

| 变量 | 含义 |
| --- | --- |
| `isPlaying` | 是否在游戏中 |
| `isFarting` | 是否按住排气 |
| `gasLevel` | 胀气值，0 到 100 |
| `suspicion` | 怀疑度，0 到 100 |
| `score` | 排气量，即得分，单位 ml |
| `fartSeconds` | 累计偷放屁时间 |
| `fartVolume` | 单次放屁量，松手后归零 |
| `isCoverActive` | 是否处于起风掩护期 |
| `npcState` | 奶蛋状态机 |
| `bystanderTier` | 旁观奶蛙当前表情档位 |
| `activeSkin` | 当前换装，`null` 表示原样 |
| `comboCount` | 掩护期内连续起手次数 |
| `nextMegaFartAt` | 下一个超级大屁的触发线 |

### 3.3 游戏循环

`gameLoop` 每帧调用 `update(dt)` 与 `render()`。`dt` 上限 0.1 秒，防止切后台回来跳帧。

`update` 的执行顺序不能随意调整：

1. 推进纯视觉计时器（震动、横幅、飘字）
2. 累加胀气 `gasLevel += 3.8 * dt`
3. 处理排气与计分
4. 推进起风周期
5. 运行奶蛋 AI
6. 判定结局
7. 触发超级大屁
8. 更新旁观奶蛙档位
9. 刷新界面

其中第 1 步故意放在 `if (!isPlaying) return` **之前**，这样结算后震动和飘字还能播完。

### 3.4 奶蛋状态机

```
IDLE ──巡逻超时──> SUSPICIOUS ──转身延时──> WATCHING ──发现你在放屁──> 抓住
 ↑                     ↑                      │
 └─────────────────────┴──────────────────────┘
                    超时返回 IDLE

任意状态 ──超级大屁──> STUNNED（3 秒，期间抓不了你）
任意状态 ──起风────> 强制 IDLE（完全不转头）
```

四个状态的优先级，从高到低：STUNNED、起风、IDLE、SUSPICIOUS、WATCHING。

**起风期间奶蛋完全失效**。`isCoverActive` 为真时，状态机被强制重置为 IDLE，不进入起疑，也不转身。

### 3.5 粒子系统

`spawnGreenFart(x, y, dir)` 生成绿烟粒子。`dir` 控制喷射方向：`-1` 朝左（默认），`+1` 朝右。

超级大屁期间整个玩家精灵图水平镜像，`dir` 传 `+1`，烟就往奶蛋方向飞。

## 四、可调参数

调难度和手感时，只改这几处，不要散着改。

### 4.1 奶蛋灵敏度

搜索 `NPC_TUNING`：

```js
const NPC_TUNING = {
  patrolMin: 3.2, patrolMax: 6.0,          // 发呆巡逻间隔（秒）
  idleToSusMin: 0.85, idleToSusMax: 1.40,  // 发呆 → 起疑
  susToWatchMin: 1.10, susToWatchMax: 1.70,// 起疑 → 抓现行
  reactDelay: 0.45,                        // 转身后愣多久才认得出
  suspicionRate: 62,                       // 安静期怀疑度增速
};
```

数值越大越警觉。`reactDelay` 是玩家的松手窗口，调到 0 就变成秒杀。

### 4.2 核心节奏

| 常量 | 当前值 | 含义 |
| --- | --- | --- |
| 胀气增速 | 3.8 / 秒 | 写在 `update` 里 |
| 排气速度 | 24 / 秒 | 写在 `update` 里 |
| 基础计分 | 70 ml / 秒 | 写在 `update` 里 |
| 掩护期倍率 | 1.8 | 计分乘数 |
| 起风间隔 | 7 到 13 秒 | 随机 |
| 起风时长 | 2.4 到 4.0 秒 | 随机 |
| `MEGA_FART_STEP` | 500 ml | 每累计这么多排气量爆一发超级大屁 |
| `NPC_STUN_TIME` | 3.0 秒 | 超级大屁震晕奶蛋的时长 |
| `GREEN_FOG_FULL_ML` | 3000 ml | 绿烟完全遮住画面的阈值 |

### 4.3 称号表

搜索 `FART_TITLES`。数组必须**按 ml 从大到小**排列，`fartTitle` 取第一个够到的档位。

```js
const FART_TITLES = [
  { ml: 88001, label: '根本没有这样的屁' },
  { ml: 54321, label: '虚空屁神' },
  // ⋯⋯
  { ml: 233,   label: '静音' },
];
```

分数低于最低档时返回 `null`，界面隐藏称号。

### 4.4 旁观奶蛙

搜索 `BYSTANDER_TIERS`。档位按**单次放屁量**升档，不是累计排气量。

```js
const BYSTANDER_TIERS = [
  { ml: 0,   key: 'disgust', label: '嫌弃' },
  { ml: 100, key: 'approve', label: '认可' },
  { ml: 300, key: 'envy',    label: '羡慕' },
  { ml: 500, key: 'shock',   label: '惊吓' },
];
```

台词写在 `BYSTANDER_LINES`，键名要和 `key` 对应。`BYSTANDER_RAGE_ML` 是狂暴档，超过就放大加抖动。

## 五、素材系统

### 5.1 内嵌与覆盖

所有精灵图以 base64 内嵌，所以游戏能离线单文件运行。

调试换素材时，在页面地址后加 `?custom=1`，程序会去同级目录探测同名文件。**默认不探测**，否则线上每次加载会多出 12 个 404 请求。

可覆盖的文件名：

```
player-idle.png      玩家静态        player-fart.png      玩家放屁
skin-floral.png      花肚兜          skin-luke.png        Luke
skin-tea.png         冰红茶          skin-secret.png      奶秘
watcher-back.png     奶蛋背对        watcher-side.png     奶蛋侧身
watcher-front.png    奶蛋正面
bys_disgust.png      旁观嫌弃        bys_approve.png      旁观认可
bys_envy.png         旁观羡慕        bys_shock.png        旁观惊吓
png1.png / png3.png  旧名兼容：玩家放屁
png2.png             旧名兼容：玩家静态
```

### 5.2 绘制约定

角色统一走 `drawChar(img, cx, baseY, targetH, anchorX, dx, dy)`。它按目标高度等比缩放，宽度自动算。**换任何尺寸的精灵图都不会变形**。

`anchorX` 是水平锚点：0 表示左缘对齐，0.5 表示居中，1 表示右缘对齐。放屁形态因为左侧有烟，锚点用 0.58。

### 5.3 抠图工具

`tools/extract_characters.py` 从白底 JPG 抠图。判据有两条：近白，或者中性浅灰且够亮。

第二条用来吃掉「排气姿势」底部那片灰色背景板。角色本体是高饱和黄色或深色脚掌，不会误伤。

如果源图**自带 alpha 通道**，不要抠图，直接用 `getbbox()` 按 alpha 边界裁切即可。多数素材属于这种。

## 六、常见改动怎么做

### 6.1 加一套换装

**第一步**，把图抠好存成 `assets/src/costume_xxx.png`。

**第二步**，在导出脚本里加一条记录，生成 WebP 并转 base64。

**第三步**，在 HTML 的 `.skin-row` 里加一个按钮：

```html
<button class="skin-chip" data-skin="xxx">名字</button>
```

**第四步**，在 `SKIN_SPRITES` 里登记：

```js
const SKIN_SPRITES = {
  floral: spriteSkinFloral,
  // ⋯⋯
  xxx: spriteSkinXxx,
};
```

事件绑定用的是 `querySelectorAll('.skin-chip')`，会自动生效，不用改。

### 6.2 加一个称号

在 `FART_TITLES` 里按 ml 降序插入一项。改完检查相邻档位，别让两个档位落在同一个数上。

### 6.3 改难度

先调 `NPC_TUNING`。不够再调 `update` 里的胀气增速与排气速度。最后才动 `MEGA_FART_STEP` 和 `NPC_STUN_TIME`。

### 6.4 改文案

界面文案在 HTML 和 `gameOver` 里，画面文案在 `ctx.fillText` 附近。搜中文原文即可定位。

### 6.5 换素材

带 `?custom=1` 打开页面，把同名 PNG 丢进同级目录即可预览，不用改代码。确认满意后再走 6.1 的流程内嵌。

## 七、踩过的坑

这一节记录实际踩到的坑，能省下大量返工。

### 7.1 文字排版

**绝对定位容器会折行。** `.scoreboard-container` 用了 `left: 50%` 加 `translateX(-50%)`，可用宽度只有半屏，导致「排气量」被折成两行。解决办法是加 `width: max-content` 和 `white-space: nowrap`。

**flex 行会挤爆。** 底部换装那一排加进第五个元素后超出容器宽度，自动换行了。减内边距和字号才容下。加元素前先算总宽。

### 7.2 字体

**中文的字宽测不出字体。** CJK 字符在所有中文字体里都是全角，16 个字乘 40 像素恒等于 640。用 `measureText` 验证字体是否生效完全无效，必须比对渲染后的像素。

**像素比对别用 alpha 通道。** 如果在画布上填了不透明白底，alpha 处处是 255，求和恒等于宽乘高乘 255。要比对红色通道。

**macOS 的 ❓ 和 ❗ 都是红色。** Apple Color Emoji 同时收录这两个字形，且都是红色。彩色 emoji 不吃 `fillStyle`，连 Unicode 变体选择符 `U+FE0E` 也无效。想改颜色只能用 ASCII 的 `?` 和 `!`。

**canvas 字体要显式设。** `ctx.font` 设置后如果解析失败会静默回退，不会报错。想确认生效只能看渲染结果。

### 7.3 素材处理

**白绒边会被泛洪掏空。** 奶蛋帽子上的白色绒边和背景同为近白，泛洪顺着两端渗进去掏空了它。解决办法是竖向补洞：同一列里被上下不透明像素夹住的透明段，就是角色内部的洞。

**角色腿缝不能误补。** 上面的补洞逻辑要加长度上限，否则两腿之间的空隙也会被填上。腿缝向下开口，不会被上下夹住，所以天然安全。

### 7.4 无头浏览器验证

**窗口宽度有下限。** `--window-size=420,900` 会被 Chrome 抬到最小 500 像素宽，截图仍按 420 裁，看起来就像右侧被切了。**这是截图假象，不是布局溢出**。判断布局问题要用 `scrollWidth` 和 `clientWidth` 实测，别靠眼看。

**无限动画循环会让 Chrome 挂住。** 游戏用 `requestAnimationFrame` 无限递归，`--dump-dom` 和 `--screenshot` 可能永远不返回。要加看门狗超时兜底：

```bash
( "$CHROME" ... ) & pid=$!
( sleep 30; kill -9 $pid 2>/dev/null ) & wd=$!
wait $pid 2>/dev/null; kill $wd 2>/dev/null
```

**不要用 setTimeout 做帧循环刹车。** 在 `--virtual-time-budget` 模式下，定时器会提前触发，画布还没渲染就被停住，截图全是空白。

**多实例要用独立 profile。** 复用 `--user-data-dir` 会让第二次启动卡死。每次用不同目录。

### 7.5 本机网络

**curl 和 node 解析不了 `pages.dev`。** 系统解析器和 Python 都正常，只有 curl 和 node 失败。原因是它们内置 c-ares 解析器，被本机代理软件 Clash 干扰。

绕过办法是加 `--resolve`：

```bash
curl --resolve naiwa-fart.pages.dev:443:172.66.44.186 https://naiwa-fart.pages.dev/
```

判断线上是否可达，用 Python 建 TCP 连接最可靠。

### 7.6 部署

**部署传播有延迟。** 刚部署完立刻请求，可能命中旧版本，表现为 POST 返回 405 或页面是旧的。等几十秒再测，**别急着改代码**。

**Cloudflare API 偶发瞬时故障。** wrangler 会提示创建 issue 并失败。直接重试即可。

**KV 是最终一致性。** 写入后立刻读可能拿到旧值，要等几十秒。

### 7.7 代码维护

**替换脚本要防锚点消失。** 用 Python 脚本做批量替换时，锚点必须在替换前断言命中次数为 1。曾经用 `let costumeOn = false;` 做锚点，但这个变量早已改名为 `activeSkin`，导致脚本静默失败。

**`requestAnimationFrame(gameLoop);` 出现两次。** 一次在函数内递归，一次是初始启动。拿它做锚点必须带上上下文，否则命中数为 2。

**改完必须跑语法检查。**

```bash
python3 -c "
import io,re
s=io.open('奶蛙偷偷放屁.html',encoding='utf-8').read()
io.open('/tmp/gc.js','w',encoding='utf-8').write(re.findall(r'<script>(.*?)</script>',s,re.S)[-1])
" && node --check /tmp/gc.js
```

注意 `node --check` 只查语法，查不出未定义变量。改完要跑一次运行时探针，把 `window.onerror` 捕获的错误打到 `document.title` 上。

## 八、当前状态与待办

### 8.1 未推送的改动

**本地有两项改动尚未上线**，需要先确认再推送：

1. 绿色浓烟遮罩：排气量攒到 `GREEN_FOG_FULL_ML` 时，画面被自己的屁完全遮住。当前阈值是 3000 ml
2. 字体换成兰亭黑：界面文字与 canvas 文字都改了

线上版本是 394,845 字节。本地是 396,239 字节。

### 8.2 已知限制

**字体依赖 macOS。** 兰亭黑是系统字体，安卓机上不存在，会回退到系统默认。想让所有设备一致，需要内嵌 Web 字体，代价是文件体积明显增大。

**单文件体积。** 当前 387 KB，其中内嵌素材占大部分。继续加素材会持续变大。

**计数口径是人次。** 每打开一次页面算一次，刷新也算。想统计独立访客需要加去重逻辑。

**绿烟只盖画布。** 顶部状态栏和排气量得分板是 HTML，不受影响。全遮时玩家仍能看见分数。

### 8.3 可以扩展的方向

- 结算面板加分享图，用 canvas 导出
- 排行榜，复用现有的 KV 命名空间
- 音效开关。目前默认开启，界面上没有入口
- 绿烟全遮时直接结算，做成第三种结局
- 更多换装与称号，流程见第六章
