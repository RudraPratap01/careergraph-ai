/**
 * ResumePage — resume evidence extraction and review.
 *
 * Flow: upload a PDF/DOCX/TXT file → the backend extracts text and matches it
 * against the curated skill taxonomy (with evidence snippets and confidence)
 * → the student reviews, edits and confirms exactly which skills are saved.
 *
 * Note: extraction is deterministic/rule-based. No external AI or NLP service
 * receives the resume, and no skill is added without explicit confirmation.
 */

import { useState, useEffect, useRef } from 'react'
import { resumeAPI, profileAPI, formatApiError } from '../services/api'
import Icon from '../components/Icon'

const EVIDENCED_SOURCES = new Set(['assessment', 'github'])

/**
 * Combines existing profile skills with newly extracted resume matches.
 *
 * The backend treats the confirmed list as the complete profile skill list, so
 * omitting an existing skill would delete it. Keeping non-evidenced profile
 * skills in the review makes that replacement explicit and reversible. Skills
 * already evidenced by an assessment or GitHub are omitted here because the
 * backend always preserves them and this review can never downgrade them.
 */
function buildReviewSkills(profileSkills = [], extractedSkills = []) {
  const profileByName = new Map()
  for (const skill of profileSkills) {
    const key = String(skill.name || '').trim().toLowerCase()
    if (key) profileByName.set(key, skill)
  }

  const extracted = (extractedSkills || []).map((skill) => {
    const key = String(skill.normalized_name || skill.name || '').trim().toLowerCase()
    const existing = profileByName.get(key)
    return {
      ...skill,
      proficiency: existing?.level || skill.proficiency || 'intermediate',
      source: 'resume',
      from_profile: false,
    }
  })

  const extractedNames = new Set(
    extracted.map((skill) => String(skill.normalized_name || skill.name || '').trim().toLowerCase())
  )
  const kept = []
  const keptNames = new Set()
  for (const skill of profileSkills) {
    if (EVIDENCED_SOURCES.has(skill.source)) continue
    const key = String(skill.name || '').trim().toLowerCase()
    if (!key || extractedNames.has(key) || keptNames.has(key)) continue
    keptNames.add(key)
    kept.push({
      name: skill.name,
      normalized_name: skill.name,
      category: 'Existing profile',
      confidence: null,
      evidence: 'Already saved on your profile before this resume review.',
      proficiency: skill.level || 'intermediate',
      source: skill.source === 'resume' ? 'resume' : 'self',
      from_profile: true,
    })
  }

  return [...extracted, ...kept]
}

function profileSkillsFromResponse(response) {
  return response?.data?.student_profile?.skills || []
}

export default function ResumePage() {
  const fileInputRef = useRef(null)

  const [uploading, setUploading] = useState(false)
  const [parsingStage, setParsingStage] = useState('')
  const [latestResume, setLatestResume] = useState(null)
  const [loadingLatest, setLoadingLatest] = useState(true)
  const [profileSkills, setProfileSkills] = useState([])
  const [profileLoaded, setProfileLoaded] = useState(false)

  // Review skills state
  const [skillsToReview, setSkillsToReview] = useState([])
  const [selectedCategory, setSelectedCategory] = useState('All')
  const [showRawText, setShowRawText] = useState(false)

  // Feedback states
  const [successMsg, setSuccessMsg] = useState(null)
  const [errorMsg, setErrorMsg] = useState(null)
  const [syncing, setSyncing] = useState(false)

  // Add missing skill helper
  const [manualSkillName, setManualSkillName] = useState('')
  const [manualSkillLevel, setManualSkillLevel] = useState('intermediate')

  const refreshLatestResume = async () => {
    try {
      const res = await resumeAPI.getLatestResume()
      setLatestResume(res.data)
    } catch (err) {
      // 404 is normal if no resume has been uploaded yet.
      if (err.response?.status !== 404) {
        setErrorMsg('Could not refresh the latest resume details.')
      }
    }
  }

  useEffect(() => {
    let cancelled = false
    const load = async () => {
      const [profileResult, resumeResult] = await Promise.allSettled([
        profileAPI.getMeProfile(),
        resumeAPI.getLatestResume(),
      ])
      if (cancelled) return

      let loadedProfileSkills = []
      if (profileResult.status === 'fulfilled') {
        loadedProfileSkills = profileSkillsFromResponse(profileResult.value)
        setProfileSkills(loadedProfileSkills)
        setProfileLoaded(true)
      }

      if (resumeResult.status === 'fulfilled') {
        setLatestResume(resumeResult.value.data)
        setSkillsToReview(
          buildReviewSkills(loadedProfileSkills, resumeResult.value.data.extracted_skills)
        )
      } else if (resumeResult.reason?.response?.status !== 404) {
        setErrorMsg('Could not load your previous resume. You can still upload a new one.')
      }
      setLoadingLatest(false)
    }
    // Initial data fetch: all state updates happen after the requests resolve.
    // oxlint-disable-next-line react/set-state-in-effect
    load()
    return () => {
      cancelled = true
    }
  }, [])


  const handleFileUpload = async (file) => {
    if (!file) return

    // Client-side extension validation
    const ext = file.name.split('.').pop().toLowerCase()
    if (!['pdf', 'docx', 'txt'].includes(ext)) {
      setErrorMsg('Unsupported format. Please upload a PDF, DOCX, or TXT file.')
      return
    }

    if (file.size > 10 * 1024 * 1024) {
      setErrorMsg('File exceeds 10 MB limit.')
      return
    }

    setErrorMsg(null)
    setSuccessMsg(null)
    setUploading(true)
    setParsingStage('Uploading file…')

    const formData = new FormData()
    formData.append('file', file)

    try {
      setParsingStage('Extracting text and matching skills against the curated taxonomy…')
      const [res, profileRes] = await Promise.all([
        resumeAPI.uploadResume(formData),
        profileAPI.getMeProfile().catch(() => null),
      ])
      const data = res.data
      const loadedProfileSkills = profileRes ? profileSkillsFromResponse(profileRes) : profileSkills
      if (profileRes) {
        setProfileSkills(loadedProfileSkills)
        setProfileLoaded(true)
      }

      setSuccessMsg(`Resume "${data.filename}" parsed. Found ${data.extracted_skills_count} skill matches to review.`)
      setSkillsToReview(buildReviewSkills(loadedProfileSkills, data.extracted_skills || []))
      await refreshLatestResume()
    } catch (err) {
      setErrorMsg(formatApiError(err, 'Resume upload failed. Please try again.'))
    } finally {

      setUploading(false)
      setParsingStage('')
      if (fileInputRef.current) fileInputRef.current.value = ''
    }
  }

  const handleDrop = (e) => {
    e.preventDefault()
    if (uploading) return
    const droppedFile = e.dataTransfer.files?.[0]
    if (droppedFile) handleFileUpload(droppedFile)
  }

  const handleProficiencyChange = (skillName, newLevel) => {
    setSkillsToReview((prev) =>
      prev.map((s) => (s.name === skillName ? { ...s, proficiency: newLevel } : s))
    )
  }

  const handleRemoveSkill = (skillName) => {
    setSkillsToReview((prev) => prev.filter((s) => s.name !== skillName))
  }

  const handleAddManualSkill = (e) => {
    e.preventDefault()
    const trimmed = manualSkillName.trim()
    if (!trimmed) return
    if (skillsToReview.some((s) => s.name.toLowerCase() === trimmed.toLowerCase())) {
      setManualSkillName('')
      return
    }

    const newSkill = {
      name: trimmed,
      normalized_name: trimmed,
      category: 'Self-reported',
      confidence: null,
      evidence: 'Added manually during this review.',
      proficiency: manualSkillLevel,
      source: 'self',
      from_profile: false,
    }
    setSkillsToReview((prev) => [newSkill, ...prev])
    setManualSkillName('')
  }

  const handleConfirmAndSync = async () => {
    setSyncing(true)
    setErrorMsg(null)
    setSuccessMsg(null)

    try {
      const payload = {
        resume_id: latestResume?.id,
        skills: skillsToReview.map((s) => ({
          name: s.normalized_name || s.name,
          level: s.proficiency || 'intermediate',
          category: s.category,
          source: s.source === 'self' ? 'self' : 'resume',
        })),
      }

      const res = await resumeAPI.confirmSkills(payload)
      setSuccessMsg(
        `${res.data.total_confirmed_skills} skills synced to your profile.`
      )
      await refreshLatestResume()
    } catch (err) {
      setErrorMsg(formatApiError(err, 'Failed to sync skills.'))
    } finally {

      setSyncing(false)
    }
  }

  // Filter skills by category
  const categories = ['All', ...new Set(skillsToReview.map((s) => s.category).filter(Boolean))]
  const filteredSkills =
    selectedCategory === 'All'
      ? skillsToReview
      : skillsToReview.filter((s) => s.category === selectedCategory)
  const keptCount = skillsToReview.filter((s) => s.from_profile).length

  return (
    <div className="page-container">
      <div className="fade-up">
        {/* Header */}
        <div style={{ marginBottom: '2rem' }}>
          <h1 className="section-title" style={{ marginBottom: '0.5rem' }}>
            Resume analysis
          </h1>
          <p className="section-subtitle" style={{ marginBottom: 0 }}>
            Upload a resume to extract skills with supporting evidence and a confidence score.
            Extraction is deterministic and happens in your CareerGraph backend — you review every
            match before it is added. Existing profile skills are included in the review so syncing
            never silently removes them.
          </p>
        </div>

        {/* Notifications */}
        {successMsg && (
          <div className="alert alert-success" role="status" style={{ marginBottom: '1.5rem' }}>
            {successMsg}
          </div>
        )}
        {errorMsg && (
          <div className="alert alert-error" role="alert" style={{ marginBottom: '1.5rem' }}>
            {errorMsg}
          </div>
        )}
        {!profileLoaded && !loadingLatest && (
          <div className="alert alert-error" role="alert" style={{ marginBottom: '1.5rem' }}>
            We couldn&apos;t load your existing profile skills. Reload the page before syncing so a
            resume review cannot replace them.
          </div>
        )}

        {/* ── File Upload Section ─────────────────────────────────────────── */}
        <div
          onDragOver={(e) => e.preventDefault()}
          onDrop={handleDrop}
          className="card"
          style={{
            border: '2px dashed var(--color-border-strong)',
            padding: '2.5rem 1.5rem',
            textAlign: 'center',
            marginBottom: '2rem',
            background: 'var(--color-bg-surface)',
          }}
        >
          <input
            ref={fileInputRef}
            type="file"
            accept=".pdf,.docx,.txt"
            className="sr-only"
            tabIndex={-1}
            aria-label="Resume file"
            onChange={(e) => {
              const file = e.target.files?.[0]
              if (file) handleFileUpload(file)
            }}
          />

          <div
            className="empty-state-icon"
            aria-hidden="true"
            style={{ margin: '0 auto 0.9rem' }}
          >
            <Icon name="file" size={24} />
          </div>

          <h2 style={{ fontSize: '1.2rem', fontWeight: 700, marginBottom: '0.5rem' }}>
            {uploading ? parsingStage : 'Drag and drop your resume'}
          </h2>

          <p style={{ color: 'var(--color-text-secondary)', fontSize: '0.875rem', maxWidth: '480px', margin: '0 auto 1.25rem' }}>
            Accepts <strong>PDF</strong>, <strong>DOCX</strong>, or <strong>TXT</strong> (maximum 10 MB). The
            file is sent to your own CareerGraph backend for text extraction — no third-party AI
            service is involved.
          </p>

          <button
            id="btn-upload-resume"
            type="button"
            className="btn btn-primary"
            disabled={uploading}
            onClick={() => fileInputRef.current?.click()}
          >
            {uploading ? (
              <><span className="spinner" style={{ width: '16px', height: '16px' }} /> Analyzing resume…</>
            ) : 'Choose a file'}
          </button>
        </div>

        {/* ── Latest Upload Info Bar ──────────────────────────────────────── */}
        {latestResume && (
          <div
            className="card"
            style={{
              marginBottom: '2rem',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              flexWrap: 'wrap',
              gap: '1rem',
              background: 'var(--color-bg-elevated)',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.875rem' }}>
              <span
                aria-hidden="true"
                style={{ color: 'var(--color-brand-light)', display: 'flex' }}
              >
                <Icon name="file" size={20} />
              </span>
              <div>
                <div style={{ fontWeight: 700, fontSize: '0.95rem' }}>{latestResume.filename}</div>
                <div style={{ fontSize: '0.8rem', color: 'var(--color-text-secondary)' }}>
                  {(latestResume.file_size_bytes / 1024).toFixed(1)} KB • Uploaded {new Date(latestResume.created_at).toLocaleDateString()}
                </div>
              </div>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
              <span className={`badge ${latestResume.status === 'reviewed' ? 'badge-strong' : 'badge-medium'}`}>
                {latestResume.status === 'reviewed' ? 'Confirmed by student' : 'Awaiting review'}
              </span>

              {latestResume.raw_text && (
                <button
                  type="button"
                  className="btn btn-secondary"
                  style={{ fontSize: '0.8rem', padding: '0.35rem 0.75rem' }}
                  onClick={() => setShowRawText(!showRawText)}
                  aria-expanded={showRawText}
                  aria-controls="resume-raw-text"
                >
                  {showRawText ? 'Hide extracted text' : 'View extracted text'}
                </button>
              )}
            </div>
          </div>
        )}

        {/* Raw text collapsible preview */}
        {showRawText && latestResume?.raw_text && (
          <div id="resume-raw-text" className="card" style={{ marginBottom: '2rem', background: '#0a0d18' }}>
            <h4 style={{ fontSize: '0.9rem', fontWeight: 700, marginBottom: '0.75rem', color: 'var(--color-text-secondary)' }}>
              Raw Extracted Resume Text ({latestResume.raw_text.length} characters)
            </h4>
            <pre style={{
              whiteSpace: 'pre-wrap',
              fontFamily: 'monospace',
              fontSize: '0.8rem',
              lineHeight: 1.6,
              color: 'var(--color-text-secondary)',
              maxHeight: '260px',
              overflowY: 'auto',
              padding: '0.75rem',
              background: 'rgba(0,0,0,0.3)',
              borderRadius: '6px',
            }}>
              {latestResume.raw_text}
            </pre>
          </div>
        )}

        {/* ── Extracted Skills Review Section ─────────────────────────────── */}
        {skillsToReview.length > 0 && (
          <div className="card" style={{ marginBottom: '2rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '1rem', marginBottom: '1.5rem' }}>
              <div>
                <h3 style={{ fontSize: '1.2rem', fontWeight: 700, marginBottom: '0.25rem' }}>
                  Review skills before syncing ({skillsToReview.length})
                </h3>
                <p style={{ fontSize: '0.85rem', color: 'var(--color-text-secondary)' }}>
                  Extracted matches include an evidence snippet and confidence score. Existing
                  profile skills are included here so you can keep or remove them deliberately
                  before syncing.
                </p>
                {keptCount > 0 && (
                  <span className="badge badge-info" style={{ marginTop: '0.5rem' }}>
                    {keptCount} existing profile {keptCount === 1 ? 'skill' : 'skills'} kept
                  </span>
                )}
              </div>

              {/* Confirm & Sync Action */}
              <button
                id="btn-confirm-skills"
                type="button"
                className="btn btn-primary"
                disabled={syncing || !profileLoaded}
                onClick={handleConfirmAndSync}
                style={{ padding: '0.625rem 1.5rem' }}
              >
                {syncing ? (
                  <><span className="spinner" style={{ width: '16px', height: '16px' }} /> Syncing…</>
                ) : 'Confirm & sync to profile'}
              </button>
            </div>

            {/* Category Filter Chips */}
            <div
              role="group"
              aria-label="Filter skills by category"
              style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem', marginBottom: '1.5rem' }}
            >
              {categories.map((cat) => (
                <button
                  key={cat}
                  type="button"
                  aria-pressed={selectedCategory === cat}
                  onClick={() => setSelectedCategory(cat)}
                  style={{
                    padding: '0.35rem 0.8rem',
                    borderRadius: '999px',
                    fontSize: '0.8rem',
                    fontWeight: 600,
                    border: '1px solid var(--color-border)',
                    background: selectedCategory === cat ? 'var(--color-brand-primary)' : 'var(--color-bg-elevated)',
                    color: selectedCategory === cat ? '#fff' : 'var(--color-text-secondary)',
                    cursor: 'pointer',
                  }}
                >
                  {cat} ({cat === 'All' ? skillsToReview.length : skillsToReview.filter((s) => s.category === cat).length})
                </button>
              ))}
            </div>

            {/* Skills Cards Grid */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '1rem', marginBottom: '2rem' }}>
              {filteredSkills.map((skill) => {
                const confPercent =
                  typeof skill.confidence === 'number' ? Math.round(skill.confidence * 100) : null
                const confColor =
                  confPercent == null
                    ? 'var(--color-brand-light)'
                    : confPercent >= 90
                      ? 'var(--color-accent-green)'
                      : confPercent >= 80
                        ? 'var(--color-brand-light)'
                        : 'var(--color-accent-yellow)'

                return (
                  <div
                    key={skill.name}
                    style={{
                      padding: '1rem',
                      background: 'var(--color-bg-elevated)',
                      border: '1px solid var(--color-border)',
                      borderRadius: '10px',
                      display: 'flex',
                      flexDirection: 'column',
                      justifyContent: 'space-between',
                      gap: '0.75rem',
                    }}
                  >
                    <div>
                      {/* Title & Category & Confidence */}
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '0.375rem' }}>
                        <div>
                          <div style={{ fontWeight: 700, fontSize: '1rem' }}>{skill.name}</div>
                          <span style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)' }}>{skill.category}</span>
                        </div>

                        {confPercent == null ? (
                          <span className="badge badge-info" style={{ fontSize: '0.725rem' }}>
                            {skill.from_profile ? 'Kept from profile' : 'Self-reported'}
                          </span>
                        ) : (
                          <span
                            className="badge"
                            style={{
                              background: `${confColor}18`,
                              color: confColor,
                              border: `1px solid ${confColor}40`,
                              fontSize: '0.725rem',
                            }}
                          >
                            {confPercent}% confidence
                          </span>
                        )}
                      </div>

                      {/* Evidence or profile context */}
                      {skill.evidence && (
                        <div
                          style={{
                            fontSize: '0.78rem',
                            color: 'var(--color-text-secondary)',
                            background: 'rgba(0,0,0,0.25)',
                            padding: '0.5rem 0.625rem',
                            borderRadius: '6px',
                            borderLeft: `2px solid ${confColor}`,
                            fontStyle: confPercent == null ? 'normal' : 'italic',
                            lineHeight: 1.4,
                          }}
                        >
                          {confPercent == null ? skill.evidence : `"${skill.evidence}"`}
                        </div>
                      )}
                    </div>

                    {/* Bottom controls: proficiency & remove */}
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', paddingTop: '0.5rem', borderTop: '1px solid rgba(255,255,255,0.05)' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                        <span style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)' }}>Proficiency:</span>
                        <select
                          className="input"
                          aria-label={`Proficiency for ${skill.name}`}
                          style={{ padding: '0.2rem 0.5rem', fontSize: '0.78rem', width: 'auto', height: '28px' }}
                          value={skill.proficiency || 'intermediate'}
                          onChange={(e) => handleProficiencyChange(skill.name, e.target.value)}
                        >
                          <option value="beginner">Beginner</option>
                          <option value="intermediate">Intermediate</option>
                          <option value="advanced">Advanced</option>
                        </select>
                      </div>

                      <button
                        type="button"
                        onClick={() => handleRemoveSkill(skill.name)}
                        aria-label={`Remove ${skill.name} from this review`}
                        style={{
                          background: 'transparent',
                          border: 'none',
                          color: 'var(--color-accent-red)',
                          fontSize: '0.78rem',
                          cursor: 'pointer',
                          padding: '0.2rem 0.4rem',
                        }}
                        title="Remove false positive"
                      >
                        Remove
                      </button>
                    </div>
                  </div>
                )
              })}
            </div>

            {/* Quick add missing skill */}
            <form onSubmit={handleAddManualSkill} style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap', alignItems: 'center', background: 'var(--color-bg-elevated)', padding: '0.75rem 1rem', borderRadius: '8px' }}>
              <span style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--color-text-secondary)' }}>
                Missed a skill?
              </span>
              <label htmlFor="manual-skill-name" className="sr-only">Skill name</label>
              <input
                id="manual-skill-name"
                type="text"
                className="input"
                style={{ flex: 1, minWidth: '180px', height: '36px', padding: '0.4rem 0.75rem', fontSize: '0.85rem' }}
                placeholder="e.g. Next.js, Redis, PyTorch"
                value={manualSkillName}
                onChange={(e) => setManualSkillName(e.target.value)}
              />
              <label htmlFor="manual-skill-level" className="sr-only">Proficiency level</label>
              <select
                id="manual-skill-level"
                className="input"
                style={{ width: '130px', height: '36px', padding: '0.4rem', fontSize: '0.85rem' }}
                value={manualSkillLevel}
                onChange={(e) => setManualSkillLevel(e.target.value)}
              >
                <option value="beginner">Beginner</option>
                <option value="intermediate">Intermediate</option>
                <option value="advanced">Advanced</option>
              </select>
              <button type="submit" className="btn btn-secondary" style={{ height: '36px', fontSize: '0.85rem' }}>
                + Add to Review
              </button>
            </form>
          </div>
        )}

        {/* Loading state for the most recent upload metadata */}
        {loadingLatest && (
          <div className="card row" role="status" style={{ marginBottom: '2rem' }}>
            <span className="spinner" /> Loading your latest resume…
          </div>
        )}
      </div>
    </div>
  )
}
