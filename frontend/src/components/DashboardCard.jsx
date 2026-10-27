/**
 * DashboardCard — a section card with a consistent icon/title/action header.
 *
 * @param {object} props
 * @param {React.ReactNode} [props.icon] Small decorative icon shown before the title.
 * @param {string} props.title Card heading.
 * @param {React.ReactNode} [props.action] Optional link/button on the right.
 * @param {React.ReactNode} props.children Card body.
 * @param {string} [props.className] Additional class names.
 */
export default function DashboardCard({ icon, title, action, children, className = '' }) {
  return (
    <section className={`card ${className}`.trim()}>
      <div className="card-header">
        <h2 className="card-title">
          {icon && <span className="card-icon" aria-hidden="true">{icon}</span>}
          {title}
        </h2>
        {action}
      </div>
      {children}
    </section>
  )
}
