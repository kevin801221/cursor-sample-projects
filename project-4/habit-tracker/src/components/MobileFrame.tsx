import React from 'react';

interface MobileFrameProps {
  children: React.ReactNode;
  theme: 'light' | 'dark';
  onToggleTheme: () => void;
}

export const MobileFrame: React.FC<MobileFrameProps> = ({ children, theme, onToggleTheme }) => {
  const timeStr = new Date().toLocaleTimeString('zh-TW', { hour: '2-digit', minute: '2-digit', hour12: false });

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        minHeight: '100vh',
        padding: '24px 16px',
        backgroundColor: theme === 'dark' ? '#090d16' : '#e2e8f0',
        transition: 'background-color 0.2s ease',
      }}
    >
      {/* Top Banner Toolbar */}
      <div
        style={{
          maxWidth: 420,
          width: '100%',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: 12,
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <span style={{ fontSize: 18 }}>📱</span>
          <span style={{ fontSize: 13, fontWeight: 600, color: theme === 'dark' ? '#94a3b8' : '#475569' }}>
            Expo / React Native 模擬器展示視圖
          </span>
        </div>
        <button
          type="button"
          onClick={onToggleTheme}
          style={{
            padding: '5px 10px',
            fontSize: 12,
            fontWeight: 600,
            borderRadius: 8,
            border: 'none',
            background: theme === 'dark' ? '#1e293b' : '#ffffff',
            color: theme === 'dark' ? '#f8fafc' : '#0f172a',
            cursor: 'pointer',
            boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
          }}
        >
          {theme === 'dark' ? '☀️ 淺色' : '🌙 深色'}
        </button>
      </div>

      {/* Device Body */}
      <div
        style={{
          width: 390,
          height: 780,
          borderRadius: 48,
          backgroundColor: theme === 'dark' ? '#111827' : '#ffffff',
          border: '10px solid #1e293b',
          boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.45)',
          overflow: 'hidden',
          display: 'flex',
          flexDirection: 'column',
          position: 'relative',
        }}
      >
        {/* Status Bar */}
        <div
          style={{
            height: 44,
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            padding: '0 24px',
            fontSize: 14,
            fontWeight: 600,
            color: 'var(--text-main)',
            userSelect: 'none',
          }}
        >
          <span>{timeStr}</span>
          {/* Dynamic Island Pill */}
          <div
            style={{
              width: 100,
              height: 22,
              backgroundColor: '#000000',
              borderRadius: 12,
            }}
          />
          <span style={{ fontSize: 12 }}>5G 100%</span>
        </div>

        {/* Screen Content */}
        <div style={{ flex: 1, overflowY: 'auto', padding: '0 18px 24px' }}>{children}</div>

        {/* Home Bar Indicator */}
        <div
          style={{
            height: 20,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}
        >
          <div
            style={{
              width: 120,
              height: 4,
              backgroundColor: 'var(--text-sub)',
              borderRadius: 2,
              opacity: 0.4,
            }}
          />
        </div>
      </div>
    </div>
  );
};
