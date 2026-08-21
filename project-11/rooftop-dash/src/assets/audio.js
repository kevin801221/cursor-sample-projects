/**
 * assets/audio.js — 四種音效（跳躍／收集／受傷／過關）+ 背景音樂，全部用 WebAudio 現場合成。
 *
 * 一樣是離線鐵則：沒有任何 .mp3 / .ogg 要下載，音色參數全在 constants.js 的 AUDIO 裡。
 * 想換音色？改 AUDIO.JUMP.freq / type，存檔就聽得到差別。
 */
import { AUDIO } from '../constants.js';

export function createAudio(scene) {
  const ctx = scene.sound && scene.sound.context;
  const usable = !!(ctx && typeof ctx.createOscillator === 'function');

  let master = null;
  let musicGain = null;
  let musicTimer = null;
  let noteIndex = 0;
  let manuallyPaused = false;

  if (usable) {
    master = ctx.createGain();
    master.gain.value = AUDIO.MASTER_GAIN;
    master.connect(ctx.destination);
    musicGain = ctx.createGain();
    musicGain.gain.value = AUDIO.MUSIC_GAIN;
    musicGain.connect(ctx.destination);
  }

  /**
   * Chrome 的自動播放政策：頁面還沒有使用者手勢就出聲，聲音不會響，
   * 只會在 console 留下一排黃色警告。第 7 幕要給學生看「console 全綠」，
   * 多一行黃字都會壞掉，所以解鎖前就安靜等著——
   * Phaser 的 SoundManager 會在第一次按鍵或點畫面時自動解鎖（sound.locked 轉 false）。
   */
  const unlocked = () => usable && !scene.sound.locked && !manuallyPaused;

  /** 一顆音：頻率從 freq 滑到 toFreq，音量從大到 0（避免爆音） */
  function tone(spec, out, gainScale = 1) {
    if (!unlocked()) return;
    if (ctx.state === 'suspended') ctx.resume();
    const t = ctx.currentTime;
    const dur = spec.ms / 1000;
    const osc = ctx.createOscillator();
    const env = ctx.createGain();
    osc.type = spec.type;
    osc.frequency.setValueAtTime(spec.freq, t);
    osc.frequency.exponentialRampToValueAtTime(Math.max(spec.toFreq, 1), t + dur);
    env.gain.setValueAtTime(0.0001, t);
    env.gain.exponentialRampToValueAtTime(gainScale, t + 0.01);
    env.gain.exponentialRampToValueAtTime(0.0001, t + dur);
    osc.connect(env);
    env.connect(out);
    osc.start(t);
    osc.stop(t + dur + 0.02);
  }

  return {
    available: usable,
    jump: () => tone(AUDIO.JUMP, master, 0.6),
    coin: () => tone(AUDIO.COIN, master, 0.8),
    hurt: () => tone(AUDIO.HURT, master, 1),
    clear: () => tone(AUDIO.CLEAR, master, 0.9),

    /** 背景音樂：一顆一顆音排出來的循環。掛在 scene.time 上，場景暫停音樂就停 */
    startMusic() {
      if (!usable || musicTimer) return;
      musicTimer = scene.time.addEvent({
        delay: AUDIO.MUSIC_STEP_MS,
        loop: true,
        callback: () => {
          const f = AUDIO.MUSIC_NOTES[noteIndex % AUDIO.MUSIC_NOTES.length];
          noteIndex += 1;
          tone({ freq: f, toFreq: f, ms: AUDIO.MUSIC_STEP_MS * 0.9, type: 'sine' }, musicGain, 1);
        },
      });
    },

    stopMusic() {
      if (musicTimer) musicTimer.remove();
      musicTimer = null;
    },

    /** 暫停時整個 AudioContext 停掉，比一個一個音源關乾淨 */
    setPaused(paused) {
      manuallyPaused = paused;
      if (!usable) return;
      if (paused) ctx.suspend();
      else if (!scene.sound.locked) ctx.resume(); // 沒解鎖就 resume()，一樣會噴黃字警告
    },
  };
}
