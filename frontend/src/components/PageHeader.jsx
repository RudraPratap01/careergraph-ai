/**
 * PageHeader — consistent title block for authenticated pages.
 *
 * @param {object} props
 * @param {string} [props.eyebrow] Optional small label above the title.
 * @param {string} props.title Page heading.
 * @param {string} [props.subtitle] Supporting description.
 * @param {React.ReactNode} [props.actions] Primary page actions (links/buttons).
 */
export default function PageHeader({ eyebrow, title, subtitle, actions }) {
  return (
    <header className="page-header">
      <div>
        {eyebrow && <p className="eyebrow" style={{ marginBottom: '0.45rem' }}>{eyebrow}</p>}
        <h1 className="page-title">{title}</h1>
        {subtitle && <p className="page-subtitle">{subtitle}</p>}
      </div>
      {actions && <div className="row">{actions}</div>}
    </header>
  )
}
