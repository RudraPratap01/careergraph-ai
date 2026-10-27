/**
 * App — root component with routing and layout landmarks.
 *
 * Route protection:
 *   ProtectedRoute   redirects to /login when there is no session.
 *   PublicOnlyRoute  redirects authenticated users away from auth pages.
 *
 * Layout: a skip link, the sticky navigation, and a single <main> landmark.
 * Scroll position resets on navigation so long pages do not open mid-scroll.
 */

import { lazy, Suspense, useEffect } from 'react'
import { BrowserRouter, Routes, Route, Navigate, useLocation } from 'react-router-dom'
import AuthProvider from './context/AuthProvider'
import { useAuth } from './hooks/useAuth'
import Navbar from './components/Navbar'

const LandingPage = lazy(() => import('./pages/LandingPage'))
const LoginPage = lazy(() => import('./pages/LoginPage'))
const RegisterPage = lazy(() => import('./pages/RegisterPage'))
const DashboardPage = lazy(() => import('./pages/DashboardPage'))
const ProfilePage = lazy(() => import('./pages/ProfilePage'))
const ResumePage = lazy(() => import('./pages/ResumePage'))
const CareerGapPage = lazy(() => import('./pages/CareerGapPage'))
const RoadmapPage = lazy(() => import('./pages/RoadmapPage'))
const AssessmentsPage = lazy(() => import('./pages/AssessmentsPage'))
const MentorsPage = lazy(() => import('./pages/MentorsPage'))
const VerificationPage = lazy(() => import('./pages/VerificationPage'))
const AdvisorPage = lazy(() => import('./pages/AdvisorPage'))
const NotFoundPage = lazy(() => import('./pages/NotFoundPage'))

function Loader({ message = 'Loading page…' }) {
  return (
    <div
      className="page-container"
      style={{ textAlign: 'center', paddingTop: '5rem' }}
      role="status"
      aria-live="polite"
    >
      <span className="spinner" style={{ margin: '0 auto 1rem' }} />
      <p className="muted small">{message}</p>
    </div>
  )
}

function ProtectedRoute({ children }) {
  const { isAuthenticated, initialCheckDone } = useAuth()
  if (!initialCheckDone && localStorage.getItem('cg_token')) {
    return <Loader message="Verifying your session…" />
  }
  return isAuthenticated ? children : <Navigate to="/login" replace />
}

function PublicOnlyRoute({ children }) {
  const { isAuthenticated, initialCheckDone } = useAuth()
  if (!initialCheckDone && localStorage.getItem('cg_token')) {
    return <Loader message="Verifying your session…" />
  }
  return !isAuthenticated ? children : <Navigate to="/dashboard" replace />
}

function ScrollToTop() {
  const { pathname } = useLocation()
  useEffect(() => {
    window.scrollTo({ top: 0, left: 0, behavior: 'auto' })
  }, [pathname])
  return null
}

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <ScrollToTop />
        <a className="skip-link" href="#main-content">Skip to content</a>
        <Navbar />
        <main id="main-content">
          <Suspense fallback={<Loader />}>
            <Routes>
            <Route path="/" element={<LandingPage />} />

            <Route
              path="/login"
              element={<PublicOnlyRoute><LoginPage /></PublicOnlyRoute>}
            />
            <Route
              path="/register"
              element={<PublicOnlyRoute><RegisterPage /></PublicOnlyRoute>}
            />
            <Route
              path="/dashboard"
              element={<ProtectedRoute><DashboardPage /></ProtectedRoute>}
            />
            <Route
              path="/profile"
              element={<ProtectedRoute><ProfilePage /></ProtectedRoute>}
            />
            <Route
              path="/resume"
              element={<ProtectedRoute><ResumePage /></ProtectedRoute>}
            />
            <Route
              path="/career-gap"
              element={<ProtectedRoute><CareerGapPage /></ProtectedRoute>}
            />
            <Route
              path="/roadmap"
              element={<ProtectedRoute><RoadmapPage /></ProtectedRoute>}
            />
            <Route
              path="/assessments"
              element={<ProtectedRoute><AssessmentsPage /></ProtectedRoute>}
            />
            <Route
              path="/mentors"
              element={<ProtectedRoute><MentorsPage /></ProtectedRoute>}
            />
            <Route
              path="/verification"
              element={<ProtectedRoute><VerificationPage /></ProtectedRoute>}
            />
            <Route
              path="/advisor"
              element={<ProtectedRoute><AdvisorPage /></ProtectedRoute>}
            />

            <Route path="*" element={<NotFoundPage />} />
            </Routes>
          </Suspense>
        </main>
      </BrowserRouter>
    </AuthProvider>
  )
}
