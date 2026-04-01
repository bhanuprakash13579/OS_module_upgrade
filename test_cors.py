import requests
res = requests.options("http://127.0.0.1:8000/api/mode", headers={"Origin": "http://localhost:1420", "Access-Control-Request-Method": "GET"})
print(f"1420: {res.status_code} {res.text}")

res2 = requests.options("http://127.0.0.1:8000/api/mode", headers={"Origin": "http://localhost:5173", "Access-Control-Request-Method": "GET"})
print(f"5173: {res2.status_code} {res2.text}")
