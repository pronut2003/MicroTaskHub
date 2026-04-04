import { useState, useEffect } from 'react'
import AdminPanel from './AdminPanel'
import TaskList from './TaskList'
import TaskBoard from './TaskBoard'
import CalendarView from './CalendarView'
import TaskForm from './TaskForm'
import DashboardStats from './DashboardStats'

function Dashboard({ authToken, user, onLogout }) {
  const [activeTab, setActiveTab] = useState('overview')
  const [viewMode, setViewMode] = useState('list') 
  const [tasks, setTasks] = useState([])
  const [users, setUsers] = useState([])
  const [auditLogs, setAuditLogs] = useState([])
  const [loading, setLoading] = useState(false)
  const [showTaskModal, setShowTaskModal] = useState(false)
  const [editingTask, setEditingTask] = useState(null)
  
  const isAdmin = user?.roles?.includes('Admin') || user?.role === 'admin'
  const isManager = user?.roles?.includes('Manager') || user?.role === 'manager' || isAdmin
  const canManageUsers = isAdmin || isManager

  useEffect(() => {
    if (activeTab === 'tasks') {
        fetchTasks()
    } else if (activeTab === 'users' && canManageUsers) {
        fetchUsers()
    } else if (activeTab === 'audit' && isAdmin) {
        fetchAuditLogs()
    }
  }, [activeTab])

  const fetchTasks = async (filters = {}) => {
      setLoading(true)
      try {
          const params = new URLSearchParams({
              limit: 100,
              ...filters
          })
          const res = await fetch(`/api/tasks/?${params}`, {
              headers: { 'Authorization': `Bearer ${authToken}` }
          })
          if (res.ok) {
              const data = await res.json()
              
              setTasks(data.items || data)
          }
      } catch (e) {
          console.error(e)
      } finally {
          setLoading(false)
      }
  }

  const fetchUsers = async () => {
    setLoading(true)
    try {
        const res = await fetch('/api/users/', {
            headers: { 'Authorization': `Bearer ${authToken}` }
        })
        if (res.ok) {
            const data = await res.json()
            setUsers(data)
        }
    } catch (e) {
        console.error(e)
    } finally {
        setLoading(false)
    }
  }

  const fetchAuditLogs = async () => {
      setLoading(true)
      try {
          const res = await fetch('/api/rbac/audit', {
              headers: { 'Authorization': `Bearer ${authToken}` }
          })
          if (res.ok) {
              const data = await res.json()
              setAuditLogs(data)
          }
      } catch (e) {
          console.error(e)
      } finally {
          setLoading(false)
      }
  }

  const handleCreateTask = async (taskData) => {
      try {
          const method = editingTask ? 'PUT' : 'POST'
          const url = editingTask ? `/api/tasks/${editingTask.id}` : '/api/tasks/'
          
          const res = await fetch(url, {
              method: method,
              headers: {
                  'Authorization': `Bearer ${authToken}`,
                  'Content-Type': 'application/json'
              },
              body: JSON.stringify(taskData)
          })
          
          if (res.ok) {
              setShowTaskModal(false)
              setEditingTask(null)
              fetchTasks()
          } else {
              alert('Failed to save task')
          }
      } catch (e) {
          console.error(e)
          alert('Error saving task')
      }
  }

  const handleDeleteTask = async (taskId) => {
      if (!window.confirm('Are you sure you want to delete this task?')) return
      
      try {
          const res = await fetch(`/api/tasks/${taskId}`, {
              method: 'DELETE',
              headers: { 'Authorization': `Bearer ${authToken}` }
          })
          if (res.ok) fetchTasks()
      } catch (e) {
          console.error(e)
      }
  }
  
  const handleStatusChange = async (taskId, newStatus) => {
      try {
          const res = await fetch(`/api/tasks/${taskId}`, {
              method: 'PUT',
              headers: {
                  'Authorization': `Bearer ${authToken}`,
                  'Content-Type': 'application/json'
              },
              body: JSON.stringify({ status: newStatus })
          })
          if (res.ok) fetchTasks()
      } catch (e) {
          console.error(e)
      }
  }

  return (
    <div className="dashboard-layout">
      {/* Sidebar */}
      <div className="sidebar">
        <div className="sidebar-brand">MicroTaskHub</div>
        <div 
            className={`nav-item ${activeTab === 'overview' ? 'active' : ''}`}
            onClick={() => setActiveTab('overview')}
        >
            Overview
        </div>
        <div 
            className={`nav-item ${activeTab === 'tasks' ? 'active' : ''}`}
            onClick={() => setActiveTab('tasks')}
        >
            Tasks
        </div>
        {canManageUsers && (
            <div 
                className={`nav-item ${activeTab === 'users' ? 'active' : ''}`}
                onClick={() => setActiveTab('users')}
            >
                Users
            </div>
        )}
        {isAdmin && (
            <div 
                className={`nav-item ${activeTab === 'audit' ? 'active' : ''}`}
                onClick={() => setActiveTab('audit')}
            >
                Audit Logs
            </div>
        )}
        {isManager && (
            <div 
                className={`nav-item ${activeTab === 'reports' ? 'active' : ''}`}
                onClick={() => {
                    setActiveTab('reports')
                    if (tasks.length === 0) fetchTasks()
                }}
            >
                Reports
            </div>
        )}
        <div style={{marginTop: 'auto'}}>
            <div className="nav-item" onClick={onLogout}>Logout</div>
        </div>
      </div>

      {/* Main Content */}
      <div className="main-content">
        <div className="content-header">
            <div>
                <h1>
                    {activeTab === 'overview' ? 'Dashboard Overview' : 
                     activeTab === 'tasks' ? 'Tasks' : 
                     activeTab === 'users' ? 'User Management' : 
                     activeTab === 'audit' ? 'Audit Logs' : 'Reports'}
                </h1>
                <p className="welcome-text">Logged in as {user?.full_name} ({user?.role})</p>
            </div>
            
            <div style={{display: 'flex', gap: '10px'}}>
                {activeTab === 'tasks' && (
                    <>
                        <div className="view-toggle">
                            <button 
                                className={`toggle-btn ${viewMode === 'list' ? 'active' : ''}`}
                                onClick={() => setViewMode('list')}
                            >
                                List
                            </button>
                            <button 
                                className={`toggle-btn ${viewMode === 'board' ? 'active' : ''}`}
                                onClick={() => setViewMode('board')}
                            >
                                Board
                            </button>
                            <button 
                                className={`toggle-btn ${viewMode === 'calendar' ? 'active' : ''}`}
                                onClick={() => setViewMode('calendar')}
                            >
                                Calendar
                            </button>
                        </div>
                        <button className="btn-primary" onClick={() => { setEditingTask(null); setShowTaskModal(true) }}>
                            New Task
                        </button>
                    </>
                )}
            </div>
        </div>

        {activeTab === 'overview' && (
            <DashboardStats authToken={authToken} userRole={user?.role} />
        )}

        {activeTab === 'tasks' && (
            <>
                {loading ? <p>Loading tasks...</p> : (
                    viewMode === 'list' ? (
                        <TaskList 
                            tasks={tasks} 
                            onEdit={(task) => { setEditingTask(task); setShowTaskModal(true) }}
                            onDelete={handleDeleteTask}
                        />
                    ) : viewMode === 'board' ? (
                        <TaskBoard 
                            tasks={tasks}
                            onEdit={(task) => { setEditingTask(task); setShowTaskModal(true) }}
                            onDelete={handleDeleteTask}
                            onStatusChange={handleStatusChange}
                        />
                    ) : (
                        <CalendarView 
                            tasks={tasks}
                            onEdit={(task) => { setEditingTask(task); setShowTaskModal(true) }}
                            onDateRangeChange={(start, end) => fetchTasks({ 
                                from_date: start.toISOString(), 
                                to_date: end.toISOString()
                            })}
                        />
                    )
                )}
            </>
        )}

        {activeTab === 'users' && canManageUsers && (
            <div className="users-section">
                {isAdmin && <AdminPanel authToken={authToken} onRoleChange={fetchUsers} />}
                
                <div className="users-table-container" style={{marginTop: '20px'}}>
                    <table className="users-table">
                        <thead>
                            <tr>
                                <th>Name</th>
                                <th>Email</th>
                                <th>Role</th>
                                <th>Dept</th>
                            </tr>
                        </thead>
                        <tbody>
                            {users.map(u => (
                                <tr key={u.id}>
                                    <td>{u.full_name}</td>
                                    <td>{u.email}</td>
                                    <td>{u.role}</td>
                                    <td>{u.department || '-'}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>
        )}

        {activeTab === 'audit' && isAdmin && (
            <div className="users-table-container">
                <table className="users-table">
                    <thead>
                        <tr>
                            <th>Time</th>
                            <th>User ID</th>
                            <th>Action</th>
                            <th>Details</th>
                        </tr>
                    </thead>
                    <tbody>
                        {auditLogs.map(log => (
                            <tr key={log.id}>
                                <td>{new Date(log.timestamp).toLocaleString()}</td>
                                <td>{log.user_id}</td>
                                <td>{log.action}</td>
                                <td>{log.details}</td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        )}

        {activeTab === 'reports' && isManager && (
            <div className="reports-container">
                <div className="report-card">
                    <h3>Tasks by Status</h3>
                    <div className="stats-grid">
                        {['PENDING', 'IN_PROGRESS', 'COMPLETED'].map(status => (
                            <div key={status} className="stat-item">
                                <span className="stat-label">{status.replace('_', ' ')}</span>
                                <span className="stat-value">
                                    {tasks.filter(t => t.status === status).length}
                                </span>
                            </div>
                        ))}
                    </div>
                </div>
                <div className="report-card">
                    <h3>Tasks by Priority</h3>
                    <div className="stats-grid">
                        {['LOW', 'MEDIUM', 'HIGH', 'CRITICAL'].map(p => (
                            <div key={p} className="stat-item">
                                <span className="stat-label">{p}</span>
                                <span className="stat-value">
                                    {tasks.filter(t => t.priority === p).length}
                                </span>
                            </div>
                        ))}
                    </div>
                </div>
            </div>
        )}
      </div>

      {showTaskModal && (
          <TaskForm 
              task={editingTask}
              user={user}
              onSubmit={handleCreateTask}
              onCancel={() => setShowTaskModal(false)}
          />
      )}
    </div>
  )
}

export default Dashboard
