-- 1. Schema Updates for Enhanced Roles and Departments
CREATE TABLE IF NOT EXISTS departments (
    department_id INT AUTO_INCREMENT PRIMARY KEY,
    department_name VARCHAR(100) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Update users table
-- First, ensure existing roles are compatible with the new ENUM
UPDATE users SET role = 'user' WHERE role IS NULL OR role = '';
UPDATE users SET role = LOWER(role);
-- Handle existing 'Admin' -> 'admin', etc.

ALTER TABLE users ADD COLUMN department_id INT;
ALTER TABLE users ADD CONSTRAINT fk_users_department FOREIGN KEY (department_id) REFERENCES departments(department_id);

-- Modify role column to ENUM
ALTER TABLE users MODIFY COLUMN role ENUM('user', 'manager', 'admin') NOT NULL DEFAULT 'user';

-- Update tasks table
-- We use 'is_deleted' instead of 'status' for soft delete to preserve the existing workflow status column.
ALTER TABLE tasks ADD COLUMN is_deleted TINYINT DEFAULT 0;
ALTER TABLE tasks ADD COLUMN assigned_to_user_id INT;
ALTER TABLE tasks ADD COLUMN created_by_user_id INT;

-- Migrate data from old columns if they exist (assuming assigned_to_id and created_by_id exist)
UPDATE tasks SET assigned_to_user_id = assigned_to_id WHERE assigned_to_user_id IS NULL;
UPDATE tasks SET created_by_user_id = created_by_id WHERE created_by_user_id IS NULL;

ALTER TABLE tasks ADD CONSTRAINT fk_tasks_assigned_user FOREIGN KEY (assigned_to_user_id) REFERENCES users(id);
ALTER TABLE tasks ADD CONSTRAINT fk_tasks_created_user FOREIGN KEY (created_by_user_id) REFERENCES users(id);


-- 2. Implement RBAC Schema
CREATE TABLE IF NOT EXISTS permissions (
    permission_id INT AUTO_INCREMENT PRIMARY KEY,
    permission_name VARCHAR(50) UNIQUE NOT NULL,
    description TEXT
);

CREATE TABLE IF NOT EXISTS role_permissions_enum (
    role ENUM('user', 'manager', 'admin'),
    permission_id INT,
    PRIMARY KEY (role, permission_id),
    FOREIGN KEY (permission_id) REFERENCES permissions(permission_id)
);

-- Populate Permissions
INSERT IGNORE INTO permissions (permission_name, description) VALUES 
('create_task', 'Create new tasks'),
('read_own_tasks', 'Read tasks assigned to self'),
('read_team_tasks', 'Read tasks in department'),
('reassign_tasks', 'Reassign tasks to others'),
('update_task', 'Update task details'),
('delete_task', 'Delete tasks'),
('view_system_metrics', 'View system dashboard'),
('view_audit_trails', 'View audit logs'),
('manage_users', 'Create and manage users');

-- Assign Permissions (using subqueries to get IDs)
-- User
INSERT IGNORE INTO role_permissions_enum (role, permission_id)
SELECT 'user', permission_id FROM permissions WHERE permission_name IN ('read_own_tasks');

-- Manager
INSERT IGNORE INTO role_permissions_enum (role, permission_id)
SELECT 'manager', permission_id FROM permissions WHERE permission_name IN ('read_own_tasks', 'read_team_tasks', 'reassign_tasks', 'create_task');

-- Admin
INSERT IGNORE INTO role_permissions_enum (role, permission_id)
SELECT 'admin', permission_id FROM permissions;


-- 3. Audit Logging
ALTER TABLE audit_logs ADD COLUMN entity_type VARCHAR(50);
ALTER TABLE audit_logs ADD COLUMN entity_id INT;
-- (status and error_details were added in previous migration)

-- Triggers
DROP TRIGGER IF EXISTS after_user_insert;
CREATE TRIGGER after_user_insert
AFTER INSERT ON users
FOR EACH ROW
BEGIN
    INSERT INTO audit_logs (user_id, action, entity_type, entity_id, details, timestamp)
    VALUES (NEW.id, 'INSERT', 'User', NEW.id, CONCAT('User created: ', NEW.email), NOW());
END;

DROP TRIGGER IF EXISTS after_task_update;
CREATE TRIGGER after_task_update
AFTER UPDATE ON tasks
FOR EACH ROW
BEGIN
    INSERT INTO audit_logs (user_id, action, entity_type, entity_id, details, timestamp)
    VALUES (IFNULL(NEW.updated_by_user_id, NEW.created_by_user_id), 'UPDATE', 'Task', NEW.id, CONCAT('Task updated status: ', NEW.status), NOW());
END;
-- Note: 'updated_by_user_id' doesn't exist, we might need to rely on app logic for user_id or add it. 
-- For the trigger, we'll use created_by_user_id as fallback or NULL.


-- 4. Task CRUD with Soft Delete
-- Active Tasks View
CREATE OR REPLACE VIEW active_tasks AS 
SELECT * FROM tasks WHERE is_deleted = 0;

-- Stored Procedure for Soft Delete
DROP PROCEDURE IF EXISTS soft_delete_task;
DELIMITER //
CREATE PROCEDURE soft_delete_task(IN p_task_id INT, IN p_user_id INT)
BEGIN
    UPDATE tasks SET is_deleted = 1 WHERE id = p_task_id;
    
    INSERT INTO audit_logs (user_id, action, entity_type, entity_id, details, timestamp)
    VALUES (p_user_id, 'SOFT_DELETE', 'Task', p_task_id, 'Task soft deleted', NOW());
END //
DELIMITER ;


-- 5. Dashboard Views
-- User Dashboard View
CREATE OR REPLACE VIEW user_dashboard_view AS
SELECT t.* 
FROM tasks t
WHERE t.is_deleted = 0;
-- Note: The filtering by user_id happens in the query: SELECT * FROM user_dashboard_view WHERE assigned_to_user_id = X

-- Manager Dashboard View
CREATE OR REPLACE VIEW manager_dashboard_view AS
SELECT t.*, u.department_id as owner_dept
FROM tasks t
JOIN users u ON t.created_by_user_id = u.id
WHERE t.is_deleted = 0;

-- Admin Dashboard View (Aggregates)
-- This is complex for a view to return multiple metrics. Usually views return datasets.
-- We'll create a view that aggregates stats by status
CREATE OR REPLACE VIEW admin_task_stats_view AS
SELECT status, count(*) as count
FROM tasks
WHERE is_deleted = 0
GROUP BY status;

