/**
 * ResumePage — Phase 3: Resume Intelligence.
 *
 * Implements:
 *   1. Secure PDF / DOCX / TXT file upload with drag-and-drop
 *   2. Text extraction telemetry and raw text preview
 *   3. AI skill extraction with confidence metrics and evidence excerpts
 *   4. Student review workflow: adjust proficiency, remove false positives, add missing skills
 *   5. One-click sync to StudentProfile
 */

import { useState, useEffect, useRef } from 'react'
import { resumeAPI, formatApiError } from '../services/api'


export default function ResumePage() {
  const fileInputRef = useRef(null)

  const [uploading, setUploading] = useState(false)
  const [parsingStage, setParsingStage] = useState('')
  const [latestResume, setLatestResume] = useState(null)
  const [loadingLatest, setLoadingLatest] = useState(true)

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

  const fetchLatestResume = async () => {
    setLoadingLatest(true)
    try {
      const res = await resumeAPI.getLatestResume()
      setLatestResume(res.data)
      if (res.data.extracted_skills) {
        setSkillsToReview(res.data.extracted_skills)
      }
    } catch (err) {
      // 404 is normal if no resume has been uploaded yet
      if (err.response?.status !== 404) {
        console.error('Failed to load latest resume:', err)
      }
    } finally {
      setLoadingLatest(false)
    }
  }

  useEffect(() => {
    fetchLatestResume()
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
      setParsingStage('Extracting text & running NLP skill extraction…')
      const res = await resumeAPI.uploadResume(formData)
      const data = res.data

      setSuccessMsg(`Resume "${data.filename}" successfully analyzed! Found ${data.extracted_skills_count} skills.`)
      setSkillsToReview(data.extracted_skills || [])
      fetchLatestResume()
    } catch (err) {
      console.error(err)
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
      category: 'Self-Reported',
      confidence: 1.0,
      evidence: 'Added manually during student review',
      proficiency: manualSkillLevel,
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
        })),
      }

      const res = await resumeAPI.confirmSkills(payload)
      setSuccessMsg(
        `✓ ${res.data.total_confirmed_skills} skills successfully confirmed and synchronized with your Career Profile!`
      )
      fetchLatestResume()
    } catch (err) {
      console.error(err)
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

  return (
    <div className="page-container">
      <div className="fade-up">
        {/* Header */}
        <div style={{ marginBottom: '2rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.5rem' }}>
            <h1 className="section-title" style={{ marginBottom: 0 }}>
              📄 Resume Intelligence
            </h1>
            <span className="badge badge-info">Phase 3</span>
          </div>
          <p className="section-subtitle" style={{ marginBottom: 0 }}>
            Upload your resume (PDF or DOCX). CareerGraph AI securely parses text, extracts skills with evidence and confidence scores, and lets you review before updating your profile.
          </p>
        </div>

        {/* Notifications */}
        {successMsg && (
          <div className="alert alert-success" style={{ marginBottom: '1.5rem' }}>
            {successMsg}
          </div>
        )}
        {errorMsg && (
          <div className="alert alert-error" style={{ marginBottom: '1.5rem' }}>
            ✗ {errorMsg}
          </div>
        )}

        {/* ── File Upload Section ─────────────────────────────────────────── */}
        <div
          onDragOver={(e) => e.preventDefault()}
          onDrop={handleDrop}
          className="card"
          style={{
            border: '2px dashed var(--color-border)',
            padding: '2.5rem 1.5rem',
            textAlign: 'center',
            marginBottom: '2rem',
            background: 'var(--color-bg-surface)',
            cursor: uploading ? 'not-allowed' : 'pointer',
            transition: 'border-color 0.2s',
          }}
          onClick={() => {
            if (!uploading && fileInputRef.current) fileInputRef.current.click()
          }}
        >
          <input
            ref={fileInputRef}
            type="file"
            accept=".pdf,.docx,.txt"
            style={{ display: 'none' }}
            onChange={(e) => {
              const file = e.target.files?.[0]
              if (file) handleFileUpload(file)
            }}
          />

          <div style={{ fontSize: '2.75rem', marginBottom: '0.75rem' }}>
            {uploading ? '⏳' : '📤'}
          </div>

          <h3 style={{ fontSize: '1.2rem', fontWeight: 700, marginBottom: '0.5rem' }}>
            {uploading ? parsingStage : 'Click or drag & drop your resume'}
          </h3>

          <p style={{ color: 'var(--color-text-secondary)', fontSize: '0.875rem', maxWidth: '460px', margin: '0 auto 1.25rem' }}>
            Accepts <strong>PDF</strong>, <strong>DOCX</strong>, or <strong>TXT</strong> (maximum 10 MB). Text is parsed locally and processed securely.
          </p>

          <button
            id="btn-upload-resume"
            type="button"
            className="btn btn-primary"
            disabled={uploading}
            onClick={(e) => {
              e.stopPropagation()
              if (fileInputRef.current) fileInputRef.current.click()
            }}
          >
            {uploading ? (
              <><span className="spinner" style={{ width: '16px', height: '16px' }} /> Analyzing Resume…</>
            ) : 'Select File From Computer'}
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
              <div style={{ fontSize: '1.75rem' }}>📎</div>
              <div>
                <div style={{ fontWeight: 700, fontSize: '0.95rem' }}>{latestResume.filename}</div>
                <div style={{ fontSize: '0.8rem', color: 'var(--color-text-secondary)' }}>
                  {(latestResume.file_size_bytes / 1024).toFixed(1)} KB • Uploaded {new Date(latestResume.created_at).toLocaleDateString()}
                </div>
              </div>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
              <span className={`badge ${latestResume.status === 'reviewed' ? 'badge-strong' : 'badge-medium'}`}>
                {latestResume.status === 'reviewed' ? '✓ Confirmed by Student' : '⏳ Awaiting Review'}
              </span>

              {latestResume.raw_text && (
                <button
                  type="button"
                  className="btn btn-secondary"
                  style={{ fontSize: '0.8rem', padding: '0.35rem 0.75rem' }}
                  onClick={() => setShowRawText(!showRawText)}
                >
                  {showRawText ? 'Hide Raw Text' : 'View Extracted Text'}
                </button>
              )}
            </div>
          </div>
        )}

        {/* Raw text collapsible preview */}
        {showRawText && latestResume?.raw_text && (
          <div className="card" style={{ marginBottom: '2rem', background: '#0a0d18' }}>
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
                  🔍 Extracted Skills Review ({skillsToReview.length})
                </h3>
                <p style={{ fontSize: '0.85rem', color: 'var(--color-text-secondary)' }}>
                  Review each skill, verify the extracted evidence snippet, adjust your proficiency level, or remove any false positives.
                </p>
              </div>

              {/* Confirm & Sync Action */}
              <button
                id="btn-confirm-skills"
                type="button"
                className="btn btn-primary"
                disabled={syncing}
                onClick={handleConfirmAndSync}
                style={{ padding: '0.625rem 1.5rem' }}
              >
                {syncing ? (
                  <><span className="spinner" style={{ width: '16px', height: '16px' }} /> Syncing to Profile…</>
                ) : '✓ Confirm & Sync Skills to Profile'}
              </button>
            </div>

            {/* Category Filter Chips */}
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem', marginBottom: '1.5rem' }}>
              {categories.map((cat) => (
                <button
                  key={cat}
                  type="button"
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
                const confPercent = Math.round(skill.confidence * 100)
                const confColor =
                  confPercent >= 90 ? 'var(--color-accent-green)' : confPercent >= 80 ? 'var(--color-brand-light)' : 'var(--color-accent-yellow)'

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

                        <span
                          className="badge"
                          style={{
                            background: `${confColor}18`,
                            color: confColor,
                            border: `1px solid ${confColor}40`,
                            fontSize: '0.725rem',
                          }}
                        >
                          {confPercent}% match
                        </span>
                      </div>

                      {/* Evidence quote */}
                      {skill.evidence && (
                        <div
                          style={{
                            fontSize: '0.78rem',
                            color: 'var(--color-text-secondary)',
                            background: 'rgba(0,0,0,0.25)',
                            padding: '0.5rem 0.625rem',
                            borderRadius: '6px',
                            borderLeft: `2px solid ${confColor}`,
                            fontStyle: 'italic',
                            lineHeight: 1.4,
                          }}
                        >
                          "{skill.evidence}"
                        </div>
                      )}
                    </div>

                    {/* Bottom controls: proficiency & remove */}
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', paddingTop: '0.5rem', borderTop: '1px solid rgba(255,255,255,0.05)' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                        <span style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)' }}>Proficiency:</span>
                        <select
                          className="input"
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
                        Remove ✗
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
              <input
                type="text"
                className="input"
                style={{ flex: 1, minWidth: '180px', height: '36px', padding: '0.4rem 0.75rem', fontSize: '0.85rem' }}
                placeholder="e.g. Next.js, Redis, PyTorch"
                value={manualSkillName}
                onChange={(e) => setManualSkillName(e.target.value)}
              />
              <select
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

        {/* Empty state if no resume uploaded yet */}
        {!latestResume && !loadingLatest && (
          <div className="card" style={{ textAlign: 'center', padding: '3rem 1.5rem' }}>
            <div style={{ fontSize: '2.5rem', marginBottom: '0.75rem' }}>📑</div>
            <h3 style={{ fontSize: '1.1rem', fontWeight: 700, marginBottom: '0.5rem' }}>
              No Resume Uploaded Yet
            </h3>
            <p style={{ color: 'var(--color-text-secondary)', fontSize: '0.875rem', maxWidth: '420px', margin: '0 auto 1.5rem' }}>
              Upload your engineering resume above to extract languages, frameworks, and tools backed by contextual evidence.
            </p>
          </div>
        )}
      </div>
    </div>
  )
}
