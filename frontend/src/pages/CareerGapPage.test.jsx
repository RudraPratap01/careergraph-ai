/**
 * CareerGapPage tests — Phase 4 UI.
 *
 * The API layer is mocked; these tests verify the page renders the backend's
 * deterministic readiness result (score, band, matched/missing skills,
 * explanation and disclaimer) and re-runs the analysis when the target
 * occupation changes.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'

vi.mock('../services/api', () => ({
  careerAPI: {
    listOccupations: vi.fn(),
    getOccupation: vi.fn(),
    getGapAnalysis: vi.fn(),
  },
  profileAPI: { getMeProfile: vi.fn() },
  formatApiError: (_e, fallback) => fallback,
}))

import CareerGapPage from './CareerGapPage'
import { careerAPI, profileAPI } from '../services/api'

const GAP = {
  occupation_key: 'frontend-developer',
  occupation_name: 'Frontend Developer',
  occupation_category: 'Software Engineering',
  target_source: 'profile.target_role',
  readiness_score: 25,
  readiness_band: 'Emerging',
  matched_count: 1,
  required_count: 4,
  matched_skills: [
    { name: 'Python', category: 'Languages', weight: 4, matched: true, user_level: 'advanced', rationale: '' },
  ],
  missing_skills: [
    { name: 'REST APIs', category: 'Concepts & Architecture', weight: 3, matched: false, user_level: null, rationale: '' },
    { name: 'React', category: 'Frameworks & Libraries', weight: 5, matched: false, user_level: null, rationale: '' },
    { name: 'TypeScript', category: 'Languages', weight: 3, matched: false, user_level: null, rationale: '' },
  ],
  bonus_skills: [],
  missing_bonus_skills: [],
  unknown_skills: ['Underwater Basket Weaving'],
  contributions: [],
  explanation: 'Frontend Developer: you cover 1 of 4 required skills.',
  disclaimer: 'It is a deterministic coverage metric, not a probability of getting hired.',
}

function renderPage() {
  return render(
    <MemoryRouter>
      <CareerGapPage />
    </MemoryRouter>
  )
}

beforeEach(() => {
  vi.clearAllMocks()
  careerAPI.listOccupations.mockResolvedValue({
    data: [
      { key: 'frontend-developer', name: 'Frontend Developer', description: 'Frontend role' },
      { key: 'backend-developer', name: 'Backend Developer', description: 'Backend role' },
    ],
  })
  profileAPI.getMeProfile.mockResolvedValue({
    data: { student_profile: { target_role: 'Frontend Developer' } },
  })
  careerAPI.getGapAnalysis.mockResolvedValue({ data: GAP })
})

describe('CareerGapPage', () => {
  it('analyses the saved target role on load and renders the result', async () => {
    renderPage()

    expect(await screen.findByTestId('gap-analysis')).toBeInTheDocument()
    expect(careerAPI.getGapAnalysis).toHaveBeenCalledWith('Frontend Developer')

    expect(screen.getByText('25%')).toBeInTheDocument()
    expect(screen.getByText('Emerging')).toBeInTheDocument()
    expect(screen.getByText('1/4 required skills covered')).toBeInTheDocument()
    expect(screen.getByRole('progressbar')).toHaveAttribute('aria-valuenow', '25')
  })

  it('shows matched, missing and unknown skills, plus the disclaimer', async () => {
    renderPage()
    await screen.findByTestId('gap-analysis')

    // Matched section contains Python.
    expect(screen.getByText('Matched required skills (1)')).toBeInTheDocument()
    expect(screen.getByText('Python')).toBeInTheDocument()

    // Missing section.
    expect(screen.getByText('Missing required skills (3)')).toBeInTheDocument()
    expect(screen.getByText('REST APIs')).toBeInTheDocument()

    // Unknown skills are reported, not silently dropped.
    expect(screen.getByText('Underwater Basket Weaving')).toBeInTheDocument()

    // Disclaimer makes the metric's meaning explicit.
    expect(screen.getByText(/not a probability of getting hired/i)).toBeInTheDocument()
  })

  it('re-runs the analysis when a different occupation is chosen', async () => {
    const user = userEvent.setup()
    renderPage()
    await screen.findByTestId('gap-analysis')

    await user.selectOptions(screen.getByLabelText('Target occupation'), 'backend-developer')

    const backendGap = { ...GAP, occupation_key: 'backend-developer', occupation_name: 'Backend Developer' }
    careerAPI.getGapAnalysis.mockResolvedValue({ data: backendGap })

    await user.click(screen.getByRole('button', { name: 'Analyze gap' }))

    expect(careerAPI.getGapAnalysis).toHaveBeenLastCalledWith('backend-developer')
    // Scope to the result panel: the <option> also contains the role name.
    const panel = await screen.findByTestId('gap-analysis')
    expect(within(panel).getByText('Backend Developer')).toBeInTheDocument()
  })

  it('prompts the student to choose an occupation when none is set', async () => {
    profileAPI.getMeProfile.mockResolvedValue({ data: { student_profile: { target_role: null } } })
    const badRequest = Object.assign(new Error('no target'), { response: { status: 400 } })
    careerAPI.getGapAnalysis.mockRejectedValue(badRequest)

    renderPage()

    expect(await screen.findByText(/Select a target occupation/i)).toBeInTheDocument()
    expect(screen.queryByTestId('gap-analysis')).not.toBeInTheDocument()
  })

  it('offers a link to build the roadmap', async () => {
    renderPage()
    await screen.findByTestId('gap-analysis')
    const link = screen.getByRole('link', { name: /Build my learning roadmap/i })
    expect(link).toHaveAttribute('href', '/roadmap')
  })
})
