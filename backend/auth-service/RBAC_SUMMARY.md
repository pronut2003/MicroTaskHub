# RBAC System Implementation Summary

## Overview
A comprehensive Role-Based Access Control (RBAC) system has been implemented to manage user permissions, department associations, and task visibility. The system introduces enhanced roles (User, Manager, Admin), soft delete functionality for tasks, and automated audit logging.

## Schema Changes

### 1. Departments & Users
- **Departments Table**: Added `departments` table with `department_id` and `department_name`.
- **User Roles**: Updated `users` table to include a `role` ENUM column (`user`, `manager`, `admin`).
- **Department Association**: Added `department_id` foreign key to `users` table.

### 2. Role-Based Permissions
- **Permissions Table**: Renamed columns to `permission_id` and `permission_name` for clarity.
- **Role Permissions**: Created a new junction table `role_permissions` with composite primary key `(role, permission_id)`.
- **Defined Permissions**:
  - `create_task`, `read_own_tasks` (User default)
  - `read_team_tasks`, `reassign_tasks` (Manager extras)
  - `view_system_metrics`, `manage_users`, `delete_task` (Admin extras)

### 3. Task Management (Soft Delete)
- **Soft Delete**: Added `is_deleted` (TINYINT) to `tasks` table.
- **Legacy Compatibility**: Preserved `created_by_id` and `assigned_to_id` while adding foreign key linked columns `created_by_user_id` and `assigned_to_user_id`.
- **Views**:
  - `active_tasks`: Filters out soft-deleted tasks.
  - `user_dashboard_view`: Shows active tasks for users.
  - `manager_dashboard_view`: Includes department information for managers.
  - `admin_dashboard_view`: Aggregates system-wide metrics (User count, Active tasks, Completed tasks).

### 4. Audit Logging
- **Audit Table**: Enhanced `audit_logs` with `entity_type` and `entity_id`.
- **Triggers**:
  - `after_user_insert`: Logs new user creation.
  - `after_task_update`: Logs task status updates.
- **Stored Procedures**:
  - `soft_delete_task(task_id, user_id)`: Marks task as deleted and logs the action in audit trails.

## Implementation Details

### Database Migration
- Incremental migration script `apply_schema.py` ensures backward compatibility.
- Legacy tables (`role_permissions_legacy`) are preserved.

### ORM Models (`models.py`)
- Updated SQLAlchemy models to reflect new schema.
- Added `UserRole`, `TaskPriority`, `TaskStatus` Enums with value-based mapping to handle database case sensitivity.
- Implemented `RolePermission` model for the new junction table.

### Verification
- `verify_implementation.py` script validates:
  - User creation with roles.
  - Task creation and assignment.
  - Soft delete functionality (view filtering).
  - Audit log capture (triggers and procedures).
  - Dashboard view queries.

## Usage
- **Users**: Can see their own active tasks.
- **Managers**: Can see team tasks and reassign them.
- **Admins**: Have full access to system metrics and user management.
