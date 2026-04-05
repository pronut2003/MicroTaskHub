import { useState } from 'react'

function Login({ onLoginSuccess }) {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()

    if (!email || !password) {
      setError('Email and password are required')
      return
    }

    setLoading(true)
    setError('')

    try {
      const response = await fetch('/api/users/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      })

      const data = await response.json()

      if (!response.ok) {
        setError(data.detail || 'Login failed')
        setLoading(false)
        return
      }

      localStorage.setItem('userEmail', data.user.email)
      localStorage.setItem('userName', data.user.full_name)
      localStorage.setItem('userRole', data.user.role)
      setEmail('')
      setPassword('')
      onLoginSuccess(data.access_token)
    } catch (err) {
      setError('Failed to login. Please check if backend is running.')
      console.error(err)
      setLoading(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="auth-form">
      <div className="form-group">
        <label htmlFor="login-email">Email</label>
        <input
          type="email"
          id="login-email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          placeholder="Enter your email"
          disabled={loading}
        />
      </div>

      <div className="form-group">
        <label htmlFor="login-password">Password</label>
        <input
          type="password"
          id="login-password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          placeholder="Enter your password"
          disabled={loading}
        />
      </div>

      {error && <div className="error-message">{error}</div>}

      <button type="submit" className="submit-button" disabled={loading}>
        {loading ? 'Logging in...' : 'Login'}
      </button>
    </form>
  )
}

export default Login
