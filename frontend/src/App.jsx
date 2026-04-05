import { useState } from 'react'
import './App.css'
import Register from './components/Register'
import Login from './components/Login'
import Dashboard from './components/Dashboard'
import TaskList from './components/TaskList'
import AdminUsers from './components/AdminUsers'

function App() {
  const [authToken, setAuthToken] = useState(localStorage.getItem('token') || null)
  const [userRole, setUserRole] = useState(localStorage.getItem('userRole') || 'User')
  const [currentView, setCurrentView] = useState(authToken ? 'dashboard' : 'login')

  const handleLogout = () => {
    localStorage.removeItem('token')
    localStorage.removeItem('userEmail')
    localStorage.removeItem('userName')
    localStorage.removeItem('userRole')
    setAuthToken(null)
    setUserRole('User')
    setCurrentView('login')
  }

  const handleLoginSuccess = (token) => {
    setAuthToken(token)
    setUserRole(localStorage.getItem('userRole') || 'User')
    localStorage.setItem('token', token)
    setCurrentView('dashboard')
  }

  if (authToken) {
    return (
      <div className="dashboard-container">
        <div className="dashboard-header">
          <div className="header-content">
            <h1>MicroTaskHub</h1>
            <p className="welcome-text">
              Welcome, <span className="user-email">{localStorage.getItem('userName') || 'User'}</span>
              <span className={`role-badge role-${userRole.toLowerCase()}`} style={{marginLeft: '10px'}}>{userRole}</span>
            </p>
          </div>
          <div className="header-right">
            <nav className="nav-tabs">
              <button
                className={`nav-tab ${currentView === 'dashboard' ? 'active' : ''}`}
                onClick={() => setCurrentView('dashboard')}
              >
                Dashboard
              </button>
              <button
                className={`nav-tab ${currentView === 'tasks' ? 'active' : ''}`}
                onClick={() => setCurrentView('tasks')}
              >
                Tasks
              </button>
              {userRole === 'Admin' && (
                <button
                  className={`nav-tab ${currentView === 'admin-users' ? 'active' : ''}`}
                  onClick={() => setCurrentView('admin-users')}
                >
                  Users
                </button>
              )}
            </nav>
            <button className="logout-button" onClick={handleLogout}>Logout</button>
          </div>
        </div>

        {currentView === 'dashboard' && (
          <Dashboard authToken={authToken} userRole={userRole} onLogout={handleLogout} />
        )}
        {currentView === 'tasks' && (
          <TaskList authToken={authToken} userRole={userRole} onLogout={handleLogout} />
        )}
        {currentView === 'admin-users' && userRole === 'Admin' && (
          <AdminUsers authToken={authToken} onLogout={handleLogout} />
        )}
      </div>
    )
  }

  return (
    <div className="auth-container">
      <div className="auth-card">
        <h1 className="app-title">MicroTaskHub</h1>

        <div className="auth-tabs">
          <button
            className={`tab-button ${currentView === 'login' ? 'active' : ''}`}
            onClick={() => setCurrentView('login')}
          >
            Login
          </button>
          <button
            className={`tab-button ${currentView === 'register' ? 'active' : ''}`}
            onClick={() => setCurrentView('register')}
          >
            Register
          </button>
        </div>

        <div className="auth-content">
          {currentView === 'login' ? (
            <Login onLoginSuccess={handleLoginSuccess} />
          ) : (
            <Register onRegisterSuccess={() => setCurrentView('login')} />
          )}
        </div>
      </div>
    </div>
  )
}

export default App
