export interface Habit {
  id: string;
  name: string;
  category: '健康' | '學習' | '運動' | '生活';
  icon: string;
  color: string;
  targetDaysPerWeek: number;
  completedDates: string[]; // 'YYYY-MM-DD'
  createdAt: string;
}

export interface HabitStats {
  totalHabits: number;
  completedToday: number;
  bestStreak: number;
  currentStreak: number;
  weeklyRate: number;
}
