/**
 * Component Library Token & Architecture Checker
 */
import fs from 'fs';
import path from 'path';

const files = [
  'src/tokens/tokens.ts',
  'src/components/Button.tsx',
  'src/components/Input.tsx',
  'src/components/Card.tsx',
  'src/components/Modal.tsx',
  'src/components/Showcase.tsx'
];

let errors = 0;

console.log('【1】檔案結構完整性檢查');
for (const f of files) {
  if (fs.existsSync(f)) {
    console.log(`  ✓ ${f} 存在`);
  } else {
    console.log(`  ✗ ${f} 缺失`);
    errors++;
  }
}

console.log('\n【2】禁止寫死十六進位色碼稽核 (src/components/*.tsx)');
const tsxFiles = fs.readdirSync('src/components').filter(f => f.endsWith('.tsx'));
for (const f of tsxFiles) {
  const content = fs.readFileSync(path.join('src/components', f), 'utf-8');
  // Look for hardcoded hex colors outside comments/docs
  const matches = content.match(/(#[0-9a-fA-F]{3,8})/g);
  if (matches && f !== 'Showcase.tsx') { // Showcase displays them as labels
    console.log(`  ✗ ${f} 發現寫死色碼: ${matches.join(', ')}`);
    errors++;
  } else {
    console.log(`  ✓ ${f} 無違規寫死色碼`);
  }
}

console.log('\n【3】無障礙屬性 (A11y) 稽核');
const inputContent = fs.readFileSync('src/components/Input.tsx', 'utf-8');
if (inputContent.includes('aria-invalid') && inputContent.includes('aria-describedby')) {
  console.log('  ✓ Input.tsx 包含 aria-invalid 與 aria-describedby');
} else {
  console.log('  ✗ Input.tsx 缺少 ARIA 屬性');
  errors++;
}

const modalContent = fs.readFileSync('src/components/Modal.tsx', 'utf-8');
if (modalContent.includes('Escape') && modalContent.includes('role="dialog"')) {
  console.log('  ✓ Modal.tsx 支援 ESC 鍵關閉與 role="dialog"');
} else {
  console.log('  ✗ Modal.tsx 缺少 dialog A11y 支援');
  errors++;
}

if (errors === 0) {
  console.log('\n🎉 元件庫全部檢查通過！(0 錯誤)');
  process.exit(0);
} else {
  console.log(`\n⚠️ 發現 ${errors} 個錯誤`);
  process.exit(1);
}
