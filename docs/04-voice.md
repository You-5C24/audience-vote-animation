# 04 · 配音

原号作者是自己配音的。我们用 TTS：录一段样本做一次声音克隆，以后每集的台词都用这个音色合成。

## 三种

| | 是什么 | 要什么 |
| --- | --- | --- |
| `minimax`（本机默认） | MiniMax `t2a_v2`，`moss_audio_` 克隆音色。中文自然，英文发音也清楚 | `MINIMAX_API_KEY`、`MINIMAX_VOICE_ID` 写进 `.env`（系列文件夹或任一上级目录，或 `~/.vote-series/.env`） |
| `volc` | 火山引擎「声音复刻」，你自己的声音 | 控制台复刻一次，把 `VOLC_API_KEY`、`VOLC_SPEAKER_ID`（S_ 开头）写进 `.env` |
| `edge`（占位） | edge-tts 免费 AI 声音，只用来先看样片 | 不要密钥 |

本机已经配好：

```
~/.vote-series/.env     # 权限 600，已在 .gitignore
MINIMAX_API_KEY=...
MINIMAX_VOICE_ID=moss_audio_59d1aa8a-d212-11f1-b609-be0318ac13bc
MINIMAX_TTS_MODEL=speech-2.8-hd
MINIMAX_TTS_BASE_URL=https://api.minimax.cn
```

`series.json` 里写 `"voice": {"provider": "minimax"}` 就默认走 MiniMax。

```bash
python scripts/voice.py EP --test "This is Leo."     # 先试一句
python scripts/voice.py EP                            # 整集：合成 + 去首尾静音 + 对齐每个词 + 嘴型
python scripts/voice.py EP --provider edge            # 没配密钥时占位
```

- 每句单独合成、有缓存：改哪句只重新合成哪句。缓存 key 里带 `voice_id`，换音色不会误用旧音频
  - 想强制重合成某句：删掉 `EP/voice/<id>_*.mp3`
- `faster-whisper`（CPU）对出每个词的时间，字幕和道具都卡这个时间；顺便用它听一遍：识别结果和台词对不上，多半是发音有问题，换个说法重合成
- `script.json` 里每句的 `gap` 是这句后面停多久；投票、揭晓前多停 0.5 秒
- MiniMax 中文音色读阿拉伯数字容易读得生硬：写成汉字（三十、四十七）
- MiniMax 返回 **HTTP 200 也可能是失败**，真错误码在 `base_resp.status_code`；`voice.py` 已经处理

## 混音：音乐音量必须低于人声 13–15 dB

这是一条硬指标，不是听感偏好。旁白片里音乐一旦接近人声电平，观众第一反应就是「背景音乐太吵」。

**在哪里量：** `Mixer.write()` 会把整条轨归一化到 −1 dBFS，所以**成片里量出来的人声-音乐比值是假的**——两边一起被缩放，比值恒定。必须量归一化之前的原始 mix：

```python
import audio_lib, numpy as np
def raw_write(self, path, reverb=0.06, fade=0.35):
    np.save('/tmp/mix_raw.npy', np.stack([self.L, self.R], 1))
audio_lib.Mixer.write = raw_write      # 然后跑 audio.py
```

分别取「人声开口帧的 RMS」和「台词间隙的 RMS」，两者相减应在 −13 到 −15 dB。

**参考增益**（`audio.py` 里的 `g=`）：贝斯 0.06、琶音 0.019、踩镲 0.013、拍手 0.015。这套数值实测落在 −15.6 dB。想更轻就继续等比往下压，别只压某一个声部——只压贝斯会让人声显得更空。

## 成片前必须核对：音轨时长 == 旁白时长

`render.py all` 不检查这件事。`audio.py` 报 `wrote soundtrack.wav` 才算成功；如果 SFX 段被改坏、`mix.write()` 被删掉，它会**静默跳过**，留下上一集的旧音轨，成片于是被截短到旧音轨的长度，而画面帧齐全、也不会报错。

```bash
python3 -c "import wave; w=wave.open('vo.wav'); print('vo', w.getnframes()/w.getframerate())
w=wave.open('soundtrack.wav'); print('st', w.getnframes()/w.getframerate())"
ffprobe -v error -show_entries format=duration -of csv=p=0 *.mp4
```

三个数字必须一致（±0.05s）。不一致就是音轨没重生成。

## 注意

- 密钥是你的，只放 `.env`，不要打印、不要提交到 GitHub（`.gitignore` 已经排除 `.env`）
- 国内平台发布要勾选「AI 生成 / 合成」声明；海外平台按各自规则标注
- 不要克隆别人的声音
