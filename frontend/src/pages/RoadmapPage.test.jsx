/**
 * RoadmapPage tests — Phase 5 UI.
 *
 * All API calls are mocked; these tests verify the page renders the backend's
 * ordering, relationships, progress and states, and that progress updates call
 * the correct endpoint.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'

vi.mock('../services/api', () => ({
  careerAPI: { listOccupations: vi.fn() },
  profileAPI: { getMeProfile: vi.fn() },
  roadmapAPI: {
    getCurrent: vi.fn(),
    generate: vi.fn(),
    refresh: vi.fn(),
    updateStep: vi.fn(),
  },
  formatApiError: (_e, fallback) => fallback,
}))

import RoadmapPage from './RoadmapPage'
import { careerAPI, profileAPI, roadmapAPI } from '../services/api'

const ROADMAP = {
  id: 7,
  user_id: 1,
  occupation_key: 'frontend-developer',
  occupation_name: 'Frontend Developer',
  occupation_category: 'Software Engineering',
  target_source: 'request',
  graph_backend: 'memory',
  is_partial: false,
  notes: null,
  status: 'active',
  steps: [
    {
      position: 1,
      skill: 'Python',
      category: 'Languages',
      depth: 1,
      status: 'pending',
      is_target_skill: false,
      prerequisites: [],
      reason: 'Python is a prerequisite for Data Structures & Algorithms.',
    },
    {
      position: 2,
      skill: 'Data Structures & Algorithms',
      category: 'Concepts & Architecture',
      depth: 0,
      status: 'pending',
      is_target_skill: true,
      prerequisites: ['Python'],
      reason: 'Data Structures & Algorithms is required for Frontend Developer.',
    },
  ],
  possessed_skills: ['JavaScript'],
  progress: { total_steps: 2, completed_steps: 0, in_progress_steps: 0, percent_complete: 0 },
  next_action: 'Start with Python — it is a prerequisite.',
  explanation: '2 steps to learn.',
  disclaimer: 'Deterministic guidance, not a guarantee of employment.',
  created_at: '2026-01-01T00:00:00Z',
  updated_at: '2026-01-01T00:00:00Z',
}

function renderPage() {
  return render(
    <MemoryRouter>
      <RoadmapPage />
    </MemoryRouter>
  )
}

beforeEach(() => {
  vi.clearAllMocks()
  careerAPI.listOccupations.mockResolvedValue({
    data: [{ key: 'frontend-developer', name: 'Frontend Developer', description: 'Frontend role' }],
  })
  profileAPI.getMeProfile.mockResolvedValue({
    data: { student_profile: { target_role: 'Frontend Developer' } },
  })
  roadmapAPI.getCurrent.mockResolvedValue({ data: ROADMAP })
})

describe('RoadmapPage', () => {
  it('renders the ordered steps with prerequisite relationships', async () => {
    renderPage()

    expect(await screen.findByTestId('roadmap')).toBeInTheDocument()
    expect(within(screen.getByTestId('roadmap')).getByText('Frontend Developer')).toBeInTheDocument()

    const items = screen.getAllByRole('listitem')
    expect(items).toHaveLength(2)
    // The prerequisite step is rendered before the skill that depends on it.
    expect(within(items[0]).getByText('Python')).toBeInTheDocument()
    expect(within(items[1]).getByText('Data Structures & Algorithms')).toBeInTheDocument()

    // Relationship + role labels are shown.
    expect(within(items[0]).getByText('Prerequisite')).toBeInTheDocument()
    expect(within(items[1]).getByText('Role skill')).toBeInTheDocument()
    expect(within(items[1]).getByText('Python')).toBeInTheDocument() // "Requires first"
  })

  it('shows possessed skills and the next action', async () => {
    renderPage()
    await screen.findByTestId('roadmap')

    expect(screen.getByText('✓ JavaScript')).toBeInTheDocument()
    expect(screen.getByText(/Start with Python/)).toBeInTheDocument()
    expect(screen.getByText(/not a guarantee of employment/i)).toBeInTheDocument()
  })

  it('persists a progress update through the API', async () => {
    const user = userEvent.setup()
    roadmapAPI.updateStep.mockResolvedValue({
      data: {
        message: 'ok',
        step: { ...ROADMAP.steps[0], status: 'completed' },
        progress: { total_steps: 2, completed_steps: 1, in_progress_steps: 0, percent_complete: 50 },
        next_action: 'Continue with Data Structures & Algorithms.',
      },
    })

    renderPage()
    await screen.findByTestId('roadmap')

    const firstStep = screen.getAllByRole('listitem')[0]
    await user.click(within(firstStep).getByRole('button', { name: 'Completed' }))

    expect(roadmapAPI.updateStep).toHaveBeenCalledWith(7, 'Python', 'completed')
    // The progress bar summary reflects the server response.
    expect(await screen.findByText('1/2 steps done')).toBeInTheDocument()
    expect(screen.getByText('✓ Completed')).toBeInTheDocument()
  })

  it('prompts to generate when no roadmap exists yet', async () => {
    const notFound = Object.assign(new Error('nope'), { response: { status: 404 } })
    roadmapAPI.getCurrent.mockRejectedValue(notFound)

    renderPage()

    expect(await screen.findByText(/No roadmap yet/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Generate roadmap/i })).toBeInTheDocument()
  })

  it('surfaces a partial-roadmap warning when the backend flags it', async () => {
    roadmapAPI.getCurrent.mockResolvedValue({
      data: { ...ROADMAP, is_partial: true, notes: 'No dependency data is available.' },
    })
    renderPage()
    await screen.findByTestId('roadmap')
    expect(screen.getByText(/Partial roadmap/i)).toBeInTheDocument()
    expect(screen.getByText(/No dependency data is available/)).toBeInTheDocument()
  })
})
