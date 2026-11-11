# 03 · 引擎：index.html

一个 HTML 文件，`window.renderAt(t)` 画出第 t 秒的画面（1080×1920），`render.py` 用无头 Chrome 一帧帧截图（30 fps），ffmpeg 合成。画面里每个东西都是时间的函数，没有随机数（用 `hr(n)`），所以改一句台词重渲染，结果完全可复现。

## 文件里有什么（从上到下）

| 部分 | 内容 | 每集要不要改 |
| --- | --- | --- |
| `STATE`、`C` 颜色 | 角色状态默认值、配色 | 换角色/配色时改 |
| helpers | `clamp` `hr` `eo` `eio` `spr`（弹簧）`pop(t,t0)`（弹出，带过冲）`win(t,a,b)`（淡入淡出窗口）`rr` `ell` `text` `shape` | 不改 |
| `L(id)`、`W_(id, word)` | 某句台词的开始时间、某个词说出来的时间（来自 timeline.json） | 用 |
| `room(t)` | 背景房间 | 换场景时改 |
| `leo(t, o)` | 主角。`o`：`pose`（idle / phone / point / wave）、`hair`（发量缩放，乱发时有效）、`sweat`、`brow`、`smile`、`look`、`x` `y` `s`（位置、缩放）、`shave`（0–1 擦掉胡茬）、`talkBob`；嘴型自动跟配音音量开合（mouth.json） | 加新可改项时改 |
| 道具 | `socks` `boxes` `phone` `hairTag` `teaBubble` `burst` `rules` `vote` `commentCTA` `endCard` `scissors` `boxIcon` | 每集按剧情加、改 |
| `hud(t)` | 顶部面板，读 `STATE.day/days/meter/ready`；`HUD_GAIN` 可做进度条上涨动画 | 不改 |
| `captions(t)` | 大字幕：按 timeline 的词自动分组（一次 1–3 个词，≤15 个字母），`buildChunks` 里的 `HL` 正则决定哪些词变黄 | 改 `HL` |
| `draw(t)` | **每集的场景编排**：镜头（缩放、震屏）、每句台词对应的画面窗口 `sc('L03')`、主角姿势、道具出现 | 每集重写 |
| `FIX_AT`、`renderAt` | 改造那一刻之前用 `STATE.before` 画 | 设 `FIX_AT` |

## 版面安全区（竖屏）

- 0–200：顶部面板
- 300–1000：道具、卡片、短信、投票卡
- 600–1400：主角（缩到 0.62–0.8 时让出上面给卡片）
- 1500–1720：字幕（白字黑边，重点词黄）
- 1760–1880：最后的「DAY N+1 TOMORROW」

## 写一集的场景

1. 先跑 `voice.py`，有了 `timeline.json` 才知道每句、每个词在第几秒
2. 在 `draw(t)` 里：`const [a, b] = sc('L03')` 拿到这句台词的画面窗口，`if (t >= a && t < b)` 里放这句的道具和姿势；关键词上 `pop(t, W_('L03', 'socks'))` 弹出东西
3. 震屏 / 推镜：参考 `shake`、`youK`（某个词上推近 25%，指数衰减）
4. `python scripts/render.py EP stills 1,4,8,...`（每句台词中间各一帧），用 Read 看 `stills/sheet.png`：字幕有没有挡脸、卡片有没有压住主角的脸、道具有没有出画、顶部面板有没有被盖住
5. 满意了再 `render.py EP all`

## 风格

- 粗黑描边（9px）、扁平色块、没有渐变；一个主色（红）做重点
- 每 2–3 秒画面上要有新东西（弹出、镜头动、表情变）；`motion` 检查用 motion-reel 的 `check.py motion`（可选）
- 主角说话时身体会轻微摆动，站着别完全不动
