# 02 · 角色怎么固定：状态文件

角色是代码画的（Canvas 2D），同一组参数每次画出来都一样，不会像 AI 生图那样每集变脸。剪了头发、刮了胡子这类改动，记在每集的 `state.json` 里。

## state.json

```json
{"day": 3, "days": 30, "meter": "DATE-READY", "ready": 7,
 "hair": "short", "stubble": false, "stains": true, "boxes": 7, "socks": true,
 "fixed": ["HAIRCUT", "SHAVE"],
 "before": {"stubble": true, "ready": 4}}
```

- `day / days / meter / ready`：顶部面板
- `hair / stubble / stains / boxes / socks`：角色和房间现在的样子
- `fixed`：已经改过的（`new_episode.py` 不让同一样改两次）
- `before`：这一集改之前的样子。引擎在 `FIX_AT` 之前用 `before` 画，之后用新样子（`new_episode.py` 自动写）

下一集 = 上一集的 state + 这集赢的那一项：

```bash
python scripts/new_episode.py SERIES 3 --winner SHAVE
```

## fixes.json：能投的东西

```json
"HAIRCUT": {"set": {"hair": "short"}, "ready": 4}
```

`set` 是永久改掉的字段，`ready` 是进度条涨多少。观众点赞最多的评论不在表里时：

```bash
python scripts/new_episode.py SERIES 5 --winner "SHOWER" --set '{"shower": true}' --ready 3
```

## 加一个新的可改项（例：眼镜换成隐形 / 连帽衫换衬衫）

1. 在引擎 `index.html` 顶部的 `STATE` 默认值里加字段（例 `top: 'hoodie'`）
2. 在 `leo()` 里画两个样子：`if (STATE.top === 'hoodie') {…} else {…}`；房间里的东西写在 `room()` 或道具函数里
3. 在 `fixes.json` 里加一行：`"SHIRT": {"set": {"top": "shirt"}, "ready": 4}`
4. `python scripts/render.py EP stills 2,10` 用 `?state=` 两个样子各看一眼（或临时改 state.json），确认改前改后都对，其他地方没被带歪

## 改造那一集怎么转场

在这一集的场景代码里设 `FIX_AT = W_('L03', 'done')`（台词里某个词说出来的时刻）。之前画 `before`，之后画新样子。想要过程感就加一个进度参数：

- 刮胡子：`leo(t, { shave: clamp((t - T0) / 1.2) })`，胡茬从左往右被擦掉
- 剪头发：在 `FIX_AT` 前后加一团碎发飞出（`burst()`、几个 `ell()`），新发型用 `pop()` 弹出来
- 进度条：`FIX_AT` 之前面板自动显示旧数值；想让它在 `FIX_AT` 之后慢慢涨上去：`HUD_GAIN = t => -(STATE.ready - (STATE.before?.ready ?? STATE.ready)) * (1 - eo((t - FIX_AT) / 0.8))`
