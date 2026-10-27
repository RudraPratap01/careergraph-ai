/**
 * Dashboard cards — presentational building blocks for DashboardPage.
 *
 * Every value rendered here comes from the API payloads passed in as props.
 * Keeping the cards free of fetching logic makes them easy to reason about and
 * lets the page compose them by role without duplicated header markup.
 */

import { Link } from 'react-router-dom'
import DashboardCard from '../DashboardCard'
import EmptyState from '../EmptyState'
import Icon from '../Icon'

const LEVEL_BADGE = {
  advanced: 'badge-strong',
  intermediate: 'badge-info',
  beginner: 'badge-medium',
}

export function ProfileStrengthCard({ user, completion }) {
  const healthy = completion >= 75
  return (
    <DashboardCard icon={<Icon name="users" size={16} />} title="Your profile">
      <div className="row" style={{ gap: '0.85rem', marginBottom: '1rem' }}>
        <div
          className="nav-avatar"
          style={{ width: 46, height: 46, fontSize: '1.05rem' }}
          aria-hidden="true"
        >
          {user?.full_name?.[0]?.toUpperCase() || '?'}
        </div>
        <div style={{ minWidth: 0 }}>
          <div style={{ fontWeight: 700, fontSize: '0.98rem' }}>{user?.full_name}</div>
          <div className="small muted" style={{ overflow: 'hidden', textOverflow: 'ellipsis' }}>
            {user?.email}
          </div>
        </div>
      </div>

      <div className="row" style={{ gap: '0.4rem', marginBottom: '1rem' }}>
        <span className="badge badge-info" style={{ textTransform: 'capitalize' }}>{user?.role}</span>
        <span className="badge badge-strong"><Icon name="check" size={11} /> Signed in</span>
      </div>

      <div className="spread small" style={{ marginBottom: '0.35rem' }}>
        <span className="muted">Profile strength</span>
        <span style={{ fontWeight: 700, color: healthy ? 'var(--color-accent-green)' : 'var(--color-accent-yellow)' }}>
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
        <div className="progress-bar-fill" style={{ width: `${completion}%` }} />
      </div>
    </DashboardCard>
  )
}

export function TargetCareerCard({ profile }) {
  return (
    <DashboardCard
      icon={<Icon name="target" size={16} />}
      title="Target career"
      action={<Link to="/profile" className="card-action">Edit</Link>}
    >
      {profile?.target_role ? (
        <div>
          <div style={{ fontSize: '1.2rem', fontWeight: 700, marginBottom: '0.3rem' }}>
            {profile.target_role}
          </div>
          <p className="small muted" style={{ marginBottom: '0.75rem' }}>
            Target window: <strong>{profile.target_timeline_months || 6} months</strong>
          </p>
          <div className="row" style={{ gap: '0.4rem' }}>
            <span className="badge badge-info">{profile.degree || 'Degree unspecified'}</span>
            {profile.graduation_year && (
              <span className="badge badge-medium">Class of {profile.graduation_year}</span>
            )}
          </div>
        </div>
      ) : (
        <EmptyState
          icon={<Icon name="target" size={18} />}
          title="No target role yet"
          action={<Link to="/profile" className="btn btn-secondary btn-sm">Choose a role</Link>}
        >
          Pick the role you are preparing for so readiness and roadmaps have a reference point.
        </EmptyState>
      )}
    </DashboardCard>
  )
}

export function AlumniPortfolioCard({ profile }) {
  return (
    <DashboardCard
      icon={<Icon name="briefcase" size={16} />}
      title="Mentorship portfolio"
      action={<Link to="/profile" className="card-action">Edit</Link>}
    >
      {profile?.company ? (
        <div>
          <div style={{ fontSize: '1.1rem', fontWeight: 700, marginBottom: '0.2rem' }}>
            {profile.job_title}
          </div>
          <p className="small" style={{ color: 'var(--color-brand-light)', marginBottom: '0.75rem' }}>
            {profile.company} · {profile.years_of_experience || 0} yrs experience
          </p>
          <span className={`badge ${profile.is_available_for_mentoring ? 'badge-strong' : 'badge-medium'}`}>
            {profile.is_available_for_mentoring ? 'Open to mentees' : 'Paused'}
          </span>
        </div>
      ) : (
        <EmptyState
          icon={<Icon name="briefcase" size={18} />}
          title="Portfolio not configured"
          action={<Link to="/profile" className="btn btn-secondary btn-sm">Configure profile</Link>}
        >
          Add your company, role and expertise so students can find the right mentor.
        </EmptyState>
      )}
    </DashboardCard>
  )
}

export function TelemetryCard({ health, loading }) {
  const rows = health
    ? [
        { label: 'API engine', value: health.status === 'ok' ? 'Operational' : 'Error', ok: health.status === 'ok' },
        { label: 'Relational DB', value: health.database === 'connected' ? 'Connected' : health.database, ok: health.database === 'connected' },
        { label: 'Environment', value: health.environment || 'unknown', ok: true },
        { label: 'Version', value: `v${health.version}`, ok: true },
      ]
    : []

  return (
    <DashboardCard icon={<Icon name="chart" size={16} />} title="Platform status">
      {loading ? (
        <div className="row" role="status" style={{ color: 'var(--color-text-secondary)' }}>
          <span className="spinner" style={{ width: 16, height: 16 }} /> Checking services…
        </div>
      ) : rows.length === 0 ? (
        <p className="small muted">
          Telemetry is unavailable. The app can still work if the API recovers — reload to retry.
        </p>
      ) : (
        <dl className="stack" style={{ gap: '0.5rem' }}>
          {rows.map((row) => (
            <div key={row.label} className="spread">
              <dt className="small muted">{row.label}</dt>
              <dd
                className="small"
                style={{
                  fontWeight: 600,
                  color: row.ok ? 'var(--color-accent-green)' : 'var(--color-accent-red)',
                }}
              >
                {row.value}
              </dd>
            </div>
          ))}
        </dl>
      )}
    </DashboardCard>
  )
}

export function ExpertiseCard({ areas }) {
  return (
    <DashboardCard
      icon={<Icon name="spark" size={16} />}
      title="Mentorship topics"
      action={<Link to="/profile" className="card-action">Edit topics</Link>}
    >
      {!areas || areas.length === 0 ? (
        <EmptyState
          icon={<Icon name="spark" size={18} />}
          title="No topics added yet"
          action={<Link to="/profile" className="btn btn-secondary btn-sm">Add topics</Link>}
        >
          Add the areas you can advise on so students with matching gaps can find you.
        </EmptyState>
      ) : (
        <div className="row" style={{ gap: '0.45rem' }}>
          {areas.map((area) => (
            <span key={area} className="badge badge-info">{area}</span>
          ))}
        </div>
      )}
    </DashboardCard>
  )
}

export function SkillsCard({ skills }) {
  return (
    <DashboardCard
      icon={<Icon name="spark" size={16} />}
      title={`Skills (${skills?.length || 0})`}
      action={<Link to="/profile" className="card-action">Edit skills</Link>}
    >
      {!skills || skills.length === 0 ? (
        <EmptyState
          icon={<Icon name="spark" size={18} />}
          title="No skills recorded yet"
          action={<Link to="/profile" className="btn btn-secondary btn-sm">Add skills</Link>}
        >
          Add skills manually, or extract them from a resume and confirm what is accurate.
        </EmptyState>
      ) : (
        <div className="row" style={{ gap: '0.45rem' }}>
          {skills.map((skill) => (
            <span key={skill.name} className={`badge ${LEVEL_BADGE[skill.level] || 'badge-neutral'}`}>
              {skill.name}
              <span style={{ opacity: 0.7, fontSize: '0.68rem' }}>· {skill.level}</span>
            </span>
          ))}
        </div>
      )}
    </DashboardCard>
  )
}

export function MentorPreviewCard({ mentors }) {
  return (
    <DashboardCard
      icon={<Icon name="users" size={16} />}
      title="Alumni mentors"
      action={<Link to="/mentors" className="card-action">See matches</Link>}
    >
      {mentors.length === 0 ? (
        <EmptyState
          icon={<Icon name="users" size={18} />}
          title="No mentors available yet"
        >
          Alumni who opt into mentoring will appear here.
        </EmptyState>
      ) : (
        <div className="stack">
          {mentors.slice(0, 3).map((mentor) => (
            <div key={mentor.user_id} className="surface-muted">
              <div className="spread" style={{ marginBottom: '0.15rem' }}>
                <strong className="small">{mentor.full_name}</strong>
                {mentor.meeting_link && (
                  <a
                    href={mentor.meeting_link}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="btn btn-secondary btn-sm"
                  >
                    Connect <Icon name="external" size={13} />
                  </a>
                )}
              </div>
              <p className="tiny muted" style={{ marginBottom: '0.45rem' }}>
                {mentor.job_title}{mentor.company ? ` · ${mentor.company}` : ''}
              </p>
              <div className="row" style={{ gap: '0.3rem' }}>
                {(mentor.expertise_areas || []).slice(0, 3).map((area) => (
                  <span key={area} className="badge badge-info" style={{ fontSize: '0.68rem' }}>{area}</span>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}
    </DashboardCard>
  )
}

export function ResumeCard({ resume }) {
  return (
    <DashboardCard
      icon={<Icon name="file" size={16} />}
      title="Resume evidence"
      action={
        <Link to="/resume" className="card-action">
          {resume ? 'Review skills' : 'Upload'}
        </Link>
      }
    >
      {resume ? (
        <div>
          <div className="row" style={{ gap: '0.6rem', marginBottom: '0.7rem' }}>
            <span className="empty-state-icon" style={{ width: 36, height: 36 }} aria-hidden="true">
              <Icon name="file" size={16} />
            </span>
            <div style={{ minWidth: 0 }}>
              <div className="small" style={{ fontWeight: 600 }}>{resume.filename}</div>
              <div className="tiny muted">
                {resume.extracted_skills?.length || 0} skills extracted ·{' '}
                {resume.status === 'reviewed' ? 'confirmed' : 'pending review'}
              </div>
            </div>
          </div>
          <Link to="/resume" className="btn btn-secondary btn-sm">Review and confirm</Link>
        </div>
      ) : (
        <EmptyState
          icon={<Icon name="file" size={18} />}
          title="No resume analysed"
          action={<Link to="/resume" className="btn btn-primary btn-sm">Upload resume</Link>}
        >
          Upload a PDF, DOCX or TXT file to extract skills — you confirm what is kept.
        </EmptyState>
      )}
    </DashboardCard>
  )
}

export function ReadinessCard({ gap, hasTargetRole }) {
  return (
    <DashboardCard
      icon={<Icon name="chart" size={16} />}
      title="Career readiness"
      action={<Link to="/career-gap" className="card-action">{gap ? 'Open analysis' : 'Analyse'}</Link>}
    >
      {gap ? (
        <div>
          <div className="row" style={{ alignItems: 'baseline', gap: '0.5rem', marginBottom: '0.4rem' }}>
            <span className="stat-value">{gap.readiness_score}%</span>
            <span className="badge badge-info">{gap.readiness_band}</span>
          </div>
          <p className="small muted" style={{ marginBottom: '0.65rem' }}>
            {gap.occupation_name} · {gap.matched_count}/{gap.required_count} required skills covered
          </p>
          <div
            className="progress-bar-track"
            role="progressbar"
            aria-valuenow={gap.readiness_score}
            aria-valuemin={0}
            aria-valuemax={100}
            aria-label="Career readiness"
          >
            <div className="progress-bar-fill" style={{ width: `${gap.readiness_score}%` }} />
          </div>
          <p className="tiny muted" style={{ marginTop: '0.55rem' }}>
            Weighted coverage, not a probability of being hired.
          </p>
        </div>
      ) : (
        <EmptyState
          icon={<Icon name="chart" size={18} />}
          title={hasTargetRole ? 'Readiness not calculated' : 'Choose a target role first'}
          action={<Link to="/career-gap" className="btn btn-secondary btn-sm">Open gap analysis</Link>}
        >
          {hasTargetRole
            ? 'Run an analysis to see which required skills are covered.'
            : 'Readiness is measured against the role you are preparing for.'}
        </EmptyState>
      )}
    </DashboardCard>
  )
}

export function RoadmapCard({ roadmap }) {
  return (
    <DashboardCard
      icon={<Icon name="route" size={16} />}
      title="Learning roadmap"
      action={<Link to="/roadmap" className="card-action">{roadmap ? 'Open roadmap' : 'Build'}</Link>}
    >
      {roadmap ? (
        <div>
          <div className="row" style={{ alignItems: 'baseline', gap: '0.5rem', marginBottom: '0.35rem' }}>
            <span className="stat-value">{roadmap.progress.percent_complete}%</span>
            <span className="badge badge-info">
              {roadmap.progress.completed_steps}/{roadmap.progress.total_steps} steps
            </span>
            {roadmap.is_partial && <span className="badge badge-medium">Partial</span>}
          </div>
          <p className="small muted" style={{ marginBottom: '0.5rem' }}>{roadmap.occupation_name}</p>
          <div
            className="progress-bar-track"
            role="progressbar"
            aria-valuenow={roadmap.progress.percent_complete}
            aria-valuemin={0}
            aria-valuemax={100}
            aria-label="Roadmap progress"
          >
            <div className="progress-bar-fill" style={{ width: `${roadmap.progress.percent_complete}%` }} />
          </div>
          {roadmap.next_action && (
            <p className="tiny" style={{ color: 'var(--color-brand-light)', marginTop: '0.55rem' }}>
              Next: {roadmap.next_action}
            </p>
          )}
        </div>
      ) : (
        <EmptyState
          icon={<Icon name="route" size={18} />}
          title="No roadmap yet"
          action={<Link to="/roadmap" className="btn btn-secondary btn-sm">Generate roadmap</Link>}
        >
          Build a prerequisite-ordered plan from your current skills and target role.
        </EmptyState>
      )}
    </DashboardCard>
  )
}

export function AdvisorCard({ gap }) {
  return (
    <DashboardCard
      icon={<Icon name="spark" size={16} />}
      title="Career advisor"
      action={<Link to="/advisor" className="card-action">Ask</Link>}
    >
      <div className="stack" style={{ gap: '0.5rem' }}>
        <p className="small muted">
          Ask a question grounded in your gap, roadmap and a curated source library.
        </p>
        {gap ? (
          <p className="tiny" style={{ color: 'var(--color-brand-light)' }}>
            Context ready: {gap.occupation_name} · {gap.missing_skills?.length || 0} missing required skills
          </p>
        ) : (
          <p className="tiny muted">
            Set a target role to add readiness and roadmap context.
          </p>
        )}
        <Link to="/advisor" className="btn btn-secondary btn-sm" style={{ alignSelf: 'flex-start' }}>
          <Icon name="spark" size={14} /> Ask a grounded question
        </Link>
      </div>
    </DashboardCard>
  )
}

export function AssessmentsCard({ assessments }) {
  const completed = assessments.filter((attempt) => attempt.status === 'completed')
  const latest = completed[0]

  return (
    <DashboardCard
      icon={<Icon name="checkCircle" size={16} />}
      title="Skill assessments"
      action={<Link to="/assessments" className="card-action">{completed.length ? 'View history' : 'Take one'}</Link>}
    >
      {latest ? (
        <div>
          <div className="row" style={{ alignItems: 'baseline', gap: '0.5rem', marginBottom: '0.35rem' }}>
            <span className="stat-value">{latest.score_percent}%</span>
            <span className={`badge ${latest.passed ? 'badge-strong' : 'badge-medium'}`}>
              {latest.passed ? 'Passed' : 'Not passed'}
            </span>
          </div>
          <p className="small muted">
            {latest.assessment_name} · {completed.length} attempt{completed.length === 1 ? '' : 's'} completed
          </p>
          {latest.passed_skills?.length > 0 && (
            <p className="tiny" style={{ color: 'var(--color-brand-light)', marginTop: '0.4rem' }}>
              Confirmed evidence: {latest.passed_skills.join(', ')}
            </p>
          )}
        </div>
      ) : (
        <EmptyState
          icon={<Icon name="checkCircle" size={18} />}
          title="No assessments completed"
          action={<Link to="/assessments" className="btn btn-secondary btn-sm">Browse assessments</Link>}
        >
          Pass a short curated check to add a skill as assessment evidence.
        </EmptyState>
      )}
    </DashboardCard>
  )
}

export function GithubCard({ github }) {
  return (
    <DashboardCard
      icon={<Icon name="code" size={16} />}
      title="GitHub evidence"
      action={<Link to="/verification" className="card-action">{github ? 'Review evidence' : 'Verify'}</Link>}
    >
      {github ? (
        <div>
          <div className="row" style={{ gap: '0.5rem', marginBottom: '0.35rem' }}>
            <strong>@{github.account.username}</strong>
            <span className="badge badge-strong"><Icon name="check" size={11} /> Verified account</span>
          </div>
          <p className="small muted" style={{ marginBottom: '0.45rem' }}>
            {github.repos_analyzed} repositories analysed · {github.skills.length} skills detected
          </p>
          {github.relevant_to_target?.length > 0 && (
            <p className="tiny" style={{ color: 'var(--color-brand-light)' }}>
              Relevant to your target role: {github.relevant_to_target.slice(0, 4).join(', ')}
            </p>
          )}
        </div>
      ) : (
        <EmptyState
          icon={<Icon name="code" size={18} />}
          title="GitHub not linked"
          action={<Link to="/verification" className="btn btn-secondary btn-sm">Verify GitHub</Link>}
        >
          Turn public repositories into evidence-backed skill suggestions you can confirm.
        </EmptyState>
      )}
    </DashboardCard>
  )
}

export function MentorshipCard({ isStudent, requests }) {
  const pending = requests.filter((request) => request.status === 'pending')
  const active = requests.filter((request) => request.status === 'accepted')

  return (
    <DashboardCard
      icon={<Icon name="graduation" size={16} />}
      title={isStudent ? 'Mentorship' : 'Mentorship requests'}
      action={<Link to="/mentors" className="card-action">{isStudent ? 'Find a mentor' : 'Review requests'}</Link>}
    >
      {isStudent ? (
        <div className="stack" style={{ gap: '0.4rem' }}>
          <p className="small muted">
            {active.length} active mentorship{active.length === 1 ? '' : 's'} ·{' '}
            {pending.length} pending request{pending.length === 1 ? '' : 's'}
          </p>
          {active.length > 0 && (
            <p className="tiny muted">
              Mentors: {active.map((request) => request.alumni_name || `#${request.alumni_id}`).join(', ')}
            </p>
          )}
          {active.length === 0 && pending.length === 0 && (
            <p className="tiny muted">
              Mentors are ranked against the skills you still need for your target role.
            </p>
          )}
        </div>
      ) : pending.length > 0 ? (
        <p className="small muted">
          <strong>{pending.length}</strong> pending request{pending.length === 1 ? '' : 's'} awaiting your decision.
        </p>
      ) : (
        <p className="small muted">No pending requests right now.</p>
      )}
    </DashboardCard>
  )
}

export function PlatformRoadmapCard({ phases }) {
  const done = phases.filter((phase) => phase.done).length
  return (
    <DashboardCard icon={<Icon name="layers" size={16} />} title="Platform roadmap">
      <p className="tiny muted" style={{ marginBottom: '0.8rem' }}>
        {done} of {phases.length} milestones shipped. Phase 7 uses local retrieval; an LLM is optional.
      </p>
      <ol className="stack" style={{ gap: '0.4rem' }}>
        {phases.map((phase) => (
          <li key={phase.number} className="row" style={{ gap: '0.55rem', fontSize: '0.82rem' }}>
            <span
              aria-hidden="true"
              style={{
                display: 'grid',
                placeItems: 'center',
                width: 18,
                height: 18,
                borderRadius: '50%',
                flexShrink: 0,
                fontSize: '0.6rem',
                fontWeight: 700,
                color: phase.done ? '#062f22' : 'var(--color-text-muted)',
                background: phase.done ? 'var(--color-accent-green)' : 'var(--color-bg-elevated)',
                border: phase.done ? 'none' : '1px solid var(--color-border)',
              }}
            >
              {phase.done ? <Icon name="check" size={10} strokeWidth={3} /> : phase.number}
            </span>
            <span className={phase.done ? '' : 'muted'} style={{ fontWeight: phase.done ? 500 : 400 }}>
              Phase {phase.number} — {phase.label}
            </span>
          </li>
        ))}
      </ol>
    </DashboardCard>
  )
}
