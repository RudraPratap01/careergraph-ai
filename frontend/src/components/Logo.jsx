/**
 * Logo — the CareerGraph AI wordmark.
 *
 * The mark is a three-node graph: a visual shorthand for connecting skills,
 * roles and people. It is decorative (the wordmark carries the name).
 */

import { Link } from 'react-router-dom'

export default function Logo({ to = '/', className = '' }) {
  return (
    <Link to={to} className={`brand ${className}`.trim()} aria-label="CareerGraph AI home">
      <span className="brand-mark" aria-hidden="true">
        <svg viewBox="0 0 24 24" fill="none" focusable="false">
          <circle cx="6" cy="17" r="2.5" fill="currentColor" />
          <circle cx="17.5" cy="6" r="2.5" fill="currentColor" />
          <circle cx="18" cy="18" r="2" fill="currentColor" opacity="0.7" />
          <path
            d="M8.1 15.6 15.4 7.7M8.3 18.2l7.7.5"
            stroke="currentColor"
            strokeWidth="1.4"
            strokeLinecap="round"
            opacity="0.65"
          />
        </svg>
      </span>
      <span className="brand-word">
        CareerGraph <span>AI</span>
      </span>
    </Link>
  )
}
