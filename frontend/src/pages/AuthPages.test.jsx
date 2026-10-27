/**
 * Auth page tests.
 *
 * Covers the behaviours most likely to regress during a UI pass: the form
 * calls the auth context with the right payload, the password visibility
 * toggle actually changes the input type, role selection is announced, and
 * mismatched passwords never reach the API.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'

const auth = vi.hoisted(() => ({
  login: vi.fn(),
  register: vi.fn(),
}))

vi.mock('../hooks/useAuth', () => ({
  useAuth: () => ({
    login: auth.login,
    register: auth.register,
    loading: false,
  }),
}))

import LoginPage from './LoginPage'
import RegisterPage from './RegisterPage'

function renderLogin() {
  return render(
    <MemoryRouter>
      <LoginPage />
    </MemoryRouter>
  )
}

function renderRegister() {
  return render(
    <MemoryRouter>
      <RegisterPage />
    </MemoryRouter>
  )
}

describe('LoginPage', () => {
  beforeEach(() => {
    auth.login.mockReset()
    auth.login.mockResolvedValue({ success: true, role: 'student' })
  })

  it('submits the entered credentials', async () => {
    const user = userEvent.setup()
    renderLogin()

    await user.type(screen.getByLabelText('Email address'), 'student@example.com')
    await user.type(screen.getByLabelText('Password'), 'Password1')
    await user.click(screen.getByRole('button', { name: 'Sign in' }))

    expect(auth.login).toHaveBeenCalledWith('student@example.com', 'Password1')
  })

  it('toggles password visibility with an accessible button', async () => {
    const user = userEvent.setup()
    renderLogin()

    const password = screen.getByLabelText('Password')
    expect(password).toHaveAttribute('type', 'password')

    const toggle = screen.getByRole('button', { name: 'Show password' })
    await user.click(toggle)

    expect(password).toHaveAttribute('type', 'text')
    expect(screen.getByRole('button', { name: 'Hide password' })).toHaveAttribute('aria-pressed', 'true')
  })

  it('announces a failed sign-in without navigating away', async () => {
    auth.login.mockResolvedValue({ success: false, error: 'Invalid credentials.' })
    const user = userEvent.setup()
    renderLogin()

    await user.type(screen.getByLabelText('Email address'), 'student@example.com')
    await user.type(screen.getByLabelText('Password'), 'WrongPass1')
    await user.click(screen.getByRole('button', { name: 'Sign in' }))

    expect(await screen.findByRole('alert')).toHaveTextContent('Invalid credentials.')
  })
})

describe('RegisterPage', () => {
  beforeEach(() => {
    auth.register.mockReset()
    auth.register.mockResolvedValue({ success: true, role: 'student' })
  })

  async function fillForm(user, { confirm = 'Password1', role = null } = {}) {
    if (role) await user.click(screen.getByRole('button', { name: new RegExp(role) }))
    await user.type(screen.getByLabelText('Full name'), 'Test Student')
    await user.type(screen.getByLabelText('Email address'), 'student@example.com')
    await user.type(screen.getByLabelText('Password'), 'Password1')
    await user.type(screen.getByLabelText('Confirm password'), confirm)
  }

  it('selects the alumni role with aria-pressed state', async () => {
    const user = userEvent.setup()
    renderRegister()

    const alumni = screen.getByRole('button', { name: /Alumni/ })
    expect(alumni).toHaveAttribute('aria-pressed', 'false')

    await user.click(alumni)
    expect(alumni).toHaveAttribute('aria-pressed', 'true')
    expect(screen.getByRole('button', { name: /Student/ })).toHaveAttribute('aria-pressed', 'false')
  })

  it('blocks submission when passwords do not match', async () => {
    const user = userEvent.setup()
    renderRegister()

    await fillForm(user, { confirm: 'Different1' })
    await user.click(screen.getByRole('button', { name: 'Create account' }))

    expect(await screen.findByRole('alert')).toHaveTextContent('Passwords do not match.')
    expect(auth.register).not.toHaveBeenCalled()
  })

  it('sends the chosen role and never sends confirm_password', async () => {
    const user = userEvent.setup()
    renderRegister()

    await fillForm(user, { role: 'Alumni' })
    await user.click(screen.getByRole('button', { name: 'Create account' }))

    expect(auth.register).toHaveBeenCalledWith({
      full_name: 'Test Student',
      email: 'student@example.com',
      password: 'Password1',
      role: 'alumni',
    })
  })

  it('toggles each password field independently', async () => {
    const user = userEvent.setup()
    renderRegister()

    const [showFirst] = screen.getAllByRole('button', { name: 'Show password' })
    await user.click(showFirst)

    expect(screen.getByLabelText('Password')).toHaveAttribute('type', 'text')
    expect(screen.getByLabelText('Confirm password')).toHaveAttribute('type', 'password')
  })
})
