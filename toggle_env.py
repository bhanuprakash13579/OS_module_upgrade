#!/usr/bin/env python3
import os
import sys

def main():
    if len(sys.argv) < 2 or sys.argv[1].lower() not in ["dev", "prod"]:
        print("\n[COPS Mode Switcher]")
        print("Usage: python toggle_env.py [dev|prod]")
        print("  dev  - Switches to development mode (disables device auth & IP whitelisting)")
        print("  prod - Switches to production mode (enforces strict security gates)")
        print()
        sys.exit(1)

    mode = sys.argv[1].lower()
    env_target = "development" if mode == "dev" else "production"
    
    # Path is relative to script location (assuming it's run from project root)
    backend_env_path = os.path.join("backend", ".env")
    
    if not os.path.exists(backend_env_path):
        print(f"❌ Error: Could not find {backend_env_path}")
        print("Are you running this script from the project root?")
        sys.exit(1)

    # Read current lines
    with open(backend_env_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
        
    # Process
    new_lines = []
    found_cops_env = False
    old_env = "unknown"
    
    for line in lines:
        if line.startswith("COPS_ENV="):
            found_cops_env = True
            old_env = line.strip().split("=")[1]
            new_lines.append(f"COPS_ENV={env_target}\n")
        else:
            new_lines.append(line)
            
    if not found_cops_env:
        new_lines.insert(0, f"COPS_ENV={env_target}\n")
        
    # Write back
    with open(backend_env_path, "w", encoding="utf-8") as f:
        f.writelines(new_lines)

    # Display status
    print(f"\n✅ Mode successfully switched to: {env_target.upper()}")
    print("-" * 50)
    
    if env_target == "development":
        print("🔓 DEVELOPMENT SECURITY STATUS:")
        print("  [Disabled] IP Whitelisting (allow all LAN connections)")
        print("  [Disabled] Machine/Device Fingerprint Binding")
        print("  [Enabled]  Debug Tracebacks and Verbose Logging")
        print("  [Active]   Vite proxy (/api → localhost:8000, no CORS needed)")
        print("\nReminder: Do not deploy to actual live server in this mode.")
    else:
        print("🔒 PRODUCTION SECURITY STATUS:")
        print("  [Enabled]  Strict IP Whitelisting")
        print("  [Enabled]  Hardened Machine/Device Fingerprint Binding")
        print("  [Disabled] Full raw error tracebacks on the frontend")
        print("  [Active]   CORS locked to Tauri origins only")
        print("\nReminder: Devices using the app must be registered via the Admin DB.")
        
    print("-" * 50)
    print("👉 Next Step: Restart your uvicorn backend for the changes to take effect.")
    print("   (e.g., kill the running terminal or press Ctrl+C, then restart it)")
    print()

if __name__ == "__main__":
    main()
