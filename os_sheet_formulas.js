// ============================================================
// COPS OS Sheet — SLIM script (no embedded data)
// Use this AFTER importing OS_DATA.csv into a lookup sheet.
//
// >>> IMPORTANT: set DATA_SHEET below to the EXACT name of the tab
//     that holds the imported CSV data (e.g. 'OS_details').
//
// Steps:
//   1) File > Import > Upload OS_DATA.csv > Import into a NEW sheet.
//   2) Set DATA_SHEET below to that tab's name.
//   3) Extensions > Apps Script > paste this file > Save.
//   4) (recommended) Run  cleanupStrayDataSheet()  — deletes any
//      half-loaded 'OS_DATA' tab left over from the timed-out run.
//   5) Run  setupMainSheetFormulas()   (fills existing rows)
//   6) Run  installTrigger()           (auto-fills future rows)
//   7) (optional) Run  finalizeOsDataSheet()  to style + hide the data tab
//
// Data columns (A..F):
//   A os_key ("OSNo/Year")  B Passport No  C Pax Name
//   D Supposed to Contain   E Associated BR  F Items Cleared Under BR
// ============================================================

// ↓↓↓ CHANGE THIS to whatever you named the imported tab ↓↓↓
var DATA_SHEET = 'OS_DATA';

// Warehouse lookup tab (import WAREHOUSE_DATA.csv as this tab).
// Columns: A key | B pax_name | C description | D wt_nos | E value | F location | G valuable_no
var WH_SHEET = 'WAREHOUSE';

// Warehouse columns added to each team sheet, by header keyword -> WAREHOUSE col.
var WH_COLS = [
  { hdr: 'wh pax',      title: 'WH Pax Name',    col: 'B' },
  { hdr: 'wh desc',     title: 'WH Description',  col: 'C' },
  { hdr: 'wh wt',       title: 'WH Wt/Nos',       col: 'D' },
  { hdr: 'wh value',    title: 'WH Value',        col: 'E' },
  { hdr: 'wh location', title: 'WH Location',     col: 'F' }
];

// Quoted A..F reference, safe even if the name has spaces.
function dataRangeRef_() {
  return "'" + DATA_SHEET + "'!$A:$F";
}

// Warehouse lookup formula for a row: builds the key from Case type + number
// (+ year for OS), then lists ALL matching warehouse records (multi-item
// seizures appear on separate lines). ctL/numL/yrL = column letters.
function whFormula_(r, ctL, numL, yrL, whCol) {
  var rng = "'" + WH_SHEET + "'!";
  var key = 'IF($' + ctL + r + '="OS","OS "&$' + numL + r + '&"/"&$' + yrL + r +
            ',IF($' + ctL + r + '="DR","DR "&$' + numL + r + ',""))';
  var colR = rng + whCol + '$2:' + whCol;
  var keyR = rng + '$A$2:$A';
  var numKey = '"#"&$' + numL + r + '&"/"&$' + yrL + r;   // year-qualified bare fallback (warehouse cell had no OS/DR prefix)
  // Show ALL matches: exact OS/DR key OR the bare number+year — so nothing is missed.
  return '=IF(OR($' + ctL + r + '="",$' + numL + r + '=""),"",' +
    'LET(k,' + key + ',' +
    'IFERROR(TEXTJOIN(CHAR(10),TRUE,FILTER(' + colR + ',(' + keyR + '=k)+(' + keyR + '=' + numKey + '))),"")))';
}

// ============================================================
// CROSS-SHEET DUPLICATE STATUS (Team A / Team B / Team C)
// No timestamps. Status is written (as plain text) at entry time by the
// trigger, so the FIRST team to enter a case owns it ("NEW CASE") and any
// later entry shows "ALREADY ENTERED at location <loc> by <first team>".
// Whoever already has the case = whoever entered earlier.
// ============================================================

var STATUS_TEAMS = ['Team A', 'Team B', 'Team C'];
var STAMP_COL = 14;          // column N — legacy/unused; cleared on row removal

// Build a LIVE status formula for row r on sheet <self>. It recomputes
// instantly in the browser (no slow server round-trip). Owner = first team
// (Team A -> B -> C order) that holds the case; that team's location is shown.
// Works for both OS and DR (key = Case type + number + year).
//   ctL/numL/yrL/locL = column letters (same layout across the 3 team sheets).
function buildStatusFormula_(r, self, ctL, numL, yrL, locL) {
  var T = STATUS_TEAMS;
  function cnt(t) {
    return "COUNTIFS('" + t + "'!$" + ctL + ":$" + ctL + ",$" + ctL + r +
           ",'" + t + "'!$" + numL + ":$" + numL + ",$" + numL + r +
           ",'" + t + "'!$" + yrL + ":$" + yrL + ",$" + yrL + r + ")";
  }
  function loc(t) {
    return "IFERROR(INDEX(FILTER('" + t + "'!$" + locL + ":$" + locL +
           ",'" + t + "'!$" + ctL + ":$" + ctL + "=$" + ctL + r +
           ",'" + t + "'!$" + numL + ":$" + numL + "=$" + numL + r +
           ",'" + t + "'!$" + yrL + ":$" + yrL + "=$" + yrL + r + "),1),\"\")";
  }
  // running count within THIS sheet (unprefixed) up to row r
  var sp = "COUNTIFS($" + ctL + "$2:$" + ctL + r + ",$" + ctL + r +
           ",$" + numL + "$2:$" + numL + r + ",$" + numL + r +
           ",$" + yrL + "$2:$" + yrL + r + ",$" + yrL + r + ")";
  return '=IF(OR($' + ctL + r + '="",$' + numL + r + '="",$' + yrL + r + '=""),"",' +
    'LET(cA,' + cnt(T[0]) + ',cB,' + cnt(T[1]) + ',cC,' + cnt(T[2]) + ',sp,' + sp + ',' +
    'own,IF(cA>0,"' + T[0] + '",IF(cB>0,"' + T[1] + '","' + T[2] + '")),' +
    'lc,IF(cA>0,' + loc(T[0]) + ',IF(cB>0,' + loc(T[1]) + ',' + loc(T[2]) + ')),' +
    'IF(AND(own="' + self + '",sp=1),"NEW CASE",' +
    '"ALREADY ENTERED at location "&IF(lc="","—",lc)&" by "&own)))';
}

// Columns that hold FORMULAS (kept on removal); everything else in the row is
// data and gets wiped when a team removes a case.
function isFormulaCol_(header) {
  var h = (header == null ? '' : String(header)).toLowerCase();
  return h.indexOf('status') >= 0 || h.indexOf('supposed') >= 0 ||
         h.indexOf('contain') >= 0 || h.indexOf('passport') >= 0 ||
         h.indexOf('associated br') >= 0 || h.indexOf('cleared') >= 0;
}

// Team removed a case (cleared a key cell): wipe the row's DATA (cartons,
// location, dates, timestamp, leftover key cells) but keep the formula cells
// so the row is ready for reuse.
function clearRowKeepFormulas_(sheet, row) {
  var lastCol = Math.max(sheet.getLastColumn(), STAMP_COL);
  var headers = sheet.getRange(1, 1, 1, lastCol).getValues()[0];
  for (var c = 1; c <= lastCol; c++) {
    if (!isFormulaCol_(headers[c - 1])) sheet.getRange(row, c).clearContent();
  }
}

// One-time setup / refresh: fills the LIVE status formula down each team
// sheet's status column. Only the status column is written — your data is not
// changed. The formula recomputes instantly as rows are entered.
function setupTeamSheets() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  function colIn(headers, pats) {
    for (var i = 0; i < headers.length; i++) {
      var h = String(headers[i] || '').toLowerCase().trim();
      for (var p = 0; p < pats.length; p++) if (h.indexOf(pats[p]) >= 0) return i + 1;
    }
    return -1;
  }
  function colLetter(c) { var s = ''; while (c > 0) { var m = (c - 1) % 26; s = String.fromCharCode(65 + m) + s; c = Math.floor((c - 1) / 26); } return s; }

  var summary = [];
  STATUS_TEAMS.forEach(function (name) {
    var sh = ss.getSheetByName(name);
    if (!sh) { summary.push(name + ': MISSING — create this tab'); return; }
    var lastRow = sh.getLastRow();
    var headers = sh.getRange(1, 1, 1, Math.max(sh.getLastColumn(), 7)).getValues()[0];
    var ctCol  = colIn(headers, ['case type', 'casetype', 'case_type']);
    var numCol = colIn(headers, ['number', 'os no', 'os_no', 'offence no']);
    var yrCol  = colIn(headers, ['year']);
    var locCol = colIn(headers, ['location']);
    var statusCol = colIn(headers, ['status']);
    if (statusCol < 1 || ctCol < 1 || numCol < 1 || yrCol < 1) {
      summary.push(name + ': could not find status/case/number/year columns'); return;
    }
    if (lastRow >= 2) {
      var ctL = colLetter(ctCol), numL = colLetter(numCol), yrL = colLetter(yrCol),
          locL = colLetter(locCol > 0 ? locCol : 7);
      var forms = [];
      for (var r = 2; r <= lastRow; r++) forms.push([buildStatusFormula_(r, name, ctL, numL, yrL, locL)]);
      sh.getRange(2, statusCol, forms.length, 1).setFormulas(forms);
    }
    summary.push(name + ': ready (' + Math.max(lastRow - 1, 0) + ' rows)');
  });

  SpreadsheetApp.getUi().alert(
    'Live status formulas applied:\n' + summary.join('\n') +
    '\n\nConditional formatting: "Text contains" → ALREADY ENTERED (red).'
  );
}

// Delete a leftover, half-loaded 'OS_DATA' tab from the timed-out loader.
// Will NOT delete your real DATA_SHEET. Skips if the stray tab actually
// holds the full ~11,602 rows (in case you named your good data 'OS_DATA').
function cleanupStrayDataSheet() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var stray = ss.getSheetByName('OS_DATA');
  if (!stray) {
    SpreadsheetApp.getUi().alert('No "OS_DATA" tab found — nothing to clean up.');
    return;
  }
  if (stray.getName() === DATA_SHEET) {
    SpreadsheetApp.getUi().alert('"OS_DATA" IS your DATA_SHEET — not deleting it.');
    return;
  }
  var rows = stray.getLastRow();
  var ui = SpreadsheetApp.getUi();
  var resp = ui.alert(
    'Delete stray "OS_DATA" tab?',
    'It has ' + rows + ' rows (the full set is ~11,602). ' +
    'Your real data is in "' + DATA_SHEET + '". Delete the stray "OS_DATA"?',
    ui.ButtonSet.YES_NO
  );
  if (resp === ui.Button.YES) {
    ss.deleteSheet(stray);
    ui.alert('Deleted stray "OS_DATA" tab.');
  }
}

function finalizeOsDataSheet() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var sheet = ss.getSheetByName(DATA_SHEET);
  if (!sheet) {
    SpreadsheetApp.getUi().alert('No sheet named "' + DATA_SHEET + '" found. Set DATA_SHEET correctly and import OS_DATA.csv first.');
    return;
  }
  sheet.setFrozenRows(1);
  sheet.getRange(1, 1, 1, 6)
    .setBackground('#1a73e8').setFontColor('#ffffff').setFontWeight('bold');
  sheet.getRange(2, 4, Math.max(sheet.getLastRow() - 1, 1), 3).setWrap(true);
  sheet.hideSheet();
  SpreadsheetApp.getUi().alert('"' + DATA_SHEET + '" styled and hidden. Now run setupMainSheetFormulas().');
}

function setupMainSheetFormulas() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var main = ss.getActiveSheet();
  if (main.getName() === DATA_SHEET) {
    SpreadsheetApp.getUi().alert('Please switch to your main tracking sheet first, then run again.');
    return;
  }
  if (!ss.getSheetByName(DATA_SHEET)) {
    SpreadsheetApp.getUi().alert('No sheet named "' + DATA_SHEET + '" found. Set DATA_SHEET correctly and import OS_DATA.csv first.');
    return;
  }
  var headers = main.getRange(1, 1, 1, main.getLastColumn()).getValues()[0];

  function colLetter(idx) {
    var letter = '';
    idx = idx + 1; // 1-based
    while (idx > 0) {
      var rem = (idx - 1) % 26;
      letter = String.fromCharCode(65 + rem) + letter;
      idx = Math.floor((idx - 1) / 26);
    }
    return letter;
  }

  // Find column indices by header name (case-insensitive partial match)
  function findCol(patterns) {
    for (var i = 0; i < headers.length; i++) {
      var h = (headers[i] || '').toLowerCase().trim();
      for (var p = 0; p < patterns.length; p++) {
        if (h.indexOf(patterns[p]) >= 0) return i;
      }
    }
    return -1;
  }

  var osNoCol     = findCol(['os no', 'os_no', 'os number', 'offence no', 'number']);
  var yearCol     = findCol(['year', 'os year', 'os_year']);
  var caseTypeCol = findCol(['case type', 'casetype', 'case_type']);
  var containsCol  = findCol(['supposed', 'contain']);
  var passportCol = findCol(['passport']);
  var brCol       = findCol(['associated br', 'br no', 'br number']);
  var clearedCol   = findCol(['cleared', 'br item']);

  if (osNoCol < 0 || yearCol < 0) {
    SpreadsheetApp.getUi().alert(
      'Could not find the case-number and Year columns in the first row.\n' +
      'Headers found: ' + headers.join(', ') + '\n\n' +
      'Expected a "number" (or "OS No") column and a "Year" column.'
    );
    return;
  }

  var lastRow = main.getLastRow();
  if (lastRow < 2) {
    SpreadsheetApp.getUi().alert('No data rows found below the header.');
    return;
  }

  var osLetter   = colLetter(osNoCol);
  var yearLetter = colLetter(yearCol);
  var typeLetter = caseTypeCol >= 0 ? colLetter(caseTypeCol) : null;
  var dataRange  = dataRangeRef_();

  // Only look up when Case type = "OS" (the lookup table holds OS data only),
  // so DR rows with the same number/year don't pick up OS contents.
  function vlookupFormula(row, lookupColNum) {
    var lookup = 'VLOOKUP(' + osLetter + row + '&"/"&' + yearLetter + row +
                 ',' + dataRange + ',' + lookupColNum + ',FALSE)';
    if (typeLetter) {
      return '=IFERROR(IF(' + typeLetter + row + '="OS",' + lookup + ',""),"")';
    }
    return '=IFERROR(' + lookup + ',"")';
  }

  // [main column index, OS_DATA column number, label]
  var targets = [
    [containsCol, 4, 'Supposed to Contain'],
    [passportCol, 2, 'Passport No'],
    [brCol,       5, 'Associated BR'],
    [clearedCol,  6, 'Items Cleared Under BR']
  ];

  var applied = [];
  for (var t = 0; t < targets.length; t++) {
    var colIdx  = targets[t][0];
    var dataCol = targets[t][1];
    var label   = targets[t][2];
    if (colIdx < 0) {
      applied.push('  SKIPPED (not found): ' + label);
      continue;
    }
    var formulas = [];
    for (var row = 2; row <= lastRow; row++) {
      formulas.push([vlookupFormula(row, dataCol)]);
    }
    main.getRange(2, colIdx + 1, lastRow - 1, 1).setFormulas(formulas);
    applied.push('  Applied: ' + label + ' -> column ' + colLetter(colIdx));
  }

  SpreadsheetApp.getUi().alert(
    'Formulas applied:\n' + applied.join('\n') + '\n\n' +
    'Run installTrigger() so new rows fill automatically.'
  );
}

// Adds the 5 warehouse columns (if missing) to the ACTIVE sheet and fills the
// lookup formulas down. Run once per team sheet (Team A / B / C).
function setupWarehouseColumns() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var sh = ss.getActiveSheet();
  if (sh.getName() === DATA_SHEET || sh.getName() === WH_SHEET) {
    SpreadsheetApp.getUi().alert('Switch to a team tracking sheet first, then run again.');
    return;
  }
  if (!ss.getSheetByName(WH_SHEET)) {
    SpreadsheetApp.getUi().alert('No "' + WH_SHEET + '" tab found. Import WAREHOUSE_DATA.csv as a tab named "' + WH_SHEET + '" first.');
    return;
  }
  var lastCol = sh.getLastColumn();
  var headers = sh.getRange(1, 1, 1, lastCol).getValues()[0];
  function findCol(pats) {
    for (var i = 0; i < headers.length; i++) {
      var h = String(headers[i] || '').toLowerCase().trim();
      for (var p = 0; p < pats.length; p++) if (h.indexOf(pats[p]) >= 0) return i + 1;
    }
    return -1;
  }
  function colLetter(c) { var s = ''; while (c > 0) { var m = (c - 1) % 26; s = String.fromCharCode(65 + m) + s; c = Math.floor((c - 1) / 26); } return s; }
  var ctCol = findCol(['case type', 'casetype']);
  var numCol = findCol(['number', 'os no', 'os_no']);
  var yrCol = findCol(['year']);
  if (ctCol < 0 || numCol < 0 || yrCol < 0) {
    SpreadsheetApp.getUi().alert('Could not find Case type / number / year columns on this sheet.');
    return;
  }
  var ctL = colLetter(ctCol), numL = colLetter(numCol), yrL = colLetter(yrCol);
  var nextCol = lastCol + 1;
  WH_COLS.forEach(function (wc) {
    var existing = findCol([wc.hdr]);
    if (existing < 0) { sh.getRange(1, nextCol).setValue(wc.title); wc._col = nextCol; headers.push(wc.title); nextCol++; }
    else wc._col = existing;
  });
  var lastRow = sh.getLastRow();
  if (lastRow >= 2) {
    WH_COLS.forEach(function (wc) {
      var forms = [];
      for (var r = 2; r <= lastRow; r++) forms.push([whFormula_(r, ctL, numL, yrL, wc.col)]);
      sh.getRange(2, wc._col, lastRow - 1, 1).setFormulas(forms);
    });
  }
  SpreadsheetApp.getUi().alert('Warehouse columns set on "' + sh.getName() + '".\nRun this once on each team sheet (Team A / B / C).');
}

// ============================================================
// AUTO-FILL ON EDIT — install once with installTrigger()
// ============================================================

function installTrigger() {
  var triggers = ScriptApp.getProjectTriggers();
  for (var i = 0; i < triggers.length; i++) {
    if (triggers[i].getHandlerFunction() === 'onEditFillRow') {
      ScriptApp.deleteTrigger(triggers[i]);
    }
  }
  ScriptApp.newTrigger('onEditFillRow')
    .forSpreadsheet(SpreadsheetApp.getActiveSpreadsheet())
    .onEdit()
    .create();
  SpreadsheetApp.getUi().alert('Auto-fill trigger installed! Enter OS No + Year and the 4 columns fill automatically.');
}

function onEditFillRow(e) {
  var sheet = e.range.getSheet();
  if (sheet.getName() === DATA_SHEET) return;

  var row = e.range.getRow();
  if (row < 2) return;

  var main = sheet;
  var headers = main.getRange(1, 1, 1, main.getLastColumn()).getValues()[0];

  function findCol(patterns) {
    for (var i = 0; i < headers.length; i++) {
      var h = (headers[i] || '').toLowerCase().trim();
      for (var p = 0; p < patterns.length; p++) {
        if (h.indexOf(patterns[p]) >= 0) return i + 1; // 1-based
      }
    }
    return -1;
  }

  function colLetter(col) {
    var letter = '';
    while (col > 0) {
      var rem = (col - 1) % 26;
      letter = String.fromCharCode(65 + rem) + letter;
      col = Math.floor((col - 1) / 26);
    }
    return letter;
  }

  var osNoCol     = findCol(['os no', 'os_no', 'os number', 'offence no', 'number']);
  var yearCol     = findCol(['year', 'os year', 'os_year']);
  var caseTypeCol = findCol(['case type', 'casetype', 'case_type']);
  if (osNoCol < 0 || yearCol < 0) return;

  var editedCol = e.range.getColumn();
  if (editedCol !== osNoCol && editedCol !== yearCol && editedCol !== caseTypeCol) return;

  var onTeamSheet = STATUS_TEAMS.indexOf(sheet.getName()) >= 0;

  // A key cell was CLEARED on a team sheet -> team removed this case.
  // Wipe the row's data but KEEP the formula cells (status + lookups). The
  // status formula auto-returns "" once the key is gone. Stop here.
  // (To FIX a typo, type over the cell instead of deleting it.)
  if (onTeamSheet && (e.value === undefined || e.value === '') && e.oldValue !== undefined) {
    clearRowKeepFormulas_(main, row);
    return;
  }

  var osNoVal = main.getRange(row, osNoCol).getValue();
  var yearVal = main.getRange(row, yearCol).getValue();
  if (!osNoVal || !yearVal) return;

  var osL   = colLetter(osNoCol);
  var yearL = colLetter(yearCol);
  var typeL = caseTypeCol > 0 ? colLetter(caseTypeCol) : null;

  function makeFormula(lookupColNum) {
    var lookup = 'VLOOKUP(' + osL + row + '&"/"&' + yearL + row + ',' + dataRangeRef_() + ',' + lookupColNum + ',FALSE)';
    if (typeL) {
      return '=IFERROR(IF(' + typeL + row + '="OS",' + lookup + ',""),"")';
    }
    return '=IFERROR(' + lookup + ',"")';
  }

  var containsCol = findCol(['supposed', 'contain']);
  var passportCol = findCol(['passport']);
  var brCol       = findCol(['associated br', 'br no', 'br number']);
  var clearedCol  = findCol(['cleared', 'br item']);

  if (containsCol > 0) main.getRange(row, containsCol).setFormula(makeFormula(4));
  if (passportCol > 0) main.getRange(row, passportCol).setFormula(makeFormula(2));
  if (brCol > 0)       main.getRange(row, brCol).setFormula(makeFormula(5));
  if (clearedCol > 0)  main.getRange(row, clearedCol).setFormula(makeFormula(6));

  // --- warehouse lookups (lists ALL matching items for the OS/DR) ---
  var ssRef = e.source || SpreadsheetApp.getActiveSpreadsheet();
  if (ssRef.getSheetByName(WH_SHEET) && caseTypeCol > 0) {
    var ctLw = colLetter(caseTypeCol), numLw = colLetter(osNoCol), yrLw = colLetter(yearCol);
    for (var w = 0; w < WH_COLS.length; w++) {
      var wcCol = findCol([WH_COLS[w].hdr]);
      if (wcCol > 0) main.getRange(row, wcCol).setFormula(whFormula_(row, ctLw, numLw, yrLw, WH_COLS[w].col));
    }
  }

  // --- cross-sheet duplicate status (team sheets only) ---
  // Writes the LIVE status formula (instant in-browser) instead of computing
  // server-side, so it appears as fast as the lookup columns. OS and DR both.
  if (onTeamSheet) {
    var statusCol = findCol(['status']);
    var locCol = findCol(['location']);
    if (statusCol > 0 && caseTypeCol > 0) {
      var ctLs = colLetter(caseTypeCol), numLs = colLetter(osNoCol),
          yrLs = colLetter(yearCol), locLs = colLetter(locCol > 0 ? locCol : 7);
      main.getRange(row, statusCol).setFormula(
        buildStatusFormula_(row, sheet.getName(), ctLs, numLs, yrLs, locLs));
    }
  }
}
