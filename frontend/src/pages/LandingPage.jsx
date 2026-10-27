/**
 * LandingPage — public product overview.
 *
 * Visual hierarchy: one clear promise (know your gaps), a six-step workflow,
 * the real curated career tracks, the trust model, honest limitations, and a
 * single primary call to action. Copy avoids invented statistics or claims.
 */

import { Link } from 'react-router-dom'
import HeroGraph from '../components/HeroGraph'
import Icon from '../components/Icon'
import { useAuth } from '../hooks/useAuth'
import { CAREER_PATHS, LIMITATIONS, PRINCIPLES, WORKFLOW_STEPS } from '../content/landing'

const CURRENT_YEAR = new Date().getFullYear()

export default function LandingPage() {
  const { isAuthenticated } = useAuth()

  return (
    <div>
      {/* ── Hero ───────────────────────────────────────────────────────────── */}
      <section className="hero" aria-labelledby="hero-title">
        <div
          className="bg-grid"
          style={{ position: 'absolute', inset: 0, pointerEvents: 'none', opacity: 0.7 }}
          aria-hidden="true"
        />
        <div className="hero-inner">
          <div className="fade-up">
            <span className="eyebrow">
              <Icon name="spark" size={14} />
              Career intelligence, grounded in evidence
            </span>

            <h1 id="hero-title" className="hero-title">
              Know exactly what stands between you and{' '}
              <span className="gradient-text">your target role.</span>
            </h1>

            <p className="hero-copy">
              CareerGraph AI turns your resume, GitHub work and assessment results into an honest
              readiness score — then gives you a prerequisite-ordered learning plan and shows you
              the alumni who can help with the gaps you actually have.
            </p>

            <div className="hero-actions">
              {isAuthenticated ? (
                <Link to="/dashboard" className="btn btn-primary btn-lg" id="btn-hero-dashboard">
                  Go to dashboard <Icon name="arrowRight" size={17} />
                </Link>
              ) : (
                <>
                  <Link to="/register" className="btn btn-primary btn-lg" id="btn-hero-start">
                    Analyze my skills <Icon name="arrowRight" size={17} />
                  </Link>
                  <Link to="/login" className="btn btn-secondary btn-lg" id="btn-hero-login">
                    I already have an account
                  </Link>
                </>
              )}
            </div>

            <div className="hero-meta">
              <span className="chip"><Icon name="shield" size={14} /> Deterministic scores</span>
              <span className="chip"><Icon name="checkCircle" size={14} /> Evidence you confirm</span>
              <span className="chip"><Icon name="layers" size={14} /> One shared skill taxonomy</span>
            </div>
          </div>

          <HeroGraph />
        </div>
      </section>

      {/* ── Workflow ───────────────────────────────────────────────────────── */}
      <section className="section section-alt" aria-labelledby="workflow-title">
        <div className="section-inner">
          <div className="section-head">
            <p className="eyebrow">How it works</p>
            <h2 id="workflow-title">From scattered evidence to a plan you can act on</h2>
            <p>
              Six connected steps. Every score, gap and roadmap step is derived from the same
              curated skill model — nothing is invented for display.
            </p>
          </div>

          <div className="grid grid-auto stagger">
            {WORKFLOW_STEPS.map((step, index) => (
              <article key={step.title} className="card step-card">
                <span className="step-index" aria-hidden="true">
                  {String(index + 1).padStart(2, '0')}
                </span>
                <div>
                  <h3>{step.title}</h3>
                  <p>{step.description}</p>
                </div>
              </article>
            ))}
          </div>
        </div>
      </section>

      {/* ── Career tracks ──────────────────────────────────────────────────── */}
      <section className="section" aria-labelledby="paths-title">
        <div className="section-inner">
          <div className="section-head">
            <p className="eyebrow">Target roles</p>
            <h2 id="paths-title">Start from a role, not a generic checklist</h2>
            <p>
              Seven curated career tracks, each with weighted required skills. These are the
              first skills in each track — the full rubric lives in the app.
            </p>
          </div>

          <div className="grid grid-auto stagger">
            {CAREER_PATHS.map((career) => (
              <article key={career.role} className="card career-card">
                <h3>{career.role}</h3>
                <p className="career-count">Required skills include</p>
                <div className="row" style={{ gap: '0.4rem' }}>
                  {career.skills.map((skill) => (
                    <span key={skill} className="badge badge-info">{skill}</span>
                  ))}
                </div>
              </article>
            ))}
          </div>
        </div>
      </section>

      {/* ── Trust model + limitations ──────────────────────────────────────── */}
      <section className="section section-alt" aria-labelledby="principles-title">
        <div className="section-inner">
          <div className="section-head">
            <p className="eyebrow">Built to be trusted</p>
            <h2 id="principles-title">Clear rules, visible evidence, honest limits</h2>
            <p>
              You should always be able to explain where a number came from and what it does not
              mean.
            </p>
          </div>

          <div className="grid grid-2 stagger">
            {PRINCIPLES.map((principle) => (
              <article key={principle.title} className="card card-flat">
                <div className="card-title" style={{ marginBottom: '0.5rem' }}>
                  <span className="card-icon" aria-hidden="true">
                    <Icon name={principle.icon} size={16} />
                  </span>
                  {principle.title}
                </div>
                <p className="small muted">{principle.description}</p>
              </article>
            ))}
          </div>

          <div className="card" style={{ marginTop: '1.25rem' }}>
            <h3 style={{ fontSize: '1rem', marginBottom: '0.9rem' }}>Honest limitations</h3>
            <ul className="principle-list">
              {LIMITATIONS.map((item) => (
                <li key={item} className="principle">
                  <Icon name="alert" size={15} />
                  <span>{item}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>
      </section>

      {/* ── CTA ────────────────────────────────────────────────────────────── */}
      <section className="section">
        <div className="section-inner">
          <div className="cta-panel">
            <div>
              <p className="eyebrow">Ready when you are</p>
              <h2>Find the real gaps. Close them deliberately.</h2>
              <p>
                Create a free account, set a target role, and get a readiness breakdown you can
                defend — line by line.
              </p>
            </div>
            {isAuthenticated ? (
              <Link to="/dashboard" className="btn btn-primary btn-lg">
                Open dashboard <Icon name="arrowRight" size={17} />
              </Link>
            ) : (
              <Link to="/register" className="btn btn-primary btn-lg" id="btn-cta-start">
                Get started — free <Icon name="arrowRight" size={17} />
              </Link>
            )}
          </div>
        </div>
      </section>

      {/* ── Footer ─────────────────────────────────────────────────────────── */}
      <footer className="site-footer">
        <div className="site-footer-inner">
          <span>© {CURRENT_YEAR} CareerGraph AI · Final-year engineering project</span>
          <nav className="site-footer-links" aria-label="Footer">
            <Link to="/">Home</Link>
            {isAuthenticated ? (
              <Link to="/dashboard">Dashboard</Link>
            ) : (
              <>
                <Link to="/login">Log in</Link>
                <Link to="/register">Create account</Link>
              </>
            )}
          </nav>
          <span>FastAPI · React · SQLite / PostgreSQL</span>
        </div>
      </footer>
    </div>
  )
}
