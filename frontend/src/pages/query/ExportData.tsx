import { useState } from 'react';
import { Download, Database } from 'lucide-react';
import api from '@/lib/api';
import { showDownloadToast } from '@/components/DownloadToast';

export default function ExportData() {
  const [csvLoading, setCsvLoading] = useState(false);
  const [csvMsg, setCsvMsg] = useState('');
  const [csvError, setCsvError] = useState('');

  const [dbLoading, setDbLoading] = useState(false);
  const [dbMsg, setDbMsg] = useState('');
  const [dbError, setDbError] = useState('');

  const downloadCsv = async () => {
    setCsvMsg(''); setCsvError('');
    setCsvLoading(true);
    try {
      const res = await api.get('/backup/export/csv', { responseType: 'blob' });
      const today = new Date().toISOString().slice(0, 10);
      const defaultName = `cops_full_backup_${today}.zip`;

      try {
        const { save } = await import('@tauri-apps/plugin-dialog');
        const { writeFile } = await import('@tauri-apps/plugin-fs');
        const savePath = await save({ title: 'Save CSV Backup', defaultPath: defaultName, filters: [{ name: 'ZIP', extensions: ['zip'] }] });
        if (savePath) {
          const arrayBuf = await (res.data as Blob).arrayBuffer();
          await writeFile(savePath, new Uint8Array(arrayBuf));
          setCsvMsg(`Backup saved successfully.`);
          showDownloadToast(`Backup saved to ${savePath}`);
        }
      } catch {
        const url = window.URL.createObjectURL(new Blob([res.data], { type: 'application/zip' }));
        const a = document.createElement('a');
        a.href = url; a.download = defaultName; a.click();
        window.URL.revokeObjectURL(url);
        setCsvMsg(`Downloaded successfully.`);
        showDownloadToast(`Downloaded as ${defaultName}`);
      }
    } catch (err: any) {
      setCsvError(err.response?.data?.detail || 'Download failed.');
    } finally {
      setCsvLoading(false);
    }
  };

  const downloadDb = async () => {
    setDbMsg(''); setDbError('');
    setDbLoading(true);
    try {
      const res = await api.get('/backup/export/db', { responseType: 'blob' });
      const today = new Date().toISOString().slice(0, 10);
      const defaultName = `cops_fulldb_${today}.db`;

      try {
        const { save } = await import('@tauri-apps/plugin-dialog');
        const { writeFile } = await import('@tauri-apps/plugin-fs');
        const savePath = await save({ title: 'Save Database Backup', defaultPath: defaultName, filters: [{ name: 'Database', extensions: ['db'] }] });
        if (savePath) {
          const arrayBuf = await (res.data as Blob).arrayBuffer();
          await writeFile(savePath, new Uint8Array(arrayBuf));
          setDbMsg(`Database saved successfully.`);
          showDownloadToast(`Database saved to ${savePath}`);
        }
      } catch {
        const url = window.URL.createObjectURL(new Blob([res.data], { type: 'application/octet-stream' }));
        const a = document.createElement('a');
        a.href = url; a.download = defaultName; a.click();
        window.URL.revokeObjectURL(url);
        setDbMsg(`Downloaded successfully.`);
        showDownloadToast(`Downloaded as ${defaultName}`);
      }
    } catch (err: any) {
      setDbError(err.response?.data?.detail || 'Download failed.');
    } finally {
      setDbLoading(false);
    }
  };

  return (
    <div className="max-w-lg mx-auto py-6 space-y-6">
      <h1 className="text-lg font-bold text-slate-800">Download Backup</h1>

      {/* ── Full SQLite DB (recommended) ── */}
      <div className="border border-slate-200 rounded-lg p-4 space-y-2 bg-white">
        <div className="flex items-center gap-2">
          <Database size={16} className="text-blue-600 shrink-0" />
          <span className="text-sm font-semibold text-slate-800">Full Database Backup <span className="text-xs font-normal text-blue-600 ml-1">Recommended</span></span>
        </div>
        <p className="text-xs text-slate-500">
          Complete snapshot of everything — all OS cases, items, users, shift settings,
          print template headings, baggage rules, statutes, all master tables.
          Uploading this in the admin panel restores the app exactly as it is now on any machine.
        </p>
        <button
          type="button"
          disabled={dbLoading}
          onClick={downloadDb}
          className="flex items-center gap-2 px-4 py-2 text-sm rounded-lg bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-60"
        >
          <Database size={14} />
          {dbLoading ? 'Preparing…' : 'Download SQLite Database (.db)'}
        </button>
        {dbError && <p className="text-xs text-red-600">{dbError}</p>}
        {dbMsg   && <p className="text-xs text-emerald-700">{dbMsg}</p>}
      </div>

      {/* ── CSV ZIP (cases only) ── */}
      <div className="border border-slate-200 rounded-lg p-4 space-y-2 bg-white">
        <div className="flex items-center gap-2">
          <Download size={16} className="text-slate-500 shrink-0" />
          <span className="text-sm font-semibold text-slate-800">OS Cases Only (CSV ZIP)</span>
        </div>
        <p className="text-xs text-slate-500">
          Exports <strong>cops_master.csv</strong> + <strong>cops_items.csv</strong> — OS cases and
          items only. Does not include users, settings, or print template headings.
          Use this for selective migration or sharing data with another system.
        </p>
        <button
          type="button"
          disabled={csvLoading}
          onClick={downloadCsv}
          className="flex items-center gap-2 px-4 py-2 text-sm rounded-lg bg-emerald-600 text-white hover:bg-emerald-700 disabled:opacity-60"
        >
          <Download size={14} />
          {csvLoading ? 'Preparing…' : 'Download Backup ZIP'}
        </button>
        {csvError && <p className="text-xs text-red-600">{csvError}</p>}
        {csvMsg   && <p className="text-xs text-emerald-700">{csvMsg}</p>}
      </div>
    </div>
  );
}
