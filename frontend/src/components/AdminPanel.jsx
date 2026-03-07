import { useState, useEffect } from 'react'

function AdminPanel({ authToken, onRoleChange }) {
  const [roles, setRoles] = useState([])
  const [newRole, setNewRole] = useState('')
  const [loading, setLoading] = useState(false)
  const [msg, setMsg] = useState('')

  useEffect(() => {
    fetchRoles()
  }, [])

  const fetchRoles = async () => {
    try {
        const res = await fetch('/api/rbac/roles', {
            headers: { 'Authorization': `Bearer ${authToken}` }
        })
        if (res.ok) {
            setRoles(await res.json())
        }
    } catch (e) 
    {
        console.error(e)
    }
  }

  const createRole = async () => {
      if (!newRole) return
      setLoading(true)
      try {
          const res = await fetch('/api/rbac/roles', {
              method: 'POST',
              headers: { 
                  'Authorization': `Bearer ${authToken}`,
                  'Content-Type': 'application/json'
              },
              body: JSON.stringify({ name: newRole })
          })
          if (res.ok) {
              setNewRole('')
              fetchRoles()
              setMsg('Role created successfully')
              if (onRoleChange) onRoleChange()
          } else {
              setMsg('Failed to create role')
          }
      } catch (e) {
          console.error(e)
          setMsg('Error creating role')
      } finally {
          setLoading(false)
      }
  }

  return (
    <div className="admin-panel">
      <h3>Role Management</h3>
      {msg && <p className="status-msg">{msg}</p>}
      <div className="role-creation">
          <input 
            value={newRole} 
            onChange={(e) => setNewRole(e.target.value)} 
            placeholder="New Role Name"
            className="role-input"
          />
          <button onClick={createRole} disabled={loading}>
              {loading ? 'Creating...' : 'Create Role'}
          </button>
      </div>
      <div className="roles-list-container">
        <h4>Existing Roles</h4>
        <ul className="roles-list">
            {roles.map(r => (
                <li key={r.id} className="role-item">
                    <span className="role-name">{r.name}</span>
                </li>
            ))}
        </ul>
      </div>
    </div>
  )
}

export default AdminPanel
