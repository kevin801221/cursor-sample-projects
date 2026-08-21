import React from 'react';
import { Habit } from '../types/habit';
import { calculateStreak, getTodayDateString } from '../services/habitStorage';

interface StatsViewProps {
  habits: Habit[];
}

export const StatsView: React.FC<StatsViewProps> = ({ habits }) => {
  const todayStr = getTodayDateString();
  const completedToday = habits.filter((h) => h.completedDates.includes(todayStr)).length;
  const total = habits.length;
  const rate = total > 0 ? Math.round((completedToday / total) * 100) : 0;
  const maxStreak = Math.max(0, ...habits.map((h) => calculateStreak(h.completedDates)));

  return (
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 10, marginBottom: 18 }}>
      <div
        style={{
          padding: 12,
          borderRadius: 12,
          backgroundColor: 'var(--card-bg, #ffffff)',
          border: '1px solid var(--border-color, #e2e8f0)',
          textAlign: 'center',
        }}
      >
        <div style={{ fontSize: 11, color: 'var(--text-sub, #64748b)' }}>今日完成度</div>
        <div style={{ fontSize: 18, fontWeight: 700, color: '#3b82f6', marginTop: 2 }}>{rate}%</div>
        <div style={{ fontSize: 11, color: 'var(--text-sub, #94a3b8)' }}>{completedToday}/{total}</div>
      </div>

      <div
        style={{
          padding: 12,
          borderRadius: 12,
          backgroundColor: 'var(--card-bg, #ffffff)',
          border: '1px solid var(--border-color, #e2e8f0)',
          textAlign: 'center',
        }}
      >
        <div style={{ fontSize: 11, color: 'var(--text-sub, #64748b)' }}>最佳連擊</div>
        <div style={{ fontSize: 18, fontWeight: 700, color: '#f59e0b', marginTop: 2 }}>{maxStreak} 天</div>
        <div style={{ fontSize: 11, color: 'var(--text-sub, #94a3b8)' }}>保持熱情</div>
      </div>

      <div
        style={{
          padding: 12,
          borderRadius: 12,
          backgroundColor: 'var(--card-bg, #ffffff)',
          border: '1px solid var(--border-color, #e2e8f0)',
          textAlign: 'center',
        }}
      >
        <div style={{ fontSize: 11, color: 'var(--text-sub, #64748b)' }}>習慣總數</div>
        <div style={{ fontSize: 18, fontWeight: 700, color: '#10b981', marginTop: 2 }}>{total} 項</div>
        <div style={{ fontSize: 11, color: 'var(--text-sub, #94a3b8)' }}>日常養成</div>
      </div>
    </div>
  );
};
