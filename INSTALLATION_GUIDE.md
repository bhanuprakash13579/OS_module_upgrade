# COPS Customs — Complete Operations Manual

Version: 2.0 (Modernized)
Last updated: March 2026

---

## Table of Contents

1. [What This App Does](#1-what-this-app-does)
2. [System Requirements](#2-system-requirements)
3. [Download the Application](#3-download-the-application)
4. [Installation by Platform](#4-installation-by-platform)
5. [First-Time Setup](#5-first-time-setup)
6. [Feature Guide](#6-feature-guide)
7. [Admin Panel Reference](#7-admin-panel-reference)
8. [Backup & Restore](#8-backup--restore)
9. [LAN Multi-User Setup](#9-lan-multi-user-setup)
10. [App Auto-Updater](#10-app-auto-updater)
11. [Migrating Data from Old .mdb Database](#11-migrating-data-from-old-mdb-database)
12. [Troubleshooting](#12-troubleshooting)
13. [Security Notes](#13-security-notes)

---

## 1. What This App Does

COPS is a case management system for Customs officers. It handles the complete lifecycle of an Offence Sheet (OS):

| Module | Who Uses It | What It Does |
|--------|-------------|--------------|
| **SDO Module** | Superintendent (SDO) | Create and manage Offence Sheets — record seized goods, calculate duty, generate OS print |
| **Adjudication Module** | DC / AC | Adjudicate cases — record hearings, rulings, and final orders |
| **Query / Print** | Any user | Search cases, view case history, print the official OS document |
| **Admin Panel** | Sysadmin only | Manage users, backups, device registration, settings, and templates |

**Data lives on one PC (the Master PC).** Other PCs on the same LAN access it through a web browser — no installation needed on those PCs.

---

## 2. System Requirements

### Master PC (holds the database and runs the server)

| Item | Minimum |
|------|---------|
| OS | Windows 10/11 64-bit · Ubuntu 20.04+ · macOS 12+ |
| RAM | 4 GB |
| Disk | 2 GB free |
| Network | Wired LAN recommended (if serving other PCs) |

### Client PCs (browser-only, no installation)

| Item | Requirement |
|------|-------------|
| Browser | Chrome, Firefox, or Edge (any modern browser) |
| Network | Same physical LAN or Wi-Fi as the master PC |

---

## 3. Download the Application

The app is built automatically by GitHub Actions every time a new version is pushed. You do **not** need to compile anything yourself.

### Steps to download

1. Open a browser and go to your GitHub repository.
2. Click the **Actions** tab at the top.
3. Click the latest successful run (green ✓) for the workflow named **"Build Desktop App (Tauri)"**.
4. Scroll to the **Artifacts** section at the bottom.
5. Download the file for your platform:

| Platform | File to download | What it is |
|----------|-----------------|------------|
| Windows | `cops-desktop-windows` | Contains `.msi` installer + `.exe` |
| Linux (Ubuntu/Debian) | `cops-desktop-linux` | Contains `.deb` package + `.AppImage` |
| macOS | `cops-desktop-macos` | Contains `.dmg` disk image |

> **Note:** If you only need the background server (for advanced LAN deployments without the desktop app), download from the **"Build COPS Server"** workflow instead — it produces a single `cops-server-windows.exe` or `cops-server-linux` binary.

---

## 4. Installation by Platform

### Windows

1. Unzip the downloaded artifact.
2. Run `COPS-Setup-x64.msi` (recommended) or `COPS-Setup-x64.exe`.
3. Windows SmartScreen may appear — click **"More Info"** → **"Run Anyway"**. This is normal for unsigned builds.
4. Follow the installer steps. The app installs to `C:\Program Files\COPS Customs`.
5. A desktop shortcut is created. Launch the app from it.

> **Database location (Windows):**
> `C:\Users\<YourUsername>\AppData\Roaming\gov.in.customs.cops\cops_br_database.db`

### Linux (Ubuntu / Debian)

```bash
# Install the .deb package
sudo dpkg -i cops-customs_2.0_amd64.deb

# Fix missing dependencies if any
sudo apt-get install -f

# Launch from the application menu or terminal
cops-customs
```

Or use the portable `.AppImage` (no installation needed):
```bash
chmod +x COPS-Customs-2.0.AppImage
./COPS-Customs-2.0.AppImage
```

> **Database location (Linux):**
> `/home/<username>/.local/share/gov.in.customs.cops/cops_br_database.db`

### macOS

1. Open the downloaded `.dmg` file.
2. Drag the **COPS Customs** icon into your **Applications** folder.
3. On first launch, macOS Gatekeeper may block it — go to **System Settings → Privacy & Security** → scroll down → click **"Open Anyway"** next to the COPS entry.
4. Launch from the Applications folder or Launchpad.

> **Database location (macOS):**
> `/Users/<username>/Library/Application Support/gov.in.customs.cops/cops_br_database.db`

---

## 5. First-Time Setup

Every fresh installation starts with an empty database. Complete these steps before users log in.

### Step 1 — Open the Admin Panel

The admin panel is intentionally hidden. To access it:

1. Open the COPS app.
2. Click the **gear icon** (⚙) in the top-right corner **4 times quickly** in succession.
3. A login screen titled "System Administration" appears.

### Step 2 — Log In as Sysadmin

- **Username:** `sysadmin`
- **Password:** *(the password set when the app was built — provided separately by the developer)*

> If you are the developer: the password is set by the `ADMIN_PWD_HASH` GitHub secret. See [docs/security_deployment_guide.md](docs/security_deployment_guide.md) for how to set or change it.

### Step 3 — Register This Device

At the top of the admin panel you will see **"Device Registration"**.

- If it shows **"Not Registered"** → click **"Register This Device"**.
- This writes a `machine.key` fingerprint file next to the database.
- The app is now locked to this specific PC. If the database file is copied to another machine, it will not work (security feature).
- The button disappears after successful registration.

### Step 4 — Create User Accounts

Go to the **User Management** section:

1. Click **"Add User"**.
2. Fill in:
   - **Login ID** — the ID they type at the login screen (e.g. `sdo.kumar`)
   - **Full Name** — displayed on documents
   - **Designation** — their official designation title
   - **Role** — select one:
     - `SDO` — access to SDO / Offence Sheet module
     - `DC` — access to Adjudication module (Deputy Commissioner)
     - `AC` — access to Adjudication module (Assistant Commissioner)
   - **Initial Password** — set a temporary password; they can change it after logging in
3. Click **"Create User"**.

> At minimum you need one `SDO` user and one `DC` or `AC` user before the modules can be used.

### Step 5 — Sign Out

Click **"Sign Out"** in the top-right. The admin session is memory-only and clears automatically when the app is closed.

---

## 6. Feature Guide

### 6.1 SDO Module — Creating an Offence Sheet

The SDO module is where cases begin. A Superintendent creates an OS when goods are seized.

**How to create a new OS:**

1. Log in as an SDO user.
2. Click **"New Offence Sheet"** (or the + button).
3. Fill in the case header:
   - OS Number, OS Year, Date, Location Code
   - Passenger details: Name, Passport No., Nationality, Port of Arrival, Flight details
4. Under **Items**, add each seized item:
   - Description (free-text) — the classifier will suggest the duty type automatically (see §6.4)
   - Quantity, Unit, Value
   - Duty Type and Duty Rate are auto-filled; you can adjust if needed
5. The **total duty** and **total payable** are calculated automatically.
6. Fill in officer details and remarks.
7. Click **"Save"**.

**Printing the OS:**
- Open the saved case → click **"Print OS"**.
- The official OS document opens in a print-ready view with all headings and clauses.
- Use your browser's Print (Ctrl+P) to send to the printer.

### 6.2 Adjudication Module

Used by DC/AC officers to record the adjudication hearing and final order.

**How to adjudicate a case:**

1. Log in as a DC or AC user.
2. Go to **"Adjudication"** → search for the OS by OS number or passenger name.
3. Open the case → click **"Start Adjudication"**.
4. Fill in hearing details, confiscation order, fine amount, and officer remarks.
5. Save. The case status changes to "Adjudicated".

### 6.3 Query & Print

Any logged-in user can search and view all cases.

- **Search** by OS number, year, passenger name, passport, or date range.
- **View** the full case details including items, duty calculation, and adjudication results.
- **Print** the official OS document from the search results.

### 6.4 Smart Item Classifier

When entering an item description in the SDO module, the app automatically suggests the correct **duty type** when you move to the next field (on blur).

- The classifier matches your free-text description against known item keywords.
- If a match is found, Duty Type is filled in automatically.
- You can always override the suggestion.
- This saves time and reduces errors from manually looking up duty codes.

### 6.5 OS Print Template Editor

The printed OS document has headings, officer designations, clauses, and other static text that may need to change when laws or departmental guidelines change.

**How to edit the OS template (for future law changes):**

1. Open Admin Panel (gear × 4 → sysadmin login).
2. Go to **"OS Print Template"**.
3. You will see a list of all editable fields — each has a **Key**, a current **Value**, and an **Effective From** date.
4. To change a heading or clause:
   - Click the field you want to edit.
   - Change the value.
   - Set the **Effective From** date to today or a future date.
   - Click **"Save"**.
5. The app uses **the most recent version** whose Effective From date is on or before today's date. Old versions are kept in history and are never deleted.

**Why this design?**
- If a new law takes effect on 1 April, you can enter the new wording now with `Effective From = 2026-04-01` — it activates automatically on that date without any redeployment.
- Historical OS prints will still show the old wording (because they were printed under the old law). Only new prints after the effective date use the new wording.
- This means the system is self-updating for legal changes — no developer needed.

**What fields are editable:**

| Field Key | What it controls |
|-----------|-----------------|
| `header_line1` | First line of the OS header (department name) |
| `header_line2` | Second line (commissionerate) |
| `header_line3` | Third line (division/range) |
| `office_address` | Full office address block |
| `supdt_designation` | SDO officer designation line on the print |
| `adjn_designation` | Adjudicating officer designation line |
| `goods_clause_default` | Default legal clause for goods confiscation |
| `penalty_clause_default` | Default legal clause for penalty |
| *(and more...)* | All static text on the OS print is editable |

### 6.6 Baggage Rules & Special Allowances

The duty calculation uses configurable rules for:
- **Free baggage allowance** — the duty-free value limit per passenger
- **Special item allowances** — specific items that have their own allowance limits (e.g. gold, electronics)

These are versioned the same way as the template: each rule has an **Effective From** date. If the Finance Ministry changes duty-free limits in the Budget, you just add new entries with the new effective date.

**How to update baggage rules:**

1. Admin Panel → **"Baggage Rules Config"**.
2. Click **"Add New Rule"**.
3. Set the rule key (e.g. `general_free_allowance`), new value, and Effective From date.
4. Save. The new value takes effect automatically on the set date.

### 6.7 Legal Statutes Manager

Used to manage the list of offence keywords and their associated legal provisions.

- Each statute has a **keyword** (e.g. `gold`, `foreign_currency`), a **display name**, and the legal clauses to include in the OS print for that item type.
- When an item is classified (§6.4), its keyword drives which legal clause appears on the printed OS.
- Add new statutes or update existing ones as laws change — no recompilation needed.

---

## 7. Admin Panel Reference

Access: gear icon × 4 → sysadmin login.

| Section | What You Can Do |
|---------|----------------|
| **Device Registration** | Register this PC; view machine fingerprint |
| **User Management** | Add, edit, deactivate users; reset passwords |
| **Allowed Devices** | (LAN mode) Whitelist slave PC IP addresses |
| **OS Print Template** | Edit all print headings and legal clauses |
| **Baggage Rules Config** | Update free allowance limits |
| **Special Item Allowances** | Per-item duty-free limits |
| **Legal Statutes** | Add/edit offence keywords and legal clauses |
| **Feature Flags** | Enable/disable API access; set session timeout |
| **Shift Timings** | Set day/night shift boundary hours |
| **Margin Settings** | Adjust print top-margin for your printer |
| **Backup & Restore** | Full DB backup, ZIP backup, restore options |
| **Legacy Import** | Import from old .mdb Access database |
| **App Updates** | Check for and install app updates (desktop only) |

---

## 8. Backup & Restore

### Understanding the two backup types

| | Full Database Backup | Settings + Cases ZIP Backup |
|--|---------------------|-----------------------------|
| **What it contains** | Everything — a complete copy of the entire database file | All case data + all settings/config as CSV files |
| **File type** | `.db` SQLite file | `.zip` containing CSV files |
| **Use when** | Disaster recovery — the PC died or DB is corrupted | Regular daily backup; or restoring to a new installation |
| **Restore behaviour** | **Replaces the entire database** — any data added after the backup was taken will be lost | **Additive only** — inserts missing records, never overwrites existing data |
| **Danger level** | ⚠ Destructive | ✅ Safe |

**Recommendation:** Do the **ZIP backup** daily. Do the **Full DB backup** occasionally (weekly, or before upgrading the app).

---

### 8.1 Full Database Backup (Recommended for disaster recovery)

1. Open Admin Panel.
2. Scroll to **"Full Database Backup"** (green border section).
3. Click **"Download Full DB Backup"**.
4. A `.db` file is downloaded — store it on a USB drive or network share.

The backup is taken using SQLite's Online Backup API with WAL flush, so it is safe to run while the app is in use.

### 8.2 Full Database Restore (⚠ Destructive)

> **Warning:** This replaces your entire database. Any cases entered after the backup was taken will be permanently lost. Only use this for disaster recovery.

1. Open Admin Panel.
2. Scroll to **"Full DB Restore"** (red border section).
3. Click **"Choose file"** and select a `.db` file from a previous Full DB Backup.
4. Click **"Restore Full DB"**.
5. A confirmation dialog appears — read it and click OK only if you are sure.
6. The app will restart after restore.

### 8.3 Settings + Cases ZIP Backup (Recommended for daily use)

This backup includes:
- All Offence Sheet cases (`cops_master`, `cops_items`)
- All admin settings (`print_template_config`, `baggage_rules_config`, `special_item_allowances`, `feature_flags`, `shift_timing_master`, `margin_master`)
- All users
- All legal statutes
- All other transaction tables (BR, DR, Fuel, Warehouse, MHB, Appeal, Revenue, etc.)

**Steps:**
1. Open Admin Panel.
2. Scroll to **"Settings + Cases Backup (ZIP)"**.
3. Click **"Download Backup ZIP"**.
4. A `.zip` file named `cops_full_backup_YYYY-MM-DD.zip` is downloaded.
5. Copy to USB, network share, or cloud storage.

The CSV files inside the ZIP are human-readable and can be opened in Excel for reference.

### 8.4 ZIP Restore (Safe — additive only)

1. Open Admin Panel.
2. Scroll to **"Settings + Cases Backup (ZIP)"** → Restore section.
3. Click **"Choose file"** and select a `.zip` backup file.
4. Click **"Restore ZIP"**.
5. The result shows how many records were inserted vs skipped (skipped = already existed).

**Safe to run multiple times** — duplicates are always detected and skipped.

### 8.5 Restoring after a system crash or new installation

1. Install the app on the new machine (Section 4).
2. Complete First-Time Setup — register device, create users (Section 5).
3. **Option A (Recommended):** Restore from Full DB Backup (§8.2) — you get everything back instantly.
4. **Option B:** Restore from ZIP Backup (§8.4) — safer if some data was entered after the backup.

---

## 9. LAN Multi-User Setup

Multiple PCs on the same physical network can use the system simultaneously. The Master PC runs the app and holds the database; client PCs just need a web browser.

```
┌───────────────────────────────────┐        ┌────────────────────────────────┐
│  MASTER PC (server)               │        │  CLIENT PC (browser only)      │
│                                   │──LAN──▶│                                │
│  COPS app installed & running     │        │  Chrome / Firefox / Edge       │
│  IP: 192.168.1.100                │        │  Navigate to:                  │
│  Database lives here              │        │  http://192.168.1.100:8000     │
└───────────────────────────────────┘        └────────────────────────────────┘
```

### On the Master PC

1. **Find the master PC's IP address:**
   - Windows: open Command Prompt → `ipconfig` → note the IPv4 address (e.g. `192.168.1.100`)
   - Linux/macOS: open Terminal → `ip addr show` or `ifconfig` → note the `inet` address

2. **Start the COPS app normally.** The backend listens on all interfaces automatically.

3. **(Windows only)** Allow port 8000 through Windows Firewall:
   ```
   Windows Defender Firewall → Advanced Settings →
   Inbound Rules → New Rule → Port → TCP → 8000 → Allow → Name: COPS
   ```
   Or paste this into an Administrator Command Prompt:
   ```cmd
   netsh advfirewall firewall add rule name="COPS App" dir=in action=allow protocol=TCP localport=8000
   ```

4. **Whitelist each client PC's IP** in Admin Panel → Allowed Devices (required in Production mode).

### On Each Client PC

1. Open a browser (Chrome, Firefox, or Edge).
2. Type: `http://192.168.1.100:8000` *(use the master PC's actual IP)*
3. Log in with an SDO/DC/AC account.

> No installation, no drivers, no setup needed on client PCs.

### LAN Mode Notes

| Topic | Detail |
|-------|--------|
| Database location | Master PC only — clients read/write over the network |
| Concurrent users | Supported — SQLite handles multiple simultaneous connections |
| Internet required | No — everything stays on the local network |
| Security | Non-LAN IPs are blocked automatically; only 192.168.x.x, 10.x.x.x, 172.16.x.x allowed |
| If master PC is off | Clients cannot access the app |

---

## 10. App Auto-Updater

The desktop app (Tauri) can check for updates and install them without losing any data.

### How updates work

- Your database is stored in the OS user data folder (not inside the app installation directory).
- When an update installs, it replaces only the app binary — the database file is never touched.
- All your cases, settings, and user accounts survive every update.

### Checking for updates manually

1. Open Admin Panel.
2. Scroll to **"App Updates"** section (desktop app only — not visible in browser mode).
3. Click **"Check for Updates"**.
4. If an update is available, a message shows the new version.
5. Click **"Download & Install Update"**.
6. The update downloads, installs, and the app relaunches automatically.

### Automatic update check

The app checks for updates automatically in the background when it starts. If an update is available, you will be notified.

### If updates are not working

Updates require:
- The Tauri updater to be configured with valid signing keys (`pubkey` in `tauri.conf.json`)
- A `latest.json` file to be published at the configured endpoint URL (your GitHub Releases)

If you are the developer setting this up for the first time, see [docs/security_deployment_guide.md](docs/security_deployment_guide.md) → "Tauri Auto-Updater Setup" section.

---

## 11. Migrating Data from Old .mdb Database

If you have historical case data in the old VB6/MS-Access `.mdb` database, import it before users start entering new data.

### Method A — Direct MDB Import (Recommended, Linux/macOS only)

**Prerequisite:**
```bash
# Linux
sudo apt-get install mdbtools

# macOS
brew install mdbtools
```

**Steps:**
1. Open Admin Panel.
2. Scroll to **"Import Directly from .mdb File"**.
3. Enter the full path to the `.mdb` file:
   - Linux: `/home/bhanu/Documents/cops_br_database.mdb`
   - macOS: `/Users/bhanu/Documents/cops_br_database.mdb`
4. Click **"Start MDB Import"**.
5. A 400 MB database takes approximately 3–5 minutes. The result shows how many cases were imported.

> Safe to re-run: duplicate records are always skipped.

### Method B — CSV Upload (Windows users or if .mdb is on another PC)

**Export from MS Access:**
1. Open the `.mdb` file in Microsoft Access.
2. Right-click `cops_master` table → Export → Text File → CSV format.
3. Repeat for `cops_items` table.

**Upload:**
1. Open Admin Panel → **"Legacy Import"** section.
2. Select `cops_master.csv` → click Upload.
3. Select `cops_items.csv` → click Upload.

---

## 12. Troubleshooting

### App shows blank white page on launch

The Python backend is still starting up (takes 3–8 seconds). Wait and refresh. If it persists after 30 seconds, close and reopen the app.

### "This device is not authorised" error

The device fingerprint has not been registered. Open Admin Panel → Device Registration → click "Register This Device".

### "Your device is not on the approved access list" (LAN clients)

The client PC's IP has not been whitelisted. Open Admin Panel on the master PC → Allowed Devices → Add the client's IP.

### LAN client browser shows "Unable to connect"

1. Confirm the master PC's COPS app is open and running.
2. Verify the correct IP address (`ipconfig` on master PC).
3. Windows only: check the firewall rule for port 8000 exists (see Section 9).
4. Test connectivity: `ping 192.168.1.100` from the client PC.

### Forgot the sysadmin password

The password is a bcrypt hash compiled into the app binary. It cannot be recovered from the app. The developer must:
1. Generate a new bcrypt hash.
2. Update the `ADMIN_PWD_HASH` GitHub secret.
3. Trigger a new GitHub Actions build.
4. Download and deploy the new binary.

See [docs/security_deployment_guide.md](docs/security_deployment_guide.md) for exact steps.

### MDB import fails on Windows

`mdbtools` is not available on Windows. Use Method B (CSV export from MS Access) instead.

### Port 8000 already in use

Another application is using port 8000. Either close it, or check the app startup logs. The COPS app automatically attempts to free port 8000 on startup if a previous instance is still running.

### Update check fails (shows error)

The updater requires valid signing keys and a reachable endpoint. This only works if the developer has configured `tauri.conf.json` with actual keys and a real GitHub Releases endpoint. Contact the developer.

### Print layout is wrong (too high/low on paper)

Open Admin Panel → Margin Settings → adjust `br_top_margin` or `dr_top_margin` (in inches). Print a test page after each adjustment.

---

## 13. Security Notes

| What is protected | How |
|-------------------|-----|
| Sysadmin password | bcrypt hash compiled into binary — cannot be reversed |
| User passwords | bcrypt hashed in the database — not stored in plaintext |
| JWT tokens | Derived from the machine's MAC address + hostname — tokens from one machine are invalid on any other |
| Database binding | `machine.key` ties the database to one specific PC |
| Network access | Only LAN private IPs allowed (192.168.x.x, 10.x.x.x, 172.16.x.x) — internet access is blocked at the server level |
| Admin panel | Only accessible from `127.0.0.1` (the master PC itself) — no LAN client can reach it |

### What the sysadmin should do after deployment

1. **Change the admin password** before going to production — rebuild with a new hash (see security guide).
2. **Keep backup files in a physically secure location** — they contain all case data in readable CSV format.
3. **Do not share the sysadmin password** — it gives full control over all data and user accounts.
4. **Register the device** on first setup — this ties the database to the physical machine.
5. **Whitelist only the PCs that need access** — do not leave the allowed-devices list empty in production.

---

*For developer-level documentation (GitHub secrets, build configuration, Tauri signing keys, CI/CD): see [docs/security_deployment_guide.md](docs/security_deployment_guide.md)*
