/**
 * LoginPage — email/password sign-in.
 *
 * Uses the shared AuthAside for product context and PasswordInput for an
 * accessible show/hide control. Errors are announced with role="alert".
 */

import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import AuthAside from '../components/AuthAside'
import PasswordInput from '../components/PasswordInput'
import { useAuth } from '../hooks/useAuth'

export default function LoginPage() {
  const { login, loading } = useAuth()
  const navigate = useNavigate()

  const [form, setForm] = useState({ email: '', password: '' })
  const [error, setError] = useState(null)

  const handleChange = (event) => {
    const { name, value } = event.target
    setForm((current) => ({ ...current, [name]: value }))
  }

  const handleSubmit = async (event) => {
    event.preventDefault()
    setError(null)
    const result = await login(form.email, form.password)
    if (result.success) {
      navigate('/dashboard')
    } else {
      setError(result.error)
    }
  }

  return (
    <div className="auth-layout">
      <AuthAside
        title="Welcome back to your career graph."
        description="Your profile, evidence, readiness score and roadmap are exactly where you left them."
      />

      <div className="auth-main">
        <div className="auth-card fade-up">
          <h1 className="auth-heading">Sign in</h1>
          <p className="auth-subheading">Continue to your career dashboard.</p>

          <div className="card">
            {error && (
              <div className="alert alert-error" role="alert" style={{ marginBottom: '1.15rem' }}>
                {error}
              </div>
            )}

            <form onSubmit={handleSubmit} className="stack" style={{ gap: '1.05rem' }} noValidate={false}>
              <div>
                <label htmlFor="login-email" className="label">Email address</label>
                <input
                  id="login-email"
                  name="email"
                  type="email"
                  className="input"
                  placeholder="you@example.com"
                  value={form.email}
                  onChange={handleChange}
                  required
                  autoComplete="email"
                  autoFocus
                />
              </div>

              <PasswordInput
                id="login-password"
                name="password"
                label="Password"
                value={form.password}
                onChange={handleChange}
                autoComplete="current-password"
              />

              <button
                id="btn-login-submit"
                type="submit"
                className="btn btn-primary"
                disabled={loading}
                style={{ width: '100%', marginTop: '0.25rem' }}
              >
                {loading ? (
                  <><span className="spinner" style={{ width: '16px', height: '16px' }} /> Signing in…</>
                ) : 'Sign in'}
              </button>
            </form>

            <hr className="divider" />

            <p className="auth-switch" style={{ marginTop: 0 }}>
              New to CareerGraph AI? <Link to="/register">Create an account</Link>
            </p>
          </div>

          <p className="tiny muted center" style={{ marginTop: '1rem' }}>
            Your session is stored in this browser. Sign out on shared devices.
          </p>
        </div>
      </div>
    </div>
  )
}
