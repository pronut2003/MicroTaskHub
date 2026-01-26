import { useState, useEffect } from 'react'

function DashboardStats({ authToken, userRole }) {
    const [taskStats, setTaskStats] = useState(null)
    const [timeStats, setTimeStats] = useState(null)
    const [activityStats, setActivityStats] = useState(null)
    const [adminStats, setAdminStats] = useState(null)
    const [loading, setLoading] = useState(true)

    useEffect(() => {
        const fetchStats = async () => {
            try {
                const headers = { 'Authorization': `Bearer ${authToken}` }
                
                // Fetch all stats in parallel
                const promises = [
                    fetch('/api/dashboard/stats', { headers }).then(r => r.json()),
                    fetch('/api/dashboard/tasks-time', { headers }).then(r => r.json()),
                    fetch('/api/dashboard/activity', { headers }).then(r => r.json())
                ]

                if (userRole === 'Admin') {
                    promises.push(fetch('/api/dashboard/admin/stats', { headers }).then(r => r.json()))
                }

                const results = await Promise.all(promises)
                
                setTaskStats(results[0])
                setTimeStats(results[1])
                setActivityStats(results[2])
                if (userRole === 'Admin') {
                    setAdminStats(results[3])
                }
            } catch (error) {
                console.error("Error fetching dashboard stats:", error)
            } finally {
                setLoading(false)
            }
        }

        fetchStats()
    }, [authToken, userRole])

    if (loading) return <div>Loading statistics...</div>

    return (
        <div className="dashboard-stats">
            {/* General Stats */}
            <div className="dashboard-stats-grid">
                <div className="stat-card">
                    <h3>Tasks Overview</h3>
                    <div className="stat-value">
                        {Object.values(taskStats || {}).reduce((a, b) => a + b, 0)}
                    </div>
                    <div className="stat-chart-container" style={{height: 'auto', marginTop: '16px'}}>
                        {taskStats && Object.entries(taskStats).map(([status, count]) => {
                             const total = Object.values(taskStats).reduce((a, b) => a + b, 0) || 1;
                             const pct = (count / total) * 100;
                             const color = status === 'completed' ? '#10b981' : 
                                           status === 'in_progress' ? '#3b82f6' : 
                                           status === 'pending' ? '#f59e0b' : '#ef4444';
                             return (
                                 <div key={status} style={{marginBottom: '8px'}}>
                                     <div style={{display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem', marginBottom: '4px'}}>
                                         <span style={{textTransform: 'capitalize'}}>{status.replace('_', ' ')}</span>
                                         <span>{count}</span>
                                     </div>
                                     <div style={{height: '6px', background: '#f3f4f6', borderRadius: '3px', overflow: 'hidden'}}>
                                         <div style={{width: `${pct}%`, background: color, height: '100%'}}></div>
                                     </div>
                                 </div>
                             )
                        })}
                    </div>
                </div>

                <div className="stat-card">
                    <h3>Time Critical</h3>
                    <div className="stat-value">{timeStats?.due_today || 0}</div>
                    <div style={{fontSize: '0.9rem', color: '#666', marginTop: '8px'}}>
                        Due Today
                    </div>
                    <div style={{marginTop: '4px', fontSize: '0.9rem'}}>
                        <span style={{color: '#f59e0b'}}>Week: {timeStats?.due_week || 0}</span>
                        {' • '}
                        <span style={{color: '#ef4444'}}>Overdue: {timeStats?.overdue || 0}</span>
                    </div>
                </div>

                <div className="stat-card">
                    <h3>Activity (Last 7 Days)</h3>
                    <div className="stat-value">
                        {Object.values(activityStats || {}).reduce((a, b) => a + b, 0)}
                    </div>
                    <div style={{fontSize: '0.9rem', color: '#666', marginTop: '8px'}}>
                        Actions logged
                    </div>
                </div>
            </div>

            {/* Admin Specific Stats */}
            {userRole === 'Admin' && adminStats && (
                <>
                    <h3 style={{margin: '24px 0 16px'}}>System Overview (Admin)</h3>
                    <div className="dashboard-stats-grid">
                        <div className="stat-card">
                            <h3>Active Users</h3>
                            <div className="stat-value">{adminStats.active_users}</div>
                        </div>
                        <div className="stat-card">
                            <h3>System Operations (30d)</h3>
                            <div className="stat-value">{adminStats.total_operations_30d}</div>
                        </div>
                        <div className="stat-card">
                            <h3>Error Rate</h3>
                            <div className="stat-value error-rate">{adminStats.error_rate}%</div>
                            <div style={{fontSize: '0.9rem', color: '#666', marginTop: '8px'}}>
                                {adminStats.error_count_30d} errors
                            </div>
                        </div>
                    </div>
                </>
            )}
        </div>
    )
}

export default DashboardStats
