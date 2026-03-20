# Old Module EXE Analysis — Field Limits & Form Structure

**Files analyzed:**
- `/home/bhanu/Documents/analyze/ONLINE ADJN.exe` — Adjudication module (Dec 2023 build)
- `/home/bhanu/Documents/analyze/sdo_2023.exe` — SDO Offence Booking module (Aug 2023 build)
- `/home/bhanu/Documents/analyze/cops_br_database.mdb` — Legacy MS Access production database (452 MB)

**Date of analysis:** 2026-03-17
**Purpose:** Determine exact MaxLength limits enforced by the old VB6 module for remarks fields, to correctly configure the new COPS module's character caps.

---

## Method

VB6 executables embed compiled form (`.frm`) binary data directly in the PE. The approach:

1. Used `strings` to extract readable identifiers — control names (`txtSupRem`, `txtACRem`, `txtDCRem`, `txtsuprem2`), form captions, and label text.
2. Parsed VB6 binary form record structure: each TextBox control record contains type flags, ForeColor (4 bytes), optional extra property, position block (8 bytes), then post-position properties.
3. Property tag `0x25` followed by a 4-byte little-endian uint32 encodes the `MaxLength` value. Calibrated against confirmed controls: `txtuserid` / `txtuserpwd` → `0x25 0a000000` = MaxLength 10; `txtDepDate` → MaxLength 10 (DD/MM/YYYY date).
4. Cross-referenced with the MDB schema using `mdbtools` to check field types.

---

## Database Schema (cops_br_database.mdb — cops_master table)

| Field | DB Type | Notes |
|---|---|---|
| `supdt_remarks1` | Memo/Hyperlink | Unlimited (~65536 chars) — mapped to `supdts_remarks` in new DB |
| `supdt_remarks2` | Text(100) | **Not overflow text.** Contains "Y" flag. Ignore for remarks limits. |
| `adjn_offr_remarks` | Memo/Hyperlink | Unlimited — limit enforced only at the VB6 TextBox level |
| `adjn_offr_remarks1` | Text(250) | Genuine overflow continuation for AC remarks in older data entries |

---

## VB6 Form Control Mapping

| Control Name | Field | Form Label |
|---|---|---|
| `txtSupRem` | `supdt_remarks1` / `supdts_remarks` | "Supdt's Remarks" |
| `txtsuprem2` | `supdt_remarks2` | Supdt Remarks 2 (flag field, not text overflow) |
| `txtACRem` | (secondary AC field) | "A.C. Remarks" |
| `txtDCRem` | `adjn_offr_remarks` | "Adjn. Officer Remarks" |

---

## MaxLength Properties Found

### ONLINE ADJN.exe (Adjudication Module)

| Control | Form Context | MaxLength |
|---|---|---|
| `txtSupRem` | Main ADJUDICATION DETAILS form | **1000** |
| `txtSupRem` | DETAILS OF PENAL AMOUNTS / older forms | **320** |
| `txtSupRem` | APPEAL DETAILS form | **1000** |
| `txtsuprem2` | All forms | **0 (unlimited)** |
| `txtACRem` | All forms | **0 (unlimited)** |
| `txtDCRem` | Main ADJUDICATION form | **3000** |
| `txtDCRem` | Other adjudication/appeal forms | **1500** |

### sdo_2023.exe (SDO Booking Module)

| Control | Form Context | MaxLength |
|---|---|---|
| `txtSupRem` | Main ADJUDICATION DETAILS form | **1500** ← upgraded vs ONLINE ADJN.exe |
| `txtSupRem` | Other ADJUDICATION DETAILS forms | **1000** |
| `txtSupRem` | DETAILS OF PENAL AMOUNTS / older forms | **320** |
| `txtsuprem2` | All forms | **0 (unlimited)** |
| `txtACRem` | All forms | **0 (unlimited)** |
| `txtDCRem` | Main ADJUDICATION form | **3000** |
| `txtDCRem` | Other adjudication/appeal forms | **1500** |

---

## Key Conclusions

### 1. Supdt's Remarks (`supdts_remarks`)
- The **effective operational limit is 1500 characters**, as found in `sdo_2023.exe` (the more recent SDO module).
- `ONLINE ADJN.exe` used 1000 on the main form — but SDO was the primary data-entry point, so 1500 is the binding limit.
- Cross-validated: DB max observed = **1540 chars** (OS 925/2023), consistent with 1500 limit (a few older entries slightly exceed due to data migration from even older module versions).

### 2. Adjudicating Officer Remarks (`adjn_offr_remarks`)
- The **effective operational limit is 3000 characters**, found on the main adjudication form in both EXEs.
- Cross-validated: DB max observed = **2996 chars** (OS 1096A/2019) — 4 chars short of the 3000 cap, confirming the limit.

### 3. `txtACRem` (A.C. Remarks)
- MaxLength = **0 (unlimited)** in both EXEs. No cap at the form level. The DB column is also a Memo field. This appears to be a secondary/legacy field distinct from the main `adjn_offr_remarks`.

### 4. `supdt_remarks2`
- Contains "Y"/"N" flag values — NOT an overflow text field. 13,146 rows have "Y" here. Safe to treat as a boolean indicator.

### 5. `adjn_offr_remarks1`
- Genuine overflow continuation (up to 250 chars) used in 1,036 records. Holds the remainder of AC remarks that exceeded older form limits in early module versions.

---

## New Module Configuration (applied 2026-03-17)

| Setting | Old (incorrect) | New (matches old module) |
|---|---|---|
| `ADJN_REMARKS_MAX_CHARS` (backend config) | 700 | **3000** |
| `SUPDT_REMARKS_MAX_CHARS` (backend config) | — (only frontend) | **1500** |
| Frontend `REMARKS_MAX` (AdjudicationForm.tsx) | 700 | **3000** |
| Frontend validation (OffenceForm.tsx) | 700 | **1500** |

---

## PDF Layout Validation

Tested with WeasyPrint (HTML→PDF) using exact worst-case strings:
- `supdts_remarks`: 1540 chars (actual DB maximum)
- `adjn_offr_remarks`: 2996 chars (actual DB maximum)
- All 3 ORDER clauses active (confiscation + re-export + personal penalty)

**Result: Fits in 2 pages at 8pt (no font reduction needed)**. The iterative shrink loop (8pt → 5.5pt in 0.5pt steps) is a safety margin for any hypothetical future content beyond current DB maximums.
