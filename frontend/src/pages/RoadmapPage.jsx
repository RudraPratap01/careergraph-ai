/**
 * RoadmapPage — Phase 5: personalized learning roadmap.
 *
 * Renders the prerequisite-ordered roadmap returned by the backend:
 *   - target occupation + summary + progress
 *   - ordered learning steps (prerequisites always before dependents)
 *   - per-step explanations and prerequisite relationships
 *   - real progress updates (persisted server-side)
 *   - transparent "partial roadmap" notices when dependency data is incomplete
 *
 * Nothing on this page is mocked: every value comes from the API.
 */

import { useState, useEffect, useCallback, useMemo } from 'react'
import { Link } from 'react-router-dom'
import { careerAPI, profileAPI, roadmapAPI, formatApiError } from '../services/api'

const STATE_META = {
  pending: { label: 'Not started', cls: 'btn-secondary' },
  in_progress: { label: 'In progress', cls: 'btn-secondary' },
  completed: { label: 'Completed', cls: 'btn-primary' },
}

const STEP_STATES = ['pending', 'in_progress', 'completed']

function statusBadge(state) {
  if (state === 'completed') return <span className="badge badge-strong">✓ Completed</span>
  if (state === 'in_progress') return <span className="badge badge-medium">◐ In progress</span>
  return <span className="badge badge-info">○ Not started</span>
}

export default function RoadmapPage() {
  const [roadmap, setRoadmap] = useState(null)
  const [occupations, setOccupations] = useState([])
  const [selected, setSelected] = useState('')
  const [loading, setLoading] = useState(true)
  const [working, setWorking] = useState(false)
  const [error, setError] = useState(null)
  const [notice, setNotice] = useState(null)

  const loadCurrent = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await roadmapAPI.getCurrent()
      setRoadmap(res.data)
      setSelected(res.data.occupation_key)
    } catch (err) {
      if (err.response?.status === 404) {
        setRoadmap(null)
        setNotice('No roadmap yet — pick a target occupation and generate one.')
      } else {
        setError(formatApiError(err, 'Failed to load your roadmap.'))
      }
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    let cancelled = false
    Promise.allSettled([careerAPI.listOccupations(), profileAPI.getMeProfile()]).then(
      ([occRes, profRes]) => {
        if (cancelled) return
        const occs = occRes.status === 'fulfilled' ? occRes.value.data : []
        setOccupations(occs)
        const targetRole =
          profRes.status === 'fulfilled' ? profRes.value.data?.student_profile?.target_role : null
        if (targetRole) setSelected(targetRole)
        loadCurrent()
      }
    )
    return () => {
      cancelled = true
    }
  }, [loadCurrent])

  const handleGenerate = async (regenerate = true) => {
    if (!selected) return
    setWorking(true)
    setError(null)
    setNotice(null)
    try {
      const res = await roadmapAPI.generate(selected, regenerate)
      setRoadmap(res.data)
    } catch (err) {
      setError(formatApiError(err, 'Failed to generate the roadmap.'))
    } finally {
      setWorking(false)
    }
  }

  const handleRefresh = async () => {
    setWorking(true)
    setError(null)
    try {
      const res = await roadmapAPI.refresh()
      setRoadmap(res.data)
      setNotice('Roadmap refreshed from your current skills and target role.')
    } catch (err) {
      setError(formatApiError(err, 'Failed to refresh the roadmap.'))
    } finally {
      setWorking(false)
    }
  }

  const handleStepUpdate = async (skill, state) => {
    if (!roadmap) return
    setWorking(true)
    setError(null)
    try {
      const res = await roadmapAPI.updateStep(roadmap.id, skill, state)
      const { step, progress, next_action } = res.data
      setRoadmap((prev) => ({
        ...prev,
        progress,
        next_action,
        steps: prev.steps.map((s) => (s.skill === step.skill ? { ...s, status: step.status } : s)),
      }))
    } catch (err) {
      setError(formatApiError(err, 'Failed to update that step.'))
    } finally {
      setWorking(false)
    }
  }

  const sortedSteps = useMemo(() => {
    if (!roadmap) return []
    return [...roadmap.steps].sort((a, b) => a.position - b.position)
  }, [roadmap])

  return (
    <div className="page-container">
      <div className="fade-up">
        <div className="page-header">
          <div>
            <h1 className="section-title">Learning roadmap</h1>
            <p className="section-subtitle">
              A prerequisite-ordered plan built from your current profile skills and your target role.
            </p>
          </div>
          <div className="row">
            <Link to="/advisor" className="btn btn-secondary">
              Ask about this order
            </Link>
          </div>
        </div>

        {loading && (
          <div className="card" style={{ display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
            <span className="spinner" /> Loading your roadmap…
          </div>
        )}

        {!loading && error && (
          <div className="alert alert-error" role="alert" style={{ marginBottom: '1.5rem' }}>
            {error}
          </div>
        )}

        {/* Generator / controls */}
        {!loading && (
          <div className="card" style={{ marginBottom: '1.5rem' }}>
            <label className="label" htmlFor="roadmap-occupation">
              Target occupation
            </label>
            <div style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap' }}>
              <select
                id="roadmap-occupation"
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
                onClick={() => handleGenerate(true)}
                disabled={!selected || working}
              >
                {roadmap ? 'Regenerate roadmap' : 'Generate roadmap'}
              </button>

              {roadmap && (
                <button
                  type="button"
                  className="btn btn-secondary"
                  onClick={handleRefresh}
                  disabled={working}
                >
                  ↻ Refresh from current skills
                </button>
              )}
            </div>
          </div>
        )}

        {!loading && notice && !roadmap && (
          <div className="alert alert-info" role="status" style={{ marginBottom: '1.5rem' }}>
            {notice}{' '}
            <Link to="/resume">Upload a resume</Link> or <Link to="/profile">add skills</Link> so
            your roadmap can skip what you already know.
          </div>
        )}

        {!loading && notice && roadmap && (
          <div className="alert alert-info" role="status" style={{ marginBottom: '1.5rem' }}>
            {notice}
          </div>
        )}

        {!loading && roadmap && (
          <div data-testid="roadmap">
            {/* Summary */}
            <div className="card" style={{ marginBottom: '1.5rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', flexWrap: 'wrap', gap: '1rem' }}>
                <div>
                  <div style={{ fontSize: '1.15rem', fontWeight: 700 }}>{roadmap.occupation_name}</div>
                  <div style={{ fontSize: '0.85rem', color: 'var(--color-text-secondary)' }}>
                    {roadmap.occupation_category}
                  </div>
                </div>
                <div style={{ textAlign: 'right' }}>
                  <div style={{ fontSize: '2rem', fontWeight: 800, lineHeight: 1 }}>
                    {roadmap.progress.percent_complete}%
                  </div>
                  <div style={{ fontSize: '0.82rem', color: 'var(--color-text-secondary)' }}>
                    {roadmap.progress.completed_steps}/{roadmap.progress.total_steps} steps done
                  </div>
                </div>
              </div>

              <div className="progress-bar-track" style={{ marginTop: '1rem' }}>
                <div
                  className="progress-bar-fill"
                  role="progressbar"
                  aria-valuenow={roadmap.progress.percent_complete}
                  aria-valuemin={0}
                  aria-valuemax={100}
                  aria-label="Roadmap completion"
                  style={{ width: `${roadmap.progress.percent_complete}%` }}
                />
              </div>

              {roadmap.next_action && (
                <div className="alert alert-info" style={{ marginTop: '1rem' }}>
                  <strong>Next action:</strong> {roadmap.next_action}
                </div>
              )}

              {roadmap.is_partial && (
                <div className="alert alert-info" role="status" style={{ marginTop: '1rem' }}>
                  <strong>Partial roadmap:</strong> {roadmap.notes}
                </div>
              )}

              {roadmap.possessed_skills?.length > 0 && (
                <div style={{ marginTop: '1.25rem' }}>
                  <div style={{ fontSize: '0.85rem', color: 'var(--color-text-secondary)', marginBottom: '0.5rem' }}>
                    Required skills you already have (not re-scheduled):
                  </div>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.4rem' }}>
                    {roadmap.possessed_skills.map((name) => (
                      <span key={name} className="badge badge-strong">
                        ✓ {name}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              <p style={{ marginTop: '0.875rem', fontSize: '0.78rem', color: 'var(--color-text-muted)' }}>
                {roadmap.disclaimer}
              </p>
            </div>

            {/* Ordered steps */}
            <h2 style={{ fontSize: '1.1rem', fontWeight: 700, marginBottom: '0.875rem' }}>
              Learning order ({sortedSteps.length} steps)
            </h2>

            {sortedSteps.length === 0 ? (
              <div className="alert alert-success">
                You already cover every required skill for this role. Re-run the{' '}
                <Link to="/career-gap">gap analysis</Link> to confirm readiness.
              </div>
            ) : (
              <ol style={{ listStyle: 'none', display: 'flex', flexDirection: 'column', gap: '0.875rem' }}>
                {sortedSteps.map((step) => (
                  <li key={step.skill} className="card" data-testid={`step-${step.skill}`}>
                    <div style={{ display: 'flex', gap: '1rem', alignItems: 'flex-start' }}>
                      <div
                        aria-hidden="true"
                        style={{
                          flexShrink: 0,
                          width: '28px',
                          height: '28px',
                          borderRadius: '50%',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          fontSize: '0.8rem',
                          fontWeight: 700,
                          background:
                            step.status === 'completed'
                              ? 'var(--color-accent-green)'
                              : 'var(--color-bg-elevated)',
                          border: '1px solid var(--color-border)',
                        }}
                      >
                        {step.status === 'completed' ? '✓' : step.position}
                      </div>

                      <div style={{ flex: 1, minWidth: 0 }}>
                        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem', alignItems: 'center' }}>
                          <span style={{ fontWeight: 700 }}>{step.skill}</span>
                          {statusBadge(step.status)}
                          {step.is_target_skill ? (
                            <span className="badge badge-info">Role skill</span>
                          ) : (
                            <span className="badge badge-medium">Prerequisite</span>
                          )}
                        </div>

                        {step.category && (
                          <div style={{ fontSize: '0.78rem', color: 'var(--color-text-muted)', marginTop: '0.2rem' }}>
                            {step.category}
                          </div>
                        )}

                        <p style={{ fontSize: '0.85rem', color: 'var(--color-text-secondary)', marginTop: '0.4rem' }}>
                          {step.reason}
                        </p>

                        {step.prerequisites?.length > 0 && (
                          <div style={{ marginTop: '0.5rem', fontSize: '0.78rem', color: 'var(--color-text-muted)' }}>
                            Requires first:{' '}
                            {step.prerequisites.map((p) => (
                              <span key={p} className="badge badge-info" style={{ marginRight: '0.3rem' }}>
                                {p}
                              </span>
                            ))}
                          </div>
                        )}

                        <fieldset
                          style={{ border: 'none', marginTop: '0.75rem', display: 'flex', gap: '0.4rem', flexWrap: 'wrap' }}
                        >
                          <legend className="sr-only" style={{ position: 'absolute', width: 1, height: 1, overflow: 'hidden' }}>
                            Progress for {step.skill}
                          </legend>
                          {STEP_STATES.map((state) => (
                            <button
                              key={state}
                              type="button"
                              className={`btn ${STATE_META[state].cls}`}
                              aria-pressed={step.status === state}
                              disabled={working}
                              onClick={() => handleStepUpdate(step.skill, state)}
                              style={{
                                fontSize: '0.78rem',
                                padding: '0.3rem 0.7rem',
                                outline: step.status === state ? '2px solid var(--color-brand-primary)' : 'none',
                              }}
                            >
                              {STATE_META[state].label}
                            </button>
                          ))}
                        </fieldset>
                      </div>
                    </div>
                  </li>
                ))}
              </ol>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
