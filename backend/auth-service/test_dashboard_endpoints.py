import requests

BASE_URL = "http://localhost:8000"
LOGIN_URL = f"{BASE_URL}/users/token"
DASHBOARD_URL = f"{BASE_URL}/dashboard"

def test_dashboard():
    # Login as Admin
    data = {"username": "admin@example.com", "password": "adminpassword"}
    response = requests.post(LOGIN_URL, data=data)
    if response.status_code != 200:
        print("Login failed")
        return
    
    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    print("Testing /dashboard/stats...")
    res = requests.get(f"{DASHBOARD_URL}/stats", headers=headers)
    print(res.status_code, res.json())
    
    print("Testing /dashboard/tasks-time...")
    res = requests.get(f"{DASHBOARD_URL}/tasks-time", headers=headers)
    print(res.status_code, res.json())
    
    print("Testing /dashboard/activity...")
    res = requests.get(f"{DASHBOARD_URL}/activity", headers=headers)
    print(res.status_code, res.json())
    
    print("Testing /dashboard/admin/stats...")
    res = requests.get(f"{DASHBOARD_URL}/admin/stats", headers=headers)
    print(res.status_code, res.json())

if __name__ == "__main__":
    test_dashboard()
