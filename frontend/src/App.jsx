import { useState, useEffect } from 'react'
import './App.css'
import Register from './components/Register'
import Login from './components/Login'
import Dashboard from './components/Dashboard'

function App() {
  const [authToken, setAuthToken] = useState(localStorage.getItem('token') || null)
  const [currentView, setCurrentView] = useState('login')
  const [user, setUser] = useState(null)

  const handleLogout = () => {
    localStorage.removeItem('token')
    localStorage.removeItem('userEmail')
    setAuthToken(null)
    setUser(null)
    setCurrentView('login')
  }

  useEffect(() => {
    if (authToken) {
      fetch('/api/users/me', {
        headers: {
          'Authorization': `Bearer ${authToken}`,
        },
      })
      .then(res => {
        if (res.ok) return res.json()
        throw new Error('Failed to fetch user')
      })
      .then(data => setUser(data))
      .catch(err => {
        console.error(err)
        handleLogout()
      })
    }
  }, [authToken])

  if (authToken && user) {
    return <Dashboard authToken={authToken} user={user} onLogout={handleLogout} />
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
            <Login onLoginSuccess={(token) => {
              setAuthToken(token)
              localStorage.setItem('token', token)
            }} />
          ) : (
            <Register onRegisterSuccess={() => {
              setCurrentView('login')
            }} />
          )}
        </div>
      </div>
    </div>
  )
}

export default App
