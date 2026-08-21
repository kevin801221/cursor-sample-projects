/**
 * constants.js — 全遊戲「唯一」可調數值來源（鐵律 2：常數置頂）
 *
 * 規則：
 *   1. 場景檔、prefab 檔一律不准寫死數值，全部從這裡 import。
 *   2. 調手感（跳多高、跑多快、敵人多兇）只改這一檔，不用翻場景檔。
 *   3. 這裡只放「數值與關卡資料」，不准放邏輯（那是 scenes/ 與 prefabs/ 的事）。
 *
 * 對照 walkthrough 的舊名稱（同一個東西，改成有命名空間的版本，避免全域撞名）：
 *   PLAYER_SPEED   → PLAYER.SPEED
 *   JUMP_FORCE     → PLAYER.JUMP_VELOCITY
 *   GRAVITY        → PHYSICS.GRAVITY_Y
 *   PLATFORM_HEIGHT→ PLATFORM.HEIGHT
 *   INITIAL_LIVES  → PLAYER.INITIAL_LIVES
 *   ENEMY_PATROL_SPEED → ENEMY.PATROL_SPEED
 */

export const GAME = {
  WIDTH: 800,
  HEIGHT: 600,
  BACKGROUND: '#101a2b',
  FPS: 60, // Phaser 物理固定步進；穿模算術會用到（見 physics-check.mjs）
};

export const PHYSICS = {
  GRAVITY_Y: 900,
  DEBUG: false,

  /**
   * ★★★ 沉默故障開關（鐵律 3 的活教材）★★★
   * true  = 玩家會被 setMaxVelocity() 限速 → 單幀位移小於平台厚度 → 不會穿模
   * false = 不限速 → 高速下墜時單幀位移超過平台厚度 → 直接穿過平台，
   *         而且「不會報錯、console 全綠」，只有親自玩才發現。
   * 課堂 demo：http://localhost:5173/?demo=tunneling （壞的）
   *            http://localhost:5173/?demo=tunneling&fix=1 （修好的）
   */
  CONTINUOUS_COLLISION: true,
};

export const PLAYER = {
  SPEED: 200,
  JUMP_VELOCITY: 520, // ← 課堂 demo：改成 800 存檔，跳躍高度從 150px 變成 300px
  WIDTH: 26,
  HEIGHT: 36,
  INITIAL_LIVES: 3,
  INVULNERABLE_MS: 1000,
  STOMP_SCORE: 50,

  // setMaxVelocity() 用的上限。CONTINUOUS_COLLISION 為 true 時才會套用。
  // 900 / 60fps = 15px 每幀 < PLATFORM.HEIGHT(20px) → 穿不過去。
  // 注意這個值一定要「大於 JUMP_VELOCITY」，不然連起跳都會被削掉，
  // 調 JUMP_VELOCITY 會完全沒感覺（這本身就是個經典沉默故障）。
  MAX_VELOCITY_X: 200,
  MAX_VELOCITY_Y: 900,

  COLOR_BODY: 0x4ade80,
  COLOR_DARK: 0x166534,
  COLOR_VISOR: 0x0f172a,
};

export const ENEMY = {
  PATROL_SPEED: 80,
  WIDTH: 30,
  HEIGHT: 26,
  COLOR_BODY: 0xf87171,
  COLOR_DARK: 0x7f1d1d,
};

export const COLLECTIBLE = {
  RADIUS: 9,
  SCORE: 10,
  BOB_PIXELS: 8,
  BOB_MS: 900,
  COLOR: 0xfacc15,
  COLOR_DARK: 0xa16207,
};

export const PLATFORM = {
  HEIGHT: 20, // ← 穿模算術的關鍵值：單幀位移 > 這個數就有機會穿過去
  TILE_WIDTH: 32,
  COLOR_TOP: 0x94a3b8,
  COLOR_BODY: 0x475569,
  COLOR_LINE: 0x334155,
};

export const DOOR = {
  WIDTH: 36,
  HEIGHT: 56,
  COLOR_LOCKED: 0xdc2626,
  COLOR_OPEN: 0x22c55e,
  COLOR_FRAME: 0x0f172a,
};

export const UI = {
  FONT: '16px monospace',
  FONT_BIG: '34px monospace',
  TEXT_COLOR: '#e2e8f0',
  HINT_COLOR: '#94a3b8',
  PAUSE_OVERLAY_ALPHA: 0.65,
  PAUSE_OVERLAY_COLOR: 0x000000,
  TOAST_MS: 1400,
  DEPTH_UI: 9999, // 遮罩一定要蓋在角色上面
};

export const AUDIO = {
  MASTER_GAIN: 0.18,
  MUSIC_GAIN: 0.06,
  MUSIC_STEP_MS: 260,
  // 四種音效：跳躍、收集、受傷、過關（全部用 WebAudio 合成，不載入任何檔案）
  JUMP: { freq: 420, toFreq: 760, ms: 120, type: 'square' },
  COIN: { freq: 880, toFreq: 1320, ms: 110, type: 'triangle' },
  HURT: { freq: 220, toFreq: 70, ms: 260, type: 'sawtooth' },
  CLEAR: { freq: 523, toFreq: 1046, ms: 420, type: 'square' },
  MUSIC_NOTES: [220, 277, 330, 277, 247, 294, 370, 294],
};

/**
 * 關卡資料。座標約定（照著抄就不會擺歪）：
 *   platforms: x/y = 左上角，width = 寬度，高度一律 PLATFORM.HEIGHT
 *   enemies  : x = 中心，y = 腳底站的那條線（通常就是平台的 y）
 *   coins    : x/y = 中心
 *   door     : x = 中心，y = 門檻踩的那條線（通常就是平台的 y）
 */
export const LEVELS = [
  {
    name: '第 1 關 · 屋頂起步',
    width: 1600,
    spawn: { x: 70, y: 480 },
    platforms: [
      { x: 0, y: 560, width: 520 },
      { x: 620, y: 560, width: 380 },
      { x: 1100, y: 560, width: 500 },
      { x: 300, y: 440, width: 180 },
      { x: 560, y: 350, width: 160 },
      { x: 820, y: 440, width: 200 },
      { x: 1080, y: 340, width: 180 },
      { x: 1360, y: 430, width: 200 },
    ],
    coins: [
      { x: 390, y: 400 },
      { x: 640, y: 310 },
      { x: 900, y: 400 },
      { x: 1170, y: 300 },
      { x: 1450, y: 390 },
    ],
    enemies: [
      { x: 760, y: 560, minX: 640, maxX: 980 },
      { x: 1220, y: 560, minX: 1120, maxX: 1440 },
    ],
    door: { x: 1520, y: 560 },
  },
  {
    name: '第 2 關 · 天台缺口',
    width: 1800,
    spawn: { x: 70, y: 480 },
    platforms: [
      { x: 0, y: 560, width: 300 },
      { x: 420, y: 500, width: 180 },
      { x: 700, y: 560, width: 260 },
      { x: 1060, y: 470, width: 160 },
      { x: 1300, y: 560, width: 500 },
      { x: 200, y: 400, width: 160 },
      { x: 520, y: 320, width: 180 },
      { x: 860, y: 380, width: 160 },
      { x: 1120, y: 290, width: 200 },
      { x: 1460, y: 400, width: 200 },
    ],
    coins: [
      { x: 270, y: 360 },
      { x: 500, y: 460 },
      { x: 600, y: 280 },
      { x: 930, y: 340 },
      { x: 1120, y: 430 },
      { x: 1210, y: 250 },
      { x: 1550, y: 360 },
    ],
    enemies: [
      { x: 780, y: 560, minX: 720, maxX: 940 },
      { x: 1380, y: 560, minX: 1320, maxX: 1600 },
      { x: 1180, y: 290, minX: 1140, maxX: 1300 },
    ],
    door: { x: 1720, y: 560 },
  },
];

/**
 * 穿模示範專用關卡（只有一片沒有缺口的地板）。
 * 因為沒有任何缺口，玩家只要跑到地板下面，就「一定」是穿過去的——
 * 不會跟「掉進坑裡」搞混，課堂上不用解釋第二次。
 */
export const TUNNEL_LAB = {
  name: '穿模實驗室 · ?demo=tunneling',
  width: 800,
  spawn: { x: 400, y: 60 },
  platforms: [{ x: 0, y: 500, width: 800 }],
  coins: [],
  enemies: [],
  door: null,
  /** 每次投放給玩家的初速度（px/s）。極高 → 單幀位移超過平台厚度 */
  DROP_VELOCITY_Y: 5000,
  DROP_INTERVAL_MS: 1500,
};

/**
 * DEMO：課堂用的 URL 參數旗標，由 main.js 解析後覆寫上面的常數。
 *   ?demo=tunneling        沉默故障示範（不限速，會穿模）
 *   ?demo=tunneling&fix=1  修好的版本（限速，不穿模）
 *   ?demo=level2           直接從第 2 關開始（講師不用真的先破第 1 關）
 */
export const DEMO = {
  MODE: 'normal', // 'normal' | 'tunneling'
  START_LEVEL: 1,
  SKIP_MENU: false, // 帶了 demo 參數就跳過主選單，直接進遊戲
};
