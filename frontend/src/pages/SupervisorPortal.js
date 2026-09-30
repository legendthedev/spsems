import React, { useState, useEffect, useCallback, useRef } from 'react';
import { useAuth } from '../context/AuthContext';
import api from '../services/api';
import toast from 'react-hot-toast';
import { LayoutDashboard, Users, Eye, Award, Bell, MessageSquare, LogOut } from 'lucide-react';
import ThemeToggle from '../components/ThemeToggle';

export default function SupervisorPortal() {
  const { user, logout, refreshUser } = useAuth();
  const [tab,       setTab]       = useState('dashboard');
  const [dashboard, setDashboard] = useState(null);
  const [alerts,    setAlerts]    = useState([]);
  const [loading,   setLoading]   = useState(true);

  const load = useCallback(async () => {
    try {
      const [dRes, aRes] = await Promise.all([
        api.get('/supervisor/dashboard'),
        api.get('/alerts'),
      ]);
      setDashboard(dRes.data);
      setAlerts(aRes.data.alerts || []);
    } catch {
      toast.error('Failed to load dashboard.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  if (loading) return <Loader />;
  const unread = alerts.filter(a => !a.is_read).length;

  return (
    <div style={s.layout}>
      <Sidebar active={tab} onTab={setTab} onLogout={logout} unread={unread} role={user?.role} />
      <main style={s.main}>
        <TopBar title={TAB_TITLES[tab] || 'Supervisor Portal'} user={user} onProfile={() => setTab('profile')} />
        <div style={s.content}>
          {tab === 'dashboard'  && <Overview data={dashboard} />}
          {tab === 'students'   && <StudentsTab students={dashboard?.students || []} reload={load} />}
          {tab === 'review'     && <ReviewTab  students={dashboard?.students || []} pendingReviews={dashboard?.pendingReviews || []} reload={load} />}
          {tab === 'evaluate'   && <EvaluateTab students={dashboard?.students || []} reload={load} />}
          {tab === 'alerts'     && <AlertsTab  alerts={alerts} reload={load} />}
          {tab === 'messages'   && <MessagesTab user={user} students={dashboard?.students || []} />}
          {tab === 'profile'    && <ProfileTab user={user} onUpdate={refreshUser} />}
        </div>
      </main>
    </div>
  );
}

// ─── OVERVIEW ─────────────────────────────────
function Overview({ data }) {
  if (!data) return <p style={s.empty}>No data.</p>;
  const risk_color = { on_track: '#16a34a', at_risk: '#f59e0b', critical: '#dc2626' };
  return (
    <div>
      <div style={s.statsRow}>
        <StatCard label="Assigned Students" value={data.supervisor?.current_load ?? 0}     color="#16a34a" />
        <StatCard label="Max Capacity"       value={data.supervisor?.max_load ?? 5}         color="#15803d" />
        <StatCard label="Pending Reviews"    value={data.students?.filter(p => p.status === 'in_review').length ?? 0} color="#22c55e" />
        <StatCard label="Completed"          value={data.students?.filter(p => p.status === 'completed').length ?? 0} color="#14532d" />
      </div>

      {data.students?.length > 0 ? (
        <div style={s.card}>
          <h3 style={s.cardTitle}>My Students</h3>
          <table style={s.table}>
            <thead>
              <tr>
                {['Student','Title','Chapter','Risk','Status'].map(h => <th key={h} style={s.th}>{h}</th>)}
              </tr>
            </thead>
            <tbody>
              {data.students.map(p => (
                <tr key={p.project_id} style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                  <td style={s.td}>
                    <div>{p.student_name}</div>
                    {p.supervisor_role && (
                      <span style={{
                        fontSize: 10,
                        padding: '1px 6px',
                        borderRadius: 8,
                        fontWeight: 600,
                        display: 'inline-block',
                        marginTop: 2,
                        background: p.supervisor_role === 'Co-Supervisor' ? 'rgba(14,165,233,0.15)' : 'rgba(34,197,94,0.15)',
                        color: p.supervisor_role === 'Co-Supervisor' ? '#38bdf8' : '#4ade80',
                      }}>
                        {p.supervisor_role}
                      </span>
                    )}
                  </td>
                  <td style={{ ...s.td, maxWidth: 200, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{p.title}</td>
                  <td style={s.td}>Ch. {p.current_chapter}/5</td>
                  <td style={{ ...s.td, color: risk_color[p.risk_label] || '#6b7280', fontWeight: 600 }}>{p.risk_label || '—'}</td>
                  <td style={s.td}><StatusBadge status={p.status} /></td>
                </tr>

              ))}
            </tbody>
          </table>
        </div>
      ) : <div style={s.card}><p style={s.empty}>No students assigned yet.</p></div>}
    </div>
  );
}

// ─── FILE HELPERS (shared by StudentsTab + ReviewTab) ─────
async function fetchFileBlob(docId) {
  const res = await api.get(`/supervisor/submissions/${docId}/file`, { responseType: 'blob' });
  return res.data;
}

function triggerDownload(blob, fileName) {
  const url = URL.createObjectURL(blob);
  const a   = document.createElement('a');
  a.href     = url;
  a.download = fileName || 'document';
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  setTimeout(() => URL.revokeObjectURL(url), 5000);
}

function isPdf(fileName) {
  return (fileName || '').toLowerCase().endsWith('.pdf');
}

// ─── STUDENTS TAB ─────────────────────────────
function StudentsTab({ students, reload }) {
  const [subsOpen,    setSubsOpen]    = useState(null);
  const [subsData,    setSubsData]    = useState({});
  const [blobUrls,    setBlobUrls]    = useState({});
  const [viewingFile, setViewingFile] = useState(null);
  const [loadingDoc,  setLoadingDoc]  = useState(null);

  const loadSubs = async (projectId) => {
    if (subsOpen === projectId) {
      setSubsOpen(null);
      setViewingFile(null);
      return;
    }
    try {
      const res = await api.get(`/supervisor/projects/${projectId}/submissions`);
      setSubsData(prev => ({ ...prev, [projectId]: res.data.submissions || [] }));
      setSubsOpen(projectId);
      setViewingFile(null);
    } catch {
      toast.error('Could not load submissions.');
    }
  };

  const handleView = async (sub) => {
    if (viewingFile === sub.doc_id) { setViewingFile(null); return; }
    if (blobUrls[sub.doc_id]) { setViewingFile(sub.doc_id); return; }
    setLoadingDoc(sub.doc_id);
    try {
      const blob   = await fetchFileBlob(sub.doc_id);
      const mtype  = isPdf(sub.file_name) ? 'application/pdf' : blob.type;
      const blobUrl = URL.createObjectURL(new Blob([blob], { type: mtype }));
      setBlobUrls(prev => ({ ...prev, [sub.doc_id]: blobUrl }));
      setViewingFile(sub.doc_id);
    } catch {
      toast.error('Could not load file.');
    } finally {
      setLoadingDoc(null);
    }
  };

  const handleDownload = async (sub) => {
    setLoadingDoc(sub.doc_id + '_dl');
    try {
      const blob = blobUrls[sub.doc_id]
        ? await fetch(blobUrls[sub.doc_id]).then(r => r.blob())
        : await fetchFileBlob(sub.doc_id);
      triggerDownload(blob, sub.file_name);
    } catch {
      toast.error('Download failed.');
    } finally {
      setLoadingDoc(null);
    }
  };

  const statusBadge = {
    submitted:       ['rgba(245,158,11,0.12)', '#f59e0b'],
    reviewed:        ['rgba(96,165,250,0.12)',  '#60a5fa'],
    revision_needed: ['rgba(239,68,68,0.1)',    '#f87171'],
    approved:        ['rgba(22,163,74,0.12)',   '#4ade80'],
  };
  const risk_color = { on_track: '#16a34a', at_risk: '#f59e0b', critical: '#dc2626' };

  return (
    <div>
      {students.length === 0 ? <div style={s.card}><p style={s.empty}>No students assigned.</p></div> :
        students.map(p => (
          <div key={p.project_id} style={{ ...s.card, marginBottom: 14 }}>
            {/* ── Student header ── */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
                  <h4 style={{ fontSize: 15, fontWeight: 700, color: '#fff', margin: 0 }}>{p.student_name}</h4>
                  {p.supervisor_role && (
                    <span style={{
                      fontSize: 10,
                      padding: '2px 8px',
                      borderRadius: 10,
                      fontWeight: 600,
                      background: p.supervisor_role === 'Co-Supervisor' ? 'rgba(14,165,233,0.15)' : 'rgba(34,197,94,0.15)',
                      color: p.supervisor_role === 'Co-Supervisor' ? '#38bdf8' : '#4ade80',
                    }}>
                      {p.supervisor_role}
                    </span>
                  )}
                  {p.level && (
                    <span style={{ fontSize: 10, padding: '2px 6px', borderRadius: 8, background: 'rgba(255,255,255,0.06)', color: '#9ca3af' }}>
                      {p.level}
                    </span>
                  )}
                </div>
                <p style={{ fontSize: 13, color: '#9ca3af', marginTop: 4 }}>{p.title || '—'}</p>
                <p style={{ fontSize: 12, color: '#4b5563', marginTop: 4 }}>
                  {p.ms_done || 0}/{p.ms_total || 5} milestones · {p.matric_number || '—'} · {p.submission_count || 0} submission(s)
                </p>
              </div>

              <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                <span style={{ color: risk_color[p.risk_label] || '#6b7280', fontWeight: 700, fontSize: 12 }}>
                  {p.risk_label || 'Unscanned'}
                </span>
                <button
                  style={subsOpen === p.project_id
                    ? { ...s.smBtn, background: 'rgba(96,165,250,0.12)', color: '#60a5fa', borderColor: 'rgba(96,165,250,0.25)' }
                    : s.smBtn}
                  onClick={() => loadSubs(p.project_id)}>
                  {subsOpen === p.project_id ? 'Hide Files' : 'View Files'}
                </button>
              </div>
            </div>

            {/* ── Submissions panel ── */}
            {subsOpen === p.project_id && (
              <div style={{ marginTop: 14, paddingTop: 14, borderTop: '1px solid rgba(255,255,255,0.07)' }}>
                <p style={{ fontSize: 12, fontWeight: 600, color: '#6b7280', textTransform: 'uppercase', letterSpacing: '0.5px', marginBottom: 10 }}>
                  Submitted Documents
                </p>
                {(subsData[p.project_id] || []).length === 0 ? (
                  <p style={{ fontSize: 13, color: '#4b5563', textAlign: 'center', padding: '16px 0' }}>No submissions yet.</p>
                ) : (
                  (subsData[p.project_id] || []).map(sub => {
                    const isViewing = viewingFile === sub.doc_id;
                    const isLoading = loadingDoc === sub.doc_id;
                    const isDlBusy  = loadingDoc === sub.doc_id + '_dl';
                    const [badgeBg, badgeColor] = statusBadge[sub.status] || ['rgba(255,255,255,0.06)', '#9ca3af'];
                    const pdf = isPdf(sub.file_name);
                    return (
                      <div key={sub.doc_id} style={{ background: '#0f0f0f', borderRadius: 8, padding: '12px 14px', marginBottom: 8, border: '1px solid rgba(255,255,255,0.07)' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 10 }}>
                          <div style={{ flex: 1, minWidth: 0 }}>
                            <div style={{ display: 'flex', gap: 8, alignItems: 'center', flexWrap: 'wrap' }}>
                              <span style={{ background: 'rgba(96,165,250,0.1)', color: '#60a5fa', padding: '1px 7px', borderRadius: 8, fontSize: 10, fontWeight: 700 }}>
                                {(sub.chapter || '').replace('chapter', 'Ch. ').replace('proposal', 'Proposal').toUpperCase()}
                              </span>
                              <span style={{ background: badgeBg, color: badgeColor, padding: '1px 7px', borderRadius: 8, fontSize: 10, fontWeight: 600 }}>
                                {(sub.status || '').replace(/_/g, ' ')}
                              </span>
                              <span style={{ fontSize: 11, color: '#4b5563' }}>v{sub.version}</span>
                            </div>
                            <p style={{ fontSize: 12, color: '#9ca3af', marginTop: 4, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                              &#128206; {sub.file_name || 'Unnamed file'}
                            </p>
                            <p style={{ fontSize: 11, color: '#374151', marginTop: 2 }}>{new Date(sub.uploaded_at).toLocaleString()}</p>
                            {sub.supervisor_comment && (
                              <p style={{ fontSize: 12, color: '#6b7280', marginTop: 4, fontStyle: 'italic' }}>"{sub.supervisor_comment}"</p>
                            )}
                          </div>
                          <div style={{ display: 'flex', gap: 6, flexShrink: 0 }}>
                            <button
                              disabled={isLoading}
                              style={isViewing
                                ? { ...s.smBtn, background: 'rgba(245,158,11,0.12)', color: '#f59e0b', borderColor: 'rgba(245,158,11,0.25)' }
                                : { ...s.smBtn, background: 'rgba(96,165,250,0.1)', color: '#60a5fa', borderColor: 'rgba(96,165,250,0.2)' }}
                              onClick={() => handleView(sub)}>
                              {isLoading ? '…' : isViewing ? 'Close' : 'View'}
                            </button>
                            <button
                              disabled={isDlBusy}
                              style={{ ...s.smBtn, padding: '5px 10px' }}
                              onClick={() => handleDownload(sub)}
                              title="Download file">
                              {isDlBusy ? '…' : '↓'}
                            </button>
                          </div>
                        </div>

                        {/* ── Inline file viewer ── */}
                        {isViewing && blobUrls[sub.doc_id] && (
                          <div style={{ marginTop: 10, paddingTop: 10, borderTop: '1px solid rgba(255,255,255,0.06)' }}>
                            {pdf ? (
                              <iframe
                                src={blobUrls[sub.doc_id]}
                                title={sub.file_name}
                                style={{ width: '100%', height: 600, border: 'none', borderRadius: 6, background: '#fff' }}
                              />
                            ) : (
                              <div style={{ textAlign: 'center', padding: '20px 16px', background: 'rgba(245,158,11,0.04)', borderRadius: 8, border: '1px solid rgba(245,158,11,0.15)' }}>
                                <p style={{ fontSize: 28, marginBottom: 8 }}>&#128196;</p>
                                <p style={{ fontSize: 13, color: '#e5e7eb', fontWeight: 600, marginBottom: 4 }}>{sub.file_name}</p>
                                <p style={{ fontSize: 12, color: '#9ca3af', marginBottom: 14 }}>
                                  Word and Office documents cannot be previewed in the browser.
                                </p>
                                <button onClick={() => handleDownload(sub)}
                                  style={{ ...s.btn, fontSize: 12, padding: '8px 20px' }}>
                                  ↓ Download File
                                </button>
                              </div>
                            )}
                          </div>
                        )}
                      </div>
                    );
                  })
                )}
              </div>
            )}
          </div>
        ))
      }
    </div>
  );
}

// ─── REVIEW TAB ───────────────────────────────
function ReviewTab({ students, pendingReviews, reload }) {
  const [reviewing,  setReviewing]  = useState(null);
  const [viewing,    setViewing]    = useState(null);
  const [blobUrls,   setBlobUrls]   = useState({});
  const [loadingDoc, setLoadingDoc] = useState(null);
  const [form,       setForm]       = useState({ status: 'reviewed', supervisor_comment: '' });
  const [busy,       setBusy]       = useState(false);

  const handleSubmit = async (e, docId) => {
    e.preventDefault();
    setBusy(true);
    try {
      await api.patch(`/supervisor/submissions/${docId}/review`, form);
      toast.success('Review submitted!');
      setReviewing(null);
      setViewing(null);
      setForm({ status: 'reviewed', supervisor_comment: '' });
      reload();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Review failed.');
    } finally {
      setBusy(false);
    }
  };

  const handleView = async (sub) => {
    if (viewing === sub.doc_id) { setViewing(null); return; }
    if (blobUrls[sub.doc_id]) { setViewing(sub.doc_id); return; }
    setLoadingDoc(sub.doc_id);
    try {
      const blob    = await fetchFileBlob(sub.doc_id);
      const mtype   = isPdf(sub.file_name) ? 'application/pdf' : blob.type;
      const blobUrl = URL.createObjectURL(new Blob([blob], { type: mtype }));
      setBlobUrls(prev => ({ ...prev, [sub.doc_id]: blobUrl }));
      setViewing(sub.doc_id);
    } catch {
      toast.error('Could not load file.');
    } finally {
      setLoadingDoc(null);
    }
  };

  const handleDownload = async (sub) => {
    setLoadingDoc(sub.doc_id + '_dl');
    try {
      const blob = blobUrls[sub.doc_id]
        ? await fetch(blobUrls[sub.doc_id]).then(r => r.blob())
        : await fetchFileBlob(sub.doc_id);
      triggerDownload(blob, sub.file_name);
    } catch {
      toast.error('Download failed.');
    } finally {
      setLoadingDoc(null);
    }
  };

  if (pendingReviews.length === 0) {
    return <div style={s.card}><p style={s.empty}>No pending submissions to review.</p></div>;
  }

  return (
    <div>
      <p style={{ fontSize: 12, color: '#9ca3af', marginBottom: 12 }}>
        {pendingReviews.length} submission{pendingReviews.length !== 1 ? 's' : ''} awaiting review
      </p>
      {pendingReviews.map(sub => {
        const isViewing   = viewing   === sub.doc_id;
        const isReviewing = reviewing === sub.doc_id;
        const isLoading   = loadingDoc === sub.doc_id;
        const isDlBusy    = loadingDoc === sub.doc_id + '_dl';
        const pdf         = isPdf(sub.file_name);

        return (
          <div key={sub.doc_id} style={{ ...s.card, marginBottom: 14 }}>
            {/* ── Header row ── */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
              <div style={{ flex: 1, minWidth: 0 }}>
                <h4 style={{ fontSize: 15, fontWeight: 700, color: '#fff', marginBottom: 2 }}>{sub.student_name}</h4>
                <p style={{ fontSize: 12, color: '#9ca3af', marginBottom: 6 }}>{sub.project_title}</p>
                <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
                  <span style={{ background: 'rgba(96,165,250,0.1)', color: '#60a5fa', padding: '2px 8px', borderRadius: 10, fontSize: 11, fontWeight: 600 }}>
                    {(sub.chapter || '').replace('chapter', 'Chapter ').replace('proposal', 'Proposal')}
                  </span>
                  <span style={{ fontSize: 11, color: '#4b5563' }}>v{sub.version}</span>
                  <span style={{ fontSize: 11, color: '#4b5563' }}>{new Date(sub.uploaded_at).toLocaleString()}</span>
                  {sub.file_size && <span style={{ fontSize: 11, color: '#4b5563' }}>{(sub.file_size / 1024).toFixed(1)} KB</span>}
                </div>
              </div>

              {/* ── Action buttons ── */}
              <div style={{ display: 'flex', gap: 6, flexShrink: 0, marginLeft: 12 }}>
                <button
                  disabled={isLoading}
                  style={isViewing
                    ? { ...s.smBtn, background: 'rgba(245,158,11,0.12)', color: '#f59e0b', borderColor: 'rgba(245,158,11,0.25)' }
                    : { ...s.smBtn, background: 'rgba(96,165,250,0.1)', color: '#60a5fa', borderColor: 'rgba(96,165,250,0.2)' }}
                  onClick={() => handleView(sub)}>
                  {isLoading ? '…' : isViewing ? 'Hide' : 'View Doc'}
                </button>
                <button
                  disabled={isDlBusy}
                  style={{ ...s.smBtn, padding: '5px 10px' }}
                  onClick={() => handleDownload(sub)}
                  title="Download file">
                  {isDlBusy ? '…' : '↓'}
                </button>
                <button
                  style={isReviewing
                    ? { ...s.smBtn, background: 'rgba(239,68,68,0.1)', color: '#f87171', borderColor: 'rgba(239,68,68,0.2)' }
                    : s.smBtn}
                  onClick={() => {
                    setReviewing(isReviewing ? null : sub.doc_id);
                    setForm({ status: 'reviewed', supervisor_comment: '' });
                  }}>
                  {isReviewing ? 'Cancel' : 'Review'}
                </button>
              </div>
            </div>

            {/* ── File viewer panel ── */}
            {isViewing && blobUrls[sub.doc_id] && (
              <div style={{ marginTop: 14, paddingTop: 14, borderTop: '1px solid rgba(255,255,255,0.07)' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 10 }}>
                  <span style={{ fontSize: 13, color: '#e5e7eb', fontWeight: 500 }}>&#128206; {sub.file_name}</span>
                </div>
                {pdf ? (
                  <iframe
                    src={blobUrls[sub.doc_id]}
                    title={sub.file_name}
                    style={{ width: '100%', height: 600, border: '1px solid rgba(255,255,255,0.1)', borderRadius: 8, background: '#fff' }}
                  />
                ) : (
                  <div style={{ background: 'rgba(245,158,11,0.06)', border: '1px solid rgba(245,158,11,0.2)', borderRadius: 8, padding: '20px 16px', textAlign: 'center' }}>
                    <p style={{ fontSize: 32, marginBottom: 8 }}>&#128196;</p>
                    <p style={{ fontSize: 14, color: '#e5e7eb', fontWeight: 600, marginBottom: 4 }}>{sub.file_name}</p>
                    <p style={{ fontSize: 12, color: '#9ca3af', marginBottom: 14 }}>
                      Word and Office documents cannot be previewed in the browser.
                    </p>
                    <button onClick={() => handleDownload(sub)}
                      style={{ ...s.btn, padding: '8px 20px', fontSize: 12 }}>
                      ↓ Download File
                    </button>
                  </div>
                )}
              </div>
            )}

            {/* ── Review form ── */}
            {isReviewing && (
              <form onSubmit={e => handleSubmit(e, sub.doc_id)}
                style={{ marginTop: 14, paddingTop: 14, borderTop: '1px solid rgba(255,255,255,0.07)', display: 'flex', flexDirection: 'column', gap: 10 }}>
                <FormField label="Decision *">
                  <select style={s.input} value={form.status} onChange={e => setForm(p => ({...p, status: e.target.value}))}>
                    <option value="reviewed">Reviewed</option>
                    <option value="revision_needed">Revision Needed</option>
                    <option value="approved">Approved</option>
                  </select>
                </FormField>
                <FormField label="Feedback / Comment">
                  <textarea
                    style={{ ...s.input, height: 80, resize: 'vertical' }}
                    value={form.supervisor_comment}
                    onChange={e => setForm(p => ({...p, supervisor_comment: e.target.value}))}
                    placeholder="Your feedback on this submission…" />
                </FormField>
                <button type="submit" style={busy ? { ...s.btn, opacity: 0.6 } : s.btn} disabled={busy}>
                  {busy ? 'Submitting…' : 'Submit Review'}
                </button>
              </form>
            )}
          </div>
        );
      })}
    </div>
  );
}

// ─── EVALUATE TAB ─────────────────────────────
function EvaluateTab({ students, reload }) {
  const [form, setForm] = useState({
    project_id: '', methodology_score: '', literature_score: '',
    analysis_score: '', presentation_score: '', originality_score: '',
    defense_notes: '',
  });
  const [busy,   setBusy]   = useState(false);
  const [result, setResult] = useState(null);

  const defended = students.filter(p => p.status === 'in_progress' || p.status === 'in_review');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setBusy(true);
    setResult(null);
    try {
      const res = await api.post('/supervisor/evaluate', {
        project_id:          Number(form.project_id),
        methodology_score:   Number(form.methodology_score),
        literature_score:    Number(form.literature_score),
        analysis_score:      Number(form.analysis_score),
        presentation_score:  Number(form.presentation_score),
        originality_score:   Number(form.originality_score),
        defense_notes:       form.defense_notes,
      });
      setResult(res.data);
      toast.success(`Grade: ${res.data.grade_letter} (${res.data.total_score})`);
      reload();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Evaluation failed.');
    } finally {
      setBusy(false);
    }
  };

  const scores = ['methodology', 'literature', 'analysis', 'presentation', 'originality'];
  const grade_color = { A: '#16a34a', B: '#15803d', C: '#f59e0b', D: '#f97316', F: '#dc2626' };

  return (
    <div style={s.card}>
      <h3 style={s.cardTitle}>Final Evaluation (Rubric)</h3>
      <p style={{ fontSize: 12, color: '#9ca3af', marginBottom: 14 }}>Each criterion is marked out of 20 (total 100).</p>
      <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
        <FormField label="Select Project *">
          <select style={s.input} value={form.project_id} onChange={e => setForm(p => ({...p, project_id: e.target.value}))} required>
            <option value="">Choose a project</option>
            {defended.map(p => <option key={p.project_id} value={p.project_id}>{p.student_name} — {p.title}</option>)}
          </select>
        </FormField>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3,1fr)', gap: 12 }}>
          {scores.map(sc => (
            <FormField key={sc} label={`${sc.charAt(0).toUpperCase()+sc.slice(1)} (/20)`}>
              <input style={s.input} type="number" min="0" max="20" step="0.5"
                value={form[`${sc}_score`]}
                onChange={e => setForm(p => ({...p, [`${sc}_score`]: e.target.value}))}
                required placeholder="0–20" />
            </FormField>
          ))}
        </div>
        <FormField label="Defense Notes">
          <textarea style={{ ...s.input, height: 70, resize: 'vertical' }} value={form.defense_notes} onChange={e => setForm(p => ({...p, defense_notes: e.target.value}))} placeholder="Optional notes from the defense session" />
        </FormField>
        <button type="submit" style={busy ? { ...s.btn, opacity: 0.6 } : s.btn} disabled={busy}>
          {busy ? 'Evaluating…' : 'Submit Evaluation'}
        </button>
      </form>

      {result && (
        <div style={{ marginTop: 20, background: 'rgba(22,163,74,0.08)', border: '1px solid rgba(22,163,74,0.25)', borderRadius: 10, padding: 16, textAlign: 'center' }}>
          <p style={{ fontSize: 14, color: '#4ade80', marginBottom: 8 }}>Evaluation Complete</p>
          <p style={{ fontSize: 40, fontWeight: 900, color: grade_color[result.grade_letter] || '#e5e7eb' }}>{result.grade_letter}</p>
          <p style={{ fontSize: 18, fontWeight: 700, color: '#e5e7eb' }}>{result.total_score} / 100</p>
        </div>
      )}
    </div>
  );
}

// ─── ALERTS TAB ───────────────────────────────
function AlertsTab({ alerts, reload }) {
  const markAll = async () => { try { await api.patch('/alerts/read-all'); reload(); } catch {} };
  return (
    <div style={s.card}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <h3 style={s.cardTitle}>Notifications</h3>
        {alerts.some(a => !a.is_read) && <button style={s.smBtn} onClick={markAll}>Mark all read</button>}
      </div>
      {alerts.length === 0 ? <p style={s.empty}>No notifications.</p> : alerts.map(a => (
        <div key={a.alert_id} style={{ ...s.alertItem, opacity: a.is_read ? 0.6 : 1 }}>
          <div>
            <p style={{ fontWeight: 600, fontSize: 13 }}>{a.title}</p>
            <p style={{ fontSize: 12, color: '#9ca3af', marginTop: 2 }}>{a.message}</p>
            <p style={{ fontSize: 11, color: '#4b5563', marginTop: 4 }}>{new Date(a.triggered_at).toLocaleString()}</p>
          </div>
        </div>
      ))}
    </div>
  );
}

// ─── MESSAGES TAB ─────────────────────────────
function MessagesTab({ user, students }) {
  const [messages, setMessages] = useState([]);
  const [compose,  setCompose]  = useState(false);
  const [form,     setForm]     = useState({ receiver_id: '', subject: '', body: '' });
  const [busy,     setBusy]     = useState(false);

  const fetchMessages = () => api.get('/messages').then(r => setMessages(r.data.messages || [])).catch(() => {});
  useEffect(() => { fetchMessages(); }, []);

  const handleSend = async (e) => {
    e.preventDefault();
    setBusy(true);
    try {
      await api.post('/messages', { ...form, receiver_id: Number(form.receiver_id) });
      toast.success('Message sent!');
      setCompose(false);
      setForm({ receiver_id: '', subject: '', body: '' });
      fetchMessages();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed.');
    } finally { setBusy(false); }
  };

  return (
    <div style={s.card}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <h3 style={s.cardTitle}>Messages</h3>
        <button style={s.btn} onClick={() => setCompose(!compose)}>{compose ? 'Cancel' : '+ New Message'}</button>
      </div>
      {compose && (
        <form onSubmit={handleSend} style={{ background: 'rgba(22,163,74,0.05)', border: '1px solid rgba(22,163,74,0.15)', borderRadius: 8, padding: 16, marginBottom: 14, display: 'flex', flexDirection: 'column', gap: 10 }}>
          <FormField label="Send To *">
            {students.length > 0 ? (
              <select style={s.input} value={form.receiver_id} onChange={e => setForm(p => ({...p, receiver_id: e.target.value}))} required>
                <option value="">Choose a student</option>
                {students.map(p => (
                  <option key={p.student_user_id} value={p.student_user_id}>
                    {p.student_name} ({p.matric_number || 'N/A'})
                  </option>
                ))}
              </select>
            ) : (
              <input style={s.input} type="number" placeholder="User ID" value={form.receiver_id} onChange={e => setForm(p => ({...p, receiver_id: e.target.value}))} required />
            )}
          </FormField>
          <FormField label="Subject"><input style={s.input} value={form.subject} onChange={e => setForm(p => ({...p, subject: e.target.value}))} placeholder="Message subject" /></FormField>
          <FormField label="Body *"><textarea style={{ ...s.input, height: 70 }} value={form.body} onChange={e => setForm(p => ({...p, body: e.target.value}))} required placeholder="Your message…" /></FormField>
          <button type="submit" style={busy ? { ...s.btn, opacity: 0.6 } : s.btn} disabled={busy}>{busy ? 'Sending…' : 'Send'}</button>
        </form>
      )}
      {messages.length === 0 ? <p style={s.empty}>No messages.</p> : messages.map(m => (
        <div key={m.message_id} style={{ ...s.alertItem, background: m.is_read ? '#0f0f0f' : 'rgba(22,163,74,0.06)' }}>
          <p style={{ fontWeight: 600, fontSize: 13, color: '#fff' }}>{m.subject || '(No subject)'}</p>
          <p style={{ fontSize: 12, color: '#9ca3af', marginTop: 2 }}>From: {m.sender_name} · {new Date(m.sent_at).toLocaleString()}</p>
          <p style={{ fontSize: 13, color: '#e5e7eb', marginTop: 4 }}>{m.body}</p>
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
            : <div style={{ width: 72, height: 72, background: '#15803d', borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 28, fontWeight: 700, color: '#fff', border: '2px solid #16a34a' }}>{user?.full_name?.[0]}</div>}
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
        {[['Username', user?.username], ['Email', user?.email], ['Phone', user?.phone || '—']].map(([label, val]) => (
          <div key={label} style={{ background: '#0f0f0f', borderRadius: 8, padding: '12px 14px' }}>
            <p style={s.label}>{label}</p>
            <p style={{ fontSize: 13, color: '#e5e7eb' }}>{val}</p>
          </div>
        ))}
      </div>
    </div>
  );
}

// ─── SHARED ───────────────────────────────────
function Sidebar({ role, active, onTab, onLogout, unread }) {
  const tabs = [
    { id: 'dashboard', label: 'Dashboard',       Icon: LayoutDashboard },
    { id: 'students',  label: 'My Students',     Icon: Users },
    { id: 'review',    label: 'Review Chapter',  Icon: Eye },
    { id: 'evaluate',  label: 'Final Evaluation',Icon: Award },
    { id: 'alerts',    label: `Alerts${unread > 0 ? ` (${unread})` : ''}`, Icon: Bell },
    { id: 'messages',  label: 'Messages',        Icon: MessageSquare },
  ];
  return (
    <aside style={s.sidebar}>
      <div style={s.sideHeader}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 8 }}>
          <img src="/kwasu.png" alt="KWASU" style={s.logoImg} />
          <div>
            <div style={{ color: 'var(--text-primary, #ffffff)', fontWeight: 800, fontSize: 16, letterSpacing: '0.5px', lineHeight: 1.2 }}>KWASU</div>
            <div style={{ color: '#22c55e', fontSize: 10, fontWeight: 700, letterSpacing: '1px' }}>SPSEMS</div>
          </div>
        </div>
        <p style={s.sideRole}>{role?.toUpperCase() || 'SUPERVISOR'}</p>
      </div>
      <nav style={{ flex: 1, paddingTop: 8 }}>
        {tabs.map(({ id, label, Icon }) => (
          <button key={id} style={active === id ? { ...s.navBtn, ...s.navActive } : s.navBtn} onClick={() => onTab(id)}>
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
      <h2 style={s.topTitle}>{title}</h2>
      <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
        <ThemeToggle />
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, cursor: 'pointer' }} onClick={onProfile} title="View profile">
          {user?.avatar_url
            ? <img src={user.avatar_url} alt="avatar" style={{ width: 32, height: 32, borderRadius: '50%', objectFit: 'cover', border: '2px solid #16a34a' }} />
            : <div style={s.avatar}>{user?.full_name?.[0] || 'U'}</div>}
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

function StatusBadge({ status }) {
  const map = { pending: ['rgba(245,158,11,0.15)','#f59e0b'], approved: ['rgba(22,163,74,0.15)','#22c55e'], in_progress: ['rgba(59,130,246,0.15)','#60a5fa'], in_review: ['rgba(139,92,246,0.15)','#a78bfa'], completed: ['rgba(22,163,74,0.15)','#22c55e'], rejected: ['rgba(239,68,68,0.15)','#f87171'] };
  const [bg, color] = map[status] || ['rgba(255,255,255,0.08)','#9ca3af'];
  return <span style={{ background: bg, color, padding: '2px 8px', borderRadius: 20, fontSize: 11, fontWeight: 600 }}>{status.replace(/_/g,' ')}</span>;
}

function FormField({ label, children }) {
  return <div><label style={s.label}>{label}</label>{children}</div>;
}

function Loader() {
  return <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100vh', fontSize: 15, color: '#16a34a', background: 'var(--bg-app, #0a0a0a)', fontWeight: 500, letterSpacing: '0.3px' }}>Loading...</div>;
}

const TAB_TITLES = { dashboard: 'Dashboard', students: 'My Students', review: 'Review Chapter', evaluate: 'Final Evaluation', alerts: 'Notifications', messages: 'Messages', profile: 'My Profile' };

const s = {
  layout:     { display: 'flex', minHeight: '100vh', background: 'var(--bg-app, #0a0a0a)' },
  sidebar:    { width: 228, background: 'var(--bg-sidebar, #080808)', display: 'flex', flexDirection: 'column', padding: '24px 0', borderRight: '1px solid var(--border-sidebar, rgba(255,255,255,0.06))' },
  sideHeader: { padding: '0 20px 20px', borderBottom: '1px solid var(--border-subtle, rgba(255,255,255,0.07))' },
  logoImg:    { height: 38, width: 'auto', display: 'block', objectFit: 'contain' },
  sideRole:   { color: 'var(--text-dim, #6b7280)', fontSize: 10, letterSpacing: '1.5px', textTransform: 'uppercase', fontWeight: 600 },
  navBtn:     { display: 'flex', alignItems: 'center', gap: 10, width: '100%', padding: '10px 20px', background: 'none', border: 'none', borderLeft: '3px solid transparent', color: 'var(--text-dim, #6b7280)', textAlign: 'left', fontSize: 13, cursor: 'pointer', fontWeight: 500 },
  navActive:  { background: 'rgba(22,163,74,0.08)', color: '#22c55e', borderLeftColor: '#16a34a', fontWeight: 600 },
  logoutBtn:  { width: '100%', padding: '10px 12px', background: 'rgba(239,68,68,0.08)', border: '1px solid rgba(239,68,68,0.15)', borderRadius: 7, color: '#f87171', cursor: 'pointer', fontSize: 12, fontWeight: 600, display: 'flex', alignItems: 'center', gap: 8 },
  main:       { flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' },
  topbar:     { background: 'var(--bg-topbar, #0f0f0f)', padding: '14px 24px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid var(--border-subtle, rgba(255,255,255,0.07))' },
  topTitle:   { fontSize: 17, fontWeight: 700, color: 'var(--text-primary, #ffffff)', letterSpacing: '-0.3px' },
  avatar:     { width: 32, height: 32, background: '#15803d', borderRadius: '50%', color: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 700, fontSize: 13 },
  content:    { flex: 1, padding: 24, overflowY: 'auto', background: 'var(--bg-app, #0a0a0a)' },
  statsRow:   { display: 'grid', gridTemplateColumns: 'repeat(4,1fr)', gap: 14, marginBottom: 20 },
  card:       { background: 'var(--bg-card, #141414)', borderRadius: 12, padding: '20px 22px', border: '1px solid var(--border-subtle, rgba(255,255,255,0.07))' },
  cardTitle:  { fontSize: 15, fontWeight: 700, color: 'var(--text-primary, #ffffff)', marginBottom: 14, letterSpacing: '-0.2px' },
  table:      { width: '100%', borderCollapse: 'collapse' },
  th:         { textAlign: 'left', fontSize: 10, fontWeight: 700, color: 'var(--table-th-color, #6b7280)', textTransform: 'uppercase', padding: '8px 10px', letterSpacing: '0.5px', background: 'var(--table-th-bg, #0f0f0f)' },
  td:         { padding: '10px', fontSize: 13, color: 'var(--text-secondary, #e5e7eb)' },
  alertItem:  { padding: '12px 14px', background: 'rgba(22,163,74,0.05)', borderRadius: 8, marginBottom: 8, border: '1px solid var(--border-subtle, rgba(255,255,255,0.07))' },
  label:      { display: 'block', fontSize: 11, fontWeight: 600, color: 'var(--text-dim, #6b7280)', marginBottom: 5, letterSpacing: '0.3px', textTransform: 'uppercase' },
  input:      { width: '100%', padding: '9px 11px', background: 'var(--bg-input, #0f0f0f)', border: '1px solid var(--border-input, rgba(255,255,255,0.1))', borderRadius: 7, fontSize: 13, outline: 'none', color: 'var(--text-primary, #fff)', boxSizing: 'border-box' },
  btn:        { padding: '10px 18px', background: '#15803d', color: '#fff', border: 'none', borderRadius: 7, fontWeight: 600, fontSize: 13, cursor: 'pointer' },
  smBtn:      { padding: '5px 12px', background: 'rgba(22,163,74,0.1)', color: '#22c55e', border: '1px solid rgba(22,163,74,0.2)', borderRadius: 6, fontSize: 12, fontWeight: 600, cursor: 'pointer' },
  empty:      { color: 'var(--text-dim, #6b7280)', fontSize: 13, textAlign: 'center', padding: '32px 0' },
};
