/**
 * RegisterPage — student and alumni account creation.
 *
 * Client-side validation mirrors the backend rules so users get immediate
 * feedback, while the API remains the source of truth. The role picker is a
 * labelled fieldset of toggle buttons with `aria-pressed` state.
 */

import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import AuthAside from '../components/AuthAside'
import PasswordInput from '../components/PasswordInput'
import { useAuth } from '../hooks/useAuth'

const ROLES = [
  { value: 'student', label: 'Student', description: 'Analyze my skills' },
  { value: 'alumni', label: 'Alumni', description: 'Mentor students' },
]

const PASSWORD_HINT = 'At least 8 characters, including 1 uppercase letter and 1 digit.'

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

  const handleChange = (event) => {
    const { name, value } = event.target
    setForm((current) => ({ ...current, [name]: value }))
  }

  const validate = () => {
    if (form.full_name.trim().length < 2) return 'Full name must be at least 2 characters.'
    if (form.password.length < 8) return 'Password must be at least 8 characters.'
    if (!/[A-Z]/.test(form.password)) return 'Password must contain at least one uppercase letter.'
    if (!/\d/.test(form.password)) return 'Password must contain at least one digit.'
    if (form.password !== form.confirm_password) return 'Passwords do not match.'
    return null
  }

  const handleSubmit = async (event) => {
    event.preventDefault()
    setError(null)

    const validationError = validate()
    if (validationError) {
      setError(validationError)
      return
    }

    const { confirm_password: _confirmPassword, ...payload } = form
    const result = await register(payload)

    if (result.success) {
      navigate('/dashboard')
    } else {
      setError(result.error)
    }
  }

  return (
    <div className="auth-layout">
      <AuthAside
        title="Build a career plan you can actually explain."
        description="Track the evidence behind every skill, see the weighted gaps for your target role, and follow a roadmap that respects prerequisites."
      />

      <div className="auth-main">
        <div className="auth-card fade-up">
          <h1 className="auth-heading">Create your account</h1>
          <p className="auth-subheading">Start with a profile — you can refine the evidence later.</p>

          <div className="card">
            {error && (
              <div className="alert alert-error" role="alert" style={{ marginBottom: '1.15rem' }}>
                {error}
              </div>
            )}

            <form onSubmit={handleSubmit} className="stack" style={{ gap: '0.95rem' }}>
              <fieldset style={{ border: 0, padding: 0, margin: 0 }}>
                <legend className="label">I am a</legend>
                <div className="role-picker">
                  {ROLES.map((role) => (
                    <button
                      key={role.value}
                      type="button"
                      id={`btn-role-${role.value}`}
                      className="role-option"
                      aria-pressed={form.role === role.value}
                      onClick={() => setForm((current) => ({ ...current, role: role.value }))}
                      disabled={loading}
                    >
                      <strong>{role.label}</strong>
                      <span>{role.description}</span>
                    </button>
                  ))}
                </div>
              </fieldset>

              <div>
                <label htmlFor="reg-name" className="label">Full name</label>
                <input
                  id="reg-name"
                  name="full_name"
                  type="text"
                  className="input"
                  placeholder="Aarav Sharma"
                  value={form.full_name}
                  onChange={handleChange}
                  autoComplete="name"
                  required
                />
              </div>

              <div>
                <label htmlFor="reg-email" className="label">Email address</label>
                <input
                  id="reg-email"
                  name="email"
                  type="email"
                  className="input"
                  placeholder="you@example.com"
                  value={form.email}
                  onChange={handleChange}
                  autoComplete="email"
                  required
                />
              </div>

              <PasswordInput
                id="reg-password"
                name="password"
                label="Password"
                value={form.password}
                onChange={handleChange}
                autoComplete="new-password"
                hint={PASSWORD_HINT}
              />

              <PasswordInput
                id="reg-confirm"
                name="confirm_password"
                label="Confirm password"
                value={form.confirm_password}
                onChange={handleChange}
                autoComplete="new-password"
              />

              <button
                id="btn-register-submit"
                type="submit"
                className="btn btn-primary"
                disabled={loading}
                style={{ width: '100%', marginTop: '0.25rem' }}
              >
                {loading ? (
                  <><span className="spinner" style={{ width: '16px', height: '16px' }} /> Creating account…</>
                ) : 'Create account'}
              </button>
            </form>

            <hr className="divider" />

            <p className="auth-switch" style={{ marginTop: 0 }}>
              Already have an account? <Link to="/login">Sign in</Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
