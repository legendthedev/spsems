import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { ShieldCheck } from 'lucide-react';
import api from '../services/api';
import toast from 'react-hot-toast';

export default function RegisterAdminPage() {
  const navigate = useNavigate();
  const [busy, setBusy] = useState(false);
  const [form, setForm] = useState({
    full_name: '', username: '', email: '', phone: '',
    admin_code: '', password: '', confirm_password: '',
  });

  const set = (k, v) => setForm(prev => ({ ...prev, [k]: v }));

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (form.password !== form.confirm_password) {
      toast.error('Passwords do not match.');
      return;
    }
    setBusy(true);
    try {
      await api.post('/auth/register-public', {
        role:       'admin',
        full_name:  form.full_name,
        username:   form.username,
        email:      form.email,
        password:   form.password,
        phone:      form.phone || undefined,
        admin_code: form.admin_code,
      });
      toast.success('Admin registration submitted. Awaiting approval before you can log in.');
      navigate('/login');
    } catch (err) {
      toast.error(err.response?.data?.detail || err.response?.data?.message || 'Registration failed. Check your admin code.');
    } finally {
      setBusy(false);
    }
  };

  return (
    <div style={s.page}>
      <div style={s.card}>
        <div style={s.header}>
          <img src="/kwasu.png" alt="KWASU" style={s.logoImg} />
          <div style={s.titleRow}>
            <ShieldCheck size={20} color="#16a34a" />
            <h2 style={s.title}>Admin Registration</h2>
          </div>
          <p style={s.subtitle}>Create an Admin / HOD account</p>
          <div style={s.divider} />
        </div>

        <form onSubmit={handleSubmit} style={s.form}>
          <Row>
            <Field label="Full Name *" value={form.full_name} onChange={v => set('full_name', v)} placeholder="Your full name" required />
            <Field label="Username *"  value={form.username}  onChange={v => set('username', v)}  placeholder="Choose a username" required />
          </Row>
          <Row>
            <Field label="Email *" type="email" value={form.email} onChange={v => set('email', v)} placeholder="you@kwasu.edu.ng" required />
            <Field label="Phone"   type="tel"   value={form.phone} onChange={v => set('phone', v)} placeholder="Optional" />
          </Row>

          <div>
            <label style={s.label}>Admin Registration Code *</label>
            <input
              style={{ ...s.input, borderColor: 'rgba(22,163,74,0.3)' }}
              type="password"
              value={form.admin_code}
              onChange={e => set('admin_code', e.target.value)}
              placeholder="Enter the admin access code"
              required
            />
            <p style={{ fontSize: 11, color: '#4b5563', marginTop: 5 }}>
              Contact your system administrator to obtain the admin registration code.
            </p>
          </div>

          <Row>
            <Field label="Password *"         type="password" value={form.password}         onChange={v => set('password', v)}         placeholder="Min 6 characters" required />
            <Field label="Confirm Password *"  type="password" value={form.confirm_password} onChange={v => set('confirm_password', v)} placeholder="Repeat password"   required />
          </Row>

          <div style={s.notice}>
            Admin accounts require a valid registration code and are subject to approval before activation.
          </div>

          <button type="submit" style={busy ? { ...s.btn, opacity: 0.6 } : s.btn} disabled={busy}>
            {busy ? 'Submitting...' : 'Create Admin Account'}
          </button>
        </form>

        <p style={s.footer}>
          Already have an account?{' '}<Link to="/login" style={s.link}>Sign in</Link>
          {'  ·  '}
          <Link to="/register" style={s.link}>Student</Link>
          {'  ·  '}
          <Link to="/register/lecturer" style={s.link}>Lecturer</Link>
        </p>
      </div>
    </div>
  );
}

function Row({ children }) {
  return <div style={{ display: 'flex', gap: 12 }}>{children}</div>;
}

function Field({ label, type = 'text', value, onChange, placeholder, required }) {
  return (
    <div style={{ flex: 1 }}>
      <label style={s.label}>{label}</label>
      <input
        style={s.input}
        type={type}
        value={value}
        onChange={e => onChange(e.target.value)}
        placeholder={placeholder}
        required={required}
      />
    </div>
  );
}

const s = {
  page: {
    minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center',
    background: 'linear-gradient(135deg, #050505 0%, #0a1a0a 40%, #14532d 70%, #050505 100%)',
    padding: '24px 16px',
  },
  card: {
    background: 'rgba(15,15,15,0.97)', borderRadius: 16, padding: '36px 32px',
    width: '100%', maxWidth: 560,
    boxShadow: '0 0 0 1px rgba(22,163,74,0.15), 0 24px 64px rgba(0,0,0,0.6)',
  },
  header:   { textAlign: 'center', marginBottom: 24 },
  logoImg:  { height: 46, display: 'block', margin: '0 auto 14px' },
  titleRow: { display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8, marginBottom: 6 },
  title:    { fontSize: 22, fontWeight: 800, color: '#ffffff', letterSpacing: '-0.3px' },
  subtitle: { fontSize: 12, color: '#6b7280' },
  divider:  { width: 32, height: 2, background: '#16a34a', margin: '14px auto 0', borderRadius: 2 },
  form:     { display: 'flex', flexDirection: 'column', gap: 14 },
  label:    { display: 'block', fontSize: 11, fontWeight: 600, color: '#9ca3af', marginBottom: 5, letterSpacing: '0.3px', textTransform: 'uppercase' },
  input: {
    width: '100%', padding: '10px 12px',
    background: '#0f0f0f', border: '1px solid rgba(255,255,255,0.1)',
    borderRadius: 7, fontSize: 13, outline: 'none', color: '#fff', boxSizing: 'border-box',
  },
  btn: {
    marginTop: 4, padding: '12px 0', background: '#14532d', color: '#fff',
    border: 'none', borderRadius: 8, fontWeight: 700, fontSize: 14, cursor: 'pointer',
  },
  notice: {
    background: 'rgba(22,163,74,0.08)', border: '1px solid rgba(22,163,74,0.2)',
    borderRadius: 8, padding: '10px 14px', fontSize: 12, color: '#4ade80',
  },
  footer: { textAlign: 'center', marginTop: 18, fontSize: 12, color: '#6b7280' },
  link:   { color: '#22c55e', fontWeight: 600, textDecoration: 'none' },
};
