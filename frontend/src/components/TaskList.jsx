import { useState } from 'react'

function TaskList({ tasks, onEdit, onDelete }) {
    return (
        <div className="task-list-container">
            <table className="users-table">
                <thead>
                    <tr>
                        <th>Title</th>
                        <th>Status</th>
                        <th>Priority</th>
                        <th>Due Date</th>
                        <th>Dept</th>
                        <th>Assignee</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    {tasks.map(task => (
                        <tr key={task.id}>
                            <td>{task.title}</td>
                            <td>
                                <span className={`status-badge status-${task.status}`}>
                                    {task.status.replace('_', ' ')}
                                </span>
                            </td>
                            <td>
                                <span className={`priority-text priority-${task.priority}`}>
                                    {task.priority}
                                </span>
                            </td>
                            <td>{task.due_date ? new Date(task.due_date).toLocaleDateString() : '-'}</td>
                            <td>{task.department || '-'}</td>
                            <td>{task.assignee ? task.assignee.full_name : 'Unassigned'}</td>
                            <td>
                                <button className="action-btn" onClick={() => onEdit(task)}>Edit</button>
                                <button className="action-btn danger" onClick={() => onDelete(task.id)} style={{marginLeft: '5px'}}>Delete</button>
                            </td>
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    )
}

export default TaskList
