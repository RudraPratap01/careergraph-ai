/**
 * AuthContext — the shared authentication state container.
 *
 * Kept in its own module so the provider component and the `useAuth` hook can
 * live in files that Fast Refresh can update independently.
 */

import { createContext } from 'react'

export const AuthContext = createContext(null)
