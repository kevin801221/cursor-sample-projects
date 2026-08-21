import React, { useState } from 'react';
import { Button } from './Button';
import { Input } from './Input';
import { Card } from './Card';
import { Modal } from './Modal';
import { tokens } from '../tokens/tokens';

export const Showcase: React.FC = () => {
  const [theme, setTheme] = useState<'light' | 'dark'>('dark');
  const [btnVariant, setBtnVariant] = useState<'primary' | 'secondary' | 'outline' | 'ghost' | 'danger'>('primary');
  const [btnSize, setBtnSize] = useState<'sm' | 'md' | 'lg'>('md');
  const [btnLoading, setBtnLoading] = useState(false);
  const [btnDisabled, setBtnDisabled] = useState(false);

  const [inputVal, setInputVal] = useState('kevin@antigravity.ai');
  const [inputError, setInputError] = useState(false);

  const [isModalOpen, setIsModalOpen] = useState(false);
  const [activeTab, setActiveTab] = useState<'components' | 'tokens' | 'rules'>('components');

  const toggleTheme = () => {
    const next = theme === 'light' ? 'dark' : 'light';
    setTheme(next);
    document.documentElement.setAttribute('data-theme', next);
  };

  return (
    <div style={{ maxWidth: 1100, margin: '0 auto', padding: '40px 24px' }}>
      {/* Top Header */}
      <header
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          paddingBottom: 24,
          borderBottom: '1px solid var(--color-surface-border)',
          marginBottom: 32,
        }}
      >
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <h1 style={{ fontSize: 26, fontWeight: 700, letterSpacing: '-0.02em' }}>
              Design System Component Library
            </h1>
            <span
              style={{
                fontSize: 12,
                padding: '3px 8px',
                borderRadius: 9999,
                background: 'rgba(59, 130, 246, 0.15)',
                color: 'var(--color-primary)',
                fontWeight: 600,
              }}
            >
              Project 3 · A11y Ready
            </span>
          </div>
          <p style={{ color: 'var(--color-text-secondary)', fontSize: 14, marginTop: 4 }}>
            Figma 截圖轉 React 元件庫 · Design Tokens · Cursor Rules 嚴格把關
          </p>
        </div>

        <div style={{ display: 'flex', gap: 12 }}>
          <Button variant="secondary" size="sm" onClick={toggleTheme}>
            {theme === 'dark' ? '☀️ 淺色模式' : '🌙 深色模式'}
          </Button>
          <Button variant="primary" size="sm" onClick={() => setIsModalOpen(true)}>
            🚀 體驗 Modal 對話框
          </Button>
        </div>
      </header>

      {/* Nav Tabs */}
      <div style={{ display: 'flex', gap: 10, marginBottom: 28 }}>
        <Button
          variant={activeTab === 'components' ? 'primary' : 'ghost'}
          size="sm"
          onClick={() => setActiveTab('components')}
        >
          🧩 元件展示台
        </Button>
        <Button
          variant={activeTab === 'tokens' ? 'primary' : 'ghost'}
          size="sm"
          onClick={() => setActiveTab('tokens')}
        >
          🎨 Design Tokens
        </Button>
        <Button
          variant={activeTab === 'rules' ? 'primary' : 'ghost'}
          size="sm"
          onClick={() => setActiveTab('rules')}
        >
          🛡️ Cursor Rules 規範
        </Button>
      </div>

      {activeTab === 'components' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 36 }}>
          {/* Section 1: Button */}
          <Card
            variant="elevated"
            title="1. Button 元件 (多狀態與無障礙焦點環)"
            subtitle="支援 5 種 Variant、3 種 Size、Loading 旋轉、圖示插槽與 Focus-visible"
          >
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 24, alignItems: 'center' }}>
              <div>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 12, marginBottom: 20 }}>
                  <Button variant="primary">Primary</Button>
                  <Button variant="secondary">Secondary</Button>
                  <Button variant="outline">Outline</Button>
                  <Button variant="ghost">Ghost</Button>
                  <Button variant="danger">Danger</Button>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                  <Button size="sm">Small</Button>
                  <Button size="md">Medium</Button>
                  <Button size="lg">Large</Button>
                  <Button isLoading>儲存中</Button>
                  <Button disabled>禁用狀態</Button>
                </div>
              </div>

              {/* Interactive Control */}
              <div
                style={{
                  background: 'var(--color-surface-hover)',
                  padding: 16,
                  borderRadius: 8,
                  border: '1px solid var(--color-surface-border)',
                }}
              >
                <div style={{ fontSize: 13, fontWeight: 600, marginBottom: 12, color: 'var(--color-text-primary)' }}>
                  即時 Props 控制台
                </div>
                <div style={{ display: 'flex', gap: 8, marginBottom: 10, flexWrap: 'wrap' }}>
                  {(['primary', 'secondary', 'outline', 'ghost', 'danger'] as const).map((v) => (
                    <button
                      key={v}
                      type="button"
                      style={{
                        padding: '4px 8px',
                        fontSize: 12,
                        borderRadius: 4,
                        border: '1px solid var(--color-surface-border)',
                        background: btnVariant === v ? 'var(--color-primary)' : 'var(--color-surface)',
                        color: btnVariant === v ? '#fff' : 'inherit',
                        cursor: 'pointer',
                      }}
                      onClick={() => setBtnVariant(v)}
                    >
                      {v}
                    </button>
                  ))}
                </div>
                <div style={{ display: 'flex', gap: 8, marginBottom: 10 }}>
                  {(['sm', 'md', 'lg'] as const).map((s) => (
                    <button
                      key={s}
                      type="button"
                      style={{
                        padding: '4px 8px',
                        fontSize: 12,
                        borderRadius: 4,
                        border: '1px solid var(--color-surface-border)',
                        background: btnSize === s ? 'var(--color-primary)' : 'var(--color-surface)',
                        color: btnSize === s ? '#fff' : 'inherit',
                        cursor: 'pointer',
                      }}
                      onClick={() => setBtnSize(s)}
                    >
                      {s.toUpperCase()}
                    </button>
                  ))}
                </div>
                <div style={{ display: 'flex', gap: 16, alignItems: 'center', marginBottom: 12 }}>
                  <label style={{ fontSize: 12, display: 'flex', alignItems: 'center', gap: 4 }}>
                    <input
                      type="checkbox"
                      checked={btnLoading}
                      onChange={(e) => setBtnLoading(e.target.checked)}
                    />
                    isLoading
                  </label>
                  <label style={{ fontSize: 12, display: 'flex', alignItems: 'center', gap: 4 }}>
                    <input
                      type="checkbox"
                      checked={btnDisabled}
                      onChange={(e) => setBtnDisabled(e.target.checked)}
                    />
                    disabled
                  </label>
                </div>
                <div style={{ marginTop: 12, display: 'flex', justifyContent: 'center' }}>
                  <Button
                    variant={btnVariant}
                    size={btnSize}
                    isLoading={btnLoading}
                    disabled={btnDisabled}
                  >
                    動態按鈕預覽 ({btnVariant} / {btnSize})
                  </Button>
                </div>
              </div>
            </div>
          </Card>

          {/* Section 2: Input */}
          <Card
            variant="elevated"
            title="2. Input 元件 (標籤、輔助文字、錯誤狀態與 ARIA)"
            subtitle="自動生成唯一 ID，透過 aria-describedby 與 aria-invalid 完美支援螢幕報讀"
          >
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 24 }}>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
                <Input
                  label="電子郵件"
                  placeholder="請輸入公司信箱"
                  value={inputVal}
                  onChange={(e) => setInputVal(e.target.value)}
                  helperText="我們不會將您的信箱洩漏給第三方"
                  isError={inputError}
                  errorMessage={inputError ? '電子郵件格式不正確，請重新檢查' : undefined}
                />
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => setInputError(!inputError)}
                >
                  切換錯誤狀態（目前：{inputError ? '有錯誤' : '正常'}）
                </Button>
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
                <Input
                  label="搜尋關鍵字"
                  placeholder="搜尋專案或功能..."
                  startIcon={<span>🔍</span>}
                  helperText="輸入文字後按 Enter 立即檢索"
                />
                <Input
                  label="禁用欄位"
                  value="PRO-2026-TOKEN-LOCKED"
                  disabled
                  helperText="此欄位由系統自動指派，不可手動編輯"
                />
              </div>
            </div>
          </Card>

          {/* Section 3: Card & Modal */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 24 }}>
            <Card
              variant="interactive"
              title="3. Card 元件 (互動型)"
              subtitle="滑鼠懸停具備 Elevation 動態位移與 Focus 效果"
              footer={
                <div style={{ display: 'flex', gap: 8 }}>
                  <Button variant="ghost" size="sm">
                    取消
                  </Button>
                  <Button variant="primary" size="sm">
                    查看詳情
                  </Button>
                </div>
              }
            >
              <p style={{ color: 'var(--color-text-secondary)', fontSize: 14 }}>
                這是一張具備 <code>variant="interactive"</code> 的卡片，完全遵照 Design Tokens 的圓角、間距與邊框色彩，懸停時會平滑向上浮動。
              </p>
            </Card>

            <Card
              variant="elevated"
              title="4. Modal 對話框 (ESC 與焦點捕獲)"
              subtitle="具備無障礙規格的 Dialog 與 Backdrop Blur 效果"
            >
              <p style={{ color: 'var(--color-text-secondary)', fontSize: 14, marginBottom: 16 }}>
                點擊下方按鈕可開啟對話框。開啟時會自動捕獲焦點至第一個按鈕，按鍵盤 <code>ESC</code> 鍵或點擊黑色遮罩即可快速關閉。
              </p>
              <Button
                variant="primary"
                onClick={() => setIsModalOpen(true)}
              >
                開啟對話框展示
              </Button>
            </Card>
          </div>
        </div>
      )}

      {activeTab === 'tokens' && (
        <Card variant="elevated" title="Design Tokens 規格表" subtitle="tailwind.config.js / tokens.ts 集中管理">
          <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
            <div>
              <h4 style={{ fontSize: 14, fontWeight: 600, marginBottom: 12 }}>色彩色票系統 (Colors)</h4>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 12 }}>
                {[
                  { name: 'Primary', var: 'var(--color-primary)', hex: '#3b82f6' },
                  { name: 'Secondary', var: 'var(--color-secondary)', hex: '#64748b' },
                  { name: 'Danger', var: 'var(--color-danger)', hex: '#ef4444' },
                  { name: 'Success', var: 'var(--color-success)', hex: '#10b981' },
                ].map((c) => (
                  <div
                    key={c.name}
                    style={{
                      padding: 14,
                      borderRadius: 8,
                      border: '1px solid var(--color-surface-border)',
                      background: 'var(--color-surface)',
                    }}
                  >
                    <div
                      style={{
                        height: 48,
                        borderRadius: 6,
                        background: c.var,
                        marginBottom: 8,
                      }}
                    />
                    <div style={{ fontSize: 13, fontWeight: 600 }}>{c.name}</div>
                    <div style={{ fontSize: 12, color: 'var(--color-text-muted)' }}>{c.hex}</div>
                  </div>
                ))}
              </div>
            </div>

            <div>
              <h4 style={{ fontSize: 14, fontWeight: 600, marginBottom: 12 }}>間距與圓角階梯 (Spacing & Radii)</h4>
              <div style={{ display: 'flex', gap: 16 }}>
                {Object.entries(tokens.spacing).map(([k, v]) => (
                  <div
                    key={k}
                    style={{
                      padding: '10px 16px',
                      background: 'var(--color-surface-hover)',
                      borderRadius: 8,
                      fontSize: 13,
                    }}
                  >
                    <code>spacing.{k}</code>: {v}
                  </div>
                ))}
              </div>
            </div>
          </div>
        </Card>
      )}

      {activeTab === 'rules' && (
        <Card variant="elevated" title="Cursor Rules 守則 (.cursor/rules/design-system.mdc)" subtitle="限制 AI 嚴格使用 Token，禁止寫死十六進位">
          <div
            style={{
              background: 'var(--color-surface-hover)',
              padding: 16,
              borderRadius: 8,
              fontFamily: 'monospace',
              fontSize: 13,
              lineHeight: 1.6,
              color: 'var(--color-text-primary)',
            }}
          >
            <p><strong>// 紅線條款 1：</strong> 一律使用 tokens.colors / CSS 變數，禁止寫死 <code>#1E40AF</code> 或 <code>rgb(...)</code>。</p>
            <p><strong>// 紅線條款 2：</strong> 元件間距必須使用 <code>tokens.spacing</code> (xs=4px, sm=8px, md=16px, lg=24px, xl=32px)。</p>
            <p><strong>// 紅線條款 3：</strong> 表單與互動元素必須具備 A11y 標籤 (aria-invalid, aria-describedby, focus-visible)。</p>
          </div>
        </Card>
      )}

      {/* Modal Instance */}
      <Modal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        title="確認執行操作"
        footer={
          <div style={{ display: 'flex', gap: 10 }}>
            <Button variant="ghost" size="sm" onClick={() => setIsModalOpen(false)}>
              取消 (ESC)
            </Button>
            <Button variant="primary" size="sm" onClick={() => setIsModalOpen(false)}>
              確認完成
            </Button>
          </div>
        }
      >
        <p>這是一個具備無障礙規格的 Modal 對話框：</p>
        <ul style={{ paddingLeft: 20, marginTop: 8 }}>
          <li>支援鍵盤 <code>ESC</code> 鍵關閉</li>
          <li>焦點捕獲在對話框內部</li>
          <li>背景具備 Backdrop Blur 毛玻璃模糊效果</li>
        </ul>
      </Modal>
    </div>
  );
};
