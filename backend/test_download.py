import requests
try:
    token = requests.post("http://127.0.0.1:8000/api/admin/login", json={"username": "sysadmin", "password": "cops-chennai-customs-system-password"}).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    r1 = requests.get("http://127.0.0.1:8000/api/admin/backup/export", headers=headers)
    print("export:", r1.status_code, len(r1.content))
    if r1.status_code != 200:
        print(r1.text)
        
    r2 = requests.get("http://127.0.0.1:8000/api/admin/backup/export-fulldb", headers=headers)
    print("export-fulldb:", r2.status_code, len(r2.content))
    if r2.status_code != 200:
        print(r2.text)
except Exception as e:
    print(e)
