/* eslint-disable @typescript-eslint/no-explicit-any */
import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { Gavel, AlertCircle, RefreshCw, ChevronLeft, ChevronRight } from 'lucide-react';
import api from '@/lib/api';

const PER_PAGE = 20;

const fmtDate = (d: string | null | undefined): string => {
  if (!d) return '—';
  const parts = d.split('-');
  if (parts.length === 3) return `${parts[2]}-${parts[1]}-${parts[0]}`;
  return d;
};

export default function OfflineAdjudicationList() {
  const navigate = useNavigate();
  const [cases, setCases] = useState<any[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [errorMsg, setErrorMsg] = useState('');

  const fetchCases = useCallback(async (p: number) => {
    setLoading(true);
    setErrorMsg('');
    try {
      const res = await api.get('/os/offline-pending', { params: { page: p, per_page: PER_PAGE } });
      setCases(res.data.items ?? []);
      setTotal(res.data.total ?? 0);
    } catch (err: any) {
      const status = err.response?.status;
      if (!err.response) {
        setErrorMsg('Cannot connect to server. Please ensure the backend is running.');
      } else if (status === 403) {
        setErrorMsg('Access denied. Only DC/AC role can access adjudication.');
      } else {
        let detail = err.response?.data?.detail || `Server error (${status || 'unknown'}). Please try refreshing.`;
        if (Array.isArray(detail)) detail = detail.map((e: any) => `${e.loc?.join('.')} - ${e.msg}`).join(', ');
        else if (typeof detail === 'object') detail = JSON.stringify(detail);
        setErrorMsg(detail);
      }
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchCases(1); }, [fetchCases]);

  const handlePageChange = (newPage: number) => {
    setPage(newPage);
    fetchCases(newPage);
  };

  const totalPages = Math.max(1, Math.ceil(total / PER_PAGE));
  const start = (page - 1) * PER_PAGE + 1;
  const end = Math.min(page * PER_PAGE, total);

  return (
    <div className="space-y-6 flex flex-col max-w-7xl mx-auto pt-2 pb-12">
      {/* Header */}
      <div className="flex justify-between items-center bg-amber-800 text-white p-5 rounded-xl shadow-md border border-amber-700">
        <div>
          <h1 className="text-xl font-bold tracking-tight">Pending Offline Adjudication</h1>
          <p className="text-amber-200 text-sm mt-0.5">
            {loading
              ? 'Loading...'
              : total > 0
              ? `${total} case(s) awaiting officer details`
              : 'No pending offline cases found.'}
          </p>
        </div>
        <button
          onClick={() => { setPage(1); fetchCases(1); }}
          className="flex items-center gap-2 bg-amber-700 hover:bg-amber-600 border border-amber-500 px-4 py-2 rounded-lg text-sm transition-colors"
        >
          <RefreshCw size={15} className={loading ? 'animate-spin' : ''} /> Refresh
        </button>
      </div>

      {errorMsg && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg flex items-start">
          <AlertCircle className="shrink-0 mr-3 mt-0.5" size={20} />
          <p className="text-sm">{errorMsg}</p>
        </div>
      )}

      {/* Table */}
      <div className="bg-white rounded-xl flex-1 flex flex-col border border-slate-200">
        <div className="w-full relative">
          <table className="w-full text-sm text-left">
            <thead className="text-xs text-amber-800 uppercase bg-amber-50 border-b border-amber-200 sticky top-0 z-10">
              <tr>
                <th className="px-5 py-4 font-bold tracking-wider">O.S. Ref</th>
                <th className="px-5 py-4 font-bold tracking-wider">Date</th>
                <th className="px-5 py-4 font-bold tracking-wider">Passenger Name</th>
                <th className="px-5 py-4 font-bold tracking-wider">Flight / Passport</th>
                <th className="px-5 py-4 font-bold tracking-wider text-right">Value (₹)</th>
                <th className="px-5 py-4 font-bold tracking-wider text-center w-32">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {loading ? (
                <tr>
                  <td colSpan={6} className="text-center py-12 text-slate-500">
                    <div className="flex flex-col items-center justify-center space-y-3">
                      <RefreshCw className="animate-spin text-amber-500" size={28} />
                      <span className="font-medium">Loading cases...</span>
                    </div>
                  </td>
                </tr>
              ) : cases.length === 0 ? (
                <tr>
                  <td colSpan={6} className="text-center py-12 text-slate-500">
                    <div className="flex flex-col items-center justify-center space-y-2">
                      <Gavel size={32} className="text-amber-200" />
                      <span className="font-medium">No pending offline cases found.</span>
                      <span className="text-xs text-slate-400">
                        Cases registered via offline adjudication will appear here once the officer details are missing.
                      </span>
                    </div>
                  </td>
                </tr>
              ) : (
                cases.map((row, idx) => (
                  <tr key={`${row.os_no}-${row.os_year}-${idx}`} className="hover:bg-amber-50 group">
                    <td className="px-5 py-3 align-middle">
                      <div className="font-bold text-amber-800">{row.os_no}/{row.os_year}</div>
                      <span className="inline-flex items-center mt-1 px-2 py-0.5 text-[10px] font-bold rounded bg-purple-100 text-purple-700 border border-purple-200 uppercase tracking-wide">
                        OFFLINE ADJ
                      </span>
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
                      <div className="font-bold text-slate-800">
                        {(row.total_items_value || 0).toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                      </div>
                      <div className="text-xs text-slate-400 mt-0.5">{row.total_items || 0} item(s)</div>
                    </td>
                    <td className="px-5 py-3 align-middle text-center">
                      <button
                        onClick={() => navigate(`/adjudication/offline-case/${row.os_no}/${row.os_year}`)}
                        className="inline-flex items-center gap-1.5 bg-amber-700 text-white text-xs font-semibold px-3 py-1.5 rounded-lg hover:bg-amber-600 transition-colors opacity-80 group-hover:opacity-100"
                      >
                        <Gavel size={13} /> Complete
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Footer: count + pagination */}
        {!loading && total > 0 && (
          <div className="bg-slate-50 border-t border-slate-200 px-4 py-3 flex items-center justify-between text-sm text-slate-500">
            <span className="font-medium">
              Showing {start}–{end} of {total} case{total !== 1 ? 's' : ''}
            </span>
            {totalPages > 1 && (
              <div className="flex items-center gap-1">
                <button
                  onClick={() => handlePageChange(page - 1)}
                  disabled={page === 1}
                  className="p-1.5 rounded hover:bg-slate-200 disabled:opacity-40 disabled:cursor-not-allowed"
                >
                  <ChevronLeft size={16} />
                </button>
                {Array.from({ length: totalPages }, (_, i) => i + 1)
                  .filter(p => p === 1 || p === totalPages || Math.abs(p - page) <= 2)
                  .reduce<(number | '...')[]>((acc, p, i, arr) => {
                    if (i > 0 && p - (arr[i - 1] as number) > 1) acc.push('...');
                    acc.push(p);
                    return acc;
                  }, [])
                  .map((p, i) =>
                    p === '...' ? (
                      <span key={`ellipsis-${i}`} className="px-1 text-slate-400">…</span>
                    ) : (
                      <button
                        key={p}
                        onClick={() => handlePageChange(p as number)}
                        className={`min-w-[2rem] px-2 py-1 rounded text-xs font-semibold transition-colors ${
                          page === p
                            ? 'bg-amber-700 text-white'
                            : 'hover:bg-slate-200 text-slate-600'
                        }`}
                      >
                        {p}
                      </button>
                    )
                  )}
                <button
                  onClick={() => handlePageChange(page + 1)}
                  disabled={page === totalPages}
                  className="p-1.5 rounded hover:bg-slate-200 disabled:opacity-40 disabled:cursor-not-allowed"
                >
                  <ChevronRight size={16} />
                </button>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
