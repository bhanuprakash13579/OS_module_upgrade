/* eslint-disable @typescript-eslint/no-explicit-any */
import { useState, useEffect, useCallback, useMemo, memo, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowLeft, Plus, Trash2, FileText, User, Plane, AlertCircle, CheckCircle, Info } from 'lucide-react';
import DatePicker from '@/components/DatePicker';
import api from '@/lib/api';

// ── Static seed list for item-description autocomplete ───────────────────────
const STATIC_ITEM_SUGGESTIONS = [
  'CIGARETTES','E-CIGARETTES','CIGARS','BIDI','GUTKHA','PAN MASALA','TOBACCO',
  'WHISKY','BRANDY','WINE','BEER','VODKA','RUM','GIN','SCOTCH','CHAMPAGNE','TEQUILA','LIQUOR',
  'GOLD (JEWELLERY)','GOLD (PRIMARY)','GOLD BAR','GOLD BISCUIT','GOLD CHAIN','GOLD RING',
  'SILVER (JEWELLERY)','SILVER BAR',
  'CURRENCY (FOREIGN)','CURRENCY (INDIAN)',
  'MOBILE PHONE','CELL PHONE','IPHONE','LAPTOP','TABLET','SMART WATCH',
  'CAMERA','VIDEO CAMERA','DRONE','ELECTRONIC GOODS',
  'NARCOTICS (CANNABIS/GANJA)','NARCOTICS (HEROIN)','NARCOTICS (COCAINE)',
  'ARMS','AMMUNITION','EXPLOSIVES',
  'ANTIQUES','TOYS','TEXTILES','FABRICS','COSMETICS','PERFUMES','SUNGLASSES','WATCHES',
  'RED SANDERS','POPPY SEEDS','POPPY HUSK',
  'REFURBISHED LAPTOP','REFURBISHED MOBILE PHONE',
  'MARLBORO CIGARETTES','DUNHILL CIGARETTES','GUDANG GARAM CIGARETTES',
  'CHIVAS REGAL WHISKY','JOHNNIE WALKER WHISKY','BARDINET BRANDY','JACK DANIELS WHISKY',
  'MEDICINES','FOOD ITEMS','DRY FRUITS','SPICES','LEATHER GOODS','GARMENTS',
];

const DUTY_TYPES = [
  "Antiques-01", "Audio CDs-02", "Cigarettes-03", "Currency (Foreign)-04", "Currency (FICN)-05",
  "Gold (Jewellery)-06", "Gold (Primary)-07", "Liquor-08", "Narcotics (Cannabis/Ganja)-09",
  "Narcotics (Heroin/Brown Sugar)-10", "Narcotics (Cocaine)-11", "Live Species / Wildlife-12",
  "Arms & Ammunition-13", "Silver-14", "Semi Precious / Precious Stones-15", "Video CDs-16",
  "Cameras / Video Cameras-17", "Cell Phones-18", "Cordless Phones-19", "Calculator & Digital Diary-20",
  "Electronic Goods-21", "Miscellaneous-22", "VCD / DVD Players-23", "Walkmans-24", "Watch / Watch Movements-25",
  "Textiles / Fabrics-26", "FEMA (Foreign Exchange)-27", "Commercial Fraud (Imports)-28",
  "Commercial Fraud (Exports)-29", "Tobacco / Gutkha-30", "Morphine-31", "Opium-32", "Psychotropic Substances-33",
  "Ephedrine / Precursors-34", "Fake Indian Goods / IPR-35", "Red Sanders / Timber-36",
  "Ivory / Elephant Products-37", "Pangolin / Animal Parts-38", "Coral / Marine Products-39",
  "Prohibited Imports-40", "Prohibited Exports-41", "Duty Evasion (Imports)-42", "Duty Evasion (Exports)-43",
  "Misdeclaration (Imports)-44", "Misdeclaration (Exports)-45", "Under-valuation (Imports)-46",
  "Under-valuation (Exports)-47", "Overvaluation (Exports)-48", "Drawback Fraud-49",
  "EPCG / Advance Licence Fraud-50", "FTA / Preferential Duty Fraud-51", "Narcotics (Methamphetamine/Synthetic)-52",
  "Narcotics (Ketamine/NPS)-53", "Narcotics (Mandrax/Methaqualone)-54", "Narcotics (Other NDPS)-55",
  "Narcotic (Imports)-56", "Narcotic (Exports)-57", "Explosives-58", "Dual Use / SCOMET Goods-59",
  "Human Trafficking-60", "Hazardous Waste-61", "E-Waste-62", "Areca Nut-63", "Betel Leaves-64",
  "Wildlife (CITES)-65", "ODS (Exports)-66", "ODS (Imports)-67", "Counterfeit Currency-68",
  "Counterfeit Goods-69", "Other_Baggage-99"
];

const DUTY_TYPE_OPTIONS = DUTY_TYPES.map(type => (
  <option key={type} value={type}>{type}</option>
));

const sanitizeInteger = (raw: string) => raw.replace(/[^\d]/g, '');
const sanitizeDecimal = (raw: string) => {
  const cleaned = raw.replace(/[^\d.]/g, '');
  const firstDot = cleaned.indexOf('.');
  const result = firstDot === -1
    ? cleaned
    : cleaned.slice(0, firstDot + 1) + cleaned.slice(firstDot + 1).replace(/\./g, '');
  return result.replace(/^0+([1-9])/, '$1');
};

// ── Simplified Item Row (no FA, no release category) ─────────────────────────
interface SimpleItemRowProps {
  itm: any;
  idx: number;
  rowErrors: Record<string, string> | undefined;
  updateItem: (idx: number, field: string, value: any) => void;
  onRemove: (idx: number) => void;
  onDescBlur: (idx: number, desc: string) => void;
  descDatalistId: string;
}

const SimpleItemRow = memo(function SimpleItemRow({
  itm, idx, rowErrors, updateItem, onRemove, onDescBlur, descDatalistId
}: SimpleItemRowProps) {
  return (
    <tr id={`item-row-${idx}`} className="hover:bg-slate-50 group">
      <td className="px-3 py-2 text-center font-medium text-slate-500 text-sm">{idx + 1}</td>
      <td className="px-2 py-1.5">
        <input
          type="text"
          list={descDatalistId}
          autoComplete="off"
          className={`w-full px-2 py-1.5 border ${rowErrors?.items_desc ? 'border-red-500 ring-1 ring-red-500' : 'border-slate-300'} rounded text-xs uppercase focus:outline-none focus:ring-2 focus:ring-blue-400`}
          value={itm.items_desc}
          onChange={e => updateItem(idx, 'items_desc', e.target.value.toUpperCase())}
          onBlur={e => onDescBlur(idx, e.target.value)}
        />
        {rowErrors?.items_desc && <p className="text-[10px] text-red-500 mt-0.5">{rowErrors.items_desc}</p>}
      </td>
      <td className="px-2 py-1.5">
        <div className="flex items-center gap-1">
          <input
            type="text"
            inputMode="decimal"
            className={`w-14 px-1.5 py-1.5 border ${rowErrors?.items_qty ? 'border-red-500 ring-1 ring-red-500' : 'border-slate-300'} rounded text-xs text-center focus:outline-none focus:ring-2 focus:ring-blue-400`}
            value={itm.items_qty || ''}
            placeholder="0"
            onChange={e => updateItem(idx, 'items_qty', sanitizeDecimal(e.target.value))}
          />
          <select
            className="w-16 px-1 py-1.5 border border-slate-300 rounded text-[10px] focus:outline-none focus:ring-1 focus:ring-blue-400"
            value={itm.items_uqc}
            onChange={e => updateItem(idx, 'items_uqc', e.target.value)}
          >
            <option value="NOS">Nos.</option>
            <option value="STK">Sticks</option>
            <option value="KGS">Kgs.</option>
            <option value="GMS">Gms.</option>
            <option value="LTR">Ltrs.</option>
            <option value="MTR">Mtrs.</option>
            <option value="PRS">Pairs</option>
          </select>
        </div>
        {rowErrors?.items_qty && <p className="text-[10px] text-red-500 mt-0.5">{rowErrors.items_qty}</p>}
      </td>
      <td className="px-2 py-1.5">
        <input
          type="text"
          inputMode="decimal"
          className={`w-full px-2 py-1.5 border ${rowErrors?.items_value ? 'border-red-500 ring-1 ring-red-500' : 'border-slate-300'} rounded text-xs text-right focus:outline-none focus:ring-2 focus:ring-blue-400`}
          value={itm.items_value || ''}
          placeholder="0"
          onChange={e => updateItem(idx, 'items_value', sanitizeDecimal(e.target.value))}
        />
        {rowErrors?.items_value && <p className="text-[10px] text-red-500 mt-0.5">{rowErrors.items_value}</p>}
      </td>
      <td className="px-2 py-1.5">
        <select
          className={`w-full px-2 py-1.5 border ${rowErrors?.items_duty_type ? 'border-red-500 ring-1 ring-red-500' : 'border-slate-300'} rounded text-xs focus:outline-none focus:ring-2 focus:ring-blue-400`}
          value={itm.items_duty_type}
          onChange={e => updateItem(idx, 'items_duty_type', e.target.value)}
        >
          {DUTY_TYPE_OPTIONS}
        </select>
        {rowErrors?.items_duty_type && <p className="text-[10px] text-red-500 mt-0.5">{rowErrors.items_duty_type}</p>}
      </td>
      <td className="px-2 py-1.5 text-center">
        <button
          onClick={(e) => { e.preventDefault(); onRemove(idx); }}
          className="text-slate-400 hover:text-red-500 transition-colors"
          title="Remove row"
        >
          <Trash2 size={15} />
        </button>
      </td>
    </tr>
  );
});

// Module-level cache for item descriptions
let _offlineDescCache: string[] | null = null;

// ─────────────────────────────────────────────────────────────────────────────
export default function OfflineAdjudicationForm() {
  const navigate = useNavigate();

  // ── Item description suggestions ─────────────────────────────────────────
  const [descSuggestions, setDescSuggestions] = useState<string[]>(_offlineDescCache ?? STATIC_ITEM_SUGGESTIONS);
  useEffect(() => {
    if (_offlineDescCache !== null) return;
    api.get('/os/item-descriptions')
      .then(res => {
        if (!Array.isArray(res.data)) return;
        const dbItems: string[] = res.data.map((s: string) => (s || '').toUpperCase()).filter(Boolean);
        const merged = [...dbItems];
        const existing = new Set(dbItems);
        for (const s of STATIC_ITEM_SUGGESTIONS) { if (!existing.has(s)) { merged.push(s); existing.add(s); } }
        _offlineDescCache = merged;
        setDescSuggestions(merged);
      })
      .catch(() => { /* keep static list on error */ });
  }, []);

  const descDatalist = useMemo(() => (
    <datalist id="offline-item-desc-datalist">
      {descSuggestions.map(s => <option key={s} value={s} />)}
    </datalist>
  ), [descSuggestions]);

  // ── Form state ────────────────────────────────────────────────────────────
  const [formData, setFormData] = useState({
    os_no: '',
    os_date: new Date().toISOString().split('T')[0],
    booked_by: 'Batch A',
    flight_no: '',
    pax_name: '',
    pax_nationality: '',
    passport_no: '',
    pax_address1: '',
  });

  const [optionalData, setOptionalData] = useState({
    pax_date_of_birth: '',
    passport_date: '',
    pp_issue_place: '',
    father_name: '',
    residence_at: '',
    old_passport_no: '',
    case_type: 'Non-Bonafide',
    shift: 'Day',
    supdts_remarks: '',
  });

  const [items, setItems] = useState<any[]>([{
    items_desc: '',
    items_qty: 1,
    items_uqc: 'NOS',
    items_value: 0,
    items_duty_type: 'Miscellaneous-22',
  }]);

  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});
  const [itemErrors, setItemErrors] = useState<Record<number, Record<string, string>>>({});
  const [errorMsg, setErrorMsg] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [successInfo, setSuccessInfo] = useState<{ os_no: string; os_year: number } | null>(null);
  const [autoFillBanner, setAutoFillBanner] = useState(false);
  const [additionalOpen, setAdditionalOpen] = useState(false);

  const osNoCheckTimer = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);
  const ppLookupAbort = useRef<AbortController | null>(null);

  // ── Field error helpers ───────────────────────────────────────────────────
  const setFieldError = useCallback((field: string, message: string) => {
    setFieldErrors(prev => ({ ...prev, [field]: message }));
  }, []);

  const clearFieldError = useCallback((field: string) => {
    setFieldErrors(prev => {
      if (!prev[field]) return prev;
      const { [field]: _removed, ...rest } = prev;
      return rest;
    });
  }, []);

  // ── Item handlers ─────────────────────────────────────────────────────────
  const updateItem = useCallback((idx: number, field: string, value: any) => {
    setItems(prev => prev.map((item, i) => i === idx ? { ...item, [field]: value } : item));
  }, []);

  const onRemove = useCallback((idx: number) => {
    setItems(prev => prev.filter((_, i) => i !== idx));
  }, []);

  // Smart classification on description blur
  const classifyAbortRefs = useRef<Record<number, AbortController>>({});
  useEffect(() => () => { Object.values(classifyAbortRefs.current).forEach(c => c.abort()); }, []);

  const onDescBlur = useCallback(async (idx: number, desc: string) => {
    if (!desc || desc.trim().length < 3) return;
    classifyAbortRefs.current[idx]?.abort();
    const ctrl = new AbortController();
    classifyAbortRefs.current[idx] = ctrl;
    try {
      const res = await api.get('/os/classify-item', { params: { description: desc }, signal: ctrl.signal });
      if (res.data?.duty_type && res.data.duty_type !== 'Miscellaneous-22') {
        setItems(prev => {
          const row = prev[idx];
          if (!row) return prev;
          const updated = { ...row, items_duty_type: res.data.duty_type };
          if (res.data.uqc && res.data.uqc !== 'NOS') updated.items_uqc = res.data.uqc;
          return prev.map((item, i) => i === idx ? updated : item);
        });
      }
    } catch { /* silent */ }
  }, []);

  // ── Passport lookup on blur ───────────────────────────────────────────────
  const handlePassportBlur = useCallback(async (pp: string) => {
    if (!pp || pp.trim().length < 4) return;
    ppLookupAbort.current?.abort();
    const ctrl = new AbortController();
    ppLookupAbort.current = ctrl;
    try {
      const res = await api.get('/os/passports/lookup-by-pp', {
        params: { passport_no: pp.trim().toUpperCase() },
        signal: ctrl.signal,
      });
      const data = res.data;
      if (!data || !data.pax_name) return;

      // Only fill fields that are currently empty
      setFormData(prev => ({
        ...prev,
        pax_name: prev.pax_name || (data.pax_name || ''),
        pax_nationality: prev.pax_nationality || (data.pax_nationality || ''),
        pax_address1: prev.pax_address1 || (data.pax_address1 || ''),
      }));
      setOptionalData(prev => ({
        ...prev,
        pax_date_of_birth: prev.pax_date_of_birth || (data.pax_date_of_birth || ''),
        passport_date: prev.passport_date || (data.passport_date || ''),
        pp_issue_place: prev.pp_issue_place || (data.pp_issue_place || ''),
        father_name: prev.father_name || (data.father_name || ''),
        residence_at: prev.residence_at || (data.residence_at || ''),
        old_passport_no: prev.old_passport_no || (data.old_passport_no || ''),
      }));
      setAutoFillBanner(true);
    } catch { /* silent — AbortError or not found */ }
  }, []);

  useEffect(() => () => { ppLookupAbort.current?.abort(); }, []);

  // ── O.S. No. uniqueness check ─────────────────────────────────────────────
  const handleOsNoChange = (raw: string) => {
    const sanitized = sanitizeInteger(raw);
    setFormData(prev => ({ ...prev, os_no: sanitized }));
    if (!sanitized) { setFieldError('os_no', 'O.S. No. is required.'); return; }
    if (sanitized !== raw) { setFieldError('os_no', 'Digits only.'); return; }
    clearFieldError('os_no');

    clearTimeout(osNoCheckTimer.current);
    osNoCheckTimer.current = setTimeout(async () => {
      try {
        const yr = formData.os_date ? new Date(formData.os_date).getFullYear() : new Date().getFullYear();
        const { data: result } = await api.get(`/os/check-os-no/${sanitized}/${yr}`);
        if (result.exists) setFieldError('os_no', `O.S. No. ${sanitized}/${yr} already exists!`);
      } catch { /* ignore */ }
    }, 500);
  };

  // ── Validation & submit ───────────────────────────────────────────────────
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg('');
    setFieldErrors({});
    setItemErrors({});

    const errors: Record<string, string> = {};
    const itemErrs: Record<number, Record<string, string>> = {};

    const requireField = (key: string, val: string, label: string) => {
      if (!val.trim()) errors[key] = `${label} is required.`;
    };

    requireField('os_no', formData.os_no, 'O.S. No.');
    requireField('os_date', formData.os_date, 'O.S. Date');
    requireField('booked_by', formData.booked_by, 'Booked By / Batch AIU');
    requireField('flight_no', formData.flight_no, 'Flight No.');
    requireField('pax_name', formData.pax_name, 'Passenger Name');
    requireField('pax_nationality', formData.pax_nationality, 'Nationality');
    requireField('passport_no', formData.passport_no, 'Passport No.');
    requireField('pax_address1', formData.pax_address1, 'Address');

    if (!errors.os_no && !/^\d+$/.test(formData.os_no.trim())) {
      errors.os_no = 'O.S. No. must be digits only.';
    }

    if (items.length === 0) {
      errors['items'] = 'At least one seized item is required.';
    }

    items.forEach((itm, idx) => {
      const rowErrors: Record<string, string> = {};
      if (!String(itm.items_desc || '').trim()) rowErrors.items_desc = 'Description is required.';
      if (!String(itm.items_qty || '').trim()) rowErrors.items_qty = 'Quantity required.';
      if (!String(itm.items_value || '').trim() || Number(itm.items_value) === 0) rowErrors.items_value = 'Value required.';
      if (!String(itm.items_duty_type || '').trim()) rowErrors.items_duty_type = 'Duty Type required.';
      if (Object.keys(rowErrors).length > 0) itemErrs[idx] = rowErrors;
    });

    if (Object.keys(errors).length > 0 || Object.keys(itemErrs).length > 0) {
      setFieldErrors(errors);
      setItemErrors(itemErrs);
      setErrorMsg('Please fill all mandatory fields highlighted in red before saving.');
      const firstKey = Object.keys(errors)[0];
      if (firstKey && firstKey !== 'items') {
        const el = document.getElementById(`field-${firstKey}`);
        if (el) { el.scrollIntoView({ behavior: 'smooth', block: 'center' }); (el as any).focus?.(); }
      } else if (Object.keys(itemErrs).length > 0) {
        const firstRow = Number(Object.keys(itemErrs)[0]);
        document.getElementById(`item-row-${firstRow}`)?.scrollIntoView({ behavior: 'smooth', block: 'center' });
      }
      return;
    }

    setIsSubmitting(true);
    try {
      const isDateValid = (d: string) => d && /^\d{4}-\d{2}-\d{2}$/.test(d);
      const payload: any = {
        os_no: formData.os_no,
        os_date: formData.os_date,
        booked_by: formData.booked_by,
        flight_no: formData.flight_no.toUpperCase(),
        pax_name: formData.pax_name.toUpperCase(),
        pax_nationality: formData.pax_nationality.toUpperCase(),
        passport_no: formData.passport_no.toUpperCase(),
        pax_address1: formData.pax_address1.toUpperCase(),
        is_draft: 'N',
        items: items.map((itm, i) => ({
          items_sno: i + 1,
          items_desc: String(itm.items_desc || '').toUpperCase(),
          items_qty: Number(itm.items_qty || 0),
          items_uqc: itm.items_uqc || 'NOS',
          items_value: Number(itm.items_value || 0),
          items_duty_type: itm.items_duty_type || '',
          cumulative_duty_rate: 0,
          value_per_piece: Number(itm.items_value || 0),
        })),
      };

      // Optional fields — only include if non-empty
      if (optionalData.pax_date_of_birth && isDateValid(optionalData.pax_date_of_birth))
        payload.pax_date_of_birth = optionalData.pax_date_of_birth;
      if (optionalData.passport_date && isDateValid(optionalData.passport_date))
        payload.passport_date = optionalData.passport_date;
      if (optionalData.pp_issue_place.trim()) payload.pp_issue_place = optionalData.pp_issue_place.toUpperCase();
      if (optionalData.father_name.trim()) payload.father_name = optionalData.father_name.toUpperCase();
      if (optionalData.residence_at.trim()) payload.residence_at = optionalData.residence_at.toUpperCase();
      if (optionalData.old_passport_no.trim()) payload.old_passport_no = optionalData.old_passport_no.toUpperCase();
      if (optionalData.case_type) payload.case_type = optionalData.case_type;
      if (optionalData.shift) payload.shift = optionalData.shift;
      if (optionalData.supdts_remarks.trim()) payload.supdts_remarks = optionalData.supdts_remarks;

      const res = await api.post('/os/offline', payload);
      const savedOsNo = res.data?.os_no || formData.os_no;
      const savedOsYear = res.data?.os_year || new Date(formData.os_date).getFullYear();
      setSuccessInfo({ os_no: savedOsNo, os_year: savedOsYear });
    } catch (err: any) {
      let errMsg = err.response?.data?.detail || err.message || 'Failed to save offline case.';
      if (Array.isArray(errMsg)) errMsg = errMsg.map((e: any) => `${e.loc?.join('.')} - ${e.msg}`).join(', ');
      else if (typeof errMsg === 'object') errMsg = JSON.stringify(errMsg);
      setErrorMsg(errMsg);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleRegisterAnother = () => {
    setSuccessInfo(null);
    setFormData({
      os_no: '', os_date: new Date().toISOString().split('T')[0], booked_by: 'Batch A',
      flight_no: '', pax_name: '', pax_nationality: '', passport_no: '', pax_address1: '',
    });
    setOptionalData({
      pax_date_of_birth: '', passport_date: '', pp_issue_place: '', father_name: '',
      residence_at: '', old_passport_no: '', case_type: 'Non-Bonafide', shift: 'Day', supdts_remarks: '',
    });
    setItems([{ items_desc: '', items_qty: 1, items_uqc: 'NOS', items_value: 0, items_duty_type: 'Miscellaneous-22' }]);
    setFieldErrors({});
    setItemErrors({});
    setErrorMsg('');
    setAutoFillBanner(false);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const totalValue = useMemo(
    () => items.reduce((acc, itm) => acc + Number(itm.items_value || 0), 0),
    [items]
  );

  // ── Success screen ────────────────────────────────────────────────────────
  if (successInfo) {
    return (
      <div className="space-y-4 pt-2 w-full px-2 pb-20">
        <div className="flex items-center bg-white px-4 py-3 border-b border-slate-200 rounded-xl border">
          <button onClick={() => navigate('/sdo')} className="p-2 bg-slate-50 border border-slate-200 rounded-md hover:bg-slate-100 transition-colors mr-4">
            <ArrowLeft size={20} className="text-slate-600" />
          </button>
          <h1 className="text-2xl font-bold text-slate-800 tracking-tight">Register Offline Adjudication Case</h1>
        </div>
        <div className="bg-white rounded-xl border border-green-200 p-10 text-center space-y-4 max-w-xl mx-auto mt-8">
          <CheckCircle size={48} className="text-green-500 mx-auto" />
          <h2 className="text-xl font-bold text-slate-800">Case Registered Successfully</h2>
          <p className="text-slate-600 text-sm">
            Offline adjudication case{' '}
            <span className="font-bold text-blue-700">O.S. {successInfo.os_no}/{successInfo.os_year}</span>{' '}
            has been saved and is pending completion by the adjudication officer.
          </p>
          <div className="flex gap-3 justify-center pt-2">
            <button
              onClick={handleRegisterAnother}
              className="px-5 py-2 bg-blue-700 text-white font-semibold rounded-lg hover:bg-blue-600 transition-colors text-sm"
            >
              Register Another
            </button>
            <button
              onClick={() => navigate('/sdo')}
              className="px-5 py-2 border border-slate-300 text-slate-700 font-semibold rounded-lg hover:bg-slate-50 transition-colors text-sm"
            >
              Back to SDO
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4 pt-2 w-full px-2 pb-20">
      {descDatalist}

      {/* Header */}
      <div className="flex justify-between items-center bg-white px-4 py-3 border-b border-slate-200 rounded-xl border">
        <div className="flex items-center space-x-4">
          <button onClick={() => navigate('/sdo')} className="p-2 bg-slate-50 border border-slate-200 rounded-md hover:bg-slate-100 transition-colors">
            <ArrowLeft size={20} className="text-slate-600" />
          </button>
          <div>
            <h1 className="text-2xl font-bold text-slate-800 tracking-tight">Register Offline Adjudication Case</h1>
            <p className="text-slate-500 text-sm mt-0.5">Fill in the case details and seized goods. Officer details will be added by the adjudication module.</p>
          </div>
        </div>
        <span className="bg-blue-100 text-blue-800 border border-blue-300 px-3 py-1.5 rounded-lg text-xs font-bold">
          OFFLINE ADJ
        </span>
      </div>

      {/* Error banner */}
      {errorMsg && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg flex items-start">
          <AlertCircle className="shrink-0 mr-3 mt-0.5" size={20} />
          <div>
            <h4 className="font-bold text-sm">Validation Error</h4>
            <p className="text-sm">{errorMsg}</p>
            {(Object.keys(fieldErrors).length > 0 || Object.keys(itemErrors).length > 0) && (
              <ul className="list-disc pl-4 text-xs mt-2 space-y-1">
                {Object.entries(fieldErrors).map(([k, m]) => <li key={k}>{m}</li>)}
                {Object.entries(itemErrors).flatMap(([idxStr, errs]) =>
                  Object.entries(errs).map(([k, m]) => (
                    <li key={`item-${idxStr}-${k}`}>Seized Item {Number(idxStr) + 1}: {m}</li>
                  ))
                )}
              </ul>
            )}
          </div>
        </div>
      )}

      {/* Auto-fill banner */}
      {autoFillBanner && (
        <div className="bg-blue-50 border border-blue-200 text-blue-700 px-4 py-3 rounded-lg flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Info size={16} className="shrink-0" />
            <span className="text-sm font-medium">Passenger details auto-filled from previous case record</span>
          </div>
          <button onClick={() => setAutoFillBanner(false)} className="text-blue-400 hover:text-blue-600 text-lg leading-none font-bold px-2">&times;</button>
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* ── Top Details Grid ─────────────────────────────────────────────── */}
        <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">

          {/* Case Registration Details */}
          <div className="bg-white p-5 rounded-xl border border-slate-200">
            <h2 className="text-sm font-bold text-slate-800 uppercase tracking-wider mb-4 border-b border-slate-100 pb-2 flex items-center">
              <FileText className="mr-2 text-blue-600" size={16} /> Case Registration Details
            </h2>
            <div className="space-y-3">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-500 uppercase mb-1">
                    O.S. No. <span className="text-red-500">*</span>
                  </label>
                  <input
                    id="field-os_no"
                    type="text"
                    inputMode="numeric"
                    className={`w-full px-3 py-2 bg-slate-50 border ${fieldErrors.os_no ? 'border-red-500 ring-1 ring-red-500' : 'border-slate-300 focus:ring-blue-500'} rounded focus:ring-2 text-sm`}
                    value={formData.os_no}
                    onChange={e => handleOsNoChange(e.target.value)}
                  />
                  {fieldErrors.os_no && <p className="mt-1 text-xs font-semibold text-red-600">{fieldErrors.os_no}</p>}
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-500 uppercase mb-1">
                    O.S. Date <span className="text-red-500">*</span>
                  </label>
                  <DatePicker
                    id="field-os_date"
                    value={formData.os_date}
                    onChange={isoDate => setFormData(prev => ({ ...prev, os_date: isoDate }))}
                    inputClassName="w-full px-3 py-2 bg-slate-50 border border-slate-300 focus:ring-blue-500 rounded focus:ring-2 text-sm"
                    error={!!fieldErrors.os_date}
                  />
                  {fieldErrors.os_date && <p className="mt-1 text-xs font-semibold text-red-600">{fieldErrors.os_date}</p>}
                </div>
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-500 uppercase mb-1">
                  Booked By / Batch AIU <span className="text-red-500">*</span>
                </label>
                <select
                  id="field-booked_by"
                  className={`w-full px-3 py-2 bg-slate-50 border ${fieldErrors.booked_by ? 'border-red-500 ring-1 ring-red-500' : 'border-slate-300 focus:ring-blue-500'} rounded focus:ring-2 text-sm`}
                  value={formData.booked_by}
                  onChange={e => setFormData(prev => ({ ...prev, booked_by: e.target.value }))}
                >
                  <option>Batch A</option><option>Batch B</option><option>Batch C</option><option>Batch D</option>
                  <option>AIU A</option><option>AIU B</option><option>AIU C</option><option>AIU D</option>
                </select>
                {fieldErrors.booked_by && <p className="mt-1 text-xs font-semibold text-red-600">{fieldErrors.booked_by}</p>}
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-500 uppercase mb-1">
                  Flight No. <span className="text-red-500">*</span>
                </label>
                <input
                  id="field-flight_no"
                  type="text"
                  className={`w-full px-3 py-2 bg-slate-50 border ${fieldErrors.flight_no ? 'border-red-500 ring-1 ring-red-500' : 'border-slate-300 focus:ring-blue-500'} rounded focus:ring-2 text-sm uppercase font-medium`}
                  value={formData.flight_no}
                  onChange={e => { setFormData(prev => ({ ...prev, flight_no: e.target.value.toUpperCase() })); clearFieldError('flight_no'); }}
                />
                {fieldErrors.flight_no && <p className="mt-1 text-xs font-semibold text-red-600">{fieldErrors.flight_no}</p>}
              </div>
            </div>
          </div>

          {/* Passenger & Passport */}
          <div className="bg-white p-5 rounded-xl border border-slate-200 relative overflow-hidden">
            <div className="absolute top-0 left-0 w-1 h-full bg-blue-500"></div>
            <h2 className="text-sm font-bold text-slate-800 uppercase tracking-wider mb-4 border-b border-slate-100 pb-2 flex items-center">
              <User className="mr-2 text-blue-500" size={16} /> Passenger &amp; Passport Information
            </h2>
            <div className="space-y-3">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-500 uppercase mb-1">
                    Passenger Name <span className="text-red-500">*</span>
                  </label>
                  <input
                    id="field-pax_name"
                    type="text"
                    className={`w-full px-3 py-1.5 border ${fieldErrors.pax_name ? 'border-red-500 ring-1 ring-red-500' : 'border-slate-300 focus:ring-blue-500'} rounded text-sm focus:ring-2 uppercase font-medium`}
                    value={formData.pax_name}
                    onChange={e => { setFormData(prev => ({ ...prev, pax_name: e.target.value.toUpperCase() })); clearFieldError('pax_name'); }}
                  />
                  {fieldErrors.pax_name && <p className="mt-1 text-xs font-semibold text-red-600">{fieldErrors.pax_name}</p>}
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-500 uppercase mb-1">
                    Nationality <span className="text-red-500">*</span>
                  </label>
                  <input
                    id="field-pax_nationality"
                    type="text"
                    className={`w-full px-3 py-1.5 border ${fieldErrors.pax_nationality ? 'border-red-500 ring-1 ring-red-500' : 'border-slate-300 focus:ring-blue-500'} rounded text-sm focus:ring-2 uppercase`}
                    value={formData.pax_nationality}
                    onChange={e => { setFormData(prev => ({ ...prev, pax_nationality: e.target.value.toUpperCase() })); clearFieldError('pax_nationality'); }}
                  />
                  {fieldErrors.pax_nationality && <p className="mt-1 text-xs font-semibold text-red-600">{fieldErrors.pax_nationality}</p>}
                </div>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-500 uppercase mb-1">
                    Passport No. <span className="text-red-500">*</span>
                  </label>
                  <input
                    id="field-passport_no"
                    type="text"
                    className={`w-full px-3 py-1.5 border ${fieldErrors.passport_no ? 'border-red-500 ring-1 ring-red-500' : 'border-slate-300 focus:ring-blue-500'} rounded text-sm focus:ring-2 uppercase font-bold text-slate-800`}
                    value={formData.passport_no}
                    onChange={e => { setFormData(prev => ({ ...prev, passport_no: e.target.value.toUpperCase() })); clearFieldError('passport_no'); }}
                    onBlur={e => handlePassportBlur(e.target.value)}
                  />
                  {fieldErrors.passport_no && <p className="mt-1 text-xs font-semibold text-red-600">{fieldErrors.passport_no}</p>}
                </div>
                <div className="flex items-end">
                  <p className="text-[10px] text-slate-400 italic pb-1.5">Blur to auto-fill passenger details if passport is in COPS</p>
                </div>
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-500 uppercase mb-1">
                  Address <span className="text-red-500">*</span>
                </label>
                <textarea
                  id="field-pax_address1"
                  rows={2}
                  className={`w-full px-3 py-1.5 border ${fieldErrors.pax_address1 ? 'border-red-500 ring-1 ring-red-500' : 'border-slate-300 focus:ring-blue-500'} rounded text-sm focus:ring-2 uppercase resize-none`}
                  value={formData.pax_address1}
                  onChange={e => { setFormData(prev => ({ ...prev, pax_address1: e.target.value.toUpperCase() })); clearFieldError('pax_address1'); }}
                  placeholder="Full residential address"
                />
                {fieldErrors.pax_address1 && <p className="mt-1 text-xs font-semibold text-red-600">{fieldErrors.pax_address1}</p>}
              </div>
            </div>
          </div>
        </div>

        {/* ── Additional Details (collapsible) ─────────────────────────────── */}
        <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
          <button
            type="button"
            onClick={() => setAdditionalOpen(o => !o)}
            className="w-full flex items-center justify-between px-5 py-3.5 text-left hover:bg-slate-50 transition-colors"
          >
            <span className="text-sm font-bold text-slate-700 uppercase tracking-wider flex items-center">
              <Plane className="mr-2 text-slate-400" size={15} /> Additional Details
              <span className="ml-2 text-xs font-normal text-slate-400 normal-case">(optional)</span>
            </span>
            <span className="text-slate-400 text-lg leading-none">{additionalOpen ? '▲' : '▼'}</span>
          </button>
          {additionalOpen && (
            <div className="px-5 pb-5 pt-2 border-t border-slate-100">
              <div className="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-4 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-500 uppercase mb-1">DOB</label>
                  <DatePicker
                    value={optionalData.pax_date_of_birth}
                    onChange={d => setOptionalData(prev => ({ ...prev, pax_date_of_birth: d }))}
                    inputClassName="w-full px-3 py-2 bg-slate-50 border border-slate-300 focus:ring-blue-500 rounded focus:ring-2 text-sm"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-500 uppercase mb-1">Passport Date / Expiry</label>
                  <DatePicker
                    value={optionalData.passport_date}
                    onChange={d => setOptionalData(prev => ({ ...prev, passport_date: d }))}
                    inputClassName="w-full px-3 py-2 bg-slate-50 border border-slate-300 focus:ring-blue-500 rounded focus:ring-2 text-sm"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-500 uppercase mb-1">Place of Issue</label>
                  <input
                    type="text"
                    className="w-full px-3 py-2 bg-slate-50 border border-slate-300 rounded focus:ring-2 focus:ring-blue-500 text-sm uppercase"
                    value={optionalData.pp_issue_place}
                    onChange={e => setOptionalData(prev => ({ ...prev, pp_issue_place: e.target.value.toUpperCase() }))}
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-500 uppercase mb-1">Father's Name</label>
                  <input
                    type="text"
                    className="w-full px-3 py-2 bg-slate-50 border border-slate-300 rounded focus:ring-2 focus:ring-blue-500 text-sm uppercase"
                    value={optionalData.father_name}
                    onChange={e => setOptionalData(prev => ({ ...prev, father_name: e.target.value.toUpperCase() }))}
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-500 uppercase mb-1">Normal Resident At</label>
                  <input
                    type="text"
                    className="w-full px-3 py-2 bg-slate-50 border border-slate-300 rounded focus:ring-2 focus:ring-blue-500 text-sm uppercase"
                    value={optionalData.residence_at}
                    onChange={e => setOptionalData(prev => ({ ...prev, residence_at: e.target.value.toUpperCase() }))}
                    placeholder="e.g. INDIA, ABROAD"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-500 uppercase mb-1">Old Passport Nos</label>
                  <input
                    type="text"
                    className="w-full px-3 py-2 bg-slate-50 border border-slate-300 rounded focus:ring-2 focus:ring-blue-500 text-sm uppercase"
                    value={optionalData.old_passport_no}
                    onChange={e => setOptionalData(prev => ({ ...prev, old_passport_no: e.target.value.toUpperCase() }))}
                    placeholder="Separate with ;"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-500 uppercase mb-1">Case Type</label>
                  <select
                    className="w-full px-3 py-2 bg-slate-50 border border-slate-300 rounded focus:ring-2 focus:ring-blue-500 text-sm"
                    value={optionalData.case_type}
                    onChange={e => setOptionalData(prev => ({ ...prev, case_type: e.target.value }))}
                  >
                    <option>Non-Bonafide</option>
                    <option>Mis-Declaration</option>
                    <option>Concealment</option>
                    <option>Trade Goods</option>
                    <option>Unclaimed</option>
                    <option>Export Case</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-500 uppercase mb-1">Shift</label>
                  <select
                    className="w-full px-3 py-2 bg-slate-50 border border-slate-300 rounded focus:ring-2 focus:ring-blue-500 text-sm"
                    value={optionalData.shift}
                    onChange={e => setOptionalData(prev => ({ ...prev, shift: e.target.value }))}
                  >
                    <option>Day</option>
                    <option>Night</option>
                  </select>
                </div>
                <div className="col-span-2 md:col-span-3 xl:col-span-4">
                  <label className="block text-xs font-semibold text-slate-500 uppercase mb-1">Supdt's Remarks</label>
                  <textarea
                    rows={3}
                    className="w-full px-3 py-2 bg-slate-50 border border-slate-300 rounded focus:ring-2 focus:ring-blue-500 text-sm resize-none"
                    value={optionalData.supdts_remarks}
                    onChange={e => setOptionalData(prev => ({ ...prev, supdts_remarks: e.target.value }))}
                    maxLength={1500}
                    placeholder="Optional remarks..."
                  />
                  <p className="text-right text-[10px] text-slate-400 mt-0.5">{optionalData.supdts_remarks.length}/1500</p>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* ── Seized Goods Registration ─────────────────────────────────────── */}
        <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
          <div className="p-4 border-b border-slate-200 bg-slate-50 flex justify-between items-center">
            <h2 className="text-sm font-bold text-slate-800 uppercase flex items-center tracking-wider">
              <FileText className="mr-2 text-orange-500" size={16} /> Seized Goods Registration
              <span className="ml-2 text-red-500 text-xs font-bold">*</span>
            </h2>
            <button
              type="button"
              onClick={() => setItems(prev => [...prev, {
                items_desc: '', items_qty: 1, items_uqc: 'NOS', items_value: 0, items_duty_type: 'Miscellaneous-22'
              }])}
              className="text-xs px-3 py-1.5 bg-white text-orange-700 hover:bg-orange-50 border border-orange-200 rounded font-bold flex items-center transition-colors uppercase tracking-wider"
            >
              <Plus size={14} className="mr-1" /> Add Item
            </button>
          </div>
          {fieldErrors.items && (
            <p className="px-4 py-2 text-xs font-semibold text-red-600 bg-red-50 border-b border-red-100">{fieldErrors.items}</p>
          )}
          <div className="overflow-auto">
            <table className="w-full text-sm text-left whitespace-nowrap">
              <thead className="text-[10px] text-slate-500 uppercase bg-slate-100 border-b border-slate-200 tracking-wider">
                <tr>
                  <th className="px-3 py-2 font-bold text-center w-10">S.No</th>
                  <th className="px-3 py-2 font-bold w-56">Description of Goods</th>
                  <th className="px-3 py-2 font-bold w-36 text-center">Quantity &amp; Unit</th>
                  <th className="px-3 py-2 font-bold w-28 text-right">Value (₹)</th>
                  <th className="px-3 py-2 font-bold w-40">Duty Type</th>
                  <th className="px-3 py-2 font-bold w-10"></th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 bg-white">
                {items.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="text-center py-8 text-slate-400">
                      Click "Add Item" to register seized goods.
                    </td>
                  </tr>
                ) : (
                  items.map((itm, idx) => (
                    <SimpleItemRow
                      key={idx}
                      itm={itm}
                      idx={idx}
                      rowErrors={itemErrors[idx]}
                      updateItem={updateItem}
                      onRemove={onRemove}
                      onDescBlur={onDescBlur}
                      descDatalistId="offline-item-desc-datalist"
                    />
                  ))
                )}
              </tbody>
              {items.length > 0 && (
                <tfoot className="bg-slate-50 border-t border-slate-200">
                  <tr>
                    <td colSpan={3} className="px-3 py-2 text-xs font-bold text-slate-600 uppercase text-right">Total Value:</td>
                    <td className="px-2 py-2 text-right font-bold text-sm text-slate-800">
                      ₹ {totalValue.toLocaleString('en-IN', { maximumFractionDigits: 2 })}
                    </td>
                    <td colSpan={2} />
                  </tr>
                </tfoot>
              )}
            </table>
          </div>
        </div>

        {/* ── Submit ────────────────────────────────────────────────────────── */}
        <div className="flex items-center justify-end gap-3 pt-2">
          <button
            type="button"
            onClick={() => navigate('/sdo')}
            className="px-5 py-2 border border-slate-300 bg-white text-slate-700 font-semibold rounded-lg hover:bg-slate-50 transition-colors text-sm"
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={isSubmitting}
            className="px-6 py-2 bg-blue-700 text-white font-semibold rounded-lg hover:bg-blue-600 transition-colors text-sm disabled:opacity-60 flex items-center gap-2"
          >
            {isSubmitting ? (
              <>
                <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"></span>
                Saving...
              </>
            ) : 'Save Offline Case'}
          </button>
        </div>
      </form>
    </div>
  );
}
