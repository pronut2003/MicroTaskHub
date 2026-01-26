from fastapi.testclient import TestClient
import sys
import os

# Add parent dir to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app
import models
import databse

client = TestClient(app)

def test_rbac_flow():
    # 1. Register Admin
    admin_email = "admin_test_rbac@test.com"
    admin_data = {
        "email": admin_email,
        "password": "password",
        "full_name": "Admin User",
        "phone_no": "1234567890",
        "role": "Admin"
    }
    
    # Try login first to see if exists
    login_res = client.post("/users/login", json={"email": admin_email, "password": "password"})
    if login_res.status_code == 200:
        admin_token = login_res.json()["access_token"]
    else:
        response = client.post("/users/register", json=admin_data)
        if response.status_code != 200:
            print(response.json())
        assert response.status_code == 200
        # Login
        response = client.post("/users/login", json={"email": admin_email, "password": "password"})
        assert response.status_code == 200
        admin_token = response.json()["access_token"]

    # 2. Check /users/me
    response = client.get("/users/me", headers={"Authorization": f"Bearer {admin_token}"})
    assert response.status_code == 200
    assert response.json()["role"] == "Admin"

    # 3. Create Manager Role (startup should have created it, verify)
    response = client.get("/rbac/roles", headers={"Authorization": f"Bearer {admin_token}"})
    assert response.status_code == 200
    roles = [r["name"] for r in response.json()]
    assert "Manager" in roles
    assert "Admin" in roles
    assert "User" in roles

    # 4. Register Normal User
    user_email = "user_test_rbac@test.com"
    user_data = {
        "email": user_email,
        "password": "password",
        "full_name": "Normal User",
        "phone_no": "1234567890",
        "role": "User"
    }
    
    login_res = client.post("/users/login", json={"email": user_email, "password": "password"})
    if login_res.status_code == 200:
        user_token = login_res.json()["access_token"]
    else:
        client.post("/users/register", json=user_data)
        response = client.post("/users/login", json={"email": user_email, "password": "password"})
        user_token = response.json()["access_token"]

    # 5. User tries to access /rbac/roles -> 403
    response = client.get("/rbac/roles", headers={"Authorization": f"Bearer {user_token}"})
    assert response.status_code == 403

    # 6. Admin assigns Manager role to User
    # Get user id
    response = client.get("/users/me", headers={"Authorization": f"Bearer {user_token}"})
    user_id = response.json()["id"]
    
    response = client.post(
        f"/rbac/users/{user_id}/roles",
        json={"role_names": ["Manager"]},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    
    # 7. User (now Manager) accesses Manager resource (/users/)
    response = client.get("/users/", headers={"Authorization": f"Bearer {user_token}"})
    assert response.status_code == 200
    
    print("RBAC Flow Test Passed")

if __name__ == "__main__":
    test_rbac_flow()
