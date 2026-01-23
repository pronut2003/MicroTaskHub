import { useState } from 'react'

function Register({ onRegisterSuccess }) {
  const [fullName, setFullName] = useState('')
  const [email, setEmail] = useState('')
  const [phoneNo, setPhoneNo] = useState('')
  const [role, setRole] = useState('User')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    
    if (!fullName || !email || !phoneNo || !password) {
      setError('All fields are required')
      return
    }

    if (fullName.length < 2) {
      setError('Full name must be at least 2 characters')
      return
    }

    if (!/^\d{10,}$/.test(phoneNo)) {
      setError('Phone number must be at least 10 digits (only numbers)')
      return
    }

    if (password.length < 6) {
      setError('Password must be at least 6 characters')
      return
    }

    setLoading(true)
    setError('')
    setSuccess('')

    try {
      const response = await fetch('/api/users/register', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          email,
          password,
          full_name: fullName,
          phone_no: phoneNo,
          role,
        }),
      })

      const data = await response.json()

      if (!response.ok) {
        setError(data.detail || 'Registration failed')
        setLoading(false)
        return
      }

      setSuccess('✅ Registration completed successfully!')
      console.log('Registration successful:', data)
      
      setFullName('')
      setEmail('')
      setPhoneNo('')
      setRole('User')
      setPassword('')

      setTimeout(() => {
        setSuccess('')
        onRegisterSuccess()
      }, 2000)
    } catch (err) {
      setError('Failed to connect to server. Please check if backend is running.')
      console.error('Registration error:', err)
      setLoading(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="auth-form">
      <div className="form-group">
        <label htmlFor="fullName">Full Name</label>
        <input
          type="text"
          id="fullName"
          value={fullName}
          onChange={(e) => setFullName(e.target.value)}
          placeholder="Enter your full name"
          disabled={loading}
        />
      </div>

      <div className="form-group">
        <label htmlFor="email">Email</label>
        <input
          type="email"
          id="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          placeholder="Enter your email"
          disabled={loading}
        />
      </div>

      <div className="form-group">
        <label htmlFor="phoneNo">Phone Number</label>
        <input
          type="tel"
          id="phoneNo"
          value={phoneNo}
          onChange={(e) => setPhoneNo(e.target.value.replace(/\D/g, ''))}
          placeholder="Enter your phone number (10+ digits only)"
          disabled={loading}
        />
      </div>

      <div className="form-group">
        <label htmlFor="role">Role</label>
        <select
          id="role"
          value={role}
          onChange={(e) => setRole(e.target.value)}
          disabled={loading}
          className="form-select"
        >
          <option value="User">User</option>
          <option value="Manager">Manager</option>
          <option value="Admin">Admin</option>
        </select>
      </div>

      <div className="form-group">
        <label htmlFor="password">Password</label>
        <input
          type="password"
          id="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          placeholder="Enter your password"
          disabled={loading}
        />
      </div>

      {error && <div className="error-message">{error}</div>}
      {success && <div className="success-message">{success}</div>}

      <button type="submit" className="submit-button" disabled={loading}>
        {loading ? 'Registering...' : 'Register'}
      </button>
    </form>
  )
}

export default Register
