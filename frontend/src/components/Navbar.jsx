/**
 * Navbar — top navigation bar.
 * Shows different links based on auth state and user role.
 */

import { Link, useNavigate, useLocation } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'

export default function Navbar() {
  const { isAuthenticated, user, logout } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()

  const handleLogout = () => {
    logout()
    navigate('/')
  }

  const isActive = (path) => location.pathname === path

  return (
    <nav style={{
      background: 'rgba(10,14,26,0.95)',
      backdropFilter: 'blur(12px)',
      borderBottom: '1px solid var(--color-border)',
      position: 'sticky',
      top: 0,
      zIndex: 100,
    }}>
      <div style={{
        maxWidth: '1200px',
        margin: '0 auto',
        padding: '0 1.5rem',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        height: '64px',
      }}>
        {/* Logo */}
        <Link to="/" style={{ display: 'flex', alignItems: 'center', gap: '0.625rem', textDecoration: 'none' }}>
          <div style={{
            width: '32px', height: '32px',
            background: 'linear-gradient(135deg, #6366f1, #818cf8)',
            borderRadius: '8px',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            fontSize: '16px',
          }}>⚡</div>
          <span style={{
            fontFamily: "'Space Grotesk', sans-serif",
            fontWeight: 700,
            fontSize: '1.1rem',
            color: 'var(--color-text-primary)',
          }}>
            CareerGraph <span style={{ color: 'var(--color-brand-light)' }}>AI</span>
          </span>
        </Link>

        {/* Nav links */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
          {isAuthenticated ? (
            <>
              <NavLink to="/dashboard" active={isActive('/dashboard')}>Dashboard</NavLink>
              <NavLink to="/profile" active={isActive('/profile')}>Profile</NavLink>
              {user?.role === 'student' && (
                <NavLink to="/resume" active={isActive('/resume')}>Resume</NavLink>
              )}

              <div style={{ width: '1px', height: '20px', background: 'var(--color-border)', margin: '0 0.5rem' }} />

              <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                <div style={{
                  display: 'flex', alignItems: 'center', gap: '0.5rem',
                  padding: '0.375rem 0.75rem',
                  background: 'var(--color-bg-surface)',
                  border: '1px solid var(--color-border)',
                  borderRadius: '8px',
                }}>
                  <div style={{
                    width: '24px', height: '24px',
                    background: 'var(--color-brand-primary)',
                    borderRadius: '50%',
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    fontSize: '11px', fontWeight: 700,
                  }}>
                    {user?.full_name?.[0]?.toUpperCase() || '?'}
                  </div>
                  <span style={{ fontSize: '0.85rem', color: 'var(--color-text-secondary)' }}>
                    {user?.full_name?.split(' ')[0]}
                  </span>
                  <RoleBadge role={user?.role} />
                </div>

                <button
                  id="btn-logout"
                  className="btn btn-secondary"
                  onClick={handleLogout}
                  style={{ fontSize: '0.85rem', padding: '0.375rem 0.875rem' }}
                >
                  Logout
                </button>
              </div>
            </>
          ) : (
            <>
              <NavLink to="/login" active={isActive('/login')}>Login</NavLink>
              <Link to="/register" className="btn btn-primary" id="btn-nav-register" style={{ marginLeft: '0.5rem' }}>
                Get Started
              </Link>
            </>
          )}
        </div>
      </div>
    </nav>
  )
}

function NavLink({ to, children, active }) {
  return (
    <Link
      to={to}
      style={{
        padding: '0.375rem 0.75rem',
        borderRadius: '6px',
        fontSize: '0.9rem',
        fontWeight: 500,
        color: active ? 'var(--color-brand-light)' : 'var(--color-text-secondary)',
        background: active ? 'rgba(99,102,241,0.1)' : 'transparent',
        textDecoration: 'none',
        transition: 'all 0.15s',
      }}
    >
      {children}
    </Link>
  )
}

function RoleBadge({ role }) {
  const styles = {
    student: { bg: 'rgba(99,102,241,0.15)', color: '#818cf8' },
    alumni:  { bg: 'rgba(16,185,129,0.15)', color: '#10b981' },
    admin:   { bg: 'rgba(245,158,11,0.15)', color: '#f59e0b' },
  }
  const s = styles[role] || styles.student
  return (
    <span style={{
      fontSize: '0.7rem', fontWeight: 700, textTransform: 'capitalize',
      padding: '0.1rem 0.4rem', borderRadius: '4px',
      background: s.bg, color: s.color,
    }}>
      {role}
    </span>
  )
}
