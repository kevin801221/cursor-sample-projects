/**
 * scenes/MenuScene.js — 主選單。只負責「顯示標題 + 等玩家按開始」。
 */
import Phaser from 'phaser';
import { GAME, UI, DEMO } from '../constants.js';
import { createTextures } from '../assets/textures.js';

export default class MenuScene extends Phaser.Scene {
  constructor() {
    super('MenuScene');
  }

  create() {
    createTextures(this);

    // 帶了課堂 demo 參數就直接進遊戲，講師不用先點一次開始
    if (DEMO.SKIP_MENU) {
      this.scene.start('PlayScene', { level: DEMO.START_LEVEL, fresh: true });
      return;
    }

    this.add.image(0, 0, 'sky').setOrigin(0, 0);
    this.add.tileSprite(0, GAME.HEIGHT - 260, GAME.WIDTH, 260, 'skyline').setOrigin(0, 0);

    this.add
      .text(GAME.WIDTH / 2, 150, 'ROOFTOP DASH', { font: '52px monospace', color: '#facc15' })
      .setOrigin(0.5);
    this.add
      .text(GAME.WIDTH / 2, 200, '屋頂衝刺 · Phaser 3 + Vite', {
        font: UI.FONT,
        color: UI.HINT_COLOR,
      })
      .setOrigin(0.5);

    this.add
      .text(
        GAME.WIDTH / 2,
        300,
        ['← → 移動　　SPACE 跳躍', 'P 暫停　　R 重來　　M 回主選單', '收齊金幣才會開出口門，踩敵人頭可以得分'].join('\n'),
        { font: '18px monospace', color: UI.TEXT_COLOR, align: 'center', lineSpacing: 8 }
      )
      .setOrigin(0.5);

    const start = this.add
      .text(GAME.WIDTH / 2, 430, '▶ 按 SPACE 或點一下畫面開始', {
        font: '22px monospace',
        color: '#4ade80',
      })
      .setOrigin(0.5);
    this.tweens.add({ targets: start, alpha: 0.3, duration: 700, yoyo: true, repeat: -1 });

    this.add
      .text(GAME.WIDTH / 2, GAME.HEIGHT - 30, '課堂參數：?demo=level2　?demo=tunneling　?demo=tunneling&fix=1', {
        font: '13px monospace',
        color: '#64748b',
      })
      .setOrigin(0.5);

    this.input.keyboard.once('keydown-SPACE', () => this.startGame());
    this.input.once('pointerdown', () => this.startGame());
  }

  startGame() {
    this.scene.start('PlayScene', { level: 1, fresh: true });
  }
}
