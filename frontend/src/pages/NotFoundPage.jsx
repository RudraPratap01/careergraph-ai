/**
 * NotFoundPage — shown for unknown client-side routes.
 *
 * Kept inside the app shell so users can recover without losing context.
 */

import { Link } from 'react-router-dom'
import Icon from '../components/Icon'

export default function NotFoundPage() {
  return (
    <div
      className="page-container"
      style={{ minHeight: 'calc(100vh - var(--nav-height))', display: 'grid', placeItems: 'center' }}
    >
      <div className="card fade-up center" style={{ maxWidth: '520px', width: '100%', padding: '2.5rem 2rem' }}>
        <div className="empty-state-icon" style={{ margin: '0 auto 1rem' }} aria-hidden="true">
          <Icon name="compass" size={22} />
        </div>
        <p className="eyebrow" style={{ justifyContent: 'center' }}>404</p>
        <h1 style={{ fontSize: 'clamp(1.5rem, 4vw, 2rem)', margin: '0.4rem 0 0.6rem' }}>
          This page is off the graph
        </h1>
        <p className="muted small" style={{ maxWidth: '42ch', margin: '0 auto 1.5rem' }}>
          The address may be incorrect, or the page may have moved. Your profile and roadmap are
          safe — use one of the links below to continue.
        </p>
        <div className="row" style={{ justifyContent: 'center' }}>
          <Link to="/" className="btn btn-primary">Back to home</Link>
          <Link to="/dashboard" className="btn btn-secondary">Open dashboard</Link>
        </div>
      </div>
    </div>
  )
}
