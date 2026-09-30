import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import toast from 'react-hot-toast';
import { Lock, User, LogIn, GraduationCap, Users, ShieldCheck } from 'lucide-react';
import ThemeToggle from '../components/ThemeToggle';

export default function LandingPage() {
  const { login }       = useAuth();
  const navigate        = useNavigate();
  const [form, setForm] = useState({ username: '', password: '' });
  const [busy, setBusy] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setBusy(true);
    try {
      const user = await login(form.username, form.password);
      toast.success(`Welcome back, ${user.full_name}`);
      navigate(`/${user.role}`);
    } catch (err) {
      toast.error(err.response?.data?.detail || err.response?.data?.message || 'Login failed. Check your credentials.');
    } finally {
      setBusy(false);
    }
  };

  return (
    <div style={s.page}>
      <div style={{ position: 'fixed', top: 20, right: 20, zIndex: 100 }}>
        <ThemeToggle showLabel={true} />
      </div>
      <div style={s.card}>
        <div style={s.header}>
          <img src="/kwasu.png" alt="Kwara State University" style={s.logoImg} />
          <h1 style={s.title}>SPSEMS</h1>
          <p style={s.subtitle}>Smart Project Supervision &amp; Evaluation Management System</p>
          <div style={s.divider} />
        </div>

        <form onSubmit={handleSubmit} style={s.form}>
          <div style={s.fieldWrap}>
            <label style={s.label}>Username</label>
            <div style={s.inputWrap}>
              <User size={15} style={s.inputIcon} />
              <input
                style={s.input}
                type="text"
                placeholder="Enter your username"
                value={form.username}
                onChange={e => setForm({ ...form, username: e.target.value })}
                required
                autoComplete="username"
              />
            </div>
          </div>

          <div style={s.fieldWrap}>
            <label style={s.label}>Password</label>
            <div style={s.inputWrap}>
              <Lock size={15} style={s.inputIcon} />
              <input
                style={s.input}
                type="password"
                placeholder="Enter your password"
                value={form.password}
                onChange={e => setForm({ ...form, password: e.target.value })}
                required
                autoComplete="current-password"
              />
            </div>
          </div>

          <button type="submit" style={busy ? { ...s.btn, opacity: 0.6 } : s.btn} disabled={busy}>
            <LogIn size={16} />
            {busy ? 'Signing in...' : 'Sign In'}
          </button>
        </form>

        <div style={s.registerSection}>
          <p style={s.registerLabel}>New to SPSEMS? Register as:</p>
          <div style={s.registerRow}>
            <Link to="/register" style={s.regBtn}>
              <GraduationCap size={13} />
              Student
            </Link>
            <Link to="/register/lecturer" style={s.regBtn}>
              <Users size={13} />
              Lecturer
            </Link>
            <Link to="/register/admin" style={{ ...s.regBtn, background: 'rgba(20,83,45,0.5)', borderColor: '#14532d' }}>
              <ShieldCheck size={13} />
              Admin
            </Link>
          </div>
        </div>

        <div style={s.demoBox}>
          <p style={s.demoTitle}>Demo Credentials</p>
          <div style={s.demoGrid}>
            <DemoItem role="Admin / HOD"   user="admin"       pass="password123" />
            <DemoItem role="Supervisor"    user="supervisor1" pass="password123" />
            <DemoItem role="Student"       user="student1"    pass="password123" />
          </div>
        </div>
      </div>
    </div>
  );
}

function DemoItem({ role, user, pass }) {
  return (
    <div style={{ marginBottom: 6, display: 'flex', alignItems: 'center', gap: 6 }}>
      <span style={{ fontWeight: 600, color: '#9ca3af', fontSize: 11, width: 80 }}>{role}</span>
      <code style={s.code}>{user}</code>
      <span style={{ color: '#4b5563', fontSize: 11 }}>/</span>
      <code style={s.code}>{pass}</code>
    </div>
  );
}

const s = {
  page: {
    minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center',
    background: 'var(--auth-bg, linear-gradient(135deg, #050505 0%, #0d2010 40%, #16a34a 70%, #050505 100%))',
    padding: 20,
    position: 'relative',
  },
  card: {
    background: 'var(--auth-card-bg, rgba(15,15,15,0.97))', borderRadius: 16, padding: '40px 36px',
    width: '100%', maxWidth: 440,
    boxShadow: 'var(--auth-card-shadow, 0 0 0 1px rgba(22,163,74,0.2), 0 24px 64px rgba(0,0,0,0.6))',
    backdropFilter: 'blur(12px)',
  },
  header:  { textAlign: 'center', marginBottom: 28 },
  logoImg: { height: 52, display: 'block', margin: '0 auto 14px' },
  title:    { fontSize: 26, fontWeight: 800, color: 'var(--text-primary, #ffffff)', marginBottom: 6, letterSpacing: '-0.5px' },
  subtitle: { fontSize: 12, color: 'var(--text-dim, #6b7280)', lineHeight: 1.6 },
  divider:  { width: 40, height: 2, background: '#16a34a', margin: '16px auto 0', borderRadius: 2 },
  form:     { display: 'flex', flexDirection: 'column', gap: 14 },
  fieldWrap: { display: 'flex', flexDirection: 'column', gap: 6 },
  label:    { fontSize: 12, fontWeight: 600, color: 'var(--text-muted, #9ca3af)', letterSpacing: '0.3px' },
  inputWrap: { position: 'relative', display: 'flex', alignItems: 'center' },
  inputIcon: { position: 'absolute', left: 12, color: 'var(--text-dim, #4b5563)', pointerEvents: 'none' },
  input: {
    width: '100%', padding: '11px 14px 11px 36px',
    background: 'var(--bg-input, #0f0f0f)', border: '1px solid var(--border-input, rgba(255,255,255,0.1))',
    borderRadius: 8, fontSize: 13, outline: 'none', color: 'var(--text-primary, #ffffff)',
    transition: 'border-color 0.2s',
  },
  btn: {
    marginTop: 4, padding: '12px 0', background: '#16a34a', color: '#fff',
    border: 'none', borderRadius: 8, fontWeight: 700, fontSize: 14,
    cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8,
    letterSpacing: '0.2px',
  },
  registerSection: { marginTop: 22 },
  registerLabel:   { textAlign: 'center', fontSize: 11, color: 'var(--text-dim, #6b7280)', marginBottom: 10, fontWeight: 500, textTransform: 'uppercase', letterSpacing: '0.5px' },
  registerRow:     { display: 'flex', gap: 8, justifyContent: 'center' },
  regBtn: {
    padding: '7px 14px', background: 'rgba(22,163,74,0.12)', color: '#22c55e',
    border: '1px solid rgba(22,163,74,0.25)', borderRadius: 7, fontWeight: 600,
    fontSize: 12, textDecoration: 'none', display: 'flex', alignItems: 'center', gap: 5,
  },
  demoBox: {
    marginTop: 20, background: 'var(--bg-card-subtle, rgba(255,255,255,0.03))', border: '1px solid var(--border-subtle, rgba(255,255,255,0.07))',
    borderRadius: 10, padding: '14px 16px',
  },
  demoTitle: { fontWeight: 700, fontSize: 10, color: 'var(--text-dim, #6b7280)', marginBottom: 10, textTransform: 'uppercase', letterSpacing: '0.8px' },
  demoGrid:  { fontSize: 12 },
  code: { background: 'rgba(22,163,74,0.1)', color: 'var(--color-brand-light, #4ade80)', padding: '1px 6px', borderRadius: 4, fontSize: 11, fontFamily: 'monospace' },
};
