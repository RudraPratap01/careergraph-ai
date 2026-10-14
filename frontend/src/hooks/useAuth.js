/**
 * useAuth — custom React hook for authentication state.
 *
 * Stores user info in localStorage so it survives page refresh.
 * Provides login, logout, and the current user object.
 */

import { useState, useCallback } from 'react'
import { authAPI } from '../services/api'

export function useAuth() {
  const [user, setUser] = useState(() => {
    // Read from localStorage on initial render
    try {
      const stored = localStorage.getItem('cg_user')
      return stored ? JSON.parse(stored) : null
    } catch {
      return null
    }
  })

  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  /**
   * Login: sends credentials, stores token and user in localStorage.
   * Returns true on success, false on failure.
   */
  const login = useCallback(async (email, password) => {
    setLoading(true)
    setError(null)
    try {
      const res = await authAPI.login({ email, password })
      const { access_token, ...userData } = res.data
      localStorage.setItem('cg_token', access_token)
      localStorage.setItem('cg_user', JSON.stringify(userData))
      setUser(userData)
      return { success: true, role: userData.role }
    } catch (err) {
      const msg = err.response?.data?.detail || 'Login failed. Please try again.'
      setError(msg)
      return { success: false, error: msg }
    } finally {
      setLoading(false)
    }
  }, [])

  /**
   * Register: creates account and immediately logs in.
   */
  const register = useCallback(async (data) => {
    setLoading(true)
    setError(null)
    try {
      await authAPI.register(data)
      // After registration, automatically log in
      return await login(data.email, data.password)
    } catch (err) {
      const msg = err.response?.data?.detail || 'Registration failed. Please try again.'
      setError(msg)
      return { success: false, error: msg }
    } finally {
      setLoading(false)
    }
  }, [login])

  /**
   * Logout: clears all stored data and resets state.
   */
  const logout = useCallback(() => {
    localStorage.removeItem('cg_token')
    localStorage.removeItem('cg_user')
    setUser(null)
  }, [])

  const isAuthenticated = Boolean(user)
  const isStudent = user?.role === 'student'
  const isAlumni = user?.role === 'alumni'
  const isAdmin = user?.role === 'admin'

  return {
    user,
    loading,
    error,
    isAuthenticated,
    isStudent,
    isAlumni,
    isAdmin,
    login,
    register,
    logout,
  }
}
