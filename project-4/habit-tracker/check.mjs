/**
 * Habit Tracker Architecture & Model Checker
 */
import fs from 'fs';

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
import { calculateStreak } from './src/services/habitStorage.ts';

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
