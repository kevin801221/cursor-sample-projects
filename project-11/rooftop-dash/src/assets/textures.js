/**
 * assets/textures.js — 全部美術都用 Phaser Graphics 「畫」出來，再 generateTexture 變成貼圖。
 *
 * 為什麼不放 png？因為這堂課要能離線跑、不能依賴任何外部素材下載。
 * 副作用是好處：所有顏色與尺寸都來自 constants.js，改一個數字整個畫面跟著變。
 */
import { PLAYER, ENEMY, COLLECTIBLE, PLATFORM, DOOR, GAME } from '../constants.js';

/** 畫完就丟的離屏 Graphics */
function draw(scene, key, width, height, painter) {
  if (scene.textures.exists(key)) return key;
  const g = scene.make.graphics({ add: false });
  painter(g);
  g.generateTexture(key, width, height);
  g.destroy();
  return key;
}

/** 平台寬度不固定，所以按寬度生成（同寬度只生一次） */
export function platformTexture(scene, width) {
  const h = PLATFORM.HEIGHT;
  return draw(scene, `platform-${width}`, width, h, (g) => {
    g.fillStyle(PLATFORM.COLOR_BODY, 1);
    g.fillRect(0, 0, width, h);
    g.fillStyle(PLATFORM.COLOR_TOP, 1);
    g.fillRect(0, 0, width, 4); // 頂面亮邊，讓學生一眼看出「可以站的那一面」
    g.lineStyle(1, PLATFORM.COLOR_LINE, 1);
    for (let x = PLATFORM.TILE_WIDTH; x < width; x += PLATFORM.TILE_WIDTH) {
      g.lineBetween(x, 4, x, h);
    }
  });
}

export function createTextures(scene) {
  const pw = PLAYER.WIDTH;
  const ph = PLAYER.HEIGHT;
  draw(scene, 'player', pw, ph, (g) => {
    g.fillStyle(PLAYER.COLOR_DARK, 1);
    g.fillRoundedRect(0, 0, pw, ph, 6);
    g.fillStyle(PLAYER.COLOR_BODY, 1);
    g.fillRoundedRect(1, 1, pw - 2, ph - 5, 6);
    g.fillStyle(PLAYER.COLOR_VISOR, 1);
    g.fillRoundedRect(5, 8, pw - 10, 9, 3); // 面罩，用來看出面向左右
    g.fillRect(4, ph - 4, 6, 4);
    g.fillRect(pw - 10, ph - 4, 6, 4);
  });

  const ew = ENEMY.WIDTH;
  const eh = ENEMY.HEIGHT;
  draw(scene, 'enemy', ew, eh, (g) => {
    g.fillStyle(ENEMY.COLOR_DARK, 1);
    g.fillRoundedRect(0, 0, ew, eh, 8);
    g.fillStyle(ENEMY.COLOR_BODY, 1);
    g.fillRoundedRect(1, 1, ew - 2, eh - 4, 8);
    g.fillStyle(0xffffff, 1);
    g.fillCircle(ew * 0.32, eh * 0.4, 4);
    g.fillCircle(ew * 0.68, eh * 0.4, 4);
    g.fillStyle(0x0f172a, 1);
    g.fillCircle(ew * 0.32, eh * 0.4, 2);
    g.fillCircle(ew * 0.68, eh * 0.4, 2);
  });

  const r = COLLECTIBLE.RADIUS;
  draw(scene, 'coin', r * 2, r * 2, (g) => {
    g.fillStyle(COLLECTIBLE.COLOR_DARK, 1);
    g.fillCircle(r, r, r);
    g.fillStyle(COLLECTIBLE.COLOR, 1);
    g.fillCircle(r, r, r - 2);
    g.fillStyle(0xfffbeb, 1);
    g.fillCircle(r - 2, r - 3, 2);
  });

  for (const [key, color] of [
    ['door-locked', DOOR.COLOR_LOCKED],
    ['door-open', DOOR.COLOR_OPEN],
  ]) {
    draw(scene, key, DOOR.WIDTH, DOOR.HEIGHT, (g) => {
      g.fillStyle(DOOR.COLOR_FRAME, 1);
      g.fillRoundedRect(0, 0, DOOR.WIDTH, DOOR.HEIGHT, 5);
      g.fillStyle(color, 1);
      g.fillRoundedRect(3, 3, DOOR.WIDTH - 6, DOOR.HEIGHT - 6, 4);
      g.fillStyle(0xfef3c7, 1);
      g.fillCircle(DOOR.WIDTH - 10, DOOR.HEIGHT / 2, 3);
    });
  }

  // 背景：漸層天空 + 兩層剪影大樓（視差用）
  draw(scene, 'sky', GAME.WIDTH, GAME.HEIGHT, (g) => {
    g.fillGradientStyle(0x0b1220, 0x0b1220, 0x27406b, 0x27406b, 1);
    g.fillRect(0, 0, GAME.WIDTH, GAME.HEIGHT);
    g.fillStyle(0xfde68a, 1);
    for (let i = 0; i < 40; i++) {
      const x = (i * 97) % GAME.WIDTH;
      const y = (i * 53) % (GAME.HEIGHT * 0.55);
      g.fillRect(x, y, 2, 2); // 星星（用固定算式產生，不需要亂數種子）
    }
  });

  draw(scene, 'skyline', 400, 260, (g) => {
    g.fillStyle(0x172033, 1);
    const widths = [54, 38, 70, 46, 62, 44, 58, 28];
    let x = 0;
    widths.forEach((w, i) => {
      const h = 90 + ((i * 37) % 150);
      g.fillRect(x, 260 - h, w, h);
      g.fillStyle(0x243049, 1);
      for (let wy = 260 - h + 10; wy < 250; wy += 18) {
        for (let wx = x + 6; wx < x + w - 8; wx += 14) g.fillRect(wx, wy, 5, 7);
      }
      g.fillStyle(0x172033, 1);
      x += w + 4;
    });
  });
}
