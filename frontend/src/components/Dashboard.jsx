import { useState, useEffect } from 'react'

function Dashboard({ authToken, onLogout }) {
  const [userEmail, setUserEmail] = useState(localStorage.getItem('userEmail') || 'User')
  const [users, setUsers] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    fetchUsers()
  }, [])

  const fetchUsers = async () => {
    try {
      setLoading(true)
      const response = await fetch('/api/users/', {
        headers: {
          'Authorization': `Bearer ${authToken}`,
        },
      })

      if (!response.ok) {
        throw new Error('Failed to fetch users')
      }

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

  return (
    <div className="dashboard-container">
      <div className="dashboard-header">
        <div className="header-content">
          <h1>MicroTaskHub Dashboard</h1>
          <p className="welcome-text">Welcome, <span className="user-email">{userEmail}</span></p>
        </div>
        <button className="logout-button" onClick={onLogout}>Logout</button>
      </div>

      <div className="dashboard-content">
        <div className="users-section">
          <h2>Registered Users</h2>
          
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
                        <span className={`role-badge role-${user.role.toLowerCase()}`}>
                          {user.role}
                        </span>
                      </td>
                      <td>
                        <span className={`status-badge ${user.is_active ? 'active' : 'inactive'}`}>
                          {user.is_active ? 'Active' : 'Inactive'}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default Dashboard
