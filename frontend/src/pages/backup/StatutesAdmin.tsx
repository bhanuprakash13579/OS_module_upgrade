import { useState, useEffect } from 'react';
import { Scale, Pencil, Save, X, ShieldCheck, ShieldAlert } from 'lucide-react';
import api from '@/lib/api';

interface Statute {
  id: number;
  keyword: string;
  display_name: string;
  is_prohibited: boolean;
  supdt_goods_clause: string;
  adjn_goods_clause: string;
  legal_reference: string;
}

export default function StatutesAdmin({ adminToken }: { adminToken: string }) {
  const [statutes, setStatutes] = useState<Statute[]>([]);
  const [loading, setLoading] = useState(true);
  const [editingKey, setEditingKey] = useState<string | null>(null);
  const [editData, setEditData] = useState<Partial<Statute>>({});
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    api.get('/statutes').then(res => {
      setStatutes(res.data);
      setLoading(false);
    });
  }, []);

  const startEdit = (s: Statute) => {
    setEditingKey(s.keyword);
    setEditData({
      display_name: s.display_name,
      is_prohibited: s.is_prohibited,
      supdt_goods_clause: s.supdt_goods_clause,
      adjn_goods_clause: s.adjn_goods_clause,
      legal_reference: s.legal_reference,
    });
  };

  const cancelEdit = () => {
    setEditingKey(null);
    setEditData({});
  };

  const saveEdit = async () => {
    if (!editingKey) return;
    setSaving(true);
    try {
      await api.put(`/statutes/${editingKey}`, editData, {
        headers: { Authorization: `Bearer ${adminToken}` },
      });
      setStatutes(prev => prev.map(s => s.keyword === editingKey ? { ...s, ...editData } as Statute : s));
      setEditingKey(null);
      setEditData({});
    } catch (err) {
      import.meta.env.DEV && console.error('Failed to save statute', err);
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return <div className="text-center py-8 text-slate-500 text-sm">Loading statutes...</div>;
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-lg font-bold text-slate-800 flex items-center">
            <Scale className="mr-2 text-indigo-600" size={20} /> Legal Statutes & Compliance
          </h3>
          <p className="text-xs text-slate-500 mt-0.5">
            Manage the legal clauses used by the Smart Remarks Auto-Generator. Changes apply immediately to new OS cases.
          </p>
        </div>
      </div>

      {statutes.map(s => (
        <div key={s.keyword} className="border border-slate-200 rounded-xl overflow-hidden bg-white shadow-sm">
          {/* Header */}
          <div className="flex items-center justify-between px-4 py-3 bg-slate-50 border-b border-slate-200">
            <div className="flex items-center gap-2">
              <span className="text-sm font-bold text-slate-800">{s.display_name}</span>
              <span className="text-[10px] font-mono px-1.5 py-0.5 bg-slate-200 text-slate-600 rounded">{s.keyword}</span>
              {s.is_prohibited ? (
                <span className="text-[10px] px-1.5 py-0.5 bg-red-100 text-red-700 border border-red-200 rounded font-bold flex items-center gap-0.5">
                  <ShieldAlert size={10} /> PROHIBITED
                </span>
              ) : (
                <span className="text-[10px] px-1.5 py-0.5 bg-green-100 text-green-700 border border-green-200 rounded font-bold flex items-center gap-0.5">
                  <ShieldCheck size={10} /> DUTIABLE
                </span>
              )}
            </div>
            {editingKey !== s.keyword ? (
              <button
                onClick={() => startEdit(s)}
                className="text-[11px] px-2 py-1 bg-white border border-slate-300 text-slate-600 rounded hover:bg-slate-50 flex items-center gap-1 font-semibold"
              >
                <Pencil size={12} /> Edit
              </button>
            ) : (
              <div className="flex items-center gap-1.5">
                <button
                  onClick={saveEdit}
                  disabled={saving}
                  className="text-[11px] px-2 py-1 bg-brand-600 text-white rounded hover:bg-brand-700 flex items-center gap-1 font-semibold disabled:opacity-50"
                >
                  <Save size={12} /> Save
                </button>
                <button
                  onClick={cancelEdit}
                  className="text-[11px] px-2 py-1 bg-white border border-slate-300 text-slate-600 rounded hover:bg-slate-50 flex items-center gap-1 font-semibold"
                >
                  <X size={12} /> Cancel
                </button>
              </div>
            )}
          </div>

          {/* Body */}
          {editingKey === s.keyword ? (
            <div className="p-4 space-y-3">
              <div>
                <label className="block text-[10px] font-bold text-slate-500 uppercase tracking-wider mb-1">Display Name</label>
                <input
                  type="text"
                  className="w-full px-3 py-1.5 border border-slate-300 rounded text-sm"
                  value={editData.display_name || ''}
                  onChange={e => setEditData(p => ({ ...p, display_name: e.target.value }))}
                />
              </div>
              <div className="flex items-center gap-2">
                <label className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">Prohibited Item?</label>
                <input
                  type="checkbox"
                  className="w-4 h-4 accent-red-600 rounded"
                  checked={editData.is_prohibited || false}
                  onChange={e => setEditData(p => ({ ...p, is_prohibited: e.target.checked }))}
                />
                <span className="text-xs text-slate-500">{editData.is_prohibited ? 'Yes — Absolute Confiscation' : 'No — Redemption Fine / Duty'}</span>
              </div>
              <div>
                <label className="block text-[10px] font-bold text-slate-500 uppercase tracking-wider mb-1">SUPDT Goods Clause</label>
                <textarea
                  rows={3}
                  className="w-full px-3 py-1.5 border border-slate-300 rounded text-sm resize-none"
                  placeholder="One sentence describing why this item is seizable (for Superintendent's Remarks)..."
                  value={editData.supdt_goods_clause || ''}
                  onChange={e => setEditData(p => ({ ...p, supdt_goods_clause: e.target.value }))}
                />
              </div>
              <div>
                <label className="block text-[10px] font-bold text-slate-500 uppercase tracking-wider mb-1">AC Adjudication Clause</label>
                <textarea
                  rows={3}
                  className="w-full px-3 py-1.5 border border-slate-300 rounded text-sm resize-none"
                  placeholder="One sentence describing the legal finding for this item (for Adjudicating Officer's Order)..."
                  value={editData.adjn_goods_clause || ''}
                  onChange={e => setEditData(p => ({ ...p, adjn_goods_clause: e.target.value }))}
                />
              </div>
              <div>
                <label className="block text-[10px] font-bold text-slate-500 uppercase tracking-wider mb-1">Legal Reference</label>
                <input
                  type="text"
                  className="w-full px-3 py-1.5 border border-slate-300 rounded text-sm"
                  placeholder="Acts, notifications, circulars cited..."
                  value={editData.legal_reference || ''}
                  onChange={e => setEditData(p => ({ ...p, legal_reference: e.target.value }))}
                />
              </div>
            </div>
          ) : (
            <div className="p-4 space-y-2">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-[10px] font-bold text-indigo-500 uppercase tracking-wider mb-0.5">SUPDT Clause</p>
                  <p className="text-xs text-slate-700 leading-relaxed">{s.supdt_goods_clause || '—'}</p>
                </div>
                <div>
                  <p className="text-[10px] font-bold text-amber-600 uppercase tracking-wider mb-0.5">AC Clause</p>
                  <p className="text-xs text-slate-700 leading-relaxed">{s.adjn_goods_clause || '—'}</p>
                </div>
              </div>
              <div>
                <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-0.5">Legal Reference</p>
                <p className="text-xs text-slate-600">{s.legal_reference || '—'}</p>
              </div>
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
