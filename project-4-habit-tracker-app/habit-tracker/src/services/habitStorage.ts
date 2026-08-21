import type { Habit } from '../types/habit';

const STORAGE_KEY = 'cursor_habit_tracker_data_v1';

export function getTodayDateString(): string {
  const now = new Date();
  const year = now.getFullYear();
  const month = String(now.getMonth() + 1).padStart(2, '0');
  const day = String(now.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}

export const SEED_HABITS: Habit[] = [
  {
    id: 'h-1',
    name: '早晨溫水 500ml',
    category: '健康',
    icon: '💧',
    color: '#3b82f6',
    targetDaysPerWeek: 7,
    completedDates: [getTodayDateString()],
    createdAt: '2026-08-01',
  },
  {
    id: 'h-2',
    name: '閱讀技術手冊 25 分鐘',
    category: '學習',
    icon: '📚',
    color: '#8b5cf6',
    targetDaysPerWeek: 5,
    completedDates: [],
    createdAt: '2026-08-05',
  },
  {
    id: 'h-3',
    name: '核心肌群與拉筋鍛鍊',
    category: '運動',
    icon: '🏃',
    color: '#10b981',
    targetDaysPerWeek: 4,
    completedDates: [getTodayDateString()],
    createdAt: '2026-08-10',
  },
  {
    id: 'h-4',
    name: 'Cursor 專案開發練習',
    category: '生活',
    icon: '⚡',
    color: '#f59e0b',
    targetDaysPerWeek: 6,
    completedDates: [getTodayDateString()],
    createdAt: '2026-08-02',
  },
];

export function loadHabits(): Habit[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) {
      saveHabits(SEED_HABITS);
      return SEED_HABITS;
    }
    return JSON.parse(raw);
  } catch {
    return SEED_HABITS;
  }
}

export function saveHabits(habits: Habit[]): void {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(habits));
  } catch (e) {
    console.error('Failed to save habits:', e);
  }
}

export function calculateStreak(completedDates: string[]): number {
  if (!completedDates || completedDates.length === 0) return 0;

  const dateSet = new Set(completedDates);
  let streak = 0;
  const today = new Date();

  // Check from today or yesterday
  let checkDate = new Date(today);
  const todayStr = getFormattedDate(checkDate);

  if (!dateSet.has(todayStr)) {
    // If not completed today, check if completed yesterday
    checkDate.setDate(checkDate.getDate() - 1);
    const yesterdayStr = getFormattedDate(checkDate);
    if (!dateSet.has(yesterdayStr)) {
      return 0;
    }
  }

  while (true) {
    const dStr = getFormattedDate(checkDate);
    if (dateSet.has(dStr)) {
      streak++;
      checkDate.setDate(checkDate.getDate() - 1);
    } else {
      break;
    }
  }

  return streak;
}

function getFormattedDate(d: Date): string {
  const year = d.getFullYear();
  const month = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}
