import React, { useState, useEffect, useCallback, useRef } from 'react';
import { useAuth } from '../context/AuthContext';
import api from '../services/api';
import toast from 'react-hot-toast';
import { LayoutDashboard, FileText, Upload, Bell, MessageSquare, LogOut } from 'lucide-react';

export default function StudentPortal() {
  const { user, logout, refreshUser } = useAuth();
  const [tab,       setTab]       = useState('dashboard');
  const [dashboard, setDashboard] = useState(null);
  const [alerts,    setAlerts]    = useState([]);
  const [loading,   setLoading]   = useState(true);

  const loadDashboard = useCallback(async () => {
    try {
      const [dRes, aRes] = await Promise.all([
        api.get('/projects/dashboard'),
        api.get('/alerts'),
      ]);
      setDashboard(dRes.data);
      setAlerts(aRes.data.alerts || []);
    } catch (err) {
      toast.error('Failed to load dashboard.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { loadDashboard(); }, [loadDashboard]);

  if (loading) return <Loader />;

  const unread = alerts.filter(a => !a.is_read).length;

  return (
    <div style={s.layout}>
      <Sidebar role={user?.role} active={tab} onTab={setTab} onLogout={logout} unread={unread} />
      <main style={s.main}>
        <TopBar title={TAB_TITLES[tab] || 'Student Portal'} user={user} onProfile={() => setTab('profile')} />
        <div style={s.content}>
          {tab === 'dashboard' && <Dashboard data={dashboard} />}
          {tab === 'proposal'  && <ProposalForm onSubmit={loadDashboard} />}
          {tab === 'progress'  && <ProgressTab  data={dashboard} />}
          {tab === 'alerts'    && <AlertsTab    alerts={alerts} reload={loadDashboard} />}
          {tab === 'messages'  && <MessagesTab  user={user} supervisor={dashboard?.supervisor} coSupervisor={dashboard?.co_supervisor} />}
          {tab === 'profile'   && <ProfileTab   user={user} onUpdate={refreshUser} />}
        </div>
      </main>
    </div>
  );
}

// ─── DASHBOARD ────────────────────────────────
function Dashboard({ data }) {
  if (!data) return <p style={s.empty}>No project data yet.</p>;
  const p = data.project;
  const risk_color = { on_track: '#16a34a', at_risk: '#f59e0b', critical: '#dc2626' };

  return (
    <div>
      <div style={s.statsRow}>
        <StatCard label="Project Status"   value={p ? p.status.replace(/_/g,' ') : 'None'}    color="#16a34a" />
        <StatCard label="Chapter Progress" value={p ? `${Math.round((p.chapter_progress||0)*100)}%` : '—'} color="#15803d" />
        <StatCard label="Risk Level"       value={p ? (p.risk_label || 'Unscanned') : '—'}  color={risk_color[p?.risk_label] || '#6b7280'} />
        {data.co_supervisor ? (
          <>
            <StatCard label="Main Supervisor" value={data.supervisor?.full_name || 'Not Assigned'} color="#22c55e" />
            <StatCard label="Co-Supervisor"   value={data.co_supervisor?.full_name || 'Not Assigned'} color="#0ea5e9" />
          </>
        ) : (
          <StatCard label="Supervisor" value={data.supervisor?.full_name || 'Not Assigned'} color="#22c55e" />
        )}
      </div>

      {(data.supervisor || data.co_supervisor) && (
        <div style={{ ...s.card, marginBottom: 16 }}>
          <h3 style={s.cardTitle}>Assigned Supervision Team</h3>
          <div style={{ display: 'grid', gridTemplateColumns: data.co_supervisor ? '1fr 1fr' : '1fr', gap: 14 }}>
            {data.supervisor && (
              <div style={{ background: 'rgba(34,197,94,0.06)', border: '1px solid rgba(34,197,94,0.2)', borderRadius: 10, padding: 14 }}>
                <span style={{ fontSize: 11, fontWeight: 700, color: '#22c55e', textTransform: 'uppercase', letterSpacing: 0.5 }}>Main Supervisor</span>
                <h4 style={{ fontSize: 15, fontWeight: 700, color: '#fff', margin: '4px 0 2px' }}>{data.supervisor.full_name}</h4>
                <p style={{ fontSize: 12, color: '#9ca3af', margin: 0 }}>{data.supervisor.department || 'Faculty'}</p>
                {data.supervisor.email && <p style={{ fontSize: 12, color: '#6b7280', margin: '4px 0 0' }}>{data.supervisor.email}</p>}
                {data.supervisor.expertise_areas && <p style={{ fontSize: 11, color: '#4ade80', margin: '6px 0 0' }}>Expertise: {data.supervisor.expertise_areas}</p>}
              </div>
            )}
            {data.co_supervisor && (
              <div style={{ background: 'rgba(14,165,233,0.06)', border: '1px solid rgba(14,165,233,0.2)', borderRadius: 10, padding: 14 }}>
                <span style={{ fontSize: 11, fontWeight: 700, color: '#38bdf8', textTransform: 'uppercase', letterSpacing: 0.5 }}>Co-Supervisor</span>
                <h4 style={{ fontSize: 15, fontWeight: 700, color: '#fff', margin: '4px 0 2px' }}>{data.co_supervisor.full_name}</h4>
                <p style={{ fontSize: 12, color: '#9ca3af', margin: 0 }}>{data.co_supervisor.department || 'Faculty'}</p>
                {data.co_supervisor.email && <p style={{ fontSize: 12, color: '#6b7280', margin: '4px 0 0' }}>{data.co_supervisor.email}</p>}
                {data.co_supervisor.expertise_areas && <p style={{ fontSize: 11, color: '#38bdf8', margin: '6px 0 0' }}>Expertise: {data.co_supervisor.expertise_areas}</p>}
              </div>
            )}
          </div>
        </div>
      )}

      {p ? (
        <div style={s.card}>
          <h3 style={s.cardTitle}>{p.title}</h3>
          <p style={{ color: '#9ca3af', fontSize: 13, marginBottom: 10 }}>{p.abstract}</p>
          <div style={s.tagRow}>
            <Tag color="rgba(59,130,246,0.15)" text={`Status: ${p.status}`} />
            <Tag color="rgba(22,163,74,0.15)" text={`Chapter ${p.current_chapter}/5`} />
            {p.risk_label && <Tag color={p.risk_label === 'on_track' ? 'rgba(22,163,74,0.15)' : 'rgba(239,68,68,0.15)'} text={`Risk: ${p.risk_label}`} />}
          </div>
          {p.feedback_latest && (
            <div style={s.feedbackBox}>
              <strong style={{ fontSize: 12 }}>Latest Feedback:</strong>
              <p style={{ fontSize: 13, marginTop: 4 }}>{p.feedback_latest}</p>
            </div>
          )}
        </div>
      ) : (
        <div style={s.card}>
          <p style={s.empty}>You have no active project. Use the Proposal tab to submit your research proposal.</p>
        </div>
      )}

      {data.milestones?.length > 0 && (
        <div style={{ ...s.card, marginTop: 16 }}>
          <h3 style={s.cardTitle}>Milestone Progress</h3>
          {data.milestones.map(m => (
            <div key={m.milestone_id} style={s.milestoneRow}>
              <span style={{ flex: 1, fontSize: 13 }}>{m.title}</span>
              <span style={{ fontSize: 12, color: m.is_completed ? '#16a34a' : '#f59e0b', fontWeight: 600 }}>
                {m.is_completed ? 'Completed' : m.is_overdue ? 'Overdue' : 'Pending'}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}


// ─── PROPOSAL FORM ────────────────────────────
function ProposalForm({ onSubmit }) {
  const [form, setForm] = useState({ title: '', abstract: '', keywords: '', objectives: '' });
  const [file, setFile] = useState(null);
  const [busy, setBusy] = useState(false);
  const set = (k, v) => setForm(prev => ({ ...prev, [k]: v }));

  const handleSubmit = async (e) => {
    e.preventDefault();
    setBusy(true);
    try {
      const fd = new FormData();
      Object.entries(form).forEach(([k, v]) => fd.append(k, v));
      if (file) fd.append('document', file);
      await api.post('/projects/submit', fd, { headers: { 'Content-Type': 'multipart/form-data' } });
      toast.success('Proposal submitted successfully!');
      onSubmit();
      setForm({ title: '', abstract: '', keywords: '', objectives: '' });
      setFile(null);
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Submission failed.');
    } finally {
      setBusy(false);
    }
  };

  return (
    <div style={s.card}>
      <h3 style={s.cardTitle}>Submit Research Proposal</h3>
      <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
        <FormField label="Project Title *">
          <input style={s.input} value={form.title} onChange={e => set('title', e.target.value)} required placeholder="Your research title" />
        </FormField>
        <FormField label="Abstract *">
          <textarea style={{ ...s.input, height: 100, resize: 'vertical' }} value={form.abstract} onChange={e => set('abstract', e.target.value)} required placeholder="Brief description (min 50 chars)" />
        </FormField>
        <FormField label="Keywords (comma-separated)">
          <input style={s.input} value={form.keywords} onChange={e => set('keywords', e.target.value)} placeholder="e.g. machine learning, neural networks" />
        </FormField>
        <FormField label="Objectives">
          <textarea style={{ ...s.input, height: 80, resize: 'vertical' }} value={form.objectives} onChange={e => set('objectives', e.target.value)} placeholder="Research objectives" />
        </FormField>
        <FormField label="Proposal Document (PDF)">
          <input style={s.input} type="file" accept=".pdf,.doc,.docx" onChange={e => setFile(e.target.files[0])} />
        </FormField>
        <button type="submit" style={busy ? { ...s.btn, opacity: 0.6 } : s.btn} disabled={busy}>
          {busy ? 'Submitting…' : 'Submit Proposal'}
        </button>
      </form>
    </div>
  );
}

// ─── PROGRESS TAB ─────────────────────────────
function ProgressTab({ data }) {
  const [chapter, setChapter] = useState('1');
  const [file,    setFile]    = useState(null);
  const [note,    setNote]    = useState('');
  const [busy,    setBusy]    = useState(false);

  if (!data?.project) return <p style={s.empty}>No active project.</p>;

  const handleUpload = async (e) => {
    e.preventDefault();
    if (!file) { toast.error('Select a file first.'); return; }
    setBusy(true);
    try {
      const fd = new FormData();
      fd.append('chapter', chapter);
      fd.append('notes',   note);
      fd.append('document', file);
      await api.post('/projects/upload-chapter', fd, { headers: { 'Content-Type': 'multipart/form-data' } });
      toast.success('Chapter uploaded!');
      setFile(null); setNote('');
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Upload failed.');
    } finally {
      setBusy(false);
    }
  };

  return (
    <div style={s.card}>
      <h3 style={s.cardTitle}>Upload Chapter Progress</h3>
      <form onSubmit={handleUpload} style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
        <FormField label="Chapter">
          <select style={s.input} value={chapter} onChange={e => setChapter(e.target.value)}>
            {['1','2','3','4','5'].map(c => <option key={c} value={c}>Chapter {c}</option>)}
          </select>
        </FormField>
        <FormField label="Document (PDF)">
          <input style={s.input} type="file" accept=".pdf,.doc,.docx" onChange={e => setFile(e.target.files[0])} required />
        </FormField>
        <FormField label="Notes (optional)">
          <textarea style={{ ...s.input, height: 70, resize: 'vertical' }} value={note} onChange={e => setNote(e.target.value)} placeholder="Additional notes for your supervisor" />
        </FormField>
        <button type="submit" style={busy ? { ...s.btn, opacity: 0.6 } : s.btn} disabled={busy}>
          {busy ? 'Uploading…' : 'Upload Chapter'}
        </button>
      </form>
    </div>
  );
}

// ─── ALERTS TAB ───────────────────────────────
function AlertsTab({ alerts, reload }) {
  const markRead = async (id) => {
    try { await api.patch(`/alerts/${id}/read`); reload(); } catch {}
  };
  const markAll = async () => {
    try { await api.patch('/alerts/read-all'); reload(); } catch {}
  };

  const sev = { info: 'rgba(59,130,246,0.12)', warning: 'rgba(245,158,11,0.12)', critical: 'rgba(239,68,68,0.12)', success: 'rgba(22,163,74,0.12)' };

  return (
    <div style={s.card}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <h3 style={s.cardTitle}>Notifications</h3>
        {alerts.some(a => !a.is_read) &&
          <button style={s.smBtn} onClick={markAll}>Mark all read</button>}
      </div>
      {alerts.length === 0 ? <p style={s.empty}>No notifications.</p> : alerts.map(a => (
        <div key={a.alert_id} style={{ ...s.alertItem, background: sev[a.severity] || '#f8faff', opacity: a.is_read ? 0.6 : 1 }}>
          <div style={{ flex: 1 }}>
            <p style={{ fontWeight: 600, fontSize: 13 }}>{a.title}</p>
            <p style={{ fontSize: 12, color: '#9ca3af', marginTop: 2 }}>{a.message}</p>
            <p style={{ fontSize: 11, color: '#4b5563', marginTop: 4 }}>{new Date(a.triggered_at).toLocaleString()}</p>
          </div>
          {!a.is_read && <button style={s.smBtn} onClick={() => markRead(a.alert_id)}>Mark read</button>}
        </div>
      ))}
    </div>
  );
}

// ─── MESSAGES TAB ─────────────────────────────
function MessagesTab({ user, supervisor, coSupervisor }) {
  const [messages, setMessages] = useState([]);
  const [compose,  setCompose]  = useState(false);
  const defaultRecipient = supervisor?.user_id ? String(supervisor.user_id) : (coSupervisor?.user_id ? String(coSupervisor.user_id) : '');
  const [msgForm,  setMsgForm]  = useState({ receiver_id: defaultRecipient, subject: '', body: '' });
  const [busy,     setBusy]     = useState(false);

  const fetchMessages = () => api.get('/messages').then(r => setMessages(r.data.messages || [])).catch(() => {});
  useEffect(() => { fetchMessages(); }, []);

  const handleSend = async (e) => {
    e.preventDefault();
    setBusy(true);
    try {
      await api.post('/messages', { ...msgForm, receiver_id: Number(msgForm.receiver_id) });
      toast.success('Message sent!');
      setCompose(false);
      setMsgForm({ receiver_id: defaultRecipient, subject: '', body: '' });
      fetchMessages();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Send failed.');
    } finally {
      setBusy(false);
    }
  };

  return (
    <div style={s.card}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <h3 style={s.cardTitle}>Messages</h3>
        <button style={s.btn} onClick={() => setCompose(!compose)}>
          {compose ? 'Cancel' : '+ New Message'}
        </button>
      </div>

      {compose && (
        <form onSubmit={handleSend} style={{ ...s.feedbackBox, marginBottom: 16, display: 'flex', flexDirection: 'column', gap: 10 }}>
          <FormField label="Send To *">
            {(supervisor || coSupervisor) ? (
              <select style={s.input} value={msgForm.receiver_id} onChange={e => setMsgForm(p => ({...p, receiver_id: e.target.value}))} required>
                {supervisor && (
                  <option value={supervisor.user_id}>
                    Main Supervisor — {supervisor.full_name} ({supervisor.department || 'Faculty'})
                  </option>
                )}
                {coSupervisor && (
                  <option value={coSupervisor.user_id}>
                    Co-Supervisor — {coSupervisor.full_name} ({coSupervisor.department || 'Faculty'})
                  </option>
                )}
              </select>
            ) : (
              <input style={s.input} type="number" value={msgForm.receiver_id}
                onChange={e => setMsgForm(p => ({...p, receiver_id: e.target.value}))} required placeholder="User ID of recipient" />
            )}
          </FormField>

          <FormField label="Subject">
            <input style={s.input} value={msgForm.subject} onChange={e => setMsgForm(p => ({...p, subject: e.target.value}))} placeholder="Message subject" />
          </FormField>
          <FormField label="Body *">
            <textarea style={{ ...s.input, height: 80, resize: 'vertical' }} value={msgForm.body}
              onChange={e => setMsgForm(p => ({...p, body: e.target.value}))} required placeholder="Your message…" />
          </FormField>
          <button type="submit" style={busy ? { ...s.btn, opacity: 0.6 } : s.btn} disabled={busy}>
            {busy ? 'Sending…' : 'Send'}
          </button>
        </form>
      )}

      {messages.length === 0 ? <p style={s.empty}>No messages yet.</p> : messages.map(m => (
        <div key={m.message_id} style={{ ...s.alertItem, background: m.is_read ? '#0f0f0f' : 'rgba(22,163,74,0.06)' }}>
          <div>
            <p style={{ fontWeight: 600, fontSize: 13, color: '#fff' }}>{m.subject || '(No subject)'}</p>
            <p style={{ fontSize: 12, color: '#6b7280', marginTop: 2 }}>From: {m.sender_name} · {new Date(m.sent_at).toLocaleString()}</p>
            <p style={{ fontSize: 13, marginTop: 4, color: '#9ca3af' }}>{m.body}</p>
          </div>
        </div>
      ))}
    </div>
  );
}

// ─── PROFILE TAB ──────────────────────────────
function ProfileTab({ user, onUpdate }) {
  const fileRef = useRef(null);
  const [uploading, setUploading] = useState(false);

  const handleFile = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const fd = new FormData();
    fd.append('file', file);
    setUploading(true);
    try {
      await api.patch('/auth/profile/avatar', fd, { headers: { 'Content-Type': 'multipart/form-data' } });
      toast.success('Profile picture updated!');
      onUpdate();
    } catch {
      toast.error('Upload failed.');
    } finally {
      setUploading(false);
    }
  };

  return (
    <div style={s.card}>
      <h3 style={s.cardTitle}>My Profile</h3>
      <div style={{ display: 'flex', alignItems: 'center', gap: 20, marginBottom: 20 }}>
        <div style={{ position: 'relative', cursor: 'pointer' }} onClick={() => fileRef.current?.click()}>
          {user?.avatar_url
            ? <img src={user.avatar_url} alt="avatar" style={{ width: 72, height: 72, borderRadius: '50%', objectFit: 'cover', border: '2px solid #16a34a' }} />
            : <div style={{ width: 72, height: 72, background: '#16a34a', borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 28, fontWeight: 700, color: '#fff', border: '2px solid #22c55e' }}>{user?.full_name?.[0]}</div>}
          <div style={{ position: 'absolute', bottom: 0, right: 0, background: '#16a34a', borderRadius: '50%', width: 22, height: 22, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 13 }}>&#9998;</div>
        </div>
        <div>
          <p style={{ fontWeight: 700, fontSize: 16, color: '#fff' }}>{user?.full_name}</p>
          <p style={{ fontSize: 13, color: '#9ca3af' }}>{user?.email}</p>
          <p style={{ fontSize: 12, color: '#4b5563', marginTop: 4 }}>Role: {user?.role}</p>
          <button style={{ ...s.smBtn, marginTop: 8 }} onClick={() => fileRef.current?.click()} disabled={uploading}>
            {uploading ? 'Uploading…' : 'Change Photo'}
          </button>
        </div>
      </div>
      <input ref={fileRef} type="file" accept="image/*" style={{ display: 'none' }} onChange={handleFile} />
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
        {[['Username', user?.username], ['Email', user?.email], ['Phone', user?.phone || '—'], ['Matric No.', user?.matric_number || '—']].map(([label, val]) => (
          <div key={label} style={{ background: '#0f0f0f', borderRadius: 8, padding: '12px 14px' }}>
            <p style={s.label}>{label}</p>
            <p style={{ fontSize: 13, color: '#e5e7eb' }}>{val}</p>
          </div>
        ))}
      </div>
    </div>
  );
}

// ─── SHARED COMPONENTS ────────────────────────
function Sidebar({ role, active, onTab, onLogout, unread }) {
  const tabs = [
    { id: 'dashboard', label: 'Dashboard',  Icon: LayoutDashboard },
    { id: 'proposal',  label: 'Proposal',   Icon: FileText },
    { id: 'progress',  label: 'Progress',   Icon: Upload },
    { id: 'alerts',    label: `Alerts${unread > 0 ? ` (${unread})` : ''}`, Icon: Bell },
    { id: 'messages',  label: 'Messages',   Icon: MessageSquare },
  ];
  return (
    <aside style={s.sidebar}>
      <div style={s.sideHeader}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 8 }}>
          <img src="/kwasu.png" alt="KWASU" style={s.logoImg} />
          <div>
            <div style={{ color: '#ffffff', fontWeight: 800, fontSize: 16, letterSpacing: '0.5px', lineHeight: 1.2 }}>KWASU</div>
            <div style={{ color: '#22c55e', fontSize: 10, fontWeight: 700, letterSpacing: '1px' }}>SPSEMS</div>
          </div>
        </div>
        <p style={s.sideRole}>{role?.toUpperCase() || 'STUDENT'}</p>
      </div>
      <nav style={{ flex: 1, paddingTop: 8 }}>
        {tabs.map(({ id, label, Icon }) => (
          <button key={id} style={active === id ? { ...s.navBtn, ...s.navBtnActive } : s.navBtn} onClick={() => onTab(id)}>
            <Icon size={15} style={{ flexShrink: 0 }} />
            <span>{label}</span>
          </button>
        ))}
      </nav>
      <div style={{ padding: '0 12px 4px' }}>
        <button style={s.logoutBtn} onClick={onLogout}>
          <LogOut size={14} />
          Sign Out
        </button>
      </div>
    </aside>
  );
}

function TopBar({ title, user, onProfile }) {
  return (
    <div style={s.topbar}>
      <h2 style={s.topbarTitle}>{title}</h2>
      <div style={{ ...s.userChip, cursor: 'pointer' }} onClick={onProfile} title="View profile">
        {user?.avatar_url
          ? <img src={user.avatar_url} alt="avatar" style={{ width: 32, height: 32, borderRadius: '50%', objectFit: 'cover', border: '2px solid #16a34a' }} />
          : <div style={s.avatar}>{user?.full_name?.[0] || 'U'}</div>}
        <span style={{ fontSize: 13, fontWeight: 600, color: '#e5e7eb' }}>{user?.full_name}</span>
      </div>
    </div>
  );
}

function StatCard({ label, value, color }) {
  return (
    <div style={{ ...s.statCard, borderTopColor: color }}>
      <p style={s.statLabel}>{label}</p>
      <p style={{ ...s.statValue, color }}>{value}</p>
    </div>
  );
}

function Tag({ color, text }) {
  return <span style={{ background: color, color: '#e5e7eb', padding: '3px 10px', borderRadius: 20, fontSize: 11, fontWeight: 600 }}>{text}</span>;
}

function FormField({ label, children }) {
  return (
    <div>
      <label style={s.label}>{label}</label>
      {children}
    </div>
  );
}

function Loader() {
  return <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100vh', fontSize: 15, color: '#16a34a', background: '#0a0a0a', fontWeight: 500, letterSpacing: '0.3px' }}>Loading...</div>;
}

const TAB_TITLES = { dashboard: 'Dashboard', proposal: 'Submit Proposal', progress: 'Chapter Progress', alerts: 'Notifications', messages: 'Messages', profile: 'My Profile' };

const s = {
  layout:    { display: 'flex', minHeight: '100vh', background: '#0a0a0a' },
  sidebar:   { width: 228, background: '#080808', display: 'flex', flexDirection: 'column', padding: '24px 0', borderRight: '1px solid rgba(255,255,255,0.06)' },
  sideHeader:{ padding: '0 20px 20px', borderBottom: '1px solid rgba(255,255,255,0.07)' },
  logoImg:   { height: 38, width: 'auto', display: 'block', objectFit: 'contain' },
  sideRole:  { color: '#4b5563', fontSize: 10, letterSpacing: '1.5px', textTransform: 'uppercase', fontWeight: 600 },
  navBtn:    { display: 'flex', alignItems: 'center', gap: 10, width: '100%', padding: '10px 20px', background: 'none', border: 'none', borderLeft: '3px solid transparent', color: '#6b7280', textAlign: 'left', fontSize: 13, cursor: 'pointer', fontWeight: 500, transition: 'all 0.15s' },
  navBtnActive: { background: 'rgba(22,163,74,0.08)', color: '#22c55e', borderLeftColor: '#16a34a', fontWeight: 600 },
  logoutBtn: { width: '100%', padding: '10px 12px', background: 'rgba(239,68,68,0.08)', border: '1px solid rgba(239,68,68,0.15)', borderRadius: 7, color: '#f87171', cursor: 'pointer', fontSize: 12, fontWeight: 600, display: 'flex', alignItems: 'center', gap: 8 },
  main:      { flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' },
  topbar:    { background: '#0f0f0f', padding: '14px 24px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid rgba(255,255,255,0.07)' },
  topbarTitle: { fontSize: 17, fontWeight: 700, color: '#ffffff', letterSpacing: '-0.3px' },
  userChip:  { display: 'flex', alignItems: 'center', gap: 8 },
  avatar:    { width: 32, height: 32, background: '#16a34a', borderRadius: '50%', color: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 700, fontSize: 13 },
  content:   { flex: 1, padding: '24px', overflowY: 'auto', background: '#0a0a0a' },
  statsRow:  { display: 'grid', gridTemplateColumns: 'repeat(4,1fr)', gap: 14, marginBottom: 20 },
  statCard:  { background: '#141414', borderRadius: 10, padding: '16px 18px', borderTop: '3px solid', border: '1px solid rgba(255,255,255,0.07)', borderTopWidth: 3 },
  statLabel: { fontSize: 10, color: '#6b7280', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.6px', marginBottom: 8 },
  statValue: { fontSize: 20, fontWeight: 800, textTransform: 'capitalize' },
  card:      { background: '#141414', borderRadius: 12, padding: '20px 22px', border: '1px solid rgba(255,255,255,0.07)' },
  cardTitle: { fontSize: 15, fontWeight: 700, color: '#ffffff', marginBottom: 14, letterSpacing: '-0.2px' },
  tagRow:    { display: 'flex', gap: 8, flexWrap: 'wrap', marginBottom: 10 },
  feedbackBox: { background: 'rgba(22,163,74,0.08)', border: '1px solid rgba(22,163,74,0.2)', borderRadius: 8, padding: '12px 14px', marginTop: 12 },
  milestoneRow: { display: 'flex', justifyContent: 'space-between', padding: '9px 0', borderBottom: '1px solid rgba(255,255,255,0.06)' },
  alertItem: { padding: '12px 14px', borderRadius: 8, marginBottom: 8, display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 10, border: '1px solid rgba(255,255,255,0.07)' },
  label:     { display: 'block', fontSize: 11, fontWeight: 600, color: '#6b7280', marginBottom: 5, letterSpacing: '0.3px', textTransform: 'uppercase' },
  input: {
    width: '100%', padding: '9px 11px',
    background: '#0f0f0f', border: '1px solid rgba(255,255,255,0.1)',
    borderRadius: 7, fontSize: 13, outline: 'none', color: '#fff', boxSizing: 'border-box',
  },
  btn: {
    padding: '10px 18px', background: '#16a34a', color: '#fff', border: 'none',
    borderRadius: 7, fontWeight: 600, fontSize: 13, cursor: 'pointer',
  },
  smBtn: {
    padding: '5px 12px', background: 'rgba(22,163,74,0.1)', color: '#22c55e',
    border: '1px solid rgba(22,163,74,0.2)', borderRadius: 6, fontSize: 12, fontWeight: 600, cursor: 'pointer', whiteSpace: 'nowrap',
  },
  empty: { color: '#4b5563', fontSize: 13, textAlign: 'center', padding: '32px 0' },
};
