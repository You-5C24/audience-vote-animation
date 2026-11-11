# 05 · 发布和读票

## 节奏

- 每天一集，固定时间发（观众会回来看结果）
- 平台：IG Reels、TikTok、YouTube Shorts 都可以；同一条视频可以三个平台一起发，票以主平台为准
- 第 1 集之前就把封面风格定下来：大字写「DAY N」+ 一句昨天改了什么（「HE FINALLY GOT A HAIRCUT」）+ 一个绿/红小标签（HAIR: FIXED）

## 文案模板（英文）

```
Day 2 of 30 🗓️

Leo has 29 days until his first ever blind date. Yesterday you picked HAIRCUT, so he finally saw a barber. The hair is fixed for good. The boxes are not.

BOXES or SOCKS: which one should Leo fix next? The winner gets fixed in Day 3, and every fix stays for good.

Follow so you don't miss the glow-up. Day 30 is going to be unreal.

#30daystothedate #glowup #animation
```

## 读票

- 二选一：数评论里两个词各出现多少次（大小写、复数都算），票数接近就看点赞最多的那条
- 「点赞最多的评论决定」：取点赞最高的那条；不安全、不合适、做不出来的跳过，用下一条，并在下一集里说一句为什么
- 把结果写进系列的 `log.md`：Day、两个选项、赢家、票数或那条评论、发布时间、播放、评论数
- 然后 `python scripts/new_episode.py SERIES N --winner XXX`

## 别做

- 不搬原号的角色、设定（「同学聚会」「James」）、面板文字和封面字
- 不在视频里放真实品牌、真人
- 不承诺收入；卖教程时写清楚「Results vary」
