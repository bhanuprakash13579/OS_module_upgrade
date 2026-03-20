# COPS Customs Application — Installation & Setup Guide

Version: 2.0 (Modernized)
Platform: Windows 10/11 (.exe) · Ubuntu/Debian Linux (.deb)
Architecture: Standalone desktop app with optional LAN multi-user access

---

## Table of Contents

1. [System Requirements](#1-system-requirements)
2. [Installation](#2-installation)
3. [First-Time Setup (Every New Installation)](#3-first-time-setup)
4. [Migrating Data from Old .mdb Database](#4-migrating-data-from-old-mdb)
5. [LAN Multi-User Setup (Multiple PCs)](#5-lan-multi-user-setup)
6. [Regular Backup Procedure](#6-regular-backup-procedure)
7. [Restoring from Backup](#7-restoring-from-backup)
8. [Troubleshooting](#8-troubleshooting)
9. [Security Notes](#9-security-notes)

---

## 1. System Requirements

### Master / Server PC (the one that holds the database)

| Item | Minimum |
|------|---------|
| OS | Windows 10 64-bit or Ubuntu 20.04+ |
| RAM | 4 GB |
| Disk | 2 GB free |
| Network | Wired LAN (if other PCs will connect) |

### Client PCs (LAN access — browser only, no installation needed)

| Item | Requirement |
|------|-------------|
| Browser | Chrome, Firefox, or Edge (any modern browser) |
| Network | Same physical LAN as the master PC |
| Installation | None — just open the browser |

---

## 2. Installation

### Windows (.exe)

1. Download `COPS-Setup-x64.exe` from the GitHub Releases page.
2. Run the installer — Windows may show a SmartScreen warning (click "More Info" → "Run Anyway").
3. The app installs to `C:\Program Files\COPS Customs`.
4. A desktop shortcut is created automatically.
5. Launch the app from the desktop shortcut.

> **Database location (Windows):**
> `C:\Users\<YourUser>\AppData\Roaming\gov.in.customs.cops\cops_br_database.db`

### Linux (.deb — Ubuntu/Debian)

```bash
# Install the .deb package
sudo dpkg -i cops-customs_2.0_amd64.deb

# If dependencies are missing
sudo apt-get install -f

# Launch
cops-customs
```

> **Database location (Linux):**
> `/home/<user>/.local/share/gov.in.customs.cops/cops_br_database.db`

---

## 3. First-Time Setup

Every new installation (on any machine) starts with an empty database and must
go through this one-time setup before anyone can log in.

### Step 1 — Open the Admin Panel

The admin panel is hidden. To access it:

1. Open the COPS app.
2. Click the **Settings** gear icon in the top-right corner **4 times quickly**.
3. A login screen appears titled "System Admin".

### Step 2 — Log In as System Admin

- **Username:** `sysadmin`
- **Password:** *(provided separately by the system administrator — not written here)*

### Step 3 — Register This Device

After logging in you will see **"Device Authorisation"** at the top.

- If it shows "Not registered" → click **"Register This Device"**.
- The button disappears once registration succeeds.
- This ties the database to this specific machine. The app will not work if the
  database file is copied to another computer (security feature).

### Step 4 — Create User Accounts

In the **"User Management"** section:

1. Click **"Add User"**.
2. Fill in:
   - **Login ID** — the username they will type at login (e.g. `sdo.officer@customs`)
   - **Full Name** — display name
   - **Designation** — their official title
   - **Role** — choose one:
     - `SDO` — for Superintendent (SDO Module access only)
     - `DC` — for Deputy Commissioner (Adjudication Module)
     - `AC` — for Assistant Commissioner (Adjudication Module)
   - **Initial Password** — set a temporary password; the user can change it after first login
3. Click **"Create User"**.
4. Repeat for each user.

> You need at least one SDO user and one DC or AC user before the modules
> can be used.

### Step 5 — Sign Out of Admin Panel

Click **"Sign Out"** in the top-right of the admin panel. The admin session
exists only in memory — it is automatically cleared when the app is closed.

---

## 4. Migrating Data from Old .mdb Database

If you have data in the old VB6/Access database (`.mdb` file), import it
before users start entering new data.

### Method A — Direct MDB Import (Recommended)

This method reads the `.mdb` file directly. No conversion needed.

**Prerequisite (Linux only):** install mdbtools

```bash
sudo apt-get install mdbtools
```

**Steps:**

1. Open the Admin Panel (gear × 4 → login as sysadmin).
2. Scroll to **"Import Directly from .mdb File"**.
3. Enter the full file path to the `.mdb` file, e.g.:
   - Linux: `/home/bhanu/Documents/analyze/cops_br_database.mdb`
   - Windows: `C:\Users\bhanu\Documents\cops_br_database.mdb`
4. Click **"Start MDB Import"**.
5. Wait — a 400 MB file takes approximately 3–5 minutes.
6. The result shows how many cases and items were inserted vs. skipped.

> Safe to re-run: duplicate records are always skipped automatically.

### Method B — CSV Upload (If .mdb is not accessible)

If the .mdb file is on a different computer, export the two tables manually
from MS Access, then upload the CSV files.

**Export from MS Access:**
1. Open the `.mdb` in MS Access.
2. Right-click `cops_master` → Export → Text File → CSV format.
3. Repeat for `cops_items`.

**Upload steps:**
1. Open Admin Panel → scroll to **"Import from Old Database (.mdb)"**.
2. Under **"Step 1 — cops_master.csv"**, select the master CSV and click Upload.
3. Under **"Step 2 — cops_items.csv"**, select the items CSV and click Upload.

---

## 5. LAN Multi-User Setup (Multiple PCs)

This setup allows other computers on the same physical LAN to access the
system through a web browser — **no installation required on client PCs**.

```
┌─────────────────────────────────────┐      ┌──────────────────────────────┐
│  MASTER PC (server)                 │      │  CLIENT PC (any browser)     │
│                                     │─────▶│                              │
│  COPS app installed & running       │ LAN  │  Chrome / Firefox / Edge     │
│  IP: 192.168.1.100                  │ wire │  Navigate to:                │
│  Database lives here                │      │  http://192.168.1.100:8000   │
│  All data stored here               │      │                              │
└─────────────────────────────────────┘      └──────────────────────────────┘
```

### On the Master PC

1. **Find the master PC's IP address:**

   - Windows: open Command Prompt → type `ipconfig` → note the IPv4 address
     (usually looks like `192.168.x.x` or `10.x.x.x`)
   - Linux: open Terminal → type `ip addr show` → note the `inet` address

2. **Start the COPS app as usual.** The backend automatically listens on all
   network interfaces (port 8000), so LAN clients can connect.

3. **(Windows only — firewall rule):** Allow port 8000 through Windows Firewall:
   ```
   Windows Defender Firewall → Advanced Settings →
   Inbound Rules → New Rule → Port → TCP → 8000 → Allow → Name: COPS
   ```

   Or run this in an Administrator Command Prompt:
   ```cmd
   netsh advfirewall firewall add rule name="COPS App" dir=in action=allow protocol=TCP localport=8000
   ```

### On Each Client PC

1. Open Chrome, Firefox, or Edge.
2. In the address bar type: `http://192.168.1.100:8000`
   *(replace `192.168.1.100` with the actual master PC IP)*
3. The COPS login page loads — log in with a normal user account (SDO/DC/AC).

> **No installation, no drivers, no setup needed on client PCs.**

### Important Notes for LAN Mode

| Topic | Detail |
|-------|--------|
| Who has the database | Only the master PC — all clients read/write to the master's DB over the network |
| Concurrent users | Supported — SQLite handles multiple simultaneous readers; writes are serialized automatically |
| Internet access required | No — everything stays within the local network |
| Security | Non-LAN IPs are blocked by the server. Only private IP ranges (192.168.x.x, 10.x.x.x, 172.16.x.x) are allowed |
| If master PC is off | Client PCs cannot access the app — the server must be running |
| Bookmarking | Clients can bookmark `http://192.168.1.100:8000` for quick access |

---

## 6. Regular Backup Procedure

**Recommended frequency:** once a day, at end of shift.

1. Open Admin Panel (gear × 4 → sysadmin login).
2. Scroll to **"Download Full Backup"**.
3. Click **"Download Backup ZIP"**.
4. A file named `cops_full_backup_YYYY-MM-DD.zip` is downloaded.
5. Copy this file to:
   - A USB drive, **or**
   - A shared network folder, **or**
   - An external hard disk

> The ZIP contains two CSV files: `cops_master.csv` and `cops_items.csv`.
> These are human-readable and can be opened in Excel if needed.

---

## 7. Restoring from Backup

### After a System Crash or Reinstallation

1. Install the COPS app on the new machine (see Section 2).
2. Complete First-Time Setup: register device, create users (Section 3).
3. Open Admin Panel → scroll to **"Restore from Backup ZIP"**.
4. Select the backup `.zip` file and click **"Restore ZIP"**.
5. Wait for the confirmation message showing how many records were restored.

> Only missing records are inserted — if some data already exists it will not
> be overwritten. Safe to restore multiple backup ZIPs in sequence.

### After Importing Old MDB + Running the App

If you want to bring in both old data and a recent backup:

1. Import the old `.mdb` first (Section 4).
2. Then restore the latest backup ZIP (Section 7).

Duplicates from both sources are automatically detected and skipped.

---

## 8. Troubleshooting

### App shows blank white page on launch

The backend (Python server) is still starting up. Wait 5–10 seconds and
refresh. If it persists, close and reopen the app.

### "This device is not authorised" error

The device has not been registered. Open Admin Panel → Device Authorisation →
click "Register This Device".

### LAN client gets "Unable to connect" in browser

1. Confirm the master PC's COPS app is open and running.
2. Check that you typed the correct IP address (use `ipconfig` / `ip addr` to verify).
3. On Windows, check that the firewall rule for port 8000 exists (see Section 5).
4. Try pinging the master PC: open Command Prompt and type `ping 192.168.1.100`.

### MDB import fails on Windows

`mdb-export` (mdbtools) is a Linux tool. On Windows, use Method B (CSV upload)
instead — export the tables from MS Access manually as CSV files.

### Forgot the sysadmin password

The sysadmin password is a bcrypt hash compiled into the binary. It cannot be
"reset" through the app. Contact the original developer to rebuild the app with
a new password hash.

### Port 8000 already in use

Another application is using port 8000. Either close it, or check the app logs.
The COPS app automatically tries to free port 8000 on startup.

---

## 9. Security Notes

| What is protected | How |
|-------------------|-----|
| Admin password | bcrypt hash — cannot be reversed even from the binary |
| JWT tokens | Machine-specific (tied to MAC address + hostname) — tokens from one machine are invalid on another |
| Database binding | `machine.key` ties the database to one specific machine |
| Network access | Only LAN/private IPs allowed — internet access is blocked by the server |
| User passwords | bcrypt hashed — not stored in plaintext anywhere |

### What the sysadmin should do after first setup

1. **Change the admin password** — rebuild the app with a new `_ADMIN_PWD_HASH`
   before deploying to production.
2. **Keep backup ZIPs in a physically secure location** — they contain all case data.
3. **Do not share the sysadmin password** — it gives full control over all user
   accounts and data.

---

*Last updated: March 2026*
