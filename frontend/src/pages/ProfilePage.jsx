/**
 * ProfilePage — student and alumni profile management.
 *
 * Loads the current profile and completion score, then exposes role-specific
 * forms: education, target role and skills for students; company, expertise,
 * capacity and availability for alumni. Saves go through the API and the
 * completion score is refreshed from the server response.
 */

import { useState, useEffect } from 'react'
import { useAuth } from '../hooks/useAuth'
import { profileAPI, formatApiError } from '../services/api'


const POPULAR_ROLES = [
  'Backend Developer',
  'Frontend Developer',
  'Full Stack Developer',
  'Data Analyst',
  'ML Engineer',
  'Cybersecurity Analyst',
  'Cloud / DevOps Engineer',
]

const POPULAR_SKILLS = [
  'Python', 'JavaScript', 'TypeScript', 'React', 'FastAPI',
  'SQL', 'PostgreSQL', 'Docker', 'Git', 'Linux', 'Pandas', 'Node.js',
]

const POPULAR_EXPERTISE = [
  'System Design', 'Backend Engineering', 'Cloud Architecture',
  'Resume Review', 'Interview Prep', 'Machine Learning', 'Career Guidance',
]

export default function ProfilePage() {
  const { user } = useAuth()
  const isStudent = user?.role === 'student'
  const isAlumni = user?.role === 'alumni'

  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [successMsg, setSuccessMsg] = useState(null)
  const [errorMsg, setErrorMsg] = useState(null)
  const [completion, setCompletion] = useState(0)

  // Student form state
  const [studentForm, setStudentForm] = useState({
    college: '',
    degree: '',
    current_year: '',
    graduation_year: '',
    cgpa: '',
    target_role: '',
    target_timeline_months: 6,
    bio: '',
    github_username: '',
    linkedin_url: '',
    portfolio_url: '',
    skills: [],
  })

  // Alumni form state
  const [alumniForm, setAlumniForm] = useState({
    company: '',
    job_title: '',
    years_of_experience: 1,
    college: '',
    graduation_year: '',
    expertise_areas: [],
    bio: '',
    linkedin_url: '',
    github_username: '',
    meeting_link: '',
    is_available_for_mentoring: true,
    max_mentees: 3,
  })

  // Skill input helper
  const [newSkillName, setNewSkillName] = useState('')
  const [newSkillLevel, setNewSkillLevel] = useState('intermediate')
  const [newExpertiseName, setNewExpertiseName] = useState('')


  const fetchProfile = async () => {
    try {
      const res = await profileAPI.getMeProfile()
      const data = res.data
      setCompletion(data.completion_percentage || 0)

      if (data.student_profile) {
        setStudentForm({
          college: data.student_profile.college || '',
          degree: data.student_profile.degree || '',
          current_year: data.student_profile.current_year || '',
          graduation_year: data.student_profile.graduation_year || '',
          cgpa: data.student_profile.cgpa || '',
          target_role: data.student_profile.target_role || '',
          target_timeline_months: data.student_profile.target_timeline_months || 6,
          bio: data.student_profile.bio || '',
          github_username: data.student_profile.github_username || '',
          linkedin_url: data.student_profile.linkedin_url || '',
          portfolio_url: data.student_profile.portfolio_url || '',
          skills: data.student_profile.skills || [],
        })
      }

      if (data.alumni_profile) {
        setAlumniForm({
          company: data.alumni_profile.company || '',
          job_title: data.alumni_profile.job_title || '',
          years_of_experience: data.alumni_profile.years_of_experience ?? 1,
          college: data.alumni_profile.college || '',
          graduation_year: data.alumni_profile.graduation_year || '',
          expertise_areas: data.alumni_profile.expertise_areas || [],
          bio: data.alumni_profile.bio || '',
          linkedin_url: data.alumni_profile.linkedin_url || '',
          github_username: data.alumni_profile.github_username || '',
          meeting_link: data.alumni_profile.meeting_link || '',
          is_available_for_mentoring: data.alumni_profile.is_available_for_mentoring ?? true,
          max_mentees: data.alumni_profile.max_mentees ?? 3,
        })
      }
    } catch (err) {
      setErrorMsg(formatApiError(err, 'Failed to load profile details.'))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    // Initial profile load; state updates occur after the request resolves.
    // oxlint-disable-next-line react/set-state-in-effect
    fetchProfile()
  }, [])


  const handleStudentChange = (e) => {
    const { name, value } = e.target
    setStudentForm((prev) => ({ ...prev, [name]: value }))
  }

  const handleAlumniChange = (e) => {
    const { name, value, type, checked } = e.target
    setAlumniForm((prev) => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value,
    }))
  }

  const handleAddSkill = (skillName, skillLevel = 'intermediate') => {
    const trimmed = (skillName || newSkillName).trim()
    if (!trimmed) return
    if (studentForm.skills.some((s) => s.name.toLowerCase() === trimmed.toLowerCase())) {
      setNewSkillName('')
      return
    }
    const updated = [...studentForm.skills, { name: trimmed, level: skillLevel }]
    setStudentForm((prev) => ({ ...prev, skills: updated }))
    setNewSkillName('')
  }

  const handleRemoveSkill = (name) => {
    setStudentForm((prev) => ({
      ...prev,
      skills: prev.skills.filter((s) => s.name.toLowerCase() !== name.toLowerCase()),
    }))
  }

  const handleAddExpertise = (areaName) => {
    const trimmed = (areaName || newExpertiseName).trim()
    if (!trimmed) return
    if (alumniForm.expertise_areas.some((a) => a.toLowerCase() === trimmed.toLowerCase())) {
      setNewExpertiseName('')
      return
    }
    const updated = [...alumniForm.expertise_areas, trimmed]
    setAlumniForm((prev) => ({ ...prev, expertise_areas: updated }))
    setNewExpertiseName('')
  }

  const handleRemoveExpertise = (area) => {
    setAlumniForm((prev) => ({
      ...prev,
      expertise_areas: prev.expertise_areas.filter((a) => a.toLowerCase() !== area.toLowerCase()),
    }))
  }

  const handleSaveStudent = async (e) => {
    e.preventDefault()
    setSaving(true)
    setSuccessMsg(null)
    setErrorMsg(null)
    try {
      const payload = {
        ...studentForm,
        current_year: studentForm.current_year ? parseInt(studentForm.current_year, 10) : null,
        graduation_year: studentForm.graduation_year ? parseInt(studentForm.graduation_year, 10) : null,
        cgpa: studentForm.cgpa ? parseFloat(studentForm.cgpa) : null,
        target_timeline_months: parseInt(studentForm.target_timeline_months, 10) || 6,
      }
      await profileAPI.updateStudentProfile(payload)
      setSuccessMsg('Student profile updated successfully!')
      fetchProfile()
    } catch (err) {
      setErrorMsg(formatApiError(err, 'Failed to save student profile.'))
    } finally {
      setSaving(false)
    }
  }

  const handleSaveAlumni = async (e) => {
    e.preventDefault()
    setSaving(true)
    setSuccessMsg(null)
    setErrorMsg(null)
    try {
      const payload = {
        ...alumniForm,
        years_of_experience: parseInt(alumniForm.years_of_experience, 10) || 0,
        graduation_year: alumniForm.graduation_year ? parseInt(alumniForm.graduation_year, 10) : null,
        max_mentees: parseInt(alumniForm.max_mentees, 10) || 3,
      }
      await profileAPI.updateAlumniProfile(payload)
      setSuccessMsg('Alumni mentor profile updated successfully!')
      fetchProfile()
    } catch (err) {
      setErrorMsg(formatApiError(err, 'Failed to save alumni profile.'))
    } finally {

      setSaving(false)
    }
  }

  if (loading) {
    return (
      <div className="page-container" style={{ textAlign: 'center', padding: '4rem 1rem' }}>
        <div className="spinner" style={{ margin: '0 auto 1rem' }} />
        <p style={{ color: 'var(--color-text-secondary)' }}>Loading your profile data…</p>
      </div>
    )
  }

  return (
    <div className="page-container">
      <div className="fade-up">
        {/* Header */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '1rem', marginBottom: '2rem' }}>
          <div>
            <h1 className="section-title">
              {isStudent ? 'Student career profile' : 'Alumni mentor profile'}
            </h1>
            <p className="section-subtitle" style={{ marginBottom: 0 }}>
              {isStudent
                ? 'Keep your target role and evidence current — every analysis and roadmap is built from this profile.'
                : 'Share your industry expertise and configure the mentoring capacity students can request.'}
            </p>
          </div>

          {/* Completion score indicator */}
          <div className="card" style={{ padding: '0.875rem 1.25rem', minWidth: '220px', background: 'var(--color-bg-surface)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem', marginBottom: '0.375rem' }}>
              <span style={{ color: 'var(--color-text-secondary)' }}>Profile strength</span>
              <span style={{ fontWeight: 700, color: completion >= 80 ? 'var(--color-accent-green)' : 'var(--color-accent-yellow)' }}>
                {completion}%
              </span>
            </div>
            <div
              className="progress-bar-track"
              role="progressbar"
              aria-valuenow={completion}
              aria-valuemin={0}
              aria-valuemax={100}
              aria-label="Profile strength"
            >
              <div
                className="progress-bar-fill"
                style={{
                  width: `${completion}%`,
                  background: completion >= 80
                    ? 'linear-gradient(90deg, #10b981, #34d399)'
                    : 'linear-gradient(90deg, var(--color-brand-primary), var(--color-brand-light))',
                }}
              />
            </div>
          </div>
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

        {/* ── Student Profile Form ────────────────────────────────────────── */}
        {isStudent && (
          <form onSubmit={handleSaveStudent}>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '1.5rem' }}>
              
              {/* Target Career Card */}
              <div className="card">
                <h3 style={{ fontSize: '1.1rem', fontWeight: 700, marginBottom: '0.5rem' }}>
                  Target career goal
                </h3>
                <p style={{ fontSize: '0.825rem', color: 'var(--color-text-secondary)', marginBottom: '1.25rem' }}>
                  The specific role you want to prepare for. We use this to calculate your skill gap.
                </p>

                <div style={{ marginBottom: '1.25rem' }}>
                  <label htmlFor="student-target-role" className="label">Target role</label>
                  <input
                    id="student-target-role"
                    name="target_role"
                    type="text"
                    className="input"
                    placeholder="e.g. Backend Developer"
                    value={studentForm.target_role}
                    onChange={handleStudentChange}
                    required
                  />
                  
                  {/* Role suggestion chips */}
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.375rem', marginTop: '0.75rem' }}>
                    {POPULAR_ROLES.map((r) => (
                      <button
                        key={r}
                        type="button"
                        aria-pressed={studentForm.target_role === r}
                        onClick={() => setStudentForm((prev) => ({ ...prev, target_role: r }))}
                        className="badge badge-info"
                        style={{
                          cursor: 'pointer',
                          background: studentForm.target_role === r ? 'var(--color-brand-primary)' : 'rgba(99,102,241,0.1)',
                          color: studentForm.target_role === r ? '#fff' : 'var(--color-brand-light)',
                          border: 'none',
                        }}
                      >
                        {r}
                      </button>
                    ))}
                  </div>
                </div>

                <div>
                  <label htmlFor="student-timeline" className="label">Target Timeline</label>
                  <select
                    id="student-timeline"
                    name="target_timeline_months"
                    className="input"
                    value={studentForm.target_timeline_months}
                    onChange={handleStudentChange}
                  >
                    <option value={3}>3 Months (Sprint preparation)</option>
                    <option value={6}>6 Months (Standard semester pace)</option>
                    <option value={12}>12 Months (Comprehensive 1-year roadmap)</option>
                    <option value={24}>24 Months (Early start / long term)</option>
                  </select>
                </div>
              </div>

              {/* Academic Background Card */}
              <div className="card">
                <h3 style={{ fontSize: '1.1rem', fontWeight: 700, marginBottom: '0.5rem' }}>
                  Academic background
                </h3>
                <p style={{ fontSize: '0.825rem', color: 'var(--color-text-secondary)', marginBottom: '1.25rem' }}>
                  Your university and current engineering standing.
                </p>

                <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                  <div>
                    <label htmlFor="student-college" className="label">College / University</label>
                    <input
                      id="student-college"
                      name="college"
                      type="text"
                      className="input"
                      placeholder="e.g. National Institute of Technology"
                      value={studentForm.college}
                      onChange={handleStudentChange}
                    />
                  </div>

                  <div>
                    <label htmlFor="student-degree" className="label">Degree & Branch</label>
                    <input
                      id="student-degree"
                      name="degree"
                      type="text"
                      className="input"
                      placeholder="e.g. B.Tech Computer Science"
                      value={studentForm.degree}
                      onChange={handleStudentChange}
                    />
                  </div>

                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))', gap: '0.75rem' }}>
                    <div>
                      <label htmlFor="student-current-year" className="label">Year of Study</label>
                      <select
                        id="student-current-year"
                        name="current_year"
                        className="input"
                        value={studentForm.current_year}
                        onChange={handleStudentChange}
                      >
                        <option value="">Select</option>
                        <option value={1}>1st Year</option>
                        <option value={2}>2nd Year</option>
                        <option value={3}>3rd Year</option>
                        <option value={4}>4th Year</option>
                      </select>
                    </div>

                    <div>
                      <label htmlFor="student-grad-year" className="label">Grad Year</label>
                      <input
                        id="student-grad-year"
                        name="graduation_year"
                        type="number"
                        min="2020"
                        max="2035"
                        className="input"
                        placeholder="2026"
                        value={studentForm.graduation_year}
                        onChange={handleStudentChange}
                      />
                    </div>

                    <div>
                      <label htmlFor="student-cgpa" className="label">CGPA</label>
                      <input
                        id="student-cgpa"
                        name="cgpa"
                        type="number"
                        step="0.01"
                        min="0"
                        max="10"
                        className="input"
                        placeholder="8.5"
                        value={studentForm.cgpa}
                        onChange={handleStudentChange}
                      />
                    </div>
                  </div>
                </div>
              </div>

              {/* Skill Inventory Card */}
              <div className="card" style={{ gridColumn: '1 / -1' }}>
                <h3 style={{ fontSize: '1.1rem', fontWeight: 700, marginBottom: '0.5rem' }}>
                  Current self-reported skills
                </h3>
                <p style={{ fontSize: '0.825rem', color: 'var(--color-text-secondary)', marginBottom: '1.25rem' }}>
                  List the technologies, tools, and languages you have worked with. Resume analysis
                  and GitHub verification can add evidence later; anything added here stays
                  self-reported.
                </p>

                {/* Add new skill inputs */}
                <div style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap', alignItems: 'flex-end', marginBottom: '1rem' }}>
                  <div style={{ flex: '2', minWidth: '180px' }}>
                    <label htmlFor="skill-name-input" className="label">Skill / Technology</label>
                    <input
                      id="skill-name-input"
                      type="text"
                      className="input"
                      placeholder="e.g. Python, Docker, React"
                      value={newSkillName}
                      onChange={(e) => setNewSkillName(e.target.value)}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter') {
                          e.preventDefault()
                          handleAddSkill()
                        }
                      }}
                    />
                  </div>

                  <div style={{ flex: '1', minWidth: '140px' }}>
                    <label htmlFor="skill-level-input" className="label">Proficiency Level</label>
                    <select
                      id="skill-level-input"
                      className="input"
                      value={newSkillLevel}
                      onChange={(e) => setNewSkillLevel(e.target.value)}
                    >
                      <option value="beginner">Beginner</option>
                      <option value="intermediate">Intermediate</option>
                      <option value="advanced">Advanced</option>
                    </select>
                  </div>

                  <button
                    id="btn-add-skill"
                    type="button"
                    onClick={() => handleAddSkill()}
                    className="btn btn-secondary"
                    style={{ height: '42px' }}
                  >
                    + Add Skill
                  </button>
                </div>

                {/* Popular suggestions */}
                <div style={{ marginBottom: '1.25rem' }}>
                  <span style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)', marginRight: '0.5rem' }}>Quick suggestions:</span>
                  <div style={{ display: 'inline-flex', flexWrap: 'wrap', gap: '0.375rem', marginTop: '0.375rem' }}>
                    {POPULAR_SKILLS.filter((s) => !studentForm.skills.some((item) => item.name.toLowerCase() === s.toLowerCase())).slice(0, 8).map((s) => (
                      <button
                        key={s}
                        type="button"
                        onClick={() => handleAddSkill(s, 'intermediate')}
                        style={{
                          background: 'var(--color-bg-elevated)',
                          border: '1px solid var(--color-border)',
                          borderRadius: '6px',
                          color: 'var(--color-text-secondary)',
                          fontSize: '0.75rem',
                          padding: '0.2rem 0.5rem',
                          cursor: 'pointer',
                        }}
                      >
                        + {s}
                      </button>
                    ))}
                  </div>
                </div>

                {/* Active skills list */}
                {studentForm.skills.length === 0 ? (
                  <div style={{ padding: '1.5rem', background: 'var(--color-bg-elevated)', borderRadius: '8px', textAlign: 'center', color: 'var(--color-text-muted)', fontSize: '0.875rem' }}>
                    No skills added yet. Add a few skills to boost your profile strength!
                  </div>
                ) : (
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
                    {studentForm.skills.map((s) => {
                      const badgeClass =
                        s.level === 'advanced' ? 'badge-strong' : s.level === 'intermediate' ? 'badge-info' : 'badge-medium'
                      return (
                        <div
                          key={s.name}
                          className={`badge ${badgeClass}`}
                          style={{
                            display: 'inline-flex',
                            alignItems: 'center',
                            gap: '0.5rem',
                            padding: '0.375rem 0.75rem',
                            fontSize: '0.85rem',
                          }}
                        >
                          <span>{s.name}</span>
                          <span style={{ fontSize: '0.7rem', opacity: 0.8, textTransform: 'capitalize' }}>
                            ({s.level})
                          </span>
                          <button
                            type="button"
                            onClick={() => handleRemoveSkill(s.name)}
                            aria-label={`Remove ${s.name}`}
                            style={{
                              background: 'transparent',
                              border: 'none',
                              color: 'inherit',
                              cursor: 'pointer',
                              fontWeight: 700,
                              marginLeft: '0.25rem',
                            }}
                          >
                            ×
                          </button>
                        </div>
                      )
                    })}
                  </div>
                )}
              </div>

              {/* Profiles & External Links Card */}
              <div className="card" style={{ gridColumn: '1 / -1' }}>
                <h3 style={{ fontSize: '1.1rem', fontWeight: 700, marginBottom: '0.5rem' }}>
                  Links &amp; bio
                </h3>
                <p style={{ fontSize: '0.825rem', color: 'var(--color-text-secondary)', marginBottom: '1.25rem' }}>
                  GitHub can be verified from the public API on the Verification page. LinkedIn and
                  portfolio links remain self-declared.
                </p>

                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '1rem', marginBottom: '1.25rem' }}>
                  <div>
                    <label htmlFor="student-github" className="label">GitHub Username</label>
                    <input
                      id="student-github"
                      name="github_username"
                      type="text"
                      className="input"
                      placeholder="octocat"
                      value={studentForm.github_username}
                      onChange={handleStudentChange}
                    />
                  </div>

                  <div>
                    <label htmlFor="student-linkedin" className="label">LinkedIn URL</label>
                    <input
                      id="student-linkedin"
                      name="linkedin_url"
                      type="url"
                      className="input"
                      placeholder="https://linkedin.com/in/username"
                      value={studentForm.linkedin_url}
                      onChange={handleStudentChange}
                    />
                  </div>

                  <div>
                    <label htmlFor="student-portfolio" className="label">Portfolio / Personal Website</label>
                    <input
                      id="student-portfolio"
                      name="portfolio_url"
                      type="url"
                      className="input"
                      placeholder="https://aaravsharma.dev"
                      value={studentForm.portfolio_url}
                      onChange={handleStudentChange}
                    />
                  </div>
                </div>

                <div>
                  <label htmlFor="student-bio" className="label">Bio / Career Pitch</label>
                  <textarea
                    id="student-bio"
                    name="bio"
                    className="input"
                    rows={3}
                    placeholder="Short summary of your engineering interests, current goals, and what roles you are pursuing."
                    value={studentForm.bio}
                    onChange={handleStudentChange}
                  />
                </div>
              </div>
            </div>

            {/* Submit button */}
            <div style={{ marginTop: '2rem', display: 'flex', justifyContent: 'flex-end', gap: '1rem' }}>
              <button
                id="btn-save-student-profile"
                type="submit"
                className="btn btn-primary"
                disabled={saving}
                style={{ padding: '0.75rem 2rem', fontSize: '1rem' }}
              >
                {saving ? (
                  <><span className="spinner" style={{ width: '16px', height: '16px' }} /> Saving profile…</>
                ) : 'Save student profile'}
              </button>
            </div>
          </form>
        )}

        {/* ── Alumni Profile Form ─────────────────────────────────────────── */}
        {isAlumni && (
          <form onSubmit={handleSaveAlumni}>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '1.5rem' }}>
              
              {/* Professional Experience */}
              <div className="card">
                <h3 style={{ fontSize: '1.1rem', fontWeight: 700, marginBottom: '0.5rem' }}>
                  Professional experience
                </h3>
                <p style={{ fontSize: '0.825rem', color: 'var(--color-text-secondary)', marginBottom: '1.25rem' }}>
                  Your current corporate role and industry background.
                </p>

                <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                  <div>
                    <label htmlFor="alumni-company" className="label">Company / Organization *</label>
                    <input
                      id="alumni-company"
                      name="company"
                      type="text"
                      className="input"
                      placeholder="e.g. Google, Microsoft, Stripe"
                      value={alumniForm.company}
                      onChange={handleAlumniChange}
                      required
                    />
                  </div>

                  <div>
                    <label htmlFor="alumni-job-title" className="label">Job Title / Role *</label>
                    <input
                      id="alumni-job-title"
                      name="job_title"
                      type="text"
                      className="input"
                      placeholder="e.g. Senior Software Engineer"
                      value={alumniForm.job_title}
                      onChange={handleAlumniChange}
                      required
                    />
                  </div>

                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))', gap: '0.75rem' }}>
                    <div>
                      <label htmlFor="alumni-experience" className="label">Years of Experience</label>
                      <input
                        id="alumni-experience"
                        name="years_of_experience"
                        type="number"
                        min="0"
                        max="50"
                        className="input"
                        placeholder="5"
                        value={alumniForm.years_of_experience}
                        onChange={handleAlumniChange}
                      />
                    </div>

                    <div>
                      <label htmlFor="alumni-grad-year" className="label">Graduation Year</label>
                      <input
                        id="alumni-grad-year"
                        name="graduation_year"
                        type="number"
                        min="1970"
                        max="2030"
                        className="input"
                        placeholder="2019"
                        value={alumniForm.graduation_year}
                        onChange={handleAlumniChange}
                      />
                    </div>
                  </div>

                  <div>
                    <label htmlFor="alumni-college" className="label">Alma Mater</label>
                    <input
                      id="alumni-college"
                      name="college"
                      type="text"
                      className="input"
                      placeholder="e.g. National Institute of Technology"
                      value={alumniForm.college}
                      onChange={handleAlumniChange}
                    />
                  </div>
                </div>
              </div>

              {/* Mentorship Settings */}
              <div className="card">
                <h3 style={{ fontSize: '1.1rem', fontWeight: 700, marginBottom: '0.5rem' }}>
                  Mentorship settings
                </h3>
                <p style={{ fontSize: '0.825rem', color: 'var(--color-text-secondary)', marginBottom: '1.25rem' }}>
                  Configure your availability to mentor engineering students.
                </p>

                <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                  {/* Availability toggle */}
                  <div style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    padding: '0.75rem 1rem',
                    background: 'var(--color-bg-elevated)',
                    borderRadius: '8px',
                    border: '1px solid var(--color-border)',
                  }}>
                    <div>
                      <label
                        htmlFor="alumni-available-toggle"
                        style={{ cursor: 'pointer', display: 'block' }}
                      >
                        <div style={{ fontWeight: 600, fontSize: '0.9rem' }}>Open to mentoring</div>
                        <div style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)' }}>
                          Allows students to discover you in the mentor directory
                        </div>
                      </label>
                    </div>
                    <input
                      id="alumni-available-toggle"
                      name="is_available_for_mentoring"
                      type="checkbox"
                      checked={alumniForm.is_available_for_mentoring}
                      onChange={handleAlumniChange}
                      style={{ width: '20px', height: '20px', accentColor: 'var(--color-brand-primary)', cursor: 'pointer' }}
                    />
                  </div>

                  <div>
                    <label htmlFor="alumni-max-mentees" className="label">Max Mentees / Month</label>
                    <input
                      id="alumni-max-mentees"
                      name="max_mentees"
                      type="number"
                      min="1"
                      max="20"
                      className="input"
                      value={alumniForm.max_mentees}
                      onChange={handleAlumniChange}
                    />
                  </div>

                  <div>
                    <label htmlFor="alumni-meeting-link" className="label">Meeting / Calendar Booking Link</label>
                    <input
                      id="alumni-meeting-link"
                      name="meeting_link"
                      type="url"
                      className="input"
                      placeholder="e.g. https://cal.com/your-name or Google Meet"
                      value={alumniForm.meeting_link}
                      onChange={handleAlumniChange}
                    />
                  </div>
                </div>
              </div>

              {/* Mentorship Expertise Areas */}
              <div className="card" style={{ gridColumn: '1 / -1' }}>
                <h3 style={{ fontSize: '1.1rem', fontWeight: 700, marginBottom: '0.5rem' }}>
                  Mentorship topics &amp; expertise
                </h3>
                <p style={{ fontSize: '0.825rem', color: 'var(--color-text-secondary)', marginBottom: '1.25rem' }}>
                  Areas where you can review portfolios, conduct mock interviews, or guide roadmap execution.
                </p>

                <div style={{ display: 'flex', gap: '0.75rem', marginBottom: '1rem', flexWrap: 'wrap' }}>
                  <div style={{ flex: '1', minWidth: '220px' }}>
                    <label htmlFor="expertise-input" className="sr-only">Expertise topic</label>
                    <input
                      id="expertise-input"
                      type="text"
                      className="input"
                      placeholder="Add an expertise topic (e.g. System Design, Resume Review)"
                      value={newExpertiseName}
                      onChange={(e) => setNewExpertiseName(e.target.value)}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter') {
                          e.preventDefault()
                          handleAddExpertise()
                        }
                      }}
                    />
                  </div>
                  <button
                    id="btn-add-expertise"
                    type="button"
                    onClick={() => handleAddExpertise()}
                    className="btn btn-secondary"
                  >
                    + Add Topic
                  </button>
                </div>

                {/* Popular suggestions */}
                <div style={{ marginBottom: '1.25rem' }}>
                  <span style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)', marginRight: '0.5rem' }}>Suggested topics:</span>
                  <div style={{ display: 'inline-flex', flexWrap: 'wrap', gap: '0.375rem', marginTop: '0.375rem' }}>
                    {POPULAR_EXPERTISE.filter((t) => !alumniForm.expertise_areas.some((a) => a.toLowerCase() === t.toLowerCase())).map((t) => (
                      <button
                        key={t}
                        type="button"
                        onClick={() => handleAddExpertise(t)}
                        style={{
                          background: 'var(--color-bg-elevated)',
                          border: '1px solid var(--color-border)',
                          borderRadius: '6px',
                          color: 'var(--color-text-secondary)',
                          fontSize: '0.75rem',
                          padding: '0.2rem 0.5rem',
                          cursor: 'pointer',
                        }}
                      >
                        + {t}
                      </button>
                    ))}
                  </div>
                </div>

                {/* Active topics */}
                {alumniForm.expertise_areas.length === 0 ? (
                  <div style={{ padding: '1.5rem', background: 'var(--color-bg-elevated)', borderRadius: '8px', textAlign: 'center', color: 'var(--color-text-muted)', fontSize: '0.875rem' }}>
                    No expertise topics added yet. Add a few topics so students can find you!
                  </div>
                ) : (
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
                    {alumniForm.expertise_areas.map((area) => (
                      <div
                        key={area}
                        className="badge badge-info"
                        style={{
                          display: 'inline-flex',
                          alignItems: 'center',
                          gap: '0.5rem',
                          padding: '0.375rem 0.75rem',
                          fontSize: '0.85rem',
                        }}
                      >
                        <span>{area}</span>
                        <button
                          type="button"
                          onClick={() => handleRemoveExpertise(area)}
                          aria-label={`Remove ${area}`}
                          style={{
                            background: 'transparent',
                            border: 'none',
                            color: 'inherit',
                            cursor: 'pointer',
                            fontWeight: 700,
                            marginLeft: '0.25rem',
                          }}
                        >
                          ×
                        </button>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Bio & Social Links */}
              <div className="card" style={{ gridColumn: '1 / -1' }}>
                <h3 style={{ fontSize: '1.1rem', fontWeight: 700, marginBottom: '0.5rem' }}>
                  Professional links &amp; bio
                </h3>

                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '1rem', marginBottom: '1.25rem' }}>
                  <div>
                    <label htmlFor="alumni-linkedin" className="label">LinkedIn Profile URL</label>
                    <input
                      id="alumni-linkedin"
                      name="linkedin_url"
                      type="url"
                      className="input"
                      placeholder="https://linkedin.com/in/username"
                      value={alumniForm.linkedin_url}
                      onChange={handleAlumniChange}
                    />
                  </div>

                  <div>
                    <label htmlFor="alumni-github" className="label">GitHub Username</label>
                    <input
                      id="alumni-github"
                      name="github_username"
                      type="text"
                      className="input"
                      placeholder="e.g. octocat"
                      value={alumniForm.github_username}
                      onChange={handleAlumniChange}
                    />
                  </div>
                </div>

                <div>
                  <label htmlFor="alumni-bio" className="label">Mentor Bio</label>
                  <textarea
                    id="alumni-bio"
                    name="bio"
                    className="input"
                    rows={3}
                    placeholder="Tell students about your journey, engineering domains, and how you can support their growth."
                    value={alumniForm.bio}
                    onChange={handleAlumniChange}
                  />
                </div>
              </div>
            </div>

            {/* Submit button */}
            <div style={{ marginTop: '2rem', display: 'flex', justifyContent: 'flex-end', gap: '1rem' }}>
              <button
                id="btn-save-alumni-profile"
                type="submit"
                className="btn btn-primary"
                disabled={saving}
                style={{ padding: '0.75rem 2rem', fontSize: '1rem' }}
              >
                {saving ? (
                  <><span className="spinner" style={{ width: '16px', height: '16px' }} /> Saving profile…</>
                ) : 'Save alumni profile'}
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  )
}
