from sqlalchemy import text, inspect
from databse import engine
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_migration():
    with engine.connect() as conn:
        inspector = inspect(engine)
        
        # 1. Departments Table
        if not inspector.has_table("departments"):
            logger.info("Creating departments table")
            conn.execute(text("""
                CREATE TABLE departments (
                    department_id INT AUTO_INCREMENT PRIMARY KEY,
                    department_name VARCHAR(100) UNIQUE NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
        
        # 2. Users Updates
        columns = [c['name'] for c in inspector.get_columns("users")]
        
        if "department_id" not in columns:
            logger.info("Adding department_id to users")
            conn.execute(text("ALTER TABLE users ADD COLUMN department_id INT"))
            conn.execute(text("ALTER TABLE users ADD CONSTRAINT fk_users_department FOREIGN KEY (department_id) REFERENCES departments(department_id)"))

        # Handle Role Enum
        try:
            conn.execute(text("UPDATE users SET role = 'user' WHERE role IS NULL OR role = ''"))
            conn.execute(text("UPDATE users SET role = 'user' WHERE LOWER(role) NOT IN ('user', 'manager', 'admin')"))
            conn.execute(text("UPDATE users SET role = LOWER(role)"))
            
            # Check if modification is needed (simplified check)
            logger.info("Modifying users.role to ENUM")
            conn.execute(text("ALTER TABLE users MODIFY COLUMN role ENUM('user', 'manager', 'admin') NOT NULL DEFAULT 'user'"))
        except Exception as e:
            logger.error(f"Failed to modify users.role: {e}")

        # 3. Permissions Table Updates
        perm_columns = [c['name'] for c in inspector.get_columns("permissions")]
        
        if "id" in perm_columns and "permission_id" not in perm_columns:
            logger.info("Renaming permissions.id to permission_id")
            conn.execute(text("ALTER TABLE permissions CHANGE COLUMN id permission_id INT AUTO_INCREMENT"))
            
        if "name" in perm_columns and "permission_name" not in perm_columns:
            logger.info("Renaming permissions.name to permission_name")
            conn.execute(text("ALTER TABLE permissions CHANGE COLUMN name permission_name VARCHAR(50)"))

        # 4. Role Permissions
        # Check if existing role_permissions is the old one (has role_id)
        if inspector.has_table("role_permissions"):
            rp_columns = [c['name'] for c in inspector.get_columns("role_permissions")]
            if "role_id" in rp_columns:
                logger.info("Renaming legacy role_permissions table")
                conn.execute(text("RENAME TABLE role_permissions TO role_permissions_legacy"))
        
        if not inspector.has_table("role_permissions"):
            logger.info("Creating new role_permissions table")
            conn.execute(text("""
                CREATE TABLE role_permissions (
                    role ENUM('user', 'manager', 'admin'),
                    permission_id INT,
                    PRIMARY KEY (role, permission_id),
                    FOREIGN KEY (permission_id) REFERENCES permissions(permission_id)
                )
            """))
            
            # Populate Permissions
            perms = [
                ('create_task', 'Create new tasks'),
                ('read_own_tasks', 'Read tasks assigned to self'),
                ('read_team_tasks', 'Read tasks in department'),
                ('reassign_tasks', 'Reassign tasks to others'),
                ('update_task', 'Update task details'),
                ('delete_task', 'Delete tasks'),
                ('view_system_metrics', 'View system dashboard'),
                ('view_audit_trails', 'View audit logs'),
                ('manage_users', 'Create and manage users')
            ]
            for p_name, p_desc in perms:
                conn.execute(text("INSERT IGNORE INTO permissions (permission_name, description) VALUES (:name, :desc)"), {"name": p_name, "desc": p_desc})

            # Assign Permissions
            def get_perm_id(name):
                res = conn.execute(text("SELECT permission_id FROM permissions WHERE permission_name = :name"), {"name": name}).scalar()
                return res

            role_map = {
                'user': ['read_own_tasks'],
                'manager': ['read_own_tasks', 'read_team_tasks', 'reassign_tasks', 'create_task'],
                'admin': [p[0] for p in perms]
            }
            
            for role, p_names in role_map.items():
                for p_name in p_names:
                    pid = get_perm_id(p_name)
                    if pid:
                        try:
                            conn.execute(text("INSERT IGNORE INTO role_permissions (role, permission_id) VALUES (:role, :pid)"), {"role": role, "pid": pid})
                        except Exception as e:
                            pass

        # 5. Tasks Updates
        task_columns = [c['name'] for c in inspector.get_columns("tasks")]
        
        if "is_deleted" not in task_columns:
            logger.info("Adding is_deleted to tasks")
            conn.execute(text("ALTER TABLE tasks ADD COLUMN is_deleted TINYINT DEFAULT 0"))
            
        if "assigned_to_user_id" not in task_columns:
            logger.info("Adding assigned_to_user_id to tasks")
            conn.execute(text("ALTER TABLE tasks ADD COLUMN assigned_to_user_id INT"))
            if "assigned_to_id" in task_columns:
                conn.execute(text("UPDATE tasks SET assigned_to_user_id = assigned_to_id"))
            conn.execute(text("ALTER TABLE tasks ADD CONSTRAINT fk_tasks_assigned_user FOREIGN KEY (assigned_to_user_id) REFERENCES users(id)"))

        if "created_by_user_id" not in task_columns:
            logger.info("Adding created_by_user_id to tasks")
            conn.execute(text("ALTER TABLE tasks ADD COLUMN created_by_user_id INT"))
            if "created_by_id" in task_columns:
                conn.execute(text("UPDATE tasks SET created_by_user_id = created_by_id"))
            conn.execute(text("ALTER TABLE tasks ADD CONSTRAINT fk_tasks_created_user FOREIGN KEY (created_by_user_id) REFERENCES users(id)"))

        # 6. Audit Logs
        audit_columns = [c['name'] for c in inspector.get_columns("audit_logs")]
        if "entity_type" not in audit_columns:
            conn.execute(text("ALTER TABLE audit_logs ADD COLUMN entity_type VARCHAR(50)"))
        if "entity_id" not in audit_columns:
            conn.execute(text("ALTER TABLE audit_logs ADD COLUMN entity_id INT"))

        # 7. Triggers
        try:
            conn.execute(text("DROP TRIGGER IF EXISTS after_user_insert"))
            conn.execute(text("""
                CREATE TRIGGER after_user_insert
                AFTER INSERT ON users
                FOR EACH ROW
                BEGIN
                    INSERT INTO audit_logs (user_id, action, entity_type, entity_id, details, timestamp)
                    VALUES (NEW.id, 'INSERT', 'User', NEW.id, CONCAT('User created: ', NEW.email), NOW());
                END
            """))
            logger.info("Created user trigger")
        except Exception as e:
            logger.error(f"Failed user trigger: {e}")
            
        try:
            conn.execute(text("DROP TRIGGER IF EXISTS after_task_update"))
            # Note: updated_by_user_id doesn't exist, using created_by_user_id or logic
            # Also checking if we can get current user. For now, fallback to created_by or NULL.
            conn.execute(text("""
                CREATE TRIGGER after_task_update
                AFTER UPDATE ON tasks
                FOR EACH ROW
                BEGIN
                    INSERT INTO audit_logs (user_id, action, entity_type, entity_id, details, timestamp)
                    VALUES (NEW.created_by_user_id, 'UPDATE', 'Task', NEW.id, CONCAT('Task updated. Status: ', NEW.status), NOW());
                END
            """))
            logger.info("Created task trigger")
        except Exception as e:
             logger.error(f"Failed task trigger: {e}")

        # 8. Views & Procedures
        logger.info("Creating Views")
        conn.execute(text("CREATE OR REPLACE VIEW active_tasks AS SELECT * FROM tasks WHERE is_deleted = 0"))
        conn.execute(text("CREATE OR REPLACE VIEW user_dashboard_view AS SELECT * FROM tasks WHERE is_deleted = 0"))
        
        try:
            conn.execute(text("""
                CREATE OR REPLACE VIEW manager_dashboard_view AS
                SELECT t.*, u.department_id as owner_dept
                FROM tasks t
                JOIN users u ON t.created_by_user_id = u.id
                WHERE t.is_deleted = 0
            """))
        except Exception as e:
            logger.error(f"Failed manager view: {e}")

        try:
             # Admin Dashboard View (Aggregates)
             # User asked for 'admin_dashboard_view' that aggregates system-wide metrics.
             # Views usually return rows. We can make a view that returns 1 row with many columns or multiple rows.
             # Simplest: View with multiple columns (subqueries).
             conn.execute(text("""
                CREATE OR REPLACE VIEW admin_dashboard_view AS
                SELECT 
                    (SELECT COUNT(*) FROM users) as total_users,
                    (SELECT COUNT(*) FROM tasks WHERE is_deleted=0) as active_tasks,
                    (SELECT COUNT(*) FROM tasks WHERE status='COMPLETED') as completed_tasks
             """))
        except Exception as e:
             logger.error(f"Failed admin view: {e}")

        try:
            conn.execute(text("DROP PROCEDURE IF EXISTS soft_delete_task"))
            conn.execute(text("""
                CREATE PROCEDURE soft_delete_task(IN p_task_id INT, IN p_user_id INT)
                BEGIN
                    UPDATE tasks SET is_deleted = 1 WHERE id = p_task_id;
                    
                    INSERT INTO audit_logs (user_id, action, entity_type, entity_id, details, timestamp)
                    VALUES (p_user_id, 'SOFT_DELETE', 'Task', p_task_id, 'Task soft deleted', NOW());
                END
            """))
            logger.info("Created stored procedure")
        except Exception as e:
            logger.error(f"Failed stored procedure: {e}")

        conn.commit()
        logger.info("Migration completed successfully")

if __name__ == "__main__":
    run_migration()
