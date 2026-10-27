/**
 * DashboardPage — the signed-in home screen.
 *
 * Responsibilities are intentionally narrow:
 *   1. Load the profile, health telemetry and (for students) career widgets.
 *   2. Compose the presentational cards in `components/dashboard`.
 *
 * Student-only requests are issued in parallel after the profile resolves,
 * and every state update is guarded against unmounts. Secondary widgets fail
 * closed to their empty state; only a profile failure blocks the page.
 */

import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import Icon from '../components/Icon'
import PageHeader from '../components/PageHeader'
import {
  AdvisorCard,
  AlumniPortfolioCard,
  AssessmentsCard,
  ExpertiseCard,
  GithubCard,
  MentorshipCard,
  MentorPreviewCard,
  PlatformRoadmapCard,
  ProfileStrengthCard,
  ReadinessCard,
  ResumeCard,
  RoadmapCard,
  SkillsCard,
  TargetCareerCard,
  TelemetryCard,
} from '../components/dashboard/DashboardCards'
import { useAuth } from '../hooks/useAuth'
import {
  assessmentAPI,
  careerAPI,
  formatApiError,
  healthAPI,
  mentorshipAPI,
  profileAPI,
  resumeAPI,
  roadmapAPI,
  verificationAPI,
} from '../services/api'

const PLATFORM_PHASES = [
  { number: 1, label: 'Foundation & authentication', done: true },
  { number: 2, label: 'Profiles & mentor directory', done: true },
  { number: 3, label: 'Resume intelligence', done: true },
  { number: 4, label: 'Skill gaps & readiness', done: true },
  { number: 5, label: 'Skill graph & learning roadmaps', done: true },
  { number: 6, label: 'GitHub verification & LinkedIn link', done: true },
  { number: 7, label: 'Grounded career advisor (optional LLM)', done: true },
  { number: 8, label: 'Assessments & alumni matching', done: true },
]

export default function DashboardPage() {
  const { user } = useAuth()
  const isStudent = user?.role === 'student'
  const isAlumni = user?.role === 'alumni'

  const [health, setHealth] = useState(null)
  const [healthLoading, setHealthLoading] = useState(true)
  const [profileData, setProfileData] = useState(null)
  const [profileLoading, setProfileLoading] = useState(true)
  const [profileError, setProfileError] = useState(null)
  const [mentors, setMentors] = useState([])
  const [latestResume, setLatestResume] = useState(null)
  const [gap, setGap] = useState(null)
  const [roadmap, setRoadmap] = useState(null)
  const [assessments, setAssessments] = useState([])
  const [mentorshipRequests, setMentorshipRequests] = useState([])
  const [verification, setVerification] = useState(null)

  useEffect(() => {
    let cancelled = false

    healthAPI
      .check()
      .then((response) => {
        if (!cancelled) setHealth(response.data)
      })
      .catch(() => {
        if (!cancelled) setHealth({ status: 'error', database: 'unreachable' })
      })
      .finally(() => {
        if (!cancelled) setHealthLoading(false)
      })

    mentorshipAPI
      .listRequests()
      .then((response) => {
        if (!cancelled) setMentorshipRequests(response.data)
      })
      .catch(() => {
        if (!cancelled) setMentorshipRequests([])
      })

    const loadProfile = async () => {
      try {
        const response = await profileAPI.getMeProfile()
        if (cancelled) return
        setProfileData(response.data)

        if (user?.role !== 'student') return

        const results = await Promise.allSettled([
          profileAPI.getAlumniMentors(),
          resumeAPI.getLatestResume(),
          careerAPI.getGapAnalysis(),
          roadmapAPI.getCurrent(),
          assessmentAPI.history(),
          verificationAPI.getStatus(),
        ])
        if (cancelled) return

        const [mentorsResult, resumeResult, gapResult, roadmapResult, assessmentResult, verificationResult] = results
        setMentors(mentorsResult.status === 'fulfilled' ? mentorsResult.value.data : [])
        setLatestResume(resumeResult.status === 'fulfilled' ? resumeResult.value.data : null)
        setGap(gapResult.status === 'fulfilled' ? gapResult.value.data : null)
        setRoadmap(roadmapResult.status === 'fulfilled' ? roadmapResult.value.data : null)
        setAssessments(assessmentResult.status === 'fulfilled' ? assessmentResult.value.data : [])
        setVerification(verificationResult.status === 'fulfilled' ? verificationResult.value.data : null)
      } catch (error) {
        if (!cancelled) {
          setProfileError(formatApiError(error, 'We could not load your profile. Please reload and try again.'))
        }
      } finally {
        if (!cancelled) setProfileLoading(false)
      }
    }

    loadProfile()

    return () => {
      cancelled = true
    }
  }, [user])

  const completion = profileData?.completion_percentage ?? 0
  const studentProfile = profileData?.student_profile
  const alumniProfile = profileData?.alumni_profile
  const firstName = user?.full_name?.split(' ')[0] || 'there'
  const showCompletionNotice = !profileLoading && !profileError && completion < 75

  return (
    <div className="page-container">
      <div className="fade-up">
        <PageHeader
          eyebrow="Career overview"
          title={`Welcome back, ${firstName}`}
          subtitle="The evidence behind your readiness, the gaps that remain, and the next useful step for each goal."
          actions={
            <Link to="/profile" className="btn btn-secondary" id="btn-edit-profile-quick">
              <Icon name="users" size={15} /> Manage profile
            </Link>
          }
        />

        {profileError && (
          <div className="alert alert-error" role="alert" style={{ marginBottom: '1.5rem' }}>
            {profileError}
          </div>
        )}

        {showCompletionNotice && (
          <div
            className="alert alert-info spread"
            style={{ marginBottom: '1.75rem' }}
          >
            <div>
              <strong>Your profile is {completion}% complete.</strong>{' '}
              {isStudent
                ? 'Add a target role and the skills you already have so readiness and roadmap results are meaningful.'
                : 'Add your company, role and mentoring availability to start receiving requests.'}
            </div>
            <Link to="/profile" className="btn btn-primary btn-sm">
              Complete profile <Icon name="arrowRight" size={14} />
            </Link>
          </div>
        )}

        <section aria-labelledby="overview-heading">
          <h2 id="overview-heading" className="sr-only">Overview</h2>
          <div className="grid grid-auto" style={{ marginBottom: '2rem' }}>
            <ProfileStrengthCard user={user} completion={completion} />
            {isStudent && <TargetCareerCard profile={studentProfile} />}
            {isAlumni && <AlumniPortfolioCard profile={alumniProfile} />}
            <TelemetryCard health={health} loading={healthLoading} />
          </div>
        </section>

        <section aria-labelledby="intelligence-heading" style={{ marginBottom: '2rem' }}>
          <div className="spread" style={{ marginBottom: '1rem' }}>
            <div>
              <h2 id="intelligence-heading" className="section-title" style={{ fontSize: '1.2rem', marginBottom: '0.15rem' }}>
                Career intelligence
              </h2>
              <p className="small muted">
                {isStudent
                  ? 'Each card links to the full analysis or evidence review.'
                  : 'Your mentoring profile and incoming requests.'}
              </p>
            </div>
            {isStudent && (
              <Link to="/career-gap" className="btn btn-ghost btn-sm">
                Open full analysis <Icon name="arrowRight" size={14} />
              </Link>
            )}
          </div>

          <div className="grid grid-auto stagger">
            {isStudent && <SkillsCard skills={studentProfile?.skills} />}
            {isAlumni && <ExpertiseCard areas={alumniProfile?.expertise_areas} />}
            {isStudent && <ResumeCard resume={latestResume} />}
            {isStudent && <ReadinessCard gap={gap} hasTargetRole={Boolean(studentProfile?.target_role)} />}
            {isStudent && <AdvisorCard gap={gap} />}
            {isStudent && <RoadmapCard roadmap={roadmap} />}
            {isStudent && <AssessmentsCard assessments={assessments} />}
            {isStudent && <GithubCard github={verification?.github} />}
            {isStudent && <MentorPreviewCard mentors={mentors} />}
            <MentorshipCard isStudent={isStudent} requests={mentorshipRequests} />
          </div>
        </section>

        <div className="grid grid-2" style={{ alignItems: 'start' }}>
          <PlatformRoadmapCard phases={PLATFORM_PHASES} />
          <div className="alert alert-info" style={{ marginTop: 0 }}>
            <strong>What this build does — and does not — claim.</strong>{' '}
            Scores are deterministic weighted coverage, not hiring probabilities. Resume and GitHub
            skills remain suggestions until you confirm them. LinkedIn links are self-declared and
            marked unverified. Phase 7 uses local lexical retrieval; an optional LLM may explain the
            cited sources but cannot change your score or roadmap order.
          </div>
        </div>
      </div>
    </div>
  )
}
