# Rooftop Dash — Game Design Document

## 核心玩法
- 角色跳過屋頂平台躲敵人、收金幣
- 目標：收集當前關卡所有金幣 → 打開出口門 → 進下一關

## 操作
- ← → 移動
- SPACE 跳躍
- P 暫停 / R 重來
- M 返回菜單

## 敵人與碰撞
- 敵人在平台上來回巡邏
- 碰到敵人扣一命（三條命遊戲結束）
- 踩敵人頭會消滅敵人、得分

## 物件
- 平台：靜態碰撞，玩家在上面跳躍
- 敵人：移動碰撞，傷害玩家
- 金幣：收集物，吃完才開門
- 出口門：只有收完金幣才可通行

## 關卡
- 至少 2 關（Scope Cut：不做動態生成、不做無限模式）

## Scope Cut（本版本不做）
- ✗ 攻擊系統（踩敵人頭除外）
- ✗ Boss 戰
- ✗ 武器或道具
- ✗ 多人模式
- ✗ 動態地圖生成
- ✗ 成就、排行榜

## 關鍵數值（全部在 src/constants.js，改手感只改那一檔）
| 數值 | 常數 | 目前值 |
|---|---|---|
| 移動速度 | `PLAYER.SPEED` | 200 |
| 跳躍力 | `PLAYER.JUMP_VELOCITY` | 520 |
| 重力 | `PHYSICS.GRAVITY_Y` | 900 |
| 速度上限（防穿模） | `PLAYER.MAX_VELOCITY_X / Y` | 200 / 900 |
| 平台厚度 | `PLATFORM.HEIGHT` | 20 |
| 初始命數 | `PLAYER.INITIAL_LIVES` | 3 |
| 敵人巡邏速度 | `ENEMY.PATROL_SPEED` | 80 |
| 金幣分數 / 踩頭分數 | `COLLECTIBLE.SCORE` / `PLAYER.STOMP_SCORE` | 10 / 50 |

## 離線鐵則（這堂課的額外限制）
- 不下載任何圖片與音效：美術用 Phaser Graphics 畫完 `generateTexture()`，
  音效用 WebAudio 合成（跳躍、收集、受傷、過關四種 + 背景音樂）
- 課堂 demo 一律用 URL 參數切換，且只覆寫 constants.js 的值：
  `?demo=level2`、`?demo=tunneling`、`?demo=tunneling&fix=1`
