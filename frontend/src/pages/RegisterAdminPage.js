import React, { useState, useEffect } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import { ShieldCheck } from 'lucide-react';
import api from '../services/api';
import toast from 'react-hot-toast';
import ThemeToggle from '../components/ThemeToggle';
import { resolveLogoUrl } from '../utils/logoHelper';

export default function RegisterAdminPage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const instSlug = (searchParams.get('institution') || 'kwasu').toLowerCase();

  const [institution, setInstitution] = useState({
    name: instSlug === 'kwasu' ? 'Kwara State University' : 'Institution Portal',
    code: instSlug === 'kwasu' ? 'KWASU' : instSlug.toUpperCase(),
    slug: instSlug,
    logo_url: instSlug === 'kwasu' ? '/kwasu.png' : '',
    primary_color: '#16a34a',
  });

  const [busy, setBusy] = useState(false);
  const [form, setForm] = useState({
    full_name: '', username: '', email: '', phone: '',
    admin_code: '', password: '', confirm_password: '',
  });

  useEffect(() => {
    api.get(`/institutions/by-slug/${instSlug}`)
      .then(res => {
        if (res.data) {
          setInstitution({
            name: res.data.name,
            code: res.data.code,
            slug: res.data.slug,
            logo_url: res.data.logo_url || (instSlug === 'kwasu' ? '/kwasu.png' : ''),
            primary_color: res.data.primary_color || '#16a34a',
          });
        }
      })
      .catch(() => {});
  }, [instSlug]);

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
        role:             'admin',
        full_name:        form.full_name,
        username:         form.username,
        email:            form.email,
        password:         form.password,
        phone:            form.phone || undefined,
        admin_code:       form.admin_code,
        institution_slug: institution.slug,
      });
      toast.success('Admin registration submitted. Awaiting approval before you can log in.');
      navigate(institution.slug === 'kwasu' ? '/login' : `/login/${institution.slug}`);
    } catch (err) {
      toast.error(err.response?.data?.detail || err.response?.data?.message || 'Registration failed. Check your admin code.');
    } finally {
      setBusy(false);
    }
  };

  const primaryColor = institution.primary_color || '#16a34a';

  return (
    <div style={s.page}>
      <div style={{ position: 'fixed', top: 20, right: 20, zIndex: 100 }}>
        <ThemeToggle showLabel={true} />
      </div>
      <div style={s.card}>
        <div style={s.header}>
          {resolveLogoUrl(institution.logo_url) ? (
            <img
              src={resolveLogoUrl(institution.logo_url)}
              alt={institution.name}
              style={s.logoImg}
              onError={(e) => {
                if (institution.slug === 'kwasu') {
                  e.target.src = '/kwasu.png';
                } else {
                  e.target.style.display = 'none';
                  const fb = document.getElementById('inst-admin-fallback');
                  if (fb) fb.style.display = 'flex';
                }
              }}
            />
          ) : institution.slug === 'kwasu' ? (
            <img src="/kwasu.png" alt="KWASU" style={s.logoImg} />
          ) : null}
          <div
            id="inst-admin-fallback"
            style={{
              ...s.logoFallbackBadge,
              display: resolveLogoUrl(institution.logo_url) || institution.slug === 'kwasu' ? 'none' : 'flex',
              background: `${primaryColor}22`,
              border: `2px solid ${primaryColor}55`,
              color: primaryColor,
            }}
          >
            {institution.code || 'SP'}
          </div>
          <div style={s.titleRow}>
            <ShieldCheck size={20} color={primaryColor} />
            <h2 style={s.title}>{institution.code} Admin Registration</h2>
          </div>
          <p style={s.subtitle}>Create an Admin / HOD account for {institution.name}</p>
          <div style={{ ...s.divider, background: primaryColor }} />
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

          <button
            type="submit"
            style={busy ? { ...s.btn, background: primaryColor, opacity: 0.6 } : { ...s.btn, background: primaryColor }}
            disabled={busy}
          >
            {busy ? 'Submitting...' : `Create ${institution.code} Admin Account`}
          </button>
        </form>

        <p style={s.footer}>
          Already have an account?{' '}
          <Link
            to={institution.slug === 'kwasu' ? '/login' : `/login/${institution.slug}`}
            style={{ ...s.link, color: primaryColor }}
          >
            Sign in
          </Link>
          {'  ·  '}
          <Link
            to={`/register?institution=${institution.slug}`}
            style={{ ...s.link, color: primaryColor }}
          >
            Student
          </Link>
          {'  ·  '}
          <Link
            to={`/register/lecturer?institution=${institution.slug}`}
            style={{ ...s.link, color: primaryColor }}
          >
            Lecturer
          </Link>
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
    background: 'var(--auth-bg, linear-gradient(135deg, #050505 0%, #0a1a0a 40%, #14532d 70%, #050505 100%))',
    padding: '24px 16px',
    position: 'relative',
  },
  card: {
    background: 'var(--auth-card-bg, rgba(15,15,15,0.97))', borderRadius: 16, padding: '36px 32px',
    width: '100%', maxWidth: 560,
    boxShadow: 'var(--auth-card-shadow, 0 0 0 1px rgba(22,163,74,0.15), 0 24px 64px rgba(0,0,0,0.6))',
  },
  header:   { textAlign: 'center', marginBottom: 24 },
  logoImg:  { height: 46, display: 'block', margin: '0 auto 14px' },
  logoFallbackBadge: {
    width: 48,
    height: 48,
    borderRadius: 12,
    margin: '0 auto 14px',
    alignItems: 'center',
    justifyContent: 'center',
    fontWeight: 800,
    fontSize: 16,
    letterSpacing: '1px',
  },
  titleRow: { display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8, marginBottom: 6 },
  title:    { fontSize: 22, fontWeight: 800, color: 'var(--text-primary, #ffffff)', letterSpacing: '-0.3px' },
  subtitle: { fontSize: 12, color: 'var(--text-dim, #6b7280)' },
  divider:  { width: 32, height: 2, background: '#16a34a', margin: '14px auto 0', borderRadius: 2 },
  form:     { display: 'flex', flexDirection: 'column', gap: 14 },
  label:    { display: 'block', fontSize: 11, fontWeight: 600, color: 'var(--text-muted, #9ca3af)', marginBottom: 5, letterSpacing: '0.3px', textTransform: 'uppercase' },
  input: {
    width: '100%', padding: '10px 12px',
    background: 'var(--bg-input, #0f0f0f)', border: '1px solid var(--border-input, rgba(255,255,255,0.1))',
    borderRadius: 7, fontSize: 13, outline: 'none', color: 'var(--text-primary, #fff)', boxSizing: 'border-box',
  },
  btn: {
    marginTop: 4, padding: '12px 0', background: '#14532d', color: '#fff',
    border: 'none', borderRadius: 8, fontWeight: 700, fontSize: 14, cursor: 'pointer',
  },
  notice: {
    background: 'rgba(22,163,74,0.08)', border: '1px solid rgba(22,163,74,0.2)',
    borderRadius: 8, padding: '10px 14px', fontSize: 12, color: '#4ade80',
  },
  footer: { textAlign: 'center', marginTop: 18, fontSize: 12, color: 'var(--text-dim, #6b7280)' },
  link:   { color: '#22c55e', fontWeight: 600, textDecoration: 'none' },
};
