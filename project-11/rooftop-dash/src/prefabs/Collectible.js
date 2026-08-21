/**
 * prefabs/Collectible.js — 金幣。不受重力、不會被推動，只等著被 overlap 撿走。
 */
import Phaser from 'phaser';
import { COLLECTIBLE } from '../constants.js';

export default class Collectible extends Phaser.Physics.Arcade.Sprite {
  constructor(scene, x, y) {
    super(scene, x, y, 'coin');
    scene.add.existing(this);
    scene.physics.add.existing(this);

    this.body.setAllowGravity(false);
    this.body.setImmovable(true);
    this.body.setCircle(COLLECTIBLE.RADIUS);

    // 上下浮動的補間動畫（暫停時會被 tweens.pauseAll() 一起停住）
    this.bob = scene.tweens.add({
      targets: this,
      y: y - COLLECTIBLE.BOB_PIXELS,
      duration: COLLECTIBLE.BOB_MS,
      yoyo: true,
      repeat: -1,
      ease: 'Sine.easeInOut',
    });
  }

  collect() {
    if (this.bob) this.bob.remove();
    this.destroy();
  }
}
