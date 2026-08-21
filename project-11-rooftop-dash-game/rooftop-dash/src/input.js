/**
 * input.js — 只管鍵盤輸入，不准放任何遊戲邏輯（.cursor/rules/00-architecture.mdc）
 *
 * 場景要問「玩家有沒有按跳」，就呼叫這裡的函式；
 * 「按了跳要做什麼」是場景與 prefab 的事，不是這一檔的事。
 */
import Phaser from 'phaser';

const KEYS = Phaser.Input.Keyboard.KeyCodes;

/** 在場景裡建立所有按鍵，回傳一包 keys 物件 */
export function createInput(scene) {
  const kb = scene.input.keyboard;
  return {
    cursors: kb.createCursorKeys(),
    jump: kb.addKey(KEYS.SPACE),
    pause: kb.addKey(KEYS.P),
    restart: kb.addKey(KEYS.R),
    menu: kb.addKey(KEYS.M),
  };
}

/** 這一幀的水平方向：-1 左、0 停、1 右 */
export function horizontal(keys) {
  const left = keys.cursors.left.isDown;
  const right = keys.cursors.right.isDown;
  return (right ? 1 : 0) - (left ? 1 : 0);
}

/** 跳躍鍵「剛按下」（長按不會連續觸發 → 一次跳一下） */
export function jumpPressed(keys) {
  return (
    Phaser.Input.Keyboard.JustDown(keys.jump) ||
    Phaser.Input.Keyboard.JustDown(keys.cursors.up)
  );
}

export const pausePressed = (keys) => Phaser.Input.Keyboard.JustDown(keys.pause);
export const restartPressed = (keys) => Phaser.Input.Keyboard.JustDown(keys.restart);
export const menuPressed = (keys) => Phaser.Input.Keyboard.JustDown(keys.menu);
