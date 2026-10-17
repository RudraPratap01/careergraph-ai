/**
 * CareerGapPage — Phase 4: Skill gaps & career readiness.
 *
 * Shows a deterministic, explainable readiness analysis for a target
 * occupation: matched vs missing required skills, bonus skills, the
 * per-skill contribution, and the explanation + disclaimer returned by the API.
 *
 * Every value shown comes from the backend; nothing is hardcoded or invented.
 */

import { useState, useEffect, useCallback } from 'react'
import { Link } from 'react-router-dom'
import { careerAPI, profileAPI, formatApiError } from '../services/api'

const BAND_COLORS = {
  'Role-ready': 'var(--color-accent-green)',
  Proficient: '#34d399',
  Developing: 'var(--color-accent-yellow)',
  Emerging: 'var(--color-accent-red)',
}

function SkillBadge({ skill, tone }) {
  const cls = tone === 'matched' ? 'badge-strong' : tone === 'bonus' ? 'badge-info' : 'badge-missing'
  return (
    <span className={`badge ${cls}`} title={skill.category || undefined}>
      {skill.name}
      <span style={{ opacity: 0.7, fontSize: '0.68rem', marginLeft: '0.35rem' }}>
        {skill.weight}/5
      </span>
    </span>
  )
}

export default function CareerGapPage() {
  const [occupations, setOccupations] = useState([])
  const [selected, setSelected] = useState('')
  const [gap, setGap] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [notice, setNotice] = useState(null)

  const runAnalysis = useCallback(async (occupation) => {
    setLoading(true)
    setError(null)
    setNotice(null)
    try {
      const res = await careerAPI.getGapAnalysis(occupation)
      setGap(res.data)
    } catch (err) {
      setGap(null)
      if (err.response?.status === 400) {
        setNotice('Select a target occupation to compute your skill gap and readiness.')
      } else {
        setError(formatApiError(err, 'Failed to compute the skill-gap analysis.'))
      }
    } finally {
      setLoading(false)
    }
  }, [])

  // Initial load: occupations + the student's saved target role.
  useEffect(() => {
    let cancelled = false
    Promise.allSettled([careerAPI.listOccupations(), profileAPI.getMeProfile()]).then(
      ([occRes, profRes]) => {
        if (cancelled) return
        const occs = occRes.status === 'fulfilled' ? occRes.value.data : []
        setOccupations(occs)

        const targetRole =
          profRes.status === 'fulfilled' ? profRes.value.data?.student_profile?.target_role : null
        const initial = targetRole || ''
        setSelected(initial)
        runAnalysis(initial)
      }
    )
    return () => {
      cancelled = true
    }
  }, [runAnalysis])

  // Resolve the selected display name (fall back to the raw value).
  const selectedOption = occupations.find((o) => o.key === selected)

  return (
    <div className="page-container">
      <div className="fade-up">
        <h1 className="section-title">🎯 Skill Gaps &amp; Career Readiness</h1>
        <p className="section-subtitle">
          Compare your verified skills against a target role. The score is a deterministic
          weighted-coverage metric — not a prediction of hiring outcomes.
        </p>

        {/* Occupation selector */}
        <div className="card" style={{ marginBottom: '1.5rem' }}>
          <label className="label" htmlFor="occupation-select">
            Target occupation
          </label>
          <div style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap' }}>
            <select
              id="occupation-select"
              className="input"
              style={{ maxWidth: '360px' }}
              value={selected}
              onChange={(e) => setSelected(e.target.value)}
            >
              <option value="">— Select an occupation —</option>
              {occupations.map((o) => (
                <option key={o.key} value={o.key}>
                  {o.name}
                </option>
              ))}
            </select>
            <button
              type="button"
              className="btn btn-primary"
              onClick={() => runAnalysis(selected)}
              disabled={!selected || loading}
            >
              {loading ? 'Analyzing…' : 'Analyze gap'}
            </button>
          </div>
          {selectedOption && (
            <p style={{ fontSize: '0.85rem', color: 'var(--color-text-secondary)', marginTop: '0.75rem' }}>
              {selectedOption.description}
            </p>
          )}
        </div>

        {loading && (
          <div className="card" style={{ display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
            <span className="spinner" /> Computing your readiness…
          </div>
        )}

        {!loading && notice && (
          <div className="alert alert-info" role="status">
            {notice}{' '}
            {!selected && (
              <>
                You can also set a <Link to="/profile">target role on your profile</Link> to make
                this the default.
              </>
            )}
          </div>
        )}

        {!loading && error && (
          <div className="alert alert-error" role="alert">
            {error}
          </div>
        )}

        {!loading && !error && gap && (
          <div data-testid="gap-analysis">
            {/* Readiness summary */}
            <div className="card" style={{ marginBottom: '1.5rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', flexWrap: 'wrap', gap: '1rem' }}>
                <div>
                  <div style={{ fontSize: '1.15rem', fontWeight: 700 }}>{gap.occupation_name}</div>
                  <div style={{ fontSize: '0.85rem', color: 'var(--color-text-secondary)' }}>
                    {gap.occupation_category} • value from {gap.target_source}
                  </div>
                </div>
                <div style={{ textAlign: 'right' }}>
                  <div
                    style={{
                      fontSize: '2.25rem',
                      fontWeight: 800,
                      color: BAND_COLORS[gap.readiness_band] || 'var(--color-brand-light)',
                      lineHeight: 1,
                    }}
                  >
                    {gap.readiness_score}%
                  </div>
                  <div style={{ fontSize: '0.85rem', color: 'var(--color-text-secondary)' }}>
                    {gap.readiness_band}
                  </div>
                </div>
              </div>

              <div className="progress-bar-track" style={{ marginTop: '1rem' }}>
                <div
                  className="progress-bar-fill"
                  role="progressbar"
                  aria-valuenow={gap.readiness_score}
                  aria-valuemin={0}
                  aria-valuemax={100}
                  aria-label="Readiness score"
                  style={{
                    width: `${gap.readiness_score}%`,
                    background: BAND_COLORS[gap.readiness_band] || undefined,
                  }}
                />
              </div>

              <p style={{ marginTop: '0.875rem', fontSize: '0.9rem' }}>{gap.explanation}</p>
              <p style={{ marginTop: '0.5rem', fontSize: '0.78rem', color: 'var(--color-text-muted)' }}>
                {gap.disclaimer}
              </p>

              <div style={{ marginTop: '1.25rem', display: 'flex', gap: '0.75rem', flexWrap: 'wrap' }}>
                <Link
                  to="/roadmap"
                  className="btn btn-primary"
                  style={{ fontSize: '0.85rem' }}
                >
                  🗺️ Build my learning roadmap
                </Link>
                <span className="badge badge-info">
                  {gap.matched_count}/{gap.required_count} required skills covered
                </span>
              </div>
            </div>

            {/* Matched / missing */}
            <div
              style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))',
                gap: '1.5rem',
              }}
            >
              <div className="card">
                <h2 style={{ fontSize: '1rem', fontWeight: 700, marginBottom: '0.875rem' }}>
                  ✅ Matched required skills ({gap.matched_skills.length})
                </h2>
                {gap.matched_skills.length === 0 ? (
                  <p style={{ fontSize: '0.85rem', color: 'var(--color-text-muted)' }}>
                    None of this role&apos;s required skills are in your profile yet.
                  </p>
                ) : (
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
                    {gap.matched_skills.map((s) => (
                      <SkillBadge key={s.name} skill={s} tone="matched" />
                    ))}
                  </div>
                )}
              </div>

              <div className="card">
                <h2 style={{ fontSize: '1rem', fontWeight: 700, marginBottom: '0.875rem' }}>
                  ⚠️ Missing required skills ({gap.missing_skills.length})
                </h2>
                {gap.missing_skills.length === 0 ? (
                  <p style={{ fontSize: '0.85rem', color: 'var(--color-accent-green)' }}>
                    You cover every required skill for this role.
                  </p>
                ) : (
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
                    {gap.missing_skills.map((s) => (
                      <SkillBadge key={s.name} skill={s} tone="missing" />
                    ))}
                  </div>
                )}
              </div>

              {gap.bonus_skills.length > 0 && (
                <div className="card">
                  <h2 style={{ fontSize: '1rem', fontWeight: 700, marginBottom: '0.875rem' }}>
                    ⭐ Bonus skills you already have ({gap.bonus_skills.length})
                  </h2>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
                    {gap.bonus_skills.map((s) => (
                      <SkillBadge key={s.name} skill={s} tone="bonus" />
                    ))}
                  </div>
                </div>
              )}

              {gap.unknown_skills.length > 0 && (
                <div className="card">
                  <h2 style={{ fontSize: '1rem', fontWeight: 700, marginBottom: '0.875rem' }}>
                    ❓ Skills not in the taxonomy ({gap.unknown_skills.length})
                  </h2>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
                    {gap.unknown_skills.map((name) => (
                      <span key={name} className="badge badge-medium">
                        {name}
                      </span>
                    ))}
                  </div>
                  <p style={{ fontSize: '0.78rem', color: 'var(--color-text-muted)', marginTop: '0.75rem' }}>
                    These are recorded on your profile but are not part of the curated taxonomy used
                    for scoring, so they neither help nor hurt the score.
                  </p>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
