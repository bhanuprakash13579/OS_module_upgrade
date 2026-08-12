(function () {
  'use strict';
  if (window.__BRC_LOADED) return;
  window.__BRC_LOADED = true;

  // Build stamp. A bookmarklet lives as a copy inside the browser's bookmark —
  // editing this file does NOT update it, so a fixed bug can keep reappearing
  // simply because the bookmark still holds an older build. Bump this on every
  // change; it prints to the console on load and shows in the panel header, so
  // "which build is actually running?" is answerable in two seconds instead of
  // being re-debugged from symptoms.
  const BUILD = '2026-08-12.2';
  window.__BRC_BUILD = BUILD;
  try { console.log('%c Atithi Helper build ' + BUILD + ' loaded ', 'background:#6366f1;color:#fff'); } catch { }

  // ── DUTY RATES (auto-calc for columns the real site doesn't show) ──────
  // Base set mirrors the default DrTariff seed rates from the OS_module_upgrade
  // revenue-report module (backend/app/main.py::_seed_duty_report_defaults),
  // expressed as whole percentages for the panel UI (divide by 100 when
  // computing). Verified against official sources (2026-07):
  //   - Gold/Silver non-eligible passenger: 35% BCD + 5% AIDC = 40% total,
  //     matching Notification 45/2025-Customs (24.10.2025) as revised by the
  //     May 2026 AIDC/SWS rationalisation (Notification 16/2026-Customs,
  //     12.05.2026) — gold_bcd_rate + aidc_gold_rate already totalled 40%.
  //   - Gold eligible passenger (concessional): 10% BCD + 5% AIDC = 15%
  //     total — matches the same May 2026 rationalisation, which also raised
  //     the Notification 57/2000-Customs-linked concessional BCD from 5%→10%.
  //     gold_cons_bcd_rate + aidc_gold_cons_rate already totalled 15%.
  //   - Liquor (wine/spirits, not beer): 50% duty + 100% AIDC = 150% total —
  //     confirmed verbatim by CBIC's own "Customs Clearance of Passengers At
  //     a Glance" (the same Atithi BO letterhead as the real site): "BCD @
  //     50% + AIDC @100%". NOTE: that document gives BEER its own, lower
  //     rate — "BCD @ 100% + SWS 10%" (110% total) — which this extension
  //     does NOT currently distinguish from other liquor; flag if the real
  //     site's item-type list separates beer out.
  //   - Baggage (general goods): officer-confirmed this is 35% total, flat —
  //     no separate SWS layered on top for this category, so baggage_rate
  //     is the WHOLE "Baggage duty" figure and 'SW SC' is left blank/manual
  //     for baggage rows (differs from the generic CBIC traveller-guide PDF,
  //     which showed 35%+10% SWS=38.5% — trusting the officer's first-hand
  //     read of the real system over that generic doc here).
  //   - Cigarette duty: BCD 60% + SWS 10% of BCD (6%) + GST/IGST 40%
  //     (compounded on Value+BCD+SWS, per the standard IGST-on-landed-cost
  //     formula) — the GST piece is a real, confirmable ad-valorem rate, so
  //     it's folded into 'Cigarette duty' alongside BCD (no separate GST
  //     column exists in this template); 'SW SC' still carries just the SWS
  //     component. This models to ~132.4% total, not the officer's 230.2% —
  //     the remaining gap is a per-1000-sticks Additional Excise Duty
  //     (₹2,050–8,500, effective Feb 2026) that's a fixed rupee amount, not
  //     a %, so it genuinely can't be reduced to one constant rate; it
  //     varies with cigarette price/length. 'Total Duty' (always read from
  //     the site) still captures the true final number regardless.
  //   - sws_pct_of_bcd: 10% of BCD, applied only to Cigarette's 'SW SC' —
  //     Liquor (wine/spirits) uses AIDC instead of SWS, Gold/Silver's
  //     passenger-baggage duty has no SWS component, and Baggage doesn't
  //     get a separate SWS line per the officer's correction above.
  //   - cigarette_gst_rate (NEW): 40%, current tobacco GST slab (replaced
  //     28% + GST Compensation Cess on 1 Feb 2026).
  //   - Silver concessional (silver_cons_rate/aidc_silver_cons_rate) wasn't
  //     part of what was flagged as changed, so it's left as-is — worth
  //     double-checking if the May 2026 rationalisation affected it too.
  const DUTY_RATE_DEFAULTS = {
    baggage_rate: 35, liquor_duty_rate: 50, aidc_liquor_rate: 100,
    gold_bcd_rate: 35, aidc_gold_rate: 5,
    gold_cons_bcd_rate: 10, aidc_gold_cons_rate: 5,
    silver_cons_rate: 5, aidc_silver_cons_rate: 5,
    cigarette_duty_rate: 60, sws_pct_of_bcd: 10, cigarette_gst_rate: 40
  };
  const DUTY_RATE_LABELS = {
    baggage_rate: 'Baggage Duty %  (flat total — no separate SWS for this category)',
    liquor_duty_rate: 'Liquor Duty %  (wine/spirits — not beer)',
    aidc_liquor_rate: 'AIDC on Liquor %',
    gold_bcd_rate: 'Gold/Silver Duty (BCD) %  (normal, non-concessional — totals 40% with AIDC below)',
    aidc_gold_rate: 'AIDC on Gold/Silver %  (normal, non-concessional)',
    gold_cons_bcd_rate: 'Gold Duty (Concessional) %  (totals 15% with AIDC below)',
    aidc_gold_cons_rate: 'AIDC on Gold (Concessional) %',
    silver_cons_rate: 'Silver Duty (Concessional) %',
    aidc_silver_cons_rate: 'AIDC on Silver (Concessional) %',
    cigarette_duty_rate: 'Cigarette Duty (BCD) %',
    sws_pct_of_bcd: 'Social Welfare Surcharge % of BCD  (Cigarette only → "SW SC")',
    cigarette_gst_rate: 'Cigarette GST/IGST %  (compounded on Value+BCD+SWS; NCCD/AED still manual)'
  };
  // Item descriptions that skip the plain "Baggage duty" formula — same
  // exclusion list ("_SKIP") as the reference project's default rule set.
  const BAGGAGE_DUTY_SKIP = ['GOLD', 'SILVER', 'LIQUOR', 'OTHER', 'CIGARETTE', 'GOLD(C)', 'SILVER(C)', 'RE-EXPORT', 'REEXPORT'];

  // Computes only the duty columns we have a known formula for, based on this
  // row's Item Description + Total Dutiable Value — mirrors the reference
  // project's condition_type="only"/"except" rule matching exactly (GOLD and
  // SILVER share one BCD/AIDC pair; GOLD(C) and SILVER(C) each concessional).
  function computeAutoDuty(itemDesc, value, rates) {
    const desc = String(itemDesc || '').toUpperCase().trim();
    const out = {};
    if (!desc || !value) return out;
    const r = (k) => ((rates && rates[k] !== undefined ? rates[k] : DUTY_RATE_DEFAULTS[k]) || 0) / 100;
    if (desc === 'LIQUOR') {
      out['Liquor duty'] = value * r('liquor_duty_rate');
      out['AIDC on Liquor'] = value * r('aidc_liquor_rate');
    } else if (desc === 'GOLD' || desc === 'SILVER') {
      out['Gold Duty (BCD)'] = value * r('gold_bcd_rate');
      out['AIDC Gold/Silver'] = value * r('aidc_gold_rate');
    } else if (desc === 'GOLD(C)') {
      out['Gold Duty (C)'] = value * r('gold_cons_bcd_rate');
      out['AIDC Gold/Silver'] = value * r('aidc_gold_cons_rate');
    } else if (desc === 'SILVER(C)') {
      out['Silver Duty (C)'] = value * r('silver_cons_rate');
      out['AIDC Gold/Silver'] = value * r('aidc_silver_cons_rate');
    } else if (desc === 'CIGARETTE') {
      const bcd = value * r('cigarette_duty_rate');
      const sws = bcd * r('sws_pct_of_bcd');
      const gst = (value + bcd + sws) * r('cigarette_gst_rate');
      out['Cigarette duty'] = bcd + gst;
      out['SW SC'] = sws;
    } else if (!BAGGAGE_DUTY_SKIP.includes(desc)) {
      out['Baggage duty'] = value * r('baggage_rate');
    }
    return out;
  }

  // ── STATE ──────────────────────────────────────────────────────
  const KEY = 'brc_state';
  const load = () => { try { return JSON.parse(localStorage.getItem(KEY)) || fresh(); } catch { return fresh(); } };
  const fresh = () => ({ columns: [], saveBtn: null, shifts: [], activeShiftId: null, mrzTargets: {}, bpTargets: {}, mrzTargetsAuto: {}, bpTargetsAuto: {}, defaultTargets: [], drafts: {}, dutyRates: { ...DUTY_RATE_DEFAULTS } });
  const save = () => localStorage.setItem(KEY, JSON.stringify(st));
  let st = load();
  // Backfill fields added in later versions for state saved by an older version.
  if (!st.defaultTargets) st.defaultTargets = [];
  // Seeded once, then owned by the officer — editable and deletable like any
  // other rule, and never re-added after that (the flag survives deletion).
  if (!st.defaultsSeeded) {
    st.defaultsSeeded = true;
    const has = sel => st.defaultTargets.some(t => t.selector === sel);
    if (!has('[formcontrolname="instantMessengerNumber"]')) {
      st.defaultTargets.push({
        id: 'seed_msgnum', label: 'Instant Messenger Number', mode: 'copy',
        sourceSelector: '[formcontrolname="mobile_no"]', sourceLabel: 'Mobile',
        selector: '[formcontrolname="instantMessengerNumber"]', value: ''
      });
    }
    if (!has('[formcontrolname="instantMessengerType"]')) {
      st.defaultTargets.push({
        id: 'seed_msgtype', label: 'Instant Messenger Type', mode: 'fixed',
        value: 'WhatsApp', selector: '[formcontrolname="instantMessengerType"]'
      });
    }
  }
  if (!st.mrzTargets) st.mrzTargets = {};
  if (!st.bpTargets) st.bpTargets = {};
  if (!st.mrzTargetsAuto) st.mrzTargetsAuto = {};
  if (!st.bpTargetsAuto) st.bpTargetsAuto = {};
  if (!st.drafts) st.drafts = {};
  if (!st.dutyRates) st.dutyRates = { ...DUTY_RATE_DEFAULTS };

  // ── AUTOMATIC 12-HOUR SHIFTS (07:00–19:00 Day, 19:00–07:00 Night) ────────
  // No manual Start/End Shift anymore — a captured row files itself into
  // whichever fixed 12-hour window "now" falls into, and Download always
  // exports that window's rows. shiftWindowFor() computes the boundary that
  // contains a given moment; getShiftBucket() finds/creates the row-store
  // for it (auto-created on first use, never null).
  function shiftWindowFor(date) {
    const d = new Date(date);
    const hour = d.getHours();
    let start, end, label;
    if (hour >= 7 && hour < 19) {
      start = new Date(d); start.setHours(7, 0, 0, 0);
      end = new Date(d); end.setHours(19, 0, 0, 0);
      label = 'Day';
    } else if (hour >= 19) {
      start = new Date(d); start.setHours(19, 0, 0, 0);
      end = new Date(d); end.setDate(end.getDate() + 1); end.setHours(7, 0, 0, 0);
      label = 'Night';
    } else {
      start = new Date(d); start.setDate(start.getDate() - 1); start.setHours(19, 0, 0, 0);
      end = new Date(d); end.setHours(7, 0, 0, 0);
      label = 'Night';
    }
    const id = `${start.getFullYear()}-${String(start.getMonth() + 1).padStart(2, '0')}-${String(start.getDate()).padStart(2, '0')}-${label}`;
    return { id, start, end, label };
  }

  function getShiftBucket(win) {
    let s = st.shifts.find(s => s.id === win.id);
    if (!s) {
      s = { id: win.id, name: `${win.label} Shift ${win.start.toLocaleDateString('en-GB')}`, startTime: win.start.toISOString(), endTime: win.end.toISOString(), rows: [] };
      st.shifts.push(s); save();
    }
    return s;
  }

  // Where a row captured RIGHT NOW gets filed — always the literal current
  // window, full stop (never falls back to a previous one; only Download,
  // below, does that).
  function activeShift() {
    return getShiftBucket(shiftWindowFor(new Date()));
  }

  // What the Download button exports. Same window as above, EXCEPT: if that
  // window is still empty and started very recently (within SHIFT_GRACE_MS),
  // the officer almost certainly just crossed the 7:00/19:00 boundary and
  // wants the shift that just ended, not a fresh empty one — e.g.
  // downloading at 7:05pm still expecting the 7am–7pm shift's data.
  const SHIFT_GRACE_MS = 2 * 60 * 60 * 1000; // 2 hours
  function downloadShift() {
    const now = new Date();
    const win = shiftWindowFor(now);
    const bucket = getShiftBucket(win);
    if (!bucket.rows.length && (now - win.start) < SHIFT_GRACE_MS) {
      const prevWin = shiftWindowFor(new Date(win.start.getTime() - 1));
      const prev = st.shifts.find(s => s.id === prevWin.id);
      if (prev && prev.rows.length) return prev;
    }
    return bucket;
  }

  // ── MRZ CHECK DIGIT (ICAO 9303) ─────────────────────────────────
  // Validates that a scanned MRZ line wasn't misread by a shaky scanner.
  // Weights 7,3,1 repeat; '<' = 0, digits = value, letters A-Z = 10-35.
  function mrzCheckDigit(str) {
    const w = [7, 3, 1];
    let sum = 0;
    for (let i = 0; i < str.length; i++) {
      const c = str[i];
      let v;
      if (c === '<') v = 0;
      else if (/[0-9]/.test(c)) v = +c;
      else if (/[A-Z]/.test(c)) v = c.charCodeAt(0) - 55; // A=10 ... Z=35
      // Anything else is not an MRZ character at all. Scoring it 0 — as this
      // used to — makes it indistinguishable from the filler '<', so a misread
      // that turned a '0' into '/' or '>' or a space produced the SAME sum and
      // sailed through its own check digit. Fail outright instead: -1 can never
      // match a digit, so the field is reported as misread, which is the whole
      // point of having a check digit.
      else return -1;
      sum += v * w[i % 3];
    }
    return sum % 10;
  }
  // Checks passport-no, DOB and expiry check digits from TD3 line 2.
  // Returns { ok, bad: [field names that failed] } — a bad scan still gets
  // parsed and filled, but the officer is warned to double-check it.
  function mrzChecksValid(l2) {
    const bad = [];
    const passportField = l2.slice(0, 9), passportCheck = l2[9];
    const dobField = l2.slice(13, 19), dobCheck = l2[19];
    const expField = l2.slice(21, 27), expCheck = l2[27];
    if (passportCheck !== String(mrzCheckDigit(passportField))) bad.push('Passport No');
    if (dobCheck !== String(mrzCheckDigit(dobField))) bad.push('Date of Birth');
    if (expCheck !== String(mrzCheckDigit(expField))) bad.push('Expiry Date');
    return { ok: bad.length === 0, bad };
  }

  // ── MRZ PARSER ─────────────────────────────────────────────────
  // Find where line 2 really begins, instead of trusting that line 1 was
  // exactly 44 characters. A wedge scanner that drops or duplicates a single
  // character — most often inside the long run of '<' fillers — shifts every
  // field after it, and a fixed slice then reads a 9-character window off the
  // wrong offset. That is what produced passport numbers like "0010C9381" and
  // dates like "ND/82/NaN" and "5M/35/2101": nothing was corrupt, everything
  // was simply read one or two places out.
  //
  // TD3 line 2 has a rigid shape that almost nothing else matches:
  //   9 doc-number chars, check digit, 3-letter nationality, YYMMDD, check,
  //   sex, YYMMDD, check.
  // Anchoring on that shape and confirming it with the document's own check
  // digits makes the parse self-locating.
  function _locateLine2(s) {
    const re = /[A-Z0-9<]{9}\d[A-Z<]{3}\d{6}\d[MF<]\d{6}\d/g;
    let m, structural = -1;
    while ((m = re.exec(s)) !== null) {
      const cand = s.slice(m.index);
      if (cand.length >= 28 && mrzChecksValid(cand).ok) return m.index;
      if (structural === -1) structural = m.index;
      re.lastIndex = m.index + 1;   // allow overlapping candidates
    }
    return structural;              // shape matched but digits disagree
  }

  function parseMRZ(raw) {
    const noBreaks = raw.replace(/[\r\n]/g, '');
    let l1, l2;
    const lines = raw.replace(/\r/g, '').split('\n').map(s => s.trim()).filter(Boolean);
    if (lines.length >= 2 && lines[0].length >= 44 && lines[1].length >= 44) {
      l1 = lines[0]; l2 = lines[1];
    } else if (noBreaks.length >= 60) {
      // Deliberately below 88: a scanner that DROPPED a character sends 87,
      // and bailing here meant the repair below never got a chance to run.
      // Nothing is accepted on length alone — the check digits still decide.
      // Some MRZ scanners send both TD3 lines as one continuous 88-char
      // stream with no Enter/newline between them at all (only a trailing
      // one, or none). Every real TD3 line is exactly 44 characters, so
      // split at that fixed width instead of depending on a separator that
      // may never arrive — this was silently failing (returning null with
      // zero fields filled and no warning) on exactly this kind of scanner.
      l1 = noBreaks.slice(0, 44);
      l2 = noBreaks.slice(44, 88);
    } else {
      return null;
    }
    // If the fixed split doesn't satisfy the document's own check digits, the
    // stream has drifted. Re-anchor on line 2's structure and take line 1 as
    // whatever precedes it. Only accepted when the check digits then pass, so
    // this can repair a shifted read but can never invent one.
    if (!mrzChecksValid(l2).ok) {
      const at = _locateLine2(noBreaks);
      if (at > 0) {
        const cand2 = noBreaks.slice(at);
        // Whatever sits in front of line 2 is line 1 — plus, possibly, the
        // officer's own typing that ran into the scan. Line 1 is exactly 44
        // characters, so take the last 44 and drop any prefix.
        let cand1 = noBreaks.slice(0, at);
        // Only trim when it clearly isn't line 1 already. A DUPLICATED filler
        // makes line 1 forty-five characters — still a perfectly good line 1,
        // and blindly taking the last 44 chopped its leading 'P' off.
        if (!/^P/.test(cand1)) {
          // TD3 line 1 starts with 'P' + subtype (any letter, digit, or '<').
          // Searching for only 'P<' missed passports like PAIND/PASGP/PPAUS.
          const k = cand1.search(/P[A-Z0-9<]/);
          if (k >= 0) cand1 = cand1.slice(k);
        }
        if (mrzChecksValid(cand2).ok && /^P/.test(cand1) && cand1.length >= 10) {
          l1 = cand1; l2 = cand2;
        }
      }
    }
    if (l1.length < 10 || l2.length < 28 || !/^P/.test(l1)) return null;
    const namePart = l1.slice(5);
    const [sRaw = '', gRaw = ''] = namePart.split('<<');
    const surname = sRaw.replace(/</g, ' ').trim();
    const given = gRaw.replace(/</g, ' ').trim();
    const passportNo = l2.slice(0, 9).replace(/</g, '');
    const issuingCountry = l1.slice(2, 5).replace(/</g, '');
    const nationality   = l2.slice(10, 13).replace(/</g, '');
    // '<' is ICAO's "unspecified", and anything else here is a misread. Either
    // way there is no answer to give — passing the raw character through put a
    // literal '<' into the Gender box.
    const sex = l2[20] === 'M' ? 'Male' : l2[20] === 'F' ? 'Female' : '';

    // ── Date formatter: YYMMDD → DD/MM/YYYY ─────────────────────
    // An MRZ date is exactly six DIGITS, YYMMDD. Anything else means the line
    // is not aligned the way we assumed, and the old version happily pasted
    // the raw characters straight into the form — that is where the observed
    // "ND/82/NaN" and "5M/35/2101" in the Date of Birth / Date of Expiry boxes
    // came from, and a garbage expiry then propagated into "NaN/NaN/NaN" for
    // the derived issuing date. Refuse to emit anything that isn't a real
    // calendar date; a blank field the officer fills in is far better than a
    // wrong one they have to notice first.
    //
    // The century is not in the MRZ either — only two year digits are — so it
    // has to be inferred. Pick the candidate century that puts the date
    // NEAREST to today, rather than assuming an expiry is always in the
    // future: an already-expired passport is a normal thing to be handed at a
    // counter (and the officer needs to *see* that it expired). The old
    // "expiry year below the current one ⇒ next century" rule turned the
    // canonical 120415 into 15/04/2112, and the issue date derived from it
    // into 2102 — a wrong date that looks deliberate, which is worse than a
    // blank one. A birth date additionally can never be in the future, so it
    // takes the nearest candidate that has actually happened.
    const fmt = (s, birth) => {
      if (!/^\d{6}$/.test(s || '')) return '';
      const yy = +s.slice(0, 2), mm = +s.slice(2, 4), dd = +s.slice(4, 6);
      if (mm < 1 || mm > 12 || dd < 1 || dd > 31) return '';
      const nowYear = new Date().getFullYear();
      let cands = [1900 + yy, 2000 + yy, 2100 + yy];
      if (birth) {
        const notFuture = cands.filter(c => c <= nowYear);
        if (notFuture.length) cands = notFuture;
      }
      const yr = cands.reduce((best, c) =>
        Math.abs(c - nowYear) < Math.abs(best - nowYear) ? c : best);
      const probe = new Date(yr, mm - 1, dd);   // rejects 31 Feb and friends
      if (probe.getFullYear() !== yr || probe.getMonth() !== mm - 1 || probe.getDate() !== dd) return '';
      const z = n => String(n).padStart(2, '0');
      return `${z(dd)}/${z(mm)}/${yr}`;
    };
    const expiry = fmt(l2.slice(21, 27), false);

    // Optional data / personal number (TD3 line 2, chars 28-42) — most Indian
    // passports leave this blank ('<' filler), but some countries encode a
    // national ID here, so extract it whenever present.
    const personalNumber = l2.slice(28, 42).replace(/</g, '').trim();

    // ── Issue date: the MRZ does not encode it, so derive it from expiry.
    // issue = expiry − validity + 1 day  (a passport issued on the 1st and
    // valid 10 years expires on the last day of the 10th year, not the 1st).
    //
    // Computed for EVERY nationality, not just Indian passports as before: a
    // 10-year adult validity is the near-universal standard, and leaving the
    // field blank meant the officer retyped it for every foreign passenger.
    //
    // Order of operations matters. Adding the day FIRST and only then
    // subtracting the years is not cosmetic: going back 10 years from an
    // expiry of 29 Feb lands on a date that doesn't exist, which JS silently
    // rolls forward to 1 Mar, and the +1 day then pushed the answer to 2 Mar —
    // a day late. Adding the day first sidesteps the invalid intermediate
    // date entirely. Verified by forward-checking issue + N years − 1 day back
    // against the original expiry across leap and month-boundary cases.
    //
    // Minors are the one common validity exception (India: under-15s get 5
    // years, not 10). The cut-off used here is 15, NOT 18, on purpose — 15-to
    // -17-year-olds are entitled to a full 10-year passport, so treating them
    // as minors would corrupt a date that was already right. This remains an
    // ESTIMATE by construction (see MRZ_LABELS), fully editable, and is never
    // presented as if it were read off the document.
    const dobStr = fmt(l2.slice(13, 19), true);
    let issueDate = '';
    if (expiry) {
      try {
        const iz = n => String(n).padStart(2, '0');
        const [edd, emm, eyy] = expiry.split('/').map(Number);
        const backFrom = (years) => {
          const d = new Date(eyy, emm - 1, edd);
          d.setDate(d.getDate() + 1);        // day first — see note above
          d.setFullYear(d.getFullYear() - years);
          return d;
        };
        let issD = backFrom(10);
        if (dobStr) {
          const [bdd, bmm, byy] = dobStr.split('/').map(Number);
          const birth = new Date(byy, bmm - 1, bdd);
          let ageAtIssue = issD.getFullYear() - birth.getFullYear();
          const m = issD.getMonth() - birth.getMonth();
          if (m < 0 || (m === 0 && issD.getDate() < birth.getDate())) ageAtIssue--;
          if (ageAtIssue < 15) issD = backFrom(5);
        }
        issueDate = `${iz(issD.getDate())}/${iz(issD.getMonth() + 1)}/${issD.getFullYear()}`;
      } catch { issueDate = ''; }
    }

    const checks = mrzChecksValid(l2);

    // Every one of the three check digits failing means this is not a TD3
    // second line at the offset we read it from — a misaligned stream, a
    // different document format, or a partial scan. Previously the parse went
    // ahead regardless and pasted the resulting nonsense into the form behind
    // a toast that is easy to miss mid-shift. Refuse it outright instead and
    // say so, so the officer simply rescans.
    // Even then, the fields that carry NO check digit are still worth having.
    // Name, sex, nationality and country of issuance come from fixed positions,
    // and a misaligned one is obvious on sight — the officer is holding the
    // passport. Throwing them away too meant a shaky read filled nothing at
    // all and everything was retyped. So the protected fields (number, dates)
    // are refused and the rest is offered, loudly flagged.
    const _degraded = checks.bad.length === 3;

    // A single failed check digit condemns only its own field. Blank those
    // rather than filling a value the document itself says is misread.
    const trust = (val, field) => ((_degraded || checks.bad.includes(field)) ? '' : val);
    const safePassportNo = trust(passportNo, 'Passport No');
    const safeDob        = trust(dobStr, 'Date of Birth');
    const safeExpiry     = trust(expiry, 'Expiry Date');
    if (!safeExpiry) issueDate = '';   // derived from expiry — no expiry, no estimate

    return {
      surname, givenNames: given,
      fullName: `${given} ${surname}`.trim(),
      passportNo: safePassportNo, nationality, issuingCountry, sex,
      dob:       safeDob,
      expiry:    safeExpiry,
      issueDate, // ESTIMATED from expiry (10yr adult / 5yr minor validity)
      personalNumber, // often blank — only filled if the passport actually encodes one
      // Scanning an MRZ is *only* ever done for a passport, so the identity-
      // document-type field is a safe constant to set every time — unlike
      // classification/residency status (Indian Resident vs NRI vs Tourist),
      // which the passport's nationality alone can't determine (an Indian
      // citizen can still be an NRI for Baggage Rules purposes) and is
      // deliberately left for the officer to set manually.
      identityType: 'Passport',
      // "Country Code For Mobile Number" is a required mat-select whose
      // options read "India (+91)" — i.e. it is selected by COUNTRY, and the
      // passport already establishes one. Seeded from nationality and
      // soft-filled only: a passenger genuinely can carry a number from a
      // different country (an Indian national on a UAE SIM is the common
      // case), so this never overwrites a code already chosen, and the
      // officer changes it when the number they're given says otherwise.
      mobileCountry: COUNTRY_NAMES[nationality] || '',
      _checksOk: checks.ok, _checksBad: checks.bad, _degraded
    };
  }

  const MRZ_LABELS = {
    fullName: 'Full Name', surname: 'Surname', givenNames: 'Given Names',
    passportNo: 'Passport No', nationality: 'Nationality',
    issuingCountry: 'Issuing Country',
    dob: 'Date of Birth',
    issueDate: 'Issue Date (estimated from expiry)',
    expiry: 'Expiry Date',
    sex: 'Sex',
    personalNumber: 'Personal / National ID No (if encoded)',
    identityType: 'Identity Document Type (auto: "Passport")',
    mobileCountry: 'Mobile Country Code — from nationality (only fills if blank)'
  };

  // This deployment's port of entry: Chennai. Every declaration filed here is
  // for a passenger who landed here, so "Port of Arrival" is a constant rather
  // than something to read off a boarding pass — the pass's own destination is
  // the passenger's FINAL stop, which for anyone connecting onward is a
  // different airport entirely. One line to change if this is ever deployed at
  // another port.
  const ARRIVAL_PORT = 'MAA';

  // How long is this barcode, in total, according to itself? The mandatory
  // block per leg is a fixed 35 chars, each followed by a 2-char hex length
  // for that leg's own conditional section. Returns Infinity while the buffer
  // is still too short to know — the caller keeps collecting rather than
  // firing on a partial read.
  function bcbpTotalLength(u) {
    const m = /^M([1-9])/.exec(u);
    if (!m) return Infinity;
    let p = 23;                       // 'M' + leg count + name(20) + e-ticket indicator
    for (let i = 0; i < +m[1]; i++) {
      p += 35;                        // PNR(7) from(3) to(3) carrier(3) flight(5) date(3) cls(1) seat(4) seq(5) status(1)
      if (u.length < p + 2) return Infinity;
      const v = parseInt(u.substr(p, 2), 16);
      if (isNaN(v)) return Infinity;
      p += 2 + v;
    }
    return p;
  }

  // ── BOARDING PASS (IATA BCBP) PARSER ───────────────────────────
  // Handles multi-leg passes (M2, M3, …), not just single-leg M1. A passenger
  // connecting into India on one conjunction ticket carries ONE barcode
  // covering every leg; requiring "M1" made parseBP return null for them, so
  // nothing filled and no toast appeared — a silent miss on a very ordinary
  // arrival, and one the officer would only notice as an empty form.
  function parseBP(raw) {
    const u = raw.toUpperCase().replace(/[\r\n]/g, '');
    const head = /^M([1-9])/.exec(u);
    if (!head) return null;
    const legCount = +head[1];
    // BCBP encodes the name as SURNAME/GIVENNAMES in a fixed 20-char field.
    // Pasting that in verbatim made the site reject it outright — it prints
    // "Name should be in characters only" because of the slash. So strip what
    // the box won't take and keep the whole name: JALIL/SALEEM goes in as
    // JALIL SALEEM, surname first, exactly as the pass is printed (this field
    // is "Name on Boarding Pass", which the officer compares against the
    // document in front of them). The separator becomes a space rather than
    // nothing — a space is not one of the rejected characters, and the passport
    // name box already takes "DHINAKARAN HARIHARAN" through the same control,
    // so joining the parts into "JALILSALEEM" would mangle the name for no gain.
    const rawName = u.substring(2, 22).trim();
    const name = rawName.replace(/[^A-Z ]+/g, ' ').replace(/\s+/g, ' ').trim();

    // Julian day → DD/MM/YYYY. The barcode carries no year, so "this year" is
    // the only available assumption — but applied blindly it is wrong for a
    // week every January: a 31-Dec flight scanned on 1 Jan would be dated
    // twelve months into the future. A boarding pass presented at an arrivals
    // counter is always for a flight that has just landed, so a date that
    // comes out in the future belongs to last year.
    const julianToDate = (jul) => {
      if (isNaN(jul) || jul < 1 || jul > 366) return '';
      const now = new Date();
      let d = new Date(now.getFullYear(), 0);
      d.setDate(jul);
      if (d.getTime() - now.getTime() > 7 * 864e5) {
        d = new Date(now.getFullYear() - 1, 0);
        d.setDate(jul);
      }
      const z = n => String(n).padStart(2, '0');
      return `${z(d.getDate())}/${z(d.getMonth() + 1)}/${d.getFullYear()}`;
    };

    // Walk every leg. Leg 1 starts right after the e-ticket indicator; each
    // subsequent leg follows the previous leg's conditional section, whose
    // length that leg declared.
    const legs = [];
    let p = 23;
    for (let i = 0; i < legCount; i++) {
      // A leg's mandatory block is a fixed 35 characters (IATA Res 792). Past
      // the end of the string `substr` quietly returns short or empty pieces,
      // so a scanner that gave up mid-read still produced a complete-looking
      // result — 45 characters yielded a passenger, a route AND an arrival
      // date built out of whatever bytes happened to sit at those offsets.
      // Fabricating a date on a customs declaration is worse than filling
      // nothing, so a leg whose block isn't fully present is not parsed.
      if (p + 35 > u.length) break;
      const take = n => { const v = u.substr(p, n); p += n; return v; };
      const leg = {
        pnr: take(7).trim(), from: take(3).trim(), to: take(3).trim(),
        al: take(3).trim(), flt: take(5).replace(/^0+/, '').trim(),
        jul: parseInt(take(3)),
        compartment: take(1).trim(), seat: take(4).replace(/^0+/, '').trim(),
        sequence: take(5).replace(/^0+/, '').trim(), paxStatus: take(1).trim()
      };
      // Shape-check the fields that have a defined format. A misread barcode
      // that merely starts "M1" used to yield a flight number of "XXXXXXXX"
      // and a route of XXX-XXX, which then went onto the declaration. Airport
      // codes are three letters; the flight number is right-justified numeric
      // with at most one alpha suffix. Anything else means this is not a
      // boarding pass, whatever the header claimed.
      const shapeOk = /^[A-Z]{3}$/.test(leg.from) && /^[A-Z]{3}$/.test(leg.to) &&
                      /^[A-Z0-9]{2,3}$/.test(leg.al) && /^\d{1,4}[A-Z]?$/.test(leg.flt);
      if (!shapeOk) break;
      const varSize = parseInt(take(2), 16);
      leg.condStart = p;
      leg.condSize = isNaN(varSize) ? 0 : varSize;
      p += leg.condSize;
      legs.push(leg);
      if (p > u.length + 1) break;     // truncated read — keep what parsed
    }
    if (!legs.length) return null;

    // Which leg is the arrival being declared? The one that lands HERE. This
    // counter is at Chennai, so that is the leg into MAA; any leg after it is
    // domestic onward travel and irrelevant to this declaration, and any leg
    // before it is how the passenger got to the region. Falling back to the
    // first Indian landing, then to the last leg, keeps single-leg passes and
    // unrecognised airport codes behaving exactly as before.
    let ai = legs.findIndex(l => l.to === ARRIVAL_PORT);
    if (ai === -1) ai = legs.findIndex(l => (AIRPORTS[l.to] || [])[1] === 'IND');
    if (ai === -1) ai = legs.length - 1;
    const arrival = legs[ai];
    // Where the journey began, which is what "coming from" asks — not the
    // previous hop. On KUL→DEL→MAA the passenger is coming from Malaysia even
    // though the arrival leg departed Delhi.
    const originLeg = legs[0];

    const pnr  = arrival.pnr;
    const from = originLeg.from;
    // Port of Arrival is where this counter is, not whatever the barcode's
    // final destination happens to be — a passenger connecting on to Bengaluru
    // still clears customs here, and their pass says BLR. It is a dropdown, so
    // the constant is resolved to the site's own "CHENNAI" option the same way
    // every other airport is; only the search term is fixed.
    const to   = ARRIVAL_PORT;
    const al   = arrival.al;
    const flt  = arrival.flt;
    // The site's Flight Number box rejects punctuation, so the carrier code and
    // the number run together with no separator: 3L-141 goes in as 3L141.
    const flightNo = String((al || '') + (flt || '')).replace(/[^A-Z0-9]/gi, '');
    const flightDate = julianToDate(arrival.jul);
    const compartment = arrival.compartment;
    const seat = arrival.seat;
    const sequence = arrival.sequence;
    const paxStatus = arrival.paxStatus;
    const itinerary = legs.map(l => `${l.from}-${l.to}`).join(' / ');
    // The site's "Airport (from where coming)" list is filtered by a separate
    // "Country (from where coming)" control that must be committed FIRST —
    // until it is, the airport dropdown has no options at all to select from.
    // A BCBP never carries the country, only the origin IATA code, so derive
    // it (see AIRPORTS) rather than leaving the officer to pick it by hand.
    const fromCountry = (AIRPORTS[from] && AIRPORTS[from][1]) || '';
    // Same country, spelled out, for the plain-text "Address Abroad" box in
    // the passenger-identity block. The passport carries no address at all, so
    // without this that field starts empty every single time; the origin
    // country is the one piece of it the boarding pass can actually supply.
    const fromCountryName = COUNTRY_NAMES[fromCountry] || fromCountry;

    // ── CONDITIONAL SECTION ────────────────────────────────────────────
    // Everything above lives in the 60-char mandatory block. The E-Ticket
    // Number the form marks REQUIRED is not in there — it sits in the
    // conditional section, as airline numeric code (3) + document form/serial
    // number (10), which together are the 13-digit e-ticket number printed on
    // the passenger's itinerary. Leaving it unparsed is why that box stayed
    // empty and red on every single scan.
    //
    // This section is self-describing: each block is preceded by its own
    // length in hex. Trusting those declared lengths rather than counting
    // fields ourselves is what makes this safe across airlines — carriers
    // legitimately truncate the tail at different points, and an item we
    // assume is present but isn't would otherwise shift every subsequent read
    // (the same class of off-by-N that produced the garbage in the first
    // place). Anything unreadable simply yields '' and fills nothing.
    let ticketNo = '', bagTag = '', freqFlyer = '', freeBagAllowance = '';
    try {
      if (u[60] === '>') {
        let p = 62;                                   // past '>' and the version digit
        const take = n => { const v = u.substr(p, n); p += n; return v; };
        const uniqLen = parseInt(take(2), 16);        // p now 64
        if (!isNaN(uniqLen) && uniqLen > 0) {
          const uniqEnd = p + uniqLen;
          take(1); take(1); take(1);                  // pax description, check-in source, BP issuance source
          take(4);                                    // date of issue of boarding pass
          take(1);                                    // document type
          take(3);                                    // BP-issuing airline designator
          bagTag = take(13).replace(/</g, '').trim();
          p = uniqEnd;                                // declared length wins over our field count
          const repLen = parseInt(take(2), 16);
          if (!isNaN(repLen) && repLen > 0) {
            const airlineNum = take(3).trim();        // e.g. 098 Air India, 603 SriLankan
            const docSerial  = take(10).trim();
            const digits = (airlineNum + docSerial).replace(/\D/g, '');
            if (digits.length >= 13) ticketNo = digits.slice(0, 13);
            take(1); take(1);                         // selectee, intl doc verification
            take(3); take(3);                         // marketing carrier, FF airline
            freqFlyer = take(16).replace(/</g, '').trim();
            take(1);                                  // ID/AD indicator
            freeBagAllowance = take(3).trim();
          }
        }
      }
    } catch { }

    return { passengerName: name, pnr, from, to, fromCountry, fromCountryName,
             flightNo, flightDate, compartment, seat, sequence, paxStatus,
             ticketNo, bagTag, freqFlyer, freeBagAllowance,
             legCount, itinerary,
             // "Countries visited Last Six Days" is a required box that the
             // officer otherwise types by hand on every passenger. The origin
             // country is the one country the boarding pass can actually
             // prove they were in, so it seeds the field — soft-filled, so a
             // multi-country itinerary the officer has already typed is never
             // overwritten.
             countriesVisited: fromCountryName };
  }

  const BP_LABELS = {
    passengerName: 'Passenger Name', flightNo: 'Flight No',
    from: 'From (Origin)', to: 'To (Destination)',
    fromCountry: 'Country (from where coming) — derived from origin airport',
    fromCountryName: 'Address Abroad — origin country name (only fills if blank)',
    flightDate: 'Flight Date', pnr: 'PNR',
    compartment: 'Class / Compartment', seat: 'Seat No (auto-mapped: seat_number)',
    sequence: 'Check-in Sequence No', paxStatus: 'Passenger Status',
    ticketNo: 'E-Ticket Number', bagTag: 'Baggage Tag No',
    freqFlyer: 'Frequent Flyer No', freeBagAllowance: 'Free Baggage Allowance',
    countriesVisited: 'Countries visited Last Six Days — origin country (only fills if blank)'
  };

  // ── CODE → NAME LOOKUPS FOR THE SITE'S DROPDOWNS ────────────────
  // The scanners emit codes (ISO-3166 alpha-3 for nationality/issuing
  // country, IATA 3-letter for airports) but the real site's Nationality /
  // Country of Issuance / Country-from-where-coming / Airport / Port of
  // Arrival controls are mat-autocomplete comboboxes whose option lists are
  // full names ("INDIA", "MALAYSIA", "Kuala Lumpur"). Typing a raw code into
  // them filters to zero options, so nothing can be selected — which is why
  // these five fields silently stayed empty. Each map below is only used to
  // produce *candidate* search strings; the actual value committed is always
  // whatever option the site itself offers, never our string.
  const COUNTRY_NAMES = {
    AFG:'AFGHANISTAN', ALB:'ALBANIA', DZA:'ALGERIA', AGO:'ANGOLA', ARG:'ARGENTINA',
    ARM:'ARMENIA', AUS:'AUSTRALIA', AUT:'AUSTRIA', AZE:'AZERBAIJAN', BHR:'BAHRAIN',
    BGD:'BANGLADESH', BLR:'BELARUS', BEL:'BELGIUM', BTN:'BHUTAN', BOL:'BOLIVIA',
    BRA:'BRAZIL', BRN:'BRUNEI', BGR:'BULGARIA', KHM:'CAMBODIA', CMR:'CAMEROON',
    CAN:'CANADA', CHL:'CHILE', CHN:'CHINA', COL:'COLOMBIA', COD:'CONGO',
    CRI:'COSTA RICA', HRV:'CROATIA', CUB:'CUBA', CYP:'CYPRUS', CZE:'CZECH REPUBLIC',
    DNK:'DENMARK', DJI:'DJIBOUTI', ECU:'ECUADOR', EGY:'EGYPT', EST:'ESTONIA',
    ETH:'ETHIOPIA', FJI:'FIJI', FIN:'FINLAND', FRA:'FRANCE', GEO:'GEORGIA',
    DEU:'GERMANY', GHA:'GHANA', GRC:'GREECE', GTM:'GUATEMALA', GUY:'GUYANA',
    HKG:'HONG KONG', HUN:'HUNGARY', ISL:'ICELAND', IND:'INDIA', IDN:'INDONESIA',
    IRN:'IRAN', IRQ:'IRAQ', IRL:'IRELAND', ISR:'ISRAEL', ITA:'ITALY',
    JAM:'JAMAICA', JPN:'JAPAN', JOR:'JORDAN', KAZ:'KAZAKHSTAN', KEN:'KENYA',
    KWT:'KUWAIT', KGZ:'KYRGYZSTAN', LAO:'LAOS', LVA:'LATVIA', LBN:'LEBANON',
    LBY:'LIBYA', LTU:'LITHUANIA', LUX:'LUXEMBOURG', MDG:'MADAGASCAR', MWI:'MALAWI',
    MYS:'MALAYSIA', MDV:'MALDIVES', MLI:'MALI', MLT:'MALTA', MUS:'MAURITIUS',
    MEX:'MEXICO', MDA:'MOLDOVA', MNG:'MONGOLIA', MAR:'MOROCCO', MOZ:'MOZAMBIQUE',
    MMR:'MYANMAR', NAM:'NAMIBIA', NPL:'NEPAL', NLD:'NETHERLANDS', NZL:'NEW ZEALAND',
    NGA:'NIGERIA', PRK:'NORTH KOREA', NOR:'NORWAY', OMN:'OMAN', PAK:'PAKISTAN',
    PSE:'PALESTINE', PAN:'PANAMA', PNG:'PAPUA NEW GUINEA', PRY:'PARAGUAY', PER:'PERU',
    PHL:'PHILIPPINES', POL:'POLAND', PRT:'PORTUGAL', QAT:'QATAR', ROU:'ROMANIA',
    RUS:'RUSSIA', RWA:'RWANDA', SAU:'SAUDI ARABIA', SEN:'SENEGAL', SRB:'SERBIA',
    SYC:'SEYCHELLES', SGP:'SINGAPORE', SVK:'SLOVAKIA', SVN:'SLOVENIA', SOM:'SOMALIA',
    ZAF:'SOUTH AFRICA', KOR:'SOUTH KOREA', SSD:'SOUTH SUDAN', ESP:'SPAIN', LKA:'SRI LANKA',
    SDN:'SUDAN', SWE:'SWEDEN', CHE:'SWITZERLAND', SYR:'SYRIA', TWN:'TAIWAN',
    TJK:'TAJIKISTAN', TZA:'TANZANIA', THA:'THAILAND', TUN:'TUNISIA', TUR:'TURKEY',
    TKM:'TURKMENISTAN', UGA:'UGANDA', UKR:'UKRAINE', ARE:'UNITED ARAB EMIRATES',
    GBR:'UNITED KINGDOM', USA:'UNITED STATES OF AMERICA', URY:'URUGUAY',
    UZB:'UZBEKISTAN', VEN:'VENEZUELA', VNM:'VIETNAM', YEM:'YEMEN', ZMB:'ZAMBIA',
    ZWE:'ZIMBABWE'
  };
  // Extra spellings the site may use instead of the primary name above.
  const COUNTRY_ALIASES = {
    USA: ['UNITED STATES', 'U.S.A.', 'US'],
    GBR: ['UNITED KINGDOM', 'UK', 'GREAT BRITAIN', 'ENGLAND'],
    ARE: ['UAE', 'U.A.E.'],
    KOR: ['KOREA, REPUBLIC OF', 'REPUBLIC OF KOREA'],
    PRK: ['KOREA, DEMOCRATIC PEOPLE’S REPUBLIC OF'],
    VNM: ['VIET NAM'], LAO: ['LAO PDR'], SYR: ['SYRIAN ARAB REPUBLIC'],
    IRN: ['IRAN, ISLAMIC REPUBLIC OF'], RUS: ['RUSSIAN FEDERATION'],
    CZE: ['CZECHIA'], TUR: ['TURKIYE', 'TÜRKIYE'], MMR: ['BURMA'],
    HKG: ['HONG KONG SAR', 'HONGKONG'], NLD: ['HOLLAND']
  };
  // IATA airport code → [city/airport name, ISO-3 country]. Curated to the
  // routes that actually land at Indian international terminals (Gulf, SE
  // Asia, Europe, N. America, subcontinent) plus every Indian international
  // airport, since "Port of Arrival" is always domestic.
  const AIRPORTS = {
    // India (Port of Arrival)
    DEL:['DELHI','IND'], BOM:['MUMBAI','IND'], MAA:['CHENNAI','IND'], BLR:['BENGALURU','IND'],
    HYD:['HYDERABAD','IND'], CCU:['KOLKATA','IND'], COK:['KOCHI','IND'], TRV:['THIRUVANANTHAPURAM','IND'],
    AMD:['AHMEDABAD','IND'], GOI:['GOA','IND'], GOX:['GOA','IND'], PNQ:['PUNE','IND'],
    CCJ:['KOZHIKODE','IND'], TRZ:['TIRUCHIRAPPALLI','IND'], IXE:['MANGALURU','IND'],
    JAI:['JAIPUR','IND'], LKO:['LUCKNOW','IND'], VNS:['VARANASI','IND'], IXC:['CHANDIGARH','IND'],
    ATQ:['AMRITSAR','IND'], GAU:['GUWAHATI','IND'], BBI:['BHUBANESWAR','IND'], NAG:['NAGPUR','IND'],
    IXM:['MADURAI','IND'], VTZ:['VISAKHAPATNAM','IND'], IXB:['BAGDOGRA','IND'], SXR:['SRINAGAR','IND'],
    IXJ:['JAMMU','IND'], PAT:['PATNA','IND'], IDR:['INDORE','IND'], CJB:['COIMBATORE','IND'],
    // Gulf — by far the highest-volume origins at Indian terminals, so this
    // block is deliberately exhaustive down to the secondary airports.
    DXB:['DUBAI','ARE'], AUH:['ABU DHABI','ARE'], SHJ:['SHARJAH','ARE'], RKT:['RAS AL KHAIMAH','ARE'],
    FJR:['FUJAIRAH','ARE'], AAN:['AL AIN','ARE'], DWC:['DUBAI','ARE'],
    DOH:['DOHA','QAT'], KWI:['KUWAIT CITY','KWT'], BAH:['BAHRAIN','BHR'],
    MCT:['MUSCAT','OMN'], SLL:['SALALAH','OMN'], DQM:['DUQM','OMN'], OHS:['SOHAR','OMN'],
    KHS:['KHASAB','OMN'], SUH:['SUR','OMN'], TTH:['THUMRAIT','OMN'], MSH:['MASIRAH','OMN'],
    RUH:['RIYADH','SAU'], JED:['JEDDAH','SAU'], DMM:['DAMMAM','SAU'], MED:['MADINAH','SAU'],
    AHB:['ABHA','SAU'], ELQ:['QASSIM','SAU'], HOF:['AL AHSA','SAU'], YNB:['YANBU','SAU'],
    TUU:['TABUK','SAU'], GIZ:['JIZAN','SAU'], TIF:['TAIF','SAU'], AJF:['AL JOUF','SAU'],
    RAE:['ARAR','SAU'], URY:['GURIAT','SAU'], DWD:['DAWADMI','SAU'], RAH:['RAFHA','SAU'],
    TUI:['TURAIF','SAU'], ULH:['AL ULA','SAU'], AQI:['AL QAISUMAH','SAU'], EAM:['NAJRAN','SAU'],
    SHW:['SHARURAH','SAU'], BHH:['BISHA','SAU'], WAE:['WADI AL DAWASIR','SAU'], EJH:['WEDJH','SAU'],
    // SE / E Asia — second-highest volume block, likewise expanded.
    KUL:['KUALA LUMPUR','MYS'], PEN:['PENANG','MYS'], JHB:['JOHOR BAHRU','MYS'],
    BKI:['KOTA KINABALU','MYS'], KCH:['KUCHING','MYS'], SZB:['SUBANG','MYS'], LGK:['LANGKAWI','MYS'],
    KBR:['KOTA BHARU','MYS'], TGG:['KUALA TERENGGANU','MYS'], IPH:['IPOH','MYS'], MKZ:['MELAKA','MYS'],
    AOR:['ALOR SETAR','MYS'], SBW:['SIBU','MYS'], MYY:['MIRI','MYS'], TWU:['TAWAU','MYS'],
    SDK:['SANDAKAN','MYS'], LBU:['LABUAN','MYS'], KUA:['KUANTAN','MYS'], BTU:['BINTULU','MYS'],
    SIN:['SINGAPORE','SGP'], XSP:['SINGAPORE','SGP'],
    BKK:['BANGKOK','THA'], DMK:['BANGKOK','THA'], HKT:['PHUKET','THA'], CNX:['CHIANG MAI','THA'],
    USM:['KOH SAMUI','THA'], KBV:['KRABI','THA'], UTP:['U-TAPAO','THA'], HDY:['HAT YAI','THA'],
    CEI:['CHIANG RAI','THA'], URT:['SURAT THANI','THA'], UBP:['UBON RATCHATHANI','THA'],
    KKC:['KHON KAEN','THA'],
    CGK:['JAKARTA','IDN'], DPS:['DENPASAR','IDN'], SUB:['SURABAYA','IDN'], KNO:['MEDAN','IDN'],
    JOG:['YOGYAKARTA','IDN'], BTH:['BATAM','IDN'], UPG:['MAKASSAR','IDN'], BPN:['BALIKPAPAN','IDN'],
    PKU:['PEKANBARU','IDN'], PLM:['PALEMBANG','IDN'], SRG:['SEMARANG','IDN'], PDG:['PADANG','IDN'],
    BDO:['BANDUNG','IDN'], LOP:['LOMBOK','IDN'], MDC:['MANADO','IDN'], HLP:['JAKARTA','IDN'],
    MNL:['MANILA','PHL'], CEB:['CEBU','PHL'], CRK:['CLARK','PHL'], DVO:['DAVAO','PHL'],
    ILO:['ILOILO','PHL'], KLO:['KALIBO','PHL'], PPS:['PUERTO PRINCESA','PHL'], BCD:['BACOLOD','PHL'],
    CGY:['CAGAYAN DE ORO','PHL'], ZAM:['ZAMBOANGA','PHL'],
    HKG:['HONG KONG','HKG'], MFM:['MACAU','HKG'], PVG:['SHANGHAI','CHN'], PEK:['BEIJING','CHN'],
    PKX:['BEIJING','CHN'], CAN:['GUANGZHOU','CHN'], SZX:['SHENZHEN','CHN'], KMG:['KUNMING','CHN'],
    ICN:['SEOUL','KOR'], NRT:['TOKYO','JPN'], HND:['TOKYO','JPN'], KIX:['OSAKA','JPN'],
    TPE:['TAIPEI','TWN'], SGN:['HO CHI MINH CITY','VNM'], HAN:['HANOI','VNM'], DAD:['DA NANG','VNM'],
    RGN:['YANGON','MMR'], MDL:['MANDALAY','MMR'],
    PNH:['PHNOM PENH','KHM'], REP:['SIEM REAP','KHM'], VTE:['VIENTIANE','LAO'],
    BWN:['BANDAR SERI BEGAWAN','BRN'],
    // Subcontinent / neighbours
    CMB:['COLOMBO','LKA'], HRI:['MATTALA','LKA'], JAF:['JAFFNA','LKA'], TRR:['TRINCOMALEE','LKA'],
    RML:['RATMALANA','LKA'], MLE:['MALE','MDV'], GAN:['GAN','MDV'],
    KTM:['KATHMANDU','NPL'], DAC:['DHAKA','BGD'], CGP:['CHITTAGONG','BGD'], ZYL:['SYLHET','BGD'],
    CXB:['COXS BAZAR','BGD'], JSR:['JESSORE','BGD'], RJH:['RAJSHAHI','BGD'], BZL:['BARISAL','BGD'],
    SPD:['SAIDPUR','BGD'],
    KHI:['KARACHI','PAK'], LHE:['LAHORE','PAK'], ISB:['ISLAMABAD','PAK'],
    KBL:['KABUL','AFG'], PBH:['PARO','BTN'],
    // Europe
    LHR:['LONDON','GBR'], LGW:['LONDON','GBR'], STN:['LONDON','GBR'], MAN:['MANCHESTER','GBR'],
    BHX:['BIRMINGHAM','GBR'], EDI:['EDINBURGH','GBR'], CDG:['PARIS','FRA'], ORY:['PARIS','FRA'],
    FRA:['FRANKFURT','DEU'], MUC:['MUNICH','DEU'], AMS:['AMSTERDAM','NLD'], BRU:['BRUSSELS','BEL'],
    ZRH:['ZURICH','CHE'], GVA:['GENEVA','CHE'], VIE:['VIENNA','AUT'], FCO:['ROME','ITA'],
    MXP:['MILAN','ITA'], MAD:['MADRID','ESP'], BCN:['BARCELONA','ESP'], LIS:['LISBON','PRT'],
    CPH:['COPENHAGEN','DNK'], ARN:['STOCKHOLM','SWE'], OSL:['OSLO','NOR'], HEL:['HELSINKI','FIN'],
    DUB:['DUBLIN','IRL'], WAW:['WARSAW','POL'], PRG:['PRAGUE','CZE'], BUD:['BUDAPEST','HUN'],
    IST:['ISTANBUL','TUR'], SAW:['ISTANBUL','TUR'], ATH:['ATHENS','GRC'], SVO:['MOSCOW','RUS'],
    DME:['MOSCOW','RUS'], KBP:['KYIV','UKR'], TAS:['TASHKENT','UZB'], ALA:['ALMATY','KAZ'],
    GYD:['BAKU','AZE'], TBS:['TBILISI','GEO'], EVN:['YEREVAN','ARM'],
    // Americas
    JFK:['NEW YORK','USA'], EWR:['NEWARK','USA'], ORD:['CHICAGO','USA'], LAX:['LOS ANGELES','USA'],
    SFO:['SAN FRANCISCO','USA'], IAD:['WASHINGTON','USA'], ATL:['ATLANTA','USA'], DFW:['DALLAS','USA'],
    IAH:['HOUSTON','USA'], BOS:['BOSTON','USA'], SEA:['SEATTLE','USA'], MIA:['MIAMI','USA'],
    YYZ:['TORONTO','CAN'], YVR:['VANCOUVER','CAN'], YUL:['MONTREAL','CAN'], YYC:['CALGARY','CAN'],
    MEX:['MEXICO CITY','MEX'], GRU:['SAO PAULO','BRA'], EZE:['BUENOS AIRES','ARG'],
    // Africa / Oceania
    CAI:['CAIRO','EGY'], JNB:['JOHANNESBURG','ZAF'], CPT:['CAPE TOWN','ZAF'], NBO:['NAIROBI','KEN'],
    ADD:['ADDIS ABABA','ETH'], DAR:['DAR ES SALAAM','TZA'], EBB:['ENTEBBE','UGA'], LOS:['LAGOS','NGA'],
    ACC:['ACCRA','GHA'], MRU:['MAURITIUS','MUS'], SEZ:['SEYCHELLES','SYC'], TNR:['ANTANANARIVO','MDG'],
    LUN:['LUSAKA','ZMB'], HRE:['HARARE','ZWE'], CMN:['CASABLANCA','MAR'], TUN:['TUNIS','TUN'],
    SYD:['SYDNEY','AUS'], MEL:['MELBOURNE','AUS'], BNE:['BRISBANE','AUS'], PER:['PERTH','AUS'],
    AKL:['AUCKLAND','NZL'], NAN:['NADI','FJI'], TLV:['TEL AVIV','ISR'], AMM:['AMMAN','JOR'],
    BEY:['BEIRUT','LBN'], BGW:['BAGHDAD','IRQ'], EBL:['ERBIL','IRQ'], THR:['TEHRAN','IRN'],
    IKA:['TEHRAN','IRN'], SAH:['SANAA','YEM']
  };

  // Search strings to try, in order, when driving a mat-autocomplete for a
  // given target key. Always ends with the raw scanned code so a site that
  // genuinely lists codes still resolves.
  // Many airports are listed by their official name, which can share no word
  // with the city: Bangkok is "Suvarnabhumi", Singapore is "Changi", Delhi is
  // "Indira Gandhi", Kochi is "Cochin". Searching the city name finds nothing in
  // such a list, and neither does the IATA code unless the site happens to show
  // it. Without these the control is left blank and the officer is warned —
  // safe, but it means hand-typing the commonest origins at this counter.
  // Weighted to what actually lands at Chennai: the Gulf, SE Asia, then the
  // Indian ports and the long-haul routes.
  const AIRPORT_ALIASES = {
    // Indian ports
    DEL:['INDIRA GANDHI'], BOM:['CHHATRAPATI SHIVAJI','CHATRAPATI SHIVAJI'],
    BLR:['KEMPEGOWDA'], HYD:['RAJIV GANDHI','SHAMSHABAD'],
    CCU:['NETAJI SUBHAS CHANDRA BOSE','NETAJI SUBHASH','DUM DUM'],
    COK:['COCHIN','NEDUMBASSERY'], TRV:['TRIVANDRUM'],
    AMD:['SARDAR VALLABHBHAI PATEL'], GOI:['DABOLIM'], GOX:['MANOHAR','MOPA'],
    PNQ:['LOHEGAON'], CCJ:['CALICUT','KARIPUR'], TRZ:['TIRUCHY','TRICHY'],
    IXE:['MANGALORE','BAJPE'], VNS:['LAL BAHADUR SHASTRI'],
    IXC:['SHAHEED BHAGAT SINGH','MOHALI'], ATQ:['SRI GURU RAM DASS','RAJA SANSI'],
    GAU:['LOKPRIYA GOPINATH BORDOLOI'], BBI:['BIJU PATNAIK'],
    NAG:['DR BABASAHEB AMBEDKAR','SONEGAON'], VTZ:['VISAKHAPATNAM','VIZAG'],
    PAT:['JAY PRAKASH NARAYAN','LOK NAYAK'], IDR:['DEVI AHILYABAI HOLKAR'],
    // Gulf
    DXB:['DUBAI INTERNATIONAL'], AUH:['ZAYED INTERNATIONAL','ABU DHABI INTERNATIONAL'],
    SHJ:['SHARJAH INTERNATIONAL'], DOH:['HAMAD'], KWI:['KUWAIT INTERNATIONAL'],
    BAH:['BAHRAIN INTERNATIONAL'], MCT:['MUSCAT INTERNATIONAL'], SLL:['SALALAH'],
    RUH:['KING KHALID'], JED:['KING ABDULAZIZ'], DMM:['KING FAHD'],
    // South-East / East Asia
    SIN:['CHANGI'], KUL:['KLIA','KUALA LUMPUR INTERNATIONAL'],
    BKK:['SUVARNABHUMI'], DMK:['DON MUEANG','DON MUANG'],
    CGK:['SOEKARNO HATTA','SOEKARNO-HATTA'], HKG:['CHEK LAP KOK','HONG KONG INTERNATIONAL'],
    // Long haul
    LHR:['HEATHROW'], LGW:['GATWICK'], JFK:['JOHN F KENNEDY','KENNEDY'],
    EWR:['NEWARK LIBERTY','NEWARK'], ORD:["O HARE",'OHARE'], SFO:['SAN FRANCISCO INTERNATIONAL'],
    CDG:['CHARLES DE GAULLE','ROISSY'], FRA:['FRANKFURT AM MAIN'],
    MEL:['TULLAMARINE'], SYD:['KINGSFORD SMITH'], YYZ:['PEARSON'], YVR:['VANCOUVER INTERNATIONAL'],
    CMB:['BANDARANAIKE'], KTM:['TRIBHUVAN'], DAC:['HAZRAT SHAHJALAL'], MLE:['VELANA','HULHULE']
  };

  function autocompleteCandidates(key, raw) {
    const code = String(raw || '').trim().toUpperCase();
    if (!code) return [];
    const out = [];
    const pushCountry = (iso3) => {
      if (COUNTRY_NAMES[iso3]) out.push(COUNTRY_NAMES[iso3]);
      (COUNTRY_ALIASES[iso3] || []).forEach(a => out.push(a));
    };
    if (key === 'nationality' || key === 'issuingCountry' || key === 'fromCountry') {
      pushCountry(code);
    } else if (key === 'from' || key === 'to') {
      const ap = AIRPORTS[code];
      if (ap) out.push(ap[0]);
      (AIRPORT_ALIASES[code] || []).forEach(a => out.push(a));
    }
    out.push(code);
    return [...new Set(out.filter(Boolean))];
  }

  // ── AUTO-MAP: known real-site field selectors ───────────────────
  // Candidate selectors per target key, tried in order — first one that
  // exists on the current page wins. The real "Atithi BO" site's Angular
  // reactive form exposes every field via `formcontrolname`, which is by far
  // the most stable handle (unlike auto-generated mat-* ids). The `#f_...`
  // entries are this repo's own test_site.html ids, kept as a second
  // candidate purely so "🔎 Auto-map" is demonstrable/testable against the
  // mock without needing the live site. Keys with no known real-site field
  // (surname/givenNames/personalNumber, and the BCBP compartment/sequence/
  // paxStatus block — the real site has no field for these) are intentionally
  // omitted, left for manual mapping. `seat` DOES have a known real field
  // (seat_number) and is auto-mapped below.
  // NOTE on pessenger_name: the page carries that SAME formcontrolname twice —
  // "Name on Passport" in the Passenger Identity accordion (#collapseTwo) and
  // "Name on Boarding Pass" in Travel Details (#collapseThree). They are two
  // independent controls that the officer is expected to be able to compare
  // (the site even prints "Note: Name on Boarding Pass should be same as on
  // Identity Type"). A bare [formcontrolname="pessenger_name"] resolves to
  // whichever comes first in the DOM, so BOTH scans were writing into the
  // passport box and the boarding-pass box was never filled at all. Scope each
  // to its own accordion, keeping the bare selector as a fallback for any page
  // variant that doesn't use these ids.
  const MRZ_AUTO_SELECTORS = {
    // "Name on Passport" and "Name on Boarding Pass" share one formcontrolname,
    // so the accordion scope disambiguates them. But that scope is only as good
    // as the id, and a page whose accordion is numbered differently left the
    // name unfilled. The second candidate keeps the old bare reach while still
    // refusing to write into the boarding-pass box: "any pessenger_name that is
    // NOT inside the travel section". Bare last, for a page with only one.
    fullName:       ['#collapseTwo [formcontrolname="pessenger_name"]',
                     '[formcontrolname="pessenger_name"]:not(#collapseThree *)',
                     '[formcontrolname="pessenger_name"]', '#f_name'],
    passportNo:     ['[formcontrolname="govt_identity_id"]', '#f_ppno'],
    nationality:    ['[formcontrolname="nationality"]', '#f_nat'],
    issuingCountry: ['[formcontrolname="country_of_passport_issue"]', '#f_ppcountry'],
    dob:            ['[formcontrolname="date_of_birth"]', '#f_dob'],
    issueDate:      ['[formcontrolname="passportIssuingDate"]', '#f_issue'],
    expiry:         ['[formcontrolname="date_Of_passport_expiry"]', '#f_expiry'],
    sex:            ['[formcontrolname="gender"]', '#f_gender'],
    identityType:   ['[formcontrolname="govt_identity_type"]'],
    mobileCountry:  ['[formcontrolname="mobileCode"]']
  };
  const BP_AUTO_SELECTORS = {
    passengerName: ['#collapseThree [formcontrolname="pessenger_name"]',
                    '[formcontrolname="pessenger_name"]:not(#collapseTwo *)',
                    '[formcontrolname="pessenger_name"]', '#f_name2', '#f_name'],
    pnr:           ['[formcontrolname="pnr_number"]', '#f_pnr'],
    fromCountry:   ['[formcontrolname="last_port_embarkation_country"]'],
    fromCountryName: ['[formcontrolname="addressAbroad"]'],
    from:          ['[formcontrolname="last_port_embarkation_city"]', '#f_airportfrom'],
    to:            ['[formcontrolname="airpot_location"]', '#f_airportto'],
    flightNo:      ['[formcontrolname="flight_number"]', '#f_flight'],
    flightDate:    ['[formcontrolname="date_of_arrival"]', '#f_arrivaldate'],
    seat:          ['[formcontrolname="seat_number"]'],
    ticketNo:      ['[formcontrolname="ticketNo"]'],
    countriesVisited: ['[formcontrolname="countriesVisitedLastSixDays"]']
  };

  // Several real formcontrolnames (e.g. "pessenger_name") are reused across
  // more than one tab/section of this multi-tab form — a plain
  // document.querySelector(sel) always returns the FIRST DOM match
  // regardless of which tab is currently visible, which is exactly what was
  // causing fills/reads to sometimes hit the wrong tab's identically-named
  // field. Every consumer of a stored selector (detect/fill/read) should
  // prefer whichever match is actually visible right now — Angular material
  // tabs/accordions keep inactive panels mounted but hidden, so this alone
  // resolves the ambiguity without needing a more specific stored selector.
  function queryVisible(sel) {
    const all = document.querySelectorAll(sel);
    for (const el of all) { if (el.offsetParent !== null) return el; }
    return all[0] || null;
  }

  function autoDetectSelector(candidates) {
    for (const sel of candidates) {
      try { if (queryVisible(sel)) return sel; } catch { /* invalid selector, skip */ }
    }
    return null;
  }

  // ── AUTO-MAP: Save/Submit button ─────────────────────────────────
  // Unlike form fields, a button has no formcontrolname to key off — so this
  // scores visible button/link text instead. Only claims a match when
  // there's a single unambiguous winner; a tie or no match at all is left
  // for the officer to map by hand via "Map Save Button" rather than risk
  // hooking the wrong button (which would silently stop rows being captured
  // at all, or capture on the wrong click).
  function autoDetectSaveButton() {
    const candidates = [...document.querySelectorAll('button, input[type="submit"], a[role="button"]')]
      .filter(el => el.offsetParent !== null);
    const scored = candidates.map(el => {
      const text = (el.textContent || el.value || '').trim();
      let score = 0;
      if (/^save$/i.test(text)) score = 100;
      else if (/^(save|submit|confirm|proceed)\b/i.test(text)) score = 70;
      else if (/\b(save|submit)\b/i.test(text)) score = 40;
      if (el.type === 'submit') score += 10;
      return { el, score };
    }).filter(c => c.score > 0).sort((a, b) => b.score - a.score);
    if (!scored.length || (scored.length > 1 && scored[0].score === scored[1].score)) return null;
    return getSelector(scored[0].el).sel;
  }

  // ── PAGE DETECTION ────────────────────────────────────────────────
  // The real site is a multi-tab Angular form (Passenger Identity / Contact
  // / Travel Details / Item Declaration / Gold-Silver / Document Upload /
  // Adjudication) — not every one of those tabs has passport/boarding-pass/
  // save-button fields, and this script also runs on `<all_urls>` (or
  // whatever page the bookmarklet gets clicked on), which could be a
  // completely unrelated site. Auto-map, draft-autosave and the "needs
  // manual mapping" warning should all go quiet unless the page actually
  // looks like part of this declaration form — checked by known, distinctive
  // real-site formcontrolnames rather than a URL/hostname (the Citrix tunnel
  // URL isn't a stable pattern to match against).
  const ATITHI_PAGE_SIGNATURE = [
    '[formcontrolname="pessenger_name"]', '[formcontrolname="govt_identity_id"]',
    '[formcontrolname="govt_identity_type"]', '[formcontrolname="pnr_number"]',
    '[formcontrolname="flight_number"]', '[formcontrolname="date_of_arrival"]',
    '[formarrayname="baggageItemDeclaration"]', '[formarrayname="baggageGoldDeclaration"]'
  ];
  function isAtithiPage() {
    return ATITHI_PAGE_SIGNATURE.some(sel => {
      try { return !!document.querySelector(sel); } catch { return false; }
    });
  }

  // Fills in ONLY currently-empty mrz/bp targets — never overwrites a mapping
  // the officer already has (manual or previously auto-detected), so this is
  // always safe to re-run. Anything it can't find on the page is reported so
  // the officer knows exactly which field(s) still need a manual click-map.
  // Bails out entirely (no side effects, no toast) if this doesn't even look
  // like an Atithi declaration page/tab right now.
  function runAutoMap(opts = {}) {
    if (!isAtithiPage()) return;
    const { silent = false, final = true } = opts;
    let mapped = 0;
    const unresolved = [];
    Object.entries(MRZ_AUTO_SELECTORS).forEach(([key, candidates]) => {
      if (st.mrzTargets[key]) return;
      const sel = autoDetectSelector(candidates);
      if (sel) { st.mrzTargets[key] = sel; st.mrzTargetsAuto[key] = true; mapped++; }
      else unresolved.push(MRZ_LABELS[key]);
    });
    Object.entries(BP_AUTO_SELECTORS).forEach(([key, candidates]) => {
      if (st.bpTargets[key]) return;
      const sel = autoDetectSelector(candidates);
      if (sel) { st.bpTargets[key] = sel; st.bpTargetsAuto[key] = true; mapped++; }
      else unresolved.push(BP_LABELS[key]);
    });
    if (!st.saveBtn) {
      const sel = autoDetectSaveButton();
      if (sel) { st.saveBtn = { selector: sel, auto: true }; attachHook(); mapped++; }
      else unresolved.push('Save/Submit button');
    }
    // Reuse selectors we already know from MRZ/BP mapping for the one Excel
    // column that's genuinely the same underlying site field — "Flight No"
    // is exactly the Boarding Pass's flightNo target, so there's no reason
    // to make the officer map it a second time by hand. (Most of the other
    // COPS columns aren't reusable like this: duty/AIDC/SWS columns already
    // don't need mapping at all — see computeAutoDuty — and BR NO./OS No./
    // Item Description/penalty-fine columns are raw site values with no
    // corresponding scanned field to borrow from.)
    const COLUMN_SELECTOR_REUSE = { 'Flight No': () => st.bpTargets.flightNo };
    st.columns.forEach(col => {
      if (col.selector || !COLUMN_SELECTOR_REUSE[col.label]) return;
      const sel = COLUMN_SELECTOR_REUSE[col.label]();
      if (sel) { col.selector = sel; col.selectorHint = 'reused from Boarding Pass mapping'; mapped++; }
    });
    if (mapped) save();
    // Keep a visible-in-panel record of the last attempt (not just a toast
    // that fades in a few seconds) so it's obvious exactly which fields
    // weren't found, without needing to click Auto-map again to re-read it.
    if (!silent || final) lastAutoMapResult = { mapped, unresolved, ranAt: Date.now() };
    render();
    if (mapped) toast(`🔎 Auto-mapped ${mapped} field(s) ✓`);
    else if (!silent) toast('Nothing new to auto-map — already mapped, or nothing recognized on this page.');
    if (unresolved.length && (!silent || final)) {
      toast(`⚠ Could not auto-detect on this page — please map manually: ${unresolved.join(', ')}`, 'warn');
    }
  }

  // ── FIELD HELPERS ──────────────────────────────────────────────
  // Most-stable selector for a <table> itself (id > name > CSS path).
  // Shared by column-mapping (getSelector) and the per-row draft-autosave key.
  function getTableSelector(table) {
    if (table.id) return '#' + CSS.escape(table.id);
    if (table.getAttribute('name')) return `[name="${table.getAttribute('name')}"]`;
    const parts = []; let cur = table;
    while (cur && cur !== document.body) {
      if (cur.id) { parts.unshift(cur.tagName.toLowerCase() + '#' + CSS.escape(cur.id)); break; }
      const sibs = cur.parentElement ? [...cur.parentElement.children].filter(c => c.tagName === cur.tagName) : [];
      parts.unshift(cur.tagName.toLowerCase() + (sibs.length > 1 ? `:nth-of-type(${sibs.indexOf(cur) + 1})` : ''));
      cur = cur.parentElement;
    }
    return parts.join(' > ');
  }

  // Returns the most stable selector possible for an element.
  // If inside a table cell, detects the table+column pattern automatically.
  function getSelector(el) {
    // ── TABLE DETECTION: clicked inside a <td> or <th> ──────────
    const td = el.closest('td, th');
    if (td) {
      const tr = td.closest('tr');
      const table = td.closest('table');
      if (tr && table) {
        const colIndex = [...tr.children].indexOf(td);
        const tableSel = getTableSelector(table);
        const rowCount = table.querySelectorAll('tbody tr, tr').length;
        return { sel: tableSel, hint: `📊 Table col ${colIndex + 1}`, isTable: true, colIndex, rowCount };
      }
    }
    // ── NORMAL FIELD DETECTION ───────────────────────────────────
    if (el.id) return { sel: '#' + CSS.escape(el.id), hint: 'by ID' };
    if (el.getAttribute('name')) return { sel: `[name="${el.getAttribute('name')}"]`, hint: 'by name' };
    if (el.dataset?.testid) return { sel: `[data-testid="${el.dataset.testid}"]`, hint: 'by testid' };
    if (el.dataset?.field) return { sel: `[data-field="${el.dataset.field}"]`, hint: 'by data-field' };
    if (el.getAttribute('placeholder')) return { sel: `[placeholder="${el.getAttribute('placeholder')}"]`, hint: 'by placeholder' };
    if (el.getAttribute('aria-label')) return { sel: `[aria-label="${el.getAttribute('aria-label')}"]`, hint: 'by aria-label' };
    const parts = []; let cur = el;
    while (cur && cur !== document.body) {
      if (cur.id) { parts.unshift(cur.tagName.toLowerCase() + '#' + CSS.escape(cur.id)); break; }
      const sibs = cur.parentElement ? [...cur.parentElement.children].filter(c => c.tagName === cur.tagName) : [];
      parts.unshift(cur.tagName.toLowerCase() + (sibs.length > 1 ? `:nth-of-type(${sibs.indexOf(cur) + 1})` : ''));
      cur = cur.parentElement;
    }
    return { sel: parts.join(' > '), hint: 'CSS path ⚠' };
  }

  function readField(sel) {
    if (!sel) return '';
    try {
      const el = queryVisible(sel);
      if (!el) return '';
      if (el.tagName === 'SELECT') return el.options[el.selectedIndex]?.text || el.value || '';
      // <mat-select> has no .value at all, so this used to fall through to
      // el.textContent — which drags in the whole trigger markup's whitespace
      // and ends up in the Excel cell. Read the label span the selection is
      // actually rendered into.
      if (el.tagName === 'MAT-SELECT') return matSelectText(el);
      return el.value !== undefined ? el.value : (el.textContent || '').trim();
    } catch { return ''; }
  }

  // The rendered text of a <mat-select>'s current selection.
  function matSelectText(el) {
    const txt = el.querySelector('.mat-mdc-select-min-line, .mat-mdc-select-value-text');
    return (txt ? txt.textContent : el.textContent || '').replace(/\s+/g, ' ').trim();
  }

  // Read all rows of a table column and join with ' | '
  function readTableCol(tableSel, colIndex) {
    if (!tableSel) return '';
    try {
      const table = document.querySelector(tableSel);
      if (!table) return '';
      // Get data rows only (skip header rows that have no <td>)
      const rows = [...table.querySelectorAll('tr')].filter(r => r.querySelector('td'));
      return rows.map(r => {
        const cell = r.children[colIndex];
        if (!cell) return '';
        // Try input/select inside cell first, then cell text. mat-select must
        // be in this query: the item FormArray table's "Item Type" column (and
        // "Currency" on the gold/silver page) is a <mat-select>, which has no
        // native input underneath — without it those cells fell through to
        // raw cell text and picked up the dropdown-arrow markup's whitespace.
        const inp = cell.querySelector('input, select, textarea, mat-select');
        if (inp) {
          if (inp.tagName === 'SELECT') return inp.options[inp.selectedIndex]?.text || inp.value || '';
          if (inp.tagName === 'MAT-SELECT') return matSelectText(inp);
          if (inp.type === 'checkbox' || inp.type === 'radio') return inp.checked ? 'Yes' : 'No';
          return inp.value || '';
        }
        return cell.textContent.replace(/\s+/g, ' ').trim();
      }).filter(v => v !== '').join(' | ');
    } catch { return ''; }
  }

  // Universal read — handles both single fields and table columns
  function readColumn(col) {
    if (col.isTable) return readTableCol(col.selector, col.colIndex);
    return readField(col.selector);
  }

  // Flash the mapped element(s) green to verify mapping is alive
  function testField(col) {
    if (!col.selector) { toast('No field mapped yet.'); return; }
    try {
      if (col.isTable) {
        const table = document.querySelector(col.selector);
        if (!table) { toast('⚠ Table not found — needs re-mapping!'); return; }
        const rows = [...table.querySelectorAll('tr')].filter(r => r.querySelector('td'));
        rows.forEach(r => {
          const cell = r.children[col.colIndex];
          if (!cell) return;
          const prev = cell.style.background;
          cell.style.background = 'rgba(34,197,94,0.25)';
          setTimeout(() => { cell.style.background = prev; }, 1800);
        });
        toast(`Found ${rows.length} rows ✓ — highlighted`);
        table.scrollIntoView({ behavior: 'smooth', block: 'center' });
      } else {
        const el = queryVisible(col.selector);
        if (!el) { toast('⚠ Field not found — needs re-mapping!'); return; }
        const prev = el.style.outline;
        el.style.outline = '3px solid #22c55e';
        el.scrollIntoView({ behavior: 'smooth', block: 'center' });
        setTimeout(() => { el.style.outline = prev; }, 1800);
        toast('Field found ✓ — highlighted green');
      }
    } catch { toast('Could not locate field.'); }
  }

  // ── Convert DD/MM/YYYY (or Date object) → YYYY-MM-DD for <input type="date"> ──
  function toInputDate(val) {
    if (!val) return '';
    if (val instanceof Date) {
      const z = n => String(n).padStart(2, '0');
      return `${val.getFullYear()}-${z(val.getMonth() + 1)}-${z(val.getDate())}`;
    }
    const s = String(val).trim();
    // Already YYYY-MM-DD
    if (/^\d{4}-\d{2}-\d{2}$/.test(s)) return s;
    // DD/MM/YYYY  or  DD-MM-YYYY
    const m = s.match(/^(\d{1,2})[\/-](\d{1,2})[\/-](\d{4})$/);
    if (m) return `${m[3]}-${m[2].padStart(2, '0')}-${m[1].padStart(2, '0')}`;
    return s;
  }

  // ── Convert any recognized date string → DD/MM/YYYY for text-based date pickers ──
  // DD/MM/YYYY is what MRZ parsing already produces and is the common Indian-forms display format.
  function toDisplayDate(val) {
    if (!val) return '';
    if (val instanceof Date) {
      const z = n => String(n).padStart(2, '0');
      return `${z(val.getDate())}/${z(val.getMonth() + 1)}/${val.getFullYear()}`;
    }
    const s = String(val).trim();
    if (/^\d{2}\/\d{2}\/\d{4}$/.test(s)) return s; // already DD/MM/YYYY
    const iso = s.match(/^(\d{4})-(\d{2})-(\d{2})$/);
    if (iso) return `${iso[3]}/${iso[2]}/${iso[1]}`;
    const dmy = s.match(/^(\d{1,2})-(\d{1,2})-(\d{4})$/);
    if (dmy) return `${dmy[1].padStart(2,'0')}/${dmy[2].padStart(2,'0')}/${dmy[3]}`;
    return s;
  }

  // Heuristic: does this element look like a date field driven by a JS/date-picker
  // widget rather than a native <input type="date">? Government/Citrix forms very
  // often use a readonly text input + popup calendar (jQuery UI, Kendo, custom).
  function looksLikeDateWidget(el) {
    if (el.tagName !== 'INPUT' || el.type === 'date') return false;
    if (el.readOnly || el.classList.contains('hasDatepicker')) return true;
    const sig = `${el.id} ${el.name || ''} ${el.className || ''} ${el.getAttribute('placeholder') || ''}`.toLowerCase();
    return /date|dob|expiry|issue|calendar|dpick/.test(sig);
  }

  // ── ANGULAR MATERIAL OVERLAY-DRIVEN CONTROLS ────────────────────
  // <input class="mat-mdc-autocomplete-trigger"> and <mat-select> do NOT hold
  // their value in the DOM the way a text input does — the form control's
  // real value is only committed when one of the options Material renders
  // into the cdk-overlay-container is actually clicked. Assigning .value and
  // firing input/change (what this script used to do for them) updates the
  // visible text but leaves Angular's own model empty, so the field reads as
  // blank/invalid and gets wiped on blur. Everything below drives the real
  // interaction instead: open the panel, let the site filter its own list,
  // then click the matching option.
  const _sleep = ms => new Promise(r => setTimeout(r, ms));
  // Upper bound on how long to wait for a dropdown's option list. Kept at
  // 600ms: the MutationObserver fires the instant the panel renders, so this
  // timeout is only paid when the site has NO match for what we typed. With
  // five overlay-driven fields and multiple search candidates each, the old
  // 1200ms limit added several seconds of visible lag.
  const OPTION_WAIT_MS = 600;
  const _norm = s => String(s || '').replace(/\s+/g, ' ').trim().toLowerCase();

  function _overlayPanel(el, panelClass) {
    const id = el.getAttribute('aria-controls') || el.getAttribute('aria-owns');
    if (id) {
      const byId = document.getElementById(id);
      if (byId) return byId;
    }
    const open = [...document.querySelectorAll(panelClass)].filter(p => p.offsetParent !== null);
    return open.length ? open[open.length - 1] : null;
  }

  // Resolves the INSTANT the option list appears rather than on the next poll
  // tick. The old 60ms polling loop meant every dropdown cost at least one
  // tick, and a candidate the site has no match for burned the entire timeout
  // before the next candidate was even tried — across five dropdowns that was
  // the multi-second lag the officer was seeing. A MutationObserver catches
  // the panel being rendered immediately; the short interval is only a
  // backstop for option lists that are populated without a DOM mutation under
  // document.body (e.g. attribute-only reveals).
  function _waitForOptions(el, panelClass, timeoutMs) {
    const read = () => {
      const panel = _overlayPanel(el, panelClass);
      return panel ? [...panel.querySelectorAll('mat-option, [role="option"]')] : [];
    };
    const now = read();
    if (now.length) return Promise.resolve(now);
    return new Promise(resolve => {
      let done = false;
      const finish = (v) => {
        if (done) return;
        done = true;
        obs.disconnect(); clearInterval(iv); clearTimeout(to);
        resolve(v);
      };
      const tick = () => { const o = read(); if (o.length) finish(o); };
      const obs = new MutationObserver(tick);
      obs.observe(document.body, { childList: true, subtree: true });
      const iv = setInterval(tick, 15);
      const to = setTimeout(() => finish(read()), timeoutMs);
    });
  }

  // Progressively looser matching, best-first, so "INDIA" never accidentally
  // wins over an exact "IND" when the site lists codes (or vice versa).
  function _pickOption(opts, aliases) {
    const wants = aliases.map(_norm).filter(Boolean);
    const texts = opts.map(o => _norm(o.textContent));
    for (const w of wants) { const i = texts.indexOf(w); if (i >= 0) return opts[i]; }
    for (const w of wants) {
      const i = texts.findIndex(t => t.startsWith(w) || t.startsWith(w + ' ') || t.split(/[-–(,]/)[0].trim() === w);
      if (i >= 0) return opts[i];
    }
    for (const w of wants) {
      if (w.length < 3) continue;
      const i = texts.findIndex(t => t.includes(w));
      if (i >= 0) return opts[i];
    }
    return null;
  }

  async function fillAutocomplete(el, key, raw) {
    const aliases = autocompleteCandidates(key, raw);
    if (!aliases.length) return false;
    // Committing an option means focusing this control to open its panel, which
    // pulls the caret out of whatever the officer is typing in — their next
    // keystrokes then land on <body> and are lost silently. Let them finish.
    let officerFocus = await _awaitOfficerIdle(0);
    const setter = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value')?.set;
    const put = v => { if (setter) setter.call(el, v); else el.value = v; };

    // Search strings to try, widening as we go. The exact label the site uses
    // is not knowable from here — "SRI LANKA" vs "Sri Lanka (LK)" vs
    // "COLOMBO - CMB" — so after the full names and the raw code, fall back to
    // ever-shorter prefixes. A short prefix matches far more list formats, and
    // if the site narrows to a single option we can take it outright.
    const searches = [];
    for (const a of aliases) {
      searches.push(a);
      if (a.length >= 4) searches.push(a.slice(0, 4));
      if (a.length >= 3) searches.push(a.slice(0, 3));
    }

    for (const search of [...new Set(searches)]) {
      // Re-check every round, not just on entry: a fill already in flight when
      // the officer starts typing would otherwise steal the caret back on its
      // next attempt. This bounds any loss to keystrokes typed in the same
      // instant as a focus() call rather than for the whole fill.
      const yielded = await _awaitOfficerIdle(0);
      if (yielded && yielded !== el) officerFocus = yielded;
      // Arm the borrow from whoever actually holds focus right now, not only
      // from _awaitOfficerIdle's answer. An officer who has clicked into a box
      // but not yet typed has no edit history, so the idle check reports
      // nobody — and their first keystrokes were the ones going missing. Any
      // ordinary text box that isn't one of this script's own dropdowns is a
      // place the officer could be working.
      const prev = document.activeElement;
      const prevIsOfficerBox = prev && prev !== el &&
        (prev.tagName === 'INPUT' || prev.tagName === 'TEXTAREA') &&
        !prev.classList.contains('mat-mdc-autocomplete-trigger');
      _setBorrow(officerFocus && officerFocus !== el ? officerFocus
                 : (prevIsOfficerBox ? prev : null));
      el.focus();
      el.dispatchEvent(new Event('focusin', { bubbles: true }));
      // Material's trigger opens on click as well as on input; some builds
      // only bind one of them, so do both rather than relying on either.
      el.dispatchEvent(new MouseEvent('mousedown', { bubbles: true }));
      el.click();
      // Clear first: some of these lists only (re)load on a value *change*,
      // and re-typing the same text the field already holds is a no-op.
      put('');
      el.dispatchEvent(new InputEvent('input', { bubbles: true }));
      put(search);
      el.dispatchEvent(new InputEvent('input', { bubbles: true }));
      el.dispatchEvent(new Event('keyup', { bubbles: true }));
      const opts = await _waitForOptions(el, '.mat-mdc-autocomplete-panel', OPTION_WAIT_MS);
      if (!opts.length) continue;
      // Prefer a real text match; otherwise, if our search narrowed the site's
      // own list to exactly one option, that IS the answer — the site did the
      // matching for us and its label format no longer matters.
      const match = _pickOption(opts, aliases) || (opts.length === 1 ? opts[0] : null);
      if (match) {
        match.click();
        await _sleep(30); // let Angular write back the display text and close the panel
        // Confirm something actually stuck: a click Material ignored leaves
        // the box holding our search string rather than the option's label.
        const now = String(el.value || '').trim().toLowerCase();
        if (now && now !== search.toLowerCase()) { _setBorrow(null); _returnFocus(officerFocus); return true; }
      }
    }
    // Nothing matched. Clear our leftover search text so the officer opens the
    // dropdown on a clean field instead of one pre-filled with a dead query.
    put('');
    el.dispatchEvent(new InputEvent('input', { bubbles: true }));
    el.blur();
    // Disarm unconditionally: _returnFocus is a no-op when the officer wasn't
    // typing, and leaving the borrow armed would buffer their next keystrokes
    // with nothing left to flush them.
    _setBorrow(null);
    _returnFocus(officerFocus);
    return false;
  }

  // Angular Material <input matDatepicker>. Two separate traps here, both of
  // which this script used to walk straight into:
  //
  //  1. These sites very commonly wire (focus)="picker.open()", so the old
  //     code's synthetic focus/keydown/blur burst literally popped the
  //     calendar open over the form (exactly what was observed) and let the
  //     calendar's own state write back over the typed text. Only 'input' and
  //     'change' are dispatched now — that is the same path real typing takes,
  //     and it is all MatDatepickerInput actually listens to.
  //  2. The value has to satisfy the site's DateAdapter, which is NOT
  //     guaranteed to be DD/MM/YYYY. Feeding a string the adapter can't parse
  //     leaves a half-parsed date behind (the reported "year is right, the day
  //     and month come out as NaN"). Rather than guessing the adapter, offer
  //     each plausible format and keep the first one the control actually
  //     accepts — Material flags a rejected value by putting the field into
  //     ng-invalid (matDatepickerParse), so success is verifiable here rather
  //     than assumed.
  async function fillMatDatepicker(el, val) {
    const setter = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value')?.set;
    const put = v => { if (setter) setter.call(el, v); else el.value = v; };
    const dmy = toDisplayDate(val);            // 26/02/1981 — the site's own mat-hint format
    const iso = toInputDate(val);              // 1981-02-26 — what its max="" attribute uses
    const p = dmy.split('/');
    const mdy = p.length === 3 ? `${p[1]}/${p[0]}/${p[2]}` : '';
    const MON = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
    const dMon = p.length === 3 ? `${p[0]} ${MON[+p[1] - 1]} ${p[2]}` : '';
    // Two different reasons a date box can go ng-invalid, and they must NOT be
    // treated the same:
    //
    //   matDatepickerParse — the adapter could not read the string. The format
    //     is wrong; try the next one.
    //   matDatepickerMin / matDatepickerMax — it read the date perfectly well,
    //     and the site's own rule rejects it. These fields carry max="today"
    //     (date of birth, issuing date) and min="today" (expiry), so an expired
    //     passport trips it legitimately.
    //
    // Treating a range violation as "wrong format" is what mangled these boxes:
    // the loop discarded the correctly parsed 26/02/1981, kept probing, and
    // left behind the LAST candidate it tried — 02/26/1981 — whose day 26 is
    // not a month. That is the NaN. A range failure is the officer's to see and
    // override, so the real date must stay in the box, flagged, not be replaced
    // by a mangled one.
    //
    // Parse success is judged by what the control does with the text, not by
    // validity: Angular Material rewrites the input to its own display format
    // once the adapter has understood it, and leaves the raw text alone when it
    // has not.
    // ISO is unambiguous — a day/month pair can never be misread the other
    // way round — so it has to be tried BEFORE any slash-separated
    // candidate. A slash string like "24/09/2025" is genuinely ambiguous to
    // a generic date adapter, which commonly reads slash dates as
    // MM/DD/YYYY: when the day is >12 that produces an impossible month and
    // the candidate is (correctly) rejected, but when the day is <=12 (e.g.
    // a DOB of "01/06/1982") the adapter happily accepts it AS THE WRONG
    // DATE — 6 Jan instead of 1 Jun — which then LOOKS right on screen only
    // by coincidence of the two digits matching. That's the actual source
    // of "DOB is sometimes right, sometimes reversed": it was never random,
    // it depended on whether the day happened to be a valid month number.
    // Trying iso first means whichever candidate is accepted first is
    // always the true calendar date, never a silently swapped one — and
    // since iso is understood by every adapter that matters here, it also
    // means the day>12 fields (issuing/expiry) stop falling through to a
    // literal "YYYY-MM-DD" being left sitting in the box.
    const cands = [iso, dmy, dMon, mdy].filter(Boolean);
    let best = null;               // parsed, but the site's range rejected it
    let acceptedCand = null;
    for (const cand of cands) {
      put(cand);
      el.dispatchEvent(new InputEvent('input', { bubbles: true }));
      el.dispatchEvent(new Event('change', { bubbles: true }));
      await _sleep(24);            // a frame plus change detection
      const shown = String(el.value || '');
      if (/nan|invalid/i.test(shown) || shown === '') continue;   // adapter choked
      if (!el.classList.contains('ng-invalid')) { acceptedCand = cand; break; }  // parsed AND accepted
      // Parsed but out of range. Hold on to it and keep looking for a format
      // this control likes better; if none exists, this is what it keeps.
      if (!best) best = shown;
    }
    if (acceptedCand) {
      // The date itself is now correct and accepted, but if the candidate
      // that got it there wasn't dmy, the box is literally showing that
      // other format (iso/dMon/mdy) instead of the site's own DD/MM/YYYY
      // display. A blur — with no synthetic focus before it, so it can't
      // pop the calendar the way a synthetic focus does — asks Material's
      // own MatDatepickerInput to redraw the already-valid, already-correct
      // date using its configured display format, fixing the visible text
      // without touching the value underneath it.
      if (acceptedCand !== dmy) {
        el.dispatchEvent(new Event('blur', { bubbles: true }));
        await _sleep(24);
      }
      return true;
    }
    if (best) {
      put(best);
      el.dispatchEvent(new InputEvent('input', { bubbles: true }));
      el.dispatchEvent(new Event('change', { bubbles: true }));
      return true;                 // the true date is in the box, flagged by the site
    }
    // Nothing was understood. Leave the box empty rather than holding a probe
    // string that reads as a real date.
    put('');
    el.dispatchEvent(new InputEvent('input', { bubbles: true }));
    return false;
  }

  async function fillMatSelect(el, val) {
    el.dispatchEvent(new MouseEvent('mousedown', { bubbles: true }));
    el.click();
    const opts = await _waitForOptions(el, '.mat-mdc-select-panel', OPTION_WAIT_MS);
    const match = _pickOption(opts, [String(val)]);
    if (match) { match.click(); await _sleep(30); return true; }
    // Don't leave an opened panel covering the form if we couldn't resolve it.
    document.dispatchEvent(new KeyboardEvent('keydown', { bubbles: true, key: 'Escape' }));
    return false;
  }

  // Returns a Promise<boolean> for the overlay-driven controls above (so the
  // caller can await a cascade), undefined for every ordinary field.
  function fillField(sel, val, key) {
    if (!sel || val === undefined || val === null || val === '') return;
    try {
      const el = queryVisible(sel);
      if (!el) return;
      return applyValueByElementType(el, val, key);
    } catch { }
  }

  // Core "given this element, make its value/state equal val" logic — shared by
  // fillField() (MRZ/BP/defaults/column-mrz-binding, always plain strings) and
  // the draft-autosave restorer (which additionally passes structured
  // { __kind: 'checkbox', value: bool } objects for checkbox/radio inputs,
  // since a checkbox's "value" is really its .checked state, not el.value).
  function applyValueByElementType(el, val, key) {
    try {
      if (val && typeof val === 'object' && val.__kind) {
        if (val.__kind === 'checkbox') {
          // Native .click() on the real input — fires the full trusted-like
          // event sequence a framework's change/ripple handlers expect, the
          // same reasoning already used for the date-widget fallback below.
          if (!!el.checked !== !!val.value) el.click();
          return;
        }
        val = val.value; // __kind === 'text' → fall through to string handling
      }
      if (val === undefined || val === null || val === '') return;
      const tag = el.tagName;

      // ── ANGULAR MATERIAL autocomplete / mat-select (overlay-driven) ──
      if (tag === 'INPUT' && el.classList.contains('mat-mdc-autocomplete-trigger')) {
        return fillAutocomplete(el, key, val);
      }
      if (tag === 'MAT-SELECT') {
        return fillMatSelect(el, val);
      }

      // ── SELECT dropdown: match by option text (fuzzy) or value ──
      if (tag === 'SELECT') {
        const v = String(val).trim().toLowerCase();
        // Try exact value match first, then case-insensitive text match
        let matched = [...el.options].find(o => o.value.toLowerCase() === v)
          || [...el.options].find(o => o.text.toLowerCase() === v)
          || [...el.options].find(o => o.text.toLowerCase().includes(v) || v.includes(o.text.toLowerCase()));
        if (matched) {
          el.value = matched.value;
          el.dispatchEvent(new Event('input',  { bubbles: true }));
          el.dispatchEvent(new Event('change', { bubbles: true }));
        }
        return;
      }

      // ── DATE PICKER: <input type="date"> → needs YYYY-MM-DD format ──
      if (tag === 'INPUT' && el.type === 'date') {
        const iso = toInputDate(val);
        if (!iso) return;
        // Use nativeInputValueSetter for React-controlled inputs, fallback to plain assignment
        const nativeSetter = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value')?.set;
        if (nativeSetter) nativeSetter.call(el, iso);
        else el.value = iso;
        el.dispatchEvent(new InputEvent('input',  { bubbles: true }));
        el.dispatchEvent(new Event ('change', { bubbles: true }));
        return;
      }

      // ── DATE PICKER: Angular Material <input matDatepicker> ──────
      // The real site's date_of_birth/passportIssuingDate/date_Of_passport_expiry/
      // date_of_arrival fields all carry this exact class. Material's own
      // MatDatepickerInput directive already listens to the native 'input'
      // event to parse-and-commit the value via its DateAdapter (same path
      // as real typing) — no focus/keydown/blur theatrics are needed, and
      // dispatching them was actively harmful: a synthetic 'focus' pops the
      // on-screen calendar (observed live — fields showed the calendar open
      // instead of a filled value), and the subsequent blur then re-formats
      // from whatever the calendar's own (unrelated) internal state was,
      // which is the likely source of the "day/month came out as NaN"
      // symptom while the year — read from a different code path — stayed
      // correct. Keep this narrow (exact class match only) so it doesn't
      // affect any non-Material date widget.
      if (el.classList.contains('mat-datepicker-input')) {
        return fillMatDatepicker(el, val);
      }

      // ── DATE PICKER: JS/jQuery-UI/Kendo widget on a (often readonly) text input ──
      if (looksLikeDateWidget(el)) {
        const display = toDisplayDate(val);
        if (!display) return;
        // 1) If jQuery UI datepicker is attached, drive it through its own API —
        //    this keeps the widget's internal calendar state (not just el.value) in sync.
        try {
          const $ = window.jQuery || window.$;
          if ($ && $.fn && $.fn.datepicker && el.classList.contains('hasDatepicker')) {
            const [dd, mm, yyyy] = display.split('/').map(Number);
            $(el).datepicker('setDate', new Date(yyyy, mm - 1, dd));
            el.dispatchEvent(new Event('change', { bubbles: true }));
            return;
          }
        } catch { /* fall through to generic handling below */ }
        // 2) Generic fallback: force the value through even if readonly, then fire
        //    the full event sequence (focus/input/keydown/keyup/change/blur) that
        //    most validation frameworks and calendar widgets react to.
        const wasReadOnly = el.hasAttribute('readonly');
        if (wasReadOnly) el.removeAttribute('readonly');
        const nativeSetter = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value')?.set;
        if (nativeSetter) nativeSetter.call(el, display);
        else el.value = display;
        el.dispatchEvent(new Event('focus', { bubbles: true }));
        el.dispatchEvent(new InputEvent('input', { bubbles: true }));
        el.dispatchEvent(new KeyboardEvent('keydown', { bubbles: true, key: 'Enter' }));
        el.dispatchEvent(new KeyboardEvent('keyup',   { bubbles: true, key: 'Enter' }));
        el.dispatchEvent(new Event('change', { bubbles: true }));
        el.dispatchEvent(new Event('blur',   { bubbles: true }));
        if (wasReadOnly) el.setAttribute('readonly', 'readonly');
        // NOTE: a widget that ONLY accepts a value via clicking a day in its popup
        // calendar (ignores el.value entirely, e.g. some fully-controlled React
        // pickers) cannot be filled generically without seeing its real markup.
        // If a mapped date field silently doesn't take the value on the live site,
        // that's the case — flag it and we'll add a widget-specific driver then.
        return;
      }

      // ── CUSTOM / NON-NATIVE DROPDOWN (Select2 / Kendo / div-based combobox) ──
      // Best-effort only: real markup is unknown until we see the live site.
      if (tag !== 'INPUT' && tag !== 'TEXTAREA' &&
          (el.getAttribute('role') === 'combobox' || /dropdown|select2|combo|chosen/i.test(el.className || ''))) {
        const v = String(val).trim().toLowerCase();
        el.dispatchEvent(new MouseEvent('mousedown', { bubbles: true }));
        el.click();
        setTimeout(() => {
          const opts = [...document.querySelectorAll('[role="option"], li, .option, .dropdown-item, .chosen-results li')]
            .filter(o => o.offsetParent !== null);
          const match = opts.find(o => o.textContent.trim().toLowerCase() === v)
            || opts.find(o => o.textContent.trim().toLowerCase().includes(v));
          if (match) match.click();
        }, 150);
        return;
      }

      // ── TEXT / TEXTAREA / other inputs ──────────────────────────
      const proto = el instanceof HTMLTextAreaElement ? HTMLTextAreaElement.prototype : HTMLInputElement.prototype;
      const desc  = Object.getOwnPropertyDescriptor(proto, 'value');
      if (desc?.set) desc.set.call(el, val);
      else el.value = val;
      el.dispatchEvent(new InputEvent('input',  { bubbles: true }));
      el.dispatchEvent(new Event ('change', { bubbles: true }));
      el.dispatchEvent(new Event ('blur',   { bubbles: true }));
    } catch { }
  }

  // ── DEFAULT VALUE FILL TARGETS ──────────────────────────────────
  // Fields that always get the same fixed value (e.g. Countries Visited = "NIL")
  // regardless
  // of any scan. User-extensible — add/rename/remap any number of these live,
  // so a field whose exact name/position isn't known yet is never a blocker.
  // Awaited one at a time: a default value can perfectly well be mapped onto
  // one of the overlay-driven dropdowns, and those only resolve once the site
  // has rendered its own option list (see fillAutocomplete).
  // A rule's value is either typed in by the officer or read live out of
  // another field. "Copy from field" exists because the site actively blocks
  // pasting between some boxes — Mobile into Instant Messenger Number cannot be
  // done by hand at all, which is precisely the sort of retyping this is for.
  function _ruleValue(t) {
    if (!t) return '';
    if (t.mode === 'copy') {
      if (!t.sourceSelector) return '';
      try { return _currentText(queryVisible(t.sourceSelector)); } catch { return ''; }
    }
    return t.value === undefined ? '' : String(t.value);
  }

  async function fillAllDefaults() {
    let n = 0;
    for (const t of (st.defaultTargets || [])) {
      const v = _ruleValue(t);
      if (t.selector && v !== '') { await fillField(t.selector, v); n++; }
    }
    return n;
  }

  // Keep every "copy from field" rule live: the officer types a mobile number
  // once and the mirrored box follows, instead of being filled once at load
  // when the source was still empty. Only trusted events count, so this script
  // writing the target can never feed itself, and a rule whose target IS
  // another rule's source is applied without recursing.
  let _mirrorTimer = null, _mirroring = false;
  function armFieldMirrors() {
    const onEdit = (e) => {
      if (!e.isTrusted || _mirroring) return;
      const rules = (st.defaultTargets || []).filter(t => t.mode === 'copy' && t.sourceSelector && t.selector);
      if (!rules.length) return;
      let hit = false;
      for (const t of rules) {
        let src = null;
        try { src = queryVisible(t.sourceSelector); } catch { }
        if (src && (src === e.target || src.contains(e.target))) { hit = true; break; }
      }
      if (!hit) return;
      clearTimeout(_mirrorTimer);
      _mirrorTimer = setTimeout(async () => {
        _mirroring = true;
        try {
          for (const t of rules) {
            const v = _ruleValue(t);
            if (v === '') continue;
            let tgt = null;
            try { tgt = queryVisible(t.selector); } catch { }
            if (!tgt || _currentText(tgt) === v) continue;   // already right — don't fight the officer
            await fillField(t.selector, v);
          }
        } finally { _mirroring = false; }
      }, 250);
    };
    document.addEventListener('input', onEdit, true);
    document.addEventListener('change', onEdit, true);
  }

  // Every labelled control on the page, for the rule pickers. Choosing from a
  // list beats the click-the-field crosshair for anything the page already
  // names, and it is the only way to pick a field that sits under a collapsed
  // accordion. A duplicated formcontrolname (pessenger_name appears twice) is
  // disambiguated by its accordion, exactly as the scan selectors are.
  function discoverFields() {
    const out = [], seen = new Set();
    document.querySelectorAll('[formcontrolname]').forEach(el => {
      const fc = el.getAttribute('formcontrolname');
      if (!fc) return;
      const dupes = document.querySelectorAll('[formcontrolname="' + CSS.escape(fc) + '"]');
      let sel = '[formcontrolname="' + fc + '"]';
      if (dupes.length > 1) {
        const acc = el.closest('[id^="collapse"]');
        if (acc && acc.id) sel = '#' + acc.id + ' ' + sel;
      }
      if (seen.has(sel)) return;
      seen.add(sel);
      let label = '';
      const host = el.closest('mat-form-field') || el.parentElement;
      const lab = host && (host.querySelector('mat-label') || host.querySelector('label'));
      if (lab) label = lab.textContent.trim();
      if (!label) {
        const p = el.closest('div');
        const l2 = p && p.querySelector('label');
        if (l2) label = l2.textContent.trim();
      }
      if (!label) label = fc;
      out.push({ selector: sel, label: label.replace(/\s+/g, ' ').slice(0, 48), fc });
    });
    return out.sort((a, b) => a.label.localeCompare(b.label));
  }

  // ── DRAFT AUTOSAVE (2-hour TTL) ──────────────────────────────────
  // The real site has no "Save as draft" — everything typed is lost on a
  // refresh or on navigating to search another baggage record. This silently
  // snapshots every field on the page (debounced) into the same localStorage
  // state already used for everything else, keyed by whichever passenger the
  // officer is currently on, so switching between in-progress passengers (or
  // recovering from an accidental refresh) doesn't mean retyping. A draft is
  // only ever read back when the officer explicitly clicks "Restore" in the
  // panel (or the small found-a-draft toast) — nothing is force-filled, and
  // finalizing via the site's own Save button removes the draft immediately
  // since it's no longer "in progress".
  const DRAFT_TTL_MS = 2 * 60 * 60 * 1000; // 2 hours
  const DRAFT_DEBOUNCE_MS = 800;
  const FIELD_QUERY = 'input, textarea, select, mat-select, [role="combobox"]';

  function isDraftableField(el) {
    if (el.closest('#__brc_panel') || el === toggleBtn) return false;
    if (el.tagName === 'INPUT' && ['file', 'hidden', 'button', 'submit', 'reset', 'image'].includes(el.type)) return false;
    if (el.disabled) return false;
    return true;
  }

  // What does this field currently hold? Checkboxes/radios use their own
  // .checked (not .value, which for a checkbox is a fixed constant like "on").
  // Angular-Material-style <mat-select> has no native <select> underneath —
  // its selection is only visible as rendered text, so that's what we read.
  function captureFieldValue(el) {
    if (el.tagName === 'INPUT' && (el.type === 'checkbox' || el.type === 'radio')) {
      return { __kind: 'checkbox', value: !!el.checked };
    }
    // Only NON-input comboboxes (i.e. <mat-select>) keep their selection as
    // rendered text. The five mat-autocomplete fields are real <input
    // role="combobox"> elements that DO hold their text in .value — matching
    // them on role first (as this did) found no value-text span and captured
    // an empty string, so Nationality / Country of Issuance / Country and
    // Airport (from where coming) / Port of Arrival were silently absent from
    // every draft and never came back on restore.
    if (el.tagName !== 'INPUT' && el.tagName !== 'TEXTAREA' &&
        (el.tagName === 'MAT-SELECT' || el.getAttribute('role') === 'combobox')) {
      const txt = el.querySelector('.mat-mdc-select-value-text, .mat-mdc-select-min-line');
      return { __kind: 'text', value: txt ? txt.textContent.trim() : '' };
    }
    return { __kind: 'text', value: el.value || '' };
  }

  // Stable-enough key for a field across a save→restore cycle. Repeated
  // FormArray-style rows (item/gold-silver/currency tables) reuse the exact
  // same field name/formcontrolname on every row, so those are keyed by
  // table-or-formarray + row-index instead; everything else is keyed by
  // formcontrolname/id/name, with a running occurrence counter for the rare
  // genuine duplicate (e.g. "pessenger_name" appears once under Passport
  // Details and again under Boarding Pass on the real site).
  function computeDraftKey(el, counters) {
    const formArrayEl = el.closest('[formarrayname]');
    const table = el.closest('table');
    if (formArrayEl || table) {
      const tr = el.closest('tr');
      let rowIdx = 0;
      if (tr && tr.parentElement) {
        rowIdx = [...tr.parentElement.children].filter(c => c.tagName === 'TR').indexOf(tr);
      }
      const rootSel = (formArrayEl && formArrayEl.getAttribute('formarrayname')) || (table ? getTableSelector(table) : 'row');
      let local = el.getAttribute('formcontrolname') || el.name || el.className || el.tagName;
      if (el.type === 'radio') local += '::' + el.value; // one shared name/formcontrolname per option — disambiguate by value
      return `row::${rootSel}::${rowIdx}::${local}`;
    }
    // Radio buttons: Angular Material puts formcontrolname on the enclosing
    // mat-radio-group, not the individual native input, and auto-generates a
    // per-input id (e.g. "mat-radio-3-input") whose number depends on render
    // order — not stable across a save→refresh→restore cycle. The option's
    // own `value` IS author-set and stable, so key off the group + value
    // rather than the input's own id/name.
    if (el.type === 'radio') {
      const group = el.closest('mat-radio-group, [role="radiogroup"], fieldset');
      const base = (group && (group.getAttribute('formcontrolname') || group.id)) || el.name || 'radiogroup';
      return `radio::${base}::${el.value}`;
    }
    // Same problem, same shape, for <mat-checkbox>: the formcontrolname lives
    // on the mat-checkbox wrapper while the native input underneath carries
    // only an auto-generated, render-order-dependent id ("mat-mdc-checkbox-5-
    // input"). Keying off that id meant a checkbox draft saved before a
    // reload could never be matched back to the same control afterwards.
    if (el.type === 'checkbox') {
      const wrap = el.closest('mat-checkbox, [formcontrolname]');
      const fcn = wrap && wrap.getAttribute('formcontrolname');
      if (fcn) return `checkbox::${fcn}`;
    }
    const base = el.getAttribute('formcontrolname') ? 'fc::' + el.getAttribute('formcontrolname')
      : el.id ? 'id::' + el.id
      : el.name ? 'name::' + el.name
      : 'path::' + getSelector(el).sel;
    const n = counters[base] || 0;
    counters[base] = n + 1;
    return n ? `${base}#${n}` : base;
  }

  function purgeExpiredDrafts() {
    const now = Date.now();
    let changed = false;
    Object.keys(st.drafts).forEach(k => {
      if (now - st.drafts[k].savedAt > DRAFT_TTL_MS) { delete st.drafts[k]; changed = true; }
    });
    if (changed) save();
  }

  // Which passenger is currently being worked on? Reuses the passport-number
  // MRZ Fill Target the officer already mapped during setup — no extra
  // configuration step needed just for drafts. Falls back to a single
  // "untitled" slot when no passport number has been typed/mapped yet.
  // Auto-map is a manual button, so on a fresh profile st.mrzTargets is empty
  // — and with no passportNo selector EVERY passenger's draft collapsed into
  // the single "__untitled__" slot, each one overwriting the last. The real
  // site's selector is already known (MRZ_AUTO_SELECTORS), so fall back to
  // detecting it live rather than depending on the officer having clicked
  // Auto-map first. Nothing is persisted here — this is read-only detection.
  function _liveTarget(key, table) {
    const stored = (table === 'bp' ? st.bpTargets : st.mrzTargets)?.[key];
    if (stored) return stored;
    const candidates = (table === 'bp' ? BP_AUTO_SELECTORS : MRZ_AUTO_SELECTORS)[key];
    return candidates ? autoDetectSelector(candidates) : null;
  }

  function currentPassengerKey() {
    try {
      const sel = _liveTarget('passportNo');
      if (sel) {
        const v = queryVisible(sel)?.value?.trim();
        if (v) return v;
      }
    } catch { }
    return '__untitled__';
  }
  function currentPassengerName() {
    try {
      const sel = _liveTarget('fullName');
      if (sel) return queryVisible(sel)?.value?.trim() || '';
    } catch { }
    return '';
  }

  let _lastDraftKey = null;
  // Draft key the officer explicitly deleted; refuse to recreate it until they
  // move to a different passenger. Cleared in doDraftSave once the key changes.
  let _suppressDraftKey = null;
  // ── SHARED-FOLDER SYNC (File System Access API) ──────────────────
  // The one real way to bridge Chrome ↔ Edge: both can read/write a real
  // file on disk, unlike localStorage (sandboxed per browser profile).
  // Requires ONE manual "Connect Shared Folder" click per browser — a
  // native folder picker, since no page can be granted filesystem access
  // without an explicit user gesture — but after that, push/pull happen
  // automatically with no further clicks. Chromium-only (Chrome + Edge both
  // qualify); silently does nothing if unsupported or blocked by an
  // enterprise/Citrix policy — this is a bonus path, not a dependency.
  const SYNC_FILE_NAME = 'atithi-helper-sync.json';
  let _syncDirHandle = null;

  function supportsSharedFolderSync() {
    return typeof window.showDirectoryPicker === 'function';
  }

  // A FileSystemDirectoryHandle isn't JSON-serializable, so it can't live in
  // localStorage like everything else — IndexedDB can store it directly.
  // Still per-browser-profile, same as localStorage, but that's fine: each
  // browser independently remembers ITS OWN previously-granted handle to
  // the SAME real folder the officer picked in both.
  function idbGet(key) {
    return new Promise((resolve) => {
      try {
        const req = indexedDB.open('brc_sync', 1);
        req.onupgradeneeded = () => req.result.createObjectStore('handles');
        req.onsuccess = () => {
          const tx = req.result.transaction('handles', 'readonly');
          const g = tx.objectStore('handles').get(key);
          g.onsuccess = () => resolve(g.result || null);
          g.onerror = () => resolve(null);
        };
        req.onerror = () => resolve(null);
      } catch { resolve(null); }
    });
  }
  function idbSet(key, val) {
    return new Promise((resolve) => {
      try {
        const req = indexedDB.open('brc_sync', 1);
        req.onupgradeneeded = () => req.result.createObjectStore('handles');
        req.onsuccess = () => {
          const tx = req.result.transaction('handles', 'readwrite');
          tx.objectStore('handles').put(val, key);
          tx.oncomplete = () => resolve();
          tx.onerror = () => resolve();
        };
        req.onerror = () => resolve();
      } catch { resolve(); }
    });
  }

  async function connectSharedFolder() {
    if (!supportsSharedFolderSync()) { toast("⚠ This browser doesn't support shared-folder sync — drafts/shifts still save normally to this browser, just not synced.", 'warn'); return; }
    try {
      // Browsers can drop a previously-granted permission across restarts
      // (and won't silently re-grant it without a user gesture, for good
      // reason). If we already remember a folder from before, try a
      // lightweight re-confirm on THAT handle first — one click, no need to
      // re-pick the same folder from scratch every session.
      const stored = await idbGet('syncDir');
      if (stored) {
        const perm = await stored.requestPermission({ mode: 'readwrite' });
        if (perm === 'granted') {
          _syncDirHandle = stored;
          await pullSharedFolderSync();
          await pushSharedFolderSync();
          render();
          return;
        }
      }
      const handle = await window.showDirectoryPicker();
      _syncDirHandle = handle;
      await idbSet('syncDir', handle);
      toast('🔗 Shared folder connected — pick the SAME folder in the other browser too.');
      await pullSharedFolderSync();
      await pushSharedFolderSync();
      render();
    } catch { /* user cancelled the picker — no-op, localStorage keeps working regardless */ }
  }

  async function ensureSyncDirHandle() {
    if (_syncDirHandle) return _syncDirHandle;
    if (!supportsSharedFolderSync()) return null;
    const stored = await idbGet('syncDir');
    if (!stored) return null;
    try {
      const perm = await stored.requestPermission({ mode: 'readwrite' });
      if (perm !== 'granted') return null;
      _syncDirHandle = stored;
      return stored;
    } catch { return null; }
  }

  async function pushSharedFolderSync() {
    const dir = await ensureSyncDirHandle();
    if (!dir) return;
    try {
      const fh = await dir.getFileHandle(SYNC_FILE_NAME, { create: true });
      const writable = await fh.createWritable();
      await writable.write(JSON.stringify({ shifts: st.shifts, drafts: st.drafts, savedAt: Date.now() }));
      await writable.close();
    } catch { /* transient write failure — the next debounced save retries anyway */ }
  }

  // Merge-only, same rule as everywhere else in this file: shifts merged by
  // id (keep whichever copy has more rows), drafts merged by key (keep
  // whichever has the newer savedAt) — never blindly overwrites what THIS
  // browser already has with what the other browser last wrote.
  async function pullSharedFolderSync() {
    const dir = await ensureSyncDirHandle();
    if (!dir) return;
    try {
      const fh = await dir.getFileHandle(SYNC_FILE_NAME, { create: false });
      const file = await fh.getFile();
      const data = JSON.parse(await file.text());
      let merged = 0;
      (data.shifts || []).forEach(incoming => {
        const existing = st.shifts.find(s => s.id === incoming.id);
        if (!existing) { st.shifts.push(incoming); merged++; }
        else if ((incoming.rows?.length || 0) > (existing.rows?.length || 0)) { Object.assign(existing, incoming); merged++; }
      });
      Object.entries(data.drafts || {}).forEach(([k, d]) => {
        if (!st.drafts[k] || d.savedAt > st.drafts[k].savedAt) { st.drafts[k] = d; merged++; }
      });
      if (merged) { save(); render(); toast(`🔗 Synced ${merged} record(s) from shared folder.`); }
    } catch { /* file doesn't exist yet, or permission lost — silently skip */ }
  }

  function doDraftSave() {
    // Central guard: never capture anything unless this actually looks like
    // an Atithi declaration page/tab right now — protects every caller
    // (typing, the reload/close flush) at once, so a stray input event on a
    // completely unrelated site/page (this script runs on <all_urls>) never
    // gets written into st.drafts.
    if (!isAtithiPage()) return;
    const els = [...document.querySelectorAll(FIELD_QUERY)].filter(isDraftableField);
    if (!els.length) return;
    const counters = {};
    const values = {};
    els.forEach(el => { values[computeDraftKey(el, counters)] = captureFieldValue(el); });
    const meaningful = Object.values(values).some(v => v.__kind === 'checkbox' ? v.value : String(v.value || '').trim());
    if (!meaningful) return;
    // Never save a draft without a real passport number — a blank or
    // empty-form page (e.g. open-then-refresh before any scan) would
    // otherwise keep writing irrelevant data into the '__untitled__' slot,
    // cluttering Drafts and silently overwriting real in-progress data.
    const ppSel = _liveTarget('passportNo');
    const ppVal = ppSel ? (queryVisible(ppSel)?.value || '').trim() : '';
    if (!ppVal) return;
    purgeExpiredDrafts();
    const key = currentPassengerKey();
    if (_suppressDraftKey && key !== _suppressDraftKey) _suppressDraftKey = null;
    // Migrate the draft forward as the passport number gets typed out
    // ("T" → "T3" → "T39" …), but ONLY when the new key genuinely extends the
    // old one (or the old one was the no-passport-yet placeholder).
    //
    // This used to delete st.drafts[_lastDraftKey] on ANY key change, which
    // silently destroyed exactly the data this feature exists to protect: the
    // moment the site cleared the form, or the officer opened a different
    // passenger, the key changed to something unrelated and the previous
    // passenger's in-progress draft was deleted before they could recover it.
    // Anything not recognised as the same record is now left alone and simply
    // expires on its own 2-hour TTL — an orphaned draft is recoverable, a
    // deleted one is not.
    if (_lastDraftKey && _lastDraftKey !== key &&
        (_lastDraftKey === '__untitled__' || key.startsWith(_lastDraftKey))) {
      delete st.drafts[_lastDraftKey];
    }
    // An officer who deleted this passenger's draft meant it. The form still
    // holds their data, so without this the very next keystroke wrote the draft
    // straight back and the ✕ looked broken — it deleted, then the autosave
    // undid it a second later. The block lifts as soon as a different passenger
    // is on screen, so returning to this one later still saves normally.
    if (key === _suppressDraftKey) return;
    _lastDraftKey = key;
    st.drafts[key] = { savedAt: Date.now(), name: currentPassengerName(), values };
    save();
    pushSharedFolderSync(); // fire-and-forget — never blocks typing
  }
  let _draftSaveTimer = null;
  let _passportTypedTimer = null;
  // Restoring a draft fires input/change events on every field it fills, which
  // would schedule a save of the half-restored page back over the draft that
  // is still being read from. Ignore our own writes.
  let _restoringDraft = false;
  function scheduleDraftSave() {
    if (_restoringDraft) return;
    clearTimeout(_draftSaveTimer);
    _draftSaveTimer = setTimeout(doDraftSave, DRAFT_DEBOUNCE_MS);
  }

  // Fills every currently-present field the draft has a value for. Any
  // captured field with no matching element yet (extra item/gold-silver rows
  // the officer hasn't clicked "+ Add Row" for again) is picked up the moment
  // that row appears — see armDraftTopUp — so restoring never requires
  // guessing how many rows to pre-create.
  let _topUpObserver = null, _topUpTimer = null;
  let _topUpRunning = false, _topUpAgain = false;
  function armDraftTopUp(draft) {
    if (_topUpObserver) _topUpObserver.disconnect();
    const handledKeys = new Set();
    // Restoring has to be SEQUENTIAL now that the overlay-driven controls
    // (mat-select / the five autocompletes) resolve asynchronously: firing
    // them all at once meant several inputs grabbing focus and opening
    // option panels simultaneously, so they clobbered each other and the
    // wrong panel got read. Filling in DOM order also happens to satisfy the
    // Country → Airport cascade for free, since the country control appears
    // first in the markup. The re-entrancy latch coalesces the burst of
    // MutationObserver callbacks that our own filling inevitably triggers.
    const tryFill = async () => {
      if (_topUpRunning) { _topUpAgain = true; return; }
      _topUpRunning = true;
      _restoringDraft = true;
      try {
        do {
          _topUpAgain = false;
          const counters = {};
          const els = [...document.querySelectorAll(FIELD_QUERY)].filter(isDraftableField);
          for (const el of els) {
            // Recompute for every element, handled or not — computeDraftKey's
            // duplicate counter only lines up with the saved keys if the walk
            // covers the same elements in the same order it did on save.
            const k = computeDraftKey(el, counters);
            if (handledKeys.has(k)) continue;
            const target = draft.values[k];
            if (target === undefined) continue;
            const cur = captureFieldValue(el);
            const isEmpty = cur.__kind === 'checkbox' ? cur.value === false : !String(cur.value || '').trim();
            handledKeys.add(k);
            // Never overwrite something the officer has since typed themselves —
            // only ever fill a field that's still blank/unchecked.
            if (isEmpty) await applyValueByElementType(el, target);
          }
        } while (_topUpAgain);
      } finally { _topUpRunning = false; _restoringDraft = false; }
    };
    tryFill();
    _topUpObserver = new MutationObserver(tryFill);
    _topUpObserver.observe(document.body, { childList: true, subtree: true });
    clearTimeout(_topUpTimer);
    _topUpTimer = setTimeout(() => { _topUpObserver?.disconnect(); _topUpObserver = null; }, 10 * 60 * 1000);
  }

  function restoreDraft(key) {
    const draft = st.drafts[key];
    if (!draft) return;
    armDraftTopUp(draft);
    const total = Object.keys(draft.values).length;
    toast(`📝 Draft restored for ${key === '__untitled__' ? '(no passport typed yet)' : key} — filling ${total} field(s) as they appear on the page. If a popup (e.g. Gold/Silver eligibility) reopens because a checkbox got restored, its previous answers are pre-filled — just confirm it once.`, 'warn');
  }

  // Fully hands-off by design: the moment a passport number (scanned or
  // hand-typed) matches an existing draft, it restores immediately — no
  // Restore button, no popup to click through. restoreDraft()'s own toast is
  // the only feedback, and armDraftTopUp() keeps watching the page afterward
  // so fields on OTHER tabs/steps of the form (Angular SPA route changes,
  // e.g. Travel Details / Item Declaration) get filled the instant they
  // render too, with no further action needed per tab.
  let _lastAutoRestoredKey = null;
  function checkDraftMatchAndToast(passportNo) {
    if (!passportNo || !isAtithiPage()) return;
    purgeExpiredDrafts();
    if (st.drafts[passportNo] && _lastAutoRestoredKey !== passportNo) {
      _lastAutoRestoredKey = passportNo;
      restoreDraft(passportNo);
    }
  }

  // ── COPS REVENUE REPORT TEMPLATE (mirrors dcrExcel.ts REVENUE_HEADERS exactly) ─
  // 'Duty in Foreign Currency' + 'FX Currency' are appended (not inserted) so the
  // original 25 headers stay in their exact mirrored order — delete them with the
  // ✕ button if the real Excel format doesn't want them, or reposition manually.
  const COPS_TEMPLATE = [
    'SR.NO.', 'BR NO.', 'Offline', 'OS No.', 'Item Description',
    'Total Dutiable Value', 'GOLD Weight(gms)',
    'Baggage duty', 'Liquor duty', 'Cigarette duty', 'SW SC',
    'Gold Duty (BCD)', 'Gold Duty (C)', 'Silver Duty (C)',
    'SWS on Gold', 'AIDC Gold/Silver', 'SWS on Silver', 'AIDC on Liquor',
    'Redemption Fine', 'Re-export Fine', 'Personal Penalty',
    'Other Charges', 'Fuel Duty', 'Total Duty', 'Flight No',
    'Duty in Foreign Currency', 'FX Currency'
  ];
  const COPS_NUMERIC = new Set([
    'Total Dutiable Value','GOLD Weight(gms)','Baggage duty','Liquor duty',
    'Cigarette duty','SW SC','Gold Duty (BCD)','Gold Duty (C)','Silver Duty (C)',
    'SWS on Gold','AIDC Gold/Silver','SWS on Silver','AIDC on Liquor',
    'Redemption Fine','Re-export Fine','Personal Penalty','Other Charges',
    'Fuel Duty','Total Duty','Duty in Foreign Currency'
  ]);
  // Columns pre-flagged as foreign-currency (site shows gold/silver concessional
  // duty in USD/GBP/etc., not INR) — highlighted amber in the Excel export as a
  // "convert using today's rate" flag for whoever prepares the report.
  const COPS_FX_DEFAULT = new Set(['Duty in Foreign Currency', 'FX Currency']);

  // ── EXPORT ─────────────────────────────────────────────────────
  function escapeHtml(s) {
    return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  }

  // Builds an Excel-openable HTML table (.xls) with real cell background color —
  // plain .csv can't carry color, so foreign-currency columns (gold/silver
  // concessional duty shown in USD/GBP etc. by the site) are highlighted amber
  // here so whoever prepares the report knows to convert them to INR.
  function exportXLS(shift) {
    if (!shift?.rows?.length) { toast('No data to export.'); return; }
    const dataCols = st.columns.filter(c => c.label !== 'SR.NO.');
    const headers = ['SR.NO.', ...dataCols.map(c => c.label)];
    const fxCols = new Set(dataCols.map((c, i) => c.isForeignCurrency ? i + 1 : -1).filter(i => i >= 0));
    const fx = (i, extra = '') => fxCols.has(i) ? `background:#fde68a;${extra}` : extra;

    let rows = '<tr>' + headers.map((h, i) =>
      `<th style="${fx(i, 'font-weight:700;border:1px solid #999;padding:4px 8px;')}">${escapeHtml(h)}</th>`
    ).join('') + '</tr>';

    shift.rows.forEach((r, idx) => {
      const cells = [idx + 1, ...dataCols.map(c => r[c.label] || '')];
      rows += '<tr>' + cells.map((v, i) =>
        `<td style="${fx(i, 'border:1px solid #ccc;padding:4px 8px;')}">${escapeHtml(v)}</td>`
      ).join('') + '</tr>';
    });

    const totals = ['TOTAL', ...dataCols.map(c => {
      if (!COPS_NUMERIC.has(c.label)) return '';
      const sum = shift.rows.reduce((s, r) => s + (parseFloat(r[c.label]) || 0), 0);
      return sum ? sum.toFixed(2).replace(/\.00$/, '') : '';
    })];
    rows += '<tr>' + totals.map((v, i) =>
      `<td style="${fx(i, 'border-top:2px solid #000;font-weight:700;padding:4px 8px;')}">${escapeHtml(v)}</td>`
    ).join('') + '</tr>';

    const fxNote = fxCols.size
      ? `<tr><td colspan="${headers.length}" style="background:#fde68a;color:#7c2d12;font-weight:700;padding:6px 8px;">` +
        `⚠ Amber columns are in FOREIGN CURRENCY — convert to INR using the day's exchange rate before finalizing the report.</td></tr>`
      : '';

    const html = `<html xmlns:x="urn:schemas-microsoft-com:office:excel"><head><meta charset="UTF-8"></head>` +
      `<body><table border="1" style="border-collapse:collapse;font-family:Calibri,sans-serif;font-size:11pt;">${fxNote}${rows}</table></body></html>`;

    const date = new Date().toISOString().slice(0, 10);
    const shift_ = shift.name.toUpperCase().includes('NIGHT') ? 'N' : 'D';
    const fname = `${date}(${shift_}) ${shift.name.toUpperCase()} REVENUE REPORT.xls`;
    const a = Object.assign(document.createElement('a'), {
      href: URL.createObjectURL(new Blob([html], { type: 'application/vnd.ms-excel' })),
      download: fname
    });
    a.click();
    toast(`Downloaded (Excel, colored): ${fname}`);
  }

  // ── TOAST ──────────────────────────────────────────────────────
  function toast(msg, kind = 'ok') {
    const t = document.createElement('div');
    const bg = kind === 'warn' ? '#dc2626' : '#22c55e';
    Object.assign(t.style, {
      position: 'fixed', bottom: '80px', right: '20px', background: bg,
      color: '#fff', padding: '8px 16px', borderRadius: '8px', fontSize: '13px',
      fontFamily: 'sans-serif', zIndex: '2147483647', boxShadow: '0 4px 12px rgba(0,0,0,.3)',
      transition: 'opacity .4s', maxWidth: '340px', lineHeight: '1.4'
    });
    t.textContent = msg;
    document.body.appendChild(t);
    const dur = kind === 'warn' ? 5000 : 2500;
    setTimeout(() => { t.style.opacity = '0'; setTimeout(() => t.remove(), 400); }, dur);
  }

  // ── PANEL ──────────────────────────────────────────────────────
  let panel, toggleBtn, mapping = null;
  // Collapsed-by-default toggles — the panel shows a one-line summary + an
  // "Edit ▾" button for anything that's already configured/working; the
  // full editable list only appears once the officer asks for it.
  let draftsExpanded = false;
  let syncConnected = false;
  let defaultsExpanded = false;
  let columnsExpanded = false;
  let dutyRatesExpanded = false;
  let lastAutoMapResult = null; // { mapped, unresolved } from the most recent Auto-map click/attempt

  function buildUI() {
    // Toggle button
    toggleBtn = document.createElement('div');
    toggleBtn.id = '__brc_toggle';
    Object.assign(toggleBtn.style, {
      position: 'fixed', bottom: '20px', right: '20px', width: '52px', height: '52px',
      background: 'linear-gradient(135deg,#6366f1,#8b5cf6)', borderRadius: '50%',
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      cursor: 'pointer', zIndex: '2147483646', boxShadow: '0 4px 16px rgba(99,102,241,.5)',
      fontSize: '22px', userSelect: 'none', transition: 'transform .2s'
    });
    toggleBtn.title = 'Atithi Helper';
    toggleBtn.textContent = '📋';
    toggleBtn.onmouseenter = () => toggleBtn.style.transform = 'scale(1.1)';
    toggleBtn.onmouseleave = () => toggleBtn.style.transform = 'scale(1)';
    toggleBtn.onclick = () => { panel.style.display = panel.style.display === 'none' ? 'flex' : 'none'; render(); };

    // Panel
    panel = document.createElement('div');
    panel.id = '__brc_panel';
    Object.assign(panel.style, {
      position: 'fixed', top: '0', right: '0', width: '320px', height: '100vh',
      background: '#0f172a', color: '#e2e8f0', display: 'none', flexDirection: 'column',
      zIndex: '2147483645', fontFamily: 'system-ui,sans-serif', fontSize: '13px',
      boxShadow: '-4px 0 24px rgba(0,0,0,.5)', overflowY: 'auto'
    });

    document.body.appendChild(toggleBtn);
    document.body.appendChild(panel);
    render();
  }

  function el(tag, props = {}, ...children) {
    const e = document.createElement(tag);
    Object.assign(e, props);
    if (props.style && typeof props.style === 'object') Object.assign(e.style, props.style);
    children.forEach(c => c && e.appendChild(typeof c === 'string' ? document.createTextNode(c) : c));
    return e;
  }

  function btn(label, onClick, bg = '#6366f1') {
    const b = document.createElement('button');
    b.textContent = label;
    Object.assign(b.style, {
      background: bg, color: '#fff', border: 'none', borderRadius: '6px',
      padding: '6px 12px', cursor: 'pointer', fontSize: '12px', fontWeight: '600',
      margin: '2px', transition: 'opacity .2s'
    });
    b.onmouseenter = () => b.style.opacity = '.8';
    b.onmouseleave = () => b.style.opacity = '1';
    b.onclick = onClick;
    return b;
  }

  function section(title, content) {
    const wrap = document.createElement('div');
    Object.assign(wrap.style, { borderBottom: '1px solid #1e293b', padding: '12px' });
    const h = document.createElement('div');
    Object.assign(h.style, { fontWeight: '700', fontSize: '11px', textTransform: 'uppercase', letterSpacing: '1px', color: '#94a3b8', marginBottom: '8px' });
    h.textContent = title;
    wrap.appendChild(h);
    wrap.appendChild(content);
    return wrap;
  }

  function inp(placeholder, val = '') {
    const i = document.createElement('input');
    i.placeholder = placeholder; i.value = val;
    Object.assign(i.style, {
      background: '#1e293b', border: '1px solid #334155', color: '#e2e8f0',
      borderRadius: '6px', padding: '6px 10px', width: '100%', boxSizing: 'border-box',
      fontSize: '12px', marginBottom: '6px'
    });
    return i;
  }

  function render() {
    if (!panel) return;

    // Draft-count badge on the 📋 toggle button — visible even with the panel
    // closed. Without this, after a crash/reload (bookmarklet re-inject or a
    // fresh extension load) there was no signal that recoverable drafts
    // existed until the officer thought to open the panel and check; on a
    // site that crashes/reloads often, that's exactly when it's easiest to
    // forget and just retype from scratch instead of hitting Restore.
    purgeExpiredDrafts();
    const pendingDraftCount = Object.keys(st.drafts).length;
    if (toggleBtn) {
      let badge = toggleBtn.querySelector('#__brc_badge');
      if (pendingDraftCount) {
        if (!badge) {
          badge = document.createElement('div');
          badge.id = '__brc_badge';
          Object.assign(badge.style, {
            position: 'absolute', top: '-4px', right: '-4px', minWidth: '18px', height: '18px',
            borderRadius: '9px', background: '#ef4444', color: '#fff', fontSize: '11px',
            fontWeight: '700', display: 'flex', alignItems: 'center', justifyContent: 'center',
            padding: '0 4px', boxShadow: '0 0 0 2px #0f172a'
          });
          toggleBtn.appendChild(badge);
        }
        badge.textContent = String(pendingDraftCount);
      } else if (badge) {
        badge.remove();
      }
    }

    panel.innerHTML = '';

    // Header
    const hdr = document.createElement('div');
    Object.assign(hdr.style, { padding: '14px 12px', background: '#1e293b', display: 'flex', justifyContent: 'space-between', alignItems: 'center' });
    const title = document.createElement('span');
    title.textContent = '📋 Atithi Helper';
    title.title = 'Build ' + BUILD;
    Object.assign(title.style, { fontWeight: '700', fontSize: '14px' });
    const buildTag = document.createElement('span');
    buildTag.textContent = BUILD;
    Object.assign(buildTag.style, { fontSize: '10px', opacity: '.55', marginLeft: '6px', fontWeight: '400' });
    title.appendChild(buildTag);
    const closeX = document.createElement('span');
    closeX.textContent = '✕'; closeX.style.cursor = 'pointer'; closeX.style.color = '#64748b';
    closeX.onclick = () => { panel.style.display = 'none'; };
    hdr.appendChild(title); hdr.appendChild(closeX);
    panel.appendChild(hdr);

    // DRAFTS — restore now happens automatically the instant a passport
    // number matches (see checkDraftMatchAndToast), so this is just a manual
    // fallback: collapsed to "Drafts (N)" + one toggle, in case the officer
    // wants to browse or restore one by hand instead of re-typing/re-scanning
    // the passport number. Shows passport numbers only, nothing else.
    const draftKeys = Object.keys(st.drafts);
    if (draftKeys.length) {
      const draftWrap = document.createElement('div');
      Object.assign(draftWrap.style, { borderBottom: '1px solid #1e293b', padding: '12px' });
      const draftBtn = btn(draftsExpanded ? `Hide Drafts (${draftKeys.length}) ▴` : `Drafts (${draftKeys.length}) ▾`,
        () => { draftsExpanded = !draftsExpanded; render(); }, '#334155');
      draftBtn.style.width = '100%';
      draftWrap.appendChild(draftBtn);

      if (draftsExpanded) {
        const list = document.createElement('div');
        Object.assign(list.style, { display: 'flex', flexDirection: 'column', gap: '6px', marginTop: '8px' });
        draftKeys.sort((a, b) => st.drafts[b].savedAt - st.drafts[a].savedAt).forEach(k => {
          const d = st.drafts[k];
          const mins = Math.max(1, Math.round((Date.now() - d.savedAt) / 60000));
          const row = document.createElement('div');
          Object.assign(row.style, { display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: '#0f172a', borderRadius: '6px', padding: '6px 8px' });
          const lbl = document.createElement('span');
          lbl.style.fontSize = '11px'; lbl.style.color = '#e2e8f0';
          lbl.textContent = `${k === '__untitled__' ? '(no passport yet)' : k} · ${mins}m ago`;
          row.appendChild(lbl);
          const actions = document.createElement('div');
          actions.appendChild(btn('Restore', () => { restoreDraft(k); }, '#22c55e'));
          actions.appendChild(btn('✕', () => {
            delete st.drafts[k];
            _suppressDraftKey = k;
            clearTimeout(_draftSaveTimer);   // a save already in flight would undo this
            save(); render();
          }, '#ef4444'));
          row.appendChild(actions);
          list.appendChild(row);
        });
        draftWrap.appendChild(list);
      }
      panel.appendChild(draftWrap);
    }

    // SHARED-FOLDER SYNC — one bare button, like everything else. Connects
    // once per browser via a native folder picker; after that this is just
    // a manual "pull now" in case the officer wants to force a check rather
    // than wait for the automatic pulls (on load / regaining tab focus).
    const syncWrap = document.createElement('div');
    Object.assign(syncWrap.style, { borderBottom: '1px solid #1e293b', padding: '12px' });
    const syncBtn = btn(syncConnected ? '🔗 Sync Now' : '🔗 Connect Shared Folder', async () => {
      if (syncConnected) { await pullSharedFolderSync(); await pushSharedFolderSync(); toast('🔗 Synced ✓'); }
      else { await connectSharedFolder(); syncConnected = !!(await ensureSyncDirHandle()); render(); }
    }, syncConnected ? '#334155' : '#f59e0b');
    syncBtn.style.width = '100%';
    syncWrap.appendChild(syncBtn);
    panel.appendChild(syncWrap);

    // MANUAL AUTO-MAP TRIGGER — the background attempts (on load, and on
    // navigating into a new tab) are a convenience, but the officer may
    // prefer to stand on the exact intended page/tab and trigger it
    // deliberately rather than let it re-run ambiently while browsing
    // between tabs — especially now that duplicate field names across tabs
    // are handled by preferring whichever match is visible right now.
    const autoMapWrap = document.createElement('div');
    Object.assign(autoMapWrap.style, { borderBottom: '1px solid #1e293b', padding: '12px' });
    const autoMapBtn = btn('🔎 Auto-map Fields Now', () => runAutoMap(), '#7c3aed');
    autoMapBtn.style.width = '100%';
    autoMapWrap.appendChild(autoMapBtn);
    panel.appendChild(autoMapWrap);

    // One row for a single field's manual-map fallback — only ever used
    // inside the "⚠ Needs Manual Mapping" block below, for whatever auto-map
    // couldn't find.
    function mapRow(key, label, targets, autoFlags, mapType, mapKeyProp, color) {
      const row = document.createElement('div');
      row.style.display = 'flex'; row.style.alignItems = 'center'; row.style.gap = '6px'; row.style.marginBottom = '4px';
      const status = document.createElement('span');
      status.style.fontSize = '10px'; status.style.color = '#475569';
      status.textContent = '○';
      const lbl = document.createElement('span');
      lbl.style.flex = '1'; lbl.style.fontSize = '12px';
      lbl.textContent = label;
      const mapBtn = btn('Map', () => {
        mapping = { type: mapType, [mapKeyProp]: key };
        panel.style.pointerEvents = 'none';
        document.body.style.cursor = 'crosshair';
        toast(`Click the ${label} field on the website…`);
      }, color);
      Object.assign(mapBtn.style, { padding: '3px 8px', fontSize: '11px' });
      row.appendChild(status); row.appendChild(lbl); row.appendChild(mapBtn);
      return row;
    }

    // FIELD MAPPING / SAVE BUTTON — fully silent in the normal case: fields
    // and the Save/Submit button auto-map themselves in the background
    // (scheduleAutoMapAttempts / runAutoMap), no section shown at all here.
    // This block only appears when auto-map genuinely couldn't find
    // something, as a one-off manual fallback — not a permanent section.
    if (lastAutoMapResult && isAtithiPage()) {
      // Only ever nag about fields we actually expect to find a real site
      // field for (MRZ_AUTO_SELECTORS/BP_AUTO_SELECTORS) — fields like
      // surname/givenNames/personalNumber or the boarding pass's
      // compartment/sequence/paxStatus have NO known site field at all by
      // design, and leaving them unmapped is completely fine; the tool
      // fills whatever IS mapped and silently skips the rest, always.
      const stillUnresolvedMrz = Object.keys(MRZ_AUTO_SELECTORS).filter(k => !st.mrzTargets?.[k]);
      const stillUnresolvedBp = Object.keys(BP_AUTO_SELECTORS).filter(k => !st.bpTargets?.[k]);
      const needsSaveBtn = !st.saveBtn;
      if (stillUnresolvedMrz.length || stillUnresolvedBp.length || needsSaveBtn) {
        const warnContent = document.createElement('div');
        const note = document.createElement('div');
        Object.assign(note.style, { fontSize: '11px', color: '#f59e0b', marginBottom: '8px', lineHeight: '1.5' });
        note.textContent = "Couldn't auto-detect these on the page — map manually:";
        warnContent.appendChild(note);
        stillUnresolvedMrz.forEach(key => warnContent.appendChild(mapRow(key, MRZ_LABELS[key], st.mrzTargets, st.mrzTargetsAuto, 'mrzTarget', 'mrzKey', '#22c55e')));
        stillUnresolvedBp.forEach(key => warnContent.appendChild(mapRow(key, BP_LABELS[key], st.bpTargets, st.bpTargetsAuto, 'bpTarget', 'bpKey', '#f59e0b')));
        if (needsSaveBtn) {
          const row = document.createElement('div');
          row.style.display = 'flex'; row.style.alignItems = 'center'; row.style.gap = '6px'; row.style.marginTop = '4px';
          const lbl = document.createElement('span'); lbl.style.flex = '1'; lbl.style.fontSize = '12px'; lbl.textContent = 'Save/Submit button';
          row.appendChild(lbl);
          row.appendChild(btn('Map', () => startMapping('saveBtn', null), '#f59e0b'));
          warnContent.appendChild(row);
        }
        panel.appendChild(section('⚠ Needs Manual Mapping', warnContent));
      }
    }

    // DEFAULT VALUES — collapsed to one button; no summary text underneath.
    const defWrap = document.createElement('div');
    Object.assign(defWrap.style, { borderBottom: '1px solid #1e293b', padding: '12px' });
    const defTopRow = document.createElement('div');
    defTopRow.style.display = 'flex'; defTopRow.style.gap = '6px';
    const defBtn = btn(defaultsExpanded ? 'Hide Default Values ▴' : 'Edit Default Values ▾', () => { defaultsExpanded = !defaultsExpanded; render(); }, '#334155');
    defBtn.style.flex = '1';
    defTopRow.appendChild(defBtn);
    if (defaultsExpanded && st.defaultTargets?.some(t => t.selector)) {
      defTopRow.appendChild(btn('⚡ Fill Now', async () => {
        const n = await fillAllDefaults();
        toast(n ? `Filled ${n} default field(s) ✓` : 'No default fields mapped yet.');
      }, '#7c3aed'));
    }
    defWrap.appendChild(defTopRow);
    const defContent = defWrap;

    if (defaultsExpanded) {
      const fields = discoverFields();
      // A <select> of the page's own labelled controls. Picking from a list
      // beats the crosshair for anything the page already names, and it is the
      // only way to reach a field inside a collapsed accordion.
      const fieldPicker = (current, onPick, placeholder) => {
        const sel = document.createElement('select');
        Object.assign(sel.style, {
          flex: '1', minWidth: '0', background: '#0f172a', color: '#e2e8f0',
          border: '1px solid #334155', borderRadius: '6px', padding: '6px', fontSize: '11px'
        });
        const none = document.createElement('option');
        none.value = ''; none.textContent = placeholder;
        sel.appendChild(none);
        let found = false;
        fields.forEach(f => {
          const o = document.createElement('option');
          o.value = f.selector; o.textContent = f.label;
          if (f.selector === current) { o.selected = true; found = true; }
          sel.appendChild(o);
        });
        // A selector mapped by crosshair, or saved against a page that isn't
        // open right now, still has to be visible and keepable.
        if (current && !found) {
          const o = document.createElement('option');
          o.value = current; o.textContent = '(mapped) ' + current.slice(0, 40);
          o.selected = true; sel.appendChild(o);
        }
        sel.onchange = () => { onPick(sel.value || null); save(); render(); };
        return sel;
      };

      (st.defaultTargets || []).forEach((t, i) => {
        const row = document.createElement('div');
        Object.assign(row.style, { background: '#1e293b', borderRadius: '8px', padding: '8px', marginTop: '6px' });

        // Row 1 — name + what kind of rule + delete
        const top = document.createElement('div');
        top.style.display = 'flex'; top.style.gap = '4px'; top.style.marginBottom = '4px';
        const lblIn = inp('Rule name', t.label);
        lblIn.style.marginBottom = '0'; lblIn.style.flex = '2';
        lblIn.oninput = () => { t.label = lblIn.value; save(); };
        const modeSel = document.createElement('select');
        Object.assign(modeSel.style, {
          background: '#0f172a', color: '#e2e8f0', border: '1px solid #334155',
          borderRadius: '6px', padding: '6px', fontSize: '11px'
        });
        [['fixed', 'Fixed value'], ['copy', 'Copy from field']].forEach(([v, txt]) => {
          const o = document.createElement('option');
          o.value = v; o.textContent = txt;
          if ((t.mode || 'fixed') === v) o.selected = true;
          modeSel.appendChild(o);
        });
        modeSel.onchange = () => { t.mode = modeSel.value; save(); render(); };
        const del = document.createElement('span');
        del.textContent = '✕'; del.style.cursor = 'pointer'; del.style.color = '#ef4444'; del.style.padding = '0 4px';
        del.title = 'Delete this rule';
        del.onclick = () => { st.defaultTargets.splice(i, 1); save(); render(); };
        top.appendChild(lblIn); top.appendChild(modeSel); top.appendChild(del);
        row.appendChild(top);

        // Row 2 — where the value comes from
        const srcRow = document.createElement('div');
        srcRow.style.display = 'flex'; srcRow.style.alignItems = 'center';
        srcRow.style.gap = '4px'; srcRow.style.marginBottom = '4px';
        const srcLbl = document.createElement('span');
        srcLbl.textContent = 'Value:'; srcLbl.style.fontSize = '11px';
        srcLbl.style.color = '#94a3b8'; srcLbl.style.minWidth = '38px';
        srcRow.appendChild(srcLbl);
        if ((t.mode || 'fixed') === 'copy') {
          srcRow.appendChild(fieldPicker(t.sourceSelector, v => {
            t.sourceSelector = v;
            t.sourceLabel = (fields.find(f => f.selector === v) || {}).label || '';
          }, '— copy from which field? —'));
        } else {
          const valIn = inp('Value to fill (works for dropdowns too)', t.value);
          valIn.style.marginBottom = '0'; valIn.style.flex = '1';
          valIn.oninput = () => { t.value = valIn.value; save(); };
          srcRow.appendChild(valIn);
        }
        row.appendChild(srcRow);

        // Row 3 — which field it goes into
        const tgtRow = document.createElement('div');
        tgtRow.style.display = 'flex'; tgtRow.style.alignItems = 'center';
        tgtRow.style.gap = '4px';
        const tgtLbl = document.createElement('span');
        tgtLbl.textContent = 'Into:'; tgtLbl.style.fontSize = '11px';
        tgtLbl.style.color = '#94a3b8'; tgtLbl.style.minWidth = '38px';
        tgtRow.appendChild(tgtLbl);
        tgtRow.appendChild(fieldPicker(t.selector, v => { t.selector = v; }, '— which field? —'));
        tgtRow.appendChild(btn('◎', () => {
          mapping = { type: 'defaultTarget', defId: t.id };
          panel.style.pointerEvents = 'none';
          document.body.style.cursor = 'crosshair';
          toast(`Click the ${t.label || 'field'} on the website…`);
        }, '#0ea5e9'));
        if (t.selector) tgtRow.appendChild(btn('Test', () => testField({ selector: t.selector }), '#334155'));
        row.appendChild(tgtRow);

        // What this rule will actually write, right now — no guessing.
        const preview = document.createElement('div');
        preview.style.fontSize = '10px'; preview.style.marginTop = '4px';
        const v = _ruleValue(t);
        const ready = t.selector && v !== '';
        preview.style.color = ready ? '#22c55e' : '#64748b';
        preview.textContent = !t.selector ? '○ no target field chosen'
          : v === '' ? ((t.mode === 'copy') ? '○ source field is empty right now' : '○ no value set')
          : '● will fill: ' + v;
        row.appendChild(preview);

        defContent.appendChild(row);
      });

      const addDefRow = document.createElement('div');
      addDefRow.style.display = 'flex'; addDefRow.style.gap = '6px'; addDefRow.style.margin = '6px 0';
      addDefRow.appendChild(btn('+ Fixed value', () => {
        st.defaultTargets.push({ id: Date.now().toString(), label: 'New rule', mode: 'fixed', value: '', selector: null });
        save(); render();
      }, '#22c55e'));
      addDefRow.appendChild(btn('+ Copy from field', () => {
        st.defaultTargets.push({ id: Date.now().toString(), label: 'New rule', mode: 'copy', sourceSelector: null, selector: null });
        save(); render();
      }, '#0ea5e9'));
      defContent.appendChild(addDefRow);
    }
    panel.appendChild(defWrap);

    // COLUMN MAPPING — collapsed to one button; no summary text underneath.
    const colWrap = document.createElement('div');
    Object.assign(colWrap.style, { borderBottom: '1px solid #1e293b', padding: '12px' });
    const colContent = colWrap;

    if (!st.columns.length) {
      const tplBtn = btn('⚡ Load COPS Revenue Template', () => {
        st.columns = COPS_TEMPLATE.map((label, i) => ({
          id: (Date.now() + i).toString(), label,
          selector: null, mrzField: null,
          isForeignCurrency: COPS_FX_DEFAULT.has(label)
        }));
        save(); render();
        toast('COPS template loaded — now map each field on the website');
      }, '#7c3aed');
      tplBtn.style.width = '100%'; tplBtn.style.margin = '0 0 8px 0';
      colContent.appendChild(tplBtn);
      columnsExpanded = true; // nothing to hide yet — show the add-custom-column control directly
    } else {
      const colBtn = btn(columnsExpanded ? 'Hide Column Mapping ▴' : 'Edit Column Mapping ▾', () => { columnsExpanded = !columnsExpanded; render(); }, '#334155');
      colBtn.style.width = '100%';
      colContent.appendChild(colBtn);
    }

    if (columnsExpanded) {
      st.columns.forEach((col, i) => {
        const row = document.createElement('div');
        Object.assign(row.style, { background: '#1e293b', borderRadius: '8px', padding: '8px', marginBottom: '6px' });

        // Label row
        const top = document.createElement('div');
        top.style.display = 'flex'; top.style.justifyContent = 'space-between'; top.style.alignItems = 'center';
        const lbl = document.createElement('span');
        lbl.textContent = col.label; lbl.style.fontWeight = '600';
        if (col.isForeignCurrency) lbl.style.color = '#f59e0b';
        const del = document.createElement('span');
        del.textContent = '✕'; del.style.cursor = 'pointer'; del.style.color = '#ef4444'; del.style.fontSize = '14px';
        del.onclick = () => { st.columns.splice(i, 1); save(); render(); };
        top.appendChild(lbl); top.appendChild(del);
        row.appendChild(top);

        // Field mapping
        const fRow = document.createElement('div');
        fRow.style.display = 'flex'; fRow.style.alignItems = 'center'; fRow.style.marginTop = '6px'; fRow.style.gap = '4px';
        const fieldStatus = document.createElement('span');
        fieldStatus.style.flex = '1'; fieldStatus.style.fontSize = '11px';
        if (col.selector) {
          fieldStatus.style.color = col.isTable ? '#f59e0b' : '#22c55e';
          fieldStatus.textContent = col.isTable
            ? `📊 Table col ${col.colIndex + 1} (all rows)`
            : `● Mapped (${col.selectorHint || 'CSS'})`;
        } else {
          fieldStatus.style.color = '#64748b';
          fieldStatus.textContent = '○ No field mapped';
        }
        fRow.appendChild(fieldStatus);
        fRow.appendChild(btn('Map', () => startMapping('field', col.id), '#0ea5e9'));
        if (col.selector) fRow.appendChild(btn('Test', () => testField(col), '#334155'));
        fRow.appendChild(btn('💱 FX', () => { col.isForeignCurrency = !col.isForeignCurrency; save(); render(); },
          col.isForeignCurrency ? '#f59e0b' : '#334155'));
        row.appendChild(fRow);
        if (col.isForeignCurrency) {
          const fxNote = document.createElement('div');
          Object.assign(fxNote.style, { fontSize: '10px', color: '#f59e0b', marginTop: '3px' });
          fxNote.textContent = '💱 Marked foreign-currency — highlighted amber in the Excel export';
          row.appendChild(fxNote);
        }

        // MRZ binding
        const mRow = document.createElement('div');
        mRow.style.display = 'flex'; mRow.style.alignItems = 'center'; mRow.style.marginTop = '4px'; mRow.style.gap = '4px';
        const sel = document.createElement('select');
        Object.assign(sel.style, { flex: '1', background: '#0f172a', color: '#e2e8f0', border: '1px solid #334155', borderRadius: '5px', padding: '4px', fontSize: '11px' });
        const none = document.createElement('option'); none.value = ''; none.textContent = 'No MRZ binding'; sel.appendChild(none);
        Object.entries(MRZ_LABELS).forEach(([k, l]) => {
          const o = document.createElement('option'); o.value = k; o.textContent = l;
          if (col.mrzField === k) o.selected = true;
          sel.appendChild(o);
        });
        sel.onchange = () => { col.mrzField = sel.value || null; save(); };
        mRow.appendChild(sel);
        row.appendChild(mRow);

        colContent.appendChild(row);
      });

      if (st.columns.length) {
        const resetBtn = btn('↺ Reset to COPS Template', () => {
          if (confirm('Replace all columns with COPS Revenue template?')) {
            st.columns = COPS_TEMPLATE.map((label, i) => ({
              id: (Date.now() + i).toString(), label, selector: null, mrzField: null,
              isForeignCurrency: COPS_FX_DEFAULT.has(label)
            }));
            save(); render();
            toast('COPS template loaded');
          }
        }, '#475569');
        resetBtn.style.fontSize = '11px'; resetBtn.style.marginBottom = '8px';
        colContent.appendChild(resetBtn);
      }

      // Add custom column
      const addRow = document.createElement('div');
      addRow.style.display = 'flex'; addRow.style.gap = '6px'; addRow.style.marginTop = '4px';
      const newColIn = inp('Add custom column…');
      newColIn.style.marginBottom = '0'; newColIn.style.flex = '1';
      addRow.appendChild(newColIn);
      addRow.appendChild(btn('+', () => {
        const name = newColIn.value.trim();
        if (!name) return;
        st.columns.push({ id: Date.now().toString(), label: name, selector: null, mrzField: null });
        save(); render();
      }, '#22c55e'));
      colContent.appendChild(addRow);
    }
    panel.appendChild(colWrap);

    // 3b. DUTY RATES — officer-editable % rates for the duty columns the real
    // site doesn't expose on its own (BCD/AIDC/etc.), used to auto-calc them
    // when the matching Column is left unmapped. "Total Duty" is deliberately
    // NEVER computed here — it always comes from whatever real site field is
    // mapped to that column, since the site shows it compulsorily and is the
    // safe/authoritative source for the grand total.
    const dutyWrap = document.createElement('div');
    Object.assign(dutyWrap.style, { borderBottom: '1px solid #1e293b', padding: '12px' });
    const dutyContent = dutyWrap;
    const dutyBtn = btn(dutyRatesExpanded ? 'Hide Duty Rates ▴' : 'Edit Duty Rates ▾', () => { dutyRatesExpanded = !dutyRatesExpanded; render(); }, '#334155');
    dutyBtn.style.width = '100%';
    dutyContent.appendChild(dutyBtn);

    if (dutyRatesExpanded) {
      Object.entries(DUTY_RATE_LABELS).forEach(([key, label]) => {
        const row = document.createElement('div');
        row.style.display = 'flex'; row.style.alignItems = 'center'; row.style.gap = '6px'; row.style.margin = '6px 0';
        const lbl = document.createElement('span');
        lbl.style.flex = '1'; lbl.style.fontSize = '11px'; lbl.style.color = '#cbd5e1'; lbl.textContent = label;
        const rateIn = inp('', String(st.dutyRates[key] ?? DUTY_RATE_DEFAULTS[key]));
        Object.assign(rateIn.style, { width: '56px', flex: 'none', marginBottom: '0', textAlign: 'right' });
        rateIn.type = 'number'; rateIn.step = '0.1';
        rateIn.oninput = () => { st.dutyRates[key] = parseFloat(rateIn.value) || 0; save(); };
        row.appendChild(lbl); row.appendChild(rateIn);
        dutyContent.appendChild(row);
      });
      const resetRatesBtn = btn('↺ Reset to defaults', () => {
        st.dutyRates = { ...DUTY_RATE_DEFAULTS }; save(); render();
      }, '#475569');
      resetRatesBtn.style.fontSize = '11px'; resetRatesBtn.style.marginTop = '4px';
      dutyContent.appendChild(resetRatesBtn);
    }
    panel.appendChild(dutyWrap);

    // ── DOWNLOAD ────────────────────────────────────────────────────
    // One button. Always exports the current 12-hour shift window (or the
    // one that just ended, within the grace period — see downloadShift()) —
    // no manual shift start/stop, no format choice.
    const dlWrap = document.createElement('div');
    Object.assign(dlWrap.style, { padding: '12px' });
    const dlBtn = btn('⬇ Download Excel', () => exportXLS(downloadShift()), '#f59e0b');
    Object.assign(dlBtn.style, { width: '100%', padding: '10px', fontSize: '13px' });
    dlWrap.appendChild(dlBtn);
    panel.appendChild(dlWrap);
  }

  // ── MAPPING MODE ───────────────────────────────────────────────
  let mapHighlight = null;

  function startMapping(type, colId) {
    mapping = { type, colId };
    panel.style.pointerEvents = 'none';
    document.body.style.cursor = 'crosshair';
    toast(type === 'saveBtn' ? 'Click the Save/Submit button…' : 'Click the field to map…');
  }

  function endMapping() {
    mapping = null;
    panel.style.pointerEvents = '';
    document.body.style.cursor = '';
    if (mapHighlight) { mapHighlight.style.outline = ''; mapHighlight = null; }
  }

  document.addEventListener('mouseover', (e) => {
    if (!mapping || e.target.closest('#__brc_panel') || e.target === toggleBtn) return;
    if (mapHighlight) mapHighlight.style.outline = '';
    mapHighlight = e.target;
    e.target.style.outline = '2px solid #6366f1';
  }, true);

  document.addEventListener('click', (e) => {
    if (!mapping) return;
    if (e.target.closest('#__brc_panel') || e.target === toggleBtn) return;
    e.preventDefault(); e.stopPropagation();
    const { sel, hint, isTable = false, colIndex = 0 } = getSelector(e.target);
    if (mapping.type === 'field') {
      const col = st.columns.find(c => c.id === mapping.colId);
      if (col) { col.selector = sel; col.selectorHint = hint; col.isTable = isTable; col.colIndex = colIndex; save(); }
    } else if (mapping.type === 'mrzTarget') {
      if (!st.mrzTargets) st.mrzTargets = {};
      st.mrzTargets[mapping.mrzKey] = sel;
      delete st.mrzTargetsAuto[mapping.mrzKey]; // officer just confirmed/overrode it by hand
      save();
    } else if (mapping.type === 'bpTarget') {
      if (!st.bpTargets) st.bpTargets = {};
      st.bpTargets[mapping.bpKey] = sel;
      delete st.bpTargetsAuto[mapping.bpKey]; // officer just confirmed/overrode it by hand
      save();
    } else if (mapping.type === 'defaultTarget') {
      const t = (st.defaultTargets || []).find(d => d.id === mapping.defId);
      if (t) { t.selector = sel; save(); }
    } else if (mapping.type === 'saveBtn') {
      st.saveBtn = { selector: sel };
      save();
      attachHook();
    }
    endMapping();
    render();
    toast('Mapped ✓');
  }, true);

  // ── DRAFT AUTOSAVE LISTENERS ─────────────────────────────────────
  // Fires on any typed/changed field on the page (not just mapped ones — the
  // officer may fill fields before the panel is even set up). Skipped while
  // actively click-mapping so a mapping click can't itself be mistaken for a
  // field edit. mat-select/radio/checkbox use 'change' (they don't fire
  // 'input' reliably); text inputs use 'input' for the debounce to feel live.
  document.addEventListener('input', (e) => {
    if (mapping || !isDraftableField(e.target)) return;
    scheduleDraftSave();
  }, true);
  document.addEventListener('change', (e) => {
    if (mapping || !isDraftableField(e.target)) return;
    scheduleDraftSave();
  }, true);
  // <mat-select> and <mat-autocomplete> commit their value by Angular output
  // (selectionChange), NOT by dispatching a DOM input/change event on the
  // control — so neither listener above ever fires for Gender, Classification
  // of Pax, Item Type, Currency or any of the five autocompletes, and picking
  // one of those was never making it into a draft. The officer's actual click
  // on the option does bubble to document, so key off that instead.
  document.addEventListener('click', (e) => {
    if (mapping) return;
    if (e.target.closest && e.target.closest('mat-option, [role="option"]')) scheduleDraftSave();
  }, true);
  purgeExpiredDrafts();

  // ── IMMEDIATE FLUSH ON RELOAD / NAVIGATE / TAB CLOSE ─────────────
  // The debounced autosave above waits 800ms after the last keystroke before
  // writing — fine while the officer keeps typing, but if a reload/close
  // happens inside that window the very last few characters typed wouldn't
  // be in localStorage yet. These two events fire for a reload (F5), closing
  // the tab, or navigating away, so flush synchronously right then instead of
  // waiting out the debounce. NOTE: this does NOT help against an actual
  // browser/tab crash or a Citrix session dying outright — no JS runs at all
  // in that case, which is exactly why the debounced autosave above exists
  // independently (it's already written continuously while typing, not only
  // at close time).
  document.addEventListener('visibilitychange', () => {
    if (document.visibilityState === 'hidden') { clearTimeout(_draftSaveTimer); doDraftSave(); }
    // Coming back to this tab/browser — pull whatever the OTHER browser
    // wrote to the shared folder in the meantime (e.g. it crashed there and
    // was reopened here). No-ops instantly if shared-folder sync was never
    // connected in this browser.
    else if (document.visibilityState === 'visible') { pullSharedFolderSync(); }
  });
  window.addEventListener('pagehide', () => { clearTimeout(_draftSaveTimer); doDraftSave(); });

  // ── DRAFT MATCH ON MANUALLY-TYPED PASSPORT NUMBER ────────────────
  // checkDraftMatchAndToast() already fires after an MRZ scan; this covers
  // the case where the officer types the passport number by hand instead of
  // scanning it (e.g. a damaged/unreadable MRZ) — same "in-progress draft
  // found" prompt either way.
  document.addEventListener('input', (e) => {
    const sel = _liveTarget('passportNo'); // works before Auto-map has ever been clicked
    if (!sel || mapping) return;
    try { if (e.target.matches(sel)) {
      clearTimeout(_passportTypedTimer);
      _passportTypedTimer = setTimeout(() => checkDraftMatchAndToast(e.target.value.trim()), 600);
    } } catch { }
  }, true);

  // ── SAVE HOOK ──────────────────────────────────────────────────
  let hookAttached = false;

  function attachHook() {
    if (hookAttached) return;
    hookAttached = true;
    document.addEventListener('click', (e) => {
      if (!st.saveBtn?.selector) return;
      try {
        const saveBtnEl = queryVisible(st.saveBtn.selector);
        if (saveBtnEl && (saveBtnEl === e.target || saveBtnEl.contains(e.target))) {
          const finalizedDraftKey = currentPassengerKey(); // capture before the site's own JS may reset the form
          setTimeout(() => {
            const shift = activeShift();
            const time = new Date().toLocaleTimeString();

            // BR-level columns: single fields (passport, flight no., BR no., etc.)
            // Item-level columns: table columns (item desc, value, duties, etc.)
            const brCols   = st.columns.filter(c => !c.isTable);
            const itemCols = st.columns.filter(c => c.isTable);

            // Read BR-level fields once — these repeat on every item row
            const brValues = { _time: time };
            brCols.forEach(c => { brValues[c.label] = readField(c.selector); });

            if (!itemCols.length) {
              // ── No table columns: simple one row per BR ───────────
              shift.rows.push(brValues);
              save();
              toast(`Row ${shift.rows.length} saved ✓`);
            } else {
              // ── COPS format: one Excel row per item ───────────────
              // BR with 3 items → 3 rows, BR fields repeated across all
              const refCol = itemCols[0];
              const table  = document.querySelector(refCol.selector);
              if (!table) { toast('⚠ Item table not found — re-map item columns'); return; }

              const itemRows = [...table.querySelectorAll('tr')]
                .filter(tr => tr.querySelector('td')); // data rows only, skip <th> headers

              if (!itemRows.length) { toast('⚠ No item rows found in table'); return; }

              let added = 0;
              itemRows.forEach(tr => {
                const row = { ...brValues }; // BR fields copied into every item row
                itemCols.forEach(c => {
                  const cell = tr.children[c.colIndex];
                  if (!cell) { row[c.label] = ''; return; }
                  const field = cell.querySelector('input, select, textarea');
                  if (field) {
                    row[c.label] = field.tagName === 'SELECT'
                      ? (field.options[field.selectedIndex]?.text || field.value || '')
                      : (field.value || '');
                  } else {
                    row[c.label] = cell.textContent.trim();
                  }
                });

                // Auto-calc duty columns the real site doesn't expose (BCD/AIDC/
                // etc.) using the officer-editable rates below — but ONLY fill a
                // column that's actually blank (i.e. not mapped to a real site
                // field). "Total Duty" is never in this computed set, so it's
                // always whatever the mapped site field shows, per design — the
                // site's own total is the authoritative safety net.
                const dutiableValue = parseFloat(row['Total Dutiable Value']) || 0;
                const autoDuty = computeAutoDuty(row['Item Description'], dutiableValue, st.dutyRates);
                Object.entries(autoDuty).forEach(([label, amount]) => {
                  if (st.columns.some(c => c.label === label) && !String(row[label] || '').trim()) {
                    row[label] = amount.toFixed(2);
                  }
                });

                // Skip blank trailing rows (all item columns empty)
                if (itemCols.some(c => (row[c.label] || '').trim())) {
                  shift.rows.push(row);
                  added++;
                }
              });

              save();
              toast(`${added} item row${added !== 1 ? 's' : ''} added ✓  (${shift.rows.length} total in shift)`);
            }
            // Finalized via the site's own Save button — no longer "in progress".
            if (st.drafts[finalizedDraftKey]) { delete st.drafts[finalizedDraftKey]; save(); }
            pushSharedFolderSync();
            render();
          }, 300);
        }
      } catch { }
    }, true);
  }

  if (st.saveBtn) attachHook();

  // ── GLOBAL MRZ SCANNER LISTENER ────────────────────────────────
  // Intercepts scanner keystrokes globally — no focus/click needed.
  // MRZ scanners type all 88 chars in < 200ms; human typing is always slower.
  let _mrzBuf = '', _mrzTimer = null, _lastKey = 0, _scanStart = 0;

  // Filling a date-widget field can fire synthetic keyboard events, which
  // bubble back to this same window listener, get appended to the still-full
  // buffer, re-match the scan pattern and re-enter the fill from inside
  // itself. That used to be blocked with a "fill in progress" flag that
  // ignored EVERY keydown while filling — but now that a fill legitimately
  // takes a second or two (the dropdowns wait on the site to render their
  // option lists), that flag silently swallowed the officer's very next scan:
  // scan the passport, immediately scan the boarding pass, and the boarding
  // pass was dropped on the floor.
  //
  // isTrusted is the precise discriminator instead — true only for events the
  // browser itself generated from real input (a barcode/MRZ scanner is a HID
  // keyboard, so its keystrokes are trusted), false for anything dispatched
  // from script. Re-entrancy is impossible, and no real scan is ever lost.
  //
  // Overlapping fills are then prevented by queueing rather than dropping:
  // two fills running at once would fight over focus, since each autocomplete
  // has to focus its input to open its option panel.
  let _fillChain = Promise.resolve();
  function _enqueueFill(run) {
    _fillChain = _fillChain.then(run).catch(() => { });
    return _fillChain;
  }

  // Single source of truth for "a passport got scanned" — fills MRZ-mapped
  // fields + MRZ-bound Excel columns + all Default Value fields together,
  // and warns (rather than silently trusting) a scan that fails checksum.
  // Overlay-driven controls (mat-autocomplete / mat-select) resolve
  // asynchronously — the site loads and filters its own option list before
  // anything can be clicked — so every fill below is awaited in sequence
  // rather than fired all at once. Sequencing also fixes a real dependency:
  // on the Travel Details section the Country control filters the Airport
  // control's options, so the airport can only be resolved after the country
  // has actually been committed.
  const BP_CASCADE_ORDER = ['fromCountry', 'from', 'to'];

  // Is this target one of the overlay-driven controls that can only be
  // resolved by waiting for the site to render its own option list?
  function _isOverlayTarget(sel) {
    try {
      const el = queryVisible(sel);
      return !!el && (el.tagName === 'MAT-SELECT' ||
        el.classList.contains('mat-mdc-autocomplete-trigger'));
    } catch { return false; }
  }

  // Targets where the scan only supplies PART of what the field is for, so an
  // existing value must never be clobbered. "Address Abroad" wants a full
  // address; the boarding pass can only give the origin country, which is a
  // useful starting point on a blank field but a bad trade for an address the
  // officer already typed (e.g. if they re-scan the boarding pass).
  // Seeded-from-a-related-fact rather than read off the document: right often
  // enough to save typing, not authoritative enough to overwrite the officer.
  const SOFT_FILL_KEYS = new Set(['fromCountryName', 'countriesVisited', 'mobileCountry']);

  // "What does this control currently show?" — works for plain inputs and for
  // <mat-select>, whose selection is rendered text rather than a .value.
  function _currentText(el) {
    if (!el) return '';
    if (el.tagName === 'MAT-SELECT') return matSelectText(el);
    return String(el.value || '').trim();
  }

  // The selectors to actually fill into for this scan: whatever the officer
  // has explicitly mapped, plus live detection for everything they haven't.
  //
  // Auto-map is a manual button, so on a fresh profile st.mrzTargets/bpTargets
  // are EMPTY — which meant clicking the bookmarklet and scanning straight
  // away filled nothing at all, and the officer had no way to know they were
  // expected to press "Auto-map Fields Now" first. Since the real site's
  // selectors are already known (MRZ_AUTO_SELECTORS / BP_AUTO_SELECTORS),
  // resolve the gaps at fill time instead. Deliberately read-only: nothing is
  // persisted and an existing mapping is never overwritten, so this does not
  // reintroduce the background auto-mapping that was removed.
  function _effectiveTargets(table) {
    const stored = (table === 'bp' ? st.bpTargets : st.mrzTargets) || {};
    const known = table === 'bp' ? BP_AUTO_SELECTORS : MRZ_AUTO_SELECTORS;
    const out = { ...stored };
    for (const key of Object.keys(known)) {
      // A stored mapping only wins while it still points at something real.
      // Selectors saved against an older version of the page (or against a
      // different page entirely) match nothing, and trusting them blindly
      // meant every write went nowhere while the run still reported success —
      // fields silently stayed empty with no error and no clue why. Anything
      // that no longer resolves is dropped so the live auto-detect can answer.
      if (out[key]) {
        let alive = false;
        try { alive = !!queryVisible(out[key]); } catch { }
        if (alive) continue;
        delete out[key];
      }
      try {
        const sel = autoDetectSelector(known[key]);
        if (sel) out[key] = sel;
      } catch { }
    }
    return out;
  }

  // Every selector we could reasonably use for a key, best first: whatever is
  // stored, then each built-in candidate. The single-selector approach gave up
  // the moment its first choice didn't take — which is how a whole passport
  // scan could come back with one field filled and no error. Falling through
  // the list means a field only fails after every known handle has been tried.
  function _candidatesFor(table, key, storedSel) {
    const known = (table === 'bp' ? BP_AUTO_SELECTORS : MRZ_AUTO_SELECTORS)[key] || [];
    return [...new Set([storedSel, ...known].filter(Boolean))];
  }

  // Write, then read the field back; if nothing landed, try the next handle.
  // Returns the selector that actually worked, or null.
  async function _fillFirstThatSticks(phase, table, key, value, storedSel) {
    const cands = _candidatesFor(table, key, storedSel);
    for (let i = 0; i < cands.length; i++) {
      const sel = cands[i];
      let exists = false;
      try { exists = !!queryVisible(sel); } catch { }
      if (!exists) continue;
      const ok = await _fillTraced(phase, sel, value, key);
      if (ok !== false) {
        // Remember a fallback that worked, so the next scan starts there
        // instead of re-walking a handle that is evidently dead on this page.
        if (sel !== storedSel) {
          const tbl = table === 'bp' ? st.bpTargets : st.mrzTargets;
          if (tbl) { tbl[key] = sel; save(); }
        }
        return sel;
      }
    }
    return null;
  }

  async function _fillTargets(targets, parsed, order, table) {
    let filled = 0;
    const unresolved = [];
    const entries = Object.entries(targets || {}).filter(([k, sel]) => {
      if (!sel || !parsed[k]) return false;
      if (SOFT_FILL_KEYS.has(k)) {
        const el = queryVisible(sel);
        // A <mat-select> has no .value in the DOM sense — its chosen option
        // lives in the rendered trigger text. Reading .value on one returns
        // undefined, i.e. "empty", which would have made every soft key
        // clobber an already-chosen dropdown: exactly what soft-fill exists
        // to prevent.
        if (el && _currentText(el)) return false;   // already has content — leave it
      }
      return true;
    });
    const cascade = order || [];

    // Pass 1 — everything that lands immediately (text fields, dates). Doing
    // these first means the form visibly populates the instant the scan ends,
    // instead of the officer watching a blank form while a dropdown waits on
    // the site to render its option list.
    for (const [k, sel] of entries) {
      if (_isOverlayTarget(sel)) continue;
      const used = await _fillFirstThatSticks('pass1-text', table, k, parsed[k], sel);
      if (used) filled++; else unresolved.push(k);
    }

    // Pass 2 — the overlay controls, strictly sequential (each needs focus and
    // its own panel) and with the cascade members last, in their declared
    // order, because the Country control filters the Airport control's list.
    const overlay = entries.filter(([, sel]) => _isOverlayTarget(sel))
      .sort((a, b) => {
        const ia = cascade.indexOf(a[0]), ib = cascade.indexOf(b[0]);
        return (ia === -1 ? -1 : ia) - (ib === -1 ? -1 : ib);
      });
    for (const [k, sel] of overlay) {
      const used = await _fillFirstThatSticks('pass2-dropdown', table, k, parsed[k], sel);
      if (used) filled++; else unresolved.push(k);
    }
    return { filled, unresolved };
  }

  function _warnUnresolved(keys, labels) {
    if (!keys.length) return;
    const names = keys.map(k => (labels[k] || k).replace(/ —.*$/, ''));
    toast(`⚠ Could not auto-select from the dropdown: ${names.join(', ')} — please choose ${keys.length > 1 ? 'these' : 'this'} by hand.`, 'warn');
  }

  // ── SCAN TRACE ─────────────────────────────────────────────────────────
  // Always recording, in memory, most recent scan only. Deliberately NOT a
  // mode to switch on and retry: a wrong fill is noticed after the passenger
  // has walked away, and that scan is never reproducible. This keeps the raw
  // scanner output, what it parsed to, every write this script made, and —
  // crucially — every change to those fields it did NOT make, which is the
  // only way to tell "we filled it wrong" apart from "we filled it right and
  // the page overwrote it" (identical in the finished form, opposite fixes).
  const _trace = { at: 0, kind: '', raw: '', viaSiteBox: false, parsed: null,
                   note: '', steps: [], changes: [] };
  const _traceReset = (kind, raw, viaSiteBox) => {
    Object.assign(_trace, { at: Date.now(), kind, raw, viaSiteBox,
                            parsed: null, note: '', steps: [], changes: [] });
  };
  const _traceStep = (o) => { if (_trace.at) _trace.steps.push({ ms: Date.now() - _trace.at, ...o }); };

  // fillField + before/after readings, so a step records what the box actually
  // ended up holding rather than only what we asked for.
  async function _fillTraced(phase, sel, val, key) {
    const read = () => { try { return _currentText(queryVisible(sel)); } catch { return '(unreadable)'; } };
    const before = read();
    const ok = await fillField(sel, val, key);
    const after = read();
    // `ok` is only what fillField believed. The field itself is the authority:
    // a write that left the box empty did not happen, whatever was returned,
    // and logging that as "ok" made the trace agree with a broken run — the
    // one moment it most needs to disagree. A control the officer cannot see
    // reads as '(unreadable)' and is left to fillField's own verdict.
    const landed = after !== '' || String(val) === '';
    const verdict = (ok !== false) && (landed || after === '(unreadable)');
    _traceStep({ phase, key, sel, want: String(val), before, after, ok: verdict });
    return verdict ? ok : false;
  }

  // Records changes to the mapped fields for a few seconds after a scan.
  // Steps say what this script did; changes say what happened to the field
  // afterwards — a change with no matching step at the same moment is someone
  // else writing, and the timestamp shows how long after the scan.
  function _traceWatch(targets, ms = 6000) {
    const t0 = _trace.at;
    if (!t0) return;
    const entries = Object.entries(targets || {}).filter(([, s]) => s);
    const last = new Map();
    const sample = (first) => {
      for (const [k, sel] of entries) {
        let el = null;
        try { el = queryVisible(sel); } catch { }
        const v = el ? _currentText(el) : '(element not found)';
        if (!first && last.get(k) !== v) {
          _trace.changes.push({ ms: Date.now() - t0, key: k, from: last.get(k), to: v });
        }
        last.set(k, v);
      }
    };
    sample(true);
    const iv = setInterval(() => {
      if (_trace.at !== t0) return clearInterval(iv);   // a newer scan owns the trace now
      sample(false);
    }, 200);
    setTimeout(() => clearInterval(iv), ms);
  }

  // Console entry point: __brcSimulateScan('P<IND…')  → run a scan without one
  // A keyboard-wedge scanner is the only way to produce a real scan, and the
  // keydown path deliberately refuses synthetic events (e.isTrusted), so there
  // is otherwise no way to exercise this on a machine that has no scanner
  // attached. This runs the exact same fill path a real scan takes — parse,
  // fill, settle, trace — so what you see is what an officer would see, and
  // __brcScanReport() works afterwards just the same.
  window.__brcSimulateScan = function (raw) {
    const clean = String(raw || '').replace(/[\r\n]/g, '');
    // TD3 MRZ: starts with 'P' + any subtype char (letter, digit, or '<').
    // Indian passports send 'PAI', Singaporean 'PASGP', standard 'P<' — all valid.
    if (/^P[A-Z0-9<]/.test(clean) || (clean[0] === 'P' && clean.length >= 88)) {
      _enqueueFill(() => _doMrzFill(clean, false)); return 'passport MRZ queued';
    }
    if (/^M[1-9]/.test(clean)) { _enqueueFill(() => _doBpFill(clean, false)); return 'boarding pass queued'; }
    return 'not a scan: expected a TD3 MRZ starting with P (any subtype) or a BCBP starting "M1"';
  };

  // Console entry point: _bug()
  // The one command to type when something looks wrong. __brcScanReport() is
  // the full forensic dump; this is the plain-English verdict on top of it —
  // what happened, what did not, and the most likely reason — so the answer
  // doesn't depend on reading a trace correctly mid-shift.
  window._bug = function () {
    const L = [];
    const say = t => L.push(t);
    say('── ATITHI HELPER: WHAT IS GOING WRONG ──');
    say('build          : ' + BUILD);
    say('this page      : ' + (isAtithiPage() ? 'recognised as an Atithi declaration page'
                                              : 'NOT recognised — the helper stays dormant here'));
    if (!_trace.at) {
      say('');
      say('VERDICT: no scan has been seen since this page loaded.');
      say('  • If you did scan, the scanner is not reaching this page. Click into');
      say('    the page once and scan again.');
      say('  • Only a passport MRZ (starts with "P" — any subtype: P<, PA, PP, PB, PN…) or');
      say('    a boarding pass (starts "M1") is recognised.');
      const out = L.join('\n');
      console.log(out);
      try { navigator.clipboard.writeText(out); } catch { }
      return out;
    }
    const ago = Math.round((Date.now() - _trace.at) / 1000);
    say('last scan      : ' + _trace.kind + ', ' + _trace.raw.length + ' chars, ' + ago + 's ago');
    const p = _trace.parsed;
    say('');
    if (!p) {
      say('VERDICT: the scan was not understood at all.');
      say('  ' + (_trace.note || 'It did not match a passport or boarding-pass layout.'));
    } else if (p._degraded) {
      say('VERDICT: the scan was misread. The document\'s own check digits reject');
      say('  the number and the dates, so those were deliberately left blank.');
      say('  Rescan — wipe the passport strip if it keeps happening.');
    } else {
      const wrote = _trace.steps.filter(x => x.ok).length;
      const failed = _trace.steps.filter(x => !x.ok);
      say('parsed OK      : ' + Object.keys(p).filter(k => k[0] !== '_' && p[k]).length + ' values read from the document');
      say('written OK     : ' + wrote + ' field(s)');
      if (failed.length) {
        say('COULD NOT WRITE: ' + failed.map(x => x.key).join(', '));
        say('  These fields were read from the document but would not take the value.');
        say('  Usually the field is not on this tab, or the site rejected it.');
        failed.forEach(x => say('    - ' + x.key + '  wanted "' + x.want + '"  box now "' + x.after + '"  via ' + x.sel));
      }
      const late = _trace.changes.filter(c => !_trace.steps.some(st => st.key === c.key && st.after === c.to));
      if (late.length) {
        say('CHANGED AFTER US: ' + late.map(c => c.key + ' -> "' + c.to + '"').join(', '));
        say('  Something on the page overwrote these after the scan — that is the');
        say('  site\'s own parser, not this script.');
      }
      if (!failed.length && !late.length) say('VERDICT: this scan filled everything it could. Nothing failed.');
      if (p._checksBad && p._checksBad.length) {
        say('NOTE: check digits disagreed on: ' + p._checksBad.join(', ') + ' — those were left blank on purpose.');
      }
    }
    say('');
    say('Full detail: __brcScanReport(1)   (masked, safe to share)');
    const out = L.join('\n');
    console.log(out);
    try { navigator.clipboard.writeText(out).then(() => console.log('(copied to clipboard)')); } catch { }
    return out;
  };

  // Console entry point: __brcFillDefaults() → apply every field rule now.
  // Same thing the panel's "⚡ Fill Now" button does, reachable without opening
  // the panel (and testable).
  window.__brcFillDefaults = function () { return fillAllDefaults(); };

  // Console entry point: __brcScanReport()  → full report, copied to clipboard
  //                      __brcScanReport(1) → same, with passenger data masked
  // The masked form keeps every position and length intact (that is what
  // diagnoses a field-offset problem) while removing the identity, so a report
  // can be shared without sending a real passenger's passport details.
  window.__brcScanReport = function (redact) {
    const mask = s => String(s == null ? '' : s).replace(/[A-Za-z0-9]/g, 'x');
    const m = v => redact ? mask(v) : String(v == null ? '' : v);
    const L = [];
    L.push('=== ATITHI HELPER SCAN TRACE ===');
    L.push('build: ' + BUILD + (redact ? '   (masked)' : ''));
    if (!_trace.at) {
      L.push('No scan recorded yet on this page. Scan a document, then run this again.');
    } else {
      const raw = _trace.raw.replace(/\n/g, '\\n');
      L.push('scan kind      : ' + _trace.kind);
      L.push('scanned into   : ' + (_trace.viaSiteBox ? "the SITE's own scan box" : 'the page (focus elsewhere)'));
      L.push('raw length     : ' + raw.length + ' chars');
      L.push('raw            : ' + m(raw));
      if (_trace.note) L.push('note           : ' + _trace.note);
      L.push('');
      L.push('-- parsed --');
      if (!_trace.parsed) L.push('  (nothing — parser rejected this scan)');
      else Object.entries(_trace.parsed).forEach(([k, v]) => {
        if (k.startsWith('_') || v === '' || v == null) return;
        L.push('  ' + k.padEnd(18) + ' = ' + m(v));
      });
      L.push('');
      L.push('-- writes by this script --');
      if (!_trace.steps.length) L.push('  (none)');
      _trace.steps.forEach(s => L.push(
        '  +' + String(s.ms).padStart(5) + 'ms ' + (s.ok ? 'ok  ' : 'FAIL') + ' ' +
        String(s.key).padEnd(17) + ' want=' + JSON.stringify(m(s.want)) +
        ' before=' + JSON.stringify(m(s.before)) + ' after=' + JSON.stringify(m(s.after)) +
        '  [' + s.phase + ']  ' + s.sel));
      L.push('');
      L.push('-- field changes observed (anything not matching a write above is the page itself) --');
      if (!_trace.changes.length) L.push('  (none — nothing touched these fields after the scan)');
      _trace.changes.forEach(c => L.push(
        '  +' + String(c.ms).padStart(5) + 'ms ' + String(c.key).padEnd(17) +
        JSON.stringify(m(c.from)) + ' -> ' + JSON.stringify(m(c.to))));
    }
    L.push('=== END ===');
    const text = L.join('\n');
    console.log(text);
    try { navigator.clipboard.writeText(text).then(() => console.log('%c report copied to clipboard ', 'background:#16a34a;color:#fff')); } catch { }
    return text;
  };

  // ── POST-SCAN CORRECTION PASS ──────────────────────────────────────────
  // The declaration page ships its own scan boxes (formcontrolname="scan_
  // passport" / "scan_passport_last_page" / "scan_boarding_pass") backed by
  // its own parser. Scanning through those runs TWO parsers over the same
  // keystrokes: this script's (immediately, on the 88th/58th character) and
  // the site's (asynchronously, whenever its control gets round to the text).
  // The site's wins by writing last — and its output is exactly the mangled
  // data that keeps coming back after each fix here:
  //   • "SURNAME/GIVEN" pasted verbatim into the name box, which the site's
  //     own validator then rejects with "Name should be in characters only";
  //   • dates read off misaligned MRZ offsets — "ND/82/NaN", "5M/35/2101",
  //     and "NaN/NaN/NaN" for the issue date derived from them;
  //   • a long run of barcode digits dropped into Port of Arrival.
  // Filling correctly once therefore isn't enough. Re-assert after the site
  // settles. This never fights for a field this script has no value for: it
  // restores only what it actually parsed, and otherwise clears values that
  // are impossible on their face (_isGarbage) rather than leaving the officer
  // to spot them.
  const SITE_SETTLE_MS = 3200, SITE_POLL_MS = 300;
  const DATE_KEYS = new Set(['dob', 'expiry', 'issueDate', 'flightDate']);
  const NAME_KEYS = new Set(['fullName', 'passengerName', 'surname', 'givenNames']);
  // Controls whose value is a code or a picked-from-list label — never a
  // free-running number, so a long digit run in one is barcode spill.
  const CODE_KEYS = new Set(['from', 'to', 'fromCountry', 'nationality', 'issuingCountry']);

  // ── The officer always outranks the corrector ─────────────────────────────
  // The settle window stays open for up to 3.2s, and an officer who spots a
  // wrong value corrects it immediately — well inside that window. Without this
  // guard the next poll silently reverted their typing, which is the worst
  // possible behaviour on a customs declaration: it looks like the form
  // rejected the correction. A field is the officer's the moment they focus it
  // or type a trusted keystroke into it, and it stays theirs for this scan.
  const _userEdited = new WeakMap();
  const _markEdited = (e) => { if (e.isTrusted && e.target) _userEdited.set(e.target, Date.now()); };
  for (const t of ['input', 'keydown', 'pointerdown']) document.addEventListener(t, _markEdited, true);
  function _officerOwns(el, since) {
    if (!el) return false;
    const touched = _userEdited.get(el) || 0;
    // Focus alone isn't ownership — this script's own dropdown fills leave a
    // control focused, and skipping those would gut the verification pass. It
    // counts only together with a real user event on that same control.
    if (document.activeElement === el && touched) return true;
    return touched >= since;
  }

  // Wait until the officer stops typing, then report which control was theirs
  // so focus can be handed back. Capped so a control left focused and abandoned
  // can't stall the verification pass forever.
  async function _awaitOfficerIdle(since, maxWaitMs = 20000, idleMs = 1200) {
    const until = Date.now() + maxWaitMs;
    let held = null;
    while (Date.now() < until) {
      const el = document.activeElement;
      const touched = el ? (_userEdited.get(el) || 0) : 0;
      // `touched` of 0 means "never touched by a human" — it must NOT satisfy
      // `>= since` when since is 0, or every control this script focuses looks
      // like the officer's and their keystrokes get replayed into a dropdown.
      if (!el || el === document.body || !touched || touched < since) break;
      held = el;
      if (Date.now() - touched >= idleMs) break;   // still theirs, but idle
      await new Promise(r => setTimeout(r, 200));
    }
    return held;
  }

  // ── Keystrokes typed into a control this script has borrowed ──────────────
  // Waiting for the officer to pause closes most of the gap, but not the case
  // where they start typing in the same instant as a focus() call. Those
  // keystrokes don't merely vanish — they land in the dropdown's own search
  // box, so the officer loses a character AND the search this script is in the
  // middle of gets corrupted. While a control is borrowed, hold any human-speed
  // keystroke aside and replay it into the field the officer was actually in.
  // Machine-speed bursts are left alone: that is a scanner, and it belongs to
  // the scan handler.
  let _stolenFrom = null, _stolenKeys = '', _stolenCaret = null;
  document.addEventListener('keydown', (e) => {
    if (!_stolenFrom || !e.isTrusted || e.key.length !== 1) return;
    // Focus is back where it belongs, so this keystroke is already going to the
    // right place. Anything held from before must go in FIRST though, or a
    // character borrowed mid-word gets replayed after the ones that followed it
    // and the officer's text comes out scrambled.
    if (document.activeElement === _stolenFrom) { _flushStolen(_stolenFrom); return; }
    // Never intercept anything that could be a scan. Timing is the wrong test
    // here: a threshold loose enough to catch fast human typing also catches
    // the first character of a boarding-pass scan started while the passport's
    // dropdowns are still filling — and eating that loses the entire scan,
    // which is far worse than the problem being solved. The document formats
    // are the reliable signal: let 'P'/'M' through while a header could still
    // be forming, and let everything through once one has. The officer's cost
    // is at most a 'P' or 'M' typed inside a fill round; every other character
    // is protected.
    const buf = _mrzBuf.replace(/[\r\n]/g, '');
    // Scan underway: buf starts with a recognised header. 'P' covers all
    // passport subtypes (P<, PA, PP, PB, PN …); M[1-9] covers BCBP.
    if (/^P[A-Z0-9<]/.test(buf) || /^M[1-9]/.test(buf)) return;
    const next = (buf + e.key).toUpperCase();
    // Header still forming: allow 'P' alone or 'P' + any MRZ subtype char,
    // and 'M' alone or 'M' + digit. The old pattern '^(P<?|M[1-9]?)' only
    // permitted '<' as the second char after P, blocking 'PA', 'PP', etc.
    if (next.length <= 2 && /^(P[A-Z0-9<]?|M[1-9]?)$/.test(next)) return;
    _stolenKeys += e.key;
    e.preventDefault(); e.stopPropagation();
  }, true);

  // Held keystrokes must never outlive the borrow that captured them. Every
  // change of borrowed-control — including clearing it — flushes first, or a
  // character sits in the buffer while later ones type through normally and it
  // resurfaces at the end, out of order.
  function _setBorrow(from) {
    if (_stolenKeys && _stolenFrom) _flushStolen(_stolenFrom);
    _stolenFrom = from || null;
    // Remember where their caret was. An officer correcting a typo clicks into
    // the middle of a name, so replaying at the end of the value would scramble
    // it just as badly as losing the characters did.
    _stolenCaret = null;
    try { if (_stolenFrom && typeof _stolenFrom.selectionStart === 'number') _stolenCaret = _stolenFrom.selectionStart; } catch { }
  }

  function _flushStolen(el) {
    const held = _stolenKeys;
    if (!held || !el || !el.isConnected || !('value' in el)) return;
    _stolenKeys = '';
    try {
      const cur = String(el.value || '');
      const at = (_stolenCaret === null || _stolenCaret > cur.length) ? cur.length : _stolenCaret;
      const setter = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value')?.set;
      const v = cur.slice(0, at) + held + cur.slice(at);
      if (setter) setter.call(el, v); else el.value = v;
      _stolenCaret = at + held.length;          // keep typing where they left off
      if (document.activeElement === el && el.setSelectionRange) el.setSelectionRange(_stolenCaret, _stolenCaret);
      el.dispatchEvent(new InputEvent('input', { bubbles: true }));
    } catch { }
  }

  function _returnFocus(el) {
    // With nowhere to put them, held keystrokes stay held — the settle pass
    // calls this with null whenever the officer wasn't typing, and dropping the
    // buffer there would throw away characters the fill loop is still holding.
    if (!el || !el.isConnected) return;
    _flushStolen(el);
    _stolenFrom = null;
    try {
      if (document.activeElement !== el) el.focus();
      const n = String(el.value || '').length;
      const at = (_stolenCaret === null || _stolenCaret > n) ? n : _stolenCaret;
      if (el.setSelectionRange) el.setSelectionRange(at, at);
      _stolenCaret = null;
    } catch { }
  }

  function _isGarbage(key, el) {
    const v = _currentText(el);
    if (!v) return false;
    if (/nan|undefined/i.test(v)) return true;
    if (NAME_KEYS.has(key) && /[\/\\<>0-9]/.test(v)) return true;
    if (CODE_KEYS.has(key) && /^\d{4,}$/.test(v)) return true;
    if (DATE_KEYS.has(key)) {
      const m = v.match(/^(\d{1,2})\/(\d{1,2})\/(\d{4})$/);
      if (!m) return true;                       // not a date at all
      const dd = +m[1], mm = +m[2];
      if (dd < 1 || dd > 31 || mm < 1 || mm > 12) return true;
    }
    return false;
  }

  function _clearField(el) {
    try {
      const setter = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value')?.set;
      if (setter) setter.call(el, ''); else el.value = '';
      el.dispatchEvent(new InputEvent('input', { bubbles: true }));
      el.dispatchEvent(new Event('change', { bubbles: true }));
      el.dispatchEvent(new Event('blur', { bubbles: true }));
    } catch { }
  }

  // Did an overlay control (mat-autocomplete / mat-select) end up holding
  // something that plausibly corresponds to what we scanned? These can't be
  // compared literally the way a text box can: what gets committed is the
  // site's OWN option label ("SRI LANKA", "Sri Lanka (LK)", "COLOMBO - CMB"),
  // never our search string. So match loosely against the same candidate list
  // the filler drove the dropdown with — which is still more than enough to
  // catch the failure that matters, a Port of Arrival holding a run of barcode
  // digits that corresponds to no option at all.
  function _overlayLooksRight(key, raw, value) {
    const v = _norm(value);
    if (!v) return false;
    const aliases = autocompleteCandidates(key, raw).map(_norm).filter(Boolean);
    return aliases.some(a =>
      v === a ||
      (a.length >= 2 && v.startsWith(a)) ||
      (v.length >= 2 && a.startsWith(v)) ||
      (a.length >= 3 && v.includes(a)));
  }

  async function _settleAndCorrect(targets, parsed, labels, viaSiteBox) {
    const all = Object.entries(targets || {}).filter(([k, sel]) => sel && !SOFT_FILL_KEYS.has(k));
    // Text/date boxes are cheap to re-assert, so they're polled. Overlay
    // controls are not — each refill reopens the panel and waits on the site
    // to render its list — so they get ONE verification pass after the dust
    // settles instead of being hammered every tick.
    const entries = all.filter(([, sel]) => !_isOverlayTarget(sel));
    const overlays = all.filter(([, sel]) => _isOverlayTarget(sel));
    if (!entries.length && !overlays.length) return;
    // Watch for the full settle window only when the site's own parser was
    // actually invited to run; otherwise two quick passes are enough to catch
    // a late re-render without holding the officer up.
    const startedAt = Date.now();
    const deadline = startedAt + (viaSiteBox ? SITE_SETTLE_MS : SITE_POLL_MS * 2);
    const corrected = new Set();
    const unfixable = [];
    do {
      await new Promise(r => setTimeout(r, SITE_POLL_MS));
      for (const [k, sel] of entries) {
        let el = null;
        try { el = queryVisible(sel); } catch { }
        if (!el || _officerOwns(el, startedAt)) continue;
        const want = parsed[k];
        if (want) {
          const have = String(el.value || '').trim();
          const w = String(want).trim();
          // A date box legitimately renders in its own format, so compare
          // against every spelling this script would have written.
          const same = have === w || have === toDisplayDate(w) || have === toInputDate(w);
          if (!same) {
            await _fillTraced('correct-text', sel, want, k);
            if (have) corrected.add(k);      // overwritten, not merely blank
          }
        } else if (_isGarbage(k, el)) {
          _clearField(el);
          corrected.add(k);
        }
      }
    } while (Date.now() < deadline);

    // ── Dropdowns, once, in cascade order ────────────────────────────────
    // Order matters on re-verification exactly as it did on the first fill:
    // the Country (from where coming) control filters the Airport control's
    // option list, so a corrected country invalidates whatever the airport
    // box holds and the airport must be redone after it — never before.
    const ordered = overlays.slice().sort((a, b) => {
      const ia = BP_CASCADE_ORDER.indexOf(a[0]), ib = BP_CASCADE_ORDER.indexOf(b[0]);
      return (ia === -1 ? -1 : ia) - (ib === -1 ? -1 : ib);
    });
    // Re-committing a dropdown means focusing it, which yanks the caret out of
    // wherever the officer is typing — their next keystrokes land on <body> and
    // vanish. Skipping ownership checks isn't enough, because the theft happens
    // on a DIFFERENT control from the one they're editing. So wait for them to
    // pause first: this pass is a safety net, and a safety net must never cost
    // the officer a keystroke. Focus is handed back when it's done.
    const officerFocus = await _awaitOfficerIdle(startedAt);
    let countryRedone = false;
    for (const [k, sel] of ordered) {
      const want = parsed[k];
      let el = null;
      try { el = queryVisible(sel); } catch { }
      if (!el || _officerOwns(el, startedAt)) continue;
      if (!want) {
        // Nothing scanned for this control: only step in if it holds something
        // that can't be a real option (barcode spill), never to blank a value
        // the officer picked by hand.
        if (_isGarbage(k, el)) { _clearField(el); corrected.add(k); }
        continue;
      }
      // The airport list was rebuilt under this control when the country was
      // re-committed, so whatever it shows now is stale by construction — redo
      // it even if the text still looks plausible.
      const stale = countryRedone && k === 'from';
      const had = _currentText(el);
      if (!stale && _overlayLooksRight(k, want, had)) continue;
      const ok = await _fillTraced('correct-dropdown', sel, want, k);
      if (ok !== false) {
        if (k === 'fromCountry') countryRedone = true;
        if (had) corrected.add(k);
      } else {
        unfixable.push(k);
      }
    }
    _returnFocus(officerFocus);

    if (unfixable.length) _warnUnresolved(unfixable, labels);
    if (corrected.size) {
      const names = [...corrected].map(k => String(labels[k] || k).replace(/ [—(].*$/, '').trim());
      toast(`↻ Re-fixed ${names.length} field(s) the page overwrote with unusable scan data: ${names.join(', ')}`, 'warn');
    }
  }

  async function _doMrzFill(raw, viaSiteBox) {
    _traceReset('passport MRZ', raw, viaSiteBox);
    const parsed = parseMRZ(raw);
    _trace.parsed = parsed;
    if (!parsed) {
      _trace.note = 'parseMRZ returned nothing: this is not a TD3 passport MRZ. It needs two ' +
                    '44-character lines (88 chars total) with the first starting "P".';
      return;
    }
    if (parsed._degraded) {
      _trace.note = 'All three check digits failed — the number and the dates are refused as ' +
                    'unreliable. Name, gender, nationality and country of issuance are filled ' +
                    'from fixed positions and must be checked against the passport by eye.';
      toast('⚠ Passport partly readable — number and dates refused (check digits failed). ' +
            'Name/gender/nationality filled — VERIFY them, and rescan for the rest.', 'warn');
    }
    let filled = 0, defFilled = 0, unresolved = [];
    const mrzTargets = _effectiveTargets('mrz');
    _traceWatch(mrzTargets);
    const r = await _fillTargets(mrzTargets, parsed, null, 'mrz');
    filled = r.filled; unresolved = r.unresolved;
    for (const col of st.columns) {
      if (col.mrzField && col.selector && parsed[col.mrzField]) {
        await fillField(col.selector, parsed[col.mrzField], col.mrzField); filled++;
      }
    }
    defFilled = await fillAllDefaults();
    filled += defFilled;
    if (!parsed._checksOk) {
      toast(`⚠ Scan may be misread (checksum mismatch on: ${parsed._checksBad.join(', ')}) — verify these fields before saving!`, 'warn');
    }
    if (filled > 0) toast(`🛂 Passport scanned ✓ — ${filled} field(s) filled${defFilled ? ` (incl. ${defFilled} default)` : ''}`);
    _warnUnresolved(unresolved, MRZ_LABELS);
    if (parsed.passportNo) setTimeout(() => checkDraftMatchAndToast(parsed.passportNo), 50);
    await _settleAndCorrect(mrzTargets, parsed, MRZ_LABELS, viaSiteBox);
  }

  async function _doBpFill(raw, viaSiteBox) {
    _traceReset('boarding pass', raw, viaSiteBox);
    const parsed = parseBP(raw);
    _trace.parsed = parsed;
    if (!parsed) {
      _trace.note = 'parseBP returned nothing: an IATA boarding-pass barcode must start "M" followed by the leg count.';
      return;
    }
    if (!parsed.ticketNo) {
      _trace.note = 'No E-Ticket Number in this barcode — its conditional section declares no ' +
                    'repeated block (the airline did not encode one). Nothing is wrong with the scan.';
    }
    const bpTargets = _effectiveTargets('bp');
    _traceWatch(bpTargets);
    const r = await _fillTargets(bpTargets, parsed, BP_CASCADE_ORDER, 'bp');
    const filled = r.filled, unresolved = r.unresolved;
    if (filled > 0) toast(`✈️ Boarding Pass ✓ — ${filled} field(s) filled`);
    _warnUnresolved(unresolved, BP_LABELS);
    await _settleAndCorrect(bpTargets, parsed, BP_LABELS, viaSiteBox);
  }

  // Whatever field had focus when a scan started, plus its value at that
  // moment. A scanner is just a very fast keyboard: unless the keystrokes are
  // swallowed, the entire raw scan is ALSO typed natively into the focused
  // control — and the officer's cursor is very often already sitting in the
  // Passport Number box when they scan. That native text then raced with this
  // script's own programmatic fill (and `maxlength="20"` on that field
  // silently truncated it), which is exactly how a field ended up holding a
  // mangled mix of raw scan characters and the correct parsed value. The
  // anchor lets the pre-scan value be restored before the real fill runs.
  // _scanIntoSiteBox is a latch for the whole scan, not a per-keystroke
  // lookup: it's decided once when the buffer starts and must survive every
  // subsequent character, since document.activeElement can move underneath us
  // mid-scan (and the anchor is deliberately dropped in this case).
  let _scanAnchor = null, _scanIntoSiteBox = false;

  function _captureScanAnchor() {
    const el = document.activeElement;
    const fcn = (el && el.getAttribute && el.getAttribute('formcontrolname')) || '';
    _scanIntoSiteBox = /^scan_/.test(fcn);
    if (!_scanIntoSiteBox && el && (el.tagName === 'INPUT' || el.tagName === 'TEXTAREA') &&
        !el.closest('#__brc_panel')) {
      _scanAnchor = { el, value: el.value };
    } else {
      _scanAnchor = null;
    }
  }

  // Every scan must start from a clean slate. Leaving _scanIntoSiteBox or
  // _scanStart set from the previous scan meant the NEXT scan inherited the
  // last one's decisions — e.g. after scanning into the site's own scan box,
  // a following passport scan elsewhere on the form would not be swallowed.
  // Zeroing _lastKey also forces the next keystroke to re-anchor.
  function _resetScanState() {
    _mrzBuf = ''; _scanStart = 0; _lastKey = 0;
    _scanIntoSiteBox = false; _scanAnchor = null;
  }

  // A scan is recognised the moment it has enough characters to parse (88 for
  // a passport MRZ, 58 for a boarding pass) — but the scanner often keeps
  // sending: the optional-data tail of the MRZ, or the whole conditional
  // section of a BCBP barcode. Once the buffer was reset those leftover
  // characters no longer matched any scan header, so they were typed straight
  // into whatever field had focus. That is where a Port of Arrival box ended
  // up holding a long run of digits. Keep swallowing while the burst is still
  // arriving at machine speed; the first human-length pause ends it, so
  // ordinary typing and a genuinely separate second scan are never affected.
  let _tailBurst = false;
  let _tailStr = '';       // last two swallowed chars, watched for a new header
  let _mrzTimes = [];      // arrival time of each buffered char, for re-sync

  function _restoreScanAnchor() {
    if (!_scanAnchor) return;
    const { el, value } = _scanAnchor;
    _scanAnchor = null;
    try {
      if (el.isConnected && el.value !== value) {
        const setter = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value')?.set;
        if (setter) setter.call(el, value); else el.value = value;
        el.dispatchEvent(new InputEvent('input', { bubbles: true }));
      }
      el.blur();
    } catch { }
  }

  window.addEventListener('keydown', (e) => {
    if (!e.isTrusted) return;   // our own synthetic events, never a real scan
    if (e.key.length > 1 && e.key !== 'Enter') return;
    const now = Date.now();
    // Leftover characters from the scan we just consumed — eat them silently.
    if (_tailBurst) {
      if (now - _lastKey < 60) {
        _lastKey = now;
        e.preventDefault(); e.stopPropagation();
        // …unless the "leftovers" are actually the next document. An officer
        // scanning passport-then-boarding-pass in one motion can start the
        // second scan before the first burst has decayed, and swallowing that
        // silently loses the whole boarding pass with no error shown. A scan
        // header inside the tail means the tail is over.
        _tailStr = (_tailStr + e.key.toUpperCase()).slice(-2);
        if (/^P[A-Z0-9<]$/.test(_tailStr) || /^M[1-9]$/.test(_tailStr)) {
          _tailBurst = false;
          _mrzBuf = _tailStr; _mrzTimes = [now - 1, now];
          _scanStart = now - 1; _captureScanAnchor();
        }
        return;
      }
      _tailBurst = false;   // human-length pause: the burst is over
    }
    _tailStr = '';
    if (now - _lastKey > 500) { _mrzBuf = ''; _mrzTimes = []; _scanStart = now; _captureScanAnchor(); }
    _lastKey = now;
    _mrzBuf += (e.key === 'Enter') ? '\n' : e.key.toUpperCase();
    _mrzTimes.push(now);

    let clean = _mrzBuf.replace(/[\r\n]/g, '');

    // ── Re-sync onto a scan header that starts mid-buffer ─────────────────
    // The buffer is only cleared after a half-second of silence, so an officer
    // who types in a field and scans straight afterwards had their typing
    // sitting in front of the MRZ: the buffer became
    // "PRE-EXISTINGP<INDHARIHARAN…", every offset shifted, all three check
    // digits failed and the scan was thrown away. (It failed safe — nothing
    // wrong was filled — but nothing was filled either, and the officer had no
    // idea why.) A real scan always BEGINS with its header, so once the buffer
    // starts with one this never re-triggers; that matters because "P<" also
    // occurs naturally inside names like PRADEEP<<KUMAR.
    //
    // Machine speed is the discriminator, measured per character rather than
    // over the whole buffer: an officer typing "ITEM1 …" must not have their
    // next keystrokes swallowed just because "M1" appeared.
    // MRZ TD3 line 1 starts with 'P' followed by a document subtype letter
    // (often another 'P' for regular passports, 'A'/'B'/'N' for official/
    // business/diplomatic, or '<' when no subtype is assigned). Restricting
    // the header to 'P<' missed every passport whose line 1 begins 'PA',
    // 'PP', 'PB', 'PN', etc. — including Indian passports (PAS/PAI) and
    // Singaporean passports (PASGP). The pattern is now /^P[A-Z0-9<]/ which
    // matches ANY valid TD3 passport while still being specific enough to
    // avoid false-positives from normal typing (a human pressing 'P' and
    // then any letter would need sub-60ms gaps to be treated as a scan).
    if (!/^P[A-Z0-9<]/.test(clean) && !/^M[1-9]/.test(clean)) {
      const m = /P[A-Z0-9<]|M[1-9]/.exec(clean);
      if (m && m.index > 0) {
        const times = _mrzTimes.slice(-clean.length);   // aligned with `clean`
        let machine = true;
        for (let i = m.index + 1; i < times.length; i++) {
          if (times[i] - times[i - 1] >= 60) { machine = false; break; }
        }
        if (machine && times.length - m.index >= 2) {
          _mrzBuf = clean.slice(m.index);
          _mrzTimes = times.slice(m.index);
          _scanStart = times[m.index];
          _captureScanAnchor();
          clean = _mrzBuf;
        }
      }
    }

    // Once the buffer is unambiguously a scan header ("P<" for a TD3 passport,
    // "M1" for a BCBP boarding pass) typed at machine speed, swallow every
    // remaining keystroke so none of it reaches the page. Both conditions are
    // required: a human can type "M1" into an item description, but not with
    // sub-60ms gaps between characters.
    // ...EXCEPT when the officer deliberately scanned into one of the site's
    // own scan boxes (formcontrolname="scan_passport" /
    // "scan_passport_last_page" / "scan_boarding_pass", present on the
    // gold/silver declaration page). Those exist precisely so the site can do
    // its own parse-and-fill; swallowing the keystrokes there would break the
    // site's built-in behaviour and leave the officer worse off than before
    // this script was installed. In that case let the characters through
    // untouched and leave the field's contents alone — this script still sees
    // every keystroke and fills the Excel side independently.
    const machineSpeed = now - _scanStart <= clean.length * 60;
    if (clean.length >= 2 && machineSpeed && !_scanIntoSiteBox &&
        (/^P[A-Z0-9<]/.test(clean) || /^M[1-9]/.test(clean))) {
      e.preventDefault();
      e.stopPropagation();
    }

    // ── PASSPORT MRZ: starts with P, 88+ chars ────────────────
    if (clean.length >= 88 && /^P/.test(clean)) {
      const buf = _mrzBuf;
      clearTimeout(_mrzTimer);
      _restoreScanAnchor();
      // Arm BEFORE the reset (which clears _scanIntoSiteBox) and keep
      // _lastKey, or the burst check below has nothing to measure against.
      _tailBurst = !_scanIntoSiteBox;
      const viaSiteBox = _scanIntoSiteBox;   // survives the reset below
      _resetScanState();
      _lastKey = now;
      _enqueueFill(() => _doMrzFill(buf, viaSiteBox));
      return;
    }

    // ── BOARDING PASS BCBP: starts with M1 ────────────────────
    // 58 chars is the mandatory block (through passenger status at offset 57),
    // but a real barcode does not stop there: chars 58-59 hold the hex LENGTH
    // of everything that follows, and the E-Ticket Number the form marks
    // required lives inside that conditional section. Firing the moment 58
    // chars had arrived — as this used to — handed parseBP() a 58-character
    // string and threw the rest away, so the conditional section was never
    // parsed no matter how complete the scan was. Real example, a 90-char
    // AirAsia pass: everything from "1E>3180KK..." was discarded.
    //
    // So wait for the length the barcode itself declares. If the scanner sends
    // fewer characters than promised (truncated read, or one of the airlines
    // that stops at the mandatory block), the idle flush below fires with
    // whatever did arrive rather than leaving the scan stuck forever.
    if (clean.length >= 58 && /^M[1-9]/.test(clean)) {
      const need = bcbpTotalLength(clean);   // Infinity until it can be known
      if (clean.length >= need) {
        const buf = _mrzBuf;
        clearTimeout(_mrzTimer);
        _restoreScanAnchor();
        // Arm BEFORE the reset (which clears _scanIntoSiteBox) and keep
        // _lastKey, or the burst check below has nothing to measure against.
        _tailBurst = !_scanIntoSiteBox;
        const viaSiteBox = _scanIntoSiteBox;   // survives the reset below
        _resetScanState();
        _lastKey = now;
        _enqueueFill(() => _doBpFill(buf, viaSiteBox));
        return;
      }
    }

    clearTimeout(_mrzTimer);
    _mrzTimer = setTimeout(_flushIdleScan, 400);
  }, true);

  // The burst stopped without ever reaching a length we could act on. Either a
  // boarding pass shorter than it declared (fire with what arrived — the
  // mandatory block alone still yields name/PNR/flight/seat/route), or a burst
  // that matched no scan header at all, which is the case worth recording:
  // nothing fills, no toast appears, and without a trace there is nothing left
  // to look at afterwards.
  function _flushIdleScan() {
    const clean = _mrzBuf.replace(/[\r\n]/g, '');
    if (clean.length >= 58 && /^M[1-9]/.test(clean)) {
      const buf = _mrzBuf, viaSiteBox = _scanIntoSiteBox;
      _restoreScanAnchor();
      _tailBurst = !_scanIntoSiteBox;
      _resetScanState();
      _lastKey = Date.now();
      _enqueueFill(() => _doBpFill(buf, viaSiteBox));
      return;
    }
    if (clean.length >= 20) {
      _traceReset('unrecognised', _mrzBuf, _scanIntoSiteBox);
      _trace.note = 'This burst never matched a scan header. A passport MRZ must start ' +
                    'with "P" (any subtype: P<, PA, PP, PB, PN …) and a boarding pass with "M1" — ' +
                    'check what the scanner is sending (prefix/suffix settings, unexpected BOM, ' +
                    'or a document format this build does not read).';
    }
    _resetScanState();
  }

  buildUI();
  ensureSyncDirHandle().then(h => { syncConnected = !!h; if (h) render(); });
  pullSharedFolderSync();

  // Loud, hard-to-miss reminder on every fresh load (crash/reload/relogin,
  // or a bookmarklet re-click on a new page) that recoverable work is
  // sitting in Drafts — this is the whole point of draft-autosave surviving
  // a crash, so it shouldn't depend on the officer remembering to open the
  // panel and check.
  // Keep "copy from field" rules following their source for the life of the
  // page. Registered once, unconditionally: the rules themselves are read at
  // event time, so adding or deleting one in the panel takes effect straight
  // away with no re-arming.
  armFieldMirrors();

  purgeExpiredDrafts();
  const _pending = Object.keys(st.drafts).length;
  if (_pending) {
    setTimeout(() => toast(`📝 ${_pending} unsaved passenger${_pending > 1 ? 's' : ''} from before — click 📋 to recover.`, 'warn'), 400);
  }
})();
