import React, { useState } from 'react'

function CalendarView({ tasks, onEdit, onDateRangeChange }) {
    const [currentDate, setCurrentDate] = useState(new Date())

    const getDaysInMonth = (date) => {
        const year = date.getFullYear()
        const month = date.getMonth()
        return new Date(year, month + 1, 0).getDate()
    }

    const getFirstDayOfMonth = (date) => {
        const year = date.getFullYear()
        const month = date.getMonth()
        return new Date(year, month, 1).getDay()
    }

    const prevMonth = () => {
        const newDate = new Date(currentDate.getFullYear(), currentDate.getMonth() - 1, 1)
        setCurrentDate(newDate)
        if (onDateRangeChange) {
             const fromDate = new Date(newDate.getFullYear(), newDate.getMonth(), 1)
             const toDate = new Date(newDate.getFullYear(), newDate.getMonth() + 1, 0)
             onDateRangeChange(fromDate, toDate)
        }
    }

    const nextMonth = () => {
        const newDate = new Date(currentDate.getFullYear(), currentDate.getMonth() + 1, 1)
        setCurrentDate(newDate)
        if (onDateRangeChange) {
             const fromDate = new Date(newDate.getFullYear(), newDate.getMonth(), 1)
             const toDate = new Date(newDate.getFullYear(), newDate.getMonth() + 1, 0)
             onDateRangeChange(fromDate, toDate)
        }
    }

    const daysInMonth = getDaysInMonth(currentDate)
    const firstDay = getFirstDayOfMonth(currentDate)
    const days = []

    // Fill empty slots for previous month
    for (let i = 0; i < firstDay; i++) {
        days.push(<div key={`empty-${i}`} className="calendar-day empty"></div>)
    }

    // Fill days
    for (let i = 1; i <= daysInMonth; i++) {
        const date = new Date(currentDate.getFullYear(), currentDate.getMonth(), i)
        const dateStr = date.toISOString().split('T')[0]
        
        // Find tasks for this day (based on due_date)
        const dayTasks = tasks.filter(task => {
            if (!task.due_date) return false
            return task.due_date.split('T')[0] === dateStr
        })

        days.push(
            <div key={i} className="calendar-day">
                <div className="day-number">{i}</div>
                <div className="day-tasks">
                    {dayTasks.map(task => (
                        <div
                            key={task.id}
                            className={`calendar-task status-${task.status.toLowerCase()}`}
                            onClick={() => onEdit(task)}
                            title={task.title}
                        >
                            {task.title}
                        </div>
                    ))}
                </div>
            </div>
        )
    }

    return (
        <div className="calendar-container">
            <div className="calendar-header">
                <button onClick={prevMonth}>&lt;</button>
                <h2>{currentDate.toLocaleString('default', { month: 'long', year: 'numeric' })}</h2>
                <button onClick={nextMonth}>&gt;</button>
            </div>
            <div className="calendar-grid">
                <div className="weekday">Sun</div>
                <div className="weekday">Mon</div>
                <div className="weekday">Tue</div>
                <div className="weekday">Wed</div>
                <div className="weekday">Thu</div>
                <div className="weekday">Fri</div>
                <div className="weekday">Sat</div>
                {days}
            </div>
        </div>
    )
}

export default CalendarView
