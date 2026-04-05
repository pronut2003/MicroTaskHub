import { useState, useEffect, useCallback } from 'react'
import TaskModal from './TaskModal'

function TaskList({ authToken, userRole, onLogout }) {
  const [tasks, setTasks] = useState([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [pageSize] = useState(10)
  const [filterStatus, setFilterStatus] = useState('')
  const [filterPriority, setFilterPriority] = useState('')
  const [sortBy, setSortBy] = useState('created_at')
  const [sortOrder, setSortOrder] = useState('desc')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [showModal, setShowModal] = useState(false)
  const [editingTask, setEditingTask] = useState(null)

  const fetchTasks = useCallback(async () => {
    try {
      setLoading(true)
      const params = new URLSearchParams({
        page: page.toString(),
        page_size: pageSize.toString(),
        sort_by: sortBy,
        sort_order: sortOrder,
      })
      if (filterStatus) params.set('status', filterStatus)
      if (filterPriority) params.set('priority', filterPriority)

      const response = await fetch(`/api/tasks/?${params}`, {
        headers: { 'Authorization': `Bearer ${authToken}` },
      })
      if (response.status === 401) { onLogout(); return }
      if (!response.ok) throw new Error('Failed to fetch tasks')
      const data = await response.json()
      setTasks(data.tasks)
      setTotal(data.total)
      setError('')
    } catch (err) {
      setError('Could not load tasks')
      console.error(err)
    } finally {
      setLoading(false)
    }
  }, [authToken, page, pageSize, filterStatus, filterPriority, sortBy, sortOrder, onLogout])

  useEffect(() => { fetchTasks() }, [fetchTasks])

  const handleDelete = async (taskId) => {
    if (!window.confirm('Are you sure you want to delete this task?')) return
    try {
      const response = await fetch(`/api/tasks/${taskId}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${authToken}` },
      })
      if (response.status === 401) { onLogout(); return }
      if (!response.ok) {
        const data = await response.json()
        alert(data.detail || 'Failed to delete task')
        return
      }
      fetchTasks()
    } catch (err) {
      console.error(err)
    }
  }

  const handleEdit = (task) => {
    setEditingTask(task)
    setShowModal(true)
  }

  const handleCreate = () => {
    setEditingTask(null)
    setShowModal(true)
  }

  const totalPages = Math.ceil(total / pageSize)

  const formatDate = (dateStr) => {
    if (!dateStr) return '-'
    return new Date(dateStr).toLocaleDateString()
  }

  const isOverdue = (task) => {
    if (!task.due_date || task.status === 'done') return false
    return new Date(task.due_date) < new Date()
  }

  return (
    <div className="dashboard-content">
      <div className="users-section">
        <div className="section-header">
          <h2>Tasks</h2>
          <button className="create-task-button" onClick={handleCreate}>+ New Task</button>
        </div>

        <div className="filter-bar">
          <select value={filterStatus} onChange={(e) => { setFilterStatus(e.target.value); setPage(1) }} className="filter-select">
            <option value="">All Status</option>
            <option value="todo">To Do</option>
            <option value="in-progress">In Progress</option>
            <option value="done">Done</option>
          </select>
          <select value={filterPriority} onChange={(e) => { setFilterPriority(e.target.value); setPage(1) }} className="filter-select">
            <option value="">All Priority</option>
            <option value="low">Low</option>
            <option value="medium">Medium</option>
            <option value="high">High</option>
          </select>
          <select value={sortBy} onChange={(e) => setSortBy(e.target.value)} className="filter-select">
            <option value="created_at">Created</option>
            <option value="due_date">Due Date</option>
            <option value="priority">Priority</option>
            <option value="title">Title</option>
          </select>
          <button className="sort-toggle" onClick={() => setSortOrder(sortOrder === 'desc' ? 'asc' : 'desc')}>
            {sortOrder === 'desc' ? 'Newest' : 'Oldest'}
          </button>
        </div>

        {loading && <p className="loading-text">Loading tasks...</p>}
        {error && <div className="error-message">{error}</div>}

        {!loading && !error && tasks.length === 0 && (
          <p className="empty-state">No tasks found. Create your first task!</p>
        )}

        {!loading && tasks.length > 0 && (
          <>
            <div className="users-table-container">
              <table className="users-table">
                <thead>
                  <tr>
                    <th>Title</th>
                    <th>Status</th>
                    <th>Priority</th>
                    <th>Due Date</th>
                    {userRole !== 'User' && <th>Owner</th>}
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {tasks.map((task) => (
                    <tr key={task.id}>
                      <td className="task-title-cell">
                        <span>{task.title}</span>
                        {task.description && <small className="task-desc">{task.description}</small>}
                      </td>
                      <td>
                        <span className={`role-badge task-status-${task.status}`}>{task.status}</span>
                      </td>
                      <td>
                        <span className={`role-badge priority-${task.priority}`}>{task.priority}</span>
                      </td>
                      <td className={isOverdue(task) ? 'overdue-text' : ''}>
                        {formatDate(task.due_date)}
                      </td>
                      {userRole !== 'User' && <td>{task.owner_name || '-'}</td>}
                      <td className="actions-cell">
                        <button className="action-button action-edit" onClick={() => handleEdit(task)}>Edit</button>
                        <button className="action-button action-delete" onClick={() => handleDelete(task.id)}>Delete</button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {totalPages > 1 && (
              <div className="pagination">
                <button disabled={page <= 1} onClick={() => setPage(page - 1)}>Previous</button>
                <span>Page {page} of {totalPages}</span>
                <button disabled={page >= totalPages} onClick={() => setPage(page + 1)}>Next</button>
              </div>
            )}
          </>
        )}
      </div>

      {showModal && (
        <TaskModal
          authToken={authToken}
          task={editingTask}
          onClose={() => setShowModal(false)}
          onSaved={() => { setShowModal(false); fetchTasks() }}
        />
      )}
    </div>
  )
}

export default TaskList
