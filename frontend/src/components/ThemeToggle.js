import React, { useState, useRef, useEffect } from 'react';
import { useTheme } from '../context/ThemeContext';
import { Laptop, Sun, Moon, Check, Sparkles } from 'lucide-react';
import toast from 'react-hot-toast';

export default function ThemeToggle({ showLabel = false, compact = false }) {
  const { themePreference, selectPreference, openPrompt } = useTheme();
  const [open, setOpen] = useState(false);
  const containerRef = useRef(null);

  useEffect(() => {
    const handleOutsideClick = (e) => {
      if (containerRef.current && !containerRef.current.contains(e.target)) {
        setOpen(false);
      }
    };
    if (open) {
      document.addEventListener('mousedown', handleOutsideClick);
      return () => document.removeEventListener('mousedown', handleOutsideClick);
    }
  }, [open]);

  const handlePick = (pref) => {
    selectPreference(pref);
    setOpen(false);
    const names = { system: 'Device Setting', light: 'Light Mode', dark: 'Dark Mode' };
    toast.success(`Theme: ${names[pref]}`);
  };

  const currentIcon = () => {
    if (themePreference === 'system') return <Laptop size={16} />;
    if (themePreference === 'light') return <Sun size={16} />;
    return <Moon size={16} />;
  };

  const getLabel = () => {
    if (themePreference === 'system') return 'Device';
    if (themePreference === 'light') return 'Light';
    return 'Dark';
  };

  return (
    <div ref={containerRef} style={{ position: 'relative', display: 'inline-block' }}>
      <button
        onClick={() => setOpen(!open)}
        title={`Theme: ${getLabel()} (Click to change)`}
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: 6,
          padding: compact ? '6px 8px' : '7px 11px',
          background: 'var(--bg-card, #171717)',
          color: 'var(--text-secondary, #e5e7eb)',
          border: '1px solid var(--border-subtle, rgba(255,255,255,0.12))',
          borderRadius: 8,
          fontSize: 12,
          fontWeight: 600,
          cursor: 'pointer',
          transition: 'all 0.15s ease',
        }}
      >
        <span style={{ color: themePreference === 'light' ? '#eab308' : (themePreference === 'dark' ? '#38bdf8' : '#22c55e') }}>
          {currentIcon()}
        </span>
        {showLabel && <span>{getLabel()}</span>}
      </button>

      {open && (
        <div
          style={{
            position: 'absolute',
            top: 'calc(100% + 6px)',
            right: 0,
            background: 'var(--bg-dropdown, #171717)',
            border: '1px solid var(--border-subtle, rgba(255,255,255,0.12))',
            borderRadius: 10,
            boxShadow: 'var(--shadow-dropdown, 0 10px 30px rgba(0,0,0,0.5))',
            minWidth: 180,
            padding: 4,
            zIndex: 9999,
          }}
        >
          <div style={{ padding: '6px 10px 4px', fontSize: 10, fontWeight: 700, color: 'var(--text-dim, #6b7280)', textTransform: 'uppercase', letterSpacing: '0.6px' }}>
            Appearance
          </div>

          <Item
            icon={<Laptop size={14} />}
            label="Device Setting"
            badge="Auto"
            active={themePreference === 'system'}
            onClick={() => handlePick('system')}
          />
          <Item
            icon={<Sun size={14} color="#eab308" />}
            label="Light Mode"
            active={themePreference === 'light'}
            onClick={() => handlePick('light')}
          />
          <Item
            icon={<Moon size={14} color="#38bdf8" />}
            label="Dark Mode"
            active={themePreference === 'dark'}
            onClick={() => handlePick('dark')}
          />

          <div style={{ height: 1, background: 'var(--border-subtle, rgba(255,255,255,0.08))', margin: '4px 0' }} />

          <button
            onClick={() => {
              setOpen(false);
              openPrompt();
            }}
            style={{
              width: '100%',
              display: 'flex',
              alignItems: 'center',
              gap: 8,
              padding: '7px 10px',
              background: 'none',
              border: 'none',
              color: 'var(--text-muted, #9ca3af)',
              fontSize: 11,
              fontWeight: 500,
              cursor: 'pointer',
              borderRadius: 6,
              textAlign: 'left',
            }}
          >
            <Sparkles size={13} color="#16a34a" />
            <span>Theme settings…</span>
          </button>
        </div>
      )}
    </div>
  );
}

function Item({ icon, label, badge, active, onClick }) {
  return (
    <button
      onClick={onClick}
      style={{
        width: '100%',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '8px 10px',
        background: active ? 'rgba(22,163,74,0.1)' : 'none',
        color: active ? '#22c55e' : 'var(--text-primary, #ffffff)',
        border: 'none',
        borderRadius: 6,
        fontSize: 12,
        fontWeight: active ? 700 : 500,
        cursor: 'pointer',
        textAlign: 'left',
        transition: 'background 0.15s ease',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
        {icon}
        <span>{label}</span>
        {badge && (
          <span style={{ fontSize: 9, padding: '1px 5px', borderRadius: 4, background: 'rgba(22,163,74,0.15)', color: '#22c55e', fontWeight: 700 }}>
            {badge}
          </span>
        )}
      </div>
      {active && <Check size={14} color="#22c55e" />}
    </button>
  );
}
