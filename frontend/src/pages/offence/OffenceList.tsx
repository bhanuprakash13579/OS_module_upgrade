import { useState, useEffect, useCallback, useRef, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { Plus, Search, Filter, AlertCircle, RefreshCw, Trash2, X, FileText, CreditCard, ChevronDown, ChevronUp } from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';
import api from '@/lib/api';
import DatePicker from '@/components/DatePicker';

const PER_PAGE = 20;

const fmtDate = (d: string | null | undefined): string => {
  if (!d) return '—';
  const parts = d.split('-');
  if (parts.length === 3) return `${parts[2]}-${parts[1]}-${parts[0]}`;
  return d;
};

interface BrEntry { no: string; date: string; }
interface BrDrData { brEntries: BrEntry[]; drNo: string; drDate: string; }

// Parse stored BR JSON string from backend into display-friendly list
function parseBrEntries(raw: string | null | undefined): BrEntry[] {
  if (!raw) return [];
  try { return JSON.parse(raw); } catch { return []; }
}

export default function OffenceList() {
  const navigate = useNavigate();
  const { token: _token } = useAuth();

  const [cases, setCases] = useState<any[]>([]);
  const [total, setTotal] = useState(0);
  const [currentPage, setCurrentPage] = useState(1);
  const [searchTerm, setSearchTerm] = useState('');
  const [loading, setLoading] = useState(true);
  const [errorMsg, setErrorMsg] = useState('');
  const [showFilter, setShowFilter] = useState(false);
  const [filterYear, setFilterYear] = useState('');
  const [filterStatus, setFilterStatus] = useState('');
  const [filterBrDrPending, setFilterBrDrPending] = useState(false);

  // BR/DR inline edit state
  const [expandedBrDr, setExpandedBrDr] = useState<string | null>(null);
  const [brDrData, setBrDrData] = useState<BrDrData>({ brEntries: [{ no: '', date: '' }], drNo: '', drDate: '' });
  const [brDrSaving, setBrDrSaving] = useState(false);
  const [brDrError, setBrDrError] = useState('');

  const searchDebounce = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);
  useEffect(() => () => clearTimeout(searchDebounce.current), []);

  const fetchCases = useCallback(async (
    page: number,
    search: string,
    year = filterYear,
    status = filterStatus,
    brDrPending = filterBrDrPending,
  ) => {
    setLoading(true);
    setErrorMsg('');
    try {
      const params: Record<string, any> = { page, per_page: PER_PAGE, search: search.trim() };
      if (year) params.year = year;
      if (status) params.status = status;
      if (brDrPending) params.br_dr_pending = true;
      const res = await api.get('/os/', { params });
      setCases(res.data.items);
      setTotal(res.data.total);
    } catch (err: any) {
      setErrorMsg(err.message);
    } finally {
      setLoading(false);
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filterYear, filterStatus, filterBrDrPending]);

  // Initial load + re-load on login/logout
  useEffect(() => {
    fetchCases(1, '');
    setCurrentPage(1);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [_token]);

  // Debounced search: wait 400ms after typing stops, then fetch page 1
  const handleSearchChange = (value: string) => {
    setSearchTerm(value);
    clearTimeout(searchDebounce.current);
    searchDebounce.current = setTimeout(() => {
      setCurrentPage(1);
      fetchCases(1, value);
    }, 400);
  };

  const handlePageChange = (newPage: number) => {
    setCurrentPage(newPage);
    fetchCases(newPage, searchTerm);
  };

  const handleApplyFilter = () => {
    setCurrentPage(1);
    fetchCases(1, searchTerm, filterYear, filterStatus, filterBrDrPending);
    setShowFilter(false);
  };

  const handleClearFilter = () => {
    setFilterYear('');
    setFilterStatus('');
    setFilterBrDrPending(false);
    setCurrentPage(1);
    fetchCases(1, searchTerm, '', '', false);
    setShowFilter(false);
  };

  const currentYear = new Date().getFullYear();
  const yearOptions = useMemo(
    () => Array.from({ length: currentYear - 1989 }, (_, i) => currentYear - i),
    [currentYear]
  );

  const handleDelete = async (os_no: string, os_year: number, is_draft: string) => {
    const label = is_draft === 'Y' ? 'DRAFT' : 'PENDING';
    const reason = window.prompt(
      `Delete ${label} O.S. ${os_no}/${os_year}?\n\nEnter reason for deletion (minimum 5 characters):`
    );
    if (!reason) return;                              // user cancelled
    if (reason.trim().length < 5) {
      setErrorMsg('Reason must be at least 5 characters. Deletion cancelled.');
      return;
    }
    try {
      await api.delete(`/os/${os_no}/${os_year}`, { params: { reason: reason.trim() } });
      fetchCases(currentPage, searchTerm);
    } catch (err: any) {
      const detail = err.response?.data?.detail || err.message;
      setErrorMsg(`Deletion failed: ${detail}`);
    }
  };

  // Open BR/DR edit panel for a row, pre-populating from existing data
  const openBrDr = (row: any) => {
    const key = `${row.os_no}-${row.os_year}`;
    if (expandedBrDr === key) {
      setExpandedBrDr(null);
      return;
    }
    const stored = parseBrEntries(row.post_adj_br_entries);
    setBrDrData({
      brEntries: stored.length ? stored : [{ no: '', date: '' }],
      drNo: row.post_adj_dr_no || '',
      drDate: row.post_adj_dr_date || '',
    });
    setBrDrError('');
    setExpandedBrDr(key);
  };

  const addBrEntry = () => setBrDrData(d => ({ ...d, brEntries: [...d.brEntries, { no: '', date: '' }] }));
  const removeBrEntry = (idx: number) => setBrDrData(d => ({ ...d, brEntries: d.brEntries.filter((_, i) => i !== idx) }));
  const updateBrEntry = (idx: number, field: 'no' | 'date', val: string) =>
    setBrDrData(d => ({ ...d, brEntries: d.brEntries.map((e, i) => i === idx ? { ...e, [field]: val } : e) }));

  const saveBrDr = async (os_no: string, os_year: number) => {
    setBrDrSaving(true);
    setBrDrError('');
    try {
      const payload = {
        br_entries: brDrData.brEntries
          .filter(e => e.no.trim())
          .map(e => ({ no: e.no.trim(), date: e.date || null })),
        dr_no: brDrData.drNo.trim() || null,
        dr_date: brDrData.drDate || null,
      };
      await api.patch(`/os/${os_no}/${os_year}/post-adj`, payload);
      setExpandedBrDr(null);
      fetchCases(currentPage, searchTerm);
    } catch (err: any) {
      setBrDrError(err.response?.data?.detail || err.message);
    } finally {
      setBrDrSaving(false);
    }
  };

  const totalPages = Math.ceil(total / PER_PAGE) || 1;
  const showing = {
    from: total === 0 ? 0 : (currentPage - 1) * PER_PAGE + 1,
    to: Math.min(currentPage * PER_PAGE, total),
  };

  const activeFilterCount = [filterYear, filterStatus, filterBrDrPending ? 'br' : ''].filter(Boolean).length;

  return (
    <div className="space-y-6 h-full flex flex-col max-w-7xl mx-auto pt-2">
      {/* Header */}
      <div className="flex justify-between items-center bg-white p-5 rounded-xl border border-slate-200">
        <div>
          <h1 className="text-2xl font-bold text-slate-800 tracking-tight">Offence Cases (O.S.) Register</h1>
          <p className="text-sm text-slate-500 mt-1">
            {total > 0 ? `${total.toLocaleString()} total cases` : 'Track passenger interceptions, seizures, and adjudications.'}
          </p>
        </div>
        <button
          onClick={() => navigate('/sdo/offence/new')}
          className="flex items-center px-5 py-2.5 bg-brand-600 text-white font-medium rounded-lg hover:bg-brand-700 transition-colors"
        >
          <Plus size={18} className="mr-2" />
          Register New O.S.
        </button>
      </div>

      {/* Search + actions */}
      <div className="bg-white p-4 rounded-xl border border-slate-200 flex-shrink-0">
        <div className="flex flex-col md:flex-row gap-4 items-center justify-between">
          <div className="flex-1 w-full relative max-w-md">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <Search className="h-5 w-5 text-slate-400" />
            </div>
            <input
              type="text"
              className="w-full pl-10 pr-4 py-2 border border-slate-300 rounded-lg bg-slate-50 focus:bg-white focus:ring-2 focus:ring-brand-500 focus:border-brand-500 transition-colors text-sm"
              placeholder="Search by O.S. No, Pax Name, Passport or Flight..."
              value={searchTerm}
              onChange={e => handleSearchChange(e.target.value)}
            />
          </div>
          <div className="flex gap-3 w-full md:w-auto">
            <button onClick={() => fetchCases(currentPage, searchTerm)} className="px-4 py-2 border border-slate-300 rounded-lg bg-white text-slate-700 font-medium flex items-center hover:bg-slate-50 transition-colors">
              <RefreshCw size={16} className={`mr-2 ${loading ? 'animate-spin text-brand-500' : 'text-slate-500'}`} /> Sync
            </button>
            <button
              onClick={() => setShowFilter(f => !f)}
              className={`px-4 py-2 border rounded-lg font-medium flex items-center transition-colors ${activeFilterCount > 0 ? 'border-brand-400 bg-brand-50 text-brand-700 hover:bg-brand-100' : 'border-slate-300 bg-white text-slate-700 hover:bg-slate-50'}`}
            >
              <Filter size={16} className="mr-2" /> Filter
              {activeFilterCount > 0 && <span className="ml-1.5 bg-brand-600 text-white text-xs rounded-full px-1.5 py-0.5 leading-none">
                {activeFilterCount}
              </span>}
            </button>
          </div>
        </div>

        {/* Filter panel */}
        {showFilter && (
          <div className="mt-4 pt-4 border-t border-slate-200">
            <div className="flex flex-wrap gap-4 items-end">
              <div className="flex flex-col gap-1">
                <label className="text-xs font-semibold text-slate-500 uppercase tracking-wide">Year</label>
                <select
                  value={filterYear}
                  onChange={e => setFilterYear(e.target.value)}
                  className="px-3 py-2 border border-slate-300 rounded-lg bg-slate-50 text-sm text-slate-700 focus:ring-2 focus:ring-brand-500 focus:border-brand-500"
                >
                  <option value="">All Years</option>
                  {yearOptions.map(y => <option key={y} value={y}>{y}</option>)}
                </select>
              </div>
              <div className="flex flex-col gap-1">
                <label className="text-xs font-semibold text-slate-500 uppercase tracking-wide">Status</label>
                <select
                  value={filterStatus}
                  onChange={e => setFilterStatus(e.target.value)}
                  className="px-3 py-2 border border-slate-300 rounded-lg bg-slate-50 text-sm text-slate-700 focus:ring-2 focus:ring-brand-500 focus:border-brand-500"
                >
                  <option value="">All</option>
                  <option value="draft">Draft</option>
                  <option value="pending">Pending</option>
                  <option value="adjudicated">Adjudicated</option>
                </select>
              </div>
              {/* BR/DR Pending toggle */}
              <div className="flex flex-col gap-1">
                <label className="text-xs font-semibold text-slate-500 uppercase tracking-wide">BR/DR</label>
                <button
                  type="button"
                  onClick={() => setFilterBrDrPending(v => !v)}
                  className={`px-3 py-2 border rounded-lg text-sm font-medium transition-colors flex items-center gap-1.5 ${
                    filterBrDrPending
                      ? 'border-amber-400 bg-amber-50 text-amber-800'
                      : 'border-slate-300 bg-slate-50 text-slate-600 hover:bg-white'
                  }`}
                >
                  <CreditCard size={14} />
                  {filterBrDrPending ? 'Pending Only ✓' : 'BR/DR Pending'}
                </button>
              </div>
              <div className="flex gap-2">
                <button
                  onClick={handleApplyFilter}
                  className="px-4 py-2 bg-brand-600 text-white font-medium rounded-lg hover:bg-brand-700 transition-colors text-sm"
                >
                  Apply
                </button>
                <button
                  onClick={handleClearFilter}
                  className="px-4 py-2 border border-slate-300 bg-white text-slate-600 font-medium rounded-lg hover:bg-slate-50 transition-colors text-sm flex items-center"
                >
                  <X size={14} className="mr-1" /> Clear
                </button>
              </div>
            </div>
          </div>
        )}
      </div>

      {errorMsg && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg flex items-start mx-1">
          <AlertCircle className="shrink-0 mr-3 mt-0.5" size={20} />
          <div>
            <h4 className="font-bold text-sm">Error Loading Records</h4>
            <p className="text-sm">{errorMsg}</p>
          </div>
        </div>
      )}

      {/* Table */}
      <div className="bg-white rounded-xl flex-1 overflow-hidden flex flex-col border border-slate-200 relative">
        <div className="overflow-auto overscroll-contain flex-1">
          <table className="w-full text-sm text-left">
            <thead className="text-xs text-slate-500 uppercase bg-slate-50 border-b border-slate-200 sticky top-0 z-10">
              <tr>
                <th className="px-5 py-4 font-bold tracking-wider">O.S. Ref</th>
                <th className="px-5 py-4 font-bold tracking-wider">Date</th>
                <th className="px-5 py-4 font-bold tracking-wider">Passenger Name</th>
                <th className="px-5 py-4 font-bold tracking-wider">Flight / PPN</th>
                <th className="px-5 py-4 font-bold tracking-wider text-right">Appraised Value (₹)</th>
                <th className="px-5 py-4 font-bold tracking-wider text-center">Status</th>
                <th className="px-5 py-4 font-bold tracking-wider text-center w-44">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {loading ? (
                <tr>
                  <td colSpan={7} className="text-center py-12 text-slate-500">
                    <div className="flex flex-col items-center justify-center space-y-3">
                      <RefreshCw className="animate-spin text-brand-500" size={28} />
                      <span className="font-medium">Syncing with local database...</span>
                    </div>
                  </td>
                </tr>
              ) : cases.length === 0 ? (
                <tr>
                  <td colSpan={7} className="text-center py-12 text-slate-500">
                    <div className="flex flex-col items-center justify-center space-y-2">
                      <FileText size={32} className="text-slate-300" />
                      <span className="font-medium">No offence cases found.</span>
                      <span className="text-xs">Try adjusting your search query or register a new OS.</span>
                    </div>
                  </td>
                </tr>
              ) : (
                cases.map((row, idx) => {
                  // IMPORTANT: Must match backend _pending_filters() in offence.py.
                  // A case is adjudicated if EITHER adjudication_date or adj_offr_name is set.
                  const isAdjudicated = !!(row.adjudication_date || row.adj_offr_name);
                  const totalValue = row.total_items_value || 0;
                  const rowKey = `${row.os_no}-${row.os_year}`;
                  const isExpanded = expandedBrDr === rowKey;
                  const hasBrDr = !!(row.post_adj_br_entries || row.post_adj_dr_no);
                  return (
                    <>
                      <tr key={`${rowKey}-${idx}`} className={`hover:bg-slate-50 group ${isExpanded ? 'bg-amber-50/40' : ''}`}>
                        <td className="px-5 py-3 align-middle">
                          <div className="font-bold text-brand-700">{row.os_no}/{row.os_year}</div>
                          <div className="text-xs text-slate-400 mt-0.5">{row.location_code || 'CHN'}</div>
                          {row.is_offline_adjudication === 'Y' && (
                            <span className="inline-flex items-center mt-0.5 px-1.5 py-0.5 text-[10px] font-semibold rounded bg-purple-100 text-purple-700 border border-purple-200">
                              OFFLINE ADJ
                            </span>
                          )}
                        </td>
                        <td className="px-5 py-3 align-middle font-medium text-slate-600">{fmtDate(row.os_date)}</td>
                        <td className="px-5 py-3 align-middle">
                          <div className="font-bold text-slate-800">{row.pax_name || 'UNKNOWN'}</div>
                          <div className="text-xs text-slate-500 mt-0.5">{row.pax_nationality}</div>
                        </td>
                        <td className="px-5 py-3 align-middle">
                          <div className="text-slate-700 font-medium">{row.flight_no || 'N/A'}</div>
                          <div className="text-xs text-slate-500 mt-0.5 font-mono">{row.passport_no || 'N/A'}</div>
                        </td>
                        <td className="px-5 py-3 align-middle text-right">
                          <div className="font-bold text-slate-800">{totalValue.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</div>
                          <div className="text-xs text-slate-400 mt-0.5">{row.total_items || row.items?.length || 0} item(s)</div>
                        </td>
                        <td className="px-5 py-3 align-middle text-center">
                          <span className={`inline-flex items-center px-2.5 py-1 text-xs font-bold rounded-md border ${
                            isAdjudicated
                              ? 'text-emerald-700 bg-emerald-50 border-emerald-200'
                              : row.is_draft === 'Y'
                                ? 'text-slate-600 bg-slate-100 border-slate-300'
                                : 'text-blue-700 bg-blue-50 border-blue-200'
                          }`}>
                            {isAdjudicated ? 'ADJUDICATED' : (row.is_draft === 'Y' ? 'DRAFT' : 'PENDING')}
                          </span>
                          {isAdjudicated && hasBrDr && (
                            <div className="mt-1">
                              <span className="inline-flex items-center gap-0.5 px-1.5 py-0.5 text-[10px] font-semibold text-amber-700 bg-amber-50 border border-amber-200 rounded">
                                <CreditCard size={9} /> BR/DR
                              </span>
                            </div>
                          )}
                        </td>
                        <td className="px-5 py-3 align-middle text-center">
                          <div className="flex justify-center items-center gap-1.5 opacity-60 group-hover:opacity-100 transition-opacity">
                            {isAdjudicated ? (
                              <div className="flex items-center gap-1.5">
                                <button
                                  onClick={() => navigate(`/sdo/offence/${row.os_no}/${row.os_year}/view`)}
                                  className="px-3 py-1.5 text-xs font-bold text-white bg-slate-600 hover:bg-slate-700 rounded-md transition-colors"
                                >
                                  View
                                </button>
                                <button
                                  onClick={() => openBrDr(row)}
                                  title="Add / Edit BR & DR Receipt Details"
                                  className={`px-2.5 py-1.5 text-xs font-bold rounded-md transition-colors flex items-center gap-1 ${
                                    isExpanded
                                      ? 'text-amber-800 bg-amber-100 border border-amber-300'
                                      : 'text-amber-700 bg-amber-50 border border-amber-200 hover:bg-amber-100'
                                  }`}
                                >
                                  <CreditCard size={12} />
                                  BR/DR
                                  {isExpanded ? <ChevronUp size={11} /> : <ChevronDown size={11} />}
                                </button>
                              </div>
                            ) : (
                              <div className="flex items-center gap-1.5">
                                <button
                                  onClick={() => navigate(`/sdo/offence/${row.os_no}/${row.os_year}/edit`)}
                                  title={row.is_draft === 'Y' ? 'Edit Draft' : 'Edit Pending Case'}
                                  className="px-3 py-1.5 text-xs font-bold text-slate-600 hover:text-brand-700 hover:bg-brand-50 border border-slate-200 hover:border-brand-200 rounded-md transition-colors"
                                >
                                  Edit
                                </button>
                                <button
                                  onClick={() => handleDelete(row.os_no, row.os_year, row.is_draft)}
                                  title={row.is_draft === 'Y' ? 'Delete Draft' : 'Delete Pending Case'}
                                  className="px-3 py-1.5 text-xs font-bold text-red-600 hover:text-red-800 hover:bg-red-50 border border-slate-200 hover:border-red-200 rounded-md transition-colors flex items-center"
                                >
                                  <Trash2 size={14} className="mr-1" /> Delete
                                </button>
                              </div>
                            )}
                          </div>
                        </td>
                      </tr>

                      {/* BR/DR inline edit sub-row */}
                      {isExpanded && (
                        <tr key={`${rowKey}-brdr`} className="bg-amber-50/60">
                          <td colSpan={7} className="px-6 py-4">
                            <div className="border border-amber-200 rounded-lg bg-white p-4 space-y-4">
                              <div className="flex items-center justify-between">
                                <h3 className="text-sm font-bold text-amber-900 flex items-center gap-2">
                                  <CreditCard size={15} />
                                  Post-Adjudication Receipt Details — {row.os_no}/{row.os_year}
                                </h3>
                                <button type="button" onClick={() => setExpandedBrDr(null)} className="text-slate-400 hover:text-slate-600">
                                  <X size={16} />
                                </button>
                              </div>

                              {/* Bank Receipt entries */}
                              <div>
                                <label className="text-xs font-semibold text-slate-600 uppercase tracking-wide mb-2 block">
                                  Bank Receipt(s) (BR)
                                </label>
                                <div className="space-y-2">
                                  {brDrData.brEntries.map((entry, i) => (
                                    <div key={i} className="flex items-center gap-2">
                                      <input
                                        type="text"
                                        placeholder="BR No."
                                        value={entry.no}
                                        onChange={e => updateBrEntry(i, 'no', e.target.value)}
                                        className="w-44 px-2.5 py-1.5 border border-slate-300 rounded-md text-sm bg-slate-50 focus:bg-white focus:ring-1 focus:ring-amber-400 focus:border-amber-400"
                                      />
                                      <div className="w-44">
                                        <DatePicker
                                          value={entry.date}
                                          onChange={val => updateBrEntry(i, 'date', val)}
                                          placeholder="BR Date"
                                          inputClassName="w-full px-2.5 py-1.5 border border-slate-300 rounded-md text-sm bg-slate-50 focus:bg-white focus:ring-1 focus:ring-amber-400 focus:border-amber-400"
                                        />
                                      </div>
                                      {brDrData.brEntries.length > 1 && (
                                        <button type="button" onClick={() => removeBrEntry(i)} className="text-red-400 hover:text-red-600 p-1">
                                          <X size={14} />
                                        </button>
                                      )}
                                    </div>
                                  ))}
                                </div>
                                <button
                                  type="button"
                                  onClick={addBrEntry}
                                  className="mt-2 text-xs text-amber-700 hover:text-amber-900 font-medium flex items-center gap-1"
                                >
                                  <Plus size={12} /> Add another BR
                                </button>
                              </div>

                              {/* DR entry */}
                              <div>
                                <label className="text-xs font-semibold text-slate-600 uppercase tracking-wide mb-2 block">
                                  Detention Receipt (DR)
                                </label>
                                <div className="flex items-center gap-2">
                                  <input
                                    type="text"
                                    placeholder="DR No."
                                    value={brDrData.drNo}
                                    onChange={e => setBrDrData(d => ({ ...d, drNo: e.target.value }))}
                                    className="w-44 px-2.5 py-1.5 border border-slate-300 rounded-md text-sm bg-slate-50 focus:bg-white focus:ring-1 focus:ring-amber-400 focus:border-amber-400"
                                  />
                                  <div className="w-44">
                                    <DatePicker
                                      value={brDrData.drDate}
                                      onChange={val => setBrDrData(d => ({ ...d, drDate: val }))}
                                      placeholder="DR Date"
                                      inputClassName="w-full px-2.5 py-1.5 border border-slate-300 rounded-md text-sm bg-slate-50 focus:bg-white focus:ring-1 focus:ring-amber-400 focus:border-amber-400"
                                    />
                                  </div>
                                </div>
                              </div>

                              {brDrError && (
                                <p className="text-xs text-red-600 font-medium">{brDrError}</p>
                              )}

                              <div className="flex items-center gap-2 pt-1 border-t border-amber-100">
                                <button
                                  type="button"
                                  onClick={() => saveBrDr(row.os_no, row.os_year)}
                                  disabled={brDrSaving}
                                  className="px-4 py-1.5 bg-amber-600 text-white text-xs font-bold rounded-md hover:bg-amber-700 disabled:opacity-50 transition-colors flex items-center gap-1.5"
                                >
                                  {brDrSaving ? <RefreshCw size={12} className="animate-spin" /> : null}
                                  {brDrSaving ? 'Saving…' : 'Save'}
                                </button>
                                <button
                                  type="button"
                                  onClick={() => setExpandedBrDr(null)}
                                  className="px-4 py-1.5 border border-slate-300 bg-white text-slate-600 text-xs font-medium rounded-md hover:bg-slate-50 transition-colors"
                                >
                                  Cancel
                                </button>
                              </div>
                            </div>
                          </td>
                        </tr>
                      )}
                    </>
                  );
                })
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        <div className="bg-slate-50 border-t border-slate-200 p-4 flex justify-between items-center text-sm">
          <span className="text-slate-500 font-medium">
            {total === 0 ? 'No entries' : (
              <>Showing <span className="text-slate-700">{showing.from}–{showing.to}</span> of <span className="text-slate-700">{total.toLocaleString()}</span> cases</>
            )}
          </span>
          <div className="flex space-x-1">
            <button
              onClick={() => handlePageChange(currentPage - 1)}
              disabled={currentPage === 1 || loading}
              className="px-3 py-1.5 border border-slate-300 rounded-md bg-white text-slate-600 font-medium disabled:opacity-40 hover:bg-slate-50"
            >Prev</button>
            <span className="px-3 py-1.5 border border-brand-500 bg-brand-50 text-brand-700 rounded-md font-bold">
              {currentPage} / {totalPages}
            </span>
            <button
              onClick={() => handlePageChange(currentPage + 1)}
              disabled={currentPage === totalPages || loading}
              className="px-3 py-1.5 border border-slate-300 rounded-md bg-white text-slate-600 font-medium disabled:opacity-40 hover:bg-slate-50"
            >Next</button>
          </div>
        </div>
      </div>
    </div>
  );
}
