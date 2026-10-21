/**
 * DashboardPage — Career Intelligence & Profile Dashboard (Phase 2).
 *
 * Displays:
 *   - Current user status & profile strength
 *   - Target career orientation & timeline
 *   - Skill inventory breakdown
 *   - Live alumni mentor directory preview
 *   - API & database health telemetry
 *   - Career readiness, learning roadmap, assessments, GitHub verification & mentorship (Phases 4–6, 8)
 *   - Progressive development roadmap
 */

import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import { healthAPI, profileAPI, resumeAPI, careerAPI, roadmapAPI, assessmentAPI, mentorshipAPI, verificationAPI } from '../services/api'

export default function DashboardPage() {
  const { user } = useAuth()
  const isStudent = user?.role === 'student'
  const isAlumni = user?.role === 'alumni'

  const [health, setHealth] = useState(null)
  const [healthLoading, setHealthLoading] = useState(true)
  const [profileData, setProfileData] = useState(null)
  const [profileLoading, setProfileLoading] = useState(true)
  const [mentors, setMentors] = useState([])
  const [latestResume, setLatestResume] = useState(null)
  const [gap, setGap] = useState(null)
  const [roadmap, setRoadmap] = useState(null)
  const [assessments, setAssessments] = useState([])
  const [mentorshipRequests, setMentorshipRequests] = useState([])
  const [verification, setVerification] = useState(null)

  useEffect(() => {
    // 1. Check backend health
    healthAPI
      .check()
      .then((res) => setHealth(res.data))
      .catch(() => setHealth({ status: 'error', database: 'unreachable' }))
      .finally(() => setHealthLoading(false))

    // 2. Phase 8: mentorship is available to students (sent) and alumni (received).
    mentorshipAPI
      .listRequests()
      .then((res) => setMentorshipRequests(res.data))
      .catch(() => setMentorshipRequests([]))

    // 3. Fetch user profile
    profileAPI
      .getMeProfile()
      .then((res) => {
        setProfileData(res.data)
        // If student, also fetch available mentors & latest resume
        if (user?.role === 'student') {
          profileAPI.getAlumniMentors().then((mRes) => setMentors(mRes.data)).catch(() => {})
          resumeAPI.getLatestResume().then((rRes) => setLatestResume(rRes.data)).catch(() => {})
          // Phase 4: readiness for the saved target role (400 if none selected).
          careerAPI.getGapAnalysis().then((gRes) => setGap(gRes.data)).catch(() => setGap(null))
          // Phase 5: current roadmap (404 if not generated yet).
          roadmapAPI.getCurrent().then((rRes) => setRoadmap(rRes.data)).catch(() => setRoadmap(null))
          // Phase 8: assessment attempt history (student-only endpoint).
          assessmentAPI.history().then((aRes) => setAssessments(aRes.data)).catch(() => setAssessments([]))
          // Phase 6: GitHub verification & self-declared LinkedIn link.
          verificationAPI.getStatus().then((vRes) => setVerification(vRes.data)).catch(() => setVerification(null))
        }
      })
      .catch((err) => console.error('Failed to load profile:', err))
      .finally(() => setProfileLoading(false))
  }, [user])

  const completion = profileData?.completion_percentage ?? 0
  const studentProfile = profileData?.student_profile
  const alumniProfile = profileData?.alumni_profile
  const completedAssessments = assessments.filter((a) => a.status === 'completed')
  const latestAssessment = completedAssessments[0]
  const pendingRequests = mentorshipRequests.filter((r) => r.status === 'pending')
  const activeMentorships = mentorshipRequests.filter((r) => r.status === 'accepted')

  return (
    <div className="page-container">
      <div className="fade-up">
        {/* Welcome Header */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem', marginBottom: '2rem' }}>
          <div>
            <h1 className="section-title">
              Welcome, {user?.full_name?.split(' ')[0]} 👋
            </h1>
            <p className="section-subtitle" style={{ marginBottom: 0 }}>
              Phases 1–6 and Phase 8 are active: foundation, profiles, resume intelligence,
              skill-gap readiness, learning roadmaps, GitHub verification, skill assessments,
              and alumni mentoring.
            </p>
          </div>

          <Link to="/profile" className="btn btn-secondary" id="btn-edit-profile-quick">
            ✏️ Manage Profile
          </Link>
        </div>

        {/* Profile Completion Alert Banner if incomplete */}
        {completion < 75 && !profileLoading && (
          <div className="alert alert-info" style={{ marginBottom: '2rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
            <div>
              <strong>Profile is {completion}% complete:</strong>{' '}
              {isStudent
                ? 'Add your target career role, skills, and links so CareerGraph AI can compute your skill-gap readiness and build your roadmap.'
                : 'Set your industry company and mentoring availability to start connecting with students.'}
            </div>
            <Link to="/profile" className="btn btn-primary" style={{ padding: '0.4rem 1rem', fontSize: '0.85rem' }}>
              Complete Profile →
            </Link>
          </div>
        )}

        {/* ── Top Status Cards ──────────────────────────────────────────────── */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '1rem', marginBottom: '2rem' }}>
          
          {/* User Profile Card */}
          <div className="card">
            <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '1rem' }}>
              <div style={{
                width: '48px', height: '48px',
                background: 'linear-gradient(135deg, var(--color-brand-primary), var(--color-brand-light))',
                borderRadius: '50%',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                fontSize: '1.25rem', fontWeight: 700,
              }}>
                {user?.full_name?.[0]?.toUpperCase()}
              </div>
              <div>
                <div style={{ fontWeight: 700, fontSize: '1rem' }}>{user?.full_name}</div>
                <div style={{ fontSize: '0.8rem', color: 'var(--color-text-secondary)' }}>{user?.email}</div>
              </div>
            </div>

            <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap', marginBottom: '1rem' }}>
              <span className="badge badge-info" style={{ textTransform: 'capitalize' }}>{user?.role}</span>
              <span className="badge badge-strong">✓ Authenticated</span>
            </div>

            {/* Profile strength bar */}
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', marginBottom: '0.25rem' }}>
                <span style={{ color: 'var(--color-text-secondary)' }}>Profile Strength</span>
                <span style={{ fontWeight: 600, color: completion >= 75 ? 'var(--color-accent-green)' : 'var(--color-accent-yellow)' }}>
                  {completion}%
                </span>
              </div>
              <div className="progress-bar-track">
                <div
                  className="progress-bar-fill"
                  style={{
                    width: `${completion}%`,
                    background: completion >= 75
                      ? 'linear-gradient(90deg, #10b981, #34d399)'
                      : 'linear-gradient(90deg, var(--color-brand-primary), var(--color-brand-light))',
                  }}
                />
              </div>
            </div>
          </div>

          {/* Student Target Role or Alumni Status */}
          {isStudent && (
            <div className="card">
              <div style={{ fontWeight: 600, marginBottom: '0.75rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <span>🎯</span> Target Career
              </div>
              {studentProfile?.target_role ? (
                <div>
                  <div style={{ fontSize: '1.25rem', fontWeight: 700, color: 'var(--color-text-primary)', marginBottom: '0.375rem' }}>
                    {studentProfile.target_role}
                  </div>
                  <div style={{ fontSize: '0.85rem', color: 'var(--color-text-secondary)', marginBottom: '0.75rem' }}>
                    Target Window: <strong>{studentProfile.target_timeline_months || 6} months</strong>
                  </div>
                  <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
                    <span className="badge badge-info">
                      {studentProfile.degree || 'Degree unspecified'}
                    </span>
                    {studentProfile.graduation_year && (
                      <span className="badge badge-medium">Class of {studentProfile.graduation_year}</span>
                    )}
                  </div>
                </div>
              ) : (
                <div>
                  <p style={{ fontSize: '0.85rem', color: 'var(--color-text-muted)', marginBottom: '1rem' }}>
                    No target role selected yet. Choose a career track to begin.
                  </p>
                  <Link to="/profile" className="btn btn-secondary" style={{ fontSize: '0.8rem', padding: '0.35rem 0.75rem' }}>
                    + Select Target Role
                  </Link>
                </div>
              )}
            </div>
          )}

          {isAlumni && (
            <div className="card">
              <div style={{ fontWeight: 600, marginBottom: '0.75rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <span>💼</span> Mentorship Portfolio
              </div>
              {alumniProfile?.company ? (
                <div>
                  <div style={{ fontSize: '1.1rem', fontWeight: 700, marginBottom: '0.25rem' }}>
                    {alumniProfile.job_title}
                  </div>
                  <div style={{ fontSize: '0.85rem', color: 'var(--color-brand-light)', marginBottom: '0.75rem' }}>
                    @{alumniProfile.company} ({alumniProfile.years_of_experience || 0} yrs exp)
                  </div>
                  <span className={`badge ${alumniProfile.is_available_for_mentoring ? 'badge-strong' : 'badge-medium'}`}>
                    {alumniProfile.is_available_for_mentoring ? '✓ Open to Mentees' : '⏸ Paused'}
                  </span>
                </div>
              ) : (
                <div>
                  <p style={{ fontSize: '0.85rem', color: 'var(--color-text-muted)', marginBottom: '1rem' }}>
                    Add your company & expertise areas to mentor students.
                  </p>
                  <Link to="/profile" className="btn btn-secondary" style={{ fontSize: '0.8rem', padding: '0.35rem 0.75rem' }}>
                    Configure Mentor Profile
                  </Link>
                </div>
              )}
            </div>
          )}

          {/* Backend & DB Health Telemetry */}
          <div className="card">
            <div style={{ fontWeight: 600, marginBottom: '0.75rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <span>🔌</span> Platform Telemetry
            </div>
            {healthLoading ? (
              <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center', color: 'var(--color-text-secondary)' }}>
                <span className="spinner" /> Checking…
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                <StatusRow label="API Engine" value={health?.status === 'ok' ? '✓ Operational' : '✗ Error'} ok={health?.status === 'ok'} />
                <StatusRow label="Relational DB" value={health?.database === 'connected' ? '✓ Connected' : '✗ ' + health?.database} ok={health?.database === 'connected'} />
                <StatusRow label="Environment" value={health?.environment} ok={true} />
                <StatusRow label="Version" value={`v${health?.version}`} ok={true} />
              </div>
            )}
          </div>
        </div>

        {/* ── Skills & Mentor Section ────────────────────────────────────────── */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(340px, 1fr))', gap: '1.5rem', marginBottom: '2rem' }}>
          
          {/* Student Skills Overview */}
          {isStudent && (
            <div className="card">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                <h3 style={{ fontSize: '1.05rem', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <span>⚡</span> Self-Reported Skills ({studentProfile?.skills?.length || 0})
                </h3>
                <Link to="/profile" style={{ fontSize: '0.8rem', color: 'var(--color-brand-light)' }}>
                  + Edit Skills
                </Link>
              </div>

              {!studentProfile?.skills || studentProfile.skills.length === 0 ? (
                <div style={{ padding: '1.5rem', textAlign: 'center', background: 'var(--color-bg-elevated)', borderRadius: '8px' }}>
                  <p style={{ fontSize: '0.85rem', color: 'var(--color-text-muted)', marginBottom: '0.75rem' }}>
                    No skills documented yet.
                  </p>
                  <Link to="/profile" className="btn btn-secondary" style={{ fontSize: '0.8rem' }}>
                    Add Skills in Profile
                  </Link>
                </div>
              ) : (
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
                  {studentProfile.skills.map((s) => {
                    const badgeClass =
                      s.level === 'advanced' ? 'badge-strong' : s.level === 'intermediate' ? 'badge-info' : 'badge-medium'
                    return (
                      <span key={s.name} className={`badge ${badgeClass}`}>
                        {s.name} <span style={{ opacity: 0.75, fontSize: '0.7rem', marginLeft: '0.25rem' }}>• {s.level}</span>
                      </span>
                    )
                  })}
                </div>
              )}
            </div>
          )}

          {/* Alumni Expertise Overview */}
          {isAlumni && (
            <div className="card">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                <h3 style={{ fontSize: '1.05rem', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <span>💡</span> Mentorship Topics
                </h3>
                <Link to="/profile" style={{ fontSize: '0.8rem', color: 'var(--color-brand-light)' }}>
                  + Edit Topics
                </Link>
              </div>

              {!alumniProfile?.expertise_areas || alumniProfile.expertise_areas.length === 0 ? (
                <div style={{ padding: '1.5rem', textAlign: 'center', background: 'var(--color-bg-elevated)', borderRadius: '8px' }}>
                  <p style={{ fontSize: '0.85rem', color: 'var(--color-text-muted)' }}>
                    No topics added yet. Add topics to help students find you.
                  </p>
                </div>
              ) : (
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
                  {alumniProfile.expertise_areas.map((area) => (
                    <span key={area} className="badge badge-info">{area}</span>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Available Alumni Mentors (Preview for Students) */}
          {isStudent && (
            <div className="card">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                <h3 style={{ fontSize: '1.05rem', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <span>🤝</span> Alumni Mentor Directory
                </h3>
                <span className="badge badge-info">{mentors.length} available</span>
              </div>

              {mentors.length === 0 ? (
                <div style={{ padding: '1.5rem', textAlign: 'center', background: 'var(--color-bg-elevated)', borderRadius: '8px', color: 'var(--color-text-muted)', fontSize: '0.85rem' }}>
                  No active alumni mentors yet. Mentors registered on the platform will appear here.
                </div>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                  {mentors.slice(0, 3).map((m) => (
                    <div
                      key={m.user_id}
                      style={{
                        padding: '0.75rem',
                        background: 'var(--color-bg-elevated)',
                        borderRadius: '8px',
                        border: '1px solid var(--color-border)',
                      }}
                    >
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '0.25rem' }}>
                        <div style={{ fontWeight: 600, fontSize: '0.9rem' }}>{m.full_name}</div>
                        {m.meeting_link && (
                          <a
                            href={m.meeting_link}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="btn btn-primary"
                            style={{ fontSize: '0.75rem', padding: '0.2rem 0.6rem' }}
                          >
                            Connect ↗
                          </a>
                        )}
                      </div>
                      <div style={{ fontSize: '0.8rem', color: 'var(--color-text-secondary)', marginBottom: '0.5rem' }}>
                        {m.job_title} {m.company ? `@ ${m.company}` : ''}
                      </div>
                      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.25rem' }}>
                        {(m.expertise_areas || []).slice(0, 3).map((exp) => (
                          <span key={exp} className="badge badge-info" style={{ fontSize: '0.7rem', padding: '0.1rem 0.4rem' }}>
                            {exp}
                          </span>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Student Resume Intelligence Status Card */}
          {isStudent && (
            <div className="card">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                <h3 style={{ fontSize: '1.05rem', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <span>📄</span> Resume Intelligence
                </h3>
                <Link to="/resume" style={{ fontSize: '0.8rem', color: 'var(--color-brand-light)' }}>
                  {latestResume ? 'Review Skills →' : 'Upload Resume →'}
                </Link>
              </div>

              {latestResume ? (
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.75rem' }}>
                    <div style={{ fontSize: '1.5rem' }}>📑</div>
                    <div>
                      <div style={{ fontWeight: 600, fontSize: '0.9rem' }}>{latestResume.filename}</div>
                      <div style={{ fontSize: '0.75rem', color: 'var(--color-text-secondary)' }}>
                        {latestResume.extracted_skills?.length || 0} skills extracted • {latestResume.status === 'reviewed' ? '✓ Confirmed' : '⏳ Pending Review'}
                      </div>
                    </div>
                  </div>
                  <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
                    <Link to="/resume" className="btn btn-secondary" style={{ fontSize: '0.78rem', padding: '0.3rem 0.7rem' }}>
                      Review & Confirm Skills ↗
                    </Link>
                  </div>
                </div>
              ) : (
                <div style={{ padding: '1.25rem', textAlign: 'center', background: 'var(--color-bg-elevated)', borderRadius: '8px' }}>
                  <p style={{ fontSize: '0.85rem', color: 'var(--color-text-muted)', marginBottom: '0.75rem' }}>
                    No resume analyzed yet. Upload your PDF or DOCX to automatically extract verified skills.
                  </p>
                  <Link to="/resume" className="btn btn-primary" style={{ fontSize: '0.8rem', padding: '0.4rem 0.85rem' }}>
                    + Upload Resume
                  </Link>
                </div>
              )}
            </div>
          )}

          {/* Career Readiness Card (Phase 4) */}
          {isStudent && (
            <div className="card">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                <h3 style={{ fontSize: '1.05rem', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <span>🎯</span> Career Readiness
                </h3>
                <Link to="/career-gap" style={{ fontSize: '0.8rem', color: 'var(--color-brand-light)' }}>
                  {gap ? 'View gap analysis →' : 'Analyze →'}
                </Link>
              </div>

              {gap ? (
                <div>
                  <div style={{ display: 'flex', alignItems: 'baseline', gap: '0.5rem', marginBottom: '0.5rem' }}>
                    <span style={{ fontSize: '1.75rem', fontWeight: 800 }}>{gap.readiness_score}%</span>
                    <span className="badge badge-info">{gap.readiness_band}</span>
                  </div>
                  <div style={{ fontSize: '0.82rem', color: 'var(--color-text-secondary)', marginBottom: '0.75rem' }}>
                    {gap.occupation_name} • {gap.matched_count}/{gap.required_count} required skills covered
                  </div>
                  <div className="progress-bar-track">
                    <div className="progress-bar-fill" style={{ width: `${gap.readiness_score}%` }} />
                  </div>
                </div>
              ) : (
                <div style={{ padding: '1.25rem', textAlign: 'center', background: 'var(--color-bg-elevated)', borderRadius: '8px' }}>
                  <p style={{ fontSize: '0.85rem', color: 'var(--color-text-muted)', marginBottom: '0.75rem' }}>
                    {studentProfile?.target_role
                      ? 'Run a readiness analysis against your target role.'
                      : 'Select a target role to compute your readiness.'}
                  </p>
                  <Link to="/career-gap" className="btn btn-secondary" style={{ fontSize: '0.8rem' }}>
                    Open Skill Gap Analysis
                  </Link>
                </div>
              )}
            </div>
          )}

          {/* Learning Roadmap Card (Phase 5) */}
          {isStudent && (
            <div className="card">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                <h3 style={{ fontSize: '1.05rem', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <span>🗺️</span> Learning Roadmap
                </h3>
                <Link to="/roadmap" style={{ fontSize: '0.8rem', color: 'var(--color-brand-light)' }}>
                  {roadmap ? 'Open roadmap →' : 'Build →'}
                </Link>
              </div>

              {roadmap ? (
                <div>
                  <div style={{ display: 'flex', alignItems: 'baseline', gap: '0.5rem', marginBottom: '0.5rem' }}>
                    <span style={{ fontSize: '1.75rem', fontWeight: 800 }}>{roadmap.progress.percent_complete}%</span>
                    <span className="badge badge-info">
                      {roadmap.progress.completed_steps}/{roadmap.progress.total_steps} steps
                    </span>
                    {roadmap.is_partial && <span className="badge badge-medium">Partial</span>}
                  </div>
                  <div style={{ fontSize: '0.82rem', color: 'var(--color-text-secondary)', marginBottom: '0.5rem' }}>
                    {roadmap.occupation_name}
                  </div>
                  {roadmap.next_action && (
                    <div style={{ fontSize: '0.82rem', color: 'var(--color-brand-light)' }}>
                      Next: {roadmap.next_action}
                    </div>
                  )}
                </div>
              ) : (
                <div style={{ padding: '1.25rem', textAlign: 'center', background: 'var(--color-bg-elevated)', borderRadius: '8px' }}>
                  <p style={{ fontSize: '0.85rem', color: 'var(--color-text-muted)', marginBottom: '0.75rem' }}>
                    Generate a prerequisite-ordered plan for your target role.
                  </p>
                  <Link to="/roadmap" className="btn btn-secondary" style={{ fontSize: '0.8rem' }}>
                    Generate Roadmap
                  </Link>
                </div>
              )}
            </div>
          )}

          {/* Skill Assessments Card (Phase 8) */}
          {isStudent && (
            <div className="card">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                <h3 style={{ fontSize: '1.05rem', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <span>📝</span> Skill Assessments
                </h3>
                <Link to="/assessments" style={{ fontSize: '0.8rem', color: 'var(--color-brand-light)' }}>
                  {completedAssessments.length ? 'View all →' : 'Take one →'}
                </Link>
              </div>

              {latestAssessment ? (
                <div>
                  <div style={{ display: 'flex', alignItems: 'baseline', gap: '0.5rem', marginBottom: '0.5rem' }}>
                    <span style={{ fontSize: '1.75rem', fontWeight: 800 }}>{latestAssessment.score_percent}%</span>
                    <span className={`badge ${latestAssessment.passed ? 'badge-strong' : 'badge-medium'}`}>
                      {latestAssessment.passed ? 'Passed' : 'Not passed'}
                    </span>
                  </div>
                  <div style={{ fontSize: '0.82rem', color: 'var(--color-text-secondary)' }}>
                    {latestAssessment.assessment_name} • {completedAssessments.length} attempt
                    {completedAssessments.length === 1 ? '' : 's'} completed
                  </div>
                  {latestAssessment.passed_skills?.length > 0 && (
                    <div style={{ fontSize: '0.82rem', color: 'var(--color-brand-light)', marginTop: '0.4rem' }}>
                      Evidenced: {latestAssessment.passed_skills.join(', ')}
                    </div>
                  )}
                </div>
              ) : (
                <div style={{ padding: '1.25rem', textAlign: 'center', background: 'var(--color-bg-elevated)', borderRadius: '8px' }}>
                  <p style={{ fontSize: '0.85rem', color: 'var(--color-text-muted)', marginBottom: '0.75rem' }}>
                    Pass a short curated check to add a skill to your profile as verified evidence.
                  </p>
                  <Link to="/assessments" className="btn btn-secondary" style={{ fontSize: '0.8rem' }}>
                    Browse Assessments
                  </Link>
                </div>
              )}
            </div>
          )}

          {/* GitHub Verification Card (Phase 6) */}
          {isStudent && (
            <div className="card">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                <h3 style={{ fontSize: '1.05rem', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <span>🐙</span> GitHub Verification
                </h3>
                <Link to="/verification" style={{ fontSize: '0.8rem', color: 'var(--color-brand-light)' }}>
                  {verification?.github ? 'Review evidence →' : 'Verify →'}
                </Link>
              </div>

              {verification?.github ? (
                <div>
                  <div style={{ display: 'flex', alignItems: 'baseline', gap: '0.5rem', marginBottom: '0.4rem', flexWrap: 'wrap' }}>
                    <span style={{ fontSize: '1.05rem', fontWeight: 700 }}>
                      @{verification.github.account.username}
                    </span>
                    <span className="badge badge-strong">✓ Account verified</span>
                  </div>
                  <div style={{ fontSize: '0.82rem', color: 'var(--color-text-secondary)', marginBottom: '0.5rem' }}>
                    {verification.github.repos_analyzed} repositories analysed •{' '}
                    {verification.github.skills.length} skills detected
                  </div>
                  {verification.github.relevant_to_target?.length > 0 && (
                    <div style={{ fontSize: '0.82rem', color: 'var(--color-brand-light)' }}>
                      Matches your target role:{' '}
                      {verification.github.relevant_to_target.slice(0, 4).join(', ')}
                    </div>
                  )}
                </div>
              ) : (
                <div style={{ padding: '1.25rem', textAlign: 'center', background: 'var(--color-bg-elevated)', borderRadius: '8px' }}>
                  <p style={{ fontSize: '0.85rem', color: 'var(--color-text-muted)', marginBottom: '0.75rem' }}>
                    Verify your GitHub account to turn real repositories into evidence-backed skill suggestions.
                  </p>
                  <Link to="/verification" className="btn btn-secondary" style={{ fontSize: '0.8rem' }}>
                    Verify GitHub
                  </Link>
                </div>
              )}
            </div>
          )}

          {/* Mentorship Card (Phase 8) */}
          <div className="card">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
              <h3 style={{ fontSize: '1.05rem', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <span>🤝</span> {isStudent ? 'Mentorship' : 'Mentorship Requests'}
              </h3>
              <Link to="/mentors" style={{ fontSize: '0.8rem', color: 'var(--color-brand-light)' }}>
                {isStudent ? 'Find a mentor →' : 'Review requests →'}
              </Link>
            </div>

            {isStudent ? (
              <div style={{ fontSize: '0.85rem', color: 'var(--color-text-secondary)' }}>
                {activeMentorships.length > 0 && (
                  <div style={{ marginBottom: '0.35rem' }}>
                    {activeMentorships.length} accepted mentorship
                    {activeMentorships.length === 1 ? '' : 's'}:{' '}
                    {activeMentorships.map((r) => r.alumni_name || `Mentor #${r.alumni_id}`).join(', ')}
                  </div>
                )}
                <div>
                  {pendingRequests.length} pending request{pendingRequests.length === 1 ? '' : 's'} sent
                </div>
                {activeMentorships.length === 0 && pendingRequests.length === 0 && (
                  <p style={{ color: 'var(--color-text-muted)', marginTop: '0.5rem' }}>
                    Mentors are ranked against the skills you still need for your target role.
                  </p>
                )}
              </div>
            ) : (
              <div style={{ fontSize: '0.85rem', color: 'var(--color-text-secondary)' }}>
                {pendingRequests.length > 0 ? (
                  <div>
                    <strong>{pendingRequests.length}</strong> pending request
                    {pendingRequests.length === 1 ? '' : 's'} awaiting your decision.
                  </div>
                ) : (
                  <div style={{ color: 'var(--color-text-muted)' }}>
                    No pending requests right now.
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Development Roadmap Progress Card */}
          <div className="card">
            <div style={{ fontWeight: 600, marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <span>📋</span> CareerGraph Development Roadmap
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
              {[
                { n: 1, label: 'Foundation & Auth', done: true },
                { n: 2, label: 'User Profiles & Mentors', done: true },
                { n: 3, label: 'Resume Intelligence', done: true },
                { n: 4, label: 'Skill Gaps & Career Readiness', done: true },
                { n: 5, label: 'Skill Graph & Learning Roadmap', done: true },
                { n: 6, label: 'GitHub + LinkedIn Verification', done: true },
                { n: 7, label: 'RAG Knowledge Base (OpenRouter)', done: false },
                { n: 8, label: 'Assessments & Alumni Matching', done: true },
              ].map((p) => (
                <div key={p.n} style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.825rem' }}>
                  <span style={{
                    width: '18px', height: '18px', borderRadius: '50%', flexShrink: 0,
                    background: p.done ? 'var(--color-accent-green)' : p.active ? 'var(--color-brand-primary)' : 'var(--color-bg-elevated)',
                    border: p.done || p.active ? 'none' : '1px solid var(--color-border)',
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    fontSize: '10px', fontWeight: 700,
                  }}>
                    {p.done ? '✓' : p.n}
                  </span>
                  <span style={{
                    color: p.done ? 'var(--color-text-primary)' : p.active ? 'var(--color-brand-light)' : 'var(--color-text-muted)',
                    fontWeight: p.active ? 600 : 400,
                  }}>
                    Phase {p.n} — {p.label} {p.active ? '⏳ Next' : ''}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* System Alert Info */}
        <div className="alert alert-info">
          <strong>✓ Phases 1–6 and Phase 8 are live</strong> — authentication, profiles, resume
          intelligence (PDF/DOCX/TXT parsing with confidence &amp; evidence), deterministic
          skill-gap readiness, a prerequisite-aware learning roadmap backed by a curated
          skill-dependency graph, GitHub account verification with evidence-backed skill
          suggestions, a self-declared (unverified) LinkedIn link, curated skill assessments,
          and deterministic alumni matching with enforced mentorship capacity. Phase 7 (RAG
          knowledge base) is not implemented yet.
        </div>
      </div>
    </div>
  )
}

function StatusRow({ label, value, ok }) {
  return (
    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
      <span style={{ fontSize: '0.8rem', color: 'var(--color-text-secondary)' }}>{label}</span>
      <span style={{ fontSize: '0.8rem', fontWeight: 600, color: ok ? 'var(--color-accent-green)' : 'var(--color-accent-red)' }}>
        {value}
      </span>
    </div>
  )
}
