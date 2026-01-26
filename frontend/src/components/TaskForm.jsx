import { useState, useEffect } from 'react'

function TaskForm({ task, onSubmit, onCancel, user }) {
    const [formData, setFormData] = useState({
        title: '',
        description: '',
        priority: 'medium',
        due_date: '',
        department: user.department || ''
    })

    useEffect(() => {
        if (task) {
            setFormData({
                title: task.title,
                description: task.description || '',
                priority: task.priority,
                due_date: task.due_date ? task.due_date.substring(0, 16) : '',
                department: task.department || ''
            })
        }
    }, [task])

    const handleSubmit = (e) => {
        e.preventDefault()
        
        // Validation
        if (formData.title.length > 255) {
            alert("Title must be less than 255 characters")
            return
        }
        
        if (formData.due_date) {
            const selected = new Date(formData.due_date)
            if (selected < new Date()) {
                alert("Due date must be in the future")
                return
            }
        }

        onSubmit({
            ...formData,
            due_date: formData.due_date || null
        })
    }

    return (
        <div className="task-form-overlay">
            <div className="task-form-modal">
                <h2>{task ? 'Edit Task' : 'New Task'}</h2>
                <form onSubmit={handleSubmit}>
                    <div className="form-group">
                        <label>Title</label>
                        <input 
                            required 
                            value={formData.title}
                            onChange={e => setFormData({...formData, title: e.target.value})}
                        />
                    </div>
                    
                    <div className="form-group">
                        <label>Description</label>
                        <textarea 
                            value={formData.description}
                            onChange={e => setFormData({...formData, description: e.target.value})}
                        />
                    </div>

                    <div className="form-row">
                        <div className="form-group">
                            <label>Priority</label>
                            <select 
                                value={formData.priority}
                                onChange={e => setFormData({...formData, priority: e.target.value})}
                            >
                                <option value="low">Low</option>
                                <option value="medium">Medium</option>
                                <option value="high">High</option>
                                <option value="critical">Critical</option>
                            </select>
                        </div>

                        <div className="form-group">
                            <label>Due Date</label>
                            <input 
                                type="datetime-local"
                                value={formData.due_date}
                                onChange={e => setFormData({...formData, due_date: e.target.value})}
                            />
                        </div>
                    </div>
                    
                    {(user.role === 'Admin' || user.role === 'Manager') && (
                         <div className="form-group">
                            <label>Department</label>
                            <input 
                                value={formData.department}
                                onChange={e => setFormData({...formData, department: e.target.value})}
                                placeholder="e.g. Engineering"
                            />
                        </div>
                    )}

                    <div className="form-actions">
                        <button type="button" onClick={onCancel} className="btn-secondary">Cancel</button>
                        <button type="submit" className="btn-primary">Save Task</button>
                    </div>
                </form>
            </div>
        </div>
    )
}

export default TaskForm
