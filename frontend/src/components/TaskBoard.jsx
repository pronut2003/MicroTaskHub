import { useState, useEffect } from 'react'

function TaskBoard({ tasks, onEdit, onDelete, onStatusChange }) {
    const columns = {
        pending: 'Pending',
        in_progress: 'In Progress',
        completed: 'Completed',
        cancelled: 'Cancelled'
    }

    const getPriorityColor = (p) => {
        switch(p) {
            case 'critical': return '#ef4444';
            case 'high': return '#f59e0b';
            case 'medium': return '#3b82f6';
            case 'low': return '#10b981';
            default: return '#6b7280';
        }
    }

    return (
        <div className="task-board">
            {Object.entries(columns).map(([statusKey, label]) => (
                <div key={statusKey} className="kanban-column">
                    <h3 className={`column-header header-${statusKey}`}>{label}</h3>
                    <div className="column-content">
                        {tasks.filter(t => t.status === statusKey).map(task => (
                            <div key={task.id} className="kanban-card">
                                <div className="card-header">
                                    <span 
                                        className="priority-badge"
                                        style={{backgroundColor: getPriorityColor(task.priority)}}
                                    >
                                        {task.priority}
                                    </span>
                                    <div className="card-actions">
                                        <button onClick={() => onEdit(task)}>✏️</button>
                                        <button onClick={() => onDelete(task.id)}>🗑️</button>
                                    </div>
                                </div>
                                <h4>{task.title}</h4>
                                <p className="task-meta">Due: {task.due_date ? new Date(task.due_date).toLocaleDateString() : 'No date'}</p>
                                <div className="status-select-container">
                                    <select 
                                        value={task.status} 
                                        onChange={(e) => onStatusChange(task.id, e.target.value)}
                                        className="status-select-mini"
                                    >
                                        {Object.entries(columns).map(([k, l]) => (
                                            <option key={k} value={k}>{l}</option>
                                        ))}
                                    </select>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            ))}
        </div>
    )
}

export default TaskBoard
