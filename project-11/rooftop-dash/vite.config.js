import { defineConfig } from 'vite';

export default defineConfig({
  /**
   * ★ base 路徑的坑（walkthrough §9「部署後資源 404」）★
   *
   * 預設 base 是 '/'，打包出來的 index.html 會去要 /assets/index-xxx.js。
   * 一旦部署到子路徑（GitHub Pages 的 https://user.github.io/rooftop-dash/），
   * 那條絕對路徑就會 404，畫面全黑但 console 只有一行 404——又是一個沉默故障。
   *
   * './' 產出的是相對路徑，本機 dev、npm run preview、子路徑部署三種情況都對。
   * 如果你的網站一定要掛在固定子路徑，就改成 '/你的repo名稱/'。
   */
  base: './',
  server: {
    port: 5173,
    open: false,
  },
  build: {
    outDir: 'dist',
    // Phaser 單檔就 1MB 以上，這是正常的，不要被警告嚇到
    chunkSizeWarningLimit: 1600,
  },
});
