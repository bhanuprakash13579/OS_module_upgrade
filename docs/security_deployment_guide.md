# COPS OS Module — Security & Deployment Guide

## Security Audit Summary

Your app already has **6 layers of security** built in. Here's what each layer does:

| # | Layer | File | What It Does |
|---|-------|------|-------------|
| 1 | **LAN-Only** | `device.py` → `is_lan_ip()` | Blocks ALL connections from outside private LAN ranges (10.x, 172.16.x, 192.168.x). Internet access is impossible. |
| 2 | **Device Binding** | `device.py` → `machine.key` | The app writes an HMAC fingerprint (MAC address + hostname) to `machine.key`. If someone copies the `.exe` to another PC, the fingerprint won't match → 403 blocked. |
| 3 | **IP Whitelist** | `allowed_devices` table | Only IPs you explicitly add can access the app (enforced in Production mode). |
| 4 | **Admin Panel Lock** | `main.py` middleware | The `/api/admin/*` endpoints are ONLY accessible from `127.0.0.1` (the master PC itself). No LAN client can reach the admin panel. |
| 5 | **Sysadmin Password** | `admin_auth.py` | The admin password is stored as a **bcrypt hash** compiled into the binary. Even if someone extracts the binary, they cannot reverse the hash. |
| 6 | **Machine-Bound JWT** | `device.py` → `derive_secret_key()` | JWT signing secrets are derived from the machine's MAC + hostname. Tokens from one machine are invalid on any other. |

> [!IMPORTANT]
> **All security gates (layers 2, 3) are ONLY enforced when `COPS_ENV=production`.** In development mode, these checks are skipped so you can test freely.

### Sensitive Data Check

| Item | Status | Notes |
|------|--------|-------|
| Sysadmin password | ✅ Safe | Stored as bcrypt hash only — never plaintext |
| User passwords | ✅ Safe | Hashed with bcrypt via `passlib` |
| Legacy `.mdb` passwords | ⚠️ In `config.py` | These are passwords for the old Access databases. Not a risk if `.mdb` files are not distributed. |
| JWT secret key | ✅ Safe | Derived from hardware at runtime — not stored anywhere |
| Database file | ⚠️ Unencrypted SQLite | Anyone with file access can read it. Physical PC security is important. |

---

## Step-by-Step Deployment Procedure

### STEP 1: Set the Sysadmin Password in GitHub

The sysadmin password is injected securely during the GitHub Actions build process. You must generate a hash and save it as a GitHub Secret.

**1. Generate the hash:**
On any PC with Python + passlib installed, run:
```bash
python3 -c "
from passlib.context import CryptContext
c = CryptContext(schemes=['bcrypt'], deprecated='auto')
print(c.hash('YourNewStrongPassword'))
"
```
This will print something like: `$2b$12$aBcDeFgHiJkLmNoPqRsTuVwXyZ1234567890abcdef`

**2. Add it to GitHub Secrets:**
1. Go to your GitHub repository in a browser.
2. Click on **Settings** > **Secrets and variables** > **Actions**.
3. Click the green **New repository secret** button.
4. **Name:** `ADMIN_PWD_HASH`
5. **Secret:** *(paste the hash you generated in step 1)*
6. Click **Add secret**.

> [!CAUTION]
> **Remember your password!** There is no password recovery. If lost, you must generate a new hash, update the GitHub Secret, and trigger a new build.

---

### STEP 2: Download the Application Files (Automated via GitHub)

Instead of compiling on your local machine, this project is set up to automatically build the executable files in the cloud using GitHub Actions. There are two automated builds:

1. Go to your GitHub repository in a browser: `https://github.com/bhanuprakash13579/OS_module_upgrade/actions`
2. You will see two workflows running automatically:
   - **Build COPS Server**: This builds the background server (`cops-server-windows.exe`) used on the Master PC to serve LAN clients.
   - **Build Desktop App (Tauri)**: This builds the **Native Windows App** installer (`cops-desktop-windows.msi` or `.exe`). Use this if you want an app icon and a dedicated window instead of a browser.
3. Click on the latest successful run (green checkmark) for either workflow.
4. Scroll down to the **Artifacts** section at the bottom of the page.
5. Click **`cops-desktop-windows`** or **`cops-server-windows.exe`** to download your preferred format.
*(Linux `.deb` and `.AppImage` versions are also available if needed).*

---

### STEP 3: Install on the Master PC

1. **Copy files to the master PC:**
   - The compiled binary (`python-server` or `python-server.exe`)
   - The database file (`cops_br_database.db`)
   - Place them in the same folder (e.g., `C:\COPS\` on Windows or `/opt/cops/` on Linux)

2. **Set the environment variable for Production mode:**

   **Windows (Command Prompt):**
   ```cmd
   set COPS_ENV=production
   python-server.exe
   ```

   **Windows (PowerShell):**
   ```powershell
   $env:COPS_ENV = "production"
   .\python-server.exe
   ```

   **Linux:**
   ```bash
   COPS_ENV=production ./python-server
   ```

3. **The server starts on `http://0.0.0.0:8000`** — accessible from the master PC at `http://localhost:8000` and from LAN at `http://<master-ip>:8000`.

---

### STEP 4: Register the Master Device

On the **master PC only**, open a browser to `http://localhost:8000`:

1. Navigate to the **hidden admin panel** (the gear icon or `/admin` route)
2. Login with:
   - **Username:** `sysadmin`
   - **Password:** *(the password you set in Step 1)*
3. Click **"Register This Device"**
   - This creates a `machine.key` file next to the database
   - The app is now locked to this specific PC's hardware

---

### STEP 5: Whitelist Slave PC IP Addresses

Still in the admin panel on the master PC:

1. Go to the **"Allowed Devices"** section
2. Click **"Add Device"** for each slave PC:

   | Field | What to Enter | Example |
   |-------|---------------|---------|
   | **Label** | A human-readable name | `SDO Room PC-1` |
   | **IP Address** | The LAN IP of the slave PC | `192.168.1.105` |
   | **Hostname** | Optional — for your reference | `SDO-PC-1` |
   | **Notes** | Optional notes | `Inspector Harish's PC` |

3. Repeat for every PC that needs access

> [!TIP]
> **How to find a PC's IP address:**
> - **Windows:** Open Command Prompt → type `ipconfig` → look for "IPv4 Address" under your LAN adapter
> - **Linux:** Open Terminal → type `ip addr` or `hostname -I`

> [!IMPORTANT]
> **Only _active_ LAN IPs (192.168.x.x, 10.x.x.x, 172.16-31.x.x) are allowed.** The middleware blocks everything else automatically.

---

### STEP 6: Open the App on Slave PCs

On each whitelisted slave PC:

1. **Open a web browser** (Chrome, Firefox, Edge — any modern browser)
2. **Navigate to:** `http://<master-pc-ip>:8000`
   - Example: `http://192.168.1.100:8000`
3. **Login** with the user credentials created by the sysadmin (SDO/DC/AC accounts)
4. That's it — no installation needed on slave PCs! The master serves the full UI.

> [!NOTE]
> Slave PCs do NOT need Python, Node.js, or any software installed. They just need a web browser and a LAN connection to the master PC.

---

### STEP 7: Create User Accounts (SDO / DC / AC)

In the admin panel on the master PC:

1. Go to **"User Management"**
2. Click **"Create User"**:
   - **User ID:** email or username (e.g., `inspector.kumar@customs.gov.in`)
   - **Name:** Full name
   - **Role:** `SDO` (for SDO module) or `DC`/`AC` (for Adjudication module)
   - **Password:** Set a strong initial password
3. Share the credentials with the officer

---

## How to Administer via GitHub

To change the sysadmin password for a new release:

1. **Clone the repo** on your development PC
2. **Generate a new bcrypt hash** (see Step 1 above)
3. **Edit** `backend/app/security/admin_auth.py` — replace `_ADMIN_PWD_HASH`
4. **Commit and push:**
   ```bash
   git add backend/app/security/admin_auth.py
   git commit -m "chore: rotate sysadmin password for release vX.Y"
   git push
   ```
5. Wait a few minutes for the **GitHub Action** to finish building your new `.exe` file.
6. Download the new `.exe` from the Actions tab (as shown in Step 2) and deploy it to the master PC.

> [!WARNING]
> Never commit the plaintext password. Only commit the bcrypt hash. The hash is one-way — it cannot be reversed to recover the password.

---

## Quick Reference: Security Behavior by Mode

| Scenario | Dev Mode | Prod Mode |
|----------|----------|-----------|
| LAN-only check | ✅ Always on | ✅ Always on |
| Device registration check | ❌ Skipped | ✅ Enforced |
| IP whitelist | ❌ Skipped | ✅ Enforced |
| Admin panel (localhost only) | ✅ Always on | ✅ Always on |
| DELETE from slave PC | ❌ Blocked | ❌ Blocked |
| Sysadmin password | ✅ Always required | ✅ Always required |

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| "This device is not authorised" | Run "Register This Device" in the admin panel on the master PC |
| "Your device is not on the approved access list" | Add the slave PC's IP in the admin panel → Allowed Devices |
| "Access denied: outside local network" | The PC is not on the same LAN. Ensure both PCs are on the same WiFi/switch |
| Forgot sysadmin password | Generate a new hash, edit `admin_auth.py`, rebuild the binary |
| Slave PC can't reach `http://<ip>:8000` | Check firewall: the master PC must allow inbound TCP port 8000 |
