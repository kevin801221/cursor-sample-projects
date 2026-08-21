/**
 * scenes/PlayScene.js — 遊戲主場景：平台、玩家、敵人、金幣、出口門、暫停。
 *
 * 狀態（命數／分數／金幣／關卡）一律存 registry，不存 this——
 * 因為 scene.restart() 之後 this 會整個換新，registry 才留得住（walkthrough §9）。
 */
import Phaser from 'phaser';
import {
  GAME,
  PHYSICS,
  PLAYER,
  ENEMY,
  COLLECTIBLE,
  PLATFORM,
  DOOR,
  UI,
  LEVELS,
  TUNNEL_LAB,
  DEMO,
} from '../constants.js';
import {
  createInput,
  jumpPressed,
  pausePressed,
  restartPressed,
  menuPressed,
} from '../input.js';
import { createTextures, platformTexture } from '../assets/textures.js';
import { createAudio } from '../assets/audio.js';
import Player from '../prefabs/Player.js';
import Enemy, { isStomp } from '../prefabs/Enemy.js';
import Collectible from '../prefabs/Collectible.js';

export default class PlayScene extends Phaser.Scene {
  constructor() {
    super('PlayScene');
  }

  init(data) {
    this.isTunnelLab = DEMO.MODE === 'tunneling';
    const level = data.level || DEMO.START_LEVEL;
    this.levelIndex = Phaser.Math.Clamp(level, 1, LEVELS.length) - 1;

    if (data.fresh) {
      this.registry.set('lives', PLAYER.INITIAL_LIVES);
      this.registry.set('score', 0);
      this.registry.set('won', false);
    }
    this.registry.set('level', this.levelIndex + 1);
    this.registry.set('coins', 0);

    this.isPaused = false;
    this.transitioning = false;
    this.tunnelCount = 0;
    this.tunnelCounted = false;
  }

  create() {
    createTextures(this);
    this.level = this.isTunnelLab ? TUNNEL_LAB : LEVELS[this.levelIndex];
    this.audio = createAudio(this);
    this.keys = createInput(this);

    this.buildBackground();
    this.buildWorld();
    this.buildHud();
    this.buildPauseOverlay();

    this.audio.startMusic();
    this.events.once('shutdown', () => {
      this.audio.stopMusic();
      this.audio.setPaused(false);
    });

    if (this.isTunnelLab) this.setupTunnelLab();
  }

  // ---------------------------------------------------------------- 建立世界

  buildBackground() {
    this.add.image(0, 0, 'sky').setOrigin(0, 0).setScrollFactor(0);
    this.skyline = this.add
      .tileSprite(0, GAME.HEIGHT - 260, GAME.WIDTH, 260, 'skyline')
      .setOrigin(0, 0)
      .setScrollFactor(0);
  }

  buildWorld() {
    const level = this.level;
    // 世界底部故意留得很深：掉進坑裡不會卡在畫面邊界，才判定得出「掉下去了」
    this.physics.world.setBounds(0, 0, level.width, GAME.HEIGHT * 2);
    this.cameras.main.setBounds(0, 0, level.width, GAME.HEIGHT);

    this.platforms = this.physics.add.staticGroup();
    level.platforms.forEach((p) => {
      const key = platformTexture(this, p.width);
      this.platforms
        .create(p.x + p.width / 2, p.y + PLATFORM.HEIGHT / 2, key)
        .refreshBody(); // 位置改過就 refreshBody，不然碰撞體留在舊位置
    });

    this.player = new Player(this, level.spawn.x, level.spawn.y);
    this.physics.add.collider(this.player, this.platforms);
    this.cameras.main.startFollow(this.player, true, 0.12, 0.12);

    // 用普通 group，不用 physics.add.group()：
    // Arcade 物理 group 會在 add() 時把子物件的 body 預設值蓋回去
    // （velocity 歸零、maxVelocity 變回 10000、allowGravity 變回 true），
    // prefab 建構子裡設的巡邏速度與限速會被無聲地清掉——經典沉默故障。
    this.enemies = this.add.group();
    level.enemies.forEach((cfg) => this.enemies.add(new Enemy(this, cfg)));
    this.physics.add.collider(this.enemies, this.platforms);
    // 傷害用 overlap（純接觸判定），不用 collider——不然角色會被敵人推著跑
    this.physics.add.overlap(this.player, this.enemies, this.onEnemyTouch, null, this);

    this.coins = this.add.group(); // 同上：金幣的 allowGravity(false) 不能被 group 蓋掉
    level.coins.forEach((c) => this.coins.add(new Collectible(this, c.x, c.y)));
    this.physics.add.overlap(this.player, this.coins, this.onCoin, null, this);
    this.coinsTotal = level.coins.length;

    if (level.door) {
      this.door = this.physics.add
        .staticSprite(level.door.x, level.door.y - DOOR.HEIGHT / 2, 'door-locked')
        .refreshBody();
      this.physics.add.overlap(this.player, this.door, this.onDoor, null, this);
    }
  }

  buildHud() {
    this.hud = this.add
      .text(12, 10, '', {
        font: UI.FONT,
        color: UI.TEXT_COLOR,
        backgroundColor: '#0b1220cc',
        padding: { x: 8, y: 5 },
        lineSpacing: 4,
      })
      .setScrollFactor(0)
      .setDepth(UI.DEPTH_UI);

    this.hint = this.add
      .text(12, GAME.HEIGHT - 28, '← → 移動　SPACE 跳躍　P 暫停　R 重來　M 主選單', {
        font: UI.FONT,
        color: UI.HINT_COLOR,
        backgroundColor: '#0b1220cc',
        padding: { x: 6, y: 3 },
      })
      .setScrollFactor(0)
      .setDepth(UI.DEPTH_UI);

    this.toast = this.add
      .text(GAME.WIDTH / 2, 70, '', { font: UI.FONT, color: '#fbbf24' })
      .setOrigin(0.5)
      .setScrollFactor(0)
      .setDepth(UI.DEPTH_UI)
      .setAlpha(0);
  }

  buildPauseOverlay() {
    const rect = this.add
      .rectangle(0, 0, GAME.WIDTH, GAME.HEIGHT, UI.PAUSE_OVERLAY_COLOR, UI.PAUSE_OVERLAY_ALPHA)
      .setOrigin(0, 0)
      .setScrollFactor(0);
    const text = this.add
      .text(GAME.WIDTH / 2, GAME.HEIGHT / 2, 'PAUSED\n再按一次 P 繼續', {
        font: UI.FONT_BIG,
        color: '#ffffff',
        align: 'center',
      })
      .setOrigin(0.5)
      .setScrollFactor(0);

    // 遮罩只建立一次，連按 P 也不會疊出第二層（walkthrough §6 的常見坑）
    this.pauseLayer = this.add.container(0, 0, [rect, text]);
    this.pauseLayer.setDepth(UI.DEPTH_UI).setVisible(false);
  }

  // ------------------------------------------------------------ 每幀更新

  update() {
    if (pausePressed(this.keys)) this.togglePause();
    if (this.isPaused) return;

    if (restartPressed(this.keys)) {
      this.scene.restart({ level: 1, fresh: true });
      return;
    }
    if (menuPressed(this.keys)) {
      this.scene.start('MenuScene');
      return;
    }

    // 穿模實驗室裡 SPACE 改成「立刻再投一次」（先消耗掉這一幀的 SPACE，才不會同時起跳）
    if (this.isTunnelLab && jumpPressed(this.keys)) this.dropPlayer();

    this.player.handleInput(this.keys, this.audio);
    this.enemies.getChildren().forEach((e) => e.patrol());
    this.skyline.tilePositionX = this.cameras.main.scrollX * 0.3;

    if (this.isTunnelLab) this.updateTunnelLab();
    else if (this.player.y > GAME.HEIGHT + 80) this.onFallIntoPit();

    this.refreshHud();
  }

  refreshHud() {
    if (this.isTunnelLab) {
      this.hud.setText(`${this.level.name}　　（這一關沒有金幣與敵人，只看穿模）`);
      return;
    }
    const collected = this.registry.get('coins');
    const doorState = this.door
      ? collected >= this.coinsTotal
        ? '出口門：已開啟'
        : `出口門：鎖住（還差 ${this.coinsTotal - collected} 顆）`
      : '';
    this.hud.setText(
      `${this.level.name}　　Lives: ${this.registry.get('lives')}　` +
        `Coins: ${collected}/${this.coinsTotal}　Score: ${this.registry.get('score')}\n${doorState}`
    );
  }

  showToast(message) {
    this.toast.setText(message).setAlpha(1);
    this.tweens.add({ targets: this.toast, alpha: 0, duration: UI.TOAST_MS, ease: 'Quad.easeIn' });
  }

  // ------------------------------------------------------------ 遊戲事件

  onCoin(_player, coin) {
    coin.collect();
    this.registry.inc('coins', 1);
    this.registry.inc('score', COLLECTIBLE.SCORE);
    this.audio.coin();
    if (this.registry.get('coins') >= this.coinsTotal && this.door) {
      this.door.setTexture('door-open');
      this.showToast('金幣收齊了！出口門開啟 →');
    }
  }

  onEnemyTouch(player, enemy) {
    if (isStomp(player.body.bottom, player.body.velocity.y, enemy.body.top, ENEMY.HEIGHT)) {
      enemy.squash();
      this.registry.inc('score', PLAYER.STOMP_SCORE);
      player.setVelocityY(-PLAYER.JUMP_VELOCITY * 0.7);
      this.audio.coin();
      return;
    }
    if (player.isInvulnerable) return;

    player.hurt();
    player.setVelocity(player.x < enemy.x ? -PLAYER.SPEED : PLAYER.SPEED, -PLAYER.JUMP_VELOCITY / 2);
    this.loseLife('撞到敵人了！');
  }

  onFallIntoPit() {
    if (this.player.isInvulnerable) return;
    this.player.hurt();
    this.player.respawn(this.level.spawn.x, this.level.spawn.y);
    this.loseLife('掉下去了！');
  }

  loseLife(reason) {
    const lives = this.registry.get('lives') - 1;
    this.registry.set('lives', lives);
    this.audio.hurt();
    if (lives <= 0) {
      this.registry.set('won', false);
      this.scene.start('GameOverScene');
    } else {
      this.showToast(`${reason} 剩下 ${lives} 條命`);
    }
  }

  onDoor() {
    if (this.transitioning) return;
    if (this.registry.get('coins') < this.coinsTotal) {
      this.showToast(`門還鎖著，還差 ${this.coinsTotal - this.registry.get('coins')} 顆金幣`);
      return;
    }
    this.transitioning = true;
    this.audio.clear();

    const next = this.levelIndex + 2; // 1-based 的下一關
    if (next > LEVELS.length) {
      this.registry.set('won', true);
      this.time.delayedCall(400, () => this.scene.start('GameOverScene'));
    } else {
      this.showToast(`過關！前往第 ${next} 關`);
      this.time.delayedCall(600, () => this.scene.restart({ level: next }));
    }
  }

  togglePause() {
    this.isPaused = !this.isPaused;
    if (this.isPaused) {
      this.physics.pause(); // 只停 update 不停物理的話，角色會繼續往下掉
      this.tweens.pauseAll();
      this.time.paused = true; // 連背景音樂的排程也一起停
    } else {
      this.physics.resume();
      this.tweens.resumeAll();
      this.time.paused = false;
    }
    this.pauseLayer.setVisible(this.isPaused);
    this.audio.setPaused(this.isPaused);
  }

  // -------------------------------------------------- ?demo=tunneling 專用

  setupTunnelLab() {
    this.hint.setText('SPACE 立刻再投一次　P 暫停　M 主選單');
    this.labText = this.add
      .text(12, 60, '', { font: '17px monospace', color: '#e2e8f0', lineSpacing: 6 })
      .setScrollFactor(0)
      .setDepth(UI.DEPTH_UI);

    this.dropPlayer();
    this.time.addEvent({
      delay: TUNNEL_LAB.DROP_INTERVAL_MS,
      loop: true,
      callback: () => this.dropPlayer(),
    });
  }

  /** 把玩家丟到高空，並給一個「極高」的初速度，重現高速下墜 */
  dropPlayer() {
    this.player.respawn(this.level.spawn.x, this.level.spawn.y);
    this.player.setVelocityY(TUNNEL_LAB.DROP_VELOCITY_Y);
    this.tunnelCounted = false;
    this.dropPeakVy = 0;
  }

  updateTunnelLab() {
    const vy = Math.abs(this.player.body.velocity.y);
    this.dropPeakVy = Math.max(this.dropPeakVy || 0, vy);
    const peakStep = this.dropPeakVy / GAME.FPS;
    const floorY = this.level.platforms[0].y;

    // 掉到地板下面 = 一定是穿過去的（這一關的地板沒有任何缺口）
    if (!this.tunnelCounted && this.player.y > floorY + 80) {
      this.tunnelCounted = true;
      this.tunnelCount += 1;
      this.cameras.main.flash(220, 220, 40, 40);
    }

    this.labText.setText(
      [
        `PHYSICS.CONTINUOUS_COLLISION = ${PHYSICS.CONTINUOUS_COLLISION ? 'true  ✅ 有限速' : 'false ❌ 沒限速'}`,
        `這次下墜最高速度 = ${this.dropPeakVy.toFixed(0).padStart(5)} px/s`,
        `換算單幀位移     = ${peakStep.toFixed(1).padStart(5)} px　（60fps）`,
        `平台厚度         = ${String(PLATFORM.HEIGHT).padStart(5)} px`,
        peakStep > PLATFORM.HEIGHT
          ? '→ 單幀位移 > 平台厚度：那一幀的起點在平台上、終點在平台下，引擎判定「沒碰到」'
          : '→ 單幀位移 < 平台厚度：每一幀都檢查得到碰撞',
        '',
        this.tunnelCount > 0
          ? `⚠️ 已經穿過平台 ${this.tunnelCount} 次　（console 全綠，沒有任何錯誤訊息）`
          : '✅ 穿模 0 次　每次都穩穩落在平台上',
      ].join('\n')
    );
    this.labText.setColor(this.tunnelCount > 0 ? '#fca5a5' : '#86efac');
  }
}
