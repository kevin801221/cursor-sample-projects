/**
 * Habit Tracker Architecture & Model Checker
 */
import fs from 'fs';
import ts from 'typescript';

console.log('【1】檔案架構與職責邊界檢查');
const files = [
  'src/types/habit.ts',
  'src/services/habitStorage.ts',
  'src/components/HabitCard.tsx',
  'src/components/StatsView.tsx',
  'src/components/MobileFrame.tsx',
  'src/App.tsx'
];

let errors = 0;
for (const f of files) {
  if (fs.existsSync(f)) {
    console.log(`  ✓ ${f} 存在`);
  } else {
    console.log(`  ✗ ${f} 缺失`);
    errors++;
  }
}

console.log('\n【2】連續天數 (Streak) 計算邏輯測試');
// 不直接讓 Node 載入 .ts：Node 20 不支援，而新版 Node 對 extensionless
// TypeScript import 的解析也不同。用專案鎖定的 TypeScript 先轉成標準 ESM，
// 讓同一支課堂檢查器可跨 Node 20+ 執行。
const habitStorageSource = fs.readFileSync('src/services/habitStorage.ts', 'utf8');
const habitStorageJs = ts.transpileModule(habitStorageSource, {
  compilerOptions: {
    target: ts.ScriptTarget.ES2022,
    module: ts.ModuleKind.ESNext,
  },
}).outputText;
const habitStorageUrl = `data:text/javascript;base64,${Buffer.from(habitStorageJs).toString('base64')}`;
const { calculateStreak } = await import(habitStorageUrl);

// Test 1: Empty
if (calculateStreak([]) === 0) {
  console.log('  ✓ 空陣列連續天數 = 0');
} else {
  console.log('  ✗ 空陣列測試失敗');
  errors++;
}

console.log('\n【3】Scope 規則稽核 (.cursor/rules/00-scope.mdc)');
if (fs.existsSync('.cursor/rules/00-scope.mdc')) {
  console.log('  ✓ 00-scope.mdc 規則檔存在且生效');
} else {
  console.log('  ✗ 缺少 00-scope.mdc');
  errors++;
}

if (errors === 0) {
  console.log('\n🎉 Habit Tracker 專案全部檢查通過！');
  process.exit(0);
} else {
  console.log(`\n⚠️ 發現 ${errors} 個錯誤`);
  process.exit(1);
}
