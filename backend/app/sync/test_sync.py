import requests

print("Testing Online Adjudication ₹5L Rule")
# Login
login_res = requests.post("http://127.0.0.1:8000/api/auth/login", data={"username": "bhanu@gmail.com", "password": "bhanu"})
if login_res.status_code != 200:
    print("Login Failed")
else:
    token = login_res.json()["access_token"]
    
    # Adjudicate the previously created OS '1' of year 2026.
    adj_payload = {
        "adj_offr_name": "Test ADC",
        "adj_offr_designation": "Assistant Commissioner",
        "adjn_offr_remarks": "Test order"
    }

    headers = {"Authorization": f"Bearer {token}"}
    res = requests.post("http://127.0.0.1:8000/api/os/1/2026/adjudicate", json=adj_payload, headers=headers)
    print("Status:", res.status_code)
    print("Response:", res.text)
