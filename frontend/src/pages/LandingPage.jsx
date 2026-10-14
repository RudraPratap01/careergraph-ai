/**
 * Landing Page — the first thing a visitor sees.
 *
 * Design decisions:
 *   - Explains the product clearly (no fake stats)
 *   - Shows the workflow: Profile → Analysis → Gap → Roadmap → Mentor
 *   - Professional, information-focused — not a marketing fluff page
 */

import { Link } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'

const WORKFLOW_STEPS = [
  { icon: '👤', label: 'Profile',   desc: 'Add resume, GitHub, projects, certifications' },
  { icon: '🔍', label: 'Analysis',  desc: 'Extract and normalize skills from all sources' },
  { icon: '📊', label: 'Skill Gap', desc: 'Compare your skills against your target role' },
  { icon: '🗺️', label: 'Roadmap',   desc: 'Learn → Practice → Build → Assess for each gap' },
  { icon: '📈', label: 'Progress',  desc: 'Track readiness over time with real data' },
  { icon: '🤝', label: 'Mentor',    desc: 'Match with alumni who cover your skill gaps' },
]

const CAREER_EXAMPLES = [
  { role: 'Backend Developer',      skills: ['Python', 'FastAPI', 'PostgreSQL', 'Docker', 'REST APIs'] },
  { role: 'Data Analyst',           skills: ['Python', 'SQL', 'Pandas', 'Data Visualization', 'Statistics'] },
  { role: 'ML Engineer',            skills: ['Python', 'Scikit-learn', 'PyTorch', 'NLP', 'Docker'] },
  { role: 'Frontend Developer',     skills: ['React', 'JavaScript', 'TypeScript', 'CSS', 'HTML'] },
  { role: 'Cybersecurity Analyst',  skills: ['Networking', 'Linux', 'OWASP', 'Cryptography', 'Python'] },
]

export default function LandingPage() {
  const { isAuthenticated } = useAuth()

  return (
    <div>
      {/* ── Hero ──────────────────────────────────────────────────────────── */}
      <section className="bg-grid" style={{ padding: '6rem 1.5rem 5rem', textAlign: 'center', position: 'relative', overflow: 'hidden' }}>
        {/* Glow orb */}
        <div style={{
          position: 'absolute', top: '10%', left: '50%', transform: 'translateX(-50%)',
          width: '600px', height: '300px',
          background: 'radial-gradient(ellipse at center, rgba(99,102,241,0.12) 0%, transparent 70%)',
          pointerEvents: 'none',
        }} />

        <div className="fade-up" style={{ maxWidth: '760px', margin: '0 auto', position: 'relative' }}>
          <div className="badge badge-info" style={{ marginBottom: '1.5rem', display: 'inline-flex' }}>
            ⚡ Career Intelligence Platform
          </div>

          <h1 style={{ fontSize: 'clamp(2rem, 5vw, 3.25rem)', fontWeight: 800, lineHeight: 1.1, marginBottom: '1.25rem' }}>
            Not sure what you're missing<br />
            <span style={{ color: 'var(--color-brand-light)' }}>for your target career?</span>
          </h1>

          <p style={{ fontSize: '1.125rem', color: 'var(--color-text-secondary)', maxWidth: '580px', margin: '0 auto 2.5rem', lineHeight: 1.7 }}>
            CareerGraph AI compares your current skills against what your target role actually requires —
            then helps you decide what to learn next, where to practice, and which mentor to reach out to.
          </p>

          <div style={{ display: 'flex', gap: '1rem', justifyContent: 'center', flexWrap: 'wrap' }}>
            {isAuthenticated ? (
              <Link to="/dashboard" className="btn btn-primary" id="btn-hero-dashboard" style={{ fontSize: '1rem', padding: '0.875rem 2rem' }}>
                Go to Dashboard →
              </Link>
            ) : (
              <>
                <Link to="/register" className="btn btn-primary" id="btn-hero-start" style={{ fontSize: '1rem', padding: '0.875rem 2rem' }}>
                  Analyze My Skills →
                </Link>
                <Link to="/login" className="btn btn-secondary" id="btn-hero-login" style={{ fontSize: '1rem', padding: '0.875rem 2rem' }}>
                  Login
                </Link>
              </>
            )}
          </div>
        </div>
      </section>

      {/* ── How It Works ──────────────────────────────────────────────────── */}
      <section style={{ padding: '5rem 1.5rem', background: 'var(--color-bg-secondary)' }}>
        <div className="page-container">
          <p style={{ fontSize: '0.8rem', fontWeight: 700, letterSpacing: '0.12em', color: 'var(--color-brand-light)', textTransform: 'uppercase', marginBottom: '0.75rem', textAlign: 'center' }}>
            How It Works
          </p>
          <h2 style={{ fontSize: '1.875rem', fontWeight: 700, textAlign: 'center', marginBottom: '0.75rem' }}>
            From profile to personalized roadmap
          </h2>
          <p style={{ color: 'var(--color-text-secondary)', textAlign: 'center', marginBottom: '3rem', maxWidth: '520px', margin: '0 auto 3rem' }}>
            Every step is backed by actual data from your profile — not guesswork.
          </p>

          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
            gap: '1rem',
          }}>
            {WORKFLOW_STEPS.map((step, i) => (
              <div key={step.label} className="card" style={{ display: 'flex', gap: '1rem', alignItems: 'flex-start' }}>
                <div style={{
                  flexShrink: 0,
                  width: '42px', height: '42px',
                  background: 'var(--color-bg-elevated)',
                  borderRadius: '10px',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  fontSize: '1.25rem',
                }}>
                  {step.icon}
                </div>
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.25rem' }}>
                    <span style={{ fontSize: '0.7rem', fontWeight: 700, color: 'var(--color-brand-light)' }}>
                      {String(i + 1).padStart(2, '0')}
                    </span>
                    <span style={{ fontWeight: 600, fontSize: '0.95rem' }}>{step.label}</span>
                  </div>
                  <p style={{ fontSize: '0.85rem', color: 'var(--color-text-secondary)', lineHeight: 1.5 }}>
                    {step.desc}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Career Examples ───────────────────────────────────────────────── */}
      <section style={{ padding: '5rem 1.5rem' }}>
        <div className="page-container">
          <h2 style={{ fontSize: '1.875rem', fontWeight: 700, textAlign: 'center', marginBottom: '0.75rem' }}>
            Supported career paths
          </h2>
          <p style={{ color: 'var(--color-text-secondary)', textAlign: 'center', marginBottom: '3rem' }}>
            More careers can be added — the architecture is built to extend.
          </p>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '1rem' }}>
            {CAREER_EXAMPLES.map((career) => (
              <div key={career.role} className="card">
                <h3 style={{ fontSize: '1rem', fontWeight: 700, marginBottom: '0.875rem' }}>{career.role}</h3>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.375rem' }}>
                  {career.skills.map((skill) => (
                    <span key={skill} className="badge badge-info" style={{ fontSize: '0.72rem' }}>{skill}</span>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── What this is NOT ──────────────────────────────────────────────── */}
      <section style={{ padding: '4rem 1.5rem', background: 'var(--color-bg-secondary)' }}>
        <div className="page-container" style={{ maxWidth: '700px' }}>
          <div className="card" style={{ borderColor: 'rgba(99,102,241,0.2)' }}>
            <h3 style={{ fontSize: '1.1rem', fontWeight: 700, marginBottom: '1rem' }}>
              📋 Honest limitations
            </h3>
            <ul style={{ display: 'flex', flexDirection: 'column', gap: '0.625rem' }}>
              {[
                'GitHub activity is supporting evidence, not proof of programming ability.',
                'Resume extraction can make mistakes — you can always review and correct extracted skills.',
                'Readiness is an estimate, not a guarantee of employment.',
                'AI explanations may be imperfect — core calculations are always deterministic.',
                'Mentor matching is a recommendation, not a guarantee of compatibility.',
              ].map((item, i) => (
                <li key={i} style={{ display: 'flex', gap: '0.625rem', alignItems: 'flex-start', fontSize: '0.875rem', color: 'var(--color-text-secondary)' }}>
                  <span style={{ color: 'var(--color-brand-light)', flexShrink: 0 }}>•</span>
                  {item}
                </li>
              ))}
            </ul>
          </div>
        </div>
      </section>

      {/* ── CTA ───────────────────────────────────────────────────────────── */}
      <section style={{ padding: '5rem 1.5rem', textAlign: 'center' }}>
        <h2 style={{ fontSize: '2rem', fontWeight: 700, marginBottom: '1rem' }}>
          Ready to find your gaps?
        </h2>
        <p style={{ color: 'var(--color-text-secondary)', marginBottom: '2rem' }}>
          Create a free account and start your skill analysis.
        </p>
        {!isAuthenticated && (
          <Link to="/register" className="btn btn-primary" id="btn-cta-start" style={{ fontSize: '1rem', padding: '0.875rem 2.5rem' }}>
            Get Started — Free →
          </Link>
        )}
      </section>

      {/* ── Footer ────────────────────────────────────────────────────────── */}
      <footer style={{
        borderTop: '1px solid var(--color-border)',
        padding: '1.5rem',
        textAlign: 'center',
        color: 'var(--color-text-muted)',
        fontSize: '0.825rem',
      }}>
        CareerGraph AI — Final Year Project · Built with FastAPI, React, PostgreSQL, Neo4j
      </footer>
    </div>
  )
}
