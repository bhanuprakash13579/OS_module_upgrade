import { useEffect, useRef, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, Printer } from 'lucide-react';
import api from '../../lib/api';

export default function OSPrintView() {
  const { os_no, os_year } = useParams();
  const navigate = useNavigate();
  const [data, setData] = useState<any>(null);
  const [otherPpOffences, setOtherPpOffences] = useState<string>('NIL');
  const [loading, setLoading] = useState(true);
  // Versioned config for the OS date
  const [pitConfig, setPitConfig] = useState<any>(null);
  // Pre-generated PDF promise — starts in background as soon as data loads
  const pdfPromiseRef = useRef<Promise<ArrayBuffer> | null>(null);

  const UQC_LABEL: Record<string, string> = {
    NOS: 'Nos.', STK: 'Sticks', KGS: 'Kgs.',
    GMS: 'Gms.', LTR: 'Ltrs.', MTR: 'Mtrs.', PRS: 'Pairs',
  };
  const uqcLabel = (code: string) => UQC_LABEL[(code || '').toUpperCase()] ?? (code || 'Nos.');

  const getDayOrNight = (shift: string | undefined) => {
    if (!shift) return '';
    const s = shift.toUpperCase();
    if (s.includes('A') || s.includes('B') || s.includes('DAY')) return '(D)';
    if (s.includes('C') || s.includes('D') || s.includes('NIGHT')) return '(N)';
    return '';
  };

  useEffect(() => {
    const fetchRecord = async () => {
      try {
        setLoading(true);
        // We can just use the search endpoint for one exact match
        const response = await api.post('/os-query/search', {
          os_no: os_no,
          os_year: parseInt(os_year || '0', 10),
          page: 1, limit: 1
        });
        if (response.data.items && response.data.items.length > 0) {
          const fetchedData = response.data.items[0];
          setData(fetchedData);

          // Fetch versioned config for OS date
          try {
            const pitRes = await api.get('/admin/config/pit', { params: { ref_date: fetchedData.os_date } });
            setPitConfig(pitRes.data);
          } catch { setPitConfig(null); }

          // Fetch other PP offences for same passenger
          try {
            const ppRes = await api.post('/os-query/search', {
              pax_name: fetchedData.pax_name,
              page: 1, limit: 20
            });
            // Filter out the current OS record
            const otherOffences = ppRes.data.items.filter((item: any) => 
               item.os_no !== fetchedData.os_no || item.os_year !== fetchedData.os_year
            );
            if (otherOffences.length > 0) {
               setOtherPpOffences(otherOffences.map((o: any) => `${o.passport_no} (OS ${o.os_no}/${o.os_year})`).join(', '));
            } else {
               setOtherPpOffences('NIL');
            }
          } catch(e) {
             setOtherPpOffences('NIL');
          }
        }
      } catch (err) {
        console.error("Failed to load OS record", err);
      } finally {
        setLoading(false);
      }
    };
    if (os_no && os_year) fetchRecord();
  }, [os_no, os_year]);

  // Pre-generate the PDF in the background as soon as the record loads
  useEffect(() => {
    if (data && os_no && os_year) {
      pdfPromiseRef.current = api
        .get(`/os/${os_no}/${os_year}/print-pdf`, { responseType: 'arraybuffer' })
        .then((r) => r.data);
    }
  }, [data, os_no, os_year]);

  if (loading) return <div className="p-10 text-center">Loading record...</div>;
  if (!data) return <div className="p-10 text-center text-red-500">Record not found.</div>;

  // ── Point-in-time config helpers ──────────────────────────────────────────
  const ptc = pitConfig?.print_template ?? {};
  const pitText = (key: string, fallback: string): string =>
    ptc[key]?.field_value ?? fallback;

  const colFaHeading     = pitText('col_fa_heading',     "Goods Allowed Free Under Rule 5 / Rule 13 of Baggage Rules, 1994");
  const colLiableHeading = pitText('col_liable_heading', "Goods Liable to Action Under FEMA / Foreign Trade Act, 1992 & Customs Act, 1962");
  const summaryDutyText  = pitText('summary_duty_text',   "Value of Goods Charged to Duty Under Foreign Trade (D&R) Act, 1992 & Customs Act, 1962");
  const summaryLiableText = pitText('summary_liable_text', "Value of Goods Liable to Action under FEMA / Foreign Trade (D&R) Act, 1992 & Customs Act 1962");

  const handlePrint = async () => {
    // Use the pre-generated PDF (started when page loaded); fall back to a fresh request
    const pdfReady = pdfPromiseRef.current
      ?? api.get(`/os/${os_no}/${os_year}/print-pdf`, { responseType: 'arraybuffer' }).then((r) => r.data);

    try {
      const { save } = await import('@tauri-apps/plugin-dialog');
      const { writeFile } = await import('@tauri-apps/plugin-fs');

      const [savePath, pdfData] = await Promise.all([
        save({
          title: 'Save OS Print',
          defaultPath: `OS_${os_no}_${os_year}.pdf`,
          filters: [{ name: 'PDF', extensions: ['pdf'] }],
        }),
        pdfReady,
      ]);

      if (savePath) {
        await writeFile(savePath, new Uint8Array(pdfData));
      }
    } catch {
      // Fallback: browser download (non-Tauri / web mode)
      try {
        const pdfData = await pdfReady;
        const blob = new Blob([pdfData], { type: 'application/pdf' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `OS_${os_no}_${os_year}.pdf`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        setTimeout(() => URL.revokeObjectURL(url), 5000);
      } catch (e) {
        console.error('Failed to generate PDF:', e);
        alert('Could not generate PDF. Please try again.');
      }
    }
  };

  const formatDate = (dateStr: string) => {
    if (!dateStr) return '—';
    try {
      return new Date(dateStr).toLocaleDateString('en-GB');
    } catch {
      return dateStr;
    }
  };

  const numberToWords = (num: number): string => {
    if (num === 0) return 'Zero';
    const a = ['', 'one ', 'two ', 'three ', 'four ', 'five ', 'six ', 'seven ', 'eight ', 'nine ', 'ten ', 'eleven ', 'twelve ', 'thirteen ', 'fourteen ', 'fifteen ', 'sixteen ', 'seventeen ', 'eighteen ', 'nineteen '];
    const b = ['', '', 'twenty', 'thirty', 'forty', 'fifty', 'sixty', 'seventy', 'eighty', 'ninety'];
    
    if (num < 20) return a[num];
    if (num < 100) return b[Math.floor(num / 10)] + (num % 10 !== 0 ? ' ' + a[num % 10] : '');
    if (num < 1000) return a[Math.floor(num / 100)] + 'hundred' + (num % 100 !== 0 ? ' and ' + numberToWords(num % 100) : '');
    if (num < 100000) return numberToWords(Math.floor(num / 1000)) + ' thousand' + (num % 1000 !== 0 ? ' ' + numberToWords(num % 1000) : '');
    if (num < 10000000) return numberToWords(Math.floor(num / 100000)) + ' lakh' + (num % 100000 !== 0 ? ' ' + numberToWords(num % 100000) : '');
    return numberToWords(Math.floor(num / 10000000)) + ' crore' + (num % 10000000 !== 0 ? ' ' + numberToWords(num % 10000000) : '');
  };

  // Proportional FA helper — mirrors backend _eff_fa
  const effFa = (item: any): number => {
    const val = Number(item.items_value) || 0;
    const rc = (item.items_release_category || '').toUpperCase();
    if (!['UNDER DUTY', 'UNDER OS', 'RF', 'REF', 'CONFS'].includes(rc)) return 0;
    if ((item.items_fa_type || 'value') === 'qty') {
      const totalQty = Number(item.items_qty) || 0;
      const faQty = Number(item.items_fa_qty) || 0;
      return totalQty > 0 ? Math.min((faQty / totalQty) * val, val) : 0;
    }
    return Number(item.items_fa) || 0;
  };


  // Compute category-wise values from item-level release categories
  // Add a 1-based index (displaySno) to align the ORDER paragraph serials with the table rows
  const items = (data.items || []).map((itm: any, idx: number) => ({ ...itm, displaySno: idx + 1 }));

  // Sum effective FA across all items that have FA (Under Duty + Under OS)
  const totalFAValueMonetary = items
    .filter((i: any) => {
      const rc = (i.items_release_category || 'Under OS').toUpperCase();
      return (rc === 'UNDER DUTY' || rc === 'UNDER OS' || rc === 'RF' || rc === 'REF') && (i.items_fa_type || 'value') === 'value';
    })
    .reduce((sum: number, i: any) => sum + effFa(i), 0);
  // Format qty without trailing decimal zeros
  const fmtQty = (q: number | string) => {
    const n = Number(q);
    return n % 1 === 0 ? Math.trunc(n).toString() : String(q);
  };
  // Qty-based FA items for the summary label
  const qtyFaList = items
    .filter((i: any) => {
      const rc = (i.items_release_category || 'Under OS').toUpperCase();
      return (rc === 'UNDER DUTY' || rc === 'UNDER OS' || rc === 'RF' || rc === 'REF') && (i.items_fa_type || 'value') === 'qty' && i.items_fa_qty;
    })
    .map((i: any) => `${fmtQty(i.items_fa_qty)} ${uqcLabel(i.items_fa_uqc || '')} of ${i.items_desc}`)
    .join(' & ');
  // "Under Duty" = goods passed on duty (not seized)
  const totalDutiableValue = items
    .filter((i: any) => i.items_release_category === 'Under Duty')
    .reduce((sum: number, i: any) => sum + Math.max(0, (Number(i.items_value) || 0) - effFa(i)), 0);
  // "Liable" = Under OS + RF + REF + CONFS items (value after FA deduction)
  const LIABLE_CATS = ['CONFS', 'ABS_CONFS', 'RE_EXP', 'RF', 'REF', 'UNDER OS'];
  const totalLiableValue = items
    .filter((i: any) => LIABLE_CATS.includes((i.items_release_category || 'Under OS').toUpperCase()))
    .reduce((sum: number, i: any) => sum + Math.max(0, (i.items_value || 0) - effFa(i)), 0);
  // Grand Total for the inventory = liable items value after FA
  const totalItemsValue = totalLiableValue || (data.total_items_value || 0);
  // Compute category values for the ORDER paragraph
  const rfItemsValue = items.filter((i: any) => i.items_release_category === 'RF').reduce((s: number, i: any) => s + Math.max(0, (i.items_value || 0) - effFa(i)), 0);
  const refItemsValue = items.filter((i: any) => i.items_release_category === 'REF').reduce((s: number, i: any) => s + Math.max(0, (i.items_value || 0) - effFa(i)), 0);
  const confsItemsValue = items.filter((i: any) => i.items_release_category === 'CONFS').reduce((s: number, i: any) => s + Math.max(0, (i.items_value || 0) - effFa(i)), 0);
  const hasRfItems = rfItemsValue > 0;
  const hasRefItems = refItemsValue > 0;
  const hasConfsItems = confsItemsValue > 0;
  // Fallback: if no items are categorized, use master-level values
  let confValue = hasRfItems ? rfItemsValue : (data.confiscated_value || totalItemsValue);
  const reExpValue = hasRefItems ? refItemsValue : (data.re_export_value || 0);
  let absConfValue = hasConfsItems ? confsItemsValue : 0;

  // "If there is no redemption fine, it means it is absolutely confiscated"
  if ((data.rf_amount || 0) === 0 && confValue > 0) {
    absConfValue += confValue;
    confValue = 0;
  }

  // Serial numbers grouped by disposal category (for ORDER paragraph)
  const rfSlNos = items.filter((i: any) => i.items_release_category === 'RF').map((i: any) => i.displaySno);
  const refSlNos = items.filter((i: any) => i.items_release_category === 'REF').map((i: any) => i.displaySno);
  const confsSlNos = items.filter((i: any) => i.items_release_category === 'CONFS').map((i: any) => i.displaySno);

  // Calculate prev offences count
  const otherPpOffencesCount = otherPpOffences === 'NIL' ? 0 : otherPpOffences.split(',').length;
  // Use DB field if it's purely a number, otherwise use the computed count
  const prevOffenceCountDisplay = (data.previous_visits && /^\d+$/.test(data.previous_visits)) ? data.previous_visits : otherPpOffencesCount;

  return (
    <div className="bg-slate-200 min-h-screen pb-10 print:bg-white print:p-0 print:min-h-0 print:overflow-visible">
      
      {/* Top action bar - hidden in print */}
      <div className="bg-white border-b border-slate-300 p-4 flex justify-between items-center sticky top-0 z-50 print:hidden shadow-sm print-hide-bar" data-print-hide="true">
        <button onClick={() => navigate(-1)} className="flex items-center gap-2 text-sm font-medium text-slate-600 hover:text-slate-900">
          <ArrowLeft className="w-4 h-4" /> Back to Search
        </button>
        <div className="flex gap-3">
          <button onClick={handlePrint} className="flex items-center gap-2 bg-emerald-600 text-white px-4 py-2 rounded shadow text-sm font-medium hover:bg-emerald-700 transition">
            <Printer className="w-4 h-4" /> Print Legal Order (Both Sides)
          </button>
        </div>
      </div>

      {/* Pages Container */}
      <div id="os-print-pages" className="max-w-[8.5in] mx-auto mt-8 print:mt-0 print:max-w-none print:w-[8.5in] text-black leading-tight print:leading-tight space-y-8 print:space-y-0" style={{ fontFamily: '"Times New Roman", Times, serif', fontSize: '10.5pt' }}>
        
        {/* --- PAGE 1: BOOKING REPORT --- */}
        <div className="bg-white p-8 shadow-md print:shadow-none relative print:w-[8.5in] box-border print:px-6 print:py-4 flex flex-col print:block" style={{ pageBreakAfter: 'always' }}>
          
          {/* Header */}
          <div className="border-4 border-solid border-black p-2 flex items-center mb-4 min-h-[5rem]">
            {/* Real Logo */}
            <div className="w-1/6 flex justify-center">
              <img src="/customs-logo.jpg" alt="Indian Customs Logo" className="w-16 h-16 object-contain grayscale print:grayscale" />
            </div>
            {/* Header Text */}
            <div className="w-5/6 text-center font-bold flex flex-col justify-center">
              <div className="text-2xl leading-none tracking-tight">Office of the Deputy / Asst. Commissioner of Customs</div>
              <div className="text-lg leading-tight mt-1">(Airport), Anna International Airport, Chennai-600027</div>
            </div>
          </div>

          <h2 className="text-lg font-bold uppercase text-center mb-6">Detention / Seizure of Passenger's Baggage</h2>
          
          <table className="w-full border-collapse border-4 border-solid border-black mb-4 text-left" style={{ fontSize: '10.5pt', tableLayout: 'fixed' }}>
            <colgroup>
              <col style={{ width: '18%' }} />
              <col style={{ width: '18%' }} />
              <col style={{ width: '12%' }} />
              <col style={{ width: '18%' }} />
              <col style={{ width: '16%' }} />
              <col style={{ width: '18%' }} />
            </colgroup>
            <tbody>
              <tr>
                <td className="border border-black border-b-4 px-1 py-0.5 align-top font-bold">O.S. No.</td>
                <td className="border border-black border-r-4 border-b-4 px-1 py-0.5 align-top uppercase">{data.os_no}/{data.os_year} ({data.booked_by || 'AIU'})</td>
                <td className="border border-black border-b-4 px-1 py-0.5 align-top font-bold">O.S. Date</td>
                <td className="border border-black border-r-4 border-b-4 px-1 py-0.5 align-top uppercase">{formatDate(data.os_date)}</td>
                <td className="border border-black border-b-4 px-1 py-0.5 align-top font-bold">Detention Date</td>
                <td className="border border-black border-b-4 px-1 py-0.5 align-top uppercase">{formatDate(data.detention_date || data.os_date)}</td>
              </tr>
              <tr>
                <td className="border border-black border-b-4 px-1 py-0.5 align-top font-bold" rowSpan={3} colSpan={1}>Full Name of Passenger<br/>With Address in India</td>
                <td className="border border-black border-r-4 border-b-4 p-1 align-top uppercase" rowSpan={3} colSpan={3} style={{ wordBreak: 'break-word', whiteSpace: 'normal' }}>
                  {data.pax_name}{data.father_name ? `, ${data.father_name}` : ''}{(data.pax_address1 || data.pax_address2) ? `, ${[data.pax_address1, data.pax_address2, data.pax_address3].filter(Boolean).join(', ')}` : ''}
                </td>
                <td className="border border-black border-b-4 px-1 py-0.5 align-top font-bold">Passport No. & Date</td>
                <td className="border border-black border-b-4 px-1 py-0.5 align-top uppercase">{data.passport_no} Dt. {formatDate(data.passport_date)}</td>
              </tr>
              <tr>
                <td className="border border-black border-b-4 px-1 py-0.5 align-top font-bold">Flight No. & Date</td>
                <td className="border border-black border-b-4 px-1 py-0.5 align-top uppercase">{data.flight_no} Dt. {formatDate(data.flight_date)}</td>
              </tr>
              <tr>
                <td className="border border-black border-b-4 px-1 py-0.5 align-top font-bold">From / To</td>
                <td className="border border-black border-b-4 px-1 py-0.5 align-top uppercase" style={{ wordBreak: 'break-word' }}>{data.port_of_dep_dest || data.country_of_departure || '—'} TO CHENNAI</td>
              </tr>
              <tr>
                <td className="border border-black border-b-4 px-1 py-0.5 align-top font-bold">Nationality</td>
                <td className="border border-black border-r-4 border-b-4 px-1 py-0.5 align-top uppercase" colSpan={3}>{data.nationality || data.pax_nationality || '—'}</td>
                <td className="border border-black border-b-4 px-1 py-0.5 align-top font-bold">Date of Departure</td>
                <td className="border border-black border-b-4 px-1 py-0.5 align-top uppercase">{data.date_of_departure || 'N.A.'}</td>
              </tr>
              <tr>
                <td className="border border-black border-b-4 px-1 py-0.5 align-top font-bold">Duration of Stay Abroad</td>
                <td className="border border-black border-r-4 border-b-4 px-1 py-0.5 align-top uppercase" colSpan={3}>{data.stay_abroad_days || '0'} Days</td>
                <td className="border border-black border-b-4 px-1 py-0.5 align-top font-bold">Normal Residence in</td>
                <td className="border border-black border-b-4 px-1 py-0.5 align-top uppercase" style={{ wordBreak: 'break-word' }}>{data.residence_at || data.country_of_departure || 'ABROAD'}</td>
              </tr>
              <tr>
                <td className="border border-black px-1 py-0.5 align-top font-bold">Previous Visits, if any</td>
                <td className="border border-black px-1 py-0.5 align-top uppercase" colSpan={5}>{data.previous_visits || 'NIL'}</td>
              </tr>
            </tbody>
          </table>

          <h3 className="text-center font-bold text-xl mb-2">INVENTORY OF THE GOODS IMPORTED</h3>
          
          <table className="w-full border-collapse border-4 border-solid border-black mb-4 text-center" style={{ fontSize: '9.5pt', tableLayout: 'fixed' }}>
            <colgroup>
              <col style={{ width: '5%' }} />
              <col style={{ width: '28%' }} />
              <col style={{ width: '10%' }} />
              <col style={{ width: '17%' }} />
              <col style={{ width: '18%' }} />
              <col style={{ width: '22%' }} />
            </colgroup>
            <thead>
              <tr>
                <th className="border-2 border-black border-solid p-0.5">S.No.</th>
                <th className="border-2 border-black border-solid p-0.5 text-left">Description of Goods</th>
                <th className="border-2 border-black border-solid p-0.5">Qty.</th>
                <th className="border-2 border-black border-solid p-0.5" style={{ fontSize: '8.5pt', lineHeight: '1.2' }}>{colFaHeading}</th>
                <th className="border-2 border-black border-solid p-0.5" style={{ fontSize: '8.5pt', lineHeight: '1.2' }}>Goods Passed On Duty<br/><span className="font-bold block mt-1">Value (in Rs.)</span></th>
                <th className="border-2 border-black border-solid p-0.5" style={{ fontSize: '8.5pt', lineHeight: '1.2' }}>{colLiableHeading}<br/><span className="font-normal">Total Value (in Rs.)</span></th>
              </tr>
            </thead>
            <tbody>
              {items.map((item: any) => {
                const fa = effFa(item);
                const rc = (item.items_release_category || 'Under OS').toUpperCase();
                const isLiable = ['CONFS', 'ABS_CONFS', 'RE_EXP', 'RF', 'REF', 'UNDER OS'].includes(rc);
                const isDuty = rc === 'UNDER DUTY';
                const isConfs = rc === 'CONFS';
                const dutiable = Math.max(0, (item.items_value || 0) - fa);
                const faType = item.items_fa_type || 'value';
                // FA display: show for Under Duty and Under OS/RF/REF items, but not CONFS
                const showFa = isDuty || (isLiable && !isConfs);
                const faDisplay = !showFa
                  ? '—'
                  : faType === 'qty'
                    ? (item.items_fa_qty ? `${fmtQty(item.items_fa_qty)} ${uqcLabel(item.items_fa_uqc || '')}`.trim() : '—')
                    : (fa > 0 ? fa.toLocaleString('en-IN') : '—');

                return (
                  <tr key={item.id || item.items_sno || item.displaySno}>
                    <td className="border-2 border-black border-solid p-0.5">{item.displaySno}</td>
                    <td className="border-2 border-black border-solid p-0.5 text-left uppercase" style={{ whiteSpace: 'normal', wordBreak: 'break-word' }}>{item.items_desc}</td>
                    <td className="border-2 border-black border-solid p-0.5">{Number(item.items_qty) % 1 === 0 ? Math.trunc(Number(item.items_qty)) : item.items_qty} {uqcLabel(item.items_uqc)}</td>
                    {/* FA Column */}
                    <td className="border-2 border-black border-solid p-0.5 text-right font-bold" style={{ fontSize: '9.5pt', wordBreak: 'break-word' }}>{faDisplay}</td>
                    {/* Goods Passed On Duty column — only for Under Duty items */}
                    <td className="border-2 border-black border-solid p-0.5 text-right font-bold" style={{ fontSize: '9.5pt' }}>
                      {isDuty && dutiable > 0 ? dutiable.toLocaleString('en-IN') : '—'}
                    </td>
                    {/* Goods Liable to Action column — Under OS/RF/REF/CONFS items */}
                    <td className="border-2 border-black border-solid p-0.5 text-right font-bold" style={{ fontSize: '9.5pt' }}>
                      {isLiable ? Math.max(0, (item.items_value || 0) - fa).toLocaleString('en-IN') : '—'}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>

          <table className="w-full border-collapse border-4 border-black border-solid mb-4" style={{ fontSize: '11pt' }}>
            <tbody>
              <tr>
                <td className="border-2 border-black border-solid px-2 py-1 font-bold whitespace-nowrap w-[1%]">Prev. Offence in Above PP No(s). as per COPS</td>
                <td className="border-2 border-black border-solid px-2 py-1 font-bold uppercase text-left break-words">{prevOffenceCountDisplay}</td>
              </tr>
              <tr>
                <td className="border-2 border-black border-solid px-2 py-1 font-bold whitespace-nowrap w-[1%]">Offences of Other PPs(if any)</td>
                <td className="border-2 border-black border-solid px-2 py-1 font-bold uppercase text-left break-words whitespace-pre-wrap">{otherPpOffences}</td>
              </tr>
            </tbody>
          </table>

          <table className="w-full border-collapse border-4 border-black border-solid flex-shrink-0" style={{ fontSize: '10pt', tableLayout: 'fixed' }}>
            <colgroup>
              <col style={{ width: '72%' }} />
              <col style={{ width: '28%' }} />
            </colgroup>
            <tbody>
              <tr>
                <td className="border-2 border-black border-b-0 border-solid px-2 py-0.5 align-top" style={{ wordBreak: 'break-word' }}>
                  Value of {colFaHeading}
                </td>
                <td className="border-2 border-black border-b-0 border-solid px-2 py-0.5 text-right font-bold align-top" style={{ wordBreak: 'break-word' }}>
                  Rs. {totalFAValueMonetary > 0 ? totalFAValueMonetary.toLocaleString('en-IN') : '0'}{totalFAValueMonetary > 0 ? '/-' : ''}
                  {qtyFaList && (
                    <span className="block text-[7pt] font-normal text-gray-600 mt-0.5 whitespace-normal">
                      (along with {qtyFaList})
                    </span>
                  )}
                </td>
              </tr>
              <tr>
                <td className="border-2 border-black border-b-0 border-solid px-2 py-0.5" style={{ wordBreak: 'break-word' }}>{summaryDutyText}</td>
                <td className="border-2 border-black border-b-0 border-solid px-2 py-0.5 text-right font-bold">Rs. {totalDutiableValue.toLocaleString('en-IN')}</td>
              </tr>
              <tr>
                <td className="border-2 border-black border-solid px-2 py-0.5 font-bold" style={{ wordBreak: 'break-word' }}>{summaryLiableText}</td>
                <td className="border-2 border-black border-solid px-2 py-0.5 text-right font-bold">Rs. {totalItemsValue.toLocaleString('en-IN')}</td>
              </tr>
            </tbody>
          </table>

          <div className="flex justify-between font-bold px-8 mt-12 mb-4" style={{ fontSize: '12pt' }}>
            <div>Name & Signature of Customs Officer</div>
            <div>Signature of Passenger</div>
          </div>

          <div className="mb-8 mt-8" style={{ fontSize: '12pt' }}>
            <span className="font-bold underline">Remarks: </span>
            <span className="text-justify break-words leading-tight ml-2 block mt-1">
              {data.supdts_remarks || 'NIL'}
            </span>
          </div>

          <div className="flex justify-end font-bold pr-8 mb-4" style={{ fontSize: '12pt' }}>
            <div>Supdt. of Customs</div>
          </div>

        </div>

        {/* --- PAGE 2: ADJUDICATION ORDER --- */}
        <div className="bg-white p-8 shadow-md print:shadow-none relative print:w-[8.5in] box-border print:px-6 print:py-4 flex flex-col print:block">
          
          <div className="w-full text-center">
            <span className="font-bold">Office of the Deputy / Asst. Commissioner of Customs (Airport), Anna International airport, Chennai-600027.</span>
          </div>

          <div className="w-full flex justify-between mt-4 mb-2">
            <div><span className="font-bold">Passenger Name:</span> <span className="uppercase">{data.pax_name}</span></div>
            <div>
               <span className="font-bold">OS No.</span> {data.os_no}/{data.os_year} ({data.booked_by || 'AIU'}) <span className="font-bold ml-2">Dated</span> {formatDate(data.os_date)} {getDayOrNight(data.shift || data.booked_by)}
            </div>
          </div>

          <div className="text-center font-bold underline uppercase mb-1">WAIVER OF SHOW CAUSE NOTICE</div>
          <div className="mb-2 text-justify indent-8">
            The Charges have been orally communicated to me in respect of the goods mentioned overleaf and imported by me. Orders in the case may please be passed without issue of Show Cause Notice. However I may kindly be given a Personal Hearing.
          </div>
          <div className="flex justify-end mb-2">
            <div className="w-[200px] text-center">
              <div className="h-4"></div>
              <p className="font-bold">Signature of Passenger</p>
            </div>
          </div>

          <div className="mb-2 text-justify indent-8">
            I was present during the personal hearing conducted by the Deputy/Asst. Commissioner and I was heard.
          </div>
          <div className="flex justify-end mb-4">
            <div className="w-[200px] text-center">
              <div className="h-4"></div>
              <p className="font-bold">Signature of Passenger</p>
            </div>
          </div>
        
          <div className="w-full flex justify-between mb-4">
            <div><span className="font-bold">Order Passed by:</span> Shri./Smt./Kum. <span className="uppercase">{data.adj_offr_name || '__________________________'}</span>, {data.adj_offr_designation || 'Deputy/Asst.commr.'}</div>
            <div><span className="font-bold">Date of Order / Issue:</span> {formatDate(data.adjudication_date || data.os_date)}</div>
          </div>

          <div className="text-center font-bold underline uppercase mb-2">ORDER (ORIGINAL)</div>
        
          <div className="mb-2 space-y-1 text-justify">
            <p><span className="font-bold">N.B: 1.</span> This copy is granted free of charge for the private use of the person to whom it is issued.</p>
            <p><span className="font-bold">2.</span> An Appeal against this Order shall lie before the Commissioner of Customs (Appeals), Custom House, Chennai-600 001 on payment of 7.5% of the duty demanded where duty or duty and penalty are in dispute, or penalty, where penalty alone is in dispute. The Appeal shall be filed within 60 days provided under Section 128 of the Customs Act, 1962 from the date of receipt of this Order.</p>
          </div>
          <p className="mb-2 indent-8"><span className="font-bold">Note: This issue of Show Cause Notice was waived at the instance of the Passenger.</span></p>

          <div className="mb-2 space-y-1 text-justify">
            <p className="indent-8">In terms of Foreign Trade Policy notified by the Government in pursuance to Section 3(1) & 3(2) of the Foreign Trade (Development & Regulation) Act, 1992 read with the Rules framed thereunder, also read with Section 11(2)(u) of Customs Act, 1962, import of 'goods in commercial quantity / goods in the nature of non-bonafide baggage’ is not permitted without a valid import licence, though exemption exists under clause 3(h) of the Foreign Trade (Exemption from application of Rules in certain cases) order 1993 for import of goods by a passenger from abroad only to the extent admissible under the Baggage Rules framed under Section 79 of the Customs Act, 1962.</p>
            <p className="indent-8">Import of goods non-declared / misdeclared / concealed / in trade and in commercial quantity / non-bonafide in excess of the baggage allowance is therefore liable for confiscation under Section 111(d), (i), (l), (m) & (o) of the Customs Act, 1962 read with Section 3(3) of the Foreign Trade (Development & Regulation) Act, 1992.</p>
          </div>

          <div className="font-bold underline text-center uppercase mb-1">RECORD OF PERSONAL HEARING & FINDINGS</div>
          <div className="mb-2 text-justify indent-8"
            dangerouslySetInnerHTML={{ __html: (data.adjn_offr_remarks || 'No remarks provided.').replace(/\n/g, '<br/>') }}
          />

          <div className="font-bold underline text-center uppercase mb-1">ORDER</div>
          <div className="mb-2 text-justify">
            {/* Sentence 1: Confiscation + RF clause (Redemption Fine items) */}
            {confValue > 0 && (data.rf_amount || 0) > 0 && (
              <p className="mb-1 indent-8">
                I Order confiscation of the goods{rfSlNos.length > 0 ? ` at Sl.No(s). ${rfSlNos.join(', ')}` : ''} valued at Rs.{confValue}/- under Section 111(d), (i), (l), (m) &amp; (o) of the Customs Act, 1962 read with Section 3(3) of Foreign Trade (D&amp;R) Act, 1992, but allow the passenger an option to redeem the goods valued at Rs.{confValue}/- on a fine of Rs.{data.rf_amount}/- (Rupees {numberToWords(data.rf_amount || 0).trim().replace(/\b\w/g, (l: string) => l.toUpperCase())} Only) in lieu of confiscation under Section 125 of the Customs Act 1962 within 7 days from the date of receipt of this Order, Duty extra.
              </p>
            )}

            {/* Sentence 2: Re-Export reship clause (REF items) */}
            {reExpValue > 0 && (data.ref_amount || 0) > 0 && (
              <p className="mb-1 indent-8">
                However, I give an option to reship the goods{refSlNos.length > 0 ? ` at Sl.No(s). ${refSlNos.join(', ')}` : ''} valued at Rs.{reExpValue}/- on a fine of Rs.{data.ref_amount}/- (Rupees {numberToWords(data.ref_amount || 0).trim().replace(/\b\w/g, (l: string) => l.toUpperCase())} Only) under Section 125 of the Customs Act 1962 within 1 Month from the date of this Order.
              </p>
            )}

            {/* Sentence 3: Absolute Confiscation */}
            {absConfValue > 0 && (
              <p className="mb-1 indent-8">
                I {(confValue > 0 || reExpValue > 0) ? 'also ' : ''}order absolute confiscation of the goods{confsSlNos.length > 0 ? ` at Sl.No(s). ${confsSlNos.join(', ')}` : ''} valued at Rs.{absConfValue}/- under Section 111(d), (i), (l), (m) &amp; (o) of the Customs Act, 1962 read with Section 3(3) of the Foreign Trade (D&amp;R) Act, 1992.
              </p>
            )}

            {/* Sentence 4: Personal Penalty */}
            {(data.pp_amount || 0) > 0 && (
              <p className="indent-8">
                I further impose a Personal Penalty of Rs.{data.pp_amount}/- (Rupees {numberToWords(data.pp_amount || 0).trim().replace(/\b\w/g, (l: string) => l.toUpperCase())} Only) under Section 112(a) of the Customs Act, 1962.
              </p>
            )}
          </div>

          <div className="flex justify-end mb-4">
            <div className="w-[300px] text-center">
              <div className="h-6"></div>
              <p className="font-bold">Deputy / Asst. Commissioner of Customs (Airport)</p>
            </div>
          </div>

          <div className="mb-3 text-justify">
            <p><span className="font-bold">N.B:</span> 1. Perishables will be disposed off within seven days from the date of detention.</p>
            <p>2. Where re-export is permitted, the passenger is advised to intimate the date of departure of flight atleast 48 hours in advance.</p>
            <p>3. Warehouse rent and handling charges are chargeable for goods detained.</p>
          </div>

          <table className="w-full border-collapse border-4 border-solid border-black mb-4">
            <tbody>
              <tr>
                <td className="border-2 border-black border-b-4 px-2 py-0.5 font-bold w-1/4">B.R.No. And Date</td>
                <td className="border-2 border-black border-r-4 border-b-4 px-2 py-0.5 w-1/4"></td>
                <td className="border-2 border-black border-b-4 px-2 py-0.5 font-bold w-1/4">Goods Detained Vide</td>
                <td className="border-2 border-black border-b-4 px-2 py-0.5 w-1/4">DR No. &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; Dt. &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;</td>
              </tr>
              <tr>
                <td className="border-2 border-black border-b-4 px-2 py-0.5 font-bold">Duty</td>
                <td className="border-2 border-black border-r-4 border-b-4 px-2 py-0.5">Rs. </td>
                <td className="border-2 border-black border-b-4 px-2 py-0.5 font-bold">Confiscated goods sent for disposal on</td>
                <td className="border-2 border-black border-b-4 px-2 py-0.5"></td>
              </tr>
              <tr>
                <td className="border-2 border-black border-b-4 px-2 py-0.5 font-bold">Redemption / Re-Export Fine</td>
                <td className="border-2 border-black border-r-4 border-b-4 px-2 py-0.5">Rs. </td>
                <td className="border-2 border-black border-b-4 px-2 py-0.5 font-bold">W.H.No. And Date</td>
                <td className="border-2 border-black border-b-4 px-2 py-0.5"></td>
              </tr>
              <tr>
                <td className="border-2 border-black border-b-4 px-2 py-0.5 font-bold">Personal Penalty</td>
                <td className="border-2 border-black border-r-4 border-b-4 px-2 py-0.5">Rs. </td>
                <td className="border-2 border-black border-b-4 px-2 py-0.5"></td>
                <td className="border-2 border-black border-b-4 px-2 py-0.5"></td>
              </tr>
              <tr>
                <td className="border-2 border-black px-2 py-0.5 font-bold">Cash Credit C.No. And Date</td>
                <td className="border-2 border-black border-r-4 px-2 py-0.5"></td>
                <td className="border-2 border-black px-2 py-0.5"></td>
                <td className="border-2 border-black px-2 py-0.5"></td>
              </tr>
            </tbody>
          </table>

          <div className="flex justify-end mb-4">
            <div>
              <p className="font-bold">Received the Order-in-Original</p>
            </div>
          </div>

          <div className="flex justify-between items-end">
            <div className="text-center">
              <div className="h-6"></div>
              <p className="font-bold">Signature of the Baggage Officer</p>
            </div>
            <div className="text-center">
              <div className="h-6"></div>
              <p className="font-bold">Signature of the Passenger</p>
            </div>
          </div>

        </div>

      </div>

    </div>
  );
}
