/**
 * VerificationPage — Phase 6: GitHub verification & LinkedIn link.
 *
 * Two levels of trust are shown explicitly and never blurred:
 *
 *   GitHub  — the account and its repositories are fetched live from GitHub's
 *             public API. Skills are *inferred* from repository languages and
 *             topics, carry a confidence score and repository evidence, and are
 *             only added to the profile after the student confirms them.
 *   LinkedIn — stored as a self-declared link and labelled "unverified", because
 *             LinkedIn has no public API for reading a member's profile.
 *
 * Every value on this page comes from the API; nothing is mocked.
 */

import { useState, useEffect, useCallback } from 'react'
import { useAuth } from '../hooks/useAuth'
import { verificationAPI, profileAPI, formatApiError } from '../services/api'

function proficiencyBadge(level) {
  if (level === 'advanced') return 'badge-strong'
  if (level === 'intermediate') return 'badge-info'
  return 'badge-medium'
}

export default function VerificationPage() {
  const { user } = useAuth()
  const isStudent = user?.role === 'student'

  const [status, setStatus] = useState(null)
  const [profileSkills, setProfileSkills] = useState([])
  const [username, setUsername] = useState('')
  const [linkedinUrl, setLinkedinUrl] = useState('')
  const [selectedSkills, setSelectedSkills] = useState([])
  const [loading, setLoading] = useState(true)
  const [working, setWorking] = useState(false)
  const [error, setError] = useState(null)
  const [notice, setNotice] = useState(null)

  const loadProfileSkills = useCallback(async () => {
    try {
      const res = await profileAPI.getMeProfile()
      setProfileSkills(res.data?.student_profile?.skills || [])
    } catch {
      // The profile is only used to mark skills that are already saved; a
      // failure here must not block the verification workflow.
    }
  }, [])

  useEffect(() => {
    if (!isStudent) return undefined
    let cancelled = false
    Promise.allSettled([verificationAPI.getStatus(), profileAPI.getMeProfile()]).then(
      ([statusResult, profileResult]) => {
        if (cancelled) return
        if (statusResult.status === 'fulfilled') {
          setStatus(statusResult.value.data)
          const savedUrl = statusResult.value.data?.linkedin?.linkedin_url
          if (savedUrl) setLinkedinUrl(savedUrl)
        } else {
          setError(formatApiError(statusResult.reason, 'Failed to load your verification status.'))
        }
        if (profileResult.status === 'fulfilled') {
          setProfileSkills(profileResult.value.data?.student_profile?.skills || [])
        }
        setLoading(false)
      }
    )
    return () => {
      cancelled = true
    }
  }, [isStudent])

  const handleVerify = async (event) => {
    event.preventDefault()
    const value = username.trim()
    if (!value) return
    setWorking(true)
    setError(null)
    setNotice(null)
    try {
      const res = await verificationAPI.verifyGithub(value)
      setStatus((prev) => ({ ...(prev || {}), github: res.data }))
      setSelectedSkills([])
      setUsername('')
      setNotice(
        `Verified github.com/${res.data.account.username}. ` +
          `${res.data.skills.length} skills were detected — review them below.`
      )
    } catch (err) {
      setError(formatApiError(err, 'Could not verify that GitHub account.'))
    } finally {
      setWorking(false)
    }
  }

  const handleConfirm = async () => {
    if (selectedSkills.length === 0) return
    setWorking(true)
    setError(null)
    setNotice(null)
    try {
      const res = await verificationAPI.confirmSkills(selectedSkills)
      setNotice(res.data.message)
      setSelectedSkills([])
      await loadProfileSkills()
    } catch (err) {
      setError(formatApiError(err, 'Failed to add those skills to your profile.'))
    } finally {
      setWorking(false)
    }
  }

  const handleUnlink = async () => {
    setWorking(true)
    setError(null)
    setNotice(null)
    try {
      const res = await verificationAPI.disconnectGithub()
      setStatus((prev) => ({ ...(prev || {}), github: null }))
      setNotice(res.data.message)
      await loadProfileSkills()
    } catch (err) {
      setError(formatApiError(err, 'Failed to unlink your GitHub account.'))
    } finally {
      setWorking(false)
    }
  }

  const handleLinkedin = async (event) => {
    event.preventDefault()
    const value = linkedinUrl.trim()
    if (!value) return
    setWorking(true)
    setError(null)
    setNotice(null)
    try {
      const res = await verificationAPI.saveLinkedin(value)
      setStatus((prev) => ({ ...(prev || {}), linkedin: res.data }))
      setLinkedinUrl(res.data.linkedin_url)
      setNotice('LinkedIn link saved as self-declared (unverified).')
    } catch (err) {
      setError(formatApiError(err, 'Could not save that LinkedIn URL.'))
    } finally {
      setWorking(false)
    }
  }

  const toggleSkill = (name) => {
    setSelectedSkills((prev) =>
      prev.includes(name) ? prev.filter((s) => s !== name) : [...prev, name]
    )
  }

  if (!isStudent) {
    return (
      <div className="page-container">
        <div className="card" data-testid="verification-student-only">
          <h1 className="section-title">🔗 Verification</h1>
          <p style={{ color: 'var(--color-text-secondary)' }}>
            GitHub verification is part of the student workflow. Alumni already
            showcase their GitHub and LinkedIn links on their mentor profile.
          </p>
        </div>
      </div>
    )
  }

  const github = status?.github
  const linkedin = status?.linkedin
  const profileSkillSources = new Map(
    profileSkills.map((skill) => [
      String(skill.name || '').toLowerCase(),
      skill.source || 'self',
    ])
  )

  return (
    <div className="page-container">
      <div className="fade-up">
        <h1 className="section-title">🔗 Verification</h1>
        <p className="section-subtitle">
          Connect real evidence to your profile. GitHub is fetched live; LinkedIn
          is stored as a self-declared link because it cannot be verified.
        </p>

        {loading && (
          <div className="card" style={{ display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
            <span className="spinner" /> Loading your verification status…
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

        {!loading && (
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(340px, 1fr))',
              gap: '1.5rem',
            }}
          >
            {/* ── GitHub ─────────────────────────────────────────────────── */}
            <div className="card" data-testid="github-panel">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem', gap: '0.75rem', flexWrap: 'wrap' }}>
                <h2 style={{ fontSize: '1.1rem', fontWeight: 700 }}>🐙 GitHub</h2>
                {github ? (
                  <span className="badge badge-strong">✓ Account verified</span>
                ) : (
                  <span className="badge badge-medium">Not linked</span>
                )}
              </div>

              {!github && (
                <p style={{ fontSize: '0.85rem', color: 'var(--color-text-secondary)', marginBottom: '1rem' }}>
                  Enter your GitHub username (or paste your profile URL). We read
                  your public profile and up to 100 of your most recently pushed
                  public repositories. Forks are excluded.
                </p>
              )}

              <form onSubmit={handleVerify} style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap', marginBottom: '1rem' }}>
                <label htmlFor="github-username" className="sr-only" style={{ position: 'absolute', width: 1, height: 1, overflow: 'hidden' }}>
                  GitHub username
                </label>
                <input
                  id="github-username"
                  type="text"
                  value={username}
                  onChange={(event) => setUsername(event.target.value)}
                  placeholder="octocat"
                  disabled={working}
                  style={{ flex: '1 1 180px', minWidth: '160px' }}
                />
                <button type="submit" className="btn btn-primary" disabled={working || !username.trim()}>
                  {github ? 'Re-verify' : 'Verify GitHub'}
                </button>
              </form>

              {github && (
                <div data-testid="github-account">
                  <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center', marginBottom: '0.75rem' }}>
                    {github.account.avatar_url && (
                      <img
                        src={github.account.avatar_url}
                        alt=""
                        width="44"
                        height="44"
                        style={{ borderRadius: '50%', border: '1px solid var(--color-border)' }}
                      />
                    )}
                    <div>
                      <div style={{ fontWeight: 700 }}>{github.account.name || github.account.username}</div>
                      <a
                        href={github.account.profile_url || `https://github.com/${github.account.username}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        style={{ fontSize: '0.82rem', color: 'var(--color-brand-light)' }}
                      >
                        @{github.account.username} ↗
                      </a>
                    </div>
                  </div>

                  {github.account.bio && (
                    <p style={{ fontSize: '0.85rem', color: 'var(--color-text-secondary)', marginBottom: '0.75rem' }}>
                      {github.account.bio}
                    </p>
                  )}

                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.4rem', marginBottom: '0.75rem' }}>
                    <span className="badge badge-info">{github.account.public_repos} public repos</span>
                    <span className="badge badge-info">{github.account.followers} followers</span>
                    <span className="badge badge-info">{github.total_stars} stars</span>
                    <span className="badge badge-medium">{github.repos_analyzed} analysed</span>
                    {github.forks_excluded > 0 && (
                      <span className="badge badge-medium">{github.forks_excluded} forks excluded</span>
                    )}
                  </div>

                  <p style={{ fontSize: '0.8rem', color: 'var(--color-text-secondary)', marginBottom: '0.75rem' }}>
                    {github.explanation}
                  </p>

                  {github.relevant_to_target?.length > 0 && (
                    <div className="alert alert-info" style={{ marginBottom: '0.75rem', fontSize: '0.82rem' }}>
                      Also required for your target role:{' '}
                      <strong>{github.relevant_to_target.join(', ')}</strong>
                    </div>
                  )}

                  <div style={{ fontSize: '0.88rem', fontWeight: 600, marginBottom: '0.5rem' }}>
                    Detected skills ({github.skills.length})
                  </div>

                  {github.skills.length === 0 ? (
                    <div className="alert alert-info">
                      No taxonomy skills could be inferred from the primary languages
                      and topics of your public repositories.
                    </div>
                  ) : (
                    <div data-testid="github-skills" style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                      {github.skills.map((skill) => {
                        const existingSource = profileSkillSources.get(skill.name.toLowerCase())
                        // GitHub or assessment evidence is stronger than what
                        // this verification would add, so those cannot be
                        // re-selected. A self-reported or resume skill can be
                        // upgraded to GitHub evidence.
                        const alreadyEvidenced =
                          existingSource === 'github' || existingSource === 'assessment'
                        return (
                          <label
                            key={skill.name}
                            data-testid={`github-skill-${skill.name}`}
                            style={{
                              display: 'block',
                              padding: '0.6rem 0.7rem',
                              background: 'var(--color-bg-elevated)',
                              border: '1px solid var(--color-border)',
                              borderRadius: '8px',
                              fontSize: '0.85rem',
                            }}
                          >
                            <span style={{ display: 'flex', gap: '0.5rem', alignItems: 'center', flexWrap: 'wrap' }}>
                              <input
                                type="checkbox"
                                checked={alreadyEvidenced || selectedSkills.includes(skill.name)}
                                disabled={working || alreadyEvidenced}
                                onChange={() => toggleSkill(skill.name)}
                              />
                              <strong>{skill.name}</strong>
                              <span className={`badge ${proficiencyBadge(skill.proficiency)}`}>
                                {skill.proficiency}
                              </span>
                              <span className="badge badge-info">
                                {Math.round(skill.confidence * 100)}% confidence
                              </span>
                              <span className="badge badge-medium">
                                {skill.repo_count} repo{skill.repo_count === 1 ? '' : 's'}
                              </span>
                              {alreadyEvidenced && (
                                <span className="badge badge-strong">On your profile</span>
                              )}
                              {!alreadyEvidenced && existingSource && (
                                <span className="badge badge-medium">
                                  On profile as {existingSource} — can upgrade
                                </span>
                              )}
                            </span>
                            <span style={{ display: 'block', marginTop: '0.3rem', color: 'var(--color-text-secondary)', fontSize: '0.78rem' }}>
                              {skill.evidence}
                            </span>
                          </label>
                        )
                      })}
                    </div>
                  )}

                  <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap', marginTop: '1rem' }}>
                    <button
                      type="button"
                      className="btn btn-primary"
                      onClick={handleConfirm}
                      disabled={working || selectedSkills.length === 0}
                    >
                      Add {selectedSkills.length} skill{selectedSkills.length === 1 ? '' : 's'} from GitHub
                    </button>
                    <button
                      type="button"
                      className="btn btn-secondary"
                      onClick={handleUnlink}
                      disabled={working}
                    >
                      Unlink GitHub
                    </button>
                  </div>

                  <p style={{ marginTop: '0.875rem', fontSize: '0.78rem', color: 'var(--color-text-muted)' }}>
                    {github.disclaimer}
                  </p>
                </div>
              )}
            </div>

            {/* ── LinkedIn ───────────────────────────────────────────────── */}
            <div className="card" data-testid="linkedin-panel">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem', gap: '0.75rem', flexWrap: 'wrap' }}>
                <h2 style={{ fontSize: '1.1rem', fontWeight: 700 }}>💼 LinkedIn</h2>
                {linkedin ? (
                  <span className="badge badge-medium" data-testid="linkedin-unverified">
                    Unverified — self-declared
                  </span>
                ) : (
                  <span className="badge badge-medium">Not added</span>
                )}
              </div>

              <p style={{ fontSize: '0.85rem', color: 'var(--color-text-secondary)', marginBottom: '0.75rem' }}>
                LinkedIn has no public API for reading a member&apos;s profile, so
                this link is stored as <strong>self-declared</strong> and is never
                presented as verified.
              </p>

              {linkedin && (
                <div style={{ marginBottom: '0.875rem' }} data-testid="linkedin-status">
                  <a
                    href={linkedin.linkedin_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    style={{ color: 'var(--color-brand-light)', fontSize: '0.88rem' }}
                  >
                    {linkedin.linkedin_url} ↗
                  </a>
                  <div style={{ fontSize: '0.78rem', color: 'var(--color-text-muted)', marginTop: '0.25rem' }}>
                    {linkedin.note}
                  </div>
                </div>
              )}

              <form onSubmit={handleLinkedin} style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
                <label htmlFor="linkedin-url" className="sr-only" style={{ position: 'absolute', width: 1, height: 1, overflow: 'hidden' }}>
                  LinkedIn profile URL
                </label>
                <input
                  id="linkedin-url"
                  type="url"
                  value={linkedinUrl}
                  onChange={(event) => setLinkedinUrl(event.target.value)}
                  placeholder="https://www.linkedin.com/in/your-name"
                  disabled={working}
                  style={{ flex: '1 1 220px', minWidth: '200px' }}
                />
                <button type="submit" className="btn btn-secondary" disabled={working || !linkedinUrl.trim()}>
                  Save link
                </button>
              </form>

              <div className="alert alert-info" style={{ marginTop: '1rem', fontSize: '0.8rem' }}>
                <strong>Why the difference?</strong> GitHub verification confirms the
                account and produces evidence from public repositories. A LinkedIn
                URL only tells readers where to find you.
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
