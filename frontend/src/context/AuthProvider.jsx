/**
 * AuthProvider — owns the session state for the whole application.
 *
 * On mount, an existing token is re-verified against `/auth/me` so a stale or
 * revoked session cannot leave the UI in a half-authenticated state. Login and
 * registration persist the token and user snapshot; logout clears both.
 */

import { useCallback, useEffect, useState } from 'react'
import { AuthContext } from '../context/AuthContext'
import { authAPI, formatApiError } from '../services/api'

export default function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    try {
      const stored = localStorage.getItem('cg_user')
      return stored ? JSON.parse(stored) : null
    } catch {
      return null
    }
  })

  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [initialCheckDone, setInitialCheckDone] = useState(() => {
    try {
      return !localStorage.getItem('cg_token')
    } catch {
      return true
    }
  })

  // Verify and refresh the session on mount if a token exists.
  useEffect(() => {
    const token = localStorage.getItem('cg_token')
    if (!token) return

    authAPI
      .me()
      .then((res) => {
        const freshUser = res.data
        setUser(freshUser)
        localStorage.setItem('cg_user', JSON.stringify(freshUser))
      })
      .catch((err) => {
        if (err.response?.status === 401) {
          localStorage.removeItem('cg_token')
          localStorage.removeItem('cg_user')
          setUser(null)
        }
      })
      .finally(() => {
        setInitialCheckDone(true)
      })
  }, [])

  const login = useCallback(async (email, password) => {
    setLoading(true)
    setError(null)
    try {
      const res = await authAPI.login({ email, password })
      const { access_token, ...userData } = res.data
      const fullUserData = {
        ...userData,
        email: userData.email || email,
        id: userData.user_id || userData.id,
      }
      localStorage.setItem('cg_token', access_token)
      localStorage.setItem('cg_user', JSON.stringify(fullUserData))
      setUser(fullUserData)
      return { success: true, role: fullUserData.role }
    } catch (err) {
      const msg = formatApiError(err, 'Login failed. Please check your credentials.')
      setError(msg)
      return { success: false, error: msg }
    } finally {
      setLoading(false)
    }
  }, [])

  const register = useCallback(async (data) => {
    setLoading(true)
    setError(null)
    try {
      await authAPI.register(data)
      return await login(data.email, data.password)
    } catch (err) {
      const msg = formatApiError(err, 'Registration failed. Please try again.')
      setError(msg)
      return { success: false, error: msg }
    } finally {
      setLoading(false)
    }
  }, [login])

  const logout = useCallback(() => {
    localStorage.removeItem('cg_token')
    localStorage.removeItem('cg_user')
    setUser(null)
  }, [])

  const value = {
    user,
    loading,
    error,
    initialCheckDone,
    isAuthenticated: Boolean(user),
    isStudent: user?.role === 'student',
    isAlumni: user?.role === 'alumni',
    isAdmin: user?.role === 'admin',
    login,
    register,
    logout,
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
