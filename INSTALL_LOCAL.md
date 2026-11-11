# audience-vote-animation 安装说明（本机）

原仓库：https://github.com/10291124jcjc-dotcom/ai-vote-series

## 从 GitHub 恢复

```sh
git clone git@github.com:You-5C24/audience-vote-animation.git ~/.agents/skills/audience-vote-animation
ln -s ~/.agents/skills/audience-vote-animation ~/.codex/skills/audience-vote-animation
```

按需为 Claude Code 在 `~/.claude/skills/` 建立同名链接。MiniMax API Key 从自己的凭据备份恢复到 `~/.vote-series/.env`。

## 位置

```
~/.agents/skills/audience-vote-animation/      实际文件
~/.claude/skills/audience-vote-animation       符号链接（和 lark-* 一致）
~/.vote-series/.env                   MiniMax 凭据（600）
```

## 本机做的改动（相对上游）

1. **voice.py 加了 minimax provider**：`synth_minimax()` 调 `POST {base}/v1/t2a_v2`，
   返回的 `data.audio` 是 **hex 不是 base64**（`binascii.unhexlify`），
   错误码在 `base_resp.status_code`（HTTP 永远 200）。用 `extra_info.audio_size` 校验落盘大小。
   缓存 key 从 `edge_voice` 改成 `voice_id`/`speaker_id`，换音色不会误用旧音频。
2. **engine/index.html 支持中文 UI**：`state.json` 里 `lang` 驱动 `T` 表，
   面板「第 N/30 天」、投票标题、结尾「明天 · 第 N 天」都跟着切。
3. **new_episode.py 把 `lang`/`days`/`meter` 从 series.json 写进每集 state.json**，
   否则引擎只看得到 state.json，读不到 series.json。
4. 字体加了 `PingFang SC` 等中文字族（原来只有 Arial Black，中文会掉字重）。
5. docs/04-voice.md 改成 MiniMax 为主。

**注意**：每集目录里有自己的一份 `index.html`。改了 `engine/index.html` 之后，
新集是从上一集拷贝的，所以改动只对「新建系列」或手动 `cp` 生效。

## 依赖（都已装好，python3.10 + user site）

numpy scipy pillow playwright av faster-whisper edge-tts；ffmpeg 9.0.2；Chrome 和 Edge 都在。
`--only-binary=:all:` 装 av，因为本机没 pkg-config，PyAV 源码编译会失败。
pip 连不上官方源，用 `-i https://pypi.tuna.tsinghua.edu.cn/simple`。

## 验证过

2026-11-08 跑通全链路：new_series → voice.py（MiniMax 合成 + whisper 逐词对齐）
→ render.py all → 1080×1920 / 30fps / H.264 18.9s / 音量 -15.9dB。
