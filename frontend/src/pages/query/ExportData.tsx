import { useState } from 'react';
import { Download } from 'lucide-react';
import api from '@/lib/api';

export default function ExportData() {
  const [loading, setLoading] = useState(false);
  const [msg, setMsg] = useState('');
  const [error, setError] = useState('');

  const downloadFull = async () => {
    setMsg(''); setError('');
    setLoading(true);
    try {
      const res = await api.get('/backup/export/csv', { responseType: 'blob' });
      const today = new Date().toISOString().slice(0, 10);
      const url = window.URL.createObjectURL(new Blob([res.data], { type: 'application/zip' }));
      const a = document.createElement('a');
      a.href = url;
      a.download = `cops_full_backup_${today}.zip`;
      a.click();
      window.URL.revokeObjectURL(url);
      setMsg(`Backup saved to your Downloads folder as cops_full_backup_${today}.zip — store it safely, it can restore the entire database.`);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Download failed.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-lg mx-auto py-6 space-y-4">
      <div>
        <h1 className="text-lg font-bold text-slate-800">Download Full Backup</h1>
        <p className="text-xs text-slate-500 mt-1">
          Exports every record in the database as a ZIP containing{' '}
          <strong>cops_master.csv</strong> and <strong>cops_items.csv</strong>.
          This ZIP can be restored via the admin panel if the database is ever lost.
        </p>
      </div>
      <button
        type="button"
        disabled={loading}
        onClick={downloadFull}
        className="flex items-center gap-2 px-5 py-2.5 text-sm rounded-lg bg-emerald-600 text-white hover:bg-emerald-700 disabled:opacity-60"
      >
        <Download size={15} />
        {loading ? 'Preparing backup…' : 'Download Full Backup ZIP'}
      </button>
      {error && <p className="text-xs text-red-600">{error}</p>}
      {msg   && <p className="text-xs text-emerald-700">{msg}</p>}
    </div>
  );
}
