/* eslint-disable no-unused-vars */
import React, { useState, useEffect, useCallback, useRef } from 'react';
import { useAuth } from '../context/AuthContext';
import api from '../services/api';
import toast from 'react-hot-toast';
import { LayoutDashboard, UserCog, Zap, Shuffle, History, Bell, LogOut, FolderOpen, BarChart2, Cpu, Building2, Upload, Camera, AlertTriangle, RefreshCw, Briefcase, Home, Layers } from 'lucide-react';
import ThemeToggle from '../components/ThemeToggle';
import { resolveLogoUrl } from '../utils/logoHelper';

export default function AdminPortal() {
  const { user, logout, refreshUser } = useAuth();
  const [tab,    setTab]    = useState('dashboard');
  const [stats,  setStats]  = useState(null);
  const [users,  setUsers]  = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    try {
      const [sRes, uRes, aRes] = await Promise.all([
        api.get('/admin/stats'),
        api.get('/admin/users'),
        api.get('/alerts'),
      ]);
      setStats(sRes.data);
      setUsers(uRes.data.users || []);
      setAlerts(aRes.data.alerts || []);
    } catch {
      toast.error('Failed to load admin data.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  if (loading) return <Loader />;
  const unread = alerts.filter(a => !a.is_read).length;

  return (
    <div style={s.layout}>
      <Sidebar active={tab} onTab={setTab} onLogout={logout} unread={unread} role={user?.role} user={user} />
      <main style={s.main}>
        <TopBar title={TAB_TITLES[tab] || 'Admin Portal'} user={user} onProfile={() => setTab('profile')} />
        <div style={s.content}>
          {tab === 'dashboard'  && <Overview stats={stats} />}
          {tab === 'projects'   && <ProjectsTab reload={load} />}
          {tab === 'users'      && <UsersTab users={users} reload={load} />}
          {tab === 'placement'  && <PlacementTab reload={load} />}
          {tab === 'allocate'   && <ManualAllocate users={users} reload={load} />}
          {tab === 'history'    && <AllocationHistory />}
          {tab === 'alerts'     && <AlertsTab alerts={alerts} reload={load} />}
          {tab === 'metrics'    && <MetricsTab />}
          {tab === 'ml-metrics' && <MLMetricsTab />}
          {tab === 'profile'    && <ProfileTab user={user} onUpdate={refreshUser} />}
        </div>
      </main>
    </div>
  );
}

// ─── OVERVIEW ─────────────────────────────────
function Overview({ stats }) {
  if (!stats) return <p style={s.empty}>Loading stats…</p>;
  const st = stats.stats;
  return (
    <div>
      <div style={s.statsRow}>
        <StatCard label="Total Students"    value={st.total_students}     color="#16a34a" />
        <StatCard label="Total Supervisors" value={st.total_supervisors}  color="#15803d" />
        <StatCard label="Total Projects"    value={st.total_projects}     color="#22c55e" />
        <StatCard label="At Risk"           value={st.at_risk_count}      color="#dc2626" />
        <StatCard label="Pending Approval"  value={st.pending_approvals}  color="#f59e0b" />
        <StatCard label="Unassigned"        value={st.unassigned}         color="#14532d" />
        <StatCard label="Pending Users"     value={st.pending_users}      color="#4ade80" />
        <StatCard label="Completed"         value={st.completed_projects} color="#166534" />
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginTop: 4 }}>
        <div style={s.card}>
          <h3 style={s.cardTitle}>Department Distribution</h3>
          {(stats.dept_dist || []).length === 0 ? <p style={s.empty}>No data</p> :
            stats.dept_dist.map((d, i) => (
              <div key={i} style={{ display: 'flex', justifyContent: 'space-between', padding: '7px 0', borderBottom: '1px solid rgba(255,255,255,0.05)', fontSize: 13 }}>
                <span>{d.dept || '—'}</span>
                <strong>{d.count}</strong>
              </div>
            ))}
        </div>
        <div style={s.card}>
          <h3 style={s.cardTitle}>Risk Distribution</h3>
          {(stats.risk_dist || []).length === 0 ? <p style={s.empty}>No data</p> :
            stats.risk_dist.map((r, i) => {
              const colors = { on_track: '#16a34a', at_risk: '#f59e0b', critical: '#dc2626', unscanned: '#6b7280' };
              return (
                <div key={i} style={{ display: 'flex', justifyContent: 'space-between', padding: '7px 0', borderBottom: '1px solid rgba(255,255,255,0.05)', fontSize: 13 }}>
                  <span style={{ color: colors[r.risk_label] || '#9ca3af', fontWeight: 600, textTransform: 'capitalize' }}>{r.risk_label}</span>
                  <strong>{r.count}</strong>
                </div>
              );
            })}
        </div>
      </div>
    </div>
  );
}

// ─── USERS TAB ────────────────────────────────
function UsersTab({ users, reload }) {
  const [filter, setFilter] = useState('all');

  const toggleActive = async (userId, current) => {
    try {
      await api.patch(`/admin/users/${userId}/toggle-active`, { is_active: !current });
      toast.success(current ? 'User deactivated.' : 'User activated.');
      reload();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Action failed.');
    }
  };

  const filtered = filter === 'all' ? users
    : filter === 'pending' ? users.filter(u => !u.is_active)
    : users.filter(u => u.role === filter);

  return (
    <div style={s.card}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <h3 style={s.cardTitle}>User Management</h3>
        <div style={{ display: 'flex', gap: 8 }}>
          {['all','pending','student','supervisor','admin'].map(f => (
            <button key={f} style={filter === f ? { ...s.smBtn, background: '#16a34a', color: '#fff' } : s.smBtn} onClick={() => setFilter(f)}>
              {f.charAt(0).toUpperCase()+f.slice(1)}
            </button>
          ))}
        </div>
      </div>
      <table style={s.table}>
        <thead>
          <tr>
            {['Name','Username','Role','Dept','Supervisors','Active','Action'].map(h => <th key={h} style={s.th}>{h}</th>)}
          </tr>
        </thead>
        <tbody>
          {filtered.map(u => (
            <tr key={u.user_id} style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
              <td style={s.td}>{u.full_name}</td>
              <td style={s.td}><code style={{ fontSize: 12 }}>{u.username}</code></td>
              <td style={s.td}><RoleBadge role={u.role} /></td>
              <td style={{ ...s.td, fontSize: 12, color: '#9ca3af' }}>{u.stu_dept || u.sup_dept || '—'}</td>
              <td style={{ ...s.td, fontSize: 12 }}>
                {u.role === 'student' ? (
                  <div>
                    {u.supervisor_name ? (
                      <span style={{ color: '#4ade80', display: 'block', fontSize: 11 }}>Main: {u.supervisor_name}</span>
                    ) : null}
                    {u.co_supervisor_name ? (
                      <span style={{ color: '#38bdf8', display: 'block', fontSize: 11 }}>Co: {u.co_supervisor_name}</span>
                    ) : null}
                    {!u.supervisor_name && !u.co_supervisor_name && <span style={{ color: '#6b7280' }}>—</span>}
                  </div>
                ) : '—'}
              </td>
              <td style={s.td}>
                <span style={{ color: u.is_active ? '#16a34a' : '#dc2626', fontWeight: 700, fontSize: 12 }}>
                  {u.is_active ? 'Active' : 'Inactive'}
                </span>
              </td>
              <td style={s.td}>
                <button style={u.is_active ? { ...s.smBtn, color: '#dc2626' } : { ...s.smBtn, color: '#16a34a' }}
                  onClick={() => toggleActive(u.user_id, u.is_active)}>
                  {u.is_active ? 'Deactivate' : 'Activate'}
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      {filtered.length === 0 && <p style={s.empty}>No users in this filter.</p>}
    </div>
  );
}

// ─── PROJECTS TAB ────────────────────────────
function ProjectsTab({ reload }) {
  const [projects,  setProjects]  = useState([]);
  const [filter,    setFilter]    = useState('pending');
  const [busy,      setBusy]      = useState({});
  const [selected,  setSelected]  = useState(new Set());
  const [batchBusy, setBatchBusy] = useState(false);

  const fetchProjects = useCallback(async () => {
    try {
      const res = await api.get('/projects');
      setProjects(res.data.projects || []);
      setSelected(new Set());
    } catch {
      toast.error('Failed to load projects.');
    }
  }, []);

  useEffect(() => { fetchProjects(); }, [fetchProjects]);

  const updateStatus = async (projectId, status) => {
    setBusy(b => ({ ...b, [projectId]: status }));
    try {
      await api.patch(`/projects/${projectId}/status`, { status });
      toast.success(`Project ${status}.`);
      fetchProjects();
      reload();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Action failed.');
    } finally {
      setBusy(b => ({ ...b, [projectId]: null }));
    }
  };

  const batchUpdate = async (status) => {
    if (!selected.size) return;
    setBatchBusy(true);
    const ids = [...selected];
    let ok = 0;
    for (const id of ids) {
      try {
        await api.patch(`/projects/${id}/status`, { status });
        ok++;
      } catch { /* skip failed */ }
    }
    toast.success(`${ok} project(s) ${status}.`);
    setBatchBusy(false);
    fetchProjects();
    reload();
  };

  const runPlacement = async () => {
    setBatchBusy(true);
    try {
      const res = await api.post('/admin/placement-engine');
      toast.success(res.data.message || 'Placement complete.');
      fetchProjects();
      reload();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Placement failed.');
    } finally {
      setBatchBusy(false);
    }
  };

  const filters = ['pending', 'approved', 'in_progress', 'completed', 'rejected', 'all'];
  const displayed = filter === 'all' ? projects : projects.filter(p => p.status === filter);
  const allChecked = displayed.length > 0 && displayed.every(p => selected.has(p.project_id));

  const toggleAll = () => {
    if (allChecked) {
      setSelected(prev => { const n = new Set(prev); displayed.forEach(p => n.delete(p.project_id)); return n; });
    } else {
      setSelected(prev => { const n = new Set(prev); displayed.forEach(p => n.add(p.project_id)); return n; });
    }
  };

  const toggle = (id) => setSelected(prev => {
    const n = new Set(prev);
    n.has(id) ? n.delete(id) : n.add(id);
    return n;
  });

  const statusColor = {
    pending:     ['rgba(245,158,11,0.12)', '#f59e0b'],
    approved:    ['rgba(59,130,246,0.12)', '#60a5fa'],
    in_progress: ['rgba(22,163,74,0.12)',  '#4ade80'],
    completed:   ['rgba(168,85,247,0.12)', '#c084fc'],
    rejected:    ['rgba(239,68,68,0.12)',  '#f87171'],
  };

  const selCount = selected.size;

  return (
    <div style={s.card}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
        <h3 style={s.cardTitle}>Projects</h3>
        <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
          {filters.map(f => (
            <button key={f} onClick={() => { setFilter(f); setSelected(new Set()); }}
              style={filter === f ? { ...s.smBtn, background: '#16a34a', color: '#fff', borderColor: '#16a34a' } : s.smBtn}>
              {f.replace('_', ' ')}
            </button>
          ))}
        </div>
      </div>

      {selCount > 0 && (
        <div style={{ display: 'flex', gap: 8, alignItems: 'center', padding: '10px 14px', background: 'rgba(22,163,74,0.06)', border: '1px solid rgba(22,163,74,0.2)', borderRadius: 8, marginBottom: 14 }}>
          <span style={{ fontSize: 12, color: '#4ade80', fontWeight: 600 }}>{selCount} selected</span>
          <button disabled={batchBusy} onClick={() => batchUpdate('approved')}
            style={{ padding: '5px 14px', background: 'rgba(22,163,74,0.15)', color: '#4ade80', border: '1px solid rgba(22,163,74,0.3)', borderRadius: 6, fontSize: 12, fontWeight: 600, cursor: 'pointer' }}>
            Approve Selected
          </button>
          <button disabled={batchBusy} onClick={() => batchUpdate('rejected')}
            style={{ padding: '5px 14px', background: 'rgba(239,68,68,0.1)', color: '#f87171', border: '1px solid rgba(239,68,68,0.2)', borderRadius: 6, fontSize: 12, fontWeight: 600, cursor: 'pointer' }}>
            Reject Selected
          </button>
          <button disabled={batchBusy} onClick={runPlacement}
            style={{ padding: '5px 14px', background: 'rgba(59,130,246,0.1)', color: '#60a5fa', border: '1px solid rgba(59,130,246,0.2)', borderRadius: 6, fontSize: 12, fontWeight: 600, cursor: 'pointer' }}>
            {batchBusy ? 'Working…' : 'Run Placement'}
          </button>
          <button onClick={() => setSelected(new Set())}
            style={{ padding: '5px 10px', background: 'none', color: '#6b7280', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 6, fontSize: 12, cursor: 'pointer' }}>
            Clear
          </button>
        </div>
      )}

      {selCount === 0 && (
        <div style={{ marginBottom: 14 }}>
          <button disabled={batchBusy} onClick={runPlacement}
            style={{ ...s.smBtn, background: 'rgba(59,130,246,0.1)', color: '#60a5fa', borderColor: 'rgba(59,130,246,0.2)' }}>
            {batchBusy ? 'Running…' : 'Run AI Placement for All Approved'}
          </button>
        </div>
      )}

      {displayed.length === 0 ? (
        <p style={s.empty}>No {filter === 'all' ? '' : filter} projects.</p>
      ) : (
        <table style={s.table}>
          <thead>
            <tr>
              <th style={{ ...s.th, width: 32 }}>
                <input type="checkbox" checked={allChecked} onChange={toggleAll} style={{ cursor: 'pointer' }} />
              </th>
              {['Student', 'Matric No.', 'Title', 'Dept', 'Supervisor', 'Status', 'Submitted', 'Actions'].map(h => (
                <th key={h} style={s.th}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {displayed.map(p => {
              const [bg, color] = statusColor[p.status] || ['rgba(255,255,255,0.06)', '#9ca3af'];
              const isBusy = !!busy[p.project_id];
              const isChecked = selected.has(p.project_id);
              return (
                <tr key={p.project_id}
                  style={{ borderBottom: '1px solid rgba(255,255,255,0.05)', background: isChecked ? 'rgba(22,163,74,0.04)' : 'transparent' }}>
                  <td style={{ ...s.td, width: 32 }}>
                    <input type="checkbox" checked={isChecked} onChange={() => toggle(p.project_id)} style={{ cursor: 'pointer' }} />
                  </td>
                  <td style={s.td}>{p.student_name || '—'}</td>
                  <td style={{ ...s.td, fontSize: 11, color: '#9ca3af' }}>{p.matric_number || '—'}</td>
                  <td style={{ ...s.td, maxWidth: 160, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', fontSize: 12 }}
                      title={p.title}>{p.title}</td>
                  <td style={{ ...s.td, fontSize: 12, color: '#9ca3af' }}>{p.student_dept || '—'}</td>
                  <td style={{ ...s.td, fontSize: 12 }}>
                    <div>
                      {p.supervisor_name || <span style={{ color: '#4b5563' }}>Unassigned</span>}
                      {p.co_supervisor_name && (
                        <div style={{ fontSize: 11, color: '#38bdf8', marginTop: 2 }}>Co: {p.co_supervisor_name}</div>
                      )}
                    </div>
                  </td>
                  <td style={s.td}>
                    <span style={{ background: bg, color, padding: '2px 8px', borderRadius: 10, fontSize: 11, fontWeight: 600, textTransform: 'capitalize', whiteSpace: 'nowrap' }}>
                      {p.status.replace('_', ' ')}
                    </span>
                  </td>

                  <td style={{ ...s.td, fontSize: 11, color: '#6b7280', whiteSpace: 'nowrap' }}>
                    {p.submitted_at ? new Date(p.submitted_at).toLocaleDateString() : '—'}
                  </td>
                  <td style={{ ...s.td, whiteSpace: 'nowrap' }}>
                    {p.status === 'pending' && (
                      <div style={{ display: 'flex', gap: 5 }}>
                        <button disabled={isBusy} onClick={() => updateStatus(p.project_id, 'approved')}
                          style={{ padding: '3px 10px', background: 'rgba(22,163,74,0.12)', color: '#4ade80', border: '1px solid rgba(22,163,74,0.25)', borderRadius: 6, fontSize: 11, fontWeight: 600, cursor: isBusy ? 'not-allowed' : 'pointer', opacity: isBusy ? 0.5 : 1 }}>
                          {busy[p.project_id] === 'approved' ? '…' : 'Approve'}
                        </button>
                        <button disabled={isBusy} onClick={() => updateStatus(p.project_id, 'rejected')}
                          style={{ padding: '3px 10px', background: 'rgba(239,68,68,0.1)', color: '#f87171', border: '1px solid rgba(239,68,68,0.2)', borderRadius: 6, fontSize: 11, fontWeight: 600, cursor: isBusy ? 'not-allowed' : 'pointer', opacity: isBusy ? 0.5 : 1 }}>
                          {busy[p.project_id] === 'rejected' ? '…' : 'Reject'}
                        </button>
                      </div>
                    )}
                    {p.status === 'approved' && !p.supervisor_id && (
                      <span style={{ fontSize: 11, color: '#f59e0b' }}>Needs allocation</span>
                    )}
                    {p.status === 'approved' && p.supervisor_id && (
                      <span style={{ fontSize: 11, color: '#4ade80' }}>Allocated</span>
                    )}
                    {p.status === 'in_progress' && (
                      <button disabled={isBusy} onClick={() => updateStatus(p.project_id, 'completed')}
                        style={{ padding: '3px 10px', background: 'rgba(168,85,247,0.1)', color: '#c084fc', border: '1px solid rgba(168,85,247,0.2)', borderRadius: 6, fontSize: 11, fontWeight: 600, cursor: isBusy ? 'not-allowed' : 'pointer', opacity: isBusy ? 0.5 : 1 }}>
                        {busy[p.project_id] === 'completed' ? '…' : 'Complete'}
                      </button>
                    )}
                    {(p.status === 'completed' || p.status === 'rejected') && (
                      <span style={{ color: '#4b5563', fontSize: 12 }}>—</span>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      )}
    </div>
  );
}

// ─── PLACEMENT ENGINE ─────────────────────────
function PlacementTab({ reload }) {
  const [busy,    setBusy]    = useState(false);
  const [result,  setResult]  = useState(null);

  const run = async () => {
    setBusy(true);
    setResult(null);
    try {
      const res = await api.post('/admin/placement-engine');
      setResult(res.data);
      toast.success(res.data.message);
      reload();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Placement engine failed.');
    } finally {
      setBusy(false);
    }
  };

  return (
    <div style={s.card}>
      <h3 style={s.cardTitle}>AI Placement Engine</h3>
      <p style={{ fontSize: 13, color: '#9ca3af', marginBottom: 16 }}>
        Automatically matches unassigned approved projects to available supervisors using keyword cosine similarity and workload balancing.
      </p>
      <button style={busy ? { ...s.btn, opacity: 0.6 } : s.btn} onClick={run} disabled={busy}>
        {busy ? 'Running Engine…' : 'Run Placement Engine'}
      </button>

      {result && (
        <div style={{ marginTop: 20 }}>
          <div style={{ background: 'rgba(22,163,74,0.08)', border: '1px solid rgba(22,163,74,0.25)', borderRadius: 8, padding: '12px 16px', marginBottom: 14 }}>
            <p style={{ fontWeight: 700, color: '#4ade80' }}>{result.message}</p>
          </div>
          {result.allocations?.map((a, i) => (
            <div key={i} style={{ background: 'rgba(22,163,74,0.05)', borderRadius: 8, padding: '12px 14px', marginBottom: 8, borderLeft: '3px solid #16a34a' }}>
              <p style={{ fontWeight: 600, fontSize: 13, color: '#e5e7eb' }}>{a.student_name}</p>
              <p style={{ fontSize: 12, color: '#9ca3af' }}>{a.project_title}</p>
              <p style={{ fontSize: 12, marginTop: 4 }}>
                Assigned to <strong>{a.supervisor_name}</strong> — Match: <strong style={{ color: '#16a34a' }}>{(a.match_score * 100).toFixed(1)}%</strong>
              </p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// ─── MANUAL ALLOCATE ──────────────────────────
function ManualAllocate({ users, reload }) {
  const [projects,    setProjects]    = useState([]);
  const [supervisors, setSupervisors] = useState([]);
  const [form,        setForm]        = useState({ project_id: '', supervisor_id: '' });
  const [busy,        setBusy]        = useState(false);

  useEffect(() => {
    api.get('/projects').then(r => setProjects(r.data.projects || [])).catch(() => {});
    api.get('/admin/supervisors').then(r => setSupervisors(r.data.supervisors || [])).catch(() => {});
  }, []);

  const unassigned = projects.filter(p => p.status === 'approved' && !p.supervisor_id);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setBusy(true);
    try {
      await api.post('/admin/manual-allocate', {
        project_id:    Number(form.project_id),
        supervisor_id: Number(form.supervisor_id),
      });
      toast.success('Manual allocation successful!');
      setForm({ project_id: '', supervisor_id: '' });
      reload();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Allocation failed.');
    } finally {
      setBusy(false);
    }
  };

  return (
    <div style={s.card}>
      <h3 style={s.cardTitle}>Manual Student Allocation</h3>
      <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
        <FormField label="Select Unassigned Project *">
          <select style={s.input} value={form.project_id} onChange={e => setForm(p => ({...p, project_id: e.target.value}))} required>
            <option value="">Choose a project</option>
            {unassigned.map(p => <option key={p.project_id} value={p.project_id}>{p.student_name || 'Student'} — {p.title}</option>)}
          </select>
        </FormField>
        <FormField label="Assign to Supervisor *">
          <select style={s.input} value={form.supervisor_id} onChange={e => setForm(p => ({...p, supervisor_id: e.target.value}))} required>
            <option value="">Choose a supervisor</option>
            {supervisors.filter(s => s.current_load < s.max_load).map(sv => (
              <option key={sv.supervisor_id} value={sv.supervisor_id}>
                {sv.full_name} ({sv.current_load}/{sv.max_load} students)
              </option>
            ))}
          </select>
        </FormField>
        <button type="submit" style={busy ? { ...s.btn, opacity: 0.6 } : s.btn} disabled={busy}>
          {busy ? 'Allocating…' : 'Confirm Allocation'}
        </button>
      </form>
    </div>
  );
}

// ─── ALLOCATION HISTORY ───────────────────────
function AllocationHistory() {
  const [history, setHistory] = useState([]);

  useEffect(() => {
    api.get('/admin/allocation-history').then(r => setHistory(r.data.history || [])).catch(() => {});
  }, []);

  return (
    <div style={s.card}>
      <h3 style={s.cardTitle}>Allocation History</h3>
      {history.length === 0 ? <p style={s.empty}>No allocations yet.</p> :
        <table style={s.table}>
          <thead>
            <tr>
              {['Student','Matric No.','Project','Supervisor','Method','Score','Date'].map(h => <th key={h} style={s.th}>{h}</th>)}
            </tr>
          </thead>
          <tbody>
            {history.map((h, i) => (
              <tr key={i} style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                <td style={s.td}>{h.student_name}</td>
                <td style={{ ...s.td, fontSize: 11 }}>{h.matric_number}</td>
                <td style={{ ...s.td, maxWidth: 180, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', fontSize: 12 }}>{h.project_title || '—'}</td>
                <td style={s.td}>{h.supervisor_name}</td>
                <td style={s.td}><span style={{ background: h.allocation_method === 'ai_auto' ? 'rgba(22,163,74,0.15)' : 'rgba(59,130,246,0.15)', color: h.allocation_method === 'ai_auto' ? '#4ade80' : '#60a5fa', padding: '2px 8px', borderRadius: 10, fontSize: 11, fontWeight: 600 }}>{h.allocation_method}</span></td>
                <td style={s.td}>{h.match_score ? `${(h.match_score * 100).toFixed(1)}%` : '—'}</td>
                <td style={{ ...s.td, fontSize: 11, color: '#94a3b8' }}>{new Date(h.allocated_at).toLocaleDateString()}</td>
              </tr>
            ))}
          </tbody>
        </table>
      }
    </div>
  );
}

// ─── ALERTS TAB ───────────────────────────────
function AlertsTab({ alerts, reload }) {
  const markAll = async () => { try { await api.patch('/alerts/read-all'); reload(); } catch {} };
  return (
    <div style={s.card}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 14 }}>
        <h3 style={s.cardTitle}>Notifications</h3>
        {alerts.some(a => !a.is_read) && <button style={s.smBtn} onClick={markAll}>Mark all read</button>}
      </div>
      {alerts.length === 0 ? <p style={s.empty}>No notifications.</p> : alerts.map(a => (
        <div key={a.alert_id} style={{ padding: '12px 14px', background: a.is_read ? 'rgba(255,255,255,0.03)' : 'rgba(22,163,74,0.06)', borderRadius: 8, marginBottom: 8, border: '1px solid rgba(255,255,255,0.06)', opacity: a.is_read ? 0.65 : 1 }}>
          <p style={{ fontWeight: 600, fontSize: 13, color: '#e5e7eb' }}>{a.title}</p>
          <p style={{ fontSize: 12, color: '#9ca3af', marginTop: 2 }}>{a.message}</p>
          <p style={{ fontSize: 11, color: '#9ca3af', marginTop: 4 }}>{new Date(a.triggered_at).toLocaleString()}</p>
        </div>
      ))}
    </div>
  );
}

// ─── PROFILE TAB ──────────────────────────────
function ProfileTab({ user, onUpdate }) {
  const fileRef = useRef(null);
  const [uploading, setUploading] = useState(false);

  const instLogoRef = useRef(null);
  const [uploadingLogo, setUploadingLogo] = useState(false);

  const handleInstLogoFile = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploadingLogo(true);
    try {
      const reader = new FileReader();
      reader.onload = async (ev) => {
        try {
          const dataUrl = ev.target.result;
          const targetSlug = user?.institution_slug || user?.institution_code || 'kwasu';
          await api.post(`/institutions/${targetSlug}/update-logo`, { logo_url: dataUrl });
          toast.success(`Official logo for ${user?.institution_name || user?.institution_code || 'institution'} updated!`);
          onUpdate();
        } catch {
          toast.error('Failed to update institution logo.');
        } finally {
          setUploadingLogo(false);
        }
      };
      reader.readAsDataURL(file);
    } catch {
      toast.error('Could not process selected image.');
      setUploadingLogo(false);
    }
  };

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
            : <div style={{ width: 72, height: 72, background: '#14532d', borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 28, fontWeight: 700, color: '#fff', border: '2px solid #16a34a' }}>{user?.full_name?.[0]}</div>}
          <div style={{ position: 'absolute', bottom: 0, right: 0, background: '#16a34a', borderRadius: '50%', width: 22, height: 22, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <Camera size={11} color="#fff" />
          </div>
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
        {[['Username', user?.username], ['Email', user?.email], ['Phone', user?.phone || '—']].map(([label, val]) => (
          <div key={label} style={{ background: '#0f0f0f', borderRadius: 8, padding: '12px 14px' }}>
            <p style={s.label}>{label}</p>
            <p style={{ fontSize: 13, color: '#e5e7eb' }}>{val}</p>
          </div>
        ))}
      </div>

      {/* ── Official Institution Branding & Logo Section ── */}
      <div style={{ ...s.card, marginTop: 20 }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16 }}>
          <div>
            <h3 style={s.cardTitle}>Official Institution Logo &amp; Branding</h3>
            <p style={{ fontSize: 12, color: '#9ca3af', marginTop: 2 }}>
              Upload your university official emblem to update the portal logo and institutional colors across the platform.
            </p>
          </div>
          <span style={{ fontSize: 11, background: 'rgba(34,197,94,0.15)', color: '#22c55e', padding: '4px 10px', borderRadius: 20, fontWeight: 700 }}>
            {user?.institution_code || 'KWASU'} Active Node
          </span>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: 24, flexWrap: 'wrap', marginBottom: 18 }}>
          <div style={{ width: 84, height: 84, borderRadius: 14, background: 'rgba(255,255,255,0.04)', border: '1.5px solid rgba(255,255,255,0.1)', display: 'flex', alignItems: 'center', justifyContent: 'center', overflow: 'hidden', padding: 6 }}>
            {resolveLogoUrl(user?.institution_logo) ? (
              <img src={resolveLogoUrl(user.institution_logo)} alt="School Logo" style={{ width: '100%', height: '100%', objectFit: 'contain' }} />
            ) : (
              <Building2 size={36} color="#16a34a" />
            )}
          </div>
          <div style={{ flex: 1, minWidth: 240 }}>
            <h4 style={{ fontSize: 15, fontWeight: 700, color: '#fff', margin: 0 }}>
              {user?.institution_name || 'Kwara State University'}
            </h4>
            <p style={{ fontSize: 12, color: '#9ca3af', margin: '4px 0 10px' }}>
              Official Code: <b>{user?.institution_code || 'KWASU'}</b> • Slug: <code>{user?.institution_slug || 'kwasu'}</code>
            </p>
            <input
              ref={instLogoRef}
              type="file"
              accept="image/*"
              style={{ display: 'none' }}
              onChange={handleInstLogoFile}
            />
            <button
              style={{ ...s.smBtn, background: '#16a34a', color: '#fff', display: 'inline-flex', alignItems: 'center', gap: 6 }}
              onClick={() => instLogoRef.current?.click()}
              disabled={uploadingLogo}
            >
              <Upload size={13} />
              <span>{uploadingLogo ? 'Updating Official Logo…' : 'Upload & Update School Logo'}</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

// ─── ML METRICS TAB ───────────────────────────
function MLMetricsTab() {
  const [data,      setData]      = useState(null);
  const [loading,   setLoading]   = useState(true);
  const [error,     setError]     = useState(null);
  const [retraining, setRetraining] = useState(null);

  const load = () => {
    setLoading(true);
    setError(null);
    api.get('/admin/ml-metrics')
      .then(r => setData(r.data))
      .catch(err => setError(err.response?.data?.detail || 'ML service unavailable.'))
      .finally(() => setLoading(false));
  };

  useEffect(load, []);

  const retrain = async (model) => {
    setRetraining(model);
    try {
      await api.post(`/admin/ml-retrain/${model}`);
      toast.success(`${model} retrained successfully.`);
      load();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Retrain failed.');
    } finally {
      setRetraining(null);
    }
  };

  if (loading) return <p style={{ color: '#9ca3af', padding: 24 }}>Connecting to ML service…</p>;

  if (error) return (
    <div style={{ ...s.card, borderColor: 'rgba(239,68,68,0.3)' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 12 }}>
        <AlertTriangle size={28} color="#f87171" style={{ flexShrink: 0 }} />
        <div>
          <p style={{ fontSize: 15, fontWeight: 700, color: '#f87171' }}>ML Service Offline</p>
          <p style={{ fontSize: 13, color: '#9ca3af', marginTop: 2 }}>{error}</p>
        </div>
      </div>
      <p style={{ fontSize: 12, color: '#6b7280', marginBottom: 12 }}>
        Make sure the ML microservice is running on port 8001:
      </p>
      <code style={{ display: 'block', background: '#0a0a0a', border: '1px solid rgba(255,255,255,0.08)', borderRadius: 6, padding: '10px 14px', fontSize: 12, color: '#4ade80', fontFamily: 'monospace' }}>
        cd ml-service &amp;&amp; uvicorn main:app --port 8001 --reload
      </code>
      <button onClick={load} style={{ ...s.btn, marginTop: 14, fontSize: 12 }}>Retry Connection</button>
    </div>
  );

  const { models, algorithms, model_files, uptime } = data;
  const xgb = models?.xgboost_risk_predictor || {};
  const rf  = models?.random_forest_classifier || {};

  const pct = (v) => v != null ? `${(v * 100).toFixed(1)}%` : '—';
  const kb  = (v) => v != null ? `${v} KB` : 'Not saved';

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>

      {/* ── Service status bar ── */}
      <div style={{ display: 'flex', gap: 14, flexWrap: 'wrap' }}>
        {[
          { label: 'Service Status', value: 'Online', color: '#4ade80' },
          { label: 'Uptime',         value: uptime || '—',    color: '#60a5fa' },
          { label: 'XGBoost',        value: xgb.loaded ? 'Loaded' : 'Not Loaded', color: xgb.loaded ? '#4ade80' : '#f87171' },
          { label: 'Random Forest',  value: rf.loaded  ? 'Loaded' : 'Not Loaded', color: rf.loaded  ? '#4ade80' : '#f87171' },
        ].map(({ label, value, color }) => (
          <div key={label} style={{ background: '#141414', border: '1px solid rgba(255,255,255,0.07)', borderRadius: 10, padding: '12px 18px', flex: '1 1 160px' }}>
            <p style={{ fontSize: 10, color: '#6b7280', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.6px', marginBottom: 6 }}>{label}</p>
            <p style={{ fontSize: 15, fontWeight: 800, color }}>{value}</p>
          </div>
        ))}
        <div style={{ display: 'flex', alignItems: 'flex-end', paddingBottom: 2 }}>
          <button onClick={load} style={{ ...s.smBtn, fontSize: 12, padding: '7px 14px', display: 'inline-flex', alignItems: 'center', gap: 6 }}>
            <RefreshCw size={12} />
            <span>Refresh</span>
          </button>
        </div>
      </div>

      {/* ── Model cards ── */}
      {[
        { key: 'xgboost', info: xgb, id: 'xgboost' },
        { key: 'random_forest', info: rf, id: 'random_forest' },
      ].map(({ key, info, id }) => (
        <div key={key} style={s.card}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 16 }}>
            <div>
              <h3 style={{ ...s.cardTitle, marginBottom: 4 }}>{info.name || id}</h3>
              <p style={{ fontSize: 12, color: '#6b7280' }}>{info.type}</p>
              <p style={{ fontSize: 12, color: '#4b5563', marginTop: 2 }}>{info.task}</p>
            </div>
            <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
              <span style={{ padding: '3px 10px', borderRadius: 10, fontSize: 11, fontWeight: 700,
                background: info.loaded ? 'rgba(74,222,128,0.1)' : 'rgba(248,113,113,0.1)',
                color: info.loaded ? '#4ade80' : '#f87171',
                border: `1px solid ${info.loaded ? 'rgba(74,222,128,0.2)' : 'rgba(248,113,113,0.2)'}` }}>
                {info.loaded ? '● Loaded' : '○ Not Loaded'}
              </span>
              <button
                disabled={retraining === id}
                onClick={() => retrain(id)}
                style={{ ...s.smBtn, background: 'rgba(167,139,250,0.1)', color: '#a78bfa', borderColor: 'rgba(167,139,250,0.2)', display: 'inline-flex', alignItems: 'center', gap: 5 }}>
                {retraining === id ? 'Training…' : (
                  <>
                    <RefreshCw size={11} />
                    <span>Retrain</span>
                  </>
                )}
              </button>
            </div>
          </div>

          {/* Performance metrics */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(120px, 1fr))', gap: 10, marginBottom: 16 }}>
            {info.metrics?.accuracy != null && (
              <MetricChip label="Accuracy"     value={pct(info.metrics.accuracy)}     color="#4ade80" />
            )}
            {info.metrics?.f1 != null && (
              <MetricChip label="F1 Score"     value={pct(info.metrics.f1)}           color="#60a5fa" />
            )}
            {info.metrics?.oob_score != null && (
              <MetricChip label="OOB Score"    value={pct(info.metrics.oob_score)}    color="#a78bfa" />
            )}
            {info.metrics?.train_samples != null && (
              <MetricChip label="Train Samples" value={info.metrics.train_samples}    color="#f59e0b" />
            )}
            {info.metrics?.test_samples != null && (
              <MetricChip label="Test Samples"  value={info.metrics.test_samples}     color="#f59e0b" />
            )}
            {info.model_file_kb != null && (
              <MetricChip label="Model Size"    value={kb(info.model_file_kb)}        color="#9ca3af" />
            )}
            {info.metrics?.trained_at && (
              <MetricChip label="Last Trained"
                value={new Date(info.metrics.trained_at).toLocaleDateString()}
                color="#6b7280" />
            )}
          </div>

          {/* Feature importances (RF only) */}
          {info.feature_importances && Object.keys(info.feature_importances).length > 0 && (
            <div style={{ marginBottom: 16 }}>
              <p style={{ fontSize: 11, color: '#6b7280', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.5px', marginBottom: 10 }}>Feature Importances</p>
              {Object.entries(info.feature_importances).map(([feat, imp]) => (
                <div key={feat} style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 7 }}>
                  <span style={{ fontSize: 11, color: '#9ca3af', width: 220, flexShrink: 0, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                    {feat.replace(/_/g, ' ')}
                  </span>
                  <div style={{ flex: 1, background: 'rgba(255,255,255,0.06)', borderRadius: 4, height: 6, overflow: 'hidden' }}>
                    <div style={{ width: `${Math.round(imp * 100 / Object.values(info.feature_importances)[0] * 100)}%`, height: '100%', borderRadius: 4, background: '#a78bfa', transition: 'width 0.4s ease' }} />
                  </div>
                  <span style={{ fontSize: 11, color: '#6b7280', width: 46, textAlign: 'right', flexShrink: 0 }}>{(imp * 100).toFixed(1)}%</span>
                </div>
              ))}
            </div>
          )}

          {/* Hyperparams */}
          {info.hyperparams && Object.keys(info.hyperparams).length > 0 && (
            <details style={{ marginBottom: 12 }}>
              <summary style={{ fontSize: 12, color: '#6b7280', cursor: 'pointer', userSelect: 'none', fontWeight: 600 }}>
                Hyperparameters
              </summary>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, marginTop: 10 }}>
                {Object.entries(info.hyperparams).map(([k, v]) => v != null && (
                  <div key={k} style={{ background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.08)', borderRadius: 6, padding: '4px 10px', fontSize: 11 }}>
                    <span style={{ color: '#6b7280' }}>{k.replace(/_/g, ' ')}: </span>
                    <span style={{ color: '#e5e7eb', fontWeight: 600 }}>{String(v)}</span>
                  </div>
                ))}
              </div>
            </details>
          )}

          {/* Thresholds / classes */}
          {info.thresholds && (
            <div>
              <p style={{ fontSize: 11, color: '#6b7280', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.5px', marginBottom: 8 }}>Decision Thresholds</p>
              <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                {Object.entries(info.thresholds).map(([label, rule]) => {
                  const colors = { critical: '#f87171', at_risk: '#f59e0b', on_track: '#4ade80' };
                  return (
                    <div key={label} style={{ background: 'rgba(255,255,255,0.04)', border: `1px solid ${colors[label] || '#374151'}40`, borderRadius: 8, padding: '6px 12px' }}>
                      <span style={{ color: colors[label] || '#9ca3af', fontSize: 11, fontWeight: 700, textTransform: 'capitalize' }}>{label.replace(/_/g, ' ')}</span>
                      <span style={{ color: '#4b5563', fontSize: 11, marginLeft: 6 }}>{rule}</span>
                    </div>
                  );
                })}
              </div>
            </div>
          )}
          {info.classes && (
            <div>
              <p style={{ fontSize: 11, color: '#6b7280', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.5px', marginBottom: 8 }}>Output Classes</p>
              <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                {info.classes.map((cls, i) => {
                  const clsColors = ['#f87171', '#4ade80', '#60a5fa'];
                  return (
                    <span key={cls} style={{ background: `${clsColors[i]}15`, color: clsColors[i], border: `1px solid ${clsColors[i]}30`, borderRadius: 8, padding: '4px 12px', fontSize: 11, fontWeight: 600 }}>
                      {cls}
                    </span>
                  );
                })}
              </div>
            </div>
          )}
        </div>
      ))}

      {/* ── Algorithm descriptions ── */}
      <div style={s.card}>
        <h3 style={s.cardTitle}>Algorithm Descriptions</h3>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
          {Object.entries(algorithms || {}).map(([key, algo]) => (
            <div key={key} style={{ background: '#0f0f0f', borderRadius: 8, padding: '14px 16px', border: '1px solid rgba(255,255,255,0.06)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 8 }}>
                <p style={{ fontSize: 13, fontWeight: 700, color: '#e5e7eb' }}>{algo.name}</p>
              </div>
              <p style={{ fontSize: 12, color: '#9ca3af', lineHeight: 1.6, marginBottom: 10 }}>{algo.description}</p>

              {algo.weights && (
                <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginBottom: 8 }}>
                  {Object.entries(algo.weights).map(([wk, wv]) => (
                    <span key={wk} style={{ background: 'rgba(96,165,250,0.08)', color: '#60a5fa', border: '1px solid rgba(96,165,250,0.15)', borderRadius: 6, padding: '3px 10px', fontSize: 11 }}>
                      {wk.replace(/_/g, ' ')}: {(wv * 100).toFixed(0)}%
                    </span>
                  ))}
                </div>
              )}
              {algo.grade_boundaries && (
                <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                  {Object.entries(algo.grade_boundaries).map(([grade, min]) => {
                    const gColors = { A: '#4ade80', B: '#60a5fa', C: '#f59e0b', D: '#f97316', F: '#f87171' };
                    return (
                      <span key={grade} style={{ background: `${gColors[grade] || '#6b7280'}15`, color: gColors[grade] || '#9ca3af', border: `1px solid ${gColors[grade] || '#6b7280'}30`, borderRadius: 6, padding: '3px 10px', fontSize: 11, fontWeight: 700 }}>
                        {grade} ≥ {min}
                      </span>
                    );
                  })}
                </div>
              )}
              {algo.rubrics && (
                <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', marginTop: 6 }}>
                  {algo.rubrics.map(r => (
                    <span key={r} style={{ background: 'rgba(167,139,250,0.08)', color: '#a78bfa', border: '1px solid rgba(167,139,250,0.15)', borderRadius: 6, padding: '2px 9px', fontSize: 11 }}>{r}</span>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* ── Saved model files ── */}
      <div style={s.card}>
        <h3 style={s.cardTitle}>Model Artefacts</h3>
        {(model_files || []).length === 0
          ? <p style={s.empty}>No model files found.</p>
          : (
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 12 }}>
              <thead>
                <tr style={{ borderBottom: '1px solid rgba(255,255,255,0.07)' }}>
                  {['File', 'Size', 'Last Modified'].map(h => (
                    <th key={h} style={{ textAlign: 'left', padding: '6px 10px', color: '#6b7280', fontWeight: 600, fontSize: 11, textTransform: 'uppercase', letterSpacing: '0.5px' }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {(model_files || []).map((f, i) => (
                  <tr key={i} style={{ borderBottom: '1px solid rgba(255,255,255,0.04)' }}>
                    <td style={{ padding: '8px 10px', color: '#e5e7eb', fontFamily: 'monospace' }}>{f.file}</td>
                    <td style={{ padding: '8px 10px', color: '#9ca3af' }}>{f.size_kb} KB</td>
                    <td style={{ padding: '8px 10px', color: '#4b5563' }}>{new Date(f.modified).toLocaleString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
      </div>

    </div>
  );
}

function MetricChip({ label, value, color }) {
  return (
    <div style={{ background: '#0f0f0f', border: '1px solid rgba(255,255,255,0.06)', borderRadius: 8, padding: '10px 12px' }}>
      <p style={{ fontSize: 10, color: '#6b7280', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.5px', marginBottom: 4 }}>{label}</p>
      <p style={{ fontSize: 15, fontWeight: 800, color }}>{value}</p>
    </div>
  );
}

// ─── METRICS TAB ──────────────────────────────
function MetricsTab() {
  const [data,    setData]    = useState(null);
  const [loading, setLoading] = useState(true);
  const [error,   setError]   = useState(null);

  useEffect(() => {
    api.get('/admin/metrics')
      .then(r => setData(r.data))
      .catch(() => setError('Failed to load metrics.'))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <p style={{ color: '#9ca3af', padding: 24 }}>Loading metrics…</p>;
  if (error)   return <p style={{ color: '#f87171', padding: 24 }}>{error}</p>;

  const { kpis, status_dist, weekly_subs, chapter_dist, turnaround, workload, login_activity, alert_dist, sub_status_dist } = data;

  const STATUS_COLORS = { pending: '#f59e0b', approved: '#60a5fa', in_progress: '#a78bfa', completed: '#4ade80', rejected: '#f87171' };
  const SEVERITY_COLORS = { info: '#60a5fa', warning: '#f59e0b', critical: '#f87171', success: '#4ade80' };
  const SUB_STATUS_COLORS = { submitted: '#f59e0b', reviewed: '#60a5fa', revision_needed: '#f87171', approved: '#4ade80' };

  const maxWeekly    = Math.max(...(weekly_subs.map(w => w.cnt)), 1);
  const maxLogin     = Math.max(...(login_activity.map(l => l.cnt)), 1);
  const totalStatus  = status_dist.reduce((a, r) => a + r.cnt, 0) || 1;
  const totalAlerts  = alert_dist.reduce((a, r) => a + r.cnt, 0) || 1;
  const totalSubSt   = sub_status_dist.reduce((a, r) => a + r.cnt, 0) || 1;
  const maxTurnaround = Math.max(...(turnaround.map(t => t.avg_days || 0)), 1);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>

      {/* ── KPI row ── */}
      <div style={s.statsRow}>
        <KpiCard label="Total Submissions"      value={kpis.total_submissions}    color="#60a5fa" />
        <KpiCard label="Avg Chapters / Project" value={kpis.avg_chapters_done}    color="#a78bfa" />
        <KpiCard label="Milestones Completed"   value={kpis.ms_completed}         color="#4ade80" />
        <KpiCard label="Milestones Overdue"     value={kpis.ms_overdue}           color="#f87171" />
        <KpiCard label="Milestone Completion"   value={`${kpis.ms_completion_pct}%`} color="#22c55e" />
      </div>

      {/* ── Row 1: project status + submission status ── */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
        <div style={s.card}>
          <h3 style={s.cardTitle}>Project Status Distribution</h3>
          {status_dist.map((r, i) => (
            <BarRow key={i}
              label={r.status?.replace(/_/g, ' ')}
              value={r.cnt}
              max={totalStatus}
              pct={Math.round(r.cnt / totalStatus * 100)}
              color={STATUS_COLORS[r.status] || '#6b7280'}
              showCount />
          ))}
        </div>
        <div style={s.card}>
          <h3 style={s.cardTitle}>Submission Review Status</h3>
          {sub_status_dist.map((r, i) => (
            <BarRow key={i}
              label={r.status?.replace(/_/g, ' ')}
              value={r.cnt}
              max={totalSubSt}
              pct={Math.round(r.cnt / totalSubSt * 100)}
              color={SUB_STATUS_COLORS[r.status] || '#6b7280'}
              showCount />
          ))}
          {sub_status_dist.length === 0 && <p style={s.empty}>No submissions yet.</p>}
        </div>
      </div>

      {/* ── Row 2: weekly submissions + login activity ── */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
        <div style={s.card}>
          <h3 style={s.cardTitle}>Weekly Submissions (last 8 weeks)</h3>
          {weekly_subs.length === 0
            ? <p style={s.empty}>No submissions in this period.</p>
            : weekly_subs.map((w, i) => (
              <BarRow key={i}
                label={w.week}
                value={w.cnt}
                max={maxWeekly}
                pct={Math.round(w.cnt / maxWeekly * 100)}
                color="#60a5fa"
                showCount />
            ))}
        </div>
        <div style={s.card}>
          <h3 style={s.cardTitle}>Login Activity (last 7 days)</h3>
          {login_activity.length === 0
            ? <p style={s.empty}>No login data in this period.</p>
            : login_activity.map((l, i) => (
              <BarRow key={i}
                label={l.day}
                value={l.cnt}
                max={maxLogin}
                pct={Math.round(l.cnt / maxLogin * 100)}
                color="#a78bfa"
                showCount />
            ))}
        </div>
      </div>

      {/* ── Row 3: chapter breakdown + alert severity ── */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
        <div style={s.card}>
          <h3 style={s.cardTitle}>Submissions by Chapter</h3>
          {chapter_dist.length === 0
            ? <p style={s.empty}>No data.</p>
            : chapter_dist.map((c, i) => {
              const total = chapter_dist.reduce((a, x) => a + x.cnt, 0) || 1;
              return (
                <BarRow key={i}
                  label={c.chapter?.replace('chapter', 'Chapter ')?.replace('proposal', 'Proposal') || '—'}
                  value={c.cnt}
                  max={total}
                  pct={Math.round(c.cnt / total * 100)}
                  color="#22c55e"
                  showCount />
              );
            })}
        </div>
        <div style={s.card}>
          <h3 style={s.cardTitle}>Alert Severity Breakdown</h3>
          {alert_dist.map((a, i) => (
            <BarRow key={i}
              label={a.severity}
              value={a.cnt}
              max={totalAlerts}
              pct={Math.round(a.cnt / totalAlerts * 100)}
              color={SEVERITY_COLORS[a.severity] || '#6b7280'}
              showCount />
          ))}
          {alert_dist.length === 0 && <p style={s.empty}>No alerts yet.</p>}
        </div>
      </div>

      {/* ── Supervisor workload ── */}
      <div style={s.card}>
        <h3 style={s.cardTitle}>Supervisor Workload</h3>
        {workload.length === 0
          ? <p style={s.empty}>No supervisors found.</p>
          : workload.map((w, i) => (
            <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 10 }}>
              <span style={{ fontSize: 12, color: '#9ca3af', width: 180, flexShrink: 0, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{w.name}</span>
              <div style={{ flex: 1, background: 'rgba(255,255,255,0.06)', borderRadius: 4, height: 8, overflow: 'hidden' }}>
                <div style={{ width: `${w.pct}%`, height: '100%', borderRadius: 4,
                  background: w.pct >= 90 ? '#f87171' : w.pct >= 60 ? '#f59e0b' : '#4ade80',
                  transition: 'width 0.4s ease' }} />
              </div>
              <span style={{ fontSize: 11, color: '#6b7280', flexShrink: 0, width: 60, textAlign: 'right' }}>
                {w.current_load}/{w.max_load} ({w.pct}%)
              </span>
            </div>
          ))}
      </div>

      {/* ── Review turnaround ── */}
      <div style={s.card}>
        <h3 style={s.cardTitle}>Avg Review Turnaround per Supervisor (days)</h3>
        {turnaround.length === 0
          ? <p style={s.empty}>No reviews completed yet.</p>
          : turnaround.map((t, i) => (
            <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 10 }}>
              <span style={{ fontSize: 12, color: '#9ca3af', width: 180, flexShrink: 0, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{t.supervisor_name}</span>
              <div style={{ flex: 1, background: 'rgba(255,255,255,0.06)', borderRadius: 4, height: 8, overflow: 'hidden' }}>
                <div style={{ width: `${Math.round((t.avg_days || 0) / maxTurnaround * 100)}%`, height: '100%', borderRadius: 4,
                  background: (t.avg_days || 0) <= 3 ? '#4ade80' : (t.avg_days || 0) <= 7 ? '#f59e0b' : '#f87171',
                  transition: 'width 0.4s ease' }} />
              </div>
              <span style={{ fontSize: 11, color: '#6b7280', flexShrink: 0, width: 80, textAlign: 'right' }}>
                {t.avg_days ?? '—'} days · {t.total_reviewed} reviewed
              </span>
            </div>
          ))}
      </div>

      {/* ── Milestone progress ring ── */}
      <div style={s.card}>
        <h3 style={s.cardTitle}>Milestone Health</h3>
        <div style={{ display: 'flex', gap: 24, flexWrap: 'wrap' }}>
          {[
            { label: 'Completed', value: kpis.ms_completed, color: '#4ade80' },
            { label: 'Overdue',   value: kpis.ms_overdue,   color: '#f87171' },
            { label: 'Pending',   value: kpis.ms_pending,   color: '#f59e0b' },
          ].map(({ label, value, color }) => (
            <div key={label} style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
              <div style={{ width: 54, height: 54, borderRadius: '50%', background: `conic-gradient(${color} ${Math.round(value / Math.max(kpis.ms_total,1) * 360)}deg, rgba(255,255,255,0.06) 0deg)`, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <div style={{ width: 36, height: 36, borderRadius: '50%', background: '#141414', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 11, fontWeight: 700, color }}>
                  {Math.round(value / Math.max(kpis.ms_total,1) * 100)}%
                </div>
              </div>
              <div>
                <p style={{ fontSize: 13, fontWeight: 700, color }}>{value}</p>
                <p style={{ fontSize: 11, color: '#6b7280' }}>{label}</p>
              </div>
            </div>
          ))}
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <div style={{ width: 54, height: 54, borderRadius: '50%', background: 'rgba(255,255,255,0.06)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 13, fontWeight: 700, color: '#9ca3af' }}>
              {kpis.ms_total}
            </div>
            <div>
              <p style={{ fontSize: 13, fontWeight: 700, color: '#9ca3af' }}>{kpis.ms_total}</p>
              <p style={{ fontSize: 11, color: '#6b7280' }}>Total</p>
            </div>
          </div>
        </div>
      </div>

    </div>
  );
}

function KpiCard({ label, value, color }) {
  return (
    <div style={{ background: '#141414', borderRadius: 10, padding: '16px 18px', border: '1px solid rgba(255,255,255,0.07)', borderTop: `3px solid ${color}`, borderTopWidth: 3 }}>
      <p style={{ fontSize: 10, color: '#6b7280', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.6px', marginBottom: 8 }}>{label}</p>
      <p style={{ fontSize: 22, fontWeight: 800, color }}>{value ?? '—'}</p>
    </div>
  );
}

function BarRow({ label, value, pct, color, showCount }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 10 }}>
      <span style={{ fontSize: 12, color: '#9ca3af', width: 130, flexShrink: 0, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', textTransform: 'capitalize' }}>{label}</span>
      <div style={{ flex: 1, background: 'rgba(255,255,255,0.06)', borderRadius: 4, height: 8, overflow: 'hidden' }}>
        <div style={{ width: `${pct}%`, height: '100%', borderRadius: 4, background: color, transition: 'width 0.4s ease' }} />
      </div>
      {showCount && <span style={{ fontSize: 11, color: '#6b7280', flexShrink: 0, width: 40, textAlign: 'right' }}>{value} ({pct}%)</span>}
    </div>
  );
}

// ─── SHARED ───────────────────────────────────
function Sidebar({ role, active, onTab, onLogout, unread, user }) {
  const tabs = [
    { id: 'dashboard', label: 'Dashboard',         Icon: LayoutDashboard },
    { id: 'projects',  label: 'Projects',          Icon: FolderOpen },
    { id: 'users',     label: 'User Management',   Icon: UserCog },
    { id: 'placement', label: 'AI Placement',      Icon: Zap },
    { id: 'allocate',  label: 'Manual Allocate',   Icon: Shuffle },
    { id: 'history',   label: 'History',           Icon: History },
    { id: 'alerts',    label: `Alerts${unread > 0 ? ` (${unread})` : ''}`, Icon: Bell },
    { id: 'metrics',    label: 'Performance',          Icon: BarChart2 },
    { id: 'ml-metrics', label: 'ML Engine',           Icon: Cpu },
  ];
  const logo = resolveLogoUrl(user?.institution_logo);
  const isKwasu = !user?.institution_slug || user?.institution_slug === 'kwasu' || user?.institution_code === 'KWASU';
  const instCode = user?.institution_code || 'KWASU';
  const primaryColor = user?.institution_primary_color || '#22c55e';

  return (
    <aside style={s.sidebar}>
      <div style={s.sideHeader}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 8 }}>
          {logo ? (
            <img
              src={logo}
              alt={instCode}
              style={s.logoImg}
              onError={(e) => {
                if (isKwasu) {
                  e.target.src = '/kwasu.png';
                } else {
                  e.target.style.display = 'none';
                  const fb = document.getElementById('admin-sidebar-fallback');
                  if (fb) fb.style.display = 'flex';
                }
              }}
            />
          ) : isKwasu ? (
            <img src="/kwasu.png" alt="KWASU" style={s.logoImg} />
          ) : null}
          <div
            id="admin-sidebar-fallback"
            style={{
              display: (logo || isKwasu) ? 'none' : 'flex',
              width: 38,
              height: 38,
              borderRadius: 8,
              background: `${primaryColor}22`,
              border: `1.5px solid ${primaryColor}55`,
              color: primaryColor,
              alignItems: 'center',
              justifyContent: 'center',
              fontWeight: 800,
              fontSize: 13,
              flexShrink: 0
            }}
          >
            {instCode.slice(0, 3)}
          </div>
          <div>
            <div style={{ color: 'var(--text-primary, #ffffff)', fontWeight: 800, fontSize: 16, letterSpacing: '0.5px', lineHeight: 1.2 }}>
              {instCode}
            </div>
            <div style={{ color: primaryColor, fontSize: 10, fontWeight: 700, letterSpacing: '1px' }}>
              SPSEMS
            </div>
          </div>
        </div>
        <p style={s.sideRole}>ADMINISTRATOR</p>
      </div>
      <nav style={{ flex: 1, paddingTop: 8 }}>
        {tabs.map(({ id, label, Icon }) => (
          <button key={id} style={active === id ? { ...s.navBtn, ...s.navActive } : s.navBtn} onClick={() => onTab(id)}>
            <Icon size={15} style={{ flexShrink: 0 }} />
            <span>{label}</span>
          </button>
        ))}
      </nav>
      <div style={{ padding: '8px 12px 10px', borderTop: '1px solid rgba(255,255,255,0.06)', marginTop: 8 }}>
        <p style={{ fontSize: 10, fontWeight: 700, letterSpacing: '0.6px', color: '#6b7280', textTransform: 'uppercase', marginBottom: 6 }}>
          Campus Portals
        </p>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
          <a
            href={`/portal/${user?.institution_slug || 'kwapoly'}/siwes`}
            style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 11, color: '#9ca3af', textDecoration: 'none', padding: '4px 6px', borderRadius: 4, transition: 'color 0.2s' }}
          >
            <Briefcase size={12} color="#3b82f6" />
            <span>SIWES Portal</span>
          </a>
          <a
            href={`/portal/${user?.institution_slug || 'kwapoly'}/hostel`}
            style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 11, color: '#9ca3af', textDecoration: 'none', padding: '4px 6px', borderRadius: 4, transition: 'color 0.2s' }}
          >
            <Home size={12} color="#f59e0b" />
            <span>Hostel Portal</span>
          </a>
          <a
            href={`/login/${user?.institution_slug || 'kwapoly'}`}
            style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 11, color: '#9ca3af', textDecoration: 'none', padding: '4px 6px', borderRadius: 4, transition: 'color 0.2s' }}
          >
            <Layers size={12} color={primaryColor} />
            <span>Portals Gateway</span>
          </a>
        </div>
      </div>
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
      <h2 style={s.topTitle}>{title}</h2>
      <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
        <ThemeToggle />
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, cursor: 'pointer' }} onClick={onProfile} title="View profile">
          {user?.avatar_url
            ? <img src={user.avatar_url} alt="avatar" style={{ width: 32, height: 32, borderRadius: '50%', objectFit: 'cover', border: '2px solid #16a34a' }} />
            : <div style={s.avatar}>{user?.full_name?.[0] || 'A'}</div>}
          <span style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-primary, #e5e7eb)' }}>{user?.full_name}</span>
        </div>
      </div>
    </div>
  );
}

function StatCard({ label, value, color }) {
  return (
    <div style={{ background: 'var(--bg-card, #141414)', borderRadius: 10, padding: '16px 18px', borderTop: `3px solid ${color}`, border: '1px solid var(--border-subtle, rgba(255,255,255,0.07))', borderTopWidth: 3 }}>
      <p style={{ fontSize: 10, color: 'var(--text-dim, #6b7280)', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.6px', marginBottom: 8 }}>{label}</p>
      <p style={{ fontSize: 20, fontWeight: 800, color }}>{value}</p>
    </div>
  );
}

function RoleBadge({ role }) {
  const map = { admin: ['rgba(239,68,68,0.12)','#f87171'], supervisor: ['rgba(22,163,74,0.12)','#22c55e'], student: ['rgba(59,130,246,0.12)','#60a5fa'] };
  const [bg, text] = map[role] || ['rgba(255,255,255,0.08)','#9ca3af'];
  return <span style={{ background: bg, color: text, padding: '2px 8px', borderRadius: 10, fontSize: 11, fontWeight: 600, textTransform: 'capitalize' }}>{role}</span>;
}

function FormField({ label, children }) {
  return <div><label style={s.label}>{label}</label>{children}</div>;
}

function Loader() {
  return <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100vh', fontSize: 15, color: '#16a34a', background: 'var(--bg-app, #0a0a0a)', fontWeight: 500, letterSpacing: '0.3px' }}>Loading...</div>;
}

const TAB_TITLES = { dashboard: 'Admin Dashboard', projects: 'Project Approvals', users: 'User Management', placement: 'AI Placement Engine', allocate: 'Manual Allocation', history: 'Allocation History', alerts: 'Notifications', metrics: 'System Performance Metrics', 'ml-metrics': 'ML Engine Diagnostics', profile: 'My Profile' };

const s = {
  layout:     { display: 'flex', minHeight: '100vh', background: 'var(--bg-app, #0a0a0a)' },
  sidebar:    { width: 236, background: 'var(--bg-sidebar, #080808)', display: 'flex', flexDirection: 'column', padding: '24px 0', borderRight: '1px solid var(--border-sidebar, rgba(255,255,255,0.06))' },
  sideHeader: { padding: '0 20px 20px', borderBottom: '1px solid var(--border-subtle, rgba(255,255,255,0.07))' },
  logoImg:    { height: 38, width: 'auto', display: 'block', objectFit: 'contain' },
  sideRole:   { color: 'var(--text-dim, #6b7280)', fontSize: 10, letterSpacing: '1.5px', textTransform: 'uppercase', fontWeight: 600 },
  navBtn:     { display: 'flex', alignItems: 'center', gap: 10, width: '100%', padding: '10px 20px', background: 'none', border: 'none', borderLeft: '3px solid transparent', color: 'var(--text-dim, #6b7280)', textAlign: 'left', fontSize: 13, cursor: 'pointer', fontWeight: 500 },
  navActive:  { background: 'rgba(22,163,74,0.08)', color: '#22c55e', borderLeftColor: '#16a34a', fontWeight: 600 },
  logoutBtn:  { width: '100%', padding: '10px 12px', background: 'rgba(239,68,68,0.08)', border: '1px solid rgba(239,68,68,0.15)', borderRadius: 7, color: '#f87171', cursor: 'pointer', fontSize: 12, fontWeight: 600, display: 'flex', alignItems: 'center', gap: 8 },
  main:       { flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' },
  topbar:     { background: 'var(--bg-topbar, #0f0f0f)', padding: '14px 24px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid var(--border-subtle, rgba(255,255,255,0.07))' },
  topTitle:   { fontSize: 17, fontWeight: 700, color: 'var(--text-primary, #ffffff)', letterSpacing: '-0.3px' },
  avatar:     { width: 32, height: 32, background: '#14532d', borderRadius: '50%', color: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 700, fontSize: 13 },
  content:    { flex: 1, padding: 24, overflowY: 'auto', background: 'var(--bg-app, #0a0a0a)' },
  statsRow:   { display: 'grid', gridTemplateColumns: 'repeat(4,1fr)', gap: 14, marginBottom: 20 },
  card:       { background: 'var(--bg-card, #141414)', borderRadius: 12, padding: '20px 22px', border: '1px solid var(--border-subtle, rgba(255,255,255,0.07))' },
  cardTitle:  { fontSize: 15, fontWeight: 700, color: 'var(--text-primary, #ffffff)', marginBottom: 14, letterSpacing: '-0.2px' },
  table:      { width: '100%', borderCollapse: 'collapse' },
  th:         { textAlign: 'left', fontSize: 10, fontWeight: 700, color: 'var(--table-th-color, #6b7280)', textTransform: 'uppercase', padding: '8px 10px', letterSpacing: '0.5px', background: 'var(--table-th-bg, #0f0f0f)' },
  td:         { padding: '10px', fontSize: 13, color: 'var(--text-secondary, #e5e7eb)' },
  label:      { display: 'block', fontSize: 11, fontWeight: 600, color: 'var(--text-dim, #6b7280)', marginBottom: 5, letterSpacing: '0.3px', textTransform: 'uppercase' },
  input:      { width: '100%', padding: '9px 11px', background: 'var(--bg-input, #0f0f0f)', border: '1px solid var(--border-input, rgba(255,255,255,0.1))', borderRadius: 7, fontSize: 13, outline: 'none', color: 'var(--text-primary, #fff)', boxSizing: 'border-box' },
  btn:        { padding: '11px 20px', background: '#16a34a', color: '#fff', border: 'none', borderRadius: 8, fontWeight: 600, fontSize: 13, cursor: 'pointer' },
  smBtn:      { padding: '5px 12px', background: 'rgba(22,163,74,0.1)', color: '#22c55e', border: '1px solid rgba(22,163,74,0.2)', borderRadius: 6, fontSize: 12, fontWeight: 600, cursor: 'pointer' },
  empty:      { color: 'var(--text-dim, #6b7280)', fontSize: 13, textAlign: 'center', padding: '32px 0' },
};
