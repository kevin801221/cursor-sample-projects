/**
 * main.js — 全專案「唯一」的 Phaser Game 實例（.cursor/rules/00-architecture.mdc 禁止第二個）
 *
 * 這一檔只做兩件事：
 *   1. 解析課堂 demo 用的 URL 參數，覆寫 constants.js 的數值
 *   2. 建立 Game 實例
 * 遊戲邏輯一律不寫在這裡。
 */
import Phaser from 'phaser';
import MenuScene from './scenes/MenuScene.js';
import PlayScene from './scenes/PlayScene.js';
import GameOverScene from './scenes/GameOverScene.js';
import { GAME, PHYSICS, DEMO } from './constants.js';

/**
 * 課堂遙控器：URL 參數 → 覆寫常數。
 * 注意這裡「只改常數」，沒有任何一行遊戲邏輯是 demo 專用的——
 * 壞掉的版本跟修好的版本走的是同一份程式碼路徑，教學價值才不打折。
 */
function applyDemoFlags(params) {
  const demo = params.get('demo');

  if (demo === 'tunneling') {
    DEMO.MODE = 'tunneling';
    // fix=1 才把限速打開。沒帶 fix → 不限速 → 高速下墜直接穿過平台（沉默故障）
    PHYSICS.CONTINUOUS_COLLISION = params.get('fix') === '1';
  }

  const levelMatch = /^level(\d+)$/.exec(demo || '');
  if (levelMatch) DEMO.START_LEVEL = Number(levelMatch[1]);
  if (params.has('level')) DEMO.START_LEVEL = Number(params.get('level'));
  DEMO.SKIP_MENU = !!demo || params.has('level');

  // ?cc=0 可以在正常關卡裡把限速關掉（給想自己玩壞它的學生）
  if (params.get('cc') === '0') PHYSICS.CONTINUOUS_COLLISION = false;

  console.log(
    `[Rooftop Dash] MODE=${DEMO.MODE} START_LEVEL=${DEMO.START_LEVEL} ` +
      `CONTINUOUS_COLLISION=${PHYSICS.CONTINUOUS_COLLISION}`
  );
}

applyDemoFlags(new URLSearchParams(window.location.search));

const config = {
  type: Phaser.AUTO,
  parent: 'game',
  width: GAME.WIDTH,
  height: GAME.HEIGHT,
  backgroundColor: GAME.BACKGROUND,
  pixelArt: false,
  scale: {
    mode: Phaser.Scale.FIT,
    autoCenter: Phaser.Scale.CENTER_BOTH,
  },
  physics: {
    default: 'arcade',
    arcade: { gravity: { y: PHYSICS.GRAVITY_Y }, debug: PHYSICS.DEBUG },
  },
  scene: [MenuScene, PlayScene, GameOverScene],
};

// 全專案唯一的 Game 實例。掛到 window 是為了讓課堂上能直接在 DevTools 查狀態，例如：
//   __game.registry.get('lives')    ← 驗證命數有沒有真的存進 registry（沉默故障的抓法）
window.__game = new Phaser.Game(config);
