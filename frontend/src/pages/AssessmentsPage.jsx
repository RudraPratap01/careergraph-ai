/**
 * AssessmentsPage — Phase 8: skill assessments.
 *
 * Flow: pick a curated assessment → answer its questions → get a deterministic
 * score with a per-question review → explicitly confirm which evidenced skills
 * should be added to your profile.
 *
 * Correct answers are never part of the payload before submission: the review
 * section only renders answers the server returned *after* grading.
 *
 * Nothing on this page is mocked — every value comes from the API.
 */

import { useState, useEffect, useCallback } from 'react'
import { Link } from 'react-router-dom'
import { assessmentAPI, formatApiError } from '../services/api'

export default function AssessmentsPage() {
  const [catalog, setCatalog] = useState([])
  const [history, setHistory] = useState([])
  const [attempt, setAttempt] = useState(null)   // { attempt, questions }
  const [answers, setAnswers] = useState({})     // question_id -> chosen_index
  const [result, setResult] = useState(null)
  const [selectedSkills, setSelectedSkills] = useState([])
  const [confirmNotice, setConfirmNotice] = useState(null)
  const [loading, setLoading] = useState(true)
  const [working, setWorking] = useState(false)
  const [error, setError] = useState(null)

  const loadHistory = useCallback(async () => {
    try {
      const res = await assessmentAPI.history()
      setHistory(res.data)
    } catch (err) {
      if (err.response?.status !== 403) {
        setError(formatApiError(err, 'Failed to load your assessment history.'))
      }
    }
  }, [])

  useEffect(() => {
    let cancelled = false
    Promise.allSettled([assessmentAPI.list(), assessmentAPI.history()]).then(([cat, hist]) => {
      if (cancelled) return
      if (cat.status === 'fulfilled') setCatalog(cat.value.data)
      else setError(formatApiError(cat.reason, 'Failed to load the assessment catalogue.'))
      if (hist.status === 'fulfilled') setHistory(hist.value.data)
      setLoading(false)
    })
    return () => {
      cancelled = true
    }
  }, [])

  const handleStart = async (key) => {
    setWorking(true)
    setError(null)
    setResult(null)
    setConfirmNotice(null)
    setAnswers({})
    try {
      const res = await assessmentAPI.start(key)
      setAttempt(res.data)
    } catch (err) {
      setError(formatApiError(err, 'Failed to start that assessment.'))
    } finally {
      setWorking(false)
    }
  }

  const handleSubmit = async () => {
    if (!attempt) return
    setWorking(true)
    setError(null)
    try {
      const payload = Object.entries(answers).map(([question_id, chosen_index]) => ({
        question_id,
        chosen_index,
      }))
      const res = await assessmentAPI.submit(attempt.attempt.id, payload)
      setResult(res.data)
      setSelectedSkills(res.data.suggested_skills)
      setAttempt(null) // the attempt is graded; the review view takes over
      loadHistory()
    } catch (err) {
      setError(formatApiError(err, 'Failed to submit your answers.'))
    } finally {
      setWorking(false)
    }
  }

  const handleConfirm = async () => {
    if (!result || selectedSkills.length === 0) return
    setWorking(true)
    setError(null)
    try {
      const res = await assessmentAPI.confirmSkills(result.attempt.id, selectedSkills)
      const { added, already_present, message } = res.data
      setConfirmNotice(
        message ||
          [
            added.length ? `Added: ${added.join(', ')}.` : null,
            already_present.length ? `Already on your profile: ${already_present.join(', ')}.` : null,
          ]
            .filter(Boolean)
            .join(' ')
      )
      setSelectedSkills([])
      loadHistory()
    } catch (err) {
      setError(formatApiError(err, 'Failed to add those skills to your profile.'))
    } finally {
      setWorking(false)
    }
  }

  const toggleSkill = (skill) => {
    setSelectedSkills((prev) =>
      prev.includes(skill) ? prev.filter((s) => s !== skill) : [...prev, skill]
    )
  }

  const answeredCount = Object.keys(answers).length

  return (
    <div className="page-container">
      <div className="fade-up">
        <h1 className="section-title">📝 Skill Assessments</h1>
        <p className="section-subtitle">
          Short, curated checks. Pass one and you can add the skill to your profile as{' '}
          <strong>evidenced</strong> — nothing is added without your confirmation.
        </p>

        {loading && (
          <div className="card" style={{ display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
            <span className="spinner" /> Loading assessments…
          </div>
        )}

        {!loading && error && (
          <div className="alert alert-error" role="alert" style={{ marginBottom: '1.5rem' }}>
            {error}
          </div>
        )}

        {/* ── Taking an assessment ─────────────────────────────────────────── */}
        {!loading && attempt && (
          <div className="card" data-testid="assessment-runner" style={{ marginBottom: '1.5rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', gap: '1rem', flexWrap: 'wrap' }}>
              <div>
                <div style={{ fontSize: '1.15rem', fontWeight: 700 }}>{attempt.attempt.assessment_name}</div>
                <div style={{ fontSize: '0.82rem', color: 'var(--color-text-secondary)' }}>
                  {attempt.questions.length} questions • each skill is scored on its own questions.
                </div>
              </div>
              <button
                type="button"
                className="btn btn-secondary"
                onClick={() => setAttempt(null)}
                disabled={working}
              >
                Cancel
              </button>
            </div>

            <div style={{ fontSize: '0.82rem', color: 'var(--color-text-muted)', marginTop: '0.75rem' }}>
              Answered {answeredCount}/{attempt.questions.length}
            </div>

            <ol style={{ listStyle: 'none', display: 'flex', flexDirection: 'column', gap: '1rem', marginTop: '1rem' }}>
              {attempt.questions.map((q, i) => (
                <li key={q.id} data-testid={`question-${q.id}`}>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem', alignItems: 'center' }}>
                    <span style={{ fontWeight: 600 }}>
                      {i + 1}. {q.prompt}
                    </span>
                    <span className="badge badge-info">{q.skill}</span>
                    <span className="badge badge-medium">{q.difficulty}</span>
                  </div>
                  <fieldset style={{ border: 'none', marginTop: '0.5rem', display: 'flex', flexDirection: 'column', gap: '0.35rem' }}>
                    <legend className="sr-only" style={{ position: 'absolute', width: 1, height: 1, overflow: 'hidden' }}>
                      Options for question {i + 1}
                    </legend>
                    {q.options.map((option, index) => (
                      <label
                        key={option}
                        style={{ display: 'flex', gap: '0.5rem', alignItems: 'center', fontSize: '0.9rem' }}
                      >
                        <input
                          type="radio"
                          name={`q-${q.id}`}
                          value={index}
                          checked={answers[q.id] === index}
                          onChange={() => setAnswers((prev) => ({ ...prev, [q.id]: index }))}
                        />
                        {option}
                      </label>
                    ))}
                  </fieldset>
                </li>
              ))}
            </ol>

            <div style={{ marginTop: '1.25rem' }}>
              <button
                type="button"
                className="btn btn-primary"
                onClick={handleSubmit}
                disabled={working || answeredCount === 0}
              >
                Submit answers
              </button>
              {answeredCount === 0 && (
                <span style={{ marginLeft: '0.75rem', fontSize: '0.8rem', color: 'var(--color-text-muted)' }}>
                  Answer at least one question to submit.
                </span>
              )}
            </div>
          </div>
        )}

        {/* ── Result & review ─────────────────────────────────────────────── */}
        {!loading && result && (
          <div className="card" data-testid="assessment-result" style={{ marginBottom: '1.5rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', gap: '1rem', flexWrap: 'wrap' }}>
              <div>
                <div style={{ fontSize: '1.15rem', fontWeight: 700 }}>{result.attempt.assessment_name}</div>
                <div style={{ fontSize: '0.82rem', color: 'var(--color-text-secondary)' }}>
                  {result.attempt.correct_count}/{result.attempt.total_count} correct
                </div>
              </div>
              <div style={{ textAlign: 'right' }}>
                <div style={{ fontSize: '2rem', fontWeight: 800, lineHeight: 1 }}>
                  {result.attempt.score_percent}%
                </div>
                <span className={`badge ${result.attempt.passed ? 'badge-strong' : 'badge-medium'}`}>
                  {result.attempt.passed ? 'Passed' : 'Not passed'}
                </span>
              </div>
            </div>

            {result.explanation && (
              <p style={{ fontSize: '0.85rem', color: 'var(--color-text-secondary)', marginTop: '0.75rem' }}>
                {result.explanation}
              </p>
            )}

            <div style={{ marginTop: '1rem' }}>
              <div style={{ fontSize: '0.85rem', fontWeight: 600, marginBottom: '0.4rem' }}>
                Per-skill result
              </div>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.4rem' }}>
                {result.attempt.skills.map((s) => (
                  <span
                    key={s.skill}
                    className={`badge ${s.eligible_for_evidence ? 'badge-strong' : 'badge-medium'}`}
                    title={`${s.correct}/${s.total} correct`}
                  >
                    {s.eligible_for_evidence ? '✓' : '○'} {s.skill} — {s.score_percent}%
                  </span>
                ))}
              </div>
            </div>

            {result.suggested_skills.length > 0 ? (
              <div style={{ marginTop: '1.25rem' }}>
                <div style={{ fontSize: '0.85rem', fontWeight: 600, marginBottom: '0.5rem' }}>
                  Skills you can add to your profile as evidenced
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.35rem' }}>
                  {result.suggested_skills.map((skill) => (
                    <label key={skill} style={{ display: 'flex', gap: '0.5rem', alignItems: 'center', fontSize: '0.9rem' }}>
                      <input
                        type="checkbox"
                        checked={selectedSkills.includes(skill)}
                        onChange={() => toggleSkill(skill)}
                      />
                      {skill}
                    </label>
                  ))}
                </div>
                <button
                  type="button"
                  className="btn btn-primary"
                  style={{ marginTop: '0.875rem' }}
                  onClick={handleConfirm}
                  disabled={working || selectedSkills.length === 0}
                >
                  Add {selectedSkills.length} skill{selectedSkills.length === 1 ? '' : 's'} to my profile
                </button>
              </div>
            ) : (
              <div className="alert alert-info" style={{ marginTop: '1rem' }}>
                No skill reached the evidence threshold in this attempt, so there is nothing to add.
                You can retake the assessment any time.
              </div>
            )}

            {confirmNotice && (
              <div className="alert alert-success" role="status" style={{ marginTop: '1rem' }}>
                {confirmNotice}{' '}
                <Link to="/career-gap">See how your readiness changed →</Link>
              </div>
            )}

            <details style={{ marginTop: '1.25rem' }}>
              <summary style={{ cursor: 'pointer', fontSize: '0.85rem', fontWeight: 600 }}>
                Review every question
              </summary>
              <ol style={{ listStyle: 'none', display: 'flex', flexDirection: 'column', gap: '0.75rem', marginTop: '0.75rem' }}>
                {result.results.map((r, i) => (
                  <li key={r.question_id} data-testid={`review-${r.question_id}`} style={{ fontSize: '0.85rem' }}>
                    <div>
                      <span className={`badge ${r.correct ? 'badge-strong' : 'badge-medium'}`}>
                        {r.correct ? '✓ Correct' : '✗ Incorrect'}
                      </span>{' '}
                      <span className="badge badge-info">{r.skill}</span> Question {i + 1}
                    </div>
                    <div style={{ color: 'var(--color-text-secondary)', marginTop: '0.2rem' }}>
                      {r.explanation}
                    </div>
                  </li>
                ))}
              </ol>
            </details>

            <div style={{ marginTop: '1.25rem' }}>
              <button type="button" className="btn btn-secondary" onClick={() => setResult(null)}>
                Back to the catalogue
              </button>
            </div>

            {result.disclaimer && (
              <p style={{ marginTop: '0.875rem', fontSize: '0.78rem', color: 'var(--color-text-muted)' }}>
                {result.disclaimer}
              </p>
            )}
          </div>
        )}

        {/* ── Catalogue ───────────────────────────────────────────────────── */}
        {!loading && !attempt && !result && (
          <>
            <div data-testid="assessment-catalogue" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '1rem' }}>
              {catalog.map((a) => (
                <div key={a.key} className="card" data-testid={`assessment-${a.key}`}>
                  <div style={{ fontSize: '1.02rem', fontWeight: 700, marginBottom: '0.35rem' }}>{a.name}</div>
                  <p style={{ fontSize: '0.85rem', color: 'var(--color-text-secondary)' }}>{a.description}</p>
                  <div style={{ fontSize: '0.78rem', color: 'var(--color-text-muted)', margin: '0.5rem 0' }}>
                    {a.question_count} questions • skills: {a.skills.join(', ')}
                  </div>
                  <button
                    type="button"
                    className="btn btn-primary"
                    onClick={() => handleStart(a.key)}
                    disabled={working}
                  >
                    Start assessment
                  </button>
                </div>
              ))}
            </div>

            {catalog.length === 0 && (
              <div className="alert alert-info">No assessments are available right now.</div>
            )}

            {history.length > 0 && (
              <div className="card" style={{ marginTop: '1.5rem' }} data-testid="assessment-history">
                <div style={{ fontWeight: 600, marginBottom: '0.75rem' }}>Your attempts</div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                  {history.map((h) => (
                    <div
                      key={h.id}
                      style={{ display: 'flex', justifyContent: 'space-between', gap: '0.75rem', fontSize: '0.85rem', flexWrap: 'wrap' }}
                    >
                      <span>{h.assessment_name}</span>
                      <span style={{ color: 'var(--color-text-secondary)' }}>
                        {h.status === 'completed' ? `${h.score_percent}%` : 'In progress'} •{' '}
                        {h.passed === true ? 'Passed' : h.passed === false ? 'Not passed' : '—'}
                        {h.passed_skills?.length > 0 ? ` • evidenced: ${h.passed_skills.join(', ')}` : ''}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  )
}
