import requests
import sys

print("Logging in...")
try:
    r = requests.post("http://127.0.0.1:8000/api/admin/login", json={"username": "sysadmin", "password": "your_password_here"})
    r.raise_for_status()
    token = r.json()["access_token"]
    print("Logged in!")
    headers = {"Authorization": f"Bearer {token}"}
    
    print("Testing /export...")
    r1 = requests.get("http://127.0.0.1:8000/api/admin/backup/export", headers=headers)
    print("export:", r1.status_code, len(r1.content))
    if r1.status_code != 200:
        print(r1.text)
        
    print("Testing /export-fulldb...")
    r2 = requests.get("http://127.0.0.1:8000/api/admin/backup/export-fulldb", headers=headers)
    print("export-fulldb:", r2.status_code, len(r2.content))
    if r2.status_code != 200:
        print(r2.text)
except Exception as e:
    print("ERROR:", e)
