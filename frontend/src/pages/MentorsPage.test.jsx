/**
 * MentorsPage tests — Phase 8 UI.
 *
 * All API calls (and the auth role) are mocked. These tests verify the ranked
 * mentor list renders with its full factor breakdown, that capacity/status rules
 * disable the request button, that requesting posts the mentor id and message,
 * and that alumni can accept or decline the requests they received.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'

const auth = vi.hoisted(() => ({ role: 'student' }))

vi.mock('../hooks/useAuth', () => ({
  useAuth: () => ({ user: { role: auth.role, full_name: 'Test Student' } }),
}))

vi.mock('../services/api', () => ({
  mentorshipAPI: {
    getMatches: vi.fn(),
    requestMentorship: vi.fn(),
    listRequests: vi.fn(),
    accept: vi.fn(),
    decline: vi.fn(),
    cancel: vi.fn(),
  },
  formatApiError: (_e, fallback) => fallback,
}))

import MentorsPage from './MentorsPage'
import { mentorshipAPI } from '../services/api'

function mentor(overrides = {}) {
  return {
    user_id: 42,
    full_name: 'Priya Mentor',
    company: 'Acme',
    job_title: 'Staff Engineer',
    years_of_experience: 10,
    college: 'IIT Example',
    expertise_areas: ['Python', 'SQL'],
    bio: 'Backend engineer turned mentor.',
    linkedin_url: null,
    github_username: null,
    meeting_link: null,
    is_available_for_mentoring: true,
    max_mentees: 3,
    accepted_mentees: 0,
    remaining_capacity: 3,
    match_score: 85,
    match_band: 'Strong',
    overlap_skills: ['SQL'],
    factors: [
      { key: 'gap_overlap', label: 'Covers your gaps', weight: 40, earned: 20, detail: '1 of 2 outstanding skills.' },
      { key: 'same_college', label: 'Same college', weight: 20, earned: 20, detail: 'You both studied at IIT Example.' },
      { key: 'experience', label: 'Experience', weight: 15, earned: 15, detail: '10+ years.' },
      { key: 'availability', label: 'Mentoring availability', weight: 15, earned: 15, detail: 'Actively mentoring.' },
      { key: 'capacity', label: 'Free mentee slots', weight: 10, earned: 10, detail: '3 of 3 slots free.' },
    ],
    request_status: null,
    ...overrides,
  }
}

const MATCHES = {
  target_occupation: 'Backend Developer',
  missing_skills: ['Python', 'SQL'],
  matches: [mentor()],
  explanation: 'Ranked by a weighted heuristic. 1 mentor available.',
  disclaimer: 'A match score is a ranking aid, not a promise of a good match.',
}

function renderPage() {
  return render(
    <MemoryRouter>
      <MentorsPage />
    </MemoryRouter>
  )
}

beforeEach(() => {
  vi.clearAllMocks()
  auth.role = 'student'
  mentorshipAPI.listRequests.mockResolvedValue({ data: [] })
  mentorshipAPI.getMatches.mockResolvedValue({ data: MATCHES })
})

describe('MentorsPage (student)', () => {
  it('renders ranked mentors with the outstanding skills', async () => {
    renderPage()

    const panel = await screen.findByTestId('mentor-matches')
    expect(within(panel).getByText('Ranked for Backend Developer')).toBeInTheDocument()
    // Outstanding skills are listed once per occurrence (header + expertise badges).
    expect(within(panel).getByText('Skills you still need for this role:')).toBeInTheDocument()
    expect(within(panel).getAllByText('Python').length).toBeGreaterThan(0)
    expect(within(panel).getByText(/Ranked by a weighted heuristic/)).toBeInTheDocument()
    expect(within(panel).getByText(/not a promise of a good match/)).toBeInTheDocument()
  })

  it('shows the full factor breakdown behind the score', async () => {
    const user = userEvent.setup()
    renderPage()

    const card = await screen.findByTestId('mentor-42')
    expect(within(card).getByText('85')).toBeInTheDocument()
    expect(within(card).getByText('Strong match')).toBeInTheDocument()
    expect(within(card).getByText(/Mentee slots: 3 of 3 remaining/)).toBeInTheDocument()

    await user.click(within(card).getByText('Why 85/100?'))
    expect(within(card).getByText(/Covers your gaps: 20\/40/)).toBeInTheDocument()
    expect(within(card).getByText(/Same college: 20\/20/)).toBeInTheDocument()
  })

  it('sends a mentorship request with the mentor id and message', async () => {
    const user = userEvent.setup()
    const created = {
      id: 7,
      student_id: 1,
      student_name: 'Test Student',
      alumni_id: 42,
      alumni_name: 'Priya Mentor',
      message: 'Could you help me with SQL?',
      status: 'pending',
      match_score: 85,
      created_at: '2026-01-01T00:00:00Z',
      updated_at: '2026-01-01T00:00:00Z',
    }
    mentorshipAPI.requestMentorship.mockResolvedValue({ data: created })
    mentorshipAPI.listRequests
      .mockResolvedValueOnce({ data: [] })
      .mockResolvedValue({ data: [created] })

    renderPage()
    const card = await screen.findByTestId('mentor-42')
    await user.click(within(card).getByRole('button', { name: 'Request mentorship' }))

    await user.type(within(card).getByLabelText('Optional message'), 'Could you help me with SQL?')
    await user.click(within(card).getByRole('button', { name: 'Send request' }))

    expect(mentorshipAPI.requestMentorship).toHaveBeenCalledWith(42, 'Could you help me with SQL?')
    expect(await screen.findByText('Your mentorship request was sent.')).toBeInTheDocument()
    const sent = await screen.findByTestId('requests-sent')
    expect(within(sent).getByText('pending')).toBeInTheDocument()
  })

  it('disables requesting when at capacity, unavailable or already asked', async () => {
    mentorshipAPI.getMatches.mockResolvedValue({
      data: {
        ...MATCHES,
        matches: [
          mentor({ user_id: 1, remaining_capacity: 0 }),
          mentor({ user_id: 2, is_available_for_mentoring: false }),
          mentor({ user_id: 3, request_status: 'pending' }),
          mentor({ user_id: 4, request_status: 'accepted' }),
        ],
      },
    })

    renderPage()

    expect(await screen.findByRole('button', { name: 'At capacity' })).toBeDisabled()
    expect(screen.getByRole('button', { name: 'Unavailable' })).toBeDisabled()
    expect(screen.getByRole('button', { name: 'Request pending' })).toBeDisabled()
    expect(screen.getByRole('button', { name: 'Already your mentor' })).toBeDisabled()
  })

  it('lists the requests the student sent and can cancel a pending one', async () => {
    const user = userEvent.setup()
    mentorshipAPI.listRequests.mockResolvedValue({
      data: [
        {
          id: 5,
          student_id: 1,
          student_name: 'Test Student',
          alumni_id: 42,
          alumni_name: 'Priya Mentor',
          message: 'Hi',
          status: 'pending',
          match_score: 85,
          created_at: '2026-01-01T00:00:00Z',
          updated_at: '2026-01-01T00:00:00Z',
        },
      ],
    })
    mentorshipAPI.cancel.mockResolvedValue({ data: { message: 'ok' } })

    renderPage()

    const sent = await screen.findByTestId('requests-sent')
    expect(within(sent).getByText(/Priya Mentor/)).toBeInTheDocument()
    expect(within(sent).getByText('pending')).toBeInTheDocument()

    await user.click(within(sent).getByRole('button', { name: 'Cancel' }))
    expect(mentorshipAPI.cancel).toHaveBeenCalledWith(5)
    expect(await screen.findByText('Request cancelled.')).toBeInTheDocument()
  })
})

describe('MentorsPage (alumni)', () => {
  beforeEach(() => {
    auth.role = 'alumni'
  })

  it('renders the requests received and accepts one', async () => {
    const user = userEvent.setup()
    mentorshipAPI.listRequests.mockResolvedValue({
      data: [
        {
          id: 7,
          student_id: 9,
          student_name: 'Aarav Student',
          alumni_id: 2,
          alumni_name: 'Priya Mentor',
          message: 'I would love your guidance.',
          status: 'pending',
          match_score: 72,
          created_at: '2026-01-01T00:00:00Z',
          updated_at: '2026-01-01T00:00:00Z',
        },
      ],
    })
    mentorshipAPI.accept.mockResolvedValue({ data: { message: 'ok' } })

    renderPage()

    const panel = await screen.findByTestId('requests-received')
    const card = within(panel).getByTestId('request-7')
    expect(within(card).getByText('Aarav Student')).toBeInTheDocument()
    expect(within(card).getByText(/I would love your guidance/)).toBeInTheDocument()
    expect(within(card).getByText(/ranking score 72\/100/)).toBeInTheDocument()

    // Alumni never load the match list.
    expect(mentorshipAPI.getMatches).not.toHaveBeenCalled()

    await user.click(within(card).getByRole('button', { name: 'Accept' }))
    expect(mentorshipAPI.accept).toHaveBeenCalledWith(7)
    expect(await screen.findByText('Request accepted.')).toBeInTheDocument()
  })

  it('declines a request', async () => {
    const user = userEvent.setup()
    mentorshipAPI.listRequests.mockResolvedValue({
      data: [
        {
          id: 8,
          student_id: 9,
          student_name: 'Aarav Student',
          alumni_id: 2,
          alumni_name: null,
          message: null,
          status: 'pending',
          match_score: null,
          created_at: '2026-01-01T00:00:00Z',
          updated_at: '2026-01-01T00:00:00Z',
        },
      ],
    })
    mentorshipAPI.decline.mockResolvedValue({ data: { message: 'ok' } })

    renderPage()

    const card = await screen.findByTestId('request-8')
    await user.click(within(card).getByRole('button', { name: 'Decline' }))

    expect(mentorshipAPI.decline).toHaveBeenCalledWith(8)
    expect(await screen.findByText('Request declined.')).toBeInTheDocument()
  })

  it('shows an empty state when there are no requests', async () => {
    renderPage()
    expect(await screen.findByText('You have no mentorship requests yet.')).toBeInTheDocument()
  })
})
