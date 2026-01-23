import { useState } from 'react'
import './App.css'
import Register from './components/Register'
import Login from './components/Login'
import Dashboard from './components/Dashboard'

function App() {
  const [authToken, setAuthToken] = useState(localStorage.getItem('token') || null)
  const [currentView, setCurrentView] = useState('login')

  const handleLogout = () => {
    localStorage.removeItem('token')
    localStorage.removeItem('userEmail')
    setAuthToken(null)
    setCurrentView('login')
  }

  if (authToken) {
    return <Dashboard authToken={authToken} onLogout={handleLogout} />
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
