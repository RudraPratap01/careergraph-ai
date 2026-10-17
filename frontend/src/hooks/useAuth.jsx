/**
 * AuthContext & useAuth — centralized React Context for authentication state.
 *
 * Ensures all components (Navbar, ProtectedRoute, Dashboard, Profile, etc.)
 * share the exact same reactive user state without desync or premature redirects.
 */

import { createContext, useContext, useState, useEffect, useCallback } from 'react'
import { authAPI, formatApiError } from '../services/api'

const AuthContext = createContext(null)


export function AuthProvider({ children }) {
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


  // Verify and refresh session on mount if token exists
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

  const isAuthenticated = Boolean(user)
  const isStudent = user?.role === 'student'
  const isAlumni = user?.role === 'alumni'
  const isAdmin = user?.role === 'admin'

  const value = {
    user,
    loading,
    error,
    initialCheckDone,
    isAuthenticated,
    isStudent,
    isAlumni,
    isAdmin,
    login,
    register,
    logout,
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}
