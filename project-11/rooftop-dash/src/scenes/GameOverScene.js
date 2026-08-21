/**
 * scenes/GameOverScene.js — 結算畫面。分數與關卡都從 registry 讀，不從上一個場景傳。
 */
import Phaser from 'phaser';
import { GAME, UI } from '../constants.js';
import { createTextures } from '../assets/textures.js';

export default class GameOverScene extends Phaser.Scene {
  constructor() {
    super('GameOverScene');
  }

  create() {
    createTextures(this);
    // 這裡用 keydown 事件而不是 update 裡輪詢 JustDown：
    // 結算畫面只等一個按鍵，事件不會因為「按太快、按下與放開落在同一幀」而漏掉
    this.input.keyboard.once('keydown-R', () => this.scene.start('PlayScene', { level: 1, fresh: true }));
    this.input.keyboard.once('keydown-M', () => this.scene.start('MenuScene'));

    const won = this.registry.get('won');
    this.add.image(0, 0, 'sky').setOrigin(0, 0);
    this.add.tileSprite(0, GAME.HEIGHT - 260, GAME.WIDTH, 260, 'skyline').setOrigin(0, 0);

    this.add
      .text(GAME.WIDTH / 2, 180, won ? '全部關卡完成！' : 'GAME OVER', {
        font: '46px monospace',
        color: won ? '#4ade80' : '#f87171',
      })
      .setOrigin(0.5);

    this.add
      .text(
        GAME.WIDTH / 2,
        290,
        [
          `分數 Score : ${this.registry.get('score')}`,
          `關卡 Level : ${this.registry.get('level')}`,
          `剩餘命數 Lives : ${Math.max(0, this.registry.get('lives'))}`,
        ].join('\n'),
        { font: '20px monospace', color: UI.TEXT_COLOR, align: 'center', lineSpacing: 10 }
      )
      .setOrigin(0.5);

    const hint = this.add
      .text(GAME.WIDTH / 2, 430, '按 R 重新開始　　按 M 回主選單', {
        font: '20px monospace',
        color: '#facc15',
      })
      .setOrigin(0.5);
    this.tweens.add({ targets: hint, alpha: 0.35, duration: 700, yoyo: true, repeat: -1 });
  }
}
