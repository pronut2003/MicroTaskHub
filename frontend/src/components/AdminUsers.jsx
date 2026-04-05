import { useState, useEffect } from 'react'

function AdminUsers({ authToken, onLogout }) {
  const [users, setUsers] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => { fetchUsers() }, [])

  const fetchUsers = async () => {
    try {
      setLoading(true)
      const response = await fetch('/api/users/', {
        headers: { 'Authorization': `Bearer ${authToken}` },
      })
      if (response.status === 401) { onLogout(); return }
      if (!response.ok) throw new Error('Failed to fetch users')
      const data = await response.json()
      setUsers(data)
      setError('')
    } catch (err) {
      setError('Could not load users')
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  const handleRoleChange = async (userId, newRole) => {
    try {
      const response = await fetch(`/api/users/${userId}/role`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${authToken}`,
        },
        body: JSON.stringify({ role: newRole }),
      })
      if (response.status === 401) { onLogout(); return }
      if (!response.ok) {
        const data = await response.json()
        alert(data.detail || 'Failed to update role')
        return
      }
      fetchUsers()
    } catch (err) {
      console.error(err)
    }
  }

  const handleStatusToggle = async (userId, currentStatus) => {
    try {
      const response = await fetch(`/api/users/${userId}/status`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${authToken}`,
        },
        body: JSON.stringify({ is_active: !currentStatus }),
      })
      if (response.status === 401) { onLogout(); return }
      if (!response.ok) {
        const data = await response.json()
        alert(data.detail || 'Failed to update status')
        return
      }
      fetchUsers()
    } catch (err) {
      console.error(err)
    }
  }

  return (
    <div className="dashboard-content">
      <div className="users-section">
        <h2>User Management</h2>

        {loading && <p className="loading-text">Loading users...</p>}
        {error && <div className="error-message">{error}</div>}

        {!loading && !error && users.length === 0 && (
          <p className="empty-state">No users found</p>
        )}

        {!loading && users.length > 0 && (
          <div className="users-table-container">
            <table className="users-table">
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Email</th>
                  <th>Phone</th>
                  <th>Role</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {users.map((user) => (
                  <tr key={user.id}>
                    <td className="user-name-cell">
                      <div className="user-avatar-small">{user.full_name.charAt(0).toUpperCase()}</div>
                      <span>{user.full_name}</span>
                    </td>
                    <td>{user.email}</td>
                    <td>{user.phone_no}</td>
                    <td>
                      <select
                        value={user.role}
                        onChange={(e) => handleRoleChange(user.id, e.target.value)}
                        className="role-select"
                      >
                        <option value="User">User</option>
                        <option value="Manager">Manager</option>
                        <option value="Admin">Admin</option>
                      </select>
                    </td>
                    <td>
                      <button
                        className={`status-badge ${user.is_active ? 'active' : 'inactive'}`}
                        onClick={() => handleStatusToggle(user.id, user.is_active)}
                        style={{ cursor: 'pointer', border: 'none' }}
                      >
                        {user.is_active ? 'Active' : 'Inactive'}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}

export default AdminUsers
