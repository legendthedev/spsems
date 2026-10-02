/* eslint-disable no-unused-vars */
import React, { useState, useEffect, useRef } from 'react';
import { useNavigate, useParams, useLocation, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import toast from 'react-hot-toast';
import {
  Lock, User, LogIn, GraduationCap, Users, ShieldCheck, ArrowLeft,
  ChevronDown, School, KeyRound, Lightbulb, CheckCircle2, ShieldAlert,
  Eye, EyeOff, Globe, Sparkles, ExternalLink, HelpCircle, Layers, Info, X, Mail,
  Briefcase, Home, Check
} from 'lucide-react';
import api from '../services/api';
import ThemeToggle from '../components/ThemeToggle';
import { resolveLogoUrl } from '../utils/logoHelper';

// Definition of the 3 official institutional portals
export const INSTITUTIONAL_PORTALS = {
  spsems: {
    id: 'spsems',
    gatewayCode: 'SPSEMS-01',
    title: 'SPSEMS Portal',
    badgeName: 'SPSEMS Project Supervision',
    subtitle: 'Project Supervision & Evaluation Management',
    description: 'Central postgraduate & undergraduate dissertation, thesis, and project supervision ecosystem with AI evaluation.',
    icon: Layers,
    targetRoute: '/spsems',
  },
  siwes: {
    id: 'siwes',
    gatewayCode: 'SIWES-02',
    title: 'SIWES / IT Placement Portal',
    badgeName: 'SIWES & Industrial Training',
    subtitle: 'Industrial Training & Student Work Experience',
    description: 'Students Industrial Work Experience Scheme (SIWES), E-Logbook submission, and industry supervisor assessment portal.',
    icon: Briefcase,
    targetRoute: '/siwes',
  },
  hostel: {
    id: 'hostel',
    gatewayCode: 'HOSTEL-03',
    title: 'Hostel Allocation Portal',
    badgeName: 'Hostel & Bedspace Allocation',
    subtitle: 'Campus Residence & Bedspace Balloting',
    description: 'Campus residence hall selection, room balloting, bedspace reservation pass, and hall warden clearance.',
    icon: Home,
    targetRoute: '/hostel',
  },
};

export default function LandingPage() {
  const { user, login } = useAuth();
  const navigate = useNavigate();
  const { slug: routeSlug, portalId: routePortalId } = useParams();
  const location = useLocation();

  const querySlug = new URLSearchParams(location.search).get('institution') ||
                    new URLSearchParams(location.search).get('school');
  const tokenQuery = new URLSearchParams(location.search).get('token') || '';
  const queryPortalId = new URLSearchParams(location.search).get('portal') || '';
  const targetSlug = (routeSlug || querySlug || 'kwapoly').toLowerCase();

  // Active portal selection: from URL param or query param or defaults to 'spsems'
  const initialPortal = (routePortalId || queryPortalId || 'spsems').toLowerCase();
  const isDedicatedPortalRoute = Boolean(routePortalId && INSTITUTIONAL_PORTALS[routePortalId.toLowerCase()]);
  const [activePortalId, setActivePortalId] = useState(
    INSTITUTIONAL_PORTALS[initialPortal] ? initialPortal : 'spsems'
  );

  // Sync activePortalId if routePortalId changes
  useEffect(() => {
    if (routePortalId && INSTITUTIONAL_PORTALS[routePortalId.toLowerCase()]) {
      setActivePortalId(routePortalId.toLowerCase());
    }
  }, [routePortalId]);

  // Loading animation state (Image 1)
  const [loadingAnimation, setLoadingAnimation] = useState(true);

  // Institution Branding State
  const [institution, setInstitution] = useState({
    name: targetSlug === 'kwasu' ? 'Kwara State University' : (targetSlug === 'kwapoly' ? 'Kwara State Polytechnic' : 'Institution Portal'),
    code: targetSlug.toUpperCase(),
    slug: targetSlug,
    location: targetSlug === 'kwasu' ? 'Malete' : (targetSlug === 'kwapoly' ? 'Ilorin' : ''),
    logo_url: targetSlug === 'kwasu' ? '/kwasu.png' : '',
    primary_color: '#237e3d',
    secondary_color: '#080808',
    domain: '',
    contact_email: '',
    session: '2025/2026',
    semester: 'First Semester',
    status: 'active',
    is_verified: true,
  });

  const [allInstitutions, setAllInstitutions] = useState([]);
  const [showSchoolPicker, setShowSchoolPicker] = useState(false);
  const [showLangPicker, setShowLangPicker] = useState(false);
  const [selectedLang, setSelectedLang] = useState('En');
  const [showPassword, setShowPassword] = useState(false);
  const [forgotModal, setForgotModal] = useState(false);
  const [showDemoAccounts, setShowDemoAccounts] = useState(false);

  const [form, setForm] = useState({
    username: '',
    password: '',
    verification_token: tokenQuery,
  });
  const [busy, setBusy] = useState(false);

  // Trigger loading animation on mount or when switching school
  useEffect(() => {
    setLoadingAnimation(true);
    const timer = setTimeout(() => {
      setLoadingAnimation(false);
    }, 2000);
    return () => clearTimeout(timer);
  }, [targetSlug, routePortalId]);

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
            location: instData.location || (instData.slug === 'kwasu' ? 'Malete' : (instData.slug === 'kwapoly' ? 'Ilorin' : '')),
            logo_url: instData.logo_url || (targetSlug === 'kwasu' ? '/kwasu.png' : ''),
            primary_color: instData.primary_color || '#237e3d',
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
              username: prev.username ? prev.username : instData.contact_email,
              verification_token: prev.verification_token || tokenQuery || '',
            }));
          }
        }
      } catch (err) {
        console.warn(`Could not load institution for slug '${targetSlug}'.`);
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

  const currentPortalConfig = INSTITUTIONAL_PORTALS[activePortalId] || INSTITUTIONAL_PORTALS.spsems;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setBusy(true);
    try {
      const loggedUser = await login(
        form.username,
        form.password,
        form.verification_token || null,
        institution.slug
      );
      toast.success(`Authenticated for ${currentPortalConfig.title}! Welcome, ${loggedUser.full_name}`);

      // Route directly through the gateway to the specific portal chosen!
      if (activePortalId === 'siwes') {
        navigate(`/portal/${institution.slug}/siwes`);
      } else if (activePortalId === 'hostel') {
        navigate(`/portal/${institution.slug}/hostel`);
      } else {
        // SPSEMS Project Supervision Portal (Role-based: student, supervisor, admin)
        navigate(`/${loggedUser.role}`);
      }
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

  const primaryColor = institution.primary_color || '#237e3d';
  const isKwasu = institution.slug === 'kwasu' || institution.code === 'KWASU';

  const fullSchoolNameWithLocation = isKwasu
    ? 'Kwara State University, Malete'
    : `${institution.name}${institution.location ? `, ${institution.location.split(',')[0]}` : ''}`;

  return (
    <div style={s.pageWrapper}>
      {/* ── EMBEDDED CSS ANIMATIONS FOR IMAGE 1 & IMAGE 2 ──────────────────── */}
      <style>{`
        @keyframes kwasuCircularSpin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }
        @keyframes kwasuPulseText {
          0%, 100% { opacity: 0.6; transform: scale(0.99); }
          50% { opacity: 1; transform: scale(1); }
        }
        @keyframes kwasuFadeIn {
          from { opacity: 0; transform: translateY(6px); }
          to { opacity: 1; transform: translateY(0); }
        }
        .portal-card-btn:hover {
          filter: brightness(1.12);
          transform: translateY(-1px);
        }
        .login-btn:hover {
          filter: brightness(1.08);
          box-shadow: 0 4px 14px rgba(0,0,0,0.2);
        }
        .portal-selector-tab:hover {
          background-color: rgba(35,126,61,0.08);
        }
      `}</style>

      {/* ── STAGE 1: LOADING ANIMATION (EXACTLY MATCHING IMAGE 1) ─────────── */}
      {loadingAnimation ? (
        <div style={s.loaderOverlay}>
          <div style={s.loaderCenterBox}>
            {/* Circular Spinner Ring around the School Logo */}
            <div style={s.spinnerCircleWrap}>
              <div
                style={{
                  ...s.spinnerRing,
                  borderTopColor: primaryColor,
                  borderRightColor: primaryColor,
                }}
              />
              <div style={s.logoInsideSpinner}>
                {resolveLogoUrl(institution.logo_url) ? (
                  <img
                    src={resolveLogoUrl(institution.logo_url)}
                    alt={institution.name}
                    style={s.spinnerLogoImg}
                    onError={(e) => {
                      if (isKwasu) e.target.src = '/kwasu.png';
                      else e.target.style.display = 'none';
                    }}
                  />
                ) : (
                  <span style={{ ...s.spinnerFallbackText, color: primaryColor }}>
                    {institution.code ? institution.code.slice(0, 3) : 'UNI'}
                  </span>
                )}
              </div>
            </div>

            {/* "LOADING..." Text matching Image 1 */}
            <div style={s.loadingLabel}>LOADING...</div>
          </div>
        </div>
      ) : (
        /* ── STAGE 2: SCHOOL LOGIN PAGE (EXACTLY MATCHING IMAGE 2) ─────────── */
        <div style={s.splitLayout}>
          {/* Left Column: University Primary Brand Banner */}
          <div
            style={{
              ...s.bannerColumn,
              backgroundColor: primaryColor,
            }}
          >
            <div style={s.bannerTopLabel}>institution banner image</div>

            {/* Subtle Crest Watermark & University Details */}
            <div style={s.bannerContent}>
              <div style={s.bannerWatermarkCrest}>
                {resolveLogoUrl(institution.logo_url) ? (
                  <img
                    src={resolveLogoUrl(institution.logo_url)}
                    alt=""
                    style={s.watermarkImg}
                    onError={(e) => { e.target.style.display = 'none'; }}
                  />
                ) : (
                  <School size={130} color="rgba(255,255,255,0.18)" />
                )}
              </div>

              <div style={s.bannerFooter}>
                <div style={s.bannerBadge}>
                  {isDedicatedPortalRoute ? `GATEWAY: ${currentPortalConfig.gatewayCode}` : 'CAMPUS INSTANCE • ACTIVE'}
                </div>
                <h3 style={s.bannerSchoolTitle}>{institution.name}</h3>
                <p style={s.bannerMotto}>
                  {currentPortalConfig.subtitle}
                </p>
              </div>
            </div>
          </div>

          {/* Right Column: Portal Gateway, Login Form & Portal Cards */}
          <div style={s.contentColumn}>
            {/* Top Toolbar: Language Switcher, Theme Toggle, Institution Switcher */}
            <div style={s.topToolbar}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                {isDedicatedPortalRoute ? (
                  <Link to={`/login/${institution.slug}`} style={s.networkHubBtn} title="Back to All Portals Gateway">
                    <ArrowLeft size={13} />
                    <span>All Portals Gateway</span>
                  </Link>
                ) : (
                  <Link to="/" style={s.networkHubBtn} title="All Institutions Directory">
                    <ArrowLeft size={13} />
                    <span>Network Hub</span>
                  </Link>
                )}

                {/* Institution Switcher Dropdown */}
                <div style={{ position: 'relative' }}>
                  <button
                    type="button"
                    onClick={() => setShowSchoolPicker(!showSchoolPicker)}
                    style={{
                      ...s.schoolSwitchBtn,
                      color: primaryColor,
                      borderColor: `${primaryColor}40`,
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
                          to={`/login/${sch.slug}${isDedicatedPortalRoute ? `/${activePortalId}` : ''}`}
                          onClick={() => setShowSchoolPicker(false)}
                          style={{
                            ...s.dropdownItem,
                            color: sch.slug === institution.slug ? primaryColor : 'var(--text-primary, #111)',
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
                              }}
                            >
                              {sch.code ? sch.code.slice(0, 3) : 'UN'}
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

              {/* Language Selector "文A En" (from Image 2) and ThemeToggle */}
              <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                <div style={{ position: 'relative' }}>
                  <button
                    type="button"
                    onClick={() => setShowLangPicker(!showLangPicker)}
                    style={s.langPillBtn}
                    title="Change language"
                  >
                    <span style={s.langIconText}>文A</span>
                    <span style={s.langCodeText}>{selectedLang}</span>
                  </button>

                  {showLangPicker && (
                    <div style={s.langDropdown}>
                      {[
                        { code: 'En', label: 'English' },
                        { code: 'Fr', label: 'Français' },
                        { code: 'Ar', label: 'العربية' },
                        { code: 'Yo', label: 'Yorùbá' },
                        { code: 'Ha', label: 'Hausa' },
                        { code: 'Ig', label: 'Asụsụ Igbo' }
                      ].map(l => (
                        <div
                          key={l.code}
                          onClick={() => {
                            setSelectedLang(l.code);
                            setShowLangPicker(false);
                            toast.success(`Language set to ${l.label}`);
                          }}
                          style={{
                            ...s.langItem,
                            background: selectedLang === l.code ? 'rgba(35,126,61,0.08)' : 'transparent',
                            color: selectedLang === l.code ? primaryColor : 'var(--text-primary, #333)',
                            fontWeight: selectedLang === l.code ? 700 : 500,
                          }}
                        >
                          <span>{l.label}</span>
                          <span style={{ fontSize: 11, color: '#888' }}>({l.code})</span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>

                <ThemeToggle showLabel={false} />
              </div>
            </div>

            {/* Center Area: University Emblem, Name, and Form */}
            <div style={s.formContainer}>
              {/* University Official Logo */}
              <div style={s.logoWrapper}>
                {resolveLogoUrl(institution.logo_url) ? (
                  <img
                    src={resolveLogoUrl(institution.logo_url)}
                    alt={institution.name}
                    style={s.mainLogoImg}
                    onError={(e) => {
                      if (isKwasu) e.target.src = '/kwasu.png';
                      else e.target.style.display = 'none';
                    }}
                  />
                ) : (
                  <div style={{ ...s.logoFallbackBadge, borderColor: primaryColor, color: primaryColor }}>
                    {institution.code || 'KWASU'}
                  </div>
                )}
              </div>

              {/* University Title & Location in Brand Green */}
              <h2
                style={{
                  ...s.schoolHeading,
                  color: primaryColor,
                }}
              >
                {fullSchoolNameWithLocation}
              </h2>

              {/* Dedicated Gateway Header Banner (if a specific portal is selected) */}
              <div style={{ ...s.gatewayIndicatorCard, borderColor: `${primaryColor}40`, backgroundColor: `${primaryColor}0a` }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', width: '100%' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 7 }}>
                    {React.createElement(currentPortalConfig.icon || Layers, { size: 16, color: primaryColor })}
                    <span style={{ fontSize: 12, fontWeight: 800, color: primaryColor, letterSpacing: '0.4px' }}>
                      {currentPortalConfig.title.toUpperCase()}
                    </span>
                  </div>
                  <span style={{ ...s.gatewayCodeBadge, color: primaryColor, backgroundColor: `${primaryColor}18` }}>
                    {currentPortalConfig.gatewayCode}
                  </span>
                </div>
                <p style={{ margin: '4px 0 0', fontSize: 11, color: 'var(--text-muted, #6b7280)', lineHeight: 1.3 }}>
                  {currentPortalConfig.description}
                </p>
              </div>

              {/* Destination Portal Gateway Tabs */}
              <div style={s.portalTabsRow}>
                {Object.values(INSTITUTIONAL_PORTALS).map(p => {
                  const isSelected = activePortalId === p.id;
                  const Icon = p.icon;
                  return (
                    <button
                      key={p.id}
                      type="button"
                      onClick={() => {
                        setActivePortalId(p.id);
                        if (isDedicatedPortalRoute) {
                          navigate(`/login/${institution.slug}/${p.id}`);
                        }
                      }}
                      className="portal-selector-tab"
                      style={{
                        ...s.portalSelectorTab,
                        backgroundColor: isSelected ? primaryColor : 'var(--bg-card, #ffffff)',
                        color: isSelected ? '#ffffff' : 'var(--text-primary, #374151)',
                        borderColor: isSelected ? primaryColor : 'var(--border-subtle, #d1d5db)',
                        fontWeight: isSelected ? 700 : 500,
                      }}
                    >
                      <Icon size={13} color={isSelected ? '#fff' : primaryColor} />
                      <span>{p.id.toUpperCase()}</span>
                    </button>
                  );
                })}
              </div>

              {/* Login Form matching Image 2 */}
              <form onSubmit={handleSubmit} style={s.loginForm}>
                {/* Staff/Student ID Input */}
                <div style={s.formGroup}>
                  <input
                    id="staffStudentInput"
                    type="text"
                    style={s.formInput}
                    placeholder="Staff/Student ID"
                    value={form.username}
                    onChange={(e) => setForm({ ...form, username: e.target.value })}
                    required
                    autoComplete="username"
                  />
                </div>

                {/* Password Input with Eye Toggle */}
                <div style={s.formGroup}>
                  <div style={s.passwordWrap}>
                    <input
                      type={showPassword ? 'text' : 'password'}
                      style={s.passwordInput}
                      placeholder="Password"
                      value={form.password}
                      onChange={(e) => setForm({ ...form, password: e.target.value })}
                      required
                      autoComplete="current-password"
                    />
                    <button
                      type="button"
                      onClick={() => setShowPassword(!showPassword)}
                      style={s.eyeToggleBtn}
                      title={showPassword ? 'Hide password' : 'Show password'}
                    >
                      {showPassword ? (
                        <EyeOff size={18} color="#6b7280" />
                      ) : (
                        <Eye size={18} color="#6b7280" />
                      )}
                    </button>
                  </div>
                </div>

                {/* Institution Verification Token Input (Multi-Tenant Unlock) */}
                <div style={s.tokenGroup}>
                  <div style={s.tokenHeader}>
                    <span style={s.tokenLabel}>Institution Verification Token</span>
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
                  <input
                    type="text"
                    style={s.tokenInput}
                    placeholder="e.g. VTOK-XXXXXXXX... (Issued at onboarding)"
                    value={form.verification_token}
                    onChange={(e) => setForm({ ...form, verification_token: e.target.value })}
                    autoComplete="off"
                  />
                </div>

                {/* "Forgot Password?" Right-Aligned */}
                <div style={s.forgotRow}>
                  <button
                    type="button"
                    onClick={() => setForgotModal(true)}
                    style={s.forgotLink}
                  >
                    Forgot Password?
                  </button>
                </div>

                {/* Solid Full-Width LOGIN Button */}
                <button
                  type="submit"
                  disabled={busy}
                  className="login-btn"
                  style={{
                    ...s.loginBtn,
                    backgroundColor: primaryColor,
                    opacity: busy ? 0.7 : 1,
                  }}
                >
                  {busy ? 'CONNECTING GATEWAY...' : `LOGIN TO ${currentPortalConfig.id.toUpperCase()} PORTAL`}
                </button>
              </form>

              {/* ── 3 UNIQUE PORTAL GATEWAY ENTRIES (SPSEMS, SIWES, HOSTEL) ── */}
              <div style={s.portalsSection}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 }}>
                  <span style={{ fontSize: 11, fontWeight: 700, letterSpacing: '0.6px', color: '#9ca3af', textTransform: 'uppercase' }}>
                    Available Institutional Portals ({institution.code})
                  </span>
                  <span style={{ fontSize: 11, color: primaryColor, fontWeight: 600 }}>3 Gateways Integrated</span>
                </div>

                <div style={s.portalsGrid}>
                  {Object.values(INSTITUTIONAL_PORTALS).map((portal) => {
                    const isSelected = activePortalId === portal.id;
                    const Icon = portal.icon;
                    return (
                      <div
                        key={portal.id}
                        style={{
                          ...s.portalCard,
                          borderColor: isSelected ? `${primaryColor}80` : 'var(--border-subtle, #e5e7eb)',
                          backgroundColor: isSelected ? `${primaryColor}06` : 'var(--bg-card, #ffffff)',
                        }}
                      >
                        <div style={s.portalCardBody}>
                          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 4 }}>
                            <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                              <Icon size={14} color={primaryColor} />
                              <h4 style={s.portalTitle}>{portal.title}</h4>
                            </div>
                            <span style={{ ...s.portalGatewayPill, color: primaryColor, backgroundColor: `${primaryColor}14` }}>
                              {portal.gatewayCode}
                            </span>
                          </div>
                          <p style={s.portalSubtitle} title={portal.subtitle}>
                            {portal.subtitle}
                          </p>
                        </div>

                        {/* Unique Gateway Entry Button */}
                        <button
                          type="button"
                          onClick={() => {
                            setActivePortalId(portal.id);
                            navigate(`/login/${institution.slug}/${portal.id}`);
                          }}
                          className="portal-card-btn"
                          style={{
                            ...s.portalEnterBtn,
                            backgroundColor: primaryColor,
                          }}
                          title={`Access ${portal.title} via ${portal.gatewayCode}`}
                        >
                          <span>Enter &gt;</span>
                        </button>
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Secondary Navigation & Test Logins Drawer */}
              <div style={s.secondaryNavRow}>
                <button
                  type="button"
                  onClick={() => setShowDemoAccounts(!showDemoAccounts)}
                  style={s.toggleDemoBtn}
                >
                  <Sparkles size={13} color={primaryColor} />
                  <span>{showDemoAccounts ? 'Hide Quick Logins' : 'Quick Demo Credentials'}</span>
                </button>

                <div style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
                  <Link to={`/register?institution=${institution.slug}`} style={s.subLink}>
                    Student Registration
                  </Link>
                  <span style={{ color: '#ccc' }}>•</span>
                  <Link to={`/register/lecturer?institution=${institution.slug}`} style={s.subLink}>
                    Lecturer Portal
                  </Link>
                </div>
              </div>

              {/* Demo Credentials Box */}
              {showDemoAccounts && (
                <div style={s.demoDrawer}>
                  <p style={{ margin: '0 0 8px', fontSize: 11, fontWeight: 700, color: '#9ca3af', textTransform: 'uppercase' }}>
                    {institution.code} Pre-Configured Test Accounts
                  </p>
                  <div style={s.demoGrid}>
                    <div style={s.demoItem}>
                      <span style={s.demoRole}>HOD / Admin</span>
                      <code style={{ ...s.demoCode, color: primaryColor }}>admin</code> / <code style={{ ...s.demoCode, color: primaryColor }}>password123</code>
                    </div>
                    <div style={s.demoItem}>
                      <span style={s.demoRole}>Supervisor</span>
                      <code style={{ ...s.demoCode, color: primaryColor }}>supervisor1</code> / <code style={{ ...s.demoCode, color: primaryColor }}>password123</code>
                    </div>
                    <div style={s.demoItem}>
                      <span style={s.demoRole}>Student</span>
                      <code style={{ ...s.demoCode, color: primaryColor }}>student1</code> / <code style={{ ...s.demoCode, color: primaryColor }}>password123</code>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* ── FORGOT PASSWORD MODAL ─────────────────────────────────────────── */}
      {forgotModal && (
        <div style={s.modalOverlay} onClick={() => setForgotModal(false)}>
          <div style={s.modalCard} onClick={(e) => e.stopPropagation()}>
            <div style={s.modalHeader}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <HelpCircle size={18} color={primaryColor} />
                <h3 style={s.modalTitle}>Password Recovery</h3>
              </div>
              <button
                type="button"
                onClick={() => setForgotModal(false)}
                style={s.modalCloseBtn}
              >
                <X size={16} />
              </button>
            </div>
            <p style={s.modalDesc}>
              Institutional accounts for <b>{institution.name}</b> are administered under university directory policies.
            </p>
            <div style={s.modalInfoBox}>
              <Mail size={16} color={primaryColor} style={{ flexShrink: 0, marginTop: 2 }} />
              <div style={{ fontSize: 12, color: 'var(--text-muted, #4b5563)', lineHeight: 1.4 }}>
                Please reach out to the ICT / Portal administrator at:{' '}
                <b style={{ color: primaryColor }}>{institution.contact_email || `ict@${institution.domain || 'kwarastatepolytechnic.edu.ng'}`}</b>{' '}
                or visit the student affairs portal for self-service reset.
              </div>
            </div>
            <button
              type="button"
              onClick={() => setForgotModal(false)}
              style={{ ...s.modalOkBtn, backgroundColor: primaryColor }}
            >
              Got it
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

// ── COMPONENT STYLES ─────────────────────────────────────────────────────────
const s = {
  pageWrapper: {
    minHeight: '100vh',
    width: '100%',
    margin: 0,
    padding: 0,
    backgroundColor: 'var(--bg-main, #ffffff)',
    color: 'var(--text-primary, #111827)',
    fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif',
    display: 'flex',
    flexDirection: 'column',
  },

  // ── IMAGE 1: LOADING SCREEN STYLES ──
  loaderOverlay: {
    position: 'fixed',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: 'var(--bg-main, #ffffff)',
    zIndex: 99999,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
  },
  loaderCenterBox: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
  },
  spinnerCircleWrap: {
    position: 'relative',
    width: 110,
    height: 110,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: '50%',
    backgroundColor: '#ffffff',
    boxShadow: '0 4px 20px rgba(0,0,0,0.08)',
  },
  spinnerRing: {
    position: 'absolute',
    top: -5,
    left: -5,
    width: 120,
    height: 120,
    borderRadius: '50%',
    border: '5px solid rgba(0,0,0,0.07)',
    borderTopColor: '#237e3d',
    borderRightColor: '#237e3d',
    animation: 'kwasuCircularSpin 1.1s cubic-bezier(0.5, 0.1, 0.4, 0.9) infinite',
    pointerEvents: 'none',
  },
  logoInsideSpinner: {
    width: 68,
    height: 68,
    borderRadius: '50%',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#ffffff',
  },
  spinnerLogoImg: {
    maxWidth: 58,
    maxHeight: 58,
    objectFit: 'contain',
  },
  spinnerFallbackText: {
    fontSize: 16,
    fontWeight: 800,
    letterSpacing: '0.5px',
  },
  loadingLabel: {
    marginTop: 24,
    fontSize: 13,
    fontWeight: 700,
    letterSpacing: '3.5px',
    color: '#6b7280',
    animation: 'kwasuPulseText 1.6s ease-in-out infinite',
  },

  // ── IMAGE 2: SPLIT SCREEN LAYOUT STYLES ──
  splitLayout: {
    display: 'flex',
    minHeight: '100vh',
    width: '100%',
    animation: 'kwasuFadeIn 0.4s ease-out',
    flexWrap: 'wrap',
  },
  bannerColumn: {
    flex: '0 0 33%',
    minWidth: 280,
    minHeight: '100vh',
    display: 'flex',
    flexDirection: 'column',
    justifyContent: 'space-between',
    padding: '28px 24px',
    position: 'relative',
    overflow: 'hidden',
    boxSizing: 'border-box',
  },
  bannerTopLabel: {
    fontSize: 12,
    fontWeight: 600,
    color: 'rgba(0,0,0,0.3)',
    textTransform: 'lowercase',
    fontFamily: 'monospace',
    letterSpacing: '0.2px',
  },
  bannerContent: {
    display: 'flex',
    flexDirection: 'column',
    justifyContent: 'space-between',
    flex: 1,
    marginTop: 40,
    position: 'relative',
    zIndex: 2,
  },
  bannerWatermarkCrest: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    flex: 1,
    opacity: 0.16,
    pointerEvents: 'none',
  },
  watermarkImg: {
    width: 220,
    height: 220,
    objectFit: 'contain',
    filter: 'brightness(10)',
  },
  bannerFooter: {
    marginTop: 'auto',
    color: '#ffffff',
  },
  bannerBadge: {
    display: 'inline-block',
    fontSize: 10,
    fontWeight: 700,
    letterSpacing: '0.8px',
    padding: '3px 8px',
    borderRadius: 4,
    background: 'rgba(255,255,255,0.2)',
    marginBottom: 8,
  },
  bannerSchoolTitle: {
    fontSize: 20,
    fontWeight: 800,
    margin: '0 0 6px',
    lineHeight: 1.3,
  },
  bannerMotto: {
    fontSize: 12,
    opacity: 0.85,
    margin: 0,
    lineHeight: 1.4,
  },

  contentColumn: {
    flex: 1,
    minWidth: 320,
    display: 'flex',
    flexDirection: 'column',
    backgroundColor: 'var(--bg-card, #ffffff)',
    padding: '24px 36px 40px',
    boxSizing: 'border-box',
    overflowY: 'auto',
  },
  topToolbar: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 20,
  },
  networkHubBtn: {
    display: 'inline-flex',
    alignItems: 'center',
    gap: 6,
    fontSize: 12,
    fontWeight: 600,
    color: 'var(--text-muted, #6b7280)',
    textDecoration: 'none',
    padding: '6px 10px',
    borderRadius: 6,
    border: '1px solid var(--border-subtle, #e5e7eb)',
    background: 'var(--bg-main, #ffffff)',
  },
  schoolSwitchBtn: {
    display: 'inline-flex',
    alignItems: 'center',
    gap: 6,
    fontSize: 12,
    fontWeight: 700,
    padding: '6px 12px',
    borderRadius: 6,
    border: '1px solid',
    background: 'var(--bg-main, #ffffff)',
    cursor: 'pointer',
  },
  langPillBtn: {
    display: 'inline-flex',
    alignItems: 'center',
    gap: 4,
    border: '1px solid #d1d5db',
    borderRadius: 20,
    padding: '4px 10px',
    background: 'var(--bg-main, #ffffff)',
    cursor: 'pointer',
    color: 'var(--text-primary, #374151)',
    fontSize: 12,
  },
  langIconText: {
    fontSize: 12,
    fontWeight: 700,
    letterSpacing: '-0.3px',
  },
  langCodeText: {
    fontSize: 12,
    fontWeight: 600,
  },
  langDropdown: {
    position: 'absolute',
    top: '100%',
    right: 0,
    marginTop: 6,
    background: 'var(--bg-modal, #ffffff)',
    border: '1px solid var(--border-subtle, #e5e7eb)',
    borderRadius: 8,
    boxShadow: '0 10px 25px rgba(0,0,0,0.1)',
    width: 140,
    zIndex: 100,
    overflow: 'hidden',
  },
  langItem: {
    padding: '8px 12px',
    fontSize: 12,
    cursor: 'pointer',
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
  },

  formContainer: {
    maxWidth: 460,
    width: '100%',
    margin: '0 auto',
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
  },
  logoWrapper: {
    marginBottom: 12,
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center',
  },
  mainLogoImg: {
    height: 95,
    maxWidth: 220,
    objectFit: 'contain',
  },
  logoFallbackBadge: {
    width: 80,
    height: 80,
    borderRadius: 12,
    border: '2px solid',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    fontSize: 22,
    fontWeight: 800,
  },
  schoolHeading: {
    fontSize: 17,
    fontWeight: 700,
    textAlign: 'center',
    margin: '0 0 16px',
    letterSpacing: '-0.2px',
    lineHeight: 1.3,
  },

  gatewayIndicatorCard: {
    width: '100%',
    padding: '10px 14px',
    borderRadius: 8,
    border: '1px solid',
    marginBottom: 14,
    boxSizing: 'border-box',
  },
  gatewayCodeBadge: {
    fontSize: 10,
    fontWeight: 800,
    padding: '2px 6px',
    borderRadius: 4,
    letterSpacing: '0.4px',
  },

  portalTabsRow: {
    display: 'flex',
    gap: 6,
    width: '100%',
    marginBottom: 16,
  },
  portalSelectorTab: {
    flex: 1,
    padding: '8px 4px',
    fontSize: 11,
    borderRadius: 6,
    border: '1px solid',
    cursor: 'pointer',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 5,
    transition: 'all 0.15s ease',
  },

  loginForm: {
    width: '100%',
  },
  formGroup: {
    marginBottom: 14,
    width: '100%',
  },
  formInput: {
    width: '100%',
    height: 44,
    padding: '0 14px',
    fontSize: 13,
    borderRadius: 6,
    border: '1px solid var(--border-input, #d1d5db)',
    backgroundColor: 'var(--bg-input, #ffffff)',
    color: 'var(--text-primary, #111827)',
    boxSizing: 'border-box',
    outline: 'none',
  },
  passwordWrap: {
    position: 'relative',
    width: '100%',
  },
  passwordInput: {
    width: '100%',
    height: 44,
    padding: '0 40px 0 14px',
    fontSize: 13,
    borderRadius: 6,
    border: '1px solid var(--border-input, #d1d5db)',
    backgroundColor: 'var(--bg-input, #ffffff)',
    color: 'var(--text-primary, #111827)',
    boxSizing: 'border-box',
    outline: 'none',
  },
  eyeToggleBtn: {
    position: 'absolute',
    right: 10,
    top: '50%',
    transform: 'translateY(-50%)',
    background: 'none',
    border: 'none',
    cursor: 'pointer',
    padding: 4,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
  },

  tokenGroup: {
    marginBottom: 14,
    width: '100%',
  },
  tokenHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 4,
  },
  tokenLabel: {
    fontSize: 11,
    fontWeight: 600,
    color: 'var(--text-muted, #4b5563)',
  },
  tokenInput: {
    width: '100%',
    height: 38,
    padding: '0 12px',
    fontSize: 12,
    borderRadius: 6,
    border: '1px solid var(--border-input, #d1d5db)',
    backgroundColor: 'var(--bg-input, #ffffff)',
    color: 'var(--text-primary, #111827)',
    boxSizing: 'border-box',
    outline: 'none',
  },

  forgotRow: {
    display: 'flex',
    justifyContent: 'flex-end',
    marginBottom: 18,
    marginTop: 2,
  },
  forgotLink: {
    background: 'none',
    border: 'none',
    padding: 0,
    fontSize: 13,
    fontWeight: 700,
    color: 'var(--text-primary, #111827)',
    textDecoration: 'underline',
    cursor: 'pointer',
  },

  loginBtn: {
    width: '100%',
    height: 46,
    borderRadius: 6,
    border: 'none',
    color: '#ffffff',
    fontSize: 13,
    fontWeight: 700,
    letterSpacing: '0.6px',
    cursor: 'pointer',
    transition: 'all 0.15s ease',
  },

  // ── 3 PORTAL CARDS AT BOTTOM ──
  portalsSection: {
    width: '100%',
    marginTop: 28,
    paddingTop: 10,
  },
  portalsGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(3, 1fr)',
    gap: 10,
    width: '100%',
  },
  portalCard: {
    borderRadius: 8,
    border: '1.5px solid var(--border-subtle, #e5e7eb)',
    backgroundColor: 'var(--bg-card, #ffffff)',
    padding: '12px 10px 10px',
    display: 'flex',
    flexDirection: 'column',
    justifyContent: 'space-between',
    minHeight: 110,
    boxShadow: '0 1px 3px rgba(0,0,0,0.04)',
    boxSizing: 'border-box',
  },
  portalCardBody: {
    marginBottom: 8,
  },
  portalTitle: {
    fontSize: 11,
    fontWeight: 700,
    margin: 0,
    color: 'var(--text-primary, #111827)',
    lineHeight: 1.2,
  },
  portalGatewayPill: {
    fontSize: 9,
    fontWeight: 800,
    padding: '1px 4px',
    borderRadius: 3,
    letterSpacing: '0.3px',
  },
  portalSubtitle: {
    fontSize: 10,
    color: 'var(--text-muted, #6b7280)',
    margin: '4px 0 0',
    lineHeight: 1.3,
    overflow: 'hidden',
    textOverflow: 'ellipsis',
    display: '-webkit-box',
    WebkitLineClamp: 2,
    WebkitBoxOrient: 'vertical',
  },
  portalEnterBtn: {
    width: '100%',
    padding: '6px 0',
    borderRadius: 4,
    border: 'none',
    color: '#ffffff',
    fontSize: 11,
    fontWeight: 700,
    cursor: 'pointer',
    transition: 'all 0.15s ease',
  },

  // ── SECONDARY CONTROLS / DEMO DRAWER ──
  secondaryNavRow: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    width: '100%',
    marginTop: 22,
    paddingTop: 14,
    borderTop: '1px solid var(--border-subtle, #f3f4f6)',
    flexWrap: 'wrap',
    gap: 10,
  },
  toggleDemoBtn: {
    background: 'none',
    border: 'none',
    display: 'inline-flex',
    alignItems: 'center',
    gap: 6,
    fontSize: 12,
    fontWeight: 600,
    color: 'var(--text-muted, #6b7280)',
    cursor: 'pointer',
    padding: 0,
  },
  subLink: {
    fontSize: 12,
    color: 'var(--text-muted, #6b7280)',
    textDecoration: 'none',
    fontWeight: 500,
  },
  demoDrawer: {
    width: '100%',
    marginTop: 12,
    padding: '12px 14px',
    borderRadius: 8,
    backgroundColor: 'var(--bg-main, #f9fafb)',
    border: '1px solid var(--border-subtle, #e5e7eb)',
    boxSizing: 'border-box',
  },
  demoGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(130px, 1fr))',
    gap: 8,
  },
  demoItem: {
    fontSize: 11,
    display: 'flex',
    flexDirection: 'column',
    gap: 2,
  },
  demoRole: {
    fontWeight: 600,
    color: '#6b7280',
  },
  demoCode: {
    fontFamily: 'monospace',
    fontWeight: 700,
  },

  // Dropdown menu
  dropdownMenu: {
    position: 'absolute',
    top: '100%',
    left: 0,
    marginTop: 6,
    width: 250,
    backgroundColor: 'var(--bg-modal, #ffffff)',
    border: '1px solid var(--border-subtle, #e5e7eb)',
    borderRadius: 10,
    boxShadow: '0 12px 30px rgba(0,0,0,0.15)',
    zIndex: 200,
    overflow: 'hidden',
  },
  dropdownTitle: {
    fontSize: 10,
    fontWeight: 700,
    color: '#9ca3af',
    padding: '8px 12px 4px',
    letterSpacing: '0.6px',
  },
  dropdownItem: {
    display: 'flex',
    alignItems: 'center',
    gap: 10,
    padding: '8px 12px',
    fontSize: 12,
    textDecoration: 'none',
    borderBottom: '1px solid var(--border-subtle, #f3f4f6)',
  },
  dropdownLogo: {
    width: 20,
    height: 20,
    objectFit: 'contain',
  },
  dropdownFallback: {
    width: 20,
    height: 20,
    borderRadius: 4,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    fontSize: 9,
    fontWeight: 700,
  },
  dropdownOnboardLink: {
    display: 'flex',
    alignItems: 'center',
    gap: 8,
    padding: '10px 12px',
    fontSize: 11,
    fontWeight: 600,
    color: '#16a34a',
    textDecoration: 'none',
    backgroundColor: 'rgba(22,163,74,0.06)',
  },

  // Modal styles
  modalOverlay: {
    position: 'fixed',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: 'rgba(0,0,0,0.65)',
    backdropFilter: 'blur(4px)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    padding: 16,
    zIndex: 9999,
  },
  modalCard: {
    backgroundColor: 'var(--bg-modal, #ffffff)',
    borderRadius: 12,
    padding: '24px',
    maxWidth: 420,
    width: '100%',
    boxShadow: '0 20px 50px rgba(0,0,0,0.25)',
    boxSizing: 'border-box',
  },
  modalHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  modalTitle: {
    fontSize: 16,
    fontWeight: 700,
    margin: 0,
    color: 'var(--text-primary, #111827)',
  },
  modalCloseBtn: {
    background: 'none',
    border: 'none',
    cursor: 'pointer',
    color: '#6b7280',
    padding: 4,
  },
  modalDesc: {
    fontSize: 12,
    color: 'var(--text-muted, #4b5563)',
    lineHeight: 1.5,
    margin: '0 0 14px',
  },
  modalInfoBox: {
    display: 'flex',
    gap: 8,
    alignItems: 'flex-start',
    backgroundColor: 'var(--bg-main, #f9fafb)',
    padding: '10px 12px',
    borderRadius: 8,
    border: '1px solid var(--border-subtle, #e5e7eb)',
    marginBottom: 16,
  },
  modalOkBtn: {
    width: '100%',
    height: 40,
    borderRadius: 6,
    border: 'none',
    color: '#ffffff',
    fontSize: 13,
    fontWeight: 700,
    cursor: 'pointer',
  },
};
