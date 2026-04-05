import { useState, useEffect } from 'react'

function Dashboard({ authToken, userRole, onLogout }) {
  const [stats, setStats] = useState(null)
  const [adminStats, setAdminStats] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    fetchDashboard()
  }, [])

  const fetchDashboard = async () => {
    try {
      setLoading(true)
      const response = await fetch('/api/dashboard/', {
        headers: { 'Authorization': `Bearer ${authToken}` },
      })
      if (response.status === 401) { onLogout(); return }
      if (!response.ok) throw new Error('Failed to fetch dashboard')
      const data = await response.json()
      setStats(data)

      if (userRole === 'Admin') {
        const adminResponse = await fetch('/api/dashboard/admin', {
          headers: { 'Authorization': `Bearer ${authToken}` },
        })
        if (adminResponse.ok) {
          setAdminStats(await adminResponse.json())
        }
      }
      setError('')
    } catch (err) {
      setError('Could not load dashboard')
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  if (loading) return <div className="dashboard-content"><p className="loading-text">Loading dashboard...</p></div>
  if (error) return <div className="dashboard-content"><div className="error-message">{error}</div></div>
  if (!stats) return null

  return (
    <div className="dashboard-content">
      <div className="users-section">
        <h2>Task Overview</h2>
        <div className="stats-grid">
          <div className="stat-card blue">
            <div className="stat-value">{stats.todo_count}</div>
            <div className="stat-label">To Do</div>
          </div>
          <div className="stat-card yellow">
            <div className="stat-value">{stats.in_progress_count}</div>
            <div className="stat-label">In Progress</div>
          </div>
          <div className="stat-card green">
            <div className="stat-value">{stats.done_count}</div>
            <div className="stat-label">Done</div>
          </div>
          <div className="stat-card red">
            <div className="stat-value">{stats.overdue_count}</div>
            <div className="stat-label">Overdue</div>
          </div>
          <div className="stat-card orange">
            <div className="stat-value">{stats.due_today_count}</div>
            <div className="stat-label">Due Today</div>
          </div>
          <div className="stat-card purple">
            <div className="stat-value">{stats.due_this_week_count}</div>
            <div className="stat-label">Due This Week</div>
          </div>
        </div>
      </div>

      {adminStats && (
        <div className="users-section" style={{marginTop: '20px'}}>
          <h2>System Metrics (Admin)</h2>
          <div className="stats-grid">
            <div className="stat-card blue">
              <div className="stat-value">{adminStats.total_users}</div>
              <div className="stat-label">Total Users</div>
            </div>
            <div className="stat-card green">
              <div className="stat-value">{adminStats.active_users}</div>
              <div className="stat-label">Active Users</div>
            </div>
            <div className="stat-card purple">
              <div className="stat-value">{adminStats.total_tasks}</div>
              <div className="stat-label">Total Tasks</div>
            </div>
            <div className="stat-card orange">
              <div className="stat-value">{adminStats.recent_activity_count}</div>
              <div className="stat-label">Activity (24h)</div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default Dashboard
