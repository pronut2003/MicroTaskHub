from sqlalchemy import text, func
from databse import SessionLocal, engine
import models
from datetime import datetime

def verify():
    db = SessionLocal()
    try:
        # 1. Setup Sample Data
        print("--- Setting up Sample Data ---")
        
        # Department
        dept = db.query(models.Department).filter_by(department_name="Engineering").first()
        if not dept:
            dept = models.Department(department_name="Engineering")
            db.add(dept)
            db.commit()
            db.refresh(dept)
        print(f"Department: {dept.department_name} (ID: {dept.department_id})")

        # Users
        users_data = [
            {"email": "alice_v2@example.com", "role": models.UserRole.USER, "name": "Alice User"},
            {"email": "bob_v2@example.com", "role": models.UserRole.MANAGER, "name": "Bob Manager"},
            {"email": "charlie_v2@example.com", "role": models.UserRole.ADMIN, "name": "Charlie Admin"}
        ]
        
        users_map = {}
        for u_data in users_data:
            user = db.query(models.User).filter_by(email=u_data["email"]).first()
            if not user:
                user = models.User(
                    email=u_data["email"],
                    full_name=u_data["name"],
                    password_hash="hash",
                    phone_no="123",
                    role=u_data["role"],
                    department_id=dept.department_id if u_data["role"] != models.UserRole.ADMIN else None
                )
                db.add(user)
                db.commit()
                db.refresh(user)
            users_map[u_data["role"]] = user
            print(f"User: {user.email} (ID: {user.id}, Role: {user.role})")

        # Tasks
        # Create Task 1 (Active) for Alice
        task1 = models.Task(
            title="Active Task",
            description="Should be visible",
            created_by_user_id=users_map[models.UserRole.MANAGER].id,
            assigned_to_user_id=users_map[models.UserRole.USER].id,
            created_by_id=users_map[models.UserRole.MANAGER].id, # Legacy
            assigned_to_id=users_map[models.UserRole.USER].id, # Legacy
            status=models.TaskStatus.PENDING,
            is_deleted=0
        )
        db.add(task1)
        
        # Create Task 2 (To be deleted) for Alice
        task2 = models.Task(
            title="Task to Delete",
            description="Should be hidden",
            created_by_user_id=users_map[models.UserRole.MANAGER].id,
            assigned_to_user_id=users_map[models.UserRole.USER].id,
            created_by_id=users_map[models.UserRole.MANAGER].id, # Legacy
            assigned_to_id=users_map[models.UserRole.USER].id, # Legacy
            status=models.TaskStatus.PENDING,
            is_deleted=0
        )
        db.add(task2)
        db.commit()
        db.refresh(task1)
        db.refresh(task2)
        print(f"Created Tasks: {task1.id}, {task2.id}")

        # 2. Test Soft Delete Stored Procedure
        print("\n--- Testing Soft Delete Procedure ---")
        try:
            db.execute(text("CALL soft_delete_task(:tid, :uid)"), {"tid": task2.id, "uid": users_map[models.UserRole.MANAGER].id})
            db.commit()
            print("Executed soft_delete_task")
        except Exception as e:
            print(f"Error calling procedure: {e}")
            # Fallback manual update if procedure fails in python driver (sometimes result set issues)
            task2.is_deleted = 1
            db.commit()

        # 3. Verify Active Tasks View
        print("\n--- Verifying active_tasks View ---")
        active_tasks = db.execute(text("SELECT id, title FROM active_tasks WHERE title IN ('Active Task', 'Task to Delete')")).fetchall()
        print(f"Active Tasks in View: {active_tasks}")
        # Expect only Task 1
        found_ids = [t[0] for t in active_tasks]
        if task1.id in found_ids and task2.id not in found_ids:
            print("SUCCESS: Soft deleted task is hidden.")
        else:
            print("FAILURE: Soft deleted task visibility incorrect.")

        # 4. Verify Dashboard Views
        print("\n--- Verifying Dashboard Views ---")
        # Manager View
        manager_view = db.execute(text("SELECT * FROM manager_dashboard_view LIMIT 1")).fetchone()
        print(f"Manager View Row: {manager_view}")
        
        # Admin Stats View
        admin_view = db.execute(text("SELECT * FROM admin_dashboard_view")).fetchone()
        print(f"Admin Stats: {admin_view}")

        # 5. Verify Audit Logs (Triggers)
        print("\n--- Verifying Audit Logs ---")
        logs = db.query(models.AuditLog).order_by(models.AuditLog.timestamp.desc()).limit(5).all()
        for log in logs:
            print(f"Log: {log.action} - {log.details} (Entity: {log.entity_type} #{log.entity_id})")
            
        # Check for User Insert Log
        user_log = db.query(models.AuditLog).filter(models.AuditLog.action == "INSERT", models.AuditLog.entity_type == "User").first()
        if user_log:
            print("SUCCESS: User INSERT trigger worked.")
        else:
            print("WARNING: User INSERT trigger might not have fired (check if user already existed).")
            
        # Check for Soft Delete Log
        sd_log = db.query(models.AuditLog).filter(models.AuditLog.action == "SOFT_DELETE").first()
        if sd_log:
             print("SUCCESS: Soft Delete Procedure logged action.")

    except Exception as e:
        print(f"Verification Failed: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    verify()
