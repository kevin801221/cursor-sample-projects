/**
 * Design Tokens
 * 集中管理色彩、間距、圓角與字型，全站元件禁止使用任意十六進位或非規格值
 */
export const tokens = {
  colors: {
    primary: {
      DEFAULT: 'var(--color-primary, #3b82f6)',
      hover: 'var(--color-primary-hover, #2563eb)',
      active: 'var(--color-primary-active, #1d4ed8)',
      foreground: 'var(--color-primary-fg, #ffffff)',
    },
    secondary: {
      DEFAULT: 'var(--color-secondary, #64748b)',
      hover: 'var(--color-secondary-hover, #475569)',
      foreground: 'var(--color-secondary-fg, #ffffff)',
    },
    danger: {
      DEFAULT: 'var(--color-danger, #ef4444)',
      hover: 'var(--color-danger-hover, #dc2626)',
      foreground: 'var(--color-danger-fg, #ffffff)',
    },
    success: {
      DEFAULT: 'var(--color-success, #10b981)',
      foreground: 'var(--color-success-fg, #ffffff)',
    },
    background: 'var(--color-bg, #ffffff)',
    surface: 'var(--color-surface, #f8fafc)',
    surfaceBorder: 'var(--color-surface-border, #e2e8f0)',
    text: {
      primary: 'var(--color-text-primary, #0f172a)',
      secondary: 'var(--color-text-secondary, #64748b)',
      muted: 'var(--color-text-muted, #94a3b8)',
    },
  },
  spacing: {
    xs: '4px',
    sm: '8px',
    md: '16px',
    lg: '24px',
    xl: '32px',
  },
  radii: {
    sm: '4px',
    md: '8px',
    lg: '12px',
    full: '9999px',
  },
  shadows: {
    sm: '0 1px 2px 0 rgb(0 0 0 / 0.05)',
    md: '0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1)',
    lg: '0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1)',
    xl: '0 20px 25px -5px rgb(0 0 0 / 0.1), 0 8px 10px -6px rgb(0 0 0 / 0.1)',
  }
} as const;
