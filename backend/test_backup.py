import asyncio
from fastapi.testclient import TestClient
from app.main import app
import app.security.device

# Mock LAN IP check
app.security.device.is_lan_ip = lambda ip: True

client = TestClient(app)

def test_routes():
    from app.services.auth import get_current_active_user
    app.dependency_overrides[get_current_active_user] = lambda: {"user_id": "test"}
    
    print("Testing /api/backup/export/db")
    res_db = client.get("/api/backup/export/db")
    if res_db.status_code != 200:
        print("DB FAILED:", res_db.status_code, res_db.content)
    else:
        print("DB SUCCESS, size:", len(res_db.content))
        
    print("Testing /api/backup/export/csv")
    res_csv = client.get("/api/backup/export/csv")
    if res_csv.status_code != 200:
        print("CSV FAILED:", res_csv.status_code, res_csv.content)
    else:
        print("CSV SUCCESS, size:", len(res_csv.content))

test_routes()
