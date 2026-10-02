/* eslint-disable no-unused-vars */
import React, { useState, useEffect } from 'react';
import { useNavigate, useParams, useLocation, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import toast from 'react-hot-toast';
// eslint-disable-next-line no-unused-vars
import {
  Lock, User, LogIn, GraduationCap, Users, ShieldCheck, ArrowLeft,
  ChevronDown, School, KeyRound, Lightbulb, CheckCircle2, ShieldAlert
} from 'lucide-react';
import api from '../services/api';
import ThemeToggle from '../components/ThemeToggle';
import { resolveLogoUrl } from '../utils/logoHelper';

export default function LandingPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const { slug: routeSlug } = useParams();
  const location = useLocation();

  const querySlug = new URLSearchParams(location.search).get('institution') ||
                    new URLSearchParams(location.search).get('school');
  const tokenQuery = new URLSearchParams(location.search).get('token') || '';
  const targetSlug = (routeSlug || querySlug || 'kwasu').toLowerCase();

  // Institution Branding State
  const [institution, setInstitution] = useState({
    name: targetSlug === 'kwasu' ? 'Kwara State University' : 'Institution Portal',
    code: targetSlug === 'kwasu' ? 'KWASU' : targetSlug.toUpperCase(),
    slug: targetSlug,
    logo_url: targetSlug === 'kwasu' ? '/kwasu.png' : '',
    primary_color: '#16a34a',
    secondary_color: '#080808',
    domain: '',
    contact_email: targetSlug === 'kwasu' ? 'ict@kwasu.edu.ng' : '',
    session: '2025/2026',
    semester: 'First Semester',
    status: 'active',
    is_verified: true,
  });

  const [allInstitutions, setAllInstitutions] = useState([]);
  const [showSchoolPicker, setShowSchoolPicker] = useState(false);
  const [form, setForm] = useState({
    username: targetSlug === 'kwasu' ? 'ict@kwasu.edu.ng' : '',
    password: '',
    verification_token: tokenQuery,
  });
  const [busy, setBusy] = useState(false);

  // Fetch institution data whenever slug changes
  useEffect(() => {
    async function loadInstitution() {
      try {
        const res = await api.get(`/institutions/by-slug/${targetSlug}`);
        if (res.data) {
          const instData = res.data;
          setInstitution({
            name: instData.name,
            code: instData.code,
            slug: instData.slug,
            logo_url: instData.logo_url || (targetSlug === 'kwasu' ? '/kwasu.png' : ''),
            primary_color: instData.primary_color || '#16a34a',
            secondary_color: instData.secondary_color || '#080808',
            domain: instData.domain,
            contact_email: instData.contact_email,
            session: instData.session || '2025/2026',
            semester: instData.semester || 'First Semester',
            status: instData.status,
            is_verified: instData.is_verified,
            has_verification_token: instData.has_verification_token,
          });

          // Automatically set official main email address as default username
          if (instData.contact_email) {
            setForm(prev => ({
              ...prev,
              username: prev.username && prev.username !== 'ict@kwasu.edu.ng' ? prev.username : instData.contact_email,
              verification_token: prev.verification_token || tokenQuery || '',
            }));
          }
        }
      } catch (err) {
        console.warn(`Could not load institution for slug '${targetSlug}', default to KWASU.`);
      }
    }
    loadInstitution();
  }, [targetSlug, tokenQuery]);

  // Fetch all schools for the dropdown switcher
  useEffect(() => {
    async function fetchDirectory() {
      try {
        const res = await api.get('/institutions/directory');
        if (res.data?.institutions) {
          setAllInstitutions(res.data.institutions);
        }
      } catch (e) {
        console.warn('Directory fetch failed:', e);
      }
    }
    fetchDirectory();
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setBusy(true);
    try {
      const user = await login(
        form.username,
        form.password,
        form.verification_token || null,
        institution.slug
      );
      toast.success(`Welcome back, ${user.full_name}`);
      navigate(`/${user.role}`);
    } catch (err) {
      toast.error(
        err.response?.data?.detail ||
        err.response?.data?.message ||
        'Login failed. Please check your credentials.'
      );
    } finally {
      setBusy(false);
    }
  };

  const primaryColor = institution.primary_color || '#16a34a';
  const isKwasu = institution.slug === 'kwasu' || institution.code === 'KWASU';

  return (
    <div
      style={{
        ...s.page,
        background: `radial-gradient(ellipse at 50% 15%, ${primaryColor}26 0%, #050505 85%)`,
      }}
    >
      <div style={{ position: 'fixed', top: 20, right: 20, zIndex: 100 }}>
        <ThemeToggle showLabel={true} />
      </div>

      <div
        style={{
          ...s.card,
          boxShadow: `0 0 0 1px ${primaryColor}33, 0 24px 64px rgba(0,0,0,0.7)`,
        }}
      >
        {/* Top Navigation Row */}
        <div style={s.navTopRow}>
          <Link to="/" style={s.backLink}>
            <ArrowLeft size={13} />
            <span>All Institutions</span>
          </Link>

          {/* Institution Switcher Button */}
          <div style={{ position: 'relative' }}>
            <button
              type="button"
              onClick={() => setShowSchoolPicker(!showSchoolPicker)}
              style={{
                ...s.nodeIndicator,
                color: primaryColor,
                borderColor: `${primaryColor}55`,
                background: `${primaryColor}18`,
              }}
            >
              <span>{institution.code} Portal</span>
              <ChevronDown size={12} />
            </button>

            {showSchoolPicker && (
              <div style={s.dropdownMenu}>
                <div style={s.dropdownTitle}>SWITCH INSTITUTION</div>
                {allInstitutions.map((sch) => (
                  <Link
                    key={sch.id}
                    to={`/login/${sch.slug}`}
                    onClick={() => setShowSchoolPicker(false)}
                    style={{
                      ...s.dropdownItem,
                      color: sch.slug === institution.slug ? primaryColor : 'var(--text-primary, #fff)',
                      fontWeight: sch.slug === institution.slug ? 700 : 500,
                    }}
                  >
                    {resolveLogoUrl(sch.logo) && (sch.slug === 'kwasu' || sch.logo !== '/kwasu.png') ? (
                      <img
                        src={resolveLogoUrl(sch.logo)}
                        alt=""
                        style={s.dropdownLogo}
                        onError={(e) => { e.target.style.display = 'none'; }}
                      />
                    ) : (
                      <div
                        style={{
                          ...s.dropdownFallback,
                          background: `${sch.primary_color || '#16a34a'}22`,
                          color: sch.primary_color || '#16a34a',
                          border: `1px solid ${sch.primary_color || '#16a34a'}44`,
                        }}
                      >
                        {sch.code ? sch.code.slice(0, 3) : (sch.name ? sch.name.slice(0, 2).toUpperCase() : 'UN')}
                      </div>
                    )}
                    <div style={{ display: 'flex', flexDirection: 'column' }}>
                      <span>{sch.name}</span>
                      <span style={{ fontSize: 10, color: 'var(--text-muted, #9ca3af)' }}>{sch.code}</span>
                    </div>
                  </Link>
                ))}
                <Link
                  to="/onboard"
                  onClick={() => setShowSchoolPicker(false)}
                  style={s.dropdownOnboardLink}
                >
                  <School size={12} />
                  <span>+ Onboard New University</span>
                </Link>
              </div>
            )}
          </div>
        </div>

        {/* Institution Brand Header */}
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
                  const fb = document.getElementById('inst-brand-fallback');
                  if (fb) fb.style.display = 'flex';
                }
              }}
            />
          ) : null}

          <div
            id="inst-brand-fallback"
            style={{
              ...s.logoFallbackBadge,
              display: resolveLogoUrl(institution.logo_url) ? 'none' : 'flex',
              background: `${primaryColor}22`,
              border: `2px solid ${primaryColor}55`,
              color: primaryColor,
            }}
          >
            {institution.code || (institution.name ? institution.name.slice(0, 2).toUpperCase() : 'SP')}
          </div>

          <div
            style={{
              ...s.nodeBadge,
              background: `${primaryColor}1a`,
              borderColor: `${primaryColor}40`,
              color: primaryColor,
            }}
          >
            <span style={{ ...s.nodeDot, background: primaryColor, boxShadow: `0 0 6px ${primaryColor}` }} />
            <span>{institution.name} (Active Node)</span>
          </div>

          <h1 style={s.title}>{institution.code} SPSEMS</h1>
          <p style={s.subtitle}>
            Smart Project Supervision &amp; Evaluation Management System
          </p>
          <div style={{ ...s.divider, background: primaryColor }} />
        </div>

        {/* Login Form */}
        <form onSubmit={handleSubmit} style={s.form}>
          <div style={s.fieldWrap}>
            <label style={s.label}>Institution Official Email / Username</label>
            <div style={s.inputWrap}>
              <User size={15} style={s.inputIcon} />
              <input
                style={s.input}
                type="text"
                placeholder={institution.contact_email ? `e.g. ${institution.contact_email}` : (isKwasu ? "e.g. ict@kwasu.edu.ng or student1" : "Enter your official email or username")}
                value={form.username}
                onChange={(e) => setForm({ ...form, username: e.target.value })}
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
                placeholder="Enter your account password"
                value={form.password}
                onChange={(e) => setForm({ ...form, password: e.target.value })}
                required
                autoComplete="current-password"
              />
            </div>
          </div>

          <div style={s.fieldWrap}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 5 }}>
              <label style={s.label}>Institution Verification Token</label>
              {institution.is_verified ? (
                <span style={{ fontSize: 11, color: '#22c55e', fontWeight: 600, display: 'inline-flex', alignItems: 'center', gap: 4 }}>
                  <CheckCircle2 size={12} />
                  Verified Node
                </span>
              ) : (
                <span style={{ fontSize: 11, color: '#f59e0b', fontWeight: 600, display: 'inline-flex', alignItems: 'center', gap: 4 }}>
                  <ShieldAlert size={12} />
                  Token Required
                </span>
              )}
            </div>
            <div style={s.inputWrap}>
              <KeyRound size={15} style={s.inputIcon} />
              <input
                style={s.input}
                type="text"
                placeholder="e.g. VTOK-XXXXXXXX... (Issued at onboarding)"
                value={form.verification_token}
                onChange={(e) => setForm({ ...form, verification_token: e.target.value })}
                autoComplete="off"
              />
            </div>
            <p style={{ margin: '4px 0 0', fontSize: 11, color: 'var(--text-dim, #6b7280)', lineHeight: 1.4 }}>
              Submit the token generated during the onboarding session to authenticate and unlock this portal.
            </p>
          </div>

          <button
            type="submit"
            style={{
              ...s.btn,
              background: primaryColor,
              opacity: busy ? 0.6 : 1,
            }}
            disabled={busy}
          >
            <LogIn size={16} />
            <span>{busy ? 'Signing in...' : `Sign In to ${institution.code} Portal`}</span>
          </button>
        </form>

        {/* Registration Section for this specific Institution */}
        <div style={s.registerSection}>
          <p style={s.registerLabel}>New to {institution.code}? Register as:</p>
          <div style={s.registerRow}>
            <Link
              to={`/register?institution=${institution.slug}`}
              style={{
                ...s.regBtn,
                color: primaryColor,
                background: `${primaryColor}14`,
                borderColor: `${primaryColor}30`,
              }}
            >
              <GraduationCap size={13} />
              <span>Student</span>
            </Link>
            <Link
              to={`/register/lecturer?institution=${institution.slug}`}
              style={{
                ...s.regBtn,
                color: primaryColor,
                background: `${primaryColor}14`,
                borderColor: `${primaryColor}30`,
              }}
            >
              <Users size={13} />
              <span>Lecturer</span>
            </Link>
            <Link
              to={`/register/admin?institution=${institution.slug}`}
              style={{
                ...s.regBtn,
                color: primaryColor,
                background: `${primaryColor}22`,
                borderColor: `${primaryColor}40`,
              }}
            >
              <ShieldCheck size={13} />
              <span>Admin</span>
            </Link>
          </div>
        </div>

        {/* Demo Credentials Box */}
        {isKwasu ? (
          <div style={s.demoBox}>
            <p style={s.demoTitle}>KWASU DEMO CREDENTIALS</p>
            <div style={s.demoGrid}>
              <DemoItem role="Admin / HOD" user="admin" pass="password123" color={primaryColor} />
              <DemoItem role="Supervisor" user="supervisor1" pass="password123" color={primaryColor} />
              <DemoItem role="Student" user="student1" pass="password123" color={primaryColor} />
            </div>
          </div>
        ) : (
          <div style={s.customSchoolHint}>
            <p style={{ margin: 0, fontSize: 11, color: 'var(--text-muted, #9ca3af)', lineHeight: 1.5, display: 'flex', alignItems: 'flex-start', gap: 6 }}>
              <Lightbulb size={14} color="#eab308" style={{ flexShrink: 0, marginTop: 2 }} />
              <span>
                <b>Institutional Portal</b>: Sign in using your {institution.name} administrative account,
                or use student/lecturer self-registration above with your <code style={s.code}>@{institution.domain}</code> email.
              </span>
            </p>
          </div>
        )}
      </div>
    </div>
  );
}

function DemoItem({ role, user, pass, color }) {
  return (
    <div style={{ marginBottom: 5, display: 'flex', alignItems: 'center', gap: 6 }}>
      <span style={{ fontWeight: 600, color: '#9ca3af', fontSize: 11, width: 80 }}>{role}</span>
      <code style={{ ...s.code, color: color || '#4ade80' }}>{user}</code>
      <span style={{ color: '#4b5563', fontSize: 11 }}>/</span>
      <code style={{ ...s.code, color: color || '#4ade80' }}>{pass}</code>
    </div>
  );
}

// ── STYLES ───────────────────────────────────────────────────────────────────
const s = {
  page: {
    minHeight: '100vh',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    padding: 20,
    position: 'relative',
    fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
  },
  card: {
    background: 'var(--auth-card-bg, rgba(15,15,15,0.97))',
    borderRadius: 16,
    padding: '32px 36px 36px',
    width: '100%',
    maxWidth: 450,
    backdropFilter: 'blur(12px)',
    transition: 'box-shadow 0.25s ease',
  },
  navTopRow: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 20,
    paddingBottom: 12,
    borderBottom: '1px solid var(--border-subtle, rgba(255,255,255,0.06))',
  },
  backLink: {
    display: 'inline-flex',
    alignItems: 'center',
    gap: 6,
    color: 'var(--text-muted, #9ca3af)',
    textDecoration: 'none',
    fontSize: 12,
    fontWeight: 500,
    transition: 'color 0.15s ease',
  },
  nodeIndicator: {
    display: 'inline-flex',
    alignItems: 'center',
    gap: 6,
    fontSize: 11,
    fontWeight: 700,
    padding: '4px 10px',
    borderRadius: 6,
    border: '1px solid',
    cursor: 'pointer',
    outline: 'none',
  },
  dropdownMenu: {
    position: 'absolute',
    top: 28,
    right: 0,
    background: 'var(--bg-card, #171717)',
    border: '1px solid var(--border-card, rgba(255,255,255,0.12))',
    borderRadius: 10,
    boxShadow: '0 10px 30px rgba(0,0,0,0.8)',
    padding: '8px 0',
    minWidth: 240,
    zIndex: 200,
  },
  dropdownTitle: {
    fontSize: 10,
    fontWeight: 800,
    color: 'var(--text-dim, #6b7280)',
    letterSpacing: '0.8px',
    padding: '6px 14px',
  },
  dropdownItem: {
    display: 'flex',
    alignItems: 'center',
    gap: 10,
    padding: '8px 14px',
    textDecoration: 'none',
    fontSize: 12,
    transition: 'background 0.15s ease',
  },
  dropdownLogo: {
    width: 22,
    height: 22,
    objectFit: 'contain',
    borderRadius: 4,
  },
  dropdownOnboardLink: {
    display: 'flex',
    alignItems: 'center',
    gap: 8,
    padding: '10px 14px 4px',
    borderTop: '1px solid var(--border-subtle, rgba(255,255,255,0.06))',
    color: '#22c55e',
    textDecoration: 'none',
    fontSize: 11,
    fontWeight: 700,
    marginTop: 4,
  },
  header: {
    textAlign: 'center',
    marginBottom: 24,
  },
  logoImg: {
    height: 54,
    width: 54,
    objectFit: 'contain',
    display: 'block',
    margin: '0 auto 10px',
    background: 'rgba(255,255,255,0.04)',
    borderRadius: 8,
    padding: 4,
  },
  logoFallbackBadge: {
    width: 54,
    height: 54,
    borderRadius: 12,
    alignItems: 'center',
    justifyContent: 'center',
    margin: '0 auto 10px',
    fontWeight: 800,
    fontSize: 16,
    letterSpacing: '0.5px',
  },
  dropdownFallback: {
    width: 24,
    height: 24,
    borderRadius: 6,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    fontSize: 9,
    fontWeight: 800,
    flexShrink: 0,
  },
  nodeBadge: {
    display: 'inline-flex',
    alignItems: 'center',
    gap: 6,
    fontSize: 11,
    fontWeight: 600,
    padding: '3px 10px',
    borderRadius: 999,
    marginBottom: 10,
    border: '1px solid',
  },
  nodeDot: {
    width: 6,
    height: 6,
    borderRadius: '50%',
  },
  title: {
    fontSize: 24,
    fontWeight: 800,
    color: 'var(--text-primary, #ffffff)',
    marginBottom: 4,
    letterSpacing: '-0.4px',
  },
  subtitle: {
    fontSize: 12,
    color: 'var(--text-dim, #6b7280)',
    lineHeight: 1.5,
  },
  divider: {
    width: 40,
    height: 2,
    margin: '14px auto 0',
    borderRadius: 2,
  },
  form: {
    display: 'flex',
    flexDirection: 'column',
    gap: 14,
  },
  fieldWrap: {
    display: 'flex',
    flexDirection: 'column',
    gap: 6,
  },
  label: {
    fontSize: 12,
    fontWeight: 600,
    color: 'var(--text-muted, #9ca3af)',
    letterSpacing: '0.3px',
  },
  inputWrap: {
    position: 'relative',
    display: 'flex',
    alignItems: 'center',
  },
  inputIcon: {
    position: 'absolute',
    left: 12,
    color: 'var(--text-dim, #4b5563)',
    pointerEvents: 'none',
  },
  input: {
    width: '100%',
    padding: '11px 14px 11px 36px',
    background: 'var(--bg-input, #0f0f0f)',
    border: '1px solid var(--border-input, rgba(255,255,255,0.1))',
    borderRadius: 8,
    fontSize: 13,
    outline: 'none',
    color: 'var(--text-primary, #ffffff)',
    transition: 'border-color 0.2s',
    boxSizing: 'border-box',
  },
  btn: {
    marginTop: 4,
    padding: '12px 0',
    color: '#fff',
    border: 'none',
    borderRadius: 8,
    fontWeight: 700,
    fontSize: 14,
    cursor: 'pointer',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    letterSpacing: '0.2px',
    boxShadow: '0 4px 16px rgba(0,0,0,0.3)',
    transition: 'opacity 0.15s ease',
  },
  registerSection: {
    marginTop: 20,
  },
  registerLabel: {
    textAlign: 'center',
    fontSize: 11,
    color: 'var(--text-dim, #6b7280)',
    marginBottom: 10,
    fontWeight: 500,
    textTransform: 'uppercase',
    letterSpacing: '0.5px',
  },
  registerRow: {
    display: 'flex',
    gap: 8,
    justifyContent: 'center',
  },
  regBtn: {
    padding: '7px 12px',
    borderRadius: 7,
    fontWeight: 600,
    fontSize: 11,
    textDecoration: 'none',
    display: 'flex',
    alignItems: 'center',
    gap: 5,
    border: '1px solid',
  },
  demoBox: {
    marginTop: 20,
    background: 'var(--bg-card-subtle, rgba(255,255,255,0.03))',
    border: '1px solid var(--border-subtle, rgba(255,255,255,0.07))',
    borderRadius: 10,
    padding: '14px 16px',
  },
  demoTitle: {
    fontWeight: 700,
    fontSize: 10,
    color: 'var(--text-dim, #6b7280)',
    marginBottom: 8,
    textTransform: 'uppercase',
    letterSpacing: '0.8px',
  },
  demoGrid: {
    fontSize: 12,
  },
  customSchoolHint: {
    marginTop: 18,
    padding: '12px 14px',
    background: 'var(--bg-card-subtle, rgba(255,255,255,0.03))',
    border: '1px solid var(--border-subtle, rgba(255,255,255,0.07))',
    borderRadius: 10,
  },
  code: {
    background: 'rgba(255,255,255,0.06)',
    padding: '1px 6px',
    borderRadius: 4,
    fontSize: 11,
    fontFamily: 'monospace',
  },
};
