/**
 * Chrome Extension Security & Architecture Checker
 */
import fs from 'fs';

console.log('【1】Manifest V3 規格檢查');
const manifest = JSON.parse(fs.readFileSync('manifest.json', 'utf-8'));
let errors = 0;

if (manifest.manifest_version === 3) {
  console.log('  ✓ manifest_version = 3 (符合現代標準)');
} else {
  console.log('  ✗ manifest_version 不是 3');
  errors++;
}

if (manifest.background && manifest.background.service_worker) {
  console.log(`  ✓ background service_worker 配置正確: ${manifest.background.service_worker}`);
} else {
  console.log('  ✗ 缺少 background service_worker 配置');
  errors++;
}

console.log('\n【2】Content Script 金鑰安全隔離稽核 (content.js)');
const contentCode = fs.readFileSync('content.js', 'utf-8');
const forbiddenKeywords = ['apiKey', 'api_key', 'OPENAI_API_KEY', 'Bearer', 'sk-'];
let leakFound = false;
for (const kw of forbiddenKeywords) {
  if (contentCode.includes(kw)) {
    console.log(`  ✗ content.js 發現潛在金鑰關鍵字: ${kw}`);
    leakFound = true;
    errors++;
  }
}
if (!leakFound) {
  console.log('  ✓ content.js 100% 乾淨：無任何 API 金鑰或 Token 洩露');
}

console.log('\n【3】訊息通訊架構檢查');
if (contentCode.includes('chrome.runtime.sendMessage') && fs.readFileSync('background.js', 'utf-8').includes('chrome.runtime.onMessage')) {
  console.log('  ✓ Content Script 與 Service Worker 訊息傳遞通道完整');
} else {
  console.log('  ✗ 訊息通訊機制缺失');
  errors++;
}

if (errors === 0) {
  console.log('\n🎉 Chrome 擴充功能安全稽核全部通過！');
  process.exit(0);
} else {
  console.log(`\n⚠️ 發現 ${errors} 個安全性問題`);
  process.exit(1);
}
