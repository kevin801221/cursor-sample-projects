/**
 * prefabs/Enemy.js — 在平台上來回巡邏的敵人。
 * 巡邏範圍由關卡資料的 minX / maxX 決定，速度來自 constants.js。
 */
import Phaser from 'phaser';
import { ENEMY, PLAYER } from '../constants.js';

export default class Enemy extends Phaser.Physics.Arcade.Sprite {
  /** @param cfg {{x:number,y:number,minX:number,maxX:number}} y 是腳底那條線 */
  constructor(scene, cfg) {
    super(scene, cfg.x, cfg.y - ENEMY.HEIGHT / 2, 'enemy');
    scene.add.existing(this);
    scene.physics.add.existing(this);

    this.minX = cfg.minX;
    this.maxX = cfg.maxX;
    this.setBounce(0);
    this.body.setSize(ENEMY.WIDTH, ENEMY.HEIGHT); // 動態 body 不需要 refreshBody
    // 敵人也要限速，理由跟玩家一樣：避免單幀位移超過平台厚度
    this.body.setMaxVelocity(ENEMY.PATROL_SPEED, PLAYER.MAX_VELOCITY_Y);
    this.setVelocityX(ENEMY.PATROL_SPEED);
  }

  /** 每幀呼叫：走到邊界就轉身 */
  patrol() {
    if (this.x <= this.minX && this.body.velocity.x <= 0) {
      this.setVelocityX(ENEMY.PATROL_SPEED);
      this.setFlipX(false);
    } else if (this.x >= this.maxX && this.body.velocity.x >= 0) {
      this.setVelocityX(-ENEMY.PATROL_SPEED);
      this.setFlipX(true);
    }
  }

  /** 被踩扁：縮一下再消失 */
  squash() {
    this.body.enable = false;
    this.scene.tweens.add({
      targets: this,
      scaleY: 0.2,
      alpha: 0,
      duration: 160,
      onComplete: () => this.destroy(),
    });
  }
}

/**
 * 踩頭判定（純函式，方便在 physics-check.mjs 裡驗）。
 * 條件：玩家正在往下掉，而且玩家的腳還在敵人身體的上半部。
 */
export function isStomp(playerBottom, playerVelocityY, enemyTop, enemyHeight) {
  return playerVelocityY > 0 && playerBottom <= enemyTop + enemyHeight * 0.5;
}
