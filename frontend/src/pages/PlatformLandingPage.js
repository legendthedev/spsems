import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  Building2, ArrowRight, ShieldCheck, GraduationCap, Users,
  Sparkles, Search, ChevronRight, School,
  Lock, Layers
} from 'lucide-react';
import api from '../services/api';
import ThemeToggle from '../components/ThemeToggle';

export default function PlatformLandingPage() {
  const [directory, setDirectory] = useState([]);
  const [search, setSearch] = useState('');

  useEffect(() => {
    async function fetchDirectory() {
      try {
        const res = await api.get('/institutions/directory');
        if (res.data?.institutions) {
          setDirectory(res.data.institutions);
        }
      } catch (err) {
        console.warn('Directory fetch fallback:', err);
      }
    }
    fetchDirectory();
  }, []);

  // Filter institutions based on search
  const filteredSchools = directory.filter(
    (inst) =>
      inst.name.toLowerCase().includes(search.toLowerCase()) ||
      inst.code.toLowerCase().includes(search.toLowerCase()) ||
      inst.domain.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div style={s.page}>
      {/* ── TOP NAVIGATION ──────────────────────────────────────────────── */}
      <header style={s.header}>
        <div style={s.navInner}>
          <div style={s.logoGroup}>
            <img src="/kwasu.png" alt="SPSEMS" style={s.navLogo} />
            <div>
              <div style={s.navBrand}>SPSEMS</div>
              <div style={s.navTagline}>National Higher Education Platform</div>
            </div>
          </div>

          <div style={s.navActions}>
            <a href="#existing-login" style={s.navAnchor}>
              Existing Login
            </a>
            <Link to="/onboard" style={s.navOnboardBtn}>
              <Building2 size={15} />
              <span>Onboard Institution</span>
            </Link>
            <ThemeToggle showLabel={false} />
          </div>
        </div>
      </header>

      {/* ── HERO & INSTITUTIONAL ONBOARDING SPOTLIGHT ─────────────────── */}
      <main style={s.main}>
        <section style={s.heroSection}>
          <div style={s.platformPill}>
            <Sparkles size={14} color="#22c55e" />
            <span>Autonomous Multi-University Supervision &amp; Evaluation Network</span>
          </div>

          <h1 style={s.heroHeading}>
            Smart Project Supervision &amp; Evaluation Management System
          </h1>

          <p style={s.heroSubheading}>
            A unified academic management ecosystem for universities, polytechnics, and colleges.
            Empowering institutions with AI-driven supervisor allocation, postgraduate dual-supervision governance,
            and end-to-end dissertation defense grading.
          </p>

          {/* ── PRIMARY CALLOUT: ARE YOU AN ACADEMIC INSTITUTION? ONBOARD YOUR UNIVERSITY ── */}
          <div style={s.heroOnboardCard}>
            <div style={s.heroOnboardLeft}>
              <div style={s.onboardIconBadge}>
                <Building2 size={32} color="#22c55e" />
              </div>
              <div style={s.onboardTextGroup}>
                <div style={s.onboardPre}>INSTITUTIONAL SELF-PROVISIONING</div>
                <h2 style={s.onboardTitle}>Are you an Academic Institution?</h2>
                <p style={s.onboardDesc}>
                  Onboard your university or polytechnic onto SPSEMS in minutes. Upload your official emblem to
                  automatically extract your custom brand colors, customize degree policies &amp; postgraduate
                  dual-supervisor regulations, and instantly provision an isolated tenant for your campus.
                </p>
                <div style={s.featurePillRow}>
                  <span style={s.featurePill}>✨ Instant Logo Color Extraction</span>
                  <span style={s.featurePill}>🎓 MSc &amp; PhD Dual Supervision</span>
                  <span style={s.featurePill}>🔒 Isolated Tenant Database</span>
                </div>
              </div>
            </div>

            <div style={s.heroOnboardRight}>
              <Link to="/onboard" style={s.heroCtaBtn}>
                <span>Onboard Your University</span>
                <ArrowRight size={18} />
              </Link>
              <span style={s.ctaNote}>Free institutional setup • Self-service activation</span>
            </div>
          </div>
        </section>

        {/* ── EXISTING INSTITUTION LOGIN SECTION ──────────────────────── */}
        <section id="existing-login" style={s.loginSection}>
          <div style={s.sectionHead}>
            <div style={s.badgeLabel}>
              <School size={15} color="#16a34a" />
              <span>CAMPUS GATEWAY</span>
            </div>
            <h2 style={s.sectionTitle}>Existing Institution Login</h2>
            <p style={s.sectionSubtitle}>
              Select your university to sign in to your institution's SPSEMS portal, submit project milestones,
              and manage supervision.
            </p>
          </div>

          {/* Search Bar for Institutions */}
          <div style={s.searchWrap}>
            <Search size={18} style={s.searchIcon} />
            <input
              style={s.searchInput}
              type="text"
              placeholder="Search your university or polytechnic (e.g. KWASU, UNILAG, Ibadan)..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>

          {/* FEATURED: KWASU SPSEMS (LIVE PRIMARY NODE) */}
          <div style={s.featuredKwasuCard}>
            <div style={s.featuredHeader}>
              <div style={s.featuredLogoWrap}>
                <img src="/kwasu.png" alt="KWASU Emblem" style={s.featuredLogo} />
                <div>
                  <div style={s.featuredBadgeRow}>
                    <span style={s.livePulse} />
                    <span style={s.featuredStatus}>LIVE &amp; OPERATIONAL (100% Active)</span>
                  </div>
                  <h3 style={s.featuredName}>Kwara State University (KWASU SPSEMS)</h3>
                  <div style={s.featuredMeta}>
                    <span>Domain: <b>kwasu.edu.ng</b></span>
                    <span>•</span>
                    <span>Malete, Kwara State</span>
                    <span>•</span>
                    <span>State University</span>
                  </div>
                </div>
              </div>

              <div style={s.featuredActionWrap}>
                <Link to="/login" style={s.kwasuLoginBtn}>
                  <Lock size={16} />
                  <span>Enter KWASU SPSEMS Login</span>
                  <ArrowRight size={16} />
                </Link>
              </div>
            </div>

            <div style={s.featuredDivider} />

            <div style={s.featuredBody}>
              <div style={s.featuredDescCol}>
                <p style={s.featuredDesc}>
                  Access your KWASU project supervision portal. Features automated allocation for undergraduate
                  and postgraduate (MSc / PhD dual-supervision), plagiarism checking, milestone submissions,
                  and defense evaluation.
                </p>

                {/* Quick Registration Links */}
                <div style={s.quickRegRow}>
                  <span style={s.quickRegLabel}>Direct Registration:</span>
                  <Link to="/register" style={s.quickRegBtn}>
                    <GraduationCap size={13} />
                    <span>Student Registration</span>
                  </Link>
                  <Link to="/register/lecturer" style={s.quickRegBtn}>
                    <Users size={13} />
                    <span>Lecturer Registration</span>
                  </Link>
                  <Link to="/register/admin" style={s.quickRegBtn}>
                    <ShieldCheck size={13} />
                    <span>HOD / Admin Access</span>
                  </Link>
                </div>
              </div>

              {/* Demo Credentials Box */}
              <div style={s.kwasuDemoBox}>
                <div style={s.kwasuDemoTitle}>KWASU DEMO CREDENTIALS</div>
                <div style={s.kwasuDemoList}>
                  <div style={s.kwasuDemoItem}>
                    <span style={s.kwasuDemoRole}>HOD / Admin:</span>
                    <code style={s.kwasuCode}>admin</code>
                    <span style={{ color: '#6b7280' }}>/</span>
                    <code style={s.kwasuCode}>password123</code>
                  </div>
                  <div style={s.kwasuDemoItem}>
                    <span style={s.kwasuDemoRole}>Supervisor:</span>
                    <code style={s.kwasuCode}>supervisor1</code>
                    <span style={{ color: '#6b7280' }}>/</span>
                    <code style={s.kwasuCode}>password123</code>
                  </div>
                  <div style={s.kwasuDemoItem}>
                    <span style={s.kwasuDemoRole}>Student:</span>
                    <code style={s.kwasuCode}>student1</code>
                    <span style={{ color: '#6b7280' }}>/</span>
                    <code style={s.kwasuCode}>password123</code>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* OTHER REGISTERED / ONBOARDED INSTITUTIONS GRID */}
          <div style={s.otherSchoolsSection}>
            <div style={s.otherSchoolsHead}>
              <h3 style={s.otherSchoolsTitle}>
                Registered Institutions Directory ({filteredSchools.length})
              </h3>
              <Link to="/onboard" style={s.addSchoolLink}>
                + Onboard New Institution
              </Link>
            </div>

            <div style={s.schoolsGrid}>
              {filteredSchools.map((inst) => (
                <div
                  key={inst.id}
                  style={{
                    ...s.schoolCard,
                    borderTop: `4px solid ${inst.primary_color || '#16a34a'}`,
                  }}
                >
                  <div style={s.schoolCardTop}>
                    <img
                      src={inst.logo || '/kwasu.png'}
                      alt={inst.name}
                      style={s.schoolCardLogo}
                      onError={(e) => { e.target.src = '/kwasu.png'; }}
                    />
                    <div style={s.schoolCardInfo}>
                      <div style={s.schoolCardName}>{inst.name}</div>
                      <div style={s.schoolCardDomain}>{inst.domain}</div>
                    </div>
                  </div>

                  <div style={s.schoolCardMeta}>
                    <span style={s.schoolCardTag}>{inst.type}</span>
                    <span style={s.schoolCardLocation}>{inst.location || 'Nigeria'}</span>
                  </div>

                  <div style={s.schoolCardBottom}>
                    <div style={s.schoolStatusWrap}>
                      <span
                        style={{
                          ...s.statusDot,
                          background: inst.status === 'active' ? '#16a34a' : '#f59e0b',
                        }}
                      />
                      <span style={s.statusText}>
                        {inst.status === 'active' ? 'Active Portal' : 'Configuring'}
                      </span>
                    </div>

                    <Link
                      to={`/login/${inst.slug}`}
                      style={{
                        ...s.schoolCardBtn,
                        background: inst.primary_color || '#16a34a',
                      }}
                    >
                      <span>Sign In</span>
                      <ChevronRight size={14} />
                    </Link>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* ── SYSTEM CAPABILITIES & VALUE PILLARS ─────────────────────── */}
        <section style={s.featuresSection}>
          <div style={s.featuresGrid}>
            <div style={s.featureBox}>
              <div style={s.featureIconCircle}>
                <Sparkles size={20} color="#22c55e" />
              </div>
              <h4 style={s.featureBoxTitle}>Instant Logo Color Extraction</h4>
              <p style={s.featureBoxDesc}>
                Simply upload your official school emblem. SPSEMS inspects pixel saturation and automatically styles
                your institutional portal with your school's official colors.
              </p>
            </div>

            <div style={s.featureBox}>
              <div style={s.featureIconCircle}>
                <Users size={20} color="#3b82f6" />
              </div>
              <h4 style={s.featureBoxTitle}>Dual Postgraduate Supervision</h4>
              <p style={s.featureBoxDesc}>
                Enforces institutional governance where MSc and PhD students are automatically paired with 1 Main Supervisor
                and 1 Random Co-Supervisor from qualified faculty.
              </p>
            </div>

            <div style={s.featureBox}>
              <div style={s.featureIconCircle}>
                <Layers size={20} color="#a855f7" />
              </div>
              <h4 style={s.featureBoxTitle}>Multi-Tenant Architecture</h4>
              <p style={s.featureBoxDesc}>
                Each institution operates in isolated data tenancy with private departments, custom supervisory load limits,
                and dedicated administrator controls.
              </p>
            </div>

            <div style={s.featureBox}>
              <div style={s.featureIconCircle}>
                <ShieldCheck size={20} color="#eab308" />
              </div>
              <h4 style={s.featureBoxTitle}>AI Matchmaking &amp; Risk Scoring</h4>
              <p style={s.featureBoxDesc}>
                TF-IDF domain vector similarity matching pairs student topics with lecturers' research interests,
                with machine learning predictive risk assessment for at-risk projects.
              </p>
            </div>
          </div>
        </section>
      </main>

      {/* ── FOOTER ──────────────────────────────────────────────────────── */}
      <footer style={s.footer}>
        <div style={s.footerInner}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <img src="/kwasu.png" alt="KWASU" style={{ width: 28, height: 28, objectFit: 'contain' }} />
            <span style={{ fontSize: 13, color: 'var(--text-muted, #9ca3af)' }}>
              SPSEMS • Smart Project Supervision &amp; Evaluation Management System
            </span>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: 18, fontSize: 13 }}>
            <Link to="/onboard" style={{ color: '#22c55e', textDecoration: 'none', fontWeight: 600 }}>
              Onboard Institution
            </Link>
            <Link to="/login" style={{ color: 'var(--text-muted, #9ca3af)', textDecoration: 'none' }}>
              KWASU Portal
            </Link>
          </div>
        </div>
      </footer>
    </div>
  );
}

// ── STYLES ───────────────────────────────────────────────────────────────────
const s = {
  page: {
    minHeight: '100vh',
    background: 'var(--bg-app, #0a0a0a)',
    color: 'var(--text-primary, #ffffff)',
    fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
  },
  header: {
    borderBottom: '1px solid var(--border-subtle, rgba(255,255,255,0.08))',
    background: 'var(--bg-topbar, #0f0f0f)',
    position: 'sticky',
    top: 0,
    zIndex: 100,
  },
  navInner: {
    maxWidth: 1200,
    margin: '0 auto',
    padding: '14px 24px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  logoGroup: {
    display: 'flex',
    alignItems: 'center',
    gap: 12,
  },
  navLogo: {
    width: 36,
    height: 36,
    objectFit: 'contain',
  },
  navBrand: {
    fontWeight: 800,
    fontSize: 16,
    color: 'var(--text-primary, #ffffff)',
    letterSpacing: '-0.3px',
  },
  navTagline: {
    fontSize: 11,
    color: 'var(--text-muted, #9ca3af)',
  },
  navActions: {
    display: 'flex',
    alignItems: 'center',
    gap: 16,
  },
  navAnchor: {
    color: 'var(--text-muted, #9ca3af)',
    textDecoration: 'none',
    fontSize: 13,
    fontWeight: 500,
    transition: 'color 0.15s ease',
  },
  navOnboardBtn: {
    display: 'inline-flex',
    alignItems: 'center',
    gap: 8,
    background: '#16a34a',
    color: '#ffffff',
    padding: '7px 16px',
    borderRadius: 8,
    fontSize: 13,
    fontWeight: 700,
    textDecoration: 'none',
    transition: 'background 0.15s ease',
  },
  main: {
    maxWidth: 1200,
    margin: '0 auto',
    padding: '40px 24px 80px',
  },
  heroSection: {
    textAlign: 'center',
    marginBottom: 50,
  },
  platformPill: {
    display: 'inline-flex',
    alignItems: 'center',
    gap: 8,
    background: 'rgba(22,163,74,0.12)',
    border: '1px solid rgba(22,163,74,0.3)',
    color: '#22c55e',
    fontSize: 12,
    fontWeight: 600,
    padding: '5px 14px',
    borderRadius: 999,
    marginBottom: 20,
  },
  heroHeading: {
    fontSize: 40,
    fontWeight: 800,
    letterSpacing: '-0.8px',
    margin: '0 auto 16px',
    maxWidth: 880,
    lineHeight: 1.2,
    color: 'var(--text-primary, #ffffff)',
  },
  heroSubheading: {
    fontSize: 16,
    color: 'var(--text-muted, #9ca3af)',
    maxWidth: 760,
    margin: '0 auto 36px',
    lineHeight: 1.6,
  },
  heroOnboardCard: {
    background: 'linear-gradient(135deg, rgba(22,163,74,0.14) 0%, rgba(15,23,42,0.6) 100%)',
    border: '2px solid rgba(22,163,74,0.4)',
    borderRadius: 20,
    padding: '36px 40px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    gap: 32,
    textAlign: 'left',
    boxShadow: '0 12px 40px rgba(0,0,0,0.5)',
    flexWrap: 'wrap',
  },
  heroOnboardLeft: {
    display: 'flex',
    alignItems: 'flex-start',
    gap: 20,
    flex: 1,
    minWidth: 320,
  },
  onboardIconBadge: {
    width: 60,
    height: 60,
    borderRadius: 16,
    background: 'rgba(22,163,74,0.2)',
    border: '1px solid rgba(22,163,74,0.4)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    flexShrink: 0,
  },
  onboardTextGroup: {
    display: 'flex',
    flexDirection: 'column',
    gap: 6,
  },
  onboardPre: {
    fontSize: 11,
    fontWeight: 700,
    color: '#22c55e',
    letterSpacing: '0.8px',
  },
  onboardTitle: {
    fontSize: 26,
    fontWeight: 800,
    margin: 0,
    color: 'var(--text-primary, #ffffff)',
    letterSpacing: '-0.4px',
  },
  onboardDesc: {
    fontSize: 14,
    color: 'var(--text-secondary, #e5e7eb)',
    margin: 0,
    lineHeight: 1.5,
    maxWidth: 620,
  },
  featurePillRow: {
    display: 'flex',
    flexWrap: 'wrap',
    gap: 8,
    marginTop: 8,
  },
  featurePill: {
    fontSize: 11,
    fontWeight: 600,
    color: 'var(--text-primary, #ffffff)',
    background: 'rgba(255,255,255,0.08)',
    border: '1px solid rgba(255,255,255,0.12)',
    padding: '3px 10px',
    borderRadius: 999,
  },
  heroOnboardRight: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    gap: 10,
    flexShrink: 0,
  },
  heroCtaBtn: {
    display: 'inline-flex',
    alignItems: 'center',
    gap: 10,
    background: '#16a34a',
    color: '#ffffff',
    padding: '16px 32px',
    borderRadius: 12,
    fontSize: 16,
    fontWeight: 800,
    textDecoration: 'none',
    boxShadow: '0 8px 24px rgba(22,163,74,0.4)',
    transition: 'transform 0.15s ease, background 0.15s ease',
  },
  ctaNote: {
    fontSize: 11,
    color: 'var(--text-muted, #9ca3af)',
  },
  loginSection: {
    marginTop: 40,
    marginBottom: 60,
  },
  sectionHead: {
    textAlign: 'center',
    marginBottom: 24,
  },
  badgeLabel: {
    display: 'inline-flex',
    alignItems: 'center',
    gap: 6,
    fontSize: 11,
    fontWeight: 700,
    color: '#16a34a',
    letterSpacing: '0.8px',
    marginBottom: 8,
  },
  sectionTitle: {
    fontSize: 28,
    fontWeight: 800,
    margin: '0 0 8px',
    color: 'var(--text-primary, #ffffff)',
    letterSpacing: '-0.5px',
  },
  sectionSubtitle: {
    fontSize: 14,
    color: 'var(--text-muted, #9ca3af)',
    margin: 0,
  },
  searchWrap: {
    position: 'relative',
    maxWidth: 580,
    margin: '0 auto 30px',
    display: 'flex',
    alignItems: 'center',
  },
  searchIcon: {
    position: 'absolute',
    left: 16,
    color: 'var(--text-dim, #6b7280)',
    pointerEvents: 'none',
  },
  searchInput: {
    width: '100%',
    padding: '13px 18px 13px 44px',
    background: 'var(--bg-card, #141414)',
    border: '1px solid var(--border-input, rgba(255,255,255,0.12))',
    borderRadius: 12,
    color: 'var(--text-primary, #ffffff)',
    fontSize: 14,
    outline: 'none',
    boxShadow: '0 4px 16px rgba(0,0,0,0.3)',
  },
  featuredKwasuCard: {
    background: 'var(--bg-card, #141414)',
    border: '2px solid rgba(22,163,74,0.35)',
    borderRadius: 16,
    padding: '28px 32px',
    boxShadow: '0 10px 30px rgba(0,0,0,0.4)',
    marginBottom: 36,
  },
  featuredHeader: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    gap: 20,
    flexWrap: 'wrap',
  },
  featuredLogoWrap: {
    display: 'flex',
    alignItems: 'center',
    gap: 18,
  },
  featuredLogo: {
    width: 60,
    height: 60,
    objectFit: 'contain',
    background: 'rgba(255,255,255,0.06)',
    padding: 6,
    borderRadius: 12,
  },
  featuredBadgeRow: {
    display: 'flex',
    alignItems: 'center',
    gap: 6,
    marginBottom: 4,
  },
  livePulse: {
    width: 7,
    height: 7,
    borderRadius: '50%',
    background: '#22c55e',
    boxShadow: '0 0 8px #22c55e',
  },
  featuredStatus: {
    fontSize: 11,
    fontWeight: 700,
    color: '#22c55e',
    letterSpacing: '0.5px',
  },
  featuredName: {
    fontSize: 20,
    fontWeight: 800,
    margin: '0 0 4px',
    color: 'var(--text-primary, #ffffff)',
  },
  featuredMeta: {
    display: 'flex',
    alignItems: 'center',
    gap: 8,
    fontSize: 12,
    color: 'var(--text-muted, #9ca3af)',
  },
  featuredActionWrap: {
    display: 'flex',
    alignItems: 'center',
    gap: 12,
  },
  kwasuLoginBtn: {
    display: 'inline-flex',
    alignItems: 'center',
    gap: 8,
    background: '#16a34a',
    color: '#ffffff',
    padding: '12px 24px',
    borderRadius: 10,
    fontSize: 14,
    fontWeight: 700,
    textDecoration: 'none',
    boxShadow: '0 4px 16px rgba(22,163,74,0.3)',
  },
  featuredDivider: {
    height: 1,
    background: 'var(--border-subtle, rgba(255,255,255,0.08))',
    margin: '20px 0',
  },
  featuredBody: {
    display: 'flex',
    alignItems: 'flex-start',
    justifyContent: 'space-between',
    gap: 24,
    flexWrap: 'wrap',
  },
  featuredDescCol: {
    flex: 1,
    minWidth: 300,
  },
  featuredDesc: {
    fontSize: 13,
    color: 'var(--text-secondary, #e5e7eb)',
    lineHeight: 1.6,
    margin: '0 0 16px',
  },
  quickRegRow: {
    display: 'flex',
    alignItems: 'center',
    flexWrap: 'wrap',
    gap: 8,
  },
  quickRegLabel: {
    fontSize: 11,
    fontWeight: 600,
    color: 'var(--text-dim, #6b7280)',
    textTransform: 'uppercase',
  },
  quickRegBtn: {
    display: 'inline-flex',
    alignItems: 'center',
    gap: 5,
    padding: '6px 12px',
    background: 'var(--bg-card-subtle, rgba(255,255,255,0.04))',
    border: '1px solid var(--border-subtle, rgba(255,255,255,0.1))',
    color: 'var(--text-secondary, #e5e7eb)',
    borderRadius: 7,
    fontSize: 12,
    fontWeight: 600,
    textDecoration: 'none',
  },
  kwasuDemoBox: {
    background: 'var(--bg-input, #0f0f0f)',
    border: '1px solid var(--border-card, rgba(255,255,255,0.08))',
    borderRadius: 10,
    padding: '12px 18px',
    minWidth: 260,
  },
  kwasuDemoTitle: {
    fontSize: 10,
    fontWeight: 700,
    color: 'var(--text-dim, #6b7280)',
    letterSpacing: '0.6px',
    marginBottom: 8,
  },
  kwasuDemoList: {
    display: 'flex',
    flexDirection: 'column',
    gap: 4,
  },
  kwasuDemoItem: {
    display: 'flex',
    alignItems: 'center',
    gap: 6,
    fontSize: 11,
  },
  kwasuDemoRole: {
    color: 'var(--text-muted, #9ca3af)',
    width: 80,
    fontWeight: 500,
  },
  kwasuCode: {
    fontFamily: 'monospace',
    color: '#22c55e',
    background: 'rgba(22,163,74,0.1)',
    padding: '1px 5px',
    borderRadius: 4,
    fontSize: 11,
  },
  otherSchoolsSection: {
    marginTop: 20,
  },
  otherSchoolsHead: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 16,
  },
  otherSchoolsTitle: {
    fontSize: 16,
    fontWeight: 700,
    color: 'var(--text-primary, #ffffff)',
    margin: 0,
  },
  addSchoolLink: {
    fontSize: 12,
    fontWeight: 600,
    color: '#22c55e',
    textDecoration: 'none',
  },
  schoolsGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))',
    gap: 16,
  },
  schoolCard: {
    background: 'var(--bg-card, #141414)',
    border: '1px solid var(--border-card, rgba(255,255,255,0.08))',
    borderRadius: 12,
    padding: '18px 20px',
    display: 'flex',
    flexDirection: 'column',
    justifyContent: 'space-between',
    gap: 14,
    boxShadow: '0 4px 16px rgba(0,0,0,0.3)',
  },
  schoolCardTop: {
    display: 'flex',
    alignItems: 'center',
    gap: 14,
  },
  schoolCardLogo: {
    width: 44,
    height: 44,
    objectFit: 'contain',
    borderRadius: 8,
    background: 'rgba(255,255,255,0.05)',
    padding: 4,
  },
  schoolCardInfo: {
    display: 'flex',
    flexDirection: 'column',
  },
  schoolCardName: {
    fontWeight: 700,
    fontSize: 14,
    color: 'var(--text-primary, #ffffff)',
  },
  schoolCardDomain: {
    fontSize: 11,
    color: 'var(--text-muted, #9ca3af)',
  },
  schoolCardMeta: {
    display: 'flex',
    alignItems: 'center',
    gap: 8,
    fontSize: 11,
  },
  schoolCardTag: {
    background: 'var(--bg-input, #0f0f0f)',
    border: '1px solid var(--border-subtle, rgba(255,255,255,0.08))',
    padding: '2px 8px',
    borderRadius: 4,
    color: 'var(--text-dim, #6b7280)',
    fontSize: 10,
    fontWeight: 600,
  },
  schoolCardLocation: {
    color: 'var(--text-dim, #6b7280)',
  },
  schoolCardBottom: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingTop: 10,
    borderTop: '1px solid var(--border-subtle, rgba(255,255,255,0.06))',
  },
  schoolStatusWrap: {
    display: 'flex',
    alignItems: 'center',
    gap: 6,
  },
  statusDot: {
    width: 6,
    height: 6,
    borderRadius: '50%',
  },
  statusText: {
    fontSize: 11,
    color: 'var(--text-dim, #6b7280)',
    fontWeight: 500,
  },
  schoolCardBtn: {
    display: 'inline-flex',
    alignItems: 'center',
    gap: 4,
    color: '#ffffff',
    border: 'none',
    borderRadius: 6,
    padding: '6px 12px',
    fontSize: 12,
    fontWeight: 700,
    textDecoration: 'none',
  },
  featuresSection: {
    marginTop: 40,
    paddingTop: 40,
    borderTop: '1px solid var(--border-subtle, rgba(255,255,255,0.08))',
  },
  featuresGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))',
    gap: 20,
  },
  featureBox: {
    background: 'var(--bg-card, #141414)',
    border: '1px solid var(--border-card, rgba(255,255,255,0.06))',
    borderRadius: 12,
    padding: 22,
    display: 'flex',
    flexDirection: 'column',
    gap: 10,
  },
  featureIconCircle: {
    width: 40,
    height: 40,
    borderRadius: 10,
    background: 'var(--bg-card-subtle, rgba(255,255,255,0.04))',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
  },
  featureBoxTitle: {
    fontSize: 15,
    fontWeight: 700,
    margin: 0,
    color: 'var(--text-primary, #ffffff)',
  },
  featureBoxDesc: {
    fontSize: 12,
    color: 'var(--text-muted, #9ca3af)',
    lineHeight: 1.5,
    margin: 0,
  },
  footer: {
    borderTop: '1px solid var(--border-subtle, rgba(255,255,255,0.08))',
    background: 'var(--bg-topbar, #0f0f0f)',
    padding: '20px 0',
  },
  footerInner: {
    maxWidth: 1200,
    margin: '0 auto',
    padding: '0 24px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    flexWrap: 'wrap',
    gap: 12,
  },
};
