import React, { useState } from 'react';
import { useTheme } from '../context/ThemeContext';
import { Laptop, Sun, Moon, Check, Sparkles, X } from 'lucide-react';
import toast from 'react-hot-toast';

export default function ThemePromptModal() {
  const {
    showPrompt,
    themePreference,
    systemIsDark,
    selectPreference,
    confirmTheme,
    dismissPrompt,
  } = useTheme();

  const [selected, setSelected] = useState(themePreference || 'system');

  if (!showPrompt) return null;

  const handleSelect = (pref) => {
    setSelected(pref);
    selectPreference(pref); // live preview!
  };

  const handleConfirm = () => {
    confirmTheme(selected);
    const label = selected === 'system' ? 'Device Setting' : (selected === 'light' ? 'Light Mode' : 'Dark Mode');
    toast.success(`Theme set to ${label}!`);
  };

  const handleQuickDevice = () => {
    confirmTheme('system');
    toast.success('Theme set to Device Setting (System Default)!');
  };

  return (
    <div style={styles.overlay}>
      <div style={styles.backdrop} onClick={dismissPrompt} />
      <div style={styles.modal} className="theme-modal-animate" role="dialog" aria-modal="true" aria-labelledby="theme-modal-title">
        <button style={styles.closeBtn} onClick={dismissPrompt} title="Close" aria-label="Close theme selection">
          <X size={18} />
        </button>

        <div style={styles.header}>
          <div style={styles.iconCircle}>
            <Sparkles size={22} color="#16a34a" />
          </div>
          <h2 id="theme-modal-title" style={styles.title}>Choose Your Appearance</h2>
          <p style={styles.subtitle}>
            Select how you would like KWASU SPSEMS to look on your screen. You can customize this anytime in your portal settings.
          </p>
        </div>

        <div style={styles.optionsGrid}>
          {/* Option 1: Device Setting (Preferred) */}
          <div
            style={{
              ...styles.card,
              ...(selected === 'system' ? styles.cardActive : {}),
            }}
            onClick={() => handleSelect('system')}
          >
            <div style={styles.cardHeader}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                <div style={{ ...styles.cardIconWrap, background: selected === 'system' ? 'rgba(22,163,74,0.2)' : 'rgba(255,255,255,0.06)' }}>
                  <Laptop size={20} color={selected === 'system' ? '#22c55e' : '#9ca3af'} />
                </div>
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <span style={styles.cardTitle}>Use Device Setting</span>
                    <span style={styles.recBadge}>Recommended</span>
                  </div>
                  <span style={styles.cardSub}>Matches your OS or device theme</span>
                </div>
              </div>
              <div style={{ ...styles.checkCircle, ...(selected === 'system' ? styles.checkCircleActive : {}) }}>
                {selected === 'system' && <Check size={14} color="#fff" />}
              </div>
            </div>

            <p style={styles.cardDesc}>
              Automatically adjusts between light and dark mode based on your phone, tablet, or computer's system preference.
            </p>
            <div style={styles.systemStatus}>
              Detected on your device:{' '}
              <strong style={{ color: systemIsDark ? '#38bdf8' : '#eab308' }}>
                {systemIsDark ? '🌙 Dark Mode' : '☀️ Light Mode'}
              </strong>
            </div>
          </div>

          {/* Option 2: Light Mode */}
          <div
            style={{
              ...styles.card,
              ...(selected === 'light' ? styles.cardActive : {}),
            }}
            onClick={() => handleSelect('light')}
          >
            <div style={styles.cardHeader}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                <div style={{ ...styles.cardIconWrap, background: selected === 'light' ? 'rgba(22,163,74,0.2)' : 'rgba(255,255,255,0.06)' }}>
                  <Sun size={20} color={selected === 'light' ? '#22c55e' : '#eab308'} />
                </div>
                <div>
                  <span style={styles.cardTitle}>Light Mode</span>
                  <span style={styles.cardSub}>Clean &amp; high contrast</span>
                </div>
              </div>
              <div style={{ ...styles.checkCircle, ...(selected === 'light' ? styles.checkCircleActive : {}) }}>
                {selected === 'light' && <Check size={14} color="#fff" />}
              </div>
            </div>
            <p style={styles.cardDesc}>
              A crisp, clear white theme with dark text and university green accents, ideal for brightly lit workspaces.
            </p>
          </div>

          {/* Option 3: Dark Mode */}
          <div
            style={{
              ...styles.card,
              ...(selected === 'dark' ? styles.cardActive : {}),
            }}
            onClick={() => handleSelect('dark')}
          >
            <div style={styles.cardHeader}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                <div style={{ ...styles.cardIconWrap, background: selected === 'dark' ? 'rgba(22,163,74,0.2)' : 'rgba(255,255,255,0.06)' }}>
                  <Moon size={20} color={selected === 'dark' ? '#22c55e' : '#38bdf8'} />
                </div>
                <div>
                  <span style={styles.cardTitle}>Dark Mode</span>
                  <span style={styles.cardSub}>Sleek &amp; easy on the eyes</span>
                </div>
              </div>
              <div style={{ ...styles.checkCircle, ...(selected === 'dark' ? styles.checkCircleActive : {}) }}>
                {selected === 'dark' && <Check size={14} color="#fff" />}
              </div>
            </div>
            <p style={styles.cardDesc}>
              An elegant dark aesthetic designed for low glare, improved battery life, and comfortable evening reading.
            </p>
          </div>
        </div>

        <div style={styles.actions}>
          <button style={styles.laterBtn} onClick={dismissPrompt}>
            Ask Me Later
          </button>
          <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap', justifyContent: 'flex-end' }}>
            {selected !== 'system' && (
              <button style={styles.deviceBtn} onClick={handleQuickDevice}>
                Use Device Setting
              </button>
            )}
            <button style={styles.saveBtn} onClick={handleConfirm}>
              Confirm Selection
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

const styles = {
  overlay: {
    position: 'fixed',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    zIndex: 9999,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    padding: 16,
  },
  backdrop: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    background: 'rgba(0,0,0,0.7)',
    backdropFilter: 'blur(8px)',
  },
  modal: {
    position: 'relative',
    background: 'var(--bg-modal, #111111)',
    color: 'var(--text-primary, #ffffff)',
    borderRadius: 16,
    border: '1px solid var(--border-subtle, rgba(255,255,255,0.12))',
    boxShadow: 'var(--shadow-dropdown, 0 24px 64px rgba(0,0,0,0.8))',
    width: '100%',
    maxWidth: 580,
    padding: '28px 24px',
    zIndex: 10000,
  },
  closeBtn: {
    position: 'absolute',
    top: 16,
    right: 16,
    background: 'none',
    border: 'none',
    color: 'var(--text-dim, #6b7280)',
    cursor: 'pointer',
    padding: 6,
    borderRadius: 8,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
  },
  header: {
    textAlign: 'center',
    marginBottom: 20,
  },
  iconCircle: {
    width: 48,
    height: 48,
    borderRadius: '50%',
    background: 'rgba(22,163,74,0.12)',
    border: '1px solid rgba(22,163,74,0.25)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    margin: '0 auto 12px',
  },
  title: {
    fontSize: 20,
    fontWeight: 800,
    color: 'var(--text-primary, #ffffff)',
    margin: 0,
    letterSpacing: '-0.3px',
  },
  subtitle: {
    fontSize: 13,
    color: 'var(--text-muted, #9ca3af)',
    marginTop: 6,
    lineHeight: 1.4,
  },
  optionsGrid: {
    display: 'flex',
    flexDirection: 'column',
    gap: 10,
    marginBottom: 20,
  },
  card: {
    background: 'var(--bg-card, #171717)',
    border: '1.5px solid var(--border-subtle, rgba(255,255,255,0.08))',
    borderRadius: 12,
    padding: '14px 16px',
    cursor: 'pointer',
    transition: 'all 0.15s ease',
  },
  cardActive: {
    borderColor: '#16a34a',
    background: 'rgba(22,163,74,0.06)',
    boxShadow: '0 0 0 1px #16a34a',
  },
  cardHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  cardIconWrap: {
    width: 36,
    height: 36,
    borderRadius: 8,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
  },
  cardTitle: {
    fontSize: 14,
    fontWeight: 700,
    color: 'var(--text-primary, #ffffff)',
  },
  cardSub: {
    display: 'block',
    fontSize: 11,
    color: 'var(--text-dim, #6b7280)',
    marginTop: 1,
  },
  recBadge: {
    background: 'rgba(22,163,74,0.18)',
    color: '#22c55e',
    fontSize: 10,
    fontWeight: 700,
    padding: '2px 7px',
    borderRadius: 10,
    textTransform: 'uppercase',
    letterSpacing: '0.4px',
    border: '1px solid rgba(22,163,74,0.3)',
  },
  checkCircle: {
    width: 20,
    height: 20,
    borderRadius: '50%',
    border: '1.5px solid var(--border-input, rgba(255,255,255,0.2))',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
  },
  checkCircleActive: {
    background: '#16a34a',
    borderColor: '#16a34a',
  },
  cardDesc: {
    fontSize: 12,
    color: 'var(--text-muted, #9ca3af)',
    marginTop: 8,
    marginBottom: 0,
    lineHeight: 1.4,
  },
  systemStatus: {
    marginTop: 8,
    paddingTop: 8,
    borderTop: '1px solid var(--border-subtle, rgba(255,255,255,0.06))',
    fontSize: 11,
    color: 'var(--text-dim, #6b7280)',
  },
  actions: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    gap: 12,
    flexWrap: 'wrap',
    paddingTop: 8,
  },
  laterBtn: {
    background: 'none',
    border: 'none',
    color: 'var(--text-dim, #6b7280)',
    fontSize: 13,
    fontWeight: 600,
    cursor: 'pointer',
    padding: '8px 12px',
  },
  deviceBtn: {
    background: 'var(--bg-card, #1c1c1c)',
    color: 'var(--text-primary, #ffffff)',
    border: '1px solid var(--border-subtle, rgba(255,255,255,0.12))',
    borderRadius: 8,
    padding: '9px 15px',
    fontSize: 13,
    fontWeight: 600,
    cursor: 'pointer',
  },
  saveBtn: {
    background: '#16a34a',
    color: '#ffffff',
    border: 'none',
    borderRadius: 8,
    padding: '9px 18px',
    fontSize: 13,
    fontWeight: 700,
    cursor: 'pointer',
    boxShadow: '0 2px 8px rgba(22,163,74,0.3)',
  },
};
