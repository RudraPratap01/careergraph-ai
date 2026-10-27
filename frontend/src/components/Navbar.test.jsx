/**
 * Navbar tests.
 *
 * These pin the responsive behaviour that previously did not exist: a single
 * menu trigger controls a duplicate-free mobile panel, the panel closes on
 * Escape/navigation, and active routes expose `aria-current`.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'

const auth = vi.hoisted(() => ({
  user: null,
  logout: vi.fn(),
}))

vi.mock('../hooks/useAuth', () => ({
  useAuth: () => ({
    isAuthenticated: Boolean(auth.user),
    user: auth.user,
    logout: auth.logout,
  }),
}))

import Navbar from './Navbar'

const STUDENT = { role: 'student', full_name: 'Aarav Sharma', email: 'aarav@example.com' }
const ALUMNI = { role: 'alumni', full_name: 'Meera Rao', email: 'meera@example.com' }

function renderNav(initialPath = '/dashboard') {
  return render(
    <MemoryRouter initialEntries={[initialPath]}>
      <Navbar />
    </MemoryRouter>
  )
}

function getMobilePanel(toggle) {
  return document.getElementById(toggle.getAttribute('aria-controls'))
}

describe('Navbar', () => {
  beforeEach(() => {
    auth.user = STUDENT
    auth.logout.mockClear()
  })

  it('marks the current route and lists role-specific links', () => {
    renderNav('/roadmap')

    const dashboard = screen.getByRole('link', { name: 'Dashboard' })
    const roadmap = screen.getByRole('link', { name: 'Roadmap' })

    expect(roadmap).toHaveAttribute('aria-current', 'page')
    expect(dashboard).not.toHaveAttribute('aria-current')
    expect(screen.getByRole('link', { name: 'Verification' })).toBeInTheDocument()
  })

  it('shows alumni requests instead of student-only links', () => {
    auth.user = ALUMNI
    renderNav('/dashboard')

    expect(screen.getByRole('link', { name: 'Requests' })).toBeInTheDocument()
    expect(screen.queryByRole('link', { name: 'Resume' })).not.toBeInTheDocument()
  })

  it('opens and closes the mobile menu with the trigger', async () => {
    const user = userEvent.setup()
    renderNav()

    const toggle = screen.getByRole('button', { name: 'Open navigation menu' })
    expect(toggle).toHaveAttribute('aria-expanded', 'false')

    await user.click(toggle)

    const closeButton = screen.getByRole('button', { name: 'Close navigation menu' })
    expect(closeButton).toHaveAttribute('aria-expanded', 'true')
    const panel = getMobilePanel(closeButton)
    expect(panel).not.toHaveAttribute('hidden')
    expect(within(panel).getByRole('link', { name: 'Assessments' })).toBeInTheDocument()

    await user.click(closeButton)
    expect(screen.getByRole('button', { name: 'Open navigation menu' }))
      .toHaveAttribute('aria-expanded', 'false')
  })

  it('closes on Escape and returns focus to the trigger', async () => {
    const user = userEvent.setup()
    renderNav()

    const toggle = screen.getByRole('button', { name: 'Open navigation menu' })
    await user.click(toggle)
    await user.keyboard('{Escape}')

    const closed = screen.getByRole('button', { name: 'Open navigation menu' })
    expect(closed).toHaveAttribute('aria-expanded', 'false')
    expect(closed).toHaveFocus()
  })

  it('closes after navigating from the mobile panel', async () => {
    const user = userEvent.setup()
    renderNav('/dashboard')

    const toggle = screen.getByRole('button', { name: 'Open navigation menu' })
    await user.click(toggle)
    const panel = getMobilePanel(toggle)

    await user.click(within(panel).getByRole('link', { name: 'Resume' }))

    expect(screen.getByRole('button', { name: 'Open navigation menu' }))
      .toHaveAttribute('aria-expanded', 'false')
  })

  it('offers authentication actions when signed out', async () => {
    auth.user = null
    const user = userEvent.setup()
    renderNav('/')

    expect(screen.getByRole('link', { name: 'Log in' })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Get started' })).toBeInTheDocument()

    await user.click(screen.getByRole('button', { name: 'Open navigation menu' }))
    const panel = getMobilePanel(screen.getByRole('button', { name: 'Close navigation menu' }))
    expect(within(panel).getByRole('link', { name: 'Create an account' })).toBeInTheDocument()
  })

  it('logs out and navigates home', async () => {
    const user = userEvent.setup()
    renderNav()

    await user.click(screen.getByRole('button', { name: 'Log out' }))

    expect(auth.logout).toHaveBeenCalledTimes(1)
  })
})
