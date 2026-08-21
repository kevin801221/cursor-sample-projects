import { useState, useEffect } from 'react';
import { Habit } from './types/habit';
import { loadHabits, saveHabits, getTodayDateString } from './services/habitStorage';
import { HabitCard } from './components/HabitCard';
import { StatsView } from './components/StatsView';
import { MobileFrame } from './components/MobileFrame';

export function App() {
  const [habits, setHabits] = useState<Habit[]>([]);
  const [theme, setTheme] = useState<'light' | 'dark'>('dark');
  const [newHabitName, setNewHabitName] = useState('');
  const [newCategory, setNewCategory] = useState<'健康' | '學習' | '運動' | '生活'>('健康');
  const [showAddForm, setShowAddForm] = useState(false);

  useEffect(() => {
    setHabits(loadHabits());
    document.documentElement.setAttribute('data-theme', theme);
  }, [theme]);

  const toggleTheme = () => {
    setTheme((t) => (t === 'light' ? 'dark' : 'light'));
  };

  const handleToggleHabit = (id: string) => {
    const todayStr = getTodayDateString();
    const updated = habits.map((h) => {
      if (h.id !== id) return h;
      const done = h.completedDates.includes(todayStr);
      const newDates = done
        ? h.completedDates.filter((d) => d !== todayStr)
        : [...h.completedDates, todayStr];
      return { ...h, completedDates: newDates };
    });
    setHabits(updated);
    saveHabits(updated);
  };

  const handleDeleteHabit = (id: string) => {
    const updated = habits.filter((h) => h.id !== id);
    setHabits(updated);
    saveHabits(updated);
  };

  const handleAddHabit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newHabitName.trim()) return;

    const icons = { 健康: '💧', 學習: '📚', 運動: '🏃', 生活: '⚡' };
    const colors = { 健康: '#3b82f6', 學習: '#8b5cf6', 運動: '#10b981', 生活: '#f59e0b' };

    const newHabit: Habit = {
      id: `h-${Date.now()}`,
      name: newHabitName.trim(),
      category: newCategory,
      icon: icons[newCategory],
      color: colors[newCategory],
      targetDaysPerWeek: 7,
      completedDates: [],
      createdAt: getTodayDateString(),
    };

    const updated = [newHabit, ...habits];
    setHabits(updated);
    saveHabits(updated);
    setNewHabitName('');
    setShowAddForm(false);
  };

  const today = new Date().toLocaleDateString('zh-TW', { month: 'long', day: 'numeric', weekday: 'short' });

  return (
    <MobileFrame theme={theme} onToggleTheme={toggleTheme}>
      {/* App Header */}
      <div style={{ padding: '12px 0 16px', display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end' }}>
        <div>
          <div style={{ fontSize: 13, color: 'var(--text-sub)', fontWeight: 500 }}>{today}</div>
          <h2 style={{ fontSize: 24, fontWeight: 800, color: 'var(--text-main)', letterSpacing: '-0.02em', marginTop: 2 }}>
            習慣追蹤
          </h2>
        </div>
        <button
          type="button"
          onClick={() => setShowAddForm(!showAddForm)}
          style={{
            width: 36,
            height: 36,
            borderRadius: '50%',
            backgroundColor: '#3b82f6',
            color: '#fff',
            border: 'none',
            fontSize: 20,
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            boxShadow: '0 4px 10px rgba(59, 130, 246, 0.3)',
          }}
        >
          {showAddForm ? '×' : '+'}
        </button>
      </div>

      {/* Add Form Drawer */}
      {showAddForm && (
        <form
          onSubmit={handleAddHabit}
          style={{
            padding: 16,
            borderRadius: 14,
            backgroundColor: 'var(--card-bg)',
            border: '1px solid var(--border-color)',
            marginBottom: 16,
            display: 'flex',
            flexDirection: 'column',
            gap: 10,
          }}
        >
          <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-main)' }}>新增好習慣</div>
          <input
            type="text"
            placeholder="例如：每日冥想 10 分鐘"
            value={newHabitName}
            onChange={(e) => setNewHabitName(e.target.value)}
            style={{
              padding: '10px 12px',
              borderRadius: 8,
              border: '1px solid var(--border-color)',
              backgroundColor: 'var(--bg-main)',
              color: 'var(--text-main)',
              fontSize: 14,
              outline: 'none',
            }}
          />
          <div style={{ display: 'flex', gap: 6 }}>
            {(['健康', '學習', '運動', '生活'] as const).map((cat) => (
              <button
                key={cat}
                type="button"
                onClick={() => setNewCategory(cat)}
                style={{
                  flex: 1,
                  padding: '6px 0',
                  borderRadius: 6,
                  border: '1px solid var(--border-color)',
                  backgroundColor: newCategory === cat ? '#3b82f6' : 'var(--bg-main)',
                  color: newCategory === cat ? '#fff' : 'var(--text-sub)',
                  fontSize: 12,
                  fontWeight: 600,
                  cursor: 'pointer',
                }}
              >
                {cat}
              </button>
            ))}
          </div>
          <button
            type="submit"
            style={{
              padding: '10px 0',
              borderRadius: 8,
              backgroundColor: '#3b82f6',
              color: '#fff',
              border: 'none',
              fontSize: 14,
              fontWeight: 600,
              cursor: 'pointer',
              marginTop: 4,
            }}
          >
            建立習慣
          </button>
        </form>
      )}

      {/* Stats Summary */}
      <StatsView habits={habits} />

      {/* Habit List */}
      <div style={{ display: 'flex', flexDirection: 'column' }}>
        <div style={{ fontSize: 13, fontWeight: 700, color: 'var(--text-sub)', marginBottom: 10, textTransform: 'uppercase' }}>
          今日待辦
        </div>
        {habits.map((habit) => (
          <HabitCard
            key={habit.id}
            habit={habit}
            onToggle={handleToggleHabit}
            onDelete={handleDeleteHabit}
          />
        ))}
      </div>
    </MobileFrame>
  );
}

export default App;
