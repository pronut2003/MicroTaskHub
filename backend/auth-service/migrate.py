from sqlalchemy import text
from databse import engine, Base
import models

def migrate():
    with engine.connect() as conn:
        # 1. Add department to users
        try:
            conn.execute(text("ALTER TABLE users ADD COLUMN department VARCHAR(100)"))
            print("Added department to users")
        except Exception as e:
            print(f"Skipping users.department: {e}")

        # 2. Add timestamps to roles
        try:
            conn.execute(text("ALTER TABLE roles ADD COLUMN created_at DATETIME DEFAULT CURRENT_TIMESTAMP"))
            conn.execute(text("ALTER TABLE roles ADD COLUMN updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"))
            print("Added timestamps to roles")
        except Exception as e:
            print(f"Skipping roles timestamps: {e}")

        # 3. Add assigned_at to user_roles
        try:
            conn.execute(text("ALTER TABLE user_roles ADD COLUMN assigned_at DATETIME DEFAULT CURRENT_TIMESTAMP"))
            print("Added assigned_at to user_roles")
        except Exception as e:
            print(f"Skipping user_roles.assigned_at: {e}")

        # 4. Add status and error_details to audit_logs
        try:
            conn.execute(text("ALTER TABLE audit_logs ADD COLUMN status VARCHAR(50) DEFAULT 'success'"))
            conn.execute(text("ALTER TABLE audit_logs ADD COLUMN error_details TEXT"))
            print("Added status and error_details to audit_logs")
        except Exception as e:
            print(f"Skipping audit_logs updates: {e}")

        conn.commit()

    # 5. Create new tables (Tasks)
    print("Creating new tables...")
    Base.metadata.create_all(bind=engine)
    print("Migration complete.")

if __name__ == "__main__":
    migrate()
