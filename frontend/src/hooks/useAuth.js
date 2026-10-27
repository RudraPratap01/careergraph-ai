/**
 * useAuth — access the shared authentication context.
 *
 * Throws a descriptive error when used outside `AuthProvider`, which makes a
 * missing provider fail loudly during development instead of returning null.
 */

import { useContext } from 'react'
import { AuthContext } from '../context/AuthContext'

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}
