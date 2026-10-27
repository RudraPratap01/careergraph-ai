/**
 * Navbar — responsive primary navigation.
 *
 * Desktop: inline links, user chip and logout.
 * ≤1080px: links collapse into an accessible menu button. The panel closes on
 * route change, on Escape (returning focus to the trigger) and after logout.
 * Active links expose `aria-current="page"`.
 */

import { useEffect, useId, useRef, useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import Icon from './Icon'
import Logo from './Logo'

const DASHBOARD_LINK = { to: '/dashboard', label: 'Dashboard' }
const PROFILE_LINK = { to: '/profile', label: 'Profile' }

const STUDENT_LINKS = [
  DASHBOARD_LINK,
  PROFILE_LINK,
  { to: '/resume', label: 'Resume' },
  { to: '/career-gap', label: 'Skill Gap' },
  { to: '/roadmap', label: 'Roadmap' },
  { to: '/advisor', label: 'Advisor' },
  { to: '/assessments', label: 'Assessments' },
  { to: '/verification', label: 'Verification' },
  { to: '/mentors', label: 'Mentors' },
]

const ALUMNI_LINKS = [
  DASHBOARD_LINK,
  PROFILE_LINK,
  { to: '/mentors', label: 'Requests' },
]

/** Returns the navigation entries for a role, without duplicating markup. */
function linksForRole(role) {
  if (role === 'student') return STUDENT_LINKS
  if (role === 'alumni') return ALUMNI_LINKS
  return [DASHBOARD_LINK, PROFILE_LINK]
}

const ROLE_BADGE = {
  student: 'badge-info',
  alumni: 'badge-strong',
  admin: 'badge-medium',
}

export default function Navbar() {
  const { isAuthenticated, user, logout } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  // Store the path the menu was opened on. A route change makes the menu
  // disappear without an effect that would trigger an extra render.
  const [openPath, setOpenPath] = useState(null)
  const menuId = useId()
  const toggleRef = useRef(null)
  const menuOpen = openPath === location.pathname
  const setMenuOpen = (open) => setOpenPath(open ? location.pathname : null)

  // Escape closes the menu and restores focus to its trigger.
  useEffect(() => {
    if (!menuOpen) return undefined
    const handleKeyDown = (event) => {
      if (event.key === 'Escape') {
        setOpenPath(null)
        toggleRef.current?.focus()
      }
    }
    document.addEventListener('keydown', handleKeyDown)
    return () => document.removeEventListener('keydown', handleKeyDown)
  }, [menuOpen])

  const links = linksForRole(user?.role)
  const isActive = (path) => location.pathname === path

  const handleLogout = () => {
    setOpenPath(null)
    logout()
    navigate('/')
  }

  const toggleMenu = () => setMenuOpen(!menuOpen)

  return (
    <nav className="app-nav" aria-label="Primary">
      <div className="nav-inner">
        <Logo />

        {isAuthenticated ? (
          <>
            <div className="nav-links">
              {links.map((link) => (
                <Link
                  key={link.to}
                  to={link.to}
                  className="nav-link"
                  aria-current={isActive(link.to) ? 'page' : undefined}
                >
                  {link.label}
                </Link>
              ))}

              <span className="nav-divider" aria-hidden="true" />

              <div className="nav-user">
                <span className="nav-avatar" aria-hidden="true">
                  {user?.full_name?.[0]?.toUpperCase() || '?'}
                </span>
                <span className="nav-user-name">{user?.full_name?.split(' ')[0]}</span>
                <RoleBadge role={user?.role} />
              </div>

              <button
                id="btn-logout"
                type="button"
                className="btn btn-ghost btn-sm"
                onClick={handleLogout}
                aria-label="Log out"
              >
                <Icon name="logout" size={15} />
                <span>Log out</span>
              </button>
            </div>

            <button
              ref={toggleRef}
              type="button"
              className="nav-toggle"
              aria-expanded={menuOpen}
              aria-controls={menuId}
              aria-label={menuOpen ? 'Close navigation menu' : 'Open navigation menu'}
              onClick={toggleMenu}
            >
              <Icon name={menuOpen ? 'close' : 'menu'} />
            </button>
          </>
        ) : (
          <>
            <div className="nav-links">
              <Link
                to="/login"
                className="nav-link"
                aria-current={isActive('/login') ? 'page' : undefined}
              >
                Log in
              </Link>
              <Link to="/register" className="btn btn-primary btn-sm" id="btn-nav-register">
                Get started
              </Link>
            </div>

            <button
              ref={toggleRef}
              type="button"
              className="nav-toggle"
              aria-expanded={menuOpen}
              aria-controls={menuId}
              aria-label={menuOpen ? 'Close navigation menu' : 'Open navigation menu'}
              onClick={toggleMenu}
            >
              <Icon name={menuOpen ? 'close' : 'menu'} />
            </button>
          </>
        )}
      </div>

      {/* Mobile panel: rendered for both auth states so every action stays reachable. */}
      <div id={menuId} className={`nav-mobile${menuOpen ? ' open' : ''}`} hidden={!menuOpen}>
        <div className="nav-mobile-panel">
          {isAuthenticated ? (
            <>
              {links.map((link) => (
                <Link
                  key={link.to}
                  to={link.to}
                  className="nav-mobile-link"
                  aria-current={isActive(link.to) ? 'page' : undefined}
                  onClick={() => setOpenPath(null)}
                >
                  {link.label}
                  {isActive(link.to) && <Icon name="check" size={15} />}
                </Link>
              ))}

              <div className="nav-mobile-user">
                <span className="nav-avatar" aria-hidden="true">
                  {user?.full_name?.[0]?.toUpperCase() || '?'}
                </span>
                <div style={{ minWidth: 0 }}>
                  <div className="small" style={{ fontWeight: 600 }}>{user?.full_name}</div>
                  <div className="tiny muted" style={{ overflow: 'hidden', textOverflow: 'ellipsis' }}>
                    {user?.email}
                  </div>
                </div>
                <span style={{ marginLeft: 'auto' }}>
                  <RoleBadge role={user?.role} />
                </span>
              </div>

              <div className="nav-mobile-actions">
                <button type="button" className="btn btn-secondary btn-sm" onClick={handleLogout}>
                  <Icon name="logout" size={15} />
                  Log out
                </button>
              </div>
            </>
          ) : (
            <>
              <Link
                to="/login"
                className="nav-mobile-link"
                aria-current={isActive('/login') ? 'page' : undefined}
                onClick={() => setOpenPath(null)}
              >
                Log in
              </Link>
              <div className="nav-mobile-actions">
                <Link to="/register" className="btn btn-primary" style={{ width: '100%' }}>
                  Create an account
                </Link>
              </div>
            </>
          )}
        </div>
      </div>
    </nav>
  )
}

function RoleBadge({ role }) {
  if (!role) return null
  return (
    <span
      className={`badge ${ROLE_BADGE[role] || 'badge-neutral'}`}
      style={{ fontSize: '0.66rem', textTransform: 'capitalize', padding: '0.1rem 0.45rem' }}
    >
      {role}
    </span>
  )
}
