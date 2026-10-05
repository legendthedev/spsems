/* eslint-disable no-unused-vars */
import React, { useState, useEffect } from 'react';
import { useNavigate, useParams, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import toast from 'react-hot-toast';
import {
  Briefcase, Calendar, CheckCircle2, Clock, FileText, Download,
  Building, User, LogOut, ArrowLeft, Plus, Award, ShieldCheck,
  ChevronRight, AlertCircle, FileCheck, Layers, ExternalLink
} from 'lucide-react';
import api from '../services/api';
import ThemeToggle from '../components/ThemeToggle';
import { resolveLogoUrl } from '../utils/logoHelper';

export default function SiwesPortal() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const { slug: routeSlug } = useParams();
  const targetSlug = (routeSlug || user?.institution_slug || 'kwapoly').toLowerCase();

  const [institution, setInstitution] = useState({
    name: 'Kwara State Polytechnic',
    code: 'KWAPOLY',
    slug: targetSlug,
    location: 'Ilorin',
    primary_color: '#237e3d',
    logo_url: '',
  });

  const [tab, setTab] = useState('overview');
  const [showAddLogModal, setShowAddLogModal] = useState(false);

  // Sample or state-persisted SIWES Logbook entries
  const [logEntries, setLogEntries] = useState([
    {
      id: 1,
      week: 1,
      dates: 'Aug 11 - Aug 15',
      title: 'Company Orientation & Database Infrastructure Setup',
      summary: 'Completed company security clearance. Configured Oracle database schemas and conducted preliminary network cable splicing.',
      skills: ['Network Configuration', 'Database Indexing', 'Safety Protocols'],
      hours: 40,
      supervisor_endorsed: true,
      score: 95,
    },
    {
      id: 2,
      week: 2,
      dates: 'Aug 18 - Aug 22',
      title: 'Server Rack Maintenance & Enterprise Switch Configuration',
      summary: 'Assisted senior systems engineer in racking Cisco Catalyst switches and configuring VLAN tags for department isolation.',
      skills: ['VLAN Trunking', 'Cisco CLI', 'Server Hardware'],
      hours: 40,
      supervisor_endorsed: true,
      score: 92,
    },
    {
      id: 3,
      week: 3,
      dates: 'Aug 25 - Aug 29',
      title: 'Fiber Optic Cable Testing & Power Budget Calculations',
      summary: 'Utilized Optical Time-Domain Reflectometer (OTDR) to identify attenuation breaks along the main campus distribution route.',
      skills: ['OTDR Testing', 'Fiber Splicing', 'Loss Budget Analysis'],
      hours: 40,
      supervisor_endorsed: false,
      score: null,
    }
  ]);

  const [newLog, setNewLog] = useState({
    week: 4,
    title: '',
    summary: '',
    skills: '',
    hours: 40,
  });

  useEffect(() => {
    async function loadInst() {
      try {
        const res = await api.get(`/institutions/by-slug/${targetSlug}`);
        if (res.data) {
          setInstitution({
            name: res.data.name,
            code: res.data.code,
            slug: res.data.slug,
            location: res.data.location || '',
            primary_color: res.data.primary_color || '#237e3d',
            logo_url: res.data.logo_url || '',
          });
        }
      } catch (err) {
        console.warn('Fallback to default institution for SIWES');
      }
    }
    loadInst();
  }, [targetSlug]);

  const primaryColor = institution.primary_color || '#237e3d';

  const handleAddLog = (e) => {
    e.preventDefault();
    if (!newLog.title || !newLog.summary) {
      toast.error('Please enter logbook title and weekly activity summary.');
      return;
    }
    const created = {
      id: Date.now(),
      week: Number(newLog.week) || logEntries.length + 1,
      dates: `Week ${newLog.week}`,
      title: newLog.title,
      summary: newLog.summary,
      skills: newLog.skills ? newLog.skills.split(',').map(s => s.trim()) : ['General Engineering'],
      hours: Number(newLog.hours) || 40,
      supervisor_endorsed: false,
      score: null,
    };
    setLogEntries([created, ...logEntries]);
    setShowAddLogModal(false);
    setNewLog({ week: logEntries.length + 2, title: '', summary: '', skills: '', hours: 40 });
    toast.success('Weekly logbook entry submitted for supervisor endorsement!');
  };

  const handleLogout = () => {
    logout();
    navigate(`/login/${institution.slug}/siwes`);
    toast.success('Signed out of SIWES Portal');
  };

  return (
    <div style={s.page}>
      {/* ── TOP HEADER ──────────────────────────────────────────────────────── */}
      <header style={{ ...s.header, borderBottomColor: `${primaryColor}30` }}>
        <div style={s.headerInner}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
            {resolveLogoUrl(institution.logo_url) ? (
              <img
                src={resolveLogoUrl(institution.logo_url)}
                alt={institution.name}
                style={s.headerLogo}
                onError={(e) => { e.target.style.display = 'none'; }}
              />
            ) : (
              <div style={{ ...s.headerFallbackLogo, backgroundColor: `${primaryColor}22`, color: primaryColor }}>
                {institution.code ? institution.code.slice(0, 3) : 'SIW'}
              </div>
            )}
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <span style={{ ...s.portalBadge, backgroundColor: `${primaryColor}18`, color: primaryColor, borderColor: `${primaryColor}40` }}>
                  PORTAL GATEWAY: SIWES-02
                </span>
                <span style={s.activePill}>LIVE INSTANCE</span>
              </div>
              <h1 style={s.headerTitle}>
                {institution.name} — SIWES &amp; IT Placement Portal
              </h1>
            </div>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            {/* Quick jump to SPSEMS or Hostel */}
            <div style={s.switchPortalBox}>
              <Link to={`/login/${institution.slug}/spsems`} style={s.switchPortalLink}>
                <Layers size={13} color={primaryColor} />
                <span>SPSEMS Portal</span>
              </Link>
              <span style={{ color: '#ccc' }}>•</span>
              <Link to={`/login/${institution.slug}/hostel`} style={s.switchPortalLink}>
                <span>Hostel Portal</span>
              </Link>
            </div>

            <Link to={`/login/${institution.slug}`} style={s.backGatewayBtn} title="Back to Central Campus Gateway">
              <ArrowLeft size={13} />
              <span>Campus Gateway</span>
            </Link>

            <ThemeToggle showLabel={false} />

            <button onClick={handleLogout} style={s.logoutBtn} title="Log Out">
              <LogOut size={15} />
              <span>Log Out</span>
            </button>
          </div>
        </div>

        {/* Institutional Staging Notification Banner */}
        <div style={{
          margin: '12px 24px',
          padding: '12px 18px',
          borderRadius: 10,
          background: 'rgba(245, 158, 11, 0.1)',
          border: '1px solid rgba(245, 158, 11, 0.35)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          gap: 12,
          flexWrap: 'wrap',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <span style={{ fontSize: 10, fontWeight: 800, padding: '2px 8px', borderRadius: 4, background: '#d97706', color: '#fff' }}>
              NOT IMPLEMENTED YET
            </span>
            <span style={{ fontSize: 12, color: 'var(--text-primary, #fff)', fontWeight: 600 }}>
              Institutional SIWES module is staged for Phase 2 implementation. Single Sign-On surname authentication is pre-mapped.
            </span>
          </div>
          <Link
            to={`/login/${institution.slug}/spsems`}
            style={{
              padding: '5px 12px',
              borderRadius: 6,
              background: primaryColor,
              color: '#fff',
              fontSize: 11,
              fontWeight: 700,
              textDecoration: 'none',
              display: 'inline-flex',
              alignItems: 'center',
              gap: 4
            }}
          >
            <span>Enter Active SPSEMS Portal &gt;</span>
          </Link>
        </div>

        {/* Navigation Tabs */}
        <div style={s.tabBar}>
          {[
            { id: 'overview', label: 'Placement Overview', icon: Briefcase },
            { id: 'logbook', label: 'E-Logbook Entries', icon: Calendar },
            { id: 'supervision', label: 'Supervision & Grading', icon: Award },
            { id: 'clearance', label: 'ITF Clearance & Form 8', icon: FileCheck },
          ].map(t => {
            const Icon = t.icon;
            const active = tab === t.id;
            return (
              <button
                key={t.id}
                onClick={() => setTab(t.id)}
                style={{
                  ...s.tabBtn,
                  borderBottomColor: active ? primaryColor : 'transparent',
                  color: active ? primaryColor : 'var(--text-muted, #6b7280)',
                  fontWeight: active ? 700 : 500,
                }}
              >
                <Icon size={15} />
                <span>{t.label}</span>
              </button>
            );
          })}
        </div>
      </header>

      {/* ── MAIN CONTENT AREA ───────────────────────────────────────────────── */}
      <main style={s.main}>
        {/* TAB 1: PLACEMENT OVERVIEW */}
        {tab === 'overview' && (
          <div style={s.tabContent}>
            <div style={s.heroStatusCard}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: 14 }}>
                <div>
                  <div style={s.schemeTag}>6 MONTHS INDUSTRIAL TRAINING SCHEME (SIWES 2025/2026)</div>
                  <h2 style={s.studentNameHeading}>
                    {user?.full_name || 'Enrolled SIWES Candidate'}
                  </h2>
                  <p style={s.studentMatricSub}>
                    Matric No: <b>{user?.matric_number || user?.username || 'KWAPOLY/ND/EE/2024/0481'}</b> • Department of Electrical/Electronic Engineering
                  </p>
                </div>
                <div style={{ ...s.statusPillLarge, backgroundColor: '#16a34a', color: '#fff' }}>
                  <CheckCircle2 size={16} />
                  <span>Attachment Approved &amp; Active</span>
                </div>
              </div>

              <div style={s.quickStatsGrid}>
                <div style={s.statBox}>
                  <span style={s.statLabel}>Total Weeks Required</span>
                  <span style={s.statValue}>24 Weeks</span>
                </div>
                <div style={s.statBox}>
                  <span style={s.statLabel}>Completed &amp; Endorsed</span>
                  <span style={{ ...s.statValue, color: primaryColor }}>3 Weeks</span>
                </div>
                <div style={s.statBox}>
                  <span style={s.statLabel}>Logged Work Hours</span>
                  <span style={s.statValue}>120 Hours</span>
                </div>
                <div style={s.statBox}>
                  <span style={s.statLabel}>Supervision Clearance</span>
                  <span style={{ ...s.statValue, color: '#16a34a' }}>Stage 1 Cleared</span>
                </div>
              </div>
            </div>

            {/* Placement Organisation Card & Supervisors */}
            <div style={s.twoColGrid}>
              <div style={s.card}>
                <div style={s.cardHeader}>
                  <Building size={18} color={primaryColor} />
                  <h3 style={s.cardTitle}>Placement Organization Details</h3>
                </div>
                <div style={s.infoRow}>
                  <span style={s.infoLabel}>Company / Agency</span>
                  <span style={s.infoVal}>Chevron Nigeria Ltd. / Regional IT Hub</span>
                </div>
                <div style={s.infoRow}>
                  <span style={s.infoLabel}>Department</span>
                  <span style={s.infoVal}>Systems Engineering &amp; SCADA Network Ops</span>
                </div>
                <div style={s.infoRow}>
                  <span style={s.infoLabel}>Facility Address</span>
                  <span style={s.infoVal}>Km 4 Old Jebba Road, Industrial Layout, Ilorin</span>
                </div>
                <div style={s.infoRow}>
                  <span style={s.infoLabel}>Acceptance Letter</span>
                  <span style={{ color: '#16a34a', fontWeight: 600 }}>Verified &amp; Uploaded</span>
                </div>
                <div style={s.infoRow}>
                  <span style={s.infoLabel}>Commencement Date</span>
                  <span style={s.infoVal}>August 11, 2025</span>
                </div>
              </div>

              <div style={s.card}>
                <div style={s.cardHeader}>
                  <User size={18} color={primaryColor} />
                  <h3 style={s.cardTitle}>Assigned Supervision Officers</h3>
                </div>
                <div style={s.infoRow}>
                  <span style={s.infoLabel}>Institutional Supervisor</span>
                  <span style={s.infoVal}>Engr. Dr. A. K. Mustapha (HOD Electrical)</span>
                </div>
                <div style={s.infoRow}>
                  <span style={s.infoLabel}>Institutional Email</span>
                  <span style={s.infoVal}>a.mustapha@{institution.domain || 'kwarastatepolytechnic.edu.ng'}</span>
                </div>
                <div style={s.infoRow}>
                  <span style={s.infoLabel}>Industry-Based Supervisor</span>
                  <span style={s.infoVal}>Engr. F. O. Adeleke (Lead Field Engineer)</span>
                </div>
                <div style={s.infoRow}>
                  <span style={s.infoLabel}>Industry Supervisor Phone</span>
                  <span style={s.infoVal}>+234 803 492 8812</span>
                </div>
                <div style={s.infoRow}>
                  <span style={s.infoLabel}>Last Supervisory Visit</span>
                  <span style={{ color: primaryColor, fontWeight: 600 }}>August 28, 2025 (Physically Inspected)</span>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* TAB 2: LOGBOOK ENTRIES */}
        {tab === 'logbook' && (
          <div style={s.tabContent}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 18 }}>
              <div>
                <h2 style={s.sectionHeader}>Weekly Technical E-Logbook</h2>
                <p style={s.sectionSub}>Document daily tasks, engineering operations, and skills acquired for weekly sign-off.</p>
              </div>
              <button
                onClick={() => setShowAddLogModal(true)}
                style={{ ...s.primaryBtn, backgroundColor: primaryColor }}
              >
                <Plus size={16} />
                <span>Submit Weekly Entry</span>
              </button>
            </div>

            <div style={s.entriesList}>
              {logEntries.map(entry => (
                <div key={entry.id} style={s.logCard}>
                  <div style={s.logCardHead}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                      <span style={{ ...s.weekNumberBadge, backgroundColor: `${primaryColor}18`, color: primaryColor }}>
                        Week {entry.week}
                      </span>
                      <span style={s.logDates}>{entry.dates}</span>
                    </div>
                    {entry.supervisor_endorsed ? (
                      <span style={s.endorsedBadge}>
                        <CheckCircle2 size={13} />
                        <span>Endorsed ({entry.score}/100)</span>
                      </span>
                    ) : (
                      <span style={s.pendingBadge}>
                        <Clock size={13} />
                        <span>Awaiting Supervisor Sign-off</span>
                      </span>
                    )}
                  </div>
                  <h4 style={s.logTitle}>{entry.title}</h4>
                  <p style={s.logSummary}>{entry.summary}</p>
                  <div style={s.skillsRow}>
                    {entry.skills.map(sk => (
                      <span key={sk} style={s.skillPill}>{sk}</span>
                    ))}
                    <span style={s.hoursLogged}>{entry.hours} Hours Logged</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* TAB 3: SUPERVISION & GRADING */}
        {tab === 'supervision' && (
          <div style={s.tabContent}>
            <h2 style={s.sectionHeader}>SIWES Continuous Assessment &amp; Grading</h2>
            <p style={s.sectionSub}>Comprehensive breakdown of marks across industry appraisal, institutional inspection, and final presentation.</p>

            <div style={s.gradingGrid}>
              <div style={s.gradeCard}>
                <span style={s.gradeCategory}>E-Logbook Assessment</span>
                <span style={{ ...s.gradeScore, color: primaryColor }}>28 / 30</span>
                <p style={s.gradeDesc}>Completeness of weekly technical entries, technical sketches, and consistency.</p>
              </div>
              <div style={s.gradeCard}>
                <span style={s.gradeCategory}>Industry-Based Appraisal</span>
                <span style={{ ...s.gradeScore, color: primaryColor }}>29 / 30</span>
                <p style={s.gradeDesc}>Punctuality, work ethic, teamwork, and technical dexterity scored by industry supervisor.</p>
              </div>
              <div style={s.gradeCard}>
                <span style={s.gradeCategory}>Institutional Defense</span>
                <span style={{ ...s.gradeScore, color: '#60a5fa' }}>36 / 40</span>
                <p style={s.gradeDesc}>PowerPoint presentation and technical oral defense before departmental SIWES panel.</p>
              </div>
              <div style={s.gradeCardTotal}>
                <span style={s.gradeCategory}>Cumulative SIWES Score</span>
                <span style={{ ...s.gradeScoreTotal, color: '#16a34a' }}>93% (Grade A)</span>
                <p style={s.gradeDesc}>Eligible for unconditional academic credit transfer (6 Units).</p>
              </div>
            </div>
          </div>
        )}

        {/* TAB 4: CLEARANCE & FORM 8 */}
        {tab === 'clearance' && (
          <div style={s.tabContent}>
            <div style={s.clearanceBox}>
              <Award size={48} color={primaryColor} style={{ marginBottom: 12 }} />
              <h2 style={{ fontSize: 22, fontWeight: 800, margin: '0 0 8px' }}>
                Official ITF Form 8 &amp; SIWES Clearance
              </h2>
              <p style={{ maxWidth: 540, margin: '0 auto 20px', color: 'var(--text-muted, #6b7280)', fontSize: 13, lineHeight: 1.5 }}>
                Your industrial attachment records for {institution.name} have been fully validated. You can download your official endorsed clearance slip.
              </p>
              <button
                onClick={() => toast.success('Official SIWES Clearance Certificate downloaded!')}
                style={{ ...s.downloadBtn, backgroundColor: primaryColor }}
              >
                <Download size={16} />
                <span>Download Endorsed SIWES Clearance Slip</span>
              </button>
            </div>
          </div>
        )}
      </main>

      {/* ── MODAL: SUBMIT NEW LOGBOOK ENTRY ─────────────────────────────────── */}
      {showAddLogModal && (
        <div style={s.modalOverlay} onClick={() => setShowAddLogModal(false)}>
          <div style={s.modalCard} onClick={e => e.stopPropagation()}>
            <h3 style={s.modalTitle}>Submit Weekly Logbook Entry</h3>
            <p style={s.modalSub}>Document your practical engineering assignments for supervisor review.</p>
            <form onSubmit={handleAddLog}>
              <div style={s.formGroup}>
                <label style={s.label}>Week Number</label>
                <input
                  type="number"
                  min="1"
                  max="24"
                  style={s.input}
                  value={newLog.week}
                  onChange={e => setNewLog({ ...newLog, week: e.target.value })}
                  required
                />
              </div>
              <div style={s.formGroup}>
                <label style={s.label}>Weekly Task / Topic Title</label>
                <input
                  type="text"
                  placeholder="e.g. SCADA Network Monitoring & PLC Debugging"
                  style={s.input}
                  value={newLog.title}
                  onChange={e => setNewLog({ ...newLog, title: e.target.value })}
                  required
                />
              </div>
              <div style={s.formGroup}>
                <label style={s.label}>Detailed Practical Summary</label>
                <textarea
                  rows="4"
                  placeholder="Describe operations performed, instruments calibrated, safety procedures followed..."
                  style={{ ...s.input, height: 'auto', padding: '10px 12px' }}
                  value={newLog.summary}
                  onChange={e => setNewLog({ ...newLog, summary: e.target.value })}
                  required
                />
              </div>
              <div style={s.formGroup}>
                <label style={s.label}>Key Technical Skills (Comma-separated)</label>
                <input
                  type="text"
                  placeholder="e.g. PLC Ladder Logic, Sensor Testing, Soldering"
                  style={s.input}
                  value={newLog.skills}
                  onChange={e => setNewLog({ ...newLog, skills: e.target.value })}
                />
              </div>
              <div style={{ display: 'flex', gap: 10, justifyContent: 'flex-end', marginTop: 16 }}>
                <button
                  type="button"
                  onClick={() => setShowAddLogModal(false)}
                  style={s.cancelBtn}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  style={{ ...s.primaryBtn, backgroundColor: primaryColor }}
                >
                  Save Entry
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

const s = {
  page: {
    minHeight: '100vh',
    backgroundColor: 'var(--bg-main, #f9fafb)',
    color: 'var(--text-primary, #111827)',
    fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
  },
  header: {
    backgroundColor: 'var(--bg-card, #ffffff)',
    borderBottom: '1px solid',
    padding: '16px 28px 0',
  },
  headerInner: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 14,
    flexWrap: 'wrap',
    gap: 12,
  },
  headerLogo: {
    height: 48,
    maxWidth: 90,
    objectFit: 'contain',
  },
  headerFallbackLogo: {
    width: 44,
    height: 44,
    borderRadius: 8,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    fontSize: 14,
    fontWeight: 800,
  },
  portalBadge: {
    fontSize: 10,
    fontWeight: 700,
    letterSpacing: '0.6px',
    padding: '2px 8px',
    borderRadius: 4,
    border: '1px solid',
  },
  activePill: {
    fontSize: 9,
    fontWeight: 700,
    padding: '2px 6px',
    borderRadius: 4,
    backgroundColor: 'rgba(22,163,74,0.12)',
    color: '#16a34a',
  },
  headerTitle: {
    fontSize: 17,
    fontWeight: 800,
    margin: '3px 0 0',
    color: 'var(--text-primary, #111827)',
  },
  switchPortalBox: {
    display: 'flex',
    alignItems: 'center',
    gap: 8,
    background: 'var(--bg-main, #f3f4f6)',
    padding: '5px 10px',
    borderRadius: 6,
    fontSize: 11,
    fontWeight: 600,
  },
  switchPortalLink: {
    display: 'inline-flex',
    alignItems: 'center',
    gap: 4,
    color: 'var(--text-primary, #374151)',
    textDecoration: 'none',
  },
  backGatewayBtn: {
    display: 'inline-flex',
    alignItems: 'center',
    gap: 5,
    fontSize: 12,
    fontWeight: 600,
    color: 'var(--text-muted, #6b7280)',
    textDecoration: 'none',
    padding: '6px 10px',
    borderRadius: 6,
    border: '1px solid var(--border-subtle, #e5e7eb)',
  },
  logoutBtn: {
    display: 'inline-flex',
    alignItems: 'center',
    gap: 6,
    background: 'none',
    border: '1px solid rgba(239,68,68,0.25)',
    color: '#ef4444',
    padding: '6px 12px',
    borderRadius: 6,
    fontSize: 12,
    fontWeight: 600,
    cursor: 'pointer',
  },
  tabBar: {
    display: 'flex',
    gap: 20,
    overflowX: 'auto',
  },
  tabBtn: {
    background: 'none',
    border: 'none',
    borderBottom: '2.5px solid transparent',
    padding: '10px 4px',
    fontSize: 13,
    cursor: 'pointer',
    display: 'inline-flex',
    alignItems: 'center',
    gap: 6,
  },
  main: {
    padding: '24px 28px',
    maxWidth: 1200,
    margin: '0 auto',
  },
  tabContent: {
    animation: 'kwasuFadeIn 0.3s ease-out',
  },
  heroStatusCard: {
    backgroundColor: 'var(--bg-card, #ffffff)',
    borderRadius: 12,
    padding: '22px 24px',
    border: '1px solid var(--border-subtle, #e5e7eb)',
    marginBottom: 20,
    boxShadow: '0 1px 4px rgba(0,0,0,0.03)',
  },
  schemeTag: {
    fontSize: 11,
    fontWeight: 700,
    letterSpacing: '0.6px',
    color: '#9ca3af',
  },
  studentNameHeading: {
    fontSize: 22,
    fontWeight: 800,
    margin: '4px 0',
  },
  studentMatricSub: {
    fontSize: 13,
    color: 'var(--text-muted, #6b7280)',
    margin: 0,
  },
  statusPillLarge: {
    display: 'inline-flex',
    alignItems: 'center',
    gap: 6,
    padding: '6px 14px',
    borderRadius: 20,
    fontSize: 12,
    fontWeight: 700,
  },
  quickStatsGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))',
    gap: 12,
    marginTop: 20,
    paddingTop: 16,
    borderTop: '1px solid var(--border-subtle, #f3f4f6)',
  },
  statBox: {
    display: 'flex',
    flexDirection: 'column',
    gap: 2,
  },
  statLabel: {
    fontSize: 11,
    color: 'var(--text-muted, #6b7280)',
    fontWeight: 600,
  },
  statValue: {
    fontSize: 18,
    fontWeight: 800,
  },
  twoColGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(360px, 1fr))',
    gap: 20,
  },
  card: {
    backgroundColor: 'var(--bg-card, #ffffff)',
    borderRadius: 12,
    padding: '20px 22px',
    border: '1px solid var(--border-subtle, #e5e7eb)',
    boxShadow: '0 1px 4px rgba(0,0,0,0.03)',
  },
  cardHeader: {
    display: 'flex',
    alignItems: 'center',
    gap: 8,
    marginBottom: 16,
    paddingBottom: 10,
    borderBottom: '1px solid var(--border-subtle, #f3f4f6)',
  },
  cardTitle: {
    fontSize: 15,
    fontWeight: 700,
    margin: 0,
  },
  infoRow: {
    display: 'flex',
    justifyContent: 'space-between',
    padding: '8px 0',
    borderBottom: '1px solid var(--border-subtle, #f9fafb)',
    fontSize: 13,
  },
  infoLabel: {
    color: 'var(--text-muted, #6b7280)',
  },
  infoVal: {
    fontWeight: 600,
    textAlign: 'right',
  },
  sectionHeader: {
    fontSize: 19,
    fontWeight: 800,
    margin: '0 0 4px',
  },
  sectionSub: {
    fontSize: 13,
    color: 'var(--text-muted, #6b7280)',
    margin: 0,
  },
  primaryBtn: {
    display: 'inline-flex',
    alignItems: 'center',
    gap: 6,
    padding: '9px 16px',
    borderRadius: 6,
    border: 'none',
    color: '#ffffff',
    fontSize: 13,
    fontWeight: 700,
    cursor: 'pointer',
  },
  entriesList: {
    display: 'flex',
    flexDirection: 'column',
    gap: 12,
  },
  logCard: {
    backgroundColor: 'var(--bg-card, #ffffff)',
    borderRadius: 10,
    padding: '16px 20px',
    border: '1px solid var(--border-subtle, #e5e7eb)',
  },
  logCardHead: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  weekNumberBadge: {
    fontSize: 11,
    fontWeight: 800,
    padding: '3px 8px',
    borderRadius: 4,
  },
  logDates: {
    fontSize: 12,
    color: 'var(--text-muted, #6b7280)',
  },
  endorsedBadge: {
    display: 'inline-flex',
    alignItems: 'center',
    gap: 4,
    fontSize: 11,
    fontWeight: 700,
    color: '#16a34a',
    backgroundColor: 'rgba(22,163,74,0.1)',
    padding: '3px 8px',
    borderRadius: 12,
  },
  pendingBadge: {
    display: 'inline-flex',
    alignItems: 'center',
    gap: 4,
    fontSize: 11,
    fontWeight: 600,
    color: '#f59e0b',
    backgroundColor: 'rgba(245,158,11,0.1)',
    padding: '3px 8px',
    borderRadius: 12,
  },
  logTitle: {
    fontSize: 15,
    fontWeight: 700,
    margin: '0 0 6px',
  },
  logSummary: {
    fontSize: 13,
    color: 'var(--text-muted, #4b5563)',
    lineHeight: 1.5,
    margin: '0 0 12px',
  },
  skillsRow: {
    display: 'flex',
    alignItems: 'center',
    gap: 8,
    flexWrap: 'wrap',
  },
  skillPill: {
    fontSize: 11,
    fontWeight: 600,
    padding: '2px 8px',
    borderRadius: 10,
    backgroundColor: 'var(--bg-main, #f3f4f6)',
    color: 'var(--text-primary, #374151)',
  },
  hoursLogged: {
    marginLeft: 'auto',
    fontSize: 11,
    color: 'var(--text-muted, #9ca3af)',
    fontWeight: 600,
  },
  gradingGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
    gap: 16,
    marginTop: 20,
  },
  gradeCard: {
    backgroundColor: 'var(--bg-card, #ffffff)',
    borderRadius: 10,
    padding: '20px 18px',
    border: '1px solid var(--border-subtle, #e5e7eb)',
    display: 'flex',
    flexDirection: 'column',
    gap: 6,
  },
  gradeCardTotal: {
    backgroundColor: 'var(--bg-card, #ffffff)',
    borderRadius: 10,
    padding: '20px 18px',
    border: '2px solid #16a34a',
    display: 'flex',
    flexDirection: 'column',
    gap: 6,
  },
  gradeCategory: {
    fontSize: 12,
    fontWeight: 700,
    color: 'var(--text-muted, #6b7280)',
    textTransform: 'uppercase',
  },
  gradeScore: {
    fontSize: 24,
    fontWeight: 800,
  },
  gradeScoreTotal: {
    fontSize: 24,
    fontWeight: 800,
  },
  gradeDesc: {
    fontSize: 12,
    color: 'var(--text-muted, #6b7280)',
    margin: 0,
    lineHeight: 1.4,
  },
  clearanceBox: {
    backgroundColor: 'var(--bg-card, #ffffff)',
    borderRadius: 16,
    padding: '48px 24px',
    textAlign: 'center',
    border: '1px solid var(--border-subtle, #e5e7eb)',
  },
  downloadBtn: {
    display: 'inline-flex',
    alignItems: 'center',
    gap: 8,
    padding: '12px 24px',
    borderRadius: 8,
    border: 'none',
    color: '#ffffff',
    fontSize: 14,
    fontWeight: 700,
    cursor: 'pointer',
  },
  modalOverlay: {
    position: 'fixed',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: 'rgba(0,0,0,0.65)',
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
    maxWidth: 500,
    width: '100%',
    boxSizing: 'border-box',
  },
  modalTitle: {
    fontSize: 18,
    fontWeight: 800,
    margin: '0 0 4px',
  },
  modalSub: {
    fontSize: 12,
    color: 'var(--text-muted, #6b7280)',
    margin: '0 0 16px',
  },
  formGroup: {
    marginBottom: 14,
  },
  label: {
    display: 'block',
    fontSize: 12,
    fontWeight: 600,
    marginBottom: 4,
    color: 'var(--text-primary, #374151)',
  },
  input: {
    width: '100%',
    height: 40,
    padding: '0 12px',
    borderRadius: 6,
    border: '1px solid var(--border-input, #d1d5db)',
    backgroundColor: 'var(--bg-input, #ffffff)',
    color: 'var(--text-primary, #111827)',
    boxSizing: 'border-box',
    fontSize: 13,
  },
  cancelBtn: {
    padding: '8px 16px',
    borderRadius: 6,
    border: '1px solid var(--border-subtle, #d1d5db)',
    background: 'none',
    cursor: 'pointer',
    fontSize: 13,
    fontWeight: 600,
  },
};
