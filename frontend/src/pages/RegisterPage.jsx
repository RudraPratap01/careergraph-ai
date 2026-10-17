/**
 * Register Page
 * Supports student and alumni registration.
 * Validates client-side before sending to the API.
 */

import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'

export default function RegisterPage() {
  const { register, loading } = useAuth()
  const navigate = useNavigate()

  const [form, setForm] = useState({
    full_name: '',
    email: '',
    password: '',
    confirm_password: '',
    role: 'student',
  })
  const [error, setError] = useState(null)

  const handleChange = (e) => setForm({ ...form, [e.target.name]: e.target.value })

  const validate = () => {
    if (form.full_name.trim().length < 2) return 'Full name must be at least 2 characters.'
    if (form.password.length < 8) return 'Password must be at least 8 characters.'
    if (!/[A-Z]/.test(form.password)) return 'Password must contain at least one uppercase letter.'
    if (!/\d/.test(form.password)) return 'Password must contain at least one digit.'
    if (form.password !== form.confirm_password) return 'Passwords do not match.'
    return null
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError(null)

    const validationError = validate()
    if (validationError) { setError(validationError); return }

    const { confirm_password: _confirm_password, ...payload } = form
    const result = await register(payload)

    if (result.success) {
      navigate('/dashboard')
    } else {
      setError(result.error)
    }
  }

  return (
    <div style={{ minHeight: 'calc(100vh - 64px)', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '2rem 1.5rem' }}>
      <div className="fade-up" style={{ width: '100%', maxWidth: '460px' }}>
        {/* Header */}
        <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
          <div style={{ fontSize: '2rem', marginBottom: '0.75rem' }}>🚀</div>
          <h1 style={{ fontSize: '1.625rem', fontWeight: 700, marginBottom: '0.5rem' }}>Create your account</h1>
          <p style={{ color: 'var(--color-text-secondary)', fontSize: '0.9rem' }}>
            Start your career skill analysis in minutes
          </p>
        </div>

        {/* Card */}
        <div className="card" style={{ padding: '2rem' }}>
          {error && (
            <div className="alert alert-error" style={{ marginBottom: '1.25rem' }}>
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            {/* Role selector */}
            <div>
              <label className="label">I am a</label>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem' }}>
                {[
                  { value: 'student', label: '🎓 Student', desc: 'Analyze my skills' },
                  { value: 'alumni',  label: '💼 Alumni',  desc: 'Mentor students' },
                ].map((r) => (
                  <button
                    key={r.value}
                    type="button"
                    id={`btn-role-${r.value}`}
                    onClick={() => setForm({ ...form, role: r.value })}
                    style={{
                      padding: '0.75rem',
                      borderRadius: '8px',
                      border: `1px solid ${form.role === r.value ? 'var(--color-brand-primary)' : 'var(--color-border)'}`,
                      background: form.role === r.value ? 'rgba(99,102,241,0.1)' : 'var(--color-bg-elevated)',
                      cursor: 'pointer',
                      textAlign: 'left',
                    }}
                  >
                    <div style={{ fontSize: '0.9rem', fontWeight: 600, color: form.role === r.value ? 'var(--color-brand-light)' : 'var(--color-text-primary)' }}>
                      {r.label}
                    </div>
                    <div style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)', marginTop: '0.125rem' }}>{r.desc}</div>
                  </button>
                ))}
              </div>
            </div>

            <div>
              <label htmlFor="reg-name" className="label">Full name</label>
              <input id="reg-name" name="full_name" type="text" className="input"
                placeholder="Aarav Sharma" value={form.full_name} onChange={handleChange} required />
            </div>

            <div>
              <label htmlFor="reg-email" className="label">Email address</label>
              <input id="reg-email" name="email" type="email" className="input"
                placeholder="you@example.com" value={form.email} onChange={handleChange} required />
            </div>

            <div>
              <label htmlFor="reg-password" className="label">Password</label>
              <input id="reg-password" name="password" type="password" className="input"
                placeholder="Min 8 chars, 1 uppercase, 1 digit" value={form.password} onChange={handleChange} required />
            </div>

            <div>
              <label htmlFor="reg-confirm" className="label">Confirm password</label>
              <input id="reg-confirm" name="confirm_password" type="password" className="input"
                placeholder="••••••••" value={form.confirm_password} onChange={handleChange} required />
            </div>

            <button
              id="btn-register-submit"
              type="submit"
              className="btn btn-primary"
              disabled={loading}
              style={{ width: '100%', justifyContent: 'center', marginTop: '0.25rem', padding: '0.75rem' }}
            >
              {loading ? (
                <><span className="spinner" style={{ width: '16px', height: '16px' }} /> Creating account…</>
              ) : 'Create Account →'}
            </button>
          </form>

          <hr className="divider" />

          <div style={{ textAlign: 'center', fontSize: '0.875rem', color: 'var(--color-text-secondary)' }}>
            Already have an account?{' '}
            <Link to="/login" style={{ color: 'var(--color-brand-light)', fontWeight: 600 }}>Login</Link>
          </div>
        </div>
      </div>
    </div>
  )
}
