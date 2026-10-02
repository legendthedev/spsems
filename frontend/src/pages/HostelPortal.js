/* eslint-disable no-unused-vars */
import React, { useState, useEffect } from 'react';
import { useNavigate, useParams, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import toast from 'react-hot-toast';
import {
  Home, Bed, CheckCircle2, Clock, FileText, Download,
  Building, User, LogOut, ArrowLeft, Key, ShieldCheck,
  Zap, Droplet, Wifi, AlertTriangle, Layers, Wrench, Plus
} from 'lucide-react';
import api from '../services/api';
import ThemeToggle from '../components/ThemeToggle';
import { resolveLogoUrl } from '../utils/logoHelper';

export default function HostelPortal() {
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

  const [tab, setTab] = useState('balloting');
  const [selectedHall, setSelectedHall] = useState('hall_a');
  const [allocation, setAllocation] = useState({
    hallName: 'Unity Hall of Residence (Block A)',
    roomNumber: 'Room 204',
    floor: 'Second Floor',
    bedNumber: 'Bedspace 2 (Upper Bunk)',
    allocatedDate: 'September 15, 2025',
    session: '2025/2026 Academic Session',
    slipNumber: 'KWAPOLY/HSTL/2025/0984',
    feeStatus: 'Paid & Cleared',
    wardenEndorsed: true,
  });

  const [halls, setHalls] = useState([
    {
      id: 'hall_a',
      name: 'Unity Hall (Block A - Male)',
      gender: 'Male Students',
      capacity: 320,
      available: 42,
      price: '₦ 45,000 / Session',
      features: ['24/7 Solar Inverter', 'Dedicated Borehole', 'Reading Room'],
    },
    {
      id: 'hall_b',
      name: 'Queens Hall (Block B - Female)',
      gender: 'Female Students',
      capacity: 350,
      available: 58,
      price: '₦ 45,000 / Session',
      features: ['24/7 Solar Inverter', 'Dedicated Borehole', 'Perimeter Security'],
    },
    {
      id: 'hall_c',
      name: 'Executive Postgraduate Residence (Block C)',
      gender: 'MSc / PhD & Finalists',
      capacity: 140,
      available: 19,
      price: '₦ 75,000 / Session',
      features: ['Self-Contained En-suite', 'High-Speed Wi-Fi', 'Air Conditioned Study'],
    }
  ]);

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
        console.warn('Fallback to default institution for Hostel');
      }
    }
    loadInst();
  }, [targetSlug]);

  const primaryColor = institution.primary_color || '#237e3d';

  const handleBallot = (hall) => {
    setAllocation({
      hallName: hall.name,
      roomNumber: `Room ${Math.floor(Math.random() * 300) + 101}`,
      floor: 'Floor 1',
      bedNumber: `Bedspace ${Math.floor(Math.random() * 4) + 1}`,
      allocatedDate: new Date().toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' }),
      session: '2025/2026 Academic Session',
      slipNumber: `${institution.code}/HSTL/2025/${Math.floor(Math.random() * 8999) + 1000}`,
      feeStatus: 'Paid & Cleared',
      wardenEndorsed: true,
    });
    setTab('my_slip');
    toast.success(`Bedspace successfully balloted in ${hall.name}!`);
  };

  const handleLogout = () => {
    logout();
    navigate(`/login/${institution.slug}/hostel`);
    toast.success('Signed out of Hostel Allocation Portal');
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
                {institution.code ? institution.code.slice(0, 3) : 'HST'}
              </div>
            )}
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <span style={{ ...s.portalBadge, backgroundColor: `${primaryColor}18`, color: primaryColor, borderColor: `${primaryColor}40` }}>
                  PORTAL GATEWAY: HOSTEL-03
                </span>
                <span style={s.activePill}>LIVE INSTANCE</span>
              </div>
              <h1 style={s.headerTitle}>
                {institution.name} — Hostel &amp; Bedspace Allocation Portal
              </h1>
            </div>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            {/* Quick jump to SPSEMS or SIWES */}
            <div style={s.switchPortalBox}>
              <Link to={`/login/${institution.slug}/spsems`} style={s.switchPortalLink}>
                <Layers size={13} color={primaryColor} />
                <span>SPSEMS Portal</span>
              </Link>
              <span style={{ color: '#ccc' }}>•</span>
              <Link to={`/login/${institution.slug}/siwes`} style={s.switchPortalLink}>
                <span>SIWES Portal</span>
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

        {/* Navigation Tabs */}
        <div style={s.tabBar}>
          {[
            { id: 'balloting', label: 'Halls & Bedspace Balloting', icon: Home },
            { id: 'my_slip', label: 'Official Allocation Slip', icon: FileText },
            { id: 'regulations', label: 'Hall Rules & Dues', icon: ShieldCheck },
            { id: 'warden', label: 'Warden Clearance & Maintenance', icon: Key },
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
        {/* TAB 1: HALLS & BALLOTING */}
        {tab === 'balloting' && (
          <div style={s.tabContent}>
            <div style={s.heroNoticeBox}>
              <div>
                <h2 style={{ fontSize: 18, fontWeight: 800, margin: '0 0 4px' }}>
                  2025/2026 Bedspace Balloting Window Open
                </h2>
                <p style={{ fontSize: 12, color: 'var(--text-muted, #6b7280)', margin: 0 }}>
                  Select an approved hall of residence matching your gender/faculty eligibility and confirm bedspace reservation.
                </p>
              </div>
              <span style={{ ...s.statusPill, backgroundColor: 'rgba(22,163,74,0.12)', color: '#16a34a' }}>
                <CheckCircle2 size={13} /> Balloting Active
              </span>
            </div>

            <div style={s.hallsGrid}>
              {halls.map(hall => (
                <div key={hall.id} style={s.hallCard}>
                  <div style={s.hallCardHead}>
                    <span style={s.hallGenderBadge}>{hall.gender}</span>
                    <span style={{ fontSize: 12, fontWeight: 700, color: primaryColor }}>{hall.price}</span>
                  </div>
                  <h3 style={s.hallName}>{hall.name}</h3>
                  <div style={s.availabilityRow}>
                    <Bed size={15} color={primaryColor} />
                    <span style={{ fontSize: 12, fontWeight: 600 }}>
                      <b>{hall.available}</b> bedspaces available (Total capacity: {hall.capacity})
                    </span>
                  </div>

                  <div style={s.featuresList}>
                    {hall.features.map(f => (
                      <span key={f} style={s.featurePill}>
                        <Zap size={11} color={primaryColor} />
                        <span>{f}</span>
                      </span>
                    ))}
                  </div>

                  <button
                    onClick={() => handleBallot(hall)}
                    style={{ ...s.ballotBtn, backgroundColor: primaryColor }}
                  >
                    <span>Reserve Bedspace in {hall.gender.split(' ')[0]}</span>
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* TAB 2: OFFICIAL ALLOCATION SLIP */}
        {tab === 'my_slip' && (
          <div style={s.tabContent}>
            <div style={s.slipOuterCard}>
              {/* Slip Header with University Crest */}
              <div style={s.slipHeader}>
                {resolveLogoUrl(institution.logo_url) ? (
                  <img
                    src={resolveLogoUrl(institution.logo_url)}
                    alt=""
                    style={{ height: 60, objectFit: 'contain', marginBottom: 8 }}
                  />
                ) : (
                  <Building size={40} color={primaryColor} style={{ marginBottom: 8 }} />
                )}
                <h2 style={{ fontSize: 18, fontWeight: 800, margin: '0 0 2px', textTransform: 'uppercase' }}>
                  {institution.name}
                </h2>
                <div style={{ fontSize: 11, fontWeight: 700, color: primaryColor, letterSpacing: '0.8px' }}>
                  STUDENT AFFAIRS DIVISION • DIRECTORATE OF STUDENT RESIDENCE
                </div>
                <div style={s.slipTitleBanner}>OFFICIAL BEDSPACE ALLOCATION PASS</div>
              </div>

              {/* Allocation Credentials Grid */}
              <div style={s.slipDetailsGrid}>
                <div style={s.slipDetailRow}>
                  <span style={s.slipLabel}>Resident Student Name:</span>
                  <span style={s.slipVal}>{user?.full_name || 'Enrolled Campus Resident'}</span>
                </div>
                <div style={s.slipDetailRow}>
                  <span style={s.slipLabel}>Matriculation / Staff ID:</span>
                  <span style={s.slipVal}>{user?.matric_number || user?.username || 'KWAPOLY/ST/2024/0912'}</span>
                </div>
                <div style={s.slipDetailRow}>
                  <span style={s.slipLabel}>Hall of Residence:</span>
                  <span style={{ ...s.slipVal, color: primaryColor, fontWeight: 800 }}>{allocation.hallName}</span>
                </div>
                <div style={s.slipDetailRow}>
                  <span style={s.slipLabel}>Room &amp; Floor:</span>
                  <span style={s.slipVal}>{allocation.roomNumber} ({allocation.floor})</span>
                </div>
                <div style={s.slipDetailRow}>
                  <span style={s.slipLabel}>Bedspace Identifier:</span>
                  <span style={{ ...s.slipVal, color: '#16a34a', fontWeight: 800 }}>{allocation.bedNumber}</span>
                </div>
                <div style={s.slipDetailRow}>
                  <span style={s.slipLabel}>Pass Serial Number:</span>
                  <code style={s.slipCode}>{allocation.slipNumber}</code>
                </div>
                <div style={s.slipDetailRow}>
                  <span style={s.slipLabel}>Hostel Dues Status:</span>
                  <span style={{ color: '#16a34a', fontWeight: 700 }}>VERIFIED PAID</span>
                </div>
                <div style={s.slipDetailRow}>
                  <span style={s.slipLabel}>Allocation Valid For:</span>
                  <span style={s.slipVal}>{allocation.session}</span>
                </div>
              </div>

              {/* Digital Verification Barcode / Stamp */}
              <div style={s.slipFooter}>
                <div style={s.stampBox}>
                  <ShieldCheck size={28} color="#16a34a" />
                  <div>
                    <div style={{ fontSize: 11, fontWeight: 800, color: '#16a34a' }}>CHIEF HALL WARDEN SIGN-OFF</div>
                    <div style={{ fontSize: 10, color: '#6b7280' }}>Digitally Certified on {allocation.allocatedDate}</div>
                  </div>
                </div>

                <button
                  onClick={() => toast.success('Official Hostel Allocation Slip exported for printing!')}
                  style={{ ...s.printSlipBtn, backgroundColor: primaryColor }}
                >
                  <Download size={15} />
                  <span>Download / Print Slip</span>
                </button>
              </div>
            </div>
          </div>
        )}

        {/* TAB 3: REGULATIONS & DUES */}
        {tab === 'regulations' && (
          <div style={s.tabContent}>
            <div style={s.card}>
              <h2 style={{ fontSize: 18, fontWeight: 800, margin: '0 0 8px' }}>
                Code of Conduct &amp; Residential Guidelines
              </h2>
              <p style={{ fontSize: 13, color: 'var(--text-muted, #6b7280)', marginBottom: 20 }}>
                All residents in {institution.name} hostels must comply with institutional campus tenancy guidelines.
              </p>

              <div style={s.rulesList}>
                {[
                  'Curfew Enforcement: Main hall entry gates are secured daily between 10:00 PM and 5:30 AM.',
                  'Cooking & Electrical Appliances: Only approved low-wattage cooking units allowed in designated kitchenettes.',
                  'Sub-letting & Squatting: Unauthorized transfer or sale of bedspaces results in immediate tenancy revocation.',
                  'Sanitation & Waste: Waste must be segregated and disposed into external campus collection bins daily.',
                  'Quiet Hours: Minimum noise policy enforced in all study wings from 9:00 PM.'
                ].map((rule, idx) => (
                  <div key={idx} style={s.ruleRow}>
                    <span style={{ ...s.ruleNumber, backgroundColor: `${primaryColor}20`, color: primaryColor }}>{idx + 1}</span>
                    <span style={{ fontSize: 13, lineHeight: 1.4 }}>{rule}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* TAB 4: WARDEN CLEARANCE & MAINTENANCE */}
        {tab === 'warden' && (
          <div style={s.tabContent}>
            <div style={s.card}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 18 }}>
                <div>
                  <h2 style={{ fontSize: 18, fontWeight: 800, margin: '0 0 4px' }}>
                    Facility Maintenance &amp; Room Clearance
                  </h2>
                  <p style={{ fontSize: 12, color: 'var(--text-muted, #6b7280)', margin: 0 }}>
                    Log repair requests for plumbing, electrical sockets, or submit key return upon semester completion.
                  </p>
                </div>
                <button
                  onClick={() => toast.success('Maintenance ticket submitted to Hall Porter.')}
                  style={{ ...s.ballotBtn, backgroundColor: primaryColor, width: 'auto', padding: '8px 16px' }}
                >
                  <Plus size={15} />
                  <span>Log Repair Request</span>
                </button>
              </div>

              <div style={s.maintenanceTable}>
                <div style={s.tableHeader}>
                  <span>Item / Issue</span>
                  <span>Room</span>
                  <span>Status</span>
                  <span>Action</span>
                </div>
                <div style={s.tableRow}>
                  <span>Overhead Reading Lamp Inspection</span>
                  <span>Room 204</span>
                  <span style={{ color: '#16a34a', fontWeight: 600 }}>Resolved</span>
                  <span style={{ color: '#6b7280', fontSize: 11 }}>Signed off</span>
                </div>
                <div style={s.tableRow}>
                  <span>Bathroom Faucet Washer Replacement</span>
                  <span>Block A Wing 2</span>
                  <span style={{ color: '#f59e0b', fontWeight: 600 }}>In Progress</span>
                  <span style={{ color: primaryColor, fontSize: 11, cursor: 'pointer' }}>Track Porter</span>
                </div>
              </div>
            </div>
          </div>
        )}
      </main>
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
  heroNoticeBox: {
    backgroundColor: 'var(--bg-card, #ffffff)',
    borderRadius: 12,
    padding: '18px 22px',
    border: '1px solid var(--border-subtle, #e5e7eb)',
    marginBottom: 20,
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    flexWrap: 'wrap',
    gap: 12,
  },
  statusPill: {
    display: 'inline-flex',
    alignItems: 'center',
    gap: 6,
    padding: '5px 12px',
    borderRadius: 16,
    fontSize: 12,
    fontWeight: 700,
  },
  hallsGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))',
    gap: 20,
  },
  hallCard: {
    backgroundColor: 'var(--bg-card, #ffffff)',
    borderRadius: 12,
    padding: '22px 20px',
    border: '1px solid var(--border-subtle, #e5e7eb)',
    display: 'flex',
    flexDirection: 'column',
    justifyContent: 'space-between',
    boxShadow: '0 1px 4px rgba(0,0,0,0.03)',
  },
  hallCardHead: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 10,
  },
  hallGenderBadge: {
    fontSize: 11,
    fontWeight: 700,
    color: '#6b7280',
    backgroundColor: 'var(--bg-main, #f3f4f6)',
    padding: '3px 8px',
    borderRadius: 4,
  },
  hallName: {
    fontSize: 16,
    fontWeight: 800,
    margin: '0 0 10px',
  },
  availabilityRow: {
    display: 'flex',
    alignItems: 'center',
    gap: 8,
    marginBottom: 14,
  },
  featuresList: {
    display: 'flex',
    flexDirection: 'column',
    gap: 6,
    marginBottom: 18,
  },
  featurePill: {
    display: 'flex',
    alignItems: 'center',
    gap: 6,
    fontSize: 12,
    color: 'var(--text-muted, #4b5563)',
  },
  ballotBtn: {
    width: '100%',
    padding: '10px 0',
    borderRadius: 6,
    border: 'none',
    color: '#ffffff',
    fontSize: 13,
    fontWeight: 700,
    cursor: 'pointer',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 6,
  },
  slipOuterCard: {
    maxWidth: 680,
    margin: '0 auto',
    backgroundColor: 'var(--bg-card, #ffffff)',
    borderRadius: 14,
    border: '2px solid var(--border-subtle, #e5e7eb)',
    padding: '32px 36px',
    boxShadow: '0 4px 20px rgba(0,0,0,0.06)',
  },
  slipHeader: {
    textAlign: 'center',
    borderBottom: '2px solid var(--border-subtle, #f3f4f6)',
    paddingBottom: 16,
    marginBottom: 20,
  },
  slipTitleBanner: {
    display: 'inline-block',
    marginTop: 10,
    padding: '4px 14px',
    backgroundColor: 'rgba(0,0,0,0.06)',
    borderRadius: 4,
    fontSize: 12,
    fontWeight: 800,
    letterSpacing: '1px',
  },
  slipDetailsGrid: {
    display: 'flex',
    flexDirection: 'column',
    gap: 12,
    marginBottom: 24,
  },
  slipDetailRow: {
    display: 'flex',
    justifyContent: 'space-between',
    padding: '6px 0',
    borderBottom: '1px dashed var(--border-subtle, #e5e7eb)',
    fontSize: 13,
  },
  slipLabel: {
    color: 'var(--text-muted, #6b7280)',
    fontWeight: 600,
  },
  slipVal: {
    fontWeight: 600,
    textAlign: 'right',
  },
  slipCode: {
    fontFamily: 'monospace',
    fontWeight: 700,
    backgroundColor: 'var(--bg-main, #f3f4f6)',
    padding: '2px 6px',
    borderRadius: 4,
  },
  slipFooter: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingTop: 16,
    borderTop: '1px solid var(--border-subtle, #f3f4f6)',
    flexWrap: 'wrap',
    gap: 14,
  },
  stampBox: {
    display: 'flex',
    alignItems: 'center',
    gap: 10,
  },
  printSlipBtn: {
    display: 'inline-flex',
    alignItems: 'center',
    gap: 8,
    padding: '9px 18px',
    borderRadius: 6,
    border: 'none',
    color: '#ffffff',
    fontSize: 13,
    fontWeight: 700,
    cursor: 'pointer',
  },
  card: {
    backgroundColor: 'var(--bg-card, #ffffff)',
    borderRadius: 12,
    padding: '24px 26px',
    border: '1px solid var(--border-subtle, #e5e7eb)',
  },
  rulesList: {
    display: 'flex',
    flexDirection: 'column',
    gap: 12,
  },
  ruleRow: {
    display: 'flex',
    alignItems: 'flex-start',
    gap: 12,
  },
  ruleNumber: {
    width: 24,
    height: 24,
    borderRadius: '50%',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    fontSize: 11,
    fontWeight: 800,
    flexShrink: 0,
  },
  maintenanceTable: {
    marginTop: 16,
    border: '1px solid var(--border-subtle, #e5e7eb)',
    borderRadius: 8,
    overflow: 'hidden',
  },
  tableHeader: {
    display: 'grid',
    gridTemplateColumns: '2fr 1fr 1fr 1fr',
    backgroundColor: 'var(--bg-main, #f3f4f6)',
    padding: '10px 14px',
    fontSize: 11,
    fontWeight: 700,
    color: '#6b7280',
  },
  tableRow: {
    display: 'grid',
    gridTemplateColumns: '2fr 1fr 1fr 1fr',
    padding: '12px 14px',
    fontSize: 12,
    borderTop: '1px solid var(--border-subtle, #f3f4f6)',
    alignItems: 'center',
  },
};
