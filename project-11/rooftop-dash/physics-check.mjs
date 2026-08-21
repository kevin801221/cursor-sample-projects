/**
 * physics-check.mjs — 最小可跑的自我檢查（不裝測試框架，node 直接跑）
 *
 *   npm run check    或    node physics-check.mjs
 *
 * 檢查兩件在課堂上會翻車的事：
 *   A. 穿模算術：限速後單幀位移真的小於平台厚度；?demo=tunneling 的極速真的會穿過去
 *   B. 關卡資料：金幣不會卡在平台裡、敵人巡邏範圍不會走出平台、門要站在平台上
 * 這兩種錯都「不會報錯」，只會讓課堂上的遊戲怪怪的——所以用一支腳本先擋掉。
 */
import {
  GAME,
  PLAYER,
  ENEMY,
  COLLECTIBLE,
  PLATFORM,
  DOOR,
  LEVELS,
  TUNNEL_LAB,
} from './src/constants.js';

let failures = 0;
function check(label, condition, detail = '') {
  if (condition) {
    console.log(`  ✅ ${label}`);
  } else {
    failures += 1;
    console.log(`  ❌ ${label}${detail ? `　→ ${detail}` : ''}`);
  }
}

const stepPx = (velocity) => velocity / GAME.FPS;
/** Arcade Physics 是離散 AABB：要整個身體在一幀內跨過平台，才會完全漏檢 */
const TUNNEL_THRESHOLD = PLATFORM.HEIGHT + PLAYER.HEIGHT;

console.log('\n【A】穿模算術（鐵律 3 的沉默故障）');
check(
  `限速後每幀位移 ${stepPx(PLAYER.MAX_VELOCITY_Y).toFixed(1)}px < 平台厚度 ${PLATFORM.HEIGHT}px`,
  stepPx(PLAYER.MAX_VELOCITY_Y) < PLATFORM.HEIGHT,
  '把 PLAYER.MAX_VELOCITY_Y 調小，或把 PLATFORM.HEIGHT 調大'
);
check(
  `MAX_VELOCITY_Y(${PLAYER.MAX_VELOCITY_Y}) > JUMP_VELOCITY(${PLAYER.JUMP_VELOCITY})：起跳不會被限速削掉`,
  PLAYER.MAX_VELOCITY_Y > PLAYER.JUMP_VELOCITY,
  '不然調 JUMP_VELOCITY 會完全沒感覺'
);
check(
  `?demo=tunneling 的每幀位移 ${stepPx(TUNNEL_LAB.DROP_VELOCITY_Y).toFixed(0)}px > ${TUNNEL_THRESHOLD}px：示範真的穿得過去`,
  stepPx(TUNNEL_LAB.DROP_VELOCITY_Y) > TUNNEL_THRESHOLD,
  '把 TUNNEL_LAB.DROP_VELOCITY_Y 調大'
);

console.log('\n【B】關卡資料');
const overlaps = (a, b) =>
  a.x < b.x + b.w && a.x + a.w > b.x && a.y < b.y + b.h && a.y + a.h > b.y;

LEVELS.forEach((level, i) => {
  const n = i + 1;
  const rects = level.platforms.map((p) => ({ x: p.x, y: p.y, w: p.width, h: PLATFORM.HEIGHT }));

  check(`第 ${n} 關：有金幣、有敵人、有出口門`, level.coins.length > 0 && level.enemies.length > 0 && !!level.door);

  const stuckCoin = level.coins.find((c) =>
    rects.some((r) =>
      overlaps(
        {
          x: c.x - COLLECTIBLE.RADIUS,
          y: c.y - COLLECTIBLE.RADIUS - COLLECTIBLE.BOB_PIXELS,
          w: COLLECTIBLE.RADIUS * 2,
          h: COLLECTIBLE.RADIUS * 2 + COLLECTIBLE.BOB_PIXELS,
        },
        r
      )
    )
  );
  check(`第 ${n} 關：沒有金幣卡在平台裡`, !stuckCoin, stuckCoin && JSON.stringify(stuckCoin));

  // 每顆金幣都要浮在某片平台上方 20~150px，玩家跳得到（跳躍高度約 150px）
  const jumpHeight = (PLAYER.JUMP_VELOCITY * PLAYER.JUMP_VELOCITY) / (2 * 900);
  const unreachable = level.coins.find(
    (c) =>
      !rects.some((r) => {
        const above = r.y - c.y;
        return c.x > r.x && c.x < r.x + r.w && above > 20 && above < jumpHeight;
      })
  );
  check(`第 ${n} 關：每顆金幣都在某片平台上方且跳得到`, !unreachable, unreachable && JSON.stringify(unreachable));

  const badEnemy = level.enemies.find(
    (e) =>
      e.minX >= e.maxX ||
      !rects.some(
        (r) => r.y === e.y && e.minX - ENEMY.WIDTH / 2 >= r.x && e.maxX + ENEMY.WIDTH / 2 <= r.x + r.w
      )
  );
  check(`第 ${n} 關：敵人巡邏範圍都在平台上（不會走空）`, !badEnemy, badEnemy && JSON.stringify(badEnemy));

  const doorOk = rects.some(
    (r) =>
      r.y === level.door.y &&
      level.door.x - DOOR.WIDTH / 2 >= r.x &&
      level.door.x + DOOR.WIDTH / 2 <= r.x + r.w
  );
  check(`第 ${n} 關：出口門站在平台上`, doorOk, JSON.stringify(level.door));

  const spawnOk = level.spawn.x > 0 && level.spawn.x < level.width && level.spawn.y < GAME.HEIGHT;
  check(`第 ${n} 關：出生點在世界範圍內`, spawnOk);
});

console.log(
  failures === 0
    ? `\n全部通過（${LEVELS.length} 關）。可以上課了。\n`
    : `\n有 ${failures} 項沒過，先修好再上課。\n`
);
process.exit(failures === 0 ? 0 : 1);
