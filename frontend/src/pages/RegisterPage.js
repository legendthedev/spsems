import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { GraduationCap, Users, Info } from 'lucide-react';
import api from '../services/api';
import toast from 'react-hot-toast';
import ThemeToggle from '../components/ThemeToggle';

const DEPARTMENTS = [
  'Computer Science', 'Software Engineering', 'Information Technology',
  'Cyber Security', 'Data Science', 'Electrical Engineering',
  'Mechanical Engineering', 'Mathematics', 'Physics',
];

const LEVELS = ['100', '200', '300', '400', 'PGD', 'MSc', 'PhD'];

export default function RegisterPage() {
  const navigate = useNavigate();
  const [busy, setBusy] = useState(false);
  const [supervisors, setSupervisors] = useState([]);
  const [form, setForm] = useState({
    full_name: '', username: '', email: '', password: '', confirm_password: '',
    phone: '', department: '', level: '', matric_number: '', research_domain: '',
    main_supervisor_id: '',
  });

  const isPostgrad = ['msc', 'phd'].includes((form.level || '').toLowerCase());

  useEffect(() => {
    api.get('/auth/supervisors-public')
      .then(res => {
        if (res.data?.supervisors) setSupervisors(res.data.supervisors);
      })
      .catch(() => {});
  }, []);

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
        role:               'student',
        full_name:          form.full_name,
        username:           form.username,
        email:              form.email,
        password:           form.password,
        phone:              form.phone || undefined,
        department:         form.department,
        level:              form.level,
        matric_number:      form.matric_number,
        research_domain:    form.research_domain || undefined,
        main_supervisor_id: isPostgrad && form.main_supervisor_id ? parseInt(form.main_supervisor_id, 10) : undefined,
      });
      toast.success('Registration submitted. Awaiting admin approval before you can log in.');
      navigate('/login');
    } catch (err) {
      toast.error(err.response?.data?.detail || err.response?.data?.message || 'Registration failed.');
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
          <img src="/kwasu.png" alt="KWASU" style={s.logoImg} />
          <div style={s.titleRow}>
            <GraduationCap size={20} color="#16a34a" />
            <h2 style={s.title}>Student Registration</h2>
          </div>
          <p style={s.subtitle}>Create your SPSEMS student account</p>
          <div style={s.divider} />
        </div>

        <form onSubmit={handleSubmit} style={s.form}>
          <Row>
            <Field label="Full Name *"    value={form.full_name}    onChange={v => set('full_name', v)}    placeholder="Your full name"     required />
            <Field label="Username *"     value={form.username}     onChange={v => set('username', v)}     placeholder="Choose a username"  required />
          </Row>
          <Row>
            <Field label="Email *"  type="email" value={form.email} onChange={v => set('email', v)} placeholder="you@example.com" required />
            <Field label="Phone"    type="tel"   value={form.phone} onChange={v => set('phone', v)} placeholder="Optional" />
          </Row>
          <Row>
            <Field label="Matric Number *" value={form.matric_number} onChange={v => set('matric_number', v)} placeholder="e.g. CSC/2021/001" required />
            <div style={{ flex: 1 }}>
              <label style={s.label}>Level *</label>
              <select style={s.input} value={form.level} onChange={e => set('level', e.target.value)} required>
                <option value="">Select level</option>
                {LEVELS.map(l => <option key={l} value={l}>{l}</option>)}
              </select>
            </div>
          </Row>
          <Row>
            <div style={{ flex: 1 }}>
              <label style={s.label}>Department *</label>
              <select style={s.input} value={form.department} onChange={e => set('department', e.target.value)} required>
                <option value="">Select department</option>
                {DEPARTMENTS.map(d => <option key={d} value={d}>{d}</option>)}
              </select>
            </div>
            <Field label="Research Domain" value={form.research_domain} onChange={v => set('research_domain', v)} placeholder="e.g. Machine Learning" />
          </Row>

          {isPostgrad && (
            <div style={s.postgradCard}>
              <div style={{ display: 'flex', alignItems: 'flex-start', gap: 10, marginBottom: 12 }}>
                <Users size={18} color="#22c55e" style={{ marginTop: 2, flexShrink: 0 }} />
                <div>
                  <h4 style={{ fontSize: 13, fontWeight: 700, color: '#4ade80', margin: 0 }}>
                    Postgraduate Dual-Supervisor Allocation ({form.level})
                  </h4>
                  <p style={{ fontSize: 12, color: '#9ca3af', margin: '4px 0 0', lineHeight: 1.4 }}>
                    As an {form.level} student, you will be assigned <strong>two supervisors</strong>: 1 Main Supervisor and 1 Co-Supervisor (automatically assigned at random from active faculty).
                  </p>
                </div>
              </div>

              <div>
                <label style={s.label}>Preferred Main Supervisor (Optional)</label>
                <select
                  style={s.input}
                  value={form.main_supervisor_id}
                  onChange={e => set('main_supervisor_id', e.target.value)}
                >
                  <option value="">Auto-assign Main Supervisor (recommended - lowest workload)</option>
                  {supervisors
                    .filter(sup => !form.department || sup.department === form.department)
                    .map(sup => (
                      <option key={sup.supervisor_id} value={sup.supervisor_id}>
                        {sup.full_name} ({sup.department}) {sup.expertise_areas ? `— ${sup.expertise_areas}` : ''}
                      </option>
                    ))}
                </select>
                <p style={{ fontSize: 11, color: '#6b7280', marginTop: 4, display: 'flex', alignItems: 'center', gap: 4 }}>
                  <Info size={12} />
                  Your Co-Supervisor will be assigned automatically at random upon registration.
                </p>
              </div>
            </div>
          )}

          <Row>
            <Field label="Password *"         type="password" value={form.password}         onChange={v => set('password', v)}         placeholder="Min 6 characters" required />
            <Field label="Confirm Password *"  type="password" value={form.confirm_password} onChange={v => set('confirm_password', v)} placeholder="Repeat password"   required />
          </Row>


          <div style={s.notice}>
            After submitting, your account will be reviewed by the HOD before you can log in.
          </div>

          <button type="submit" style={busy ? { ...s.btn, opacity: 0.6 } : s.btn} disabled={busy}>
            {busy ? 'Submitting...' : 'Create Student Account'}
          </button>
        </form>

        <p style={s.footer}>
          Already have an account?{' '}<Link to="/login" style={s.link}>Sign in</Link>
          {'  ·  '}
          <Link to="/register/lecturer" style={s.link}>Lecturer registration</Link>
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
    background: 'var(--auth-bg, linear-gradient(135deg, #050505 0%, #0d2010 40%, #16a34a 70%, #050505 100%))',
    padding: '24px 16px',
    position: 'relative',
  },
  card: {
    background: 'var(--auth-card-bg, rgba(15,15,15,0.97))', borderRadius: 16, padding: '36px 32px',
    width: '100%', maxWidth: 700,
    boxShadow: 'var(--auth-card-shadow, 0 0 0 1px rgba(22,163,74,0.2), 0 24px 64px rgba(0,0,0,0.6))',
  },
  header:   { textAlign: 'center', marginBottom: 24 },
  logoImg:  { height: 46, display: 'block', margin: '0 auto 14px' },
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
    marginTop: 4, padding: '12px 0', background: '#16a34a', color: '#fff',
    border: 'none', borderRadius: 8, fontWeight: 700, fontSize: 14, cursor: 'pointer',
  },
  notice: {
    background: 'rgba(22,163,74,0.08)', border: '1px solid rgba(22,163,74,0.2)',
    borderRadius: 8, padding: '10px 14px', fontSize: 12, color: '#4ade80',
  },
  postgradCard: {
    background: 'rgba(22,163,74,0.06)', border: '1px solid rgba(22,163,74,0.25)',
    borderRadius: 10, padding: '14px 16px', display: 'flex', flexDirection: 'column', gap: 10,
  },
  footer: { textAlign: 'center', marginTop: 18, fontSize: 12, color: 'var(--text-dim, #6b7280)' },
  link:   { color: '#22c55e', fontWeight: 600, textDecoration: 'none' },
};

