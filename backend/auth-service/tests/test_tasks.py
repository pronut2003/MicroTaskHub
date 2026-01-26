import pytest
import os
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from main import app
from databse import Base, get_db
import models
import auth
from datetime import datetime, timedelta

# Setup Test DB
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_tasks.db"
if os.path.exists("./test_tasks.db"):
    os.remove("./test_tasks.db")

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(scope="module")
def client():
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    # Create Roles
    db = TestingSessionLocal()
    roles = ["User", "Manager", "Admin"]
    for r in roles:
        if not db.query(models.Role).filter_by(name=r).first():
            db.add(models.Role(name=r))
    db.commit()
    db.close()
    
    yield TestClient(app)
    
    # Cleanup
    Base.metadata.drop_all(bind=engine)
    if os.path.exists("./test_tasks.db"):
        os.remove("./test_tasks.db")

def create_user(client, email, password, role, department=None):
    # Register
    res = client.post("/users/register", json={
        "email": email,
        "password": password,
        "full_name": role,
        "phone_no": "1234567890",
        "role": role,
        "department": department
    })
    if res.status_code != 200:
        # If user already exists, that's fine for subsequent runs if DB persisted, 
        # but here we clean DB. So it should be 200.
        print(f"Register failed for {email}: {res.status_code} {res.text}")
    
    # Login
    res = client.post("/users/login", json={"email": email, "password": password})
    if res.status_code != 200:
        print(f"Login failed for {email}: {res.status_code} {res.text}")
        return None
    return res.json()["access_token"]

def test_task_flow(client):
    # Create Users
    admin_token = create_user(client, "admin@task.com", "pass", "Admin", "IT")
    assert admin_token is not None, "Admin login failed"
    
    manager_token = create_user(client, "manager@task.com", "pass", "Manager", "Engineering")
    assert manager_token is not None, "Manager login failed"
    
    user_token = create_user(client, "user@task.com", "pass", "User", "Engineering")
    assert user_token is not None, "User login failed"
    
    user2_token = create_user(client, "user2@task.com", "pass", "User", "HR")
    assert user2_token is not None, "User2 login failed"

    # 1. Admin creates task
    res = client.post("/tasks/", 
        json={
            "title": "Admin Task",
            "priority": "high",
            "due_date": (datetime.utcnow() + timedelta(days=1)).isoformat()
        },
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    if res.status_code != 200:
        print(f"Admin create task failed: {res.status_code} {res.text}")
    assert res.status_code == 200
    task_id = res.json()["id"]

    # 2. Manager creates task in Engineering
    res = client.post("/tasks/", 
        json={
            "title": "Eng Task",
            "department": "Engineering"
        },
        headers={"Authorization": f"Bearer {manager_token}"}
    )
    assert res.status_code == 200
    eng_task_id = res.json()["id"]
    assert res.json()["department"] == "Engineering"

    # 3. User creates task (auto-assigned to Engineering)
    res = client.post("/tasks/", 
        json={
            "title": "User Task"
        },
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert res.status_code == 200
    user_task_id = res.json()["id"]
    assert res.json()["department"] == "Engineering"

    # 4. Manager (Engineering) should see Eng Task and User Task, but not Admin Task (IT)
    res = client.get("/tasks/", headers={"Authorization": f"Bearer {manager_token}"})
    tasks = res.json()["items"]
    ids = [t["id"] for t in tasks]
    assert eng_task_id in ids
    assert user_task_id in ids
    assert task_id not in ids

    # 5. User (Engineering) should only see own task
    res = client.get("/tasks/", headers={"Authorization": f"Bearer {user_token}"})
    tasks = res.json()["items"]
    ids = [t["id"] for t in tasks]
    assert user_task_id in ids
    assert eng_task_id not in ids
    
    # 6. Admin should see all
    res = client.get("/tasks/", headers={"Authorization": f"Bearer {admin_token}"})
    assert len(res.json()["items"]) >= 3

    # 7. Update Task
    res = client.put(f"/tasks/{user_task_id}", 
        json={"status": "in_progress"},
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert res.status_code == 200
    assert res.json()["status"] == "in_progress"

    # 8. Delete Task (User delete own)
    res = client.delete(f"/tasks/{user_task_id}", headers={"Authorization": f"Bearer {user_token}"})
    assert res.status_code == 200

    # 9. Verify Soft Delete
    res = client.get(f"/tasks/{user_task_id}", headers={"Authorization": f"Bearer {user_token}"})
    assert res.status_code == 404

    # 10. Date Filtering
    # Create a task next month
    next_month = datetime.utcnow() + timedelta(days=35)
    res = client.post("/tasks/", 
        json={
            "title": "Future Task",
            "due_date": next_month.isoformat()
        },
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert res.status_code == 200
    future_task_id = res.json()["id"]

    # Filter for next month
    start_date = (next_month - timedelta(days=5)).isoformat()
    end_date = (next_month + timedelta(days=5)).isoformat()
    
    res = client.get(f"/tasks/?from_date={start_date}&to_date={end_date}", 
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    items = res.json()["items"]
    ids = [t["id"] for t in items]
    assert future_task_id in ids
    
    # Filter for this month (should not include future task)
    res = client.get(f"/tasks/?to_date={datetime.utcnow().isoformat()}", 
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    items = res.json()["items"]
    ids = [t["id"] for t in items]
    assert future_task_id not in ids
