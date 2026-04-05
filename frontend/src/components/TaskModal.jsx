import { useState } from 'react'

function TaskModal({ authToken, task, onClose, onSaved }) {
  const [title, setTitle] = useState(task ? task.title : '')
  const [description, setDescription] = useState(task ? (task.description || '') : '')
  const [status, setStatus] = useState(task ? task.status : 'todo')
  const [priority, setPriority] = useState(task ? task.priority : 'medium')
  const [dueDate, setDueDate] = useState(task && task.due_date ? task.due_date.split('T')[0] : '')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!title.trim()) {
      setError('Title is required')
      return
    }

    setLoading(true)
    setError('')

    try {
      const body = { title: title.trim(), description: description.trim() || null, status, priority }
      if (dueDate) body.due_date = new Date(dueDate).toISOString()

      const url = task ? `/api/tasks/${task.id}` : '/api/tasks/'
      const method = task ? 'PUT' : 'POST'

      const response = await fetch(url, {
        method,
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${authToken}`,
        },
        body: JSON.stringify(body),
      })

      const data = await response.json()
      if (!response.ok) {
        setError(data.detail || 'Failed to save task')
        setLoading(false)
        return
      }

      onSaved()
    } catch (err) {
      setError('Failed to save task')
      console.error(err)
      setLoading(false)
    }
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>{task ? 'Edit Task' : 'Create Task'}</h2>
          <button className="modal-close" onClick={onClose}>&times;</button>
        </div>
        <form onSubmit={handleSubmit} className="auth-form">
          <div className="form-group">
            <label htmlFor="task-title">Title</label>
            <input
              type="text"
              id="task-title"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="Enter task title"
              disabled={loading}
            />
          </div>
          <div className="form-group">
            <label htmlFor="task-desc">Description</label>
            <textarea
              id="task-desc"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Enter description (optional)"
              disabled={loading}
              className="form-textarea"
              rows={3}
            />
          </div>
          <div className="form-row">
            <div className="form-group">
              <label htmlFor="task-status">Status</label>
              <select id="task-status" value={status} onChange={(e) => setStatus(e.target.value)} disabled={loading} className="form-select">
                <option value="todo">To Do</option>
                <option value="in-progress">In Progress</option>
                <option value="done">Done</option>
              </select>
            </div>
            <div className="form-group">
              <label htmlFor="task-priority">Priority</label>
              <select id="task-priority" value={priority} onChange={(e) => setPriority(e.target.value)} disabled={loading} className="form-select">
                <option value="low">Low</option>
                <option value="medium">Medium</option>
                <option value="high">High</option>
              </select>
            </div>
          </div>
          <div className="form-group">
            <label htmlFor="task-due">Due Date</label>
            <input
              type="date"
              id="task-due"
              value={dueDate}
              onChange={(e) => setDueDate(e.target.value)}
              disabled={loading}
            />
          </div>
          {error && <div className="error-message">{error}</div>}
          <button type="submit" className="submit-button" disabled={loading}>
            {loading ? 'Saving...' : (task ? 'Update Task' : 'Create Task')}
          </button>
        </form>
      </div>
    </div>
  )
}

export default TaskModal
