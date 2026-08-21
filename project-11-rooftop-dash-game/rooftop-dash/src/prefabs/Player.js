/**
 * prefabs/Player.js — 玩家角色。
 * 只放「自己的初始化與方法」，不去讀場景的分數／命數（那些在 registry）。
 */
import Phaser from 'phaser';
import { PLAYER, PHYSICS } from '../constants.js';
import { horizontal, jumpPressed } from '../input.js';

export default class Player extends Phaser.Physics.Arcade.Sprite {
  constructor(scene, x, y) {
    super(scene, x, y, 'player');
    scene.add.existing(this);
    scene.physics.add.existing(this);

    this.setCollideWorldBounds(true);
    this.setBounce(0);
    // 動態 body 用 setSize 就會即時更新；refreshBody() 是靜態 body（平台、門）專用，
    // 在動態 body 上呼叫會直接 TypeError（walkthrough §9 那條要看清楚是哪一種 body）
    this.body.setSize(PLAYER.WIDTH, PLAYER.HEIGHT);
    this.invulnerableUntil = 0;

    this.applyCollisionSafety();
  }

  /**
   * ★ 本課的靈魂三行 ★
   * 開了 CONTINUOUS_COLLISION 就限速，單幀位移永遠小於平台厚度 → 不會穿模；
   * 關掉就是 Phaser 預設的 10000（等於沒限速）→ 高速下墜穿過平台，而且不會報錯。
   * 兩條路走的是同一個函式，差別只有 constants.js 裡那一個布林值。
   */
  applyCollisionSafety() {
    if (PHYSICS.CONTINUOUS_COLLISION) {
      this.body.setMaxVelocity(PLAYER.MAX_VELOCITY_X, PLAYER.MAX_VELOCITY_Y);
    } else {
      this.body.setMaxVelocity(10000, 10000);
    }
  }

  /** 每幀讀輸入 → 設速度。跳躍只有站在地上時才算數 */
  handleInput(keys, audio) {
    const dir = horizontal(keys);
    this.setVelocityX(dir * PLAYER.SPEED);
    if (dir !== 0) this.setFlipX(dir < 0);

    if (jumpPressed(keys) && this.body.blocked.down) {
      this.setVelocityY(-PLAYER.JUMP_VELOCITY);
      audio.jump();
    }
  }

  get isInvulnerable() {
    return this.scene.time.now < this.invulnerableUntil;
  }

  /** 受傷：進入無敵時間並閃爍，避免站在敵人身上被連續扣光三條命 */
  hurt() {
    this.invulnerableUntil = this.scene.time.now + PLAYER.INVULNERABLE_MS;
    this.scene.tweens.add({
      targets: this,
      alpha: { from: 0.2, to: 1 },
      duration: PLAYER.INVULNERABLE_MS / 5,
      repeat: 4,
      onComplete: () => this.setAlpha(1),
    });
  }

  /** 傳送要用 body.reset()，直接改 x/y 物理 body 不一定跟得上（會變成鬼影） */
  respawn(x, y) {
    this.body.reset(x, y);
    this.setAlpha(1);
  }
}
