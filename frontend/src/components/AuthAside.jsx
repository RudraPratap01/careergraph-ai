/**
 * AuthAside — the contextual panel beside login/register forms.
 *
 * Reused by both auth pages so the value proposition stays consistent.
 * Hidden below 980px via CSS; it is supplementary content only.
 */

import Icon from './Icon'

const VALUE_POINTS = [
  'Resume, GitHub and assessment evidence in one skill inventory.',
  'Readiness scores computed from explicit weights — never guessed.',
  'A prerequisite-ordered roadmap for the gaps that matter.',
  'Alumni ranked against the skills you still need.',
]

export default function AuthAside({ title, description }) {
  return (
    <aside className="auth-aside">
      <span className="eyebrow">
        <Icon name="spark" size={14} />
        CareerGraph AI
      </span>
      <h2>{title}</h2>
      <p>{description}</p>
      <div className="auth-aside-points">
        {VALUE_POINTS.map((point) => (
          <div key={point} className="auth-aside-point">
            <Icon name="checkCircle" size={16} />
            <span>{point}</span>
          </div>
        ))}
      </div>
      <p className="tiny muted" style={{ marginTop: '0.5rem' }}>
        No fabricated achievements. No employment guarantees. Just evidence you control.
      </p>
    </aside>
  )
}
