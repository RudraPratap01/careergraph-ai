/**
 * MentorsPage — Phase 8: alumni matching & mentorship requests.
 *
 * Students see their own outstanding skills, the mentors ranked against them
 * with a fully itemised score, and the requests they have sent.
 * Alumni see the requests addressed to them and can accept or decline — the
 * server enforces their mentee capacity.
 *
 * The score is a deterministic ranking heuristic, never a probability: the
 * factor breakdown is always shown alongside it.
 *
 * Nothing on this page is mocked — every value comes from the API.
 */

import { useState, useEffect, useCallback } from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import { mentorshipAPI, formatApiError } from '../services/api'

const STATUS_BADGE = {
  pending: 'badge-medium',
  accepted: 'badge-strong',
  declined: 'badge-info',
  cancelled: 'badge-info',
}

function StatusBadge({ status }) {
  return <span className={`badge ${STATUS_BADGE[status] || 'badge-info'}`}>{status}</span>
}

export default function MentorsPage() {
  const { user } = useAuth()
  const isStudent = user?.role === 'student'

  const [matches, setMatches] = useState(null)
  const [requests, setRequests] = useState([])
  const [requestingId, setRequestingId] = useState(null)
  const [message, setMessage] = useState('')
  const [loading, setLoading] = useState(true)
  const [working, setWorking] = useState(false)
  const [error, setError] = useState(null)
  const [notice, setNotice] = useState(null)

  const load = useCallback(async () => {
    const tasks = [mentorshipAPI.listRequests()]
    if (isStudent) tasks.push(mentorshipAPI.getMatches())

    const [reqRes, matchRes] = await Promise.allSettled(tasks)
    if (reqRes.status === 'fulfilled') setRequests(reqRes.value.data)
    else setError(formatApiError(reqRes.reason, 'Failed to load mentorship requests.'))

    if (isStudent && matchRes) {
      if (matchRes.status === 'fulfilled') setMatches(matchRes.value.data)
      else setError(formatApiError(matchRes.reason, 'Failed to load mentor matches.'))
    }
    setLoading(false)
  }, [isStudent])

  useEffect(() => {
    load()
  }, [load])

  const handleRequest = async (mentorId) => {
    setWorking(true)
    setError(null)
    setNotice(null)
    try {
      await mentorshipAPI.requestMentorship(mentorId, message)
      setRequestingId(null)
      setMessage('')
      setNotice('Your mentorship request was sent.')
      await load()
    } catch (err) {
      setError(formatApiError(err, 'Failed to send that request.'))
    } finally {
      setWorking(false)
    }
  }

  const handleAction = async (action, requestId, successMessage) => {
    setWorking(true)
    setError(null)
    setNotice(null)
    try {
      await mentorshipAPI[action](requestId)
      setNotice(successMessage)
      await load()
    } catch (err) {
      setError(formatApiError(err, 'That action failed.'))
    } finally {
      setWorking(false)
    }
  }

  return (
    <div className="page-container">
      <div className="fade-up">
        <h1 className="section-title">🤝 {isStudent ? 'Find a Mentor' : 'Mentorship Requests'}</h1>
        <p className="section-subtitle">
          {isStudent
            ? 'Alumni ranked against the skills you still need, each with the exact reasoning behind their score.'
            : 'Students who asked you for mentorship. Accepting is limited by the mentee capacity on your profile.'}
        </p>

        {loading && (
          <div className="card" style={{ display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
            <span className="spinner" /> Loading…
          </div>
        )}

        {!loading && error && (
          <div className="alert alert-error" role="alert" style={{ marginBottom: '1.5rem' }}>
            {error}
          </div>
        )}

        {!loading && notice && (
          <div className="alert alert-success" role="status" style={{ marginBottom: '1.5rem' }}>
            {notice}
          </div>
        )}

        {/* ── Requests received (alumni/admin) ─────────────────────────────── */}
        {!loading && !isStudent && (
          <div data-testid="requests-received">
            {requests.length === 0 ? (
              <div className="alert alert-info">You have no mentorship requests yet.</div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                {requests.map((r) => (
                  <div key={r.id} className="card" data-testid={`request-${r.id}`}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', gap: '0.75rem', flexWrap: 'wrap' }}>
                      <div>
                        <div style={{ fontWeight: 700 }}>{r.student_name || `Student #${r.student_id}`}</div>
                        <div style={{ fontSize: '0.8rem', color: 'var(--color-text-muted)' }}>
                          {new Date(r.created_at).toLocaleString()}
                          {r.match_score != null && ` • match score ${r.match_score}/100`}
                        </div>
                      </div>
                      <StatusBadge status={r.status} />
                    </div>

                    {r.message && (
                      <p style={{ fontSize: '0.88rem', color: 'var(--color-text-secondary)', marginTop: '0.6rem' }}>
                        “{r.message}”
                      </p>
                    )}

                    {r.status === 'pending' && (
                      <div style={{ display: 'flex', gap: '0.5rem', marginTop: '0.875rem' }}>
                        <button
                          type="button"
                          className="btn btn-primary"
                          disabled={working}
                          onClick={() => handleAction('accept', r.id, 'Request accepted.')}
                        >
                          Accept
                        </button>
                        <button
                          type="button"
                          className="btn btn-secondary"
                          disabled={working}
                          onClick={() => handleAction('decline', r.id, 'Request declined.')}
                        >
                          Decline
                        </button>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* ── Ranked mentors (student) ─────────────────────────────────────── */}
        {!loading && isStudent && matches && (
          <div data-testid="mentor-matches">
            <div className="card" style={{ marginBottom: '1.5rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', gap: '0.75rem', flexWrap: 'wrap' }}>
                <div>
                  <div style={{ fontWeight: 700 }}>
                    {matches.target_occupation
                      ? `Ranked for ${matches.target_occupation}`
                      : 'No target role selected yet'}
                  </div>
                  <div style={{ fontSize: '0.82rem', color: 'var(--color-text-secondary)' }}>
                    {matches.explanation}
                  </div>
                </div>
                <Link to="/career-gap" className="btn btn-secondary" style={{ fontSize: '0.8rem' }}>
                  Review your gaps
                </Link>
              </div>

              {matches.missing_skills?.length > 0 && (
                <div style={{ marginTop: '0.75rem' }}>
                  <div style={{ fontSize: '0.82rem', color: 'var(--color-text-secondary)', marginBottom: '0.35rem' }}>
                    Skills you still need for this role:
                  </div>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.35rem' }}>
                    {matches.missing_skills.map((s) => (
                      <span key={s} className="badge badge-medium">
                        {s}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {matches.matches.length === 0 ? (
              <div className="alert alert-info">
                No alumni mentors are available yet. Check back once alumni create mentor profiles.
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                {matches.matches.map((m) => {
                  const blocked =
                    m.request_status === 'pending' ||
                    m.request_status === 'accepted' ||
                    !m.is_available_for_mentoring ||
                    m.remaining_capacity <= 0

                  return (
                    <div key={m.user_id} className="card" data-testid={`mentor-${m.user_id}`}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', gap: '1rem', flexWrap: 'wrap' }}>
                        <div>
                          <div style={{ fontWeight: 700, fontSize: '1.02rem' }}>{m.full_name}</div>
                          <div style={{ fontSize: '0.85rem', color: 'var(--color-text-secondary)' }}>
                            {[m.job_title, m.company].filter(Boolean).join(' · ') || 'Alumni mentor'}
                            {m.years_of_experience ? ` • ${m.years_of_experience} yrs experience` : ''}
                          </div>
                          {m.college && (
                            <div style={{ fontSize: '0.8rem', color: 'var(--color-text-muted)' }}>{m.college}</div>
                          )}
                        </div>
                        <div style={{ textAlign: 'right' }}>
                          <div style={{ fontSize: '1.75rem', fontWeight: 800, lineHeight: 1 }}>{m.match_score}</div>
                          <span className="badge badge-info">{m.match_band} match</span>
                        </div>
                      </div>

                      {m.bio && (
                        <p style={{ fontSize: '0.85rem', color: 'var(--color-text-secondary)', marginTop: '0.5rem' }}>
                          {m.bio}
                        </p>
                      )}

                      {m.expertise_areas?.length > 0 && (
                        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.3rem', marginTop: '0.6rem' }}>
                          {m.expertise_areas.map((s) => (
                            <span
                              key={s}
                              className={`badge ${m.overlap_skills.includes(s) ? 'badge-strong' : 'badge-info'}`}
                            >
                              {m.overlap_skills.includes(s) ? '★ ' : ''}
                              {s}
                            </span>
                          ))}
                        </div>
                      )}

                      {m.overlap_skills.length > 0 && (
                        <div style={{ fontSize: '0.8rem', color: 'var(--color-brand-light)', marginTop: '0.4rem' }}>
                          Covers {m.overlap_skills.length} of the skills you need: {m.overlap_skills.join(', ')}
                        </div>
                      )}

                      {/* Why this score — the full, auditable breakdown. */}
                      <details style={{ marginTop: '0.75rem' }}>
                        <summary style={{ cursor: 'pointer', fontSize: '0.82rem', fontWeight: 600 }}>
                          Why {m.match_score}/100?
                        </summary>
                        <ul style={{ listStyle: 'none', marginTop: '0.5rem', display: 'flex', flexDirection: 'column', gap: '0.3rem' }}>
                          {m.factors.map((f) => (
                            <li key={f.key} style={{ fontSize: '0.8rem' }}>
                              <strong>
                                {f.label}: {f.earned}/{f.weight}
                              </strong>{' '}
                              <span style={{ color: 'var(--color-text-muted)' }}>{f.detail}</span>
                            </li>
                          ))}
                        </ul>
                      </details>

                      <div style={{ fontSize: '0.78rem', color: 'var(--color-text-muted)', marginTop: '0.5rem' }}>
                        {m.is_available_for_mentoring
                          ? `Mentee slots: ${m.remaining_capacity} of ${m.max_mentees} remaining`
                          : 'Not currently accepting new mentees'}
                        {m.request_status && ` • your request: ${m.request_status}`}
                      </div>

                      {requestingId === m.user_id ? (
                        <div style={{ marginTop: '0.875rem' }}>
                          <label className="label" htmlFor={`msg-${m.user_id}`}>
                            Optional message
                          </label>
                          <textarea
                            id={`msg-${m.user_id}`}
                            className="input"
                            rows={3}
                            maxLength={1000}
                            value={message}
                            onChange={(e) => setMessage(e.target.value)}
                            placeholder="Tell them what you'd like help with…"
                          />
                          <div style={{ display: 'flex', gap: '0.5rem', marginTop: '0.5rem' }}>
                            <button
                              type="button"
                              className="btn btn-primary"
                              disabled={working}
                              onClick={() => handleRequest(m.user_id)}
                            >
                              Send request
                            </button>
                            <button
                              type="button"
                              className="btn btn-secondary"
                              disabled={working}
                              onClick={() => {
                                setRequestingId(null)
                                setMessage('')
                              }}
                            >
                              Cancel
                            </button>
                          </div>
                        </div>
                      ) : (
                        <button
                          type="button"
                          className="btn btn-primary"
                          style={{ marginTop: '0.875rem' }}
                          disabled={working || blocked}
                          onClick={() => {
                            setRequestingId(m.user_id)
                            setMessage('')
                          }}
                        >
                          {m.request_status === 'accepted'
                            ? 'Already your mentor'
                            : m.request_status === 'pending'
                              ? 'Request pending'
                              : m.remaining_capacity <= 0
                                ? 'At capacity'
                                : !m.is_available_for_mentoring
                                  ? 'Unavailable'
                                  : 'Request mentorship'}
                        </button>
                      )}
                    </div>
                  )
                })}
              </div>
            )}

            {matches.disclaimer && (
              <p style={{ marginTop: '1rem', fontSize: '0.78rem', color: 'var(--color-text-muted)' }}>
                {matches.disclaimer}
              </p>
            )}
          </div>
        )}

        {/* ── Requests you sent (student) ──────────────────────────────────── */}
        {!loading && isStudent && (
          <div className="card" style={{ marginTop: '1.5rem' }} data-testid="requests-sent">
            <div style={{ fontWeight: 600, marginBottom: '0.75rem' }}>Your requests</div>
            {requests.length === 0 ? (
              <div style={{ fontSize: '0.85rem', color: 'var(--color-text-muted)' }}>
                You have not requested mentorship yet.
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.6rem' }}>
                {requests.map((r) => (
                  <div
                    key={r.id}
                    style={{ display: 'flex', justifyContent: 'space-between', gap: '0.75rem', alignItems: 'center', flexWrap: 'wrap' }}
                  >
                    <div style={{ fontSize: '0.88rem' }}>
                      {r.alumni_name || `Mentor #${r.alumni_id}`}
                      {r.match_score != null && (
                        <span style={{ color: 'var(--color-text-muted)' }}> • score {r.match_score}</span>
                      )}
                    </div>
                    <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
                      <StatusBadge status={r.status} />
                      {r.status === 'pending' && (
                        <button
                          type="button"
                          className="btn btn-secondary"
                          style={{ fontSize: '0.78rem', padding: '0.25rem 0.6rem' }}
                          disabled={working}
                          onClick={() => handleAction('cancel', r.id, 'Request cancelled.')}
                        >
                          Cancel
                        </button>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
