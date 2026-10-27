/**
 * EmptyState — a consistent empty/zero-data message.
 *
 * @param {object} props
 * @param {React.ReactNode} [props.icon] Icon element rendered in the badge.
 * @param {string} props.title Short headline explaining what is missing.
 * @param {React.ReactNode} [props.children] Supporting copy.
 * @param {React.ReactNode} [props.action] Call to action.
 */
export default function EmptyState({ icon, title, children, action }) {
  return (
    <div className="empty-state">
      {icon && <div className="empty-state-icon" aria-hidden="true">{icon}</div>}
      <p className="empty-state-title">{title}</p>
      {children && <p className="empty-state-text">{children}</p>}
      {action}
    </div>
  )
}
