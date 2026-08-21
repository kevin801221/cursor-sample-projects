import React from 'react';
import { Habit } from '../types/habit';
import { calculateStreak, getTodayDateString } from '../services/habitStorage';

interface HabitCardProps {
  habit: Habit;
  onToggle: (id: string) => void;
  onDelete: (id: string) => void;
}

export const HabitCard: React.FC<HabitCardProps> = ({ habit, onToggle, onDelete }) => {
  const todayStr = getTodayDateString();
  const isDoneToday = habit.completedDates.includes(todayStr);
  const streak = calculateStreak(habit.completedDates);

  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '14px 16px',
        backgroundColor: 'var(--card-bg, #ffffff)',
        border: '1px solid var(--border-color, #e2e8f0)',
        borderRadius: 14,
        marginBottom: 10,
        transition: 'all 0.2s ease',
        boxShadow: isDoneToday ? '0 2px 8px rgba(59, 130, 246, 0.08)' : '0 1px 3px rgba(0,0,0,0.03)',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
        <button
          type="button"
          onClick={() => onToggle(habit.id)}
          aria-label={`打卡 ${habit.name}`}
          style={{
            width: 38,
            height: 38,
            borderRadius: '50%',
            border: isDoneToday ? 'none' : `2px solid ${habit.color}`,
            backgroundColor: isDoneToday ? habit.color : 'transparent',
            color: '#ffffff',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            cursor: 'pointer',
            fontSize: 18,
            transition: 'transform 0.15s cubic-bezier(0.175, 0.885, 0.32, 1.275)',
            outline: 'none',
          }}
          onMouseDown={(e) => (e.currentTarget.style.transform = 'scale(0.85)')}
          onMouseUp={(e) => (e.currentTarget.style.transform = 'scale(1)')}
        >
          {isDoneToday ? '✓' : habit.icon}
        </button>

        <div>
          <div
            style={{
              fontSize: 15,
              fontWeight: 600,
              color: 'var(--text-main, #0f172a)',
              textDecoration: isDoneToday ? 'line-through' : 'none',
              opacity: isDoneToday ? 0.75 : 1,
            }}
          >
            {habit.name}
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginTop: 3 }}>
            <span
              style={{
                fontSize: 11,
                padding: '2px 6px',
                borderRadius: 4,
                backgroundColor: 'var(--tag-bg, #f1f5f9)',
                color: 'var(--text-sub, #64748b)',
              }}
            >
              {habit.category}
            </span>
            <span style={{ fontSize: 12, color: 'var(--text-sub, #64748b)' }}>
              目標每週 {habit.targetDaysPerWeek} 天
            </span>
          </div>
        </div>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 4,
            padding: '4px 8px',
            borderRadius: 8,
            backgroundColor: streak > 0 ? 'rgba(245, 158, 11, 0.12)' : 'var(--tag-bg, #f1f5f9)',
            color: streak > 0 ? '#d97706' : 'var(--text-sub, #64748b)',
            fontSize: 13,
            fontWeight: 700,
          }}
        >
          <span>🔥</span>
          <span>{streak} 天</span>
        </div>

        <button
          type="button"
          onClick={() => onDelete(habit.id)}
          aria-label="刪除習慣"
          style={{
            background: 'transparent',
            border: 'none',
            color: 'var(--text-sub, #94a3b8)',
            cursor: 'pointer',
            fontSize: 14,
            padding: 4,
          }}
        >
          🗑️
        </button>
      </div>
    </div>
  );
};
