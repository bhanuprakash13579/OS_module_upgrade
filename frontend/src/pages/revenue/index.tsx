import { useState, useEffect, useCallback, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowLeft, ClipboardList, Sun, Moon, Calendar, CheckCircle, Download, X, FileText, Pencil } from 'lucide-react';
import api from '@/lib/api';
import SessionSetup from './SessionSetup';
import RevenueSheet from './RevenueSheet';
import MessageGenerator from './MessageGenerator';
import FormulaRulesPage from './FormulaRulesPage';
import type { DrSession, DrFormulaRule } from './revenueCalc';
import { fmtDate } from './revenueCalc';
import { showDownloadToast } from '@/components/DownloadToast';

type View = 'dashboard' | 'sheet' | 'new' | 'config';

// ── Challan prompt modal ──────────────────────────────────────────────────────
// Shown before ADC download when the session has no challan number yet.
// User either enters the challan or skips (online-only session).
function ChallanModal({
  session,
  onConfirm,
  onSkip,
  onClose,
  defaultValue = '',
  skipLabel = 'No offline BRs — Download without challan',
}: {
  session: DrSession;
  onConfirm: (challanNo: string) => void;
  onSkip: () => void;
  onClose: () => void;
  defaultValue?: string;
  skipLabel?: string;
}) {
  const [value, setValue] = useState(defaultValue);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => { inputRef.current?.focus(); }, []);

  const handleConfirm = () => {
    const trimmed = value.trim();
    if (!trimmed) return;
    onConfirm(trimmed);
  };

  const shiftLabel = session.shift === 'DAY' ? 'Day' : 'Night';

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-sm mx-4 p-6 space-y-4">
        <div className="flex items-start justify-between">
          <div>
            <p className="font-bold text-slate-800">Enter Bank Challan No.</p>
            <p className="text-xs text-slate-500 mt-0.5">
              {fmtDate(session.report_date)} · {shiftLabel} Shift
            </p>
          </div>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-600">
            <X size={18} />
          </button>
        </div>

        <div className="space-y-1">
          <label className="text-xs font-medium text-slate-600">
            SBI Challan No. (for offline BRs in this shift)
          </label>
          <input
            ref={inputRef}
            value={value}
            onChange={e => setValue(e.target.value)}
            onKeyDown={e => { if (e.key === 'Enter') handleConfirm(); }}
            placeholder="e.g. 3379"
            className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-teal-400"
          />
          <p className="text-xs text-slate-400">
            This is required so the bank challan appears in the monthly revenue report.
          </p>
        </div>

        <div className="flex flex-col gap-2">
          <button
            onClick={handleConfirm}
            disabled={!value.trim()}
            className="w-full py-2 bg-teal-600 hover:bg-teal-700 disabled:opacity-40 text-white text-sm font-semibold rounded-lg"
          >
            Save &amp; Download
          </button>
          <button
            onClick={onSkip}
            className="w-full py-2 border border-slate-300 text-slate-600 text-sm rounded-lg hover:bg-slate-50"
          >
            {skipLabel}
          </button>
        </div>
      </div>
    </div>
  );
}

// ── Main component ────────────────────────────────────────────────────────────

export default function RevenueModule() {
  const navigate = useNavigate();
  const [view, setView] = useState<View>('dashboard');
  const [session, setSession] = useState<DrSession | null>(null);
  const [sessions, setSessions] = useState<DrSession[]>([]);
  const [loadingSessions, setLoadingSessions] = useState(true);
  const [showMessage, setShowMessage] = useState(false);
  const [filterDate, setFilterDate] = useState('');

  // Challan prompt state (new entry before download)
  const [challanTarget, setChallanTarget] = useState<DrSession | null>(null);
  // Challan edit state (correct a previously-entered challan)
  const [editChallanTarget, setEditChallanTarget] = useState<DrSession | null>(null);

  // Monthly download
  const today = new Date();
  const [monthYear, setMonthYear] = useState(
    `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}`
  );
  const [monthDownloading, setMonthDownloading] = useState(false);

  // Formula rules — fetched once, kept in sync via FormulaRulesPage callback
  const [rules, setRules] = useState<DrFormulaRule[]>([]);
  const [rulesLoaded, setRulesLoaded] = useState(false);
  // pendingSession: a newly-created session waiting for rules to finish loading before opening
  const [pendingSession, setPendingSession] = useState<DrSession | null>(null);
  const [openError, setOpenError] = useState<string | null>(null);

  const loadSessions = useCallback(() => {
    setLoadingSessions(true);
    api.get('/dcr/sessions')
      .then(r => setSessions(r.data))
      .catch(() => {})
      .finally(() => setLoadingSessions(false));
  }, []);

  useEffect(() => {
    loadSessions();
    api.get('/dcr/formula-rules')
      .then(r => { setRules(r.data); setRulesLoaded(true); })
      .catch(() => setRulesLoaded(true));
  }, []); // eslint-disable-line

  const openSession = async (s: DrSession) => {
    setOpenError(null);
    try {
      const res = await api.get(`/dcr/sessions/${s.id}`);
      setSession(res.data);
      setView('sheet');
    } catch (e: unknown) {
      const msg = (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail
        || 'Failed to open session. Please try again.';
      setOpenError(msg);
    }
  };

  // Called when a new session is created via SessionSetup.
  // If formula rules haven't loaded yet, park the session and open it once they arrive.
  const handleSessionReady = (s: DrSession) => {
    loadSessions();
    if (rulesLoaded) {
      setSession(s);
      setView('sheet');
    } else {
      setPendingSession(s);
    }
  };

  // Open pending session once rules finish loading
  useEffect(() => {
    if (rulesLoaded && pendingSession) {
      setSession(pendingSession);
      setPendingSession(null);
      setView('sheet');
    }
  }, [rulesLoaded, pendingSession]);

  const handleBack = () => {
    setSession(null);
    setView('dashboard');
    loadSessions();
  };

  const handleRulesChanged = useCallback((updated: DrFormulaRule[]) => {
    setRules(updated);
    setRulesLoaded(true);
  }, []);

  // ── ADC download — prompts for challan if not yet set ──────────────────────
  const _doAdcDownload = useCallback(async (s: DrSession) => {
    try {
      const res = await api.get(`/dcr/sessions/${s.id}/download/adc`, { responseType: 'blob' });
      const shift = s.shift === 'DAY' ? 'D' : 'N';
      const fname = `${fmtDate(s.report_date)}(${shift}) ADC REPORT.xlsx`;
      const url = URL.createObjectURL(res.data);
      const a = document.createElement('a');
      a.href = url; a.download = fname; a.click();
      URL.revokeObjectURL(url);
      showDownloadToast(fname);
    } catch { /* silent */ }
  }, []);

  const downloadAdc = useCallback(async (s: DrSession, e: React.MouseEvent) => {
    e.stopPropagation();
    if (s.challan_no) {
      // Challan already recorded — download immediately
      _doAdcDownload(s);
    } else {
      // No challan yet — prompt before download
      setChallanTarget(s);
    }
  }, [_doAdcDownload]);

  const handleChallanConfirm = useCallback(async (challanNo: string) => {
    if (!challanTarget) return;
    try {
      const res = await api.patch(`/dcr/sessions/${challanTarget.id}/challan`, { challan_no: challanNo });
      // Update local sessions list with the saved challan number
      setSessions(prev => prev.map(s => s.id === challanTarget.id ? { ...s, challan_no: res.data.challan_no } : s));
      const updated = { ...challanTarget, challan_no: res.data.challan_no };
      setChallanTarget(null);
      _doAdcDownload(updated);
    } catch { setChallanTarget(null); }
  }, [challanTarget, _doAdcDownload]);

  const handleChallanSkip = useCallback(() => {
    if (!challanTarget) return;
    const s = challanTarget;
    setChallanTarget(null);
    _doAdcDownload(s);
  }, [challanTarget, _doAdcDownload]);

  const handleChallanEdit = useCallback(async (challanNo: string) => {
    if (!editChallanTarget) return;
    try {
      const res = await api.patch(`/dcr/sessions/${editChallanTarget.id}/challan`, { challan_no: challanNo });
      setSessions(prev => prev.map(s => s.id === editChallanTarget.id ? { ...s, challan_no: res.data.challan_no } : s));
    } catch { /* silent */ }
    setEditChallanTarget(null);
  }, [editChallanTarget]);

  // ── Per-date Revenue download ──────────────────────────────────────────────
  const downloadRevenue = useCallback(async (s: DrSession, e: React.MouseEvent) => {
    e.stopPropagation();
    try {
      const res = await api.get(`/dcr/sessions/${s.id}/download/revenue`, { responseType: 'blob' });
      const fname = `${fmtDate(s.report_date)} REVENUE REPORT.xlsx`;
      const url = URL.createObjectURL(res.data);
      const a = document.createElement('a');
      a.href = url; a.download = fname; a.click();
      URL.revokeObjectURL(url);
      showDownloadToast(fname);
    } catch { /* silent */ }
  }, []);

  // ── Monthly Revenue Report download ───────────────────────────────────────
  const downloadMonthly = useCallback(async () => {
    const [yr, mo] = monthYear.split('-').map(Number);
    setMonthDownloading(true);
    try {
      const res = await api.get('/dcr/download/monthly-revenue', {
        params: { year: yr, month: mo },
        responseType: 'blob',
      });
      const monthNames = ['January','February','March','April','May','June',
                          'July','August','September','October','November','December'];
      const fname = `${monthNames[mo - 1]} ${yr} - Monthly Revenue Report.xlsx`;
      const url = URL.createObjectURL(res.data);
      const a = document.createElement('a');
      a.href = url; a.download = fname; a.click();
      URL.revokeObjectURL(url);
      showDownloadToast(fname);
    } catch { /* silent */ }
    finally { setMonthDownloading(false); }
  }, [monthYear]);

  // ── Config page ──────────────────────────────────────────────────────────
  if (view === 'config') {
    return (
      <FormulaRulesPage
        onBack={() => setView('dashboard')}
        onRulesChanged={handleRulesChanged}
      />
    );
  }

  // ── New session ──────────────────────────────────────────────────────────
  if (view === 'new') {
    return (
      <div className="h-screen flex flex-col">
        <div className="flex items-center gap-3 px-4 py-3 bg-slate-800 text-white shrink-0">
          <button onClick={() => setView('dashboard')} className="text-slate-300 hover:text-white">
            <ArrowLeft size={18} />
          </button>
          <span className="font-semibold">New Revenue Session</span>
        </div>
        <SessionSetup onSessionReady={handleSessionReady} />
      </div>
    );
  }

  // ── Sheet view ───────────────────────────────────────────────────────────
  if (view === 'sheet' && session) {
    if (!rulesLoaded) {
      return (
        <div className="h-screen flex items-center justify-center bg-slate-900">
          <p className="text-blue-300 text-sm animate-pulse">Loading formula rules…</p>
        </div>
      );
    }
    return (
      <div className="h-screen flex flex-col">
        <div className="flex items-center gap-3 px-4 py-2 bg-slate-800 text-white shrink-0">
          <button onClick={handleBack} className="text-slate-300 hover:text-white flex items-center gap-1.5 text-sm">
            <ArrowLeft size={16} /> Sessions
          </button>
          <span className="text-slate-400">·</span>
          <span className="text-sm font-semibold">
            {fmtDate(session.report_date)} · {session.shift} · {session.batch_name}
          </span>
          {session.submitted_at && (
            <span className="ml-2 text-xs font-semibold text-emerald-400 flex items-center gap-1">
              <CheckCircle size={12} /> Submitted
            </span>
          )}
        </div>

        <div className="flex-1 overflow-hidden">
          <RevenueSheet
            session={session}
            rules={rules}
            onMessage={() => setShowMessage(true)}
            onConfig={() => setView('config')}
          />
        </div>

        {showMessage && session && (
          <MessageGenerator session={session} onClose={() => setShowMessage(false)} />
        )}
      </div>
    );
  }

  // ── Dashboard ────────────────────────────────────────────────────────────

  const dateMap = sessions.reduce<Record<string, DrSession[]>>((acc, s) => {
    const key = s.report_date;
    if (!acc[key]) acc[key] = [];
    acc[key].push(s);
    return acc;
  }, {});

  const sortedDates = Object.keys(dateMap).sort((a, b) => b.localeCompare(a));
  const visibleDates = filterDate
    ? sortedDates.filter(d => d === filterDate)
    : sortedDates;

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Challan prompt modal — shown on first ADC download when no challan set */}
      {challanTarget && (
        <ChallanModal
          session={challanTarget}
          onConfirm={handleChallanConfirm}
          onSkip={handleChallanSkip}
          onClose={() => setChallanTarget(null)}
        />
      )}
      {/* Challan edit modal — correct a previously entered challan */}
      {editChallanTarget && (
        <ChallanModal
          session={editChallanTarget}
          defaultValue={editChallanTarget.challan_no ?? ''}
          onConfirm={handleChallanEdit}
          onSkip={() => setEditChallanTarget(null)}
          onClose={() => setEditChallanTarget(null)}
          skipLabel="Cancel"
        />
      )}

      {/* Top bar */}
      <div className="flex items-center gap-3 px-4 py-3 bg-slate-800 text-white">
        <button onClick={() => navigate('/modules')} className="text-slate-300 hover:text-white">
          <ArrowLeft size={18} />
        </button>
        <ClipboardList size={18} className="text-teal-400" />
        <span className="font-bold text-lg">Revenue Report Module</span>
      </div>

      <div className="max-w-4xl mx-auto p-6 space-y-5">

        {/* Monthly Revenue Report download bar */}
        <div className="flex items-center gap-3 bg-violet-50 border border-violet-200 rounded-xl px-4 py-3">
          <FileText size={16} className="text-violet-600 shrink-0" />
          <span className="text-sm font-semibold text-violet-800 flex-1">Monthly Revenue Report</span>
          <div className="flex items-center gap-2">
            <input
              type="month"
              value={monthYear}
              onChange={e => setMonthYear(e.target.value)}
              className="text-sm border border-violet-300 rounded-lg px-2 py-1 focus:outline-none focus:ring-2 focus:ring-violet-400 bg-white"
            />
            <button
              onClick={downloadMonthly}
              disabled={monthDownloading}
              className="flex items-center gap-1.5 px-4 py-1.5 bg-violet-600 hover:bg-violet-700 disabled:opacity-50 text-white text-sm font-semibold rounded-lg"
            >
              <Download size={13} />
              {monthDownloading ? 'Generating…' : 'Download'}
            </button>
          </div>
        </div>

        {/* Action bar */}
        <div className="flex items-center justify-between gap-4 flex-wrap">
          <h2 className="text-lg font-bold text-slate-800">Sessions</h2>
          <div className="flex items-center gap-2 flex-wrap">
            <div className="flex items-center gap-1.5 bg-white border border-slate-300 rounded-xl px-3 py-1.5">
              <Calendar size={14} className="text-slate-500 shrink-0" />
              <input
                type="date"
                value={filterDate}
                onChange={e => setFilterDate(e.target.value)}
                className="text-sm text-slate-700 bg-transparent focus:outline-none w-36"
                title="Filter sessions by date"
              />
              {filterDate && (
                <button onClick={() => setFilterDate('')} className="text-slate-400 hover:text-slate-600 ml-0.5">
                  <X size={13} />
                </button>
              )}
            </div>
            <button
              onClick={() => setView('config')}
              className="px-4 py-2 text-sm font-semibold bg-white border border-slate-300 text-slate-700 rounded-xl hover:bg-slate-50 flex items-center gap-1.5"
            >
              ⚙ Rates &amp; Formulas
            </button>
            <button
              onClick={() => setView('new')}
              className="px-4 py-2 text-sm font-semibold bg-teal-600 hover:bg-teal-700 text-white rounded-xl"
            >
              + New Session
            </button>
          </div>
        </div>

        {/* Open-session error feedback */}
        {openError && (
          <div className="mb-3 px-4 py-2.5 bg-red-50 border border-red-300 rounded-xl text-sm text-red-700 flex items-center justify-between">
            <span>{openError}</span>
            <button onClick={() => setOpenError(null)} className="ml-3 text-red-400 hover:text-red-600">✕</button>
          </div>
        )}

        {/* Session list */}
        {loadingSessions ? (
          <p className="text-sm text-slate-400">Loading sessions…</p>
        ) : sessions.length === 0 ? (
          <div className="text-center py-16 bg-white rounded-2xl border border-slate-200">
            <ClipboardList size={40} className="text-slate-300 mx-auto mb-3" />
            <p className="text-slate-500 font-medium">No sessions yet</p>
            <p className="text-slate-400 text-sm mt-1">Click "New Session" to start a duty collection report</p>
          </div>
        ) : visibleDates.length === 0 ? (
          <div className="text-center py-12 bg-white rounded-2xl border border-slate-200">
            <Calendar size={36} className="text-slate-300 mx-auto mb-3" />
            <p className="text-slate-500 font-medium">No sessions on {fmtDate(filterDate)}</p>
            <button onClick={() => setFilterDate('')} className="mt-2 text-sm text-teal-600 hover:underline">
              Clear filter to see all dates
            </button>
          </div>
        ) : (
          <div className="space-y-3">
            {visibleDates.map(date => {
              const daySessions = dateMap[date];
              const firstSession = daySessions[0];
              return (
                <div key={date} className="bg-white rounded-2xl border border-slate-200 overflow-hidden">
                  {/* Date group header */}
                  <div className="px-5 py-3 bg-slate-50 border-b border-slate-200 flex items-center gap-2">
                    <Calendar size={14} className="text-slate-500" />
                    <span className="text-sm font-bold text-slate-700 flex-1">{fmtDate(date)}</span>
                    <button
                      onClick={e => downloadRevenue(firstSession, e)}
                      className="flex items-center gap-1 px-3 py-1 text-xs font-semibold bg-violet-600 hover:bg-violet-700 text-white rounded-lg"
                      title={`Download combined Revenue Report for ${fmtDate(date)} (both shifts)`}
                    >
                      <Download size={11} /> Revenue
                    </button>
                  </div>

                  {/* Sessions for this date */}
                  <div className="divide-y divide-slate-100">
                    {daySessions.map(s => (
                      <div key={s.id} className="flex items-center gap-4 px-5 py-4 hover:bg-slate-50 transition-colors group">
                        {/* Shift icon */}
                        <div className={`p-2 rounded-xl shrink-0 ${s.shift === 'DAY' ? 'bg-amber-100' : 'bg-indigo-100'}`}>
                          {s.shift === 'DAY'
                            ? <Sun size={18} className="text-amber-600" />
                            : <Moon size={18} className="text-indigo-600" />
                          }
                        </div>

                        {/* Session info */}
                        <button className="flex-1 min-w-0 text-left" onClick={() => openSession(s)}>
                          <p className="text-sm font-semibold text-slate-800">
                            {s.shift} Shift · {s.batch_name}
                          </p>
                          <p className="text-xs text-slate-500 mt-0.5">
                            Created {s.created_at ? new Date(s.created_at).toLocaleString() : '—'}
                            {s.tariff && ` · Tariff: ${s.tariff.label ?? s.tariff.effective_from}`}
                          </p>
                          {/* Challan number badge with edit button */}
                          {s.challan_no ? (
                            <p className="text-xs text-teal-700 mt-0.5 font-medium flex items-center gap-1">
                              Challan: {s.challan_no}
                              <button
                                onClick={e => { e.stopPropagation(); setEditChallanTarget(s); }}
                                title="Edit challan number"
                                className="text-teal-500 hover:text-teal-700 p-0.5"
                              >
                                <Pencil size={10} />
                              </button>
                            </p>
                          ) : (
                            <p className="text-xs text-amber-600 mt-0.5">
                              No challan — will be prompted on ADC download
                            </p>
                          )}
                          {s.submitted_at && (
                            <p className="text-xs text-emerald-600 mt-0.5 flex items-center gap-1">
                              <CheckCircle size={10} />
                              Submitted by {s.submitted_by} on {new Date(s.submitted_at).toLocaleString()}
                            </p>
                          )}
                        </button>

                        {/* Actions */}
                        <div className="flex items-center gap-2 shrink-0">
                          <button
                            onClick={e => downloadAdc(s, e)}
                            className="flex items-center gap-1 px-2.5 py-1 text-xs font-semibold bg-blue-600 hover:bg-blue-700 text-white rounded-lg"
                            title={`Download ADC Report — ${s.shift} shift`}
                          >
                            <Download size={11} /> ADC
                          </button>
                          {s.submitted_at
                            ? <span className="text-xs text-emerald-600 font-semibold bg-emerald-50 px-2 py-1 rounded-lg">✓ Submitted</span>
                            : (
                              <button
                                onClick={() => openSession(s)}
                                className="text-xs text-teal-600 font-semibold group-hover:underline px-2 py-1"
                              >
                                Open →
                              </button>
                            )
                          }
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
