# AI 观众投票动画连载 · AI Vote Series

[中文](#中文) · [English](#english)

<p align="center"><img src="demo/preview.gif" width="300" alt="30 Days to the Date - Day 1"> <img src="demo/vote.gif" width="300" alt="the daily vote"></p>

<p align="center"><b><a href="demo/30DaysToTheDate_Day1.mp4">▶ 看完整第 1 集 / Watch Day 1 (44 s)</a></b></p>

---

## 中文

**Leo 有 30 天，30 天后是他人生第一次相亲。** 他现在的袜子能自己立起来，厨房堆了 47 个外卖盒，上一次跟女生说话是点奶茶：「大杯，去冰。」每集结尾让观众在评论区二选一，先剪头发还是先扔外卖盒？票多的下一集就改，改了就不会变回去。观众投完票，第二天会回来看结果。

外网有一类号这么做（例：IG @30daystofix，7 天 8 条涨到 27 万粉）。这个仓库是做这种 **观众投票的每日动画连载** 的完整流程，免费开源：

- **Claude Skill**：装进 [Claude Code](https://claude.com/claude-code) 后说「出第 2 集，上集赢了 HAIRCUT」
- **画面全用代码画**：Canvas 2D，浏览器逐帧渲染，ffmpeg 合成；不抽卡、不花生成视频的钱
- **角色不变脸**：Leo 由一份状态文件决定（发型、胡茬、衣服、房间），剪过的头发以后每集都是短的，「改了不变回去」由程序保证

  <img src="demo/state_day1-3.png" width="600" alt="Day 1 -> haircut -> shave">

- **用你自己的声音**：旁白用你的克隆声音（火山引擎声音复刻），没配好之前用 edge-tts 免费占位；Whisper 对出每个词的时间，大字幕一组一组跳，嘴型跟着音量开合
- **配乐音效也是代码**：每个笑点、每张投票卡都有音效，卡在台词的词上

演示视频的英文旁白就是作者本人的中文克隆音色说的英文。

### 做法

| | 做什么 | 怎么做 |
| --- | --- | --- |
| ① 设定 | 主角、N 天后的大事、能投的东西（`fixes.json`） | 和 Claude 聊，照 `docs/01-format.md` |
| ② 台词 | 结果 → 改的过程 → 新问题 → 二选一 → Comment one word | `new_episode.py` 写好骨架，Claude 写台词 |
| ③ 配音 | 你的克隆声音逐句合成，对齐每个词 | `voice.py` |
| ④ 画面 | 按台词编排场景，关键词上弹出道具 | `index.html` 的 `draw(t)` |
| ⑤ 出片 | 抽帧检查 → 逐帧渲染 → 配乐音效 → MP4 | `render.py` |
| ⑥ 读票 | 数评论，写 `log.md`，第二天回到 ② | `docs/05-publish.md` |

### 你需要

- Python 3.9+、ffmpeg、Chrome（或 Edge）
- `pip install playwright numpy scipy pillow faster-whisper edge-tts`
- 想用自己的声音：火山引擎「声音复刻」，把 `VOLC_API_KEY`、`VOLC_SPEAKER_ID` 写进 `.env`（见 `docs/04-voice.md`）

### 安装成 Claude Skill

把这个仓库的链接丢给 Claude Code，说「帮我装成 Skill」。或者：

```bash
git clone git@github.com:You-5C24/audience-vote-animation.git ~/.agents/skills/audience-vote-animation
```

### 只用脚本

```bash
python scripts/new_series.py my-series --from-example      # 拿示例起步，检查环境
python scripts/render.py my-series/ep01 stills 1,8,35      # 先看几帧
python scripts/voice.py my-series/ep01 --provider edge     # 配音（edge 占位；配好密钥后去掉 --provider）
python scripts/render.py my-series/ep01 all                # 出片
python scripts/new_episode.py my-series 2 --winner HAIRCUT # 第 2 集：状态 + 台词骨架
```

### 注意

- 只学格式，不搬原号的角色、设定、台词和封面字
- 只拿生活习惯开涮，不拿长相、身材开玩笑
- 发布时标注 AI 合成；不要克隆别人的声音（演示里的声音是作者本人的，不要拿去用）

---

## English

**Leo has 30 days until his first ever blind date.** His socks can stand up on their own, his kitchen is forty-seven takeout boxes, and the last time he talked to a woman it was to order a bubble tea: large, no ice. Every episode ends with a vote in the comments (haircut, or the takeout boxes?). The winner gets fixed tomorrow, and once it's fixed, it stays fixed.

This repo is the full workflow for a **daily audience-vote cartoon series**, as a Claude Code skill:

- **Code-animated**: Canvas 2D rendered frame by frame in headless Chrome, encoded with ffmpeg. No video model, no credits.
- **Persistent character**: a `state.json` per episode (hair, stubble, clothes, room). A haircut stays a haircut in every later episode, enforced by code.
- **Your own voice**: narration in your cloned voice (Volcano Engine voice clone; edge-tts as a free placeholder). Whisper word timings drive the pop-up captions and the mouth.
- **Code-made music and sound effects**, synced to the words.

Install: `git clone git@github.com:You-5C24/audience-vote-animation.git ~/.agents/skills/audience-vote-animation`, then tell Claude Code "make Day 2, the winner was HAIRCUT".

License: code in `scripts/` and `engine/` MIT; everything else CC BY-NC 4.0. The voice in the demo is the author's own; please don't reuse it.

## 上游与许可

本项目基于 [ai-vote-series](https://github.com/10291124jcjc-dotcom/ai-vote-series)，原许可证及署名见 [LICENSE](LICENSE)。
