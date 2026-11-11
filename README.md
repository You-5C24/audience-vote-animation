# Audience Vote Animation · 观众投票动画

这是 [You-5C24](https://github.com/You-5C24) 用来制作《三十天搬出去》的 Codex Skill。LT 要在三十天内搬出去。每集推进一件事，片尾请观众二选一，下一集用具体行动兑现投票，并把已经发生的变化带进后续剧情。

## 这项技能能做什么

- **接续连载**：读取实发片尾和结票记录，沿用角色状态与已确认的剧情。零票或平票按系列约定推进。
- **从分镜到成片**：配音前检查首屏、主戏和次集承诺，先预览最难读的镜头，再用 Canvas 2D 逐帧渲染、ffmpeg 合成竖屏视频。
- **配音与字幕**：正式旁白默认用 MiniMax 克隆音色。Whisper 对齐台词和字幕，音效可按台词时间点编排。
- **准备发布素材**：检查投票词在旁白、画面和发布文案中的一致性，按系列需要制作封面。

## 安装到 Codex

```sh
git clone git@github.com:You-5C24/audience-vote-animation.git ~/.agents/skills/audience-vote-animation
ln -s ~/.agents/skills/audience-vote-animation ~/.codex/skills/audience-vote-animation
```

已安装时，在技能目录运行 `git pull` 更新。制作需要 Python、ffmpeg、Playwright 和 Chrome。正式合成前，将自己的 MiniMax API Key 配置到 `~/.vote-series/.env`。具体依赖和恢复步骤见 [安装说明](INSTALL_LOCAL.md)。

## 在聊天里使用

> 用 $audience-vote-animation 做《三十天搬出去》下一集。先核对实发片尾和结票记录，给我出片卡和主戏预览。

也可以用它新建一个连载，或修改现有分集的旁白、镜头和投票选项。入口是 [SKILL.md](SKILL.md)，仓库里的 [相亲系列](examples/30-days-to-the-date) 是用于说明项目结构的示例。

## 上游与许可

本项目基于 [ai-vote-series](https://github.com/10291124jcjc-dotcom/ai-vote-series) 定制，保留原始许可证和署名，见 [LICENSE](LICENSE)。
