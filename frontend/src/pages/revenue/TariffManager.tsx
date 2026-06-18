/**
 * TariffManager — view and update duty rates.
 *
 * Each "Save New Rates" creates a new row in dr_tariffs (with an effective_from date).
 * Historical sessions are unaffected because their tariff_id snapshot is immutable.
 *
 * HOW TO ADD A NEW RATE FIELD:
 *   1. Add column to DrTariff in backend models/duty_report.py
 *   2. Add SQLite migration in main.py apply_sqlite_migrations()
 *   3. Add a row in RATE_FIELDS below with the field name, label, and group
 *   4. Update computeDuties() in revenueCalc.ts to use the new field
 */
import { useState, useEffect } from 'react';
import { TrendingUp, Plus, ChevronDown, ChevronRight } from 'lucide-react';
import api from '@/lib/api';
import type { DrTariff } from './revenueCalc';

interface RateField {
  key: keyof Omit<DrTariff, 'id' | 'effective_from' | 'label' | 'created_at'>;
  label: string;
  pct: boolean;          // true = display/edit as percentage (0.35 → 35%)
  group: string;
}

const RATE_FIELDS: RateField[] = [
  // ── Baggage ──
  { key: 'baggage_rate',          label: 'Baggage BCD Rate',               pct: true,  group: 'Baggage' },
  // ── Liquor ──
  { key: 'liquor_duty_rate',      label: 'Liquor Duty Rate',               pct: true,  group: 'Liquor' },
  { key: 'aidc_liquor_rate',      label: 'AIDC on Liquor Rate',            pct: true,  group: 'Liquor' },
  // ── Gold (Standard) ──
  { key: 'gold_bcd_rate',         label: 'Gold BCD Rate (Standard)',       pct: true,  group: 'Gold (Standard)' },
  { key: 'aidc_gold_rate',        label: 'AIDC on Gold (Standard)',        pct: true,  group: 'Gold (Standard)' },
  // ── Gold (Concessional = GOLD(C)) ──
  { key: 'gold_cons_bcd_rate',    label: 'Gold BCD Rate (Cons. / GOLD(C))',pct: true,  group: 'Gold (Concessional)' },
  { key: 'aidc_gold_cons_rate',   label: 'AIDC on Gold (Cons. / GOLD(C))',pct: true,  group: 'Gold (Concessional)' },
  // ── Silver (Standard) ──
  { key: 'silver_bcd_rate',       label: 'Silver BCD Rate (Standard)',     pct: true,  group: 'Silver' },
  { key: 'aidc_silver_rate',      label: 'AIDC on Silver (Standard)',      pct: true,  group: 'Silver' },
  // ── Silver (Concessional = SILVER(C)) ──
  { key: 'silver_cons_rate',      label: 'Silver BCD Rate (Cons. / SILVER(C))', pct: true, group: 'Silver' },
  { key: 'aidc_silver_cons_rate', label: 'AIDC on Silver (Cons.)',         pct: true,  group: 'Silver' },
];

const GROUPS = [...new Set(RATE_FIELDS.map(f => f.group))];

function displayRate(val: number, pct: boolean): string {
  return pct ? `${(val * 100).toFixed(1)}%` : String(val);
}

function parseRate(str: string, pct: boolean): number {
  const n = parseFloat(str);
  return pct ? n / 100 : n;
}

export default function TariffManager({ onClose }: { onClose: () => void }) {
  const [tariffs, setTariffs] = useState<DrTariff[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [showNewForm, setShowNewForm] = useState(false);
  const [expandedId, setExpandedId] = useState<number | null>(null);

  const today = new Date().toISOString().slice(0, 10);
  const [newLabel, setNewLabel] = useState('');
  const [newDate, setNewDate] = useState(today);
  const [newRates, setNewRates] = useState<Record<string, string>>({});
  const [saveMsg, setSaveMsg] = useState('');

  useEffect(() => {
    api.get('/dcr/tariffs')
      .then(r => {
        setTariffs(r.data);
        if (r.data.length > 0) {
          setExpandedId(r.data[0].id);
          // Pre-fill the new-rates form from the latest tariff
          const latest = r.data[0] as DrTariff;
          const initial: Record<string, string> = {};
          for (const f of RATE_FIELDS) {
            const val = latest[f.key] as number;
            initial[f.key] = f.pct ? (val * 100).toFixed(1) : String(val);
          }
          setNewRates(initial);
        }
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const handleSaveNew = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setSaveMsg('');
    try {
      const payload: Record<string, unknown> = {
        effective_from: newDate,
        label: newLabel.trim() || null,
      };
      for (const f of RATE_FIELDS) {
        payload[f.key] = parseRate(newRates[f.key] ?? '0', f.pct);
      }
      const res = await api.post('/dcr/tariffs', payload);
      setTariffs(prev => [res.data, ...prev]);
      setExpandedId(res.data.id);
      setShowNewForm(false);
      setSaveMsg('New rates saved. Future sessions will use these rates. Historical data is unaffected.');
    } catch {
      setSaveMsg('Failed to save. Please check the values and try again.');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex">
      <div className="fixed inset-0 bg-black/40" onClick={onClose} />
      <div className="relative ml-auto w-full max-w-xl h-full bg-white shadow-2xl flex flex-col overflow-hidden">
        <div className="flex items-center justify-between px-5 py-4 border-b border-slate-200 shrink-0">
          <div className="flex items-center gap-2">
            <TrendingUp size={20} className="text-teal-600" />
            <h2 className="font-bold text-slate-800">Duty Rate History</h2>
          </div>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-600 text-lg font-bold">✕</button>
        </div>

        <div className="flex-1 overflow-y-auto p-5 space-y-4">
          {saveMsg && (
            <div className={`text-xs p-3 rounded-lg ${saveMsg.includes('Failed')
              ? 'bg-red-50 text-red-700 border border-red-200'
              : 'bg-emerald-50 text-emerald-700 border border-emerald-200'}`}>
              {saveMsg}
            </div>
          )}

          <button
            onClick={() => setShowNewForm(s => !s)}
            className="w-full flex items-center justify-center gap-2 py-2.5 rounded-xl border-2 border-dashed border-teal-300 text-teal-700 hover:bg-teal-50 font-semibold text-sm transition-colors"
          >
            <Plus size={16} /> Set New Rates (effective from a date)
          </button>

          {showNewForm && (
            <form onSubmit={handleSaveNew} className="bg-teal-50 border border-teal-200 rounded-xl p-4 space-y-4">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-xs font-semibold text-slate-600 block mb-1">Effective From</label>
                  <input type="date" value={newDate} onChange={e => setNewDate(e.target.value)}
                    className="w-full border border-slate-300 rounded-lg px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-teal-400"
                    required />
                </div>
                <div>
                  <label className="text-xs font-semibold text-slate-600 block mb-1">Label (optional)</label>
                  <input type="text" value={newLabel} onChange={e => setNewLabel(e.target.value)}
                    placeholder="e.g. Budget 2025-26"
                    className="w-full border border-slate-300 rounded-lg px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-teal-400" />
                </div>
              </div>

              {GROUPS.map(group => (
                <div key={group}>
                  <p className="text-xs font-bold text-slate-500 uppercase tracking-wide mb-2">{group}</p>
                  <div className="space-y-2">
                    {RATE_FIELDS.filter(f => f.group === group).map(f => (
                      <div key={f.key} className="flex items-center justify-between gap-3">
                        <label className="text-xs text-slate-700 flex-1">{f.label}</label>
                        <div className="flex items-center gap-1">
                          <input
                            type="number" step="0.01" min="0"
                            value={newRates[f.key] ?? ''}
                            onChange={e => setNewRates(p => ({ ...p, [f.key]: e.target.value }))}
                            className="w-20 border border-slate-300 rounded px-2 py-1 text-sm text-right focus:outline-none focus:ring-1 focus:ring-teal-400"
                          />
                          {f.pct && <span className="text-xs text-slate-500">%</span>}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              ))}

              <div className="flex gap-2 pt-2">
                <button type="submit" disabled={saving}
                  className="flex-1 bg-teal-600 hover:bg-teal-700 text-white font-semibold py-2 rounded-lg text-sm disabled:opacity-60">
                  {saving ? 'Saving…' : 'Save New Rates'}
                </button>
                <button type="button" onClick={() => setShowNewForm(false)}
                  className="px-4 py-2 bg-slate-200 hover:bg-slate-300 text-slate-700 font-semibold rounded-lg text-sm">
                  Cancel
                </button>
              </div>
            </form>
          )}

          {/* Tariff history */}
          <div className="space-y-2">
            <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide">Rate History (newest first)</p>
            {loading && <p className="text-xs text-slate-400">Loading…</p>}
            {tariffs.map((t, idx) => (
              <div key={t.id} className={`rounded-xl border ${idx === 0 ? 'border-teal-300 bg-teal-50' : 'border-slate-200 bg-white'}`}>
                <button
                  className="w-full flex items-center justify-between px-4 py-3 text-left"
                  onClick={() => setExpandedId(expandedId === t.id ? null : t.id)}
                >
                  <div>
                    <p className="text-sm font-bold text-slate-800">
                      {idx === 0 && <span className="text-teal-600 mr-2">●</span>}
                      Effective: {t.effective_from}
                      {t.label && <span className="ml-2 text-slate-500 font-normal">({t.label})</span>}
                    </p>
                    <p className="text-xs text-slate-500 mt-0.5">
                      Baggage {displayRate(t.baggage_rate, true)} · Gold BCD {displayRate(t.gold_bcd_rate, true)} · Gold(C) {displayRate(t.gold_cons_bcd_rate, true)}
                    </p>
                  </div>
                  {expandedId === t.id ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
                </button>

                {expandedId === t.id && (
                  <div className="px-4 pb-3 border-t border-slate-200">
                    {GROUPS.map(group => (
                      <div key={group} className="mt-3">
                        <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wide mb-1">{group}</p>
                        <div className="grid grid-cols-2 gap-x-6 gap-y-1">
                          {RATE_FIELDS.filter(f => f.group === group).map(f => (
                            <div key={f.key} className="flex justify-between text-xs">
                              <span className="text-slate-600">{f.label}</span>
                              <span className="font-semibold text-slate-800">
                                {displayRate(t[f.key] as number, f.pct)}
                              </span>
                            </div>
                          ))}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
