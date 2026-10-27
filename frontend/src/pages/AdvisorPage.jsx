/**
 * AdvisorPage — Phase 7: grounded career intelligence.
 *
 * The page shows the deterministic context it will use (target role,
 * readiness, missing skills, first roadmap step), lets the student ask a
 * career-learning question, and renders the answer with its retrieved source
 * IDs. The backend decides whether an LLM is configured; the UI never pretends
 * that a model was used when it was not.
 *
 * All values are API-backed. In particular, this page does not compute or
 * rewrite the readiness score, and it never sends resume text.
 */

import { useEffect, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import EmptyState from '../components/EmptyState'
import Icon from '../components/Icon'
import PageHeader from '../components/PageHeader'
import { careerAPI, formatApiError, intelligenceAPI, roadmapAPI } from '../services/api'

const MAX_QUESTION_LENGTH = 500

const BASE_SUGGESTIONS = [
  'What should I learn first for my target role?',
  'How can I close my biggest skill gap?',
  'How does my readiness score work?',
  'How do I know if my roadmap order is correct?',
  'What kind of portfolio project should I build next?',
]

function formatMode(result) {
  return result.mode === 'llm' ? 'LLM explanation · citations checked' : 'Local grounded answer'
}

function AdvisorAnswer({ result }) {
  return (
    <article
      className="card advisor-answer"
      data-testid="advisor-answer"
      aria-labelledby="advisor-answer-heading"
      style={{ marginTop: '1.25rem' }}
    >
      <div className="spread" style={{ gap: '0.75rem', flexWrap: 'wrap', marginBottom: '0.8rem' }}>
        <div>
          <p className="eyebrow" style={{ marginBottom: '0.3rem' }}>Grounded response</p>
          <h2 id="advisor-answer-heading" style={{ fontSize: '1.15rem' }}>
            {result.context?.occupation_name
              ? `Next steps for ${result.context.occupation_name}`
              : 'A grounded starting point'}
          </h2>
        </div>
        <span className={`badge ${result.mode === 'llm' ? 'badge-info' : 'badge-neutral'}`}>
          {formatMode(result)}
        </span>
      </div>

      {result.notice && (
        <p className="alert alert-info" role="status" style={{ marginBottom: '1rem' }}>
          {result.notice}
        </p>
      )}

      <p className="advisor-answer-text">{result.answer}</p>

      {result.context?.readiness_score != null && (
        <div className="surface-muted advisor-score" style={{ marginBlock: '1rem' }}>
          <span className="tiny muted">Deterministic readiness (not changed by this answer)</span>
          <span className="advisor-score-value">{result.context.readiness_score}%</span>
          <span className="badge badge-info">{result.context.readiness_band}</span>
        </div>
      )}

      <section aria-labelledby="advisor-sources-heading" style={{ marginTop: '1.25rem' }}>
        <div className="spread" style={{ gap: '0.75rem', flexWrap: 'wrap', marginBottom: '0.65rem' }}>
          <h3 id="advisor-sources-heading" style={{ fontSize: '0.95rem' }}>Sources used</h3>
          <span className="tiny muted">
            {result.sources?.length || 0} retrieved source{result.sources?.length === 1 ? '' : 's'}
          </span>
        </div>
        {result.sources?.length ? (
          <ol className="advisor-source-list">
            {result.sources.map((source) => (
              <li key={source.id} className="advisor-source">
                <span className="advisor-source-id">{source.id}</span>
                <div style={{ minWidth: 0 }}>
                  <div className="row" style={{ gap: '0.45rem', flexWrap: 'wrap' }}>
                    <strong className="small">{source.title}</strong>
                    <span className="badge badge-neutral" style={{ fontSize: '0.66rem' }}>
                      {source.kind}
                    </span>
                  </div>
                  <p className="tiny muted" style={{ marginTop: '0.15rem' }}>
                    {source.source_label}
                  </p>
                  <p className="small" style={{ marginTop: '0.3rem', color: 'var(--color-text-secondary)' }}>
                    {source.snippet}
                  </p>
                </div>
              </li>
            ))}
          </ol>
        ) : (
          <p className="small muted">
            No sufficiently relevant source was retrieved, so the answer states a limitation
            instead of inventing guidance.
          </p>
        )}
      </section>

      <div className="advisor-answer-meta">
        <details>
          <summary>Privacy and limitations</summary>
          <p className="small muted" style={{ marginTop: '0.5rem' }}>{result.privacy_note}</p>
          <ul className="advisor-limitations">
            {result.limitations?.map((limitation) => (
              <li key={limitation}>{limitation}</li>
            ))}
          </ul>
        </details>
        <p className="tiny muted" style={{ marginTop: '0.75rem' }}>{result.disclaimer}</p>
      </div>
    </article>
  )
}

export default function AdvisorPage() {
  const [status, setStatus] = useState(null)
  const [statusError, setStatusError] = useState(null)
  const [gap, setGap] = useState(null)
  const [roadmap, setRoadmap] = useState(null)
  const [contextLoading, setContextLoading] = useState(true)
  const [question, setQuestion] = useState('')
  const [answer, setAnswer] = useState(null)
  const [asking, setAsking] = useState(false)
  const [askError, setAskError] = useState(null)
  const questionRef = useRef(null)

  useEffect(() => {
    let cancelled = false

    Promise.allSettled([
      careerAPI.getGapAnalysis(),
      roadmapAPI.getCurrent(),
      intelligenceAPI.status(),
    ]).then(([gapResult, roadmapResult, statusResult]) => {
      if (cancelled) return
      setGap(gapResult.status === 'fulfilled' ? gapResult.value.data : null)
      setRoadmap(roadmapResult.status === 'fulfilled' ? roadmapResult.value.data : null)
      if (statusResult.status === 'fulfilled') {
        setStatus(statusResult.value.data)
      } else {
        setStatusError(
          formatApiError(statusResult.reason, 'Advisor configuration could not be loaded. You can still ask a question.'),
        )
      }
      setContextLoading(false)
    })

    return () => {
      cancelled = true
    }
  }, [])

  const firstStep = roadmap?.steps
    ? [...roadmap.steps].sort((a, b) => a.position - b.position)[0]
    : null
  const suggestions = BASE_SUGGESTIONS

  const handleSuggestion = (suggestion) => {
    setQuestion(suggestion)
    setAskError(null)
    questionRef.current?.focus()
  }

  const handleSubmit = async (event) => {
    event.preventDefault()
    const trimmed = question.trim()
    if (trimmed.length < 3) {
      setAskError('Enter a question with at least 3 characters.')
      questionRef.current?.focus()
      return
    }
    setAsking(true)
    setAskError(null)
    try {
      const response = await intelligenceAPI.ask(
        trimmed,
        gap?.occupation_key || undefined,
      )
      setAnswer(response.data)
    } catch (error) {
      setAskError(
        formatApiError(error, 'The advisor could not answer just now. Your deterministic scores were not changed.'),
      )
    } finally {
      setAsking(false)
    }
  }

  return (
    <div className="page-container">
      <div className="fade-up">
        <PageHeader
          eyebrow="Phase 7 · Grounded career intelligence"
          title="Career advisor"
          subtitle="Ask about your next learning step. Answers combine your deterministic gap and roadmap context with a curated, citation-attributed knowledge base."
          actions={
            <Link to="/career-gap" className="btn btn-secondary">
              <Icon name="chart" size={15} /> Review readiness
            </Link>
          }
        />

        <div className="advisor-layout">
          <section className="card" aria-labelledby="advisor-question-heading">
            <div className="spread" style={{ gap: '0.75rem', flexWrap: 'wrap', marginBottom: '0.6rem' }}>
              <div>
                <p className="eyebrow" style={{ marginBottom: '0.3rem' }}>Ask your question</p>
                <h2 id="advisor-question-heading" style={{ fontSize: '1.25rem' }}>
                  What should I work on next?
                </h2>
              </div>
              {status && (
                <span className={`badge ${status.llm_configured ? 'badge-info' : 'badge-neutral'}`}>
                  {status.llm_configured ? 'LLM explanations enabled' : 'Offline · no LLM key'}
                </span>
              )}
            </div>
            <p className="small muted" style={{ marginBottom: '0.9rem' }}>
              The advisor explains the evidence; it never recalculates your readiness or changes your
              roadmap order. If no LLM is configured, a deterministic answer is generated locally.
            </p>

            <div className="advisor-suggestions" aria-label="Suggested questions">
              {suggestions.map((suggestion) => (
                <button
                  key={suggestion}
                  type="button"
                  className="advisor-chip"
                  onClick={() => handleSuggestion(suggestion)}
                >
                  {suggestion}
                </button>
              ))}
            </div>

            <form onSubmit={handleSubmit}>
              <label className="label" htmlFor="advisor-question">Your question</label>
              <textarea
                id="advisor-question"
                ref={questionRef}
                className="input advisor-textarea"
                rows={4}
                maxLength={MAX_QUESTION_LENGTH}
                value={question}
                onChange={(event) => setQuestion(event.target.value)}
                aria-describedby="advisor-question-help"
                placeholder="e.g. Which prerequisite should I learn before Docker?"
              />
              <div className="spread advisor-form-footer">
                <span id="advisor-question-help" className="tiny muted">
                  {question.length}/{MAX_QUESTION_LENGTH} characters · no resume text is sent
                </span>
                <button type="submit" className="btn btn-primary" disabled={asking}>
                  {asking ? (
                    <>
                      <span className="spinner spinner-sm" aria-hidden="true" /> Thinking…
                    </>
                  ) : (
                    <>
                      <Icon name="spark" size={15} /> Ask advisor
                    </>
                  )}
                </button>
              </div>
            </form>

            {askError && (
              <div className="alert alert-error" role="alert" style={{ marginTop: '1rem' }}>
                {askError}
              </div>
            )}

            {asking && (
              <div className="advisor-loading" role="status" aria-live="polite">
                <span className="spinner" aria-hidden="true" />
                <span>Retrieving curated sources and drafting a grounded answer…</span>
              </div>
            )}

            {!asking && answer && <AdvisorAnswer result={answer} />}

            {!asking && !answer && (
              <div style={{ marginTop: '1.25rem' }}>
                <EmptyState icon={<Icon name="spark" size={18} />} title="Your answer will appear here">
                  Pick a suggested question or write your own. Sources are listed with every answer so you
                  can check the evidence.
                </EmptyState>
              </div>
            )}
          </section>

          <aside className="stack" aria-label="Advisor context">
            <section className="card" aria-labelledby="advisor-context-heading">
              <div className="spread" style={{ marginBottom: '0.6rem' }}>
                <h2 id="advisor-context-heading" style={{ fontSize: '1rem' }}>Your current context</h2>
                <Link to="/profile" className="card-action">Edit</Link>
              </div>
              {contextLoading ? (
                <p className="small muted"><span className="spinner spinner-sm" aria-hidden="true" /> Loading context…</p>
              ) : gap ? (
                <dl className="advisor-context-list">
                  <div>
                    <dt>Target role</dt>
                    <dd>{gap.occupation_name}</dd>
                  </div>
                  <div>
                    <dt>Readiness</dt>
                    <dd>{gap.readiness_score}% · {gap.readiness_band}</dd>
                  </div>
                  <div>
                    <dt>Required skills</dt>
                    <dd>{gap.matched_count} matched · {gap.missing_skills?.length || 0} missing</dd>
                  </div>
                  <div>
                    <dt>First roadmap step</dt>
                    <dd>{firstStep ? firstStep.skill : 'No roadmap yet'}</dd>
                  </div>
                </dl>
              ) : (
                <p className="small muted">
                  No target role or gap analysis is available yet.{' '}
                  <Link to="/profile">Set a target role</Link> to make the context specific. You can
                  still ask general questions grounded in the curated knowledge base.
                </p>
              )}
              {(!gap || !firstStep) && !contextLoading && (
                <div className="row" style={{ gap: '0.5rem', flexWrap: 'wrap', marginTop: '0.85rem' }}>
                  <Link to="/career-gap" className="btn btn-secondary btn-sm">Analyse a role</Link>
                  <Link to="/roadmap" className="btn btn-ghost btn-sm">Build a roadmap</Link>
                </div>
              )}
            </section>

            <section className="card" aria-labelledby="advisor-how-heading">
              <div className="row" style={{ gap: '0.5rem', marginBottom: '0.55rem' }}>
                <Icon name="shield" size={16} />
                <h2 id="advisor-how-heading" style={{ fontSize: '1rem' }}>How this stays honest</h2>
              </div>
              <ul className="advisor-principles">
                <li>Retrieval is local lexical search over curated sources, not a web search.</li>
                <li>No course links are invented; only retrieved source cards are shown.</li>
                <li>The deterministic score and prerequisite order stay authoritative.</li>
                <li>No resume file, resume text, email, name or account ID is sent to an LLM.</li>
              </ul>
              {statusError && (
                <p className="tiny muted" style={{ marginTop: '0.65rem' }}>{statusError}</p>
              )}
              {status && (
                <p className="tiny muted" style={{ marginTop: '0.65rem' }}>
                  {status.knowledge?.document_count || 0} curated documents ·{' '}
                  {status.knowledge?.chunk_count || 0} retrievable chunks
                  {status.llm_configured && status.model ? ` · model: ${status.model}` : ''}
                </p>
              )}
            </section>
          </aside>
        </div>
      </div>
    </div>
  )
}
