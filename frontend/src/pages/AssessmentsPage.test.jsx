/**
 * AssessmentsPage tests — Phase 8 UI.
 *
 * All API calls are mocked. These tests verify the catalogue renders, that the
 * runner only ever shows what the API sent (no answers before submission),
 * that submitting posts the selected answers, and that profile evidence is only
 * written when the student explicitly confirms it.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'

vi.mock('../services/api', () => ({
  assessmentAPI: {
    list: vi.fn(),
    get: vi.fn(),
    start: vi.fn(),
    submit: vi.fn(),
    confirmSkills: vi.fn(),
    history: vi.fn(),
  },
  formatApiError: (_e, fallback) => fallback,
}))

import AssessmentsPage from './AssessmentsPage'
import { assessmentAPI } from '../services/api'

const CATALOG = [
  {
    key: 'python-fundamentals',
    name: 'Python Fundamentals',
    description: 'Core Python syntax and data structures.',
    skills: ['Python'],
    question_count: 2,
    pass_threshold: 70,
    source: 'curated',
  },
]

const QUESTIONS = [
  {
    id: 'py-1',
    skill: 'Python',
    difficulty: 'easy',
    prompt: 'Which keyword defines a function?',
    options: ['def', 'func', 'lambda', 'define'],
  },
  {
    id: 'py-2',
    skill: 'Python',
    difficulty: 'easy',
    prompt: 'Which type is immutable?',
    options: ['list', 'dict', 'tuple', 'set'],
  },
]

function resultBody({ passed = true, suggested = ['Python'] } = {}) {
  return {
    attempt: {
      id: 11,
      user_id: 1,
      assessment_key: 'python-fundamentals',
      assessment_name: 'Python Fundamentals',
      status: 'completed',
      score_percent: passed ? 100 : 50,
      passed,
      correct_count: passed ? 2 : 1,
      total_count: 2,
      skills: [
        {
          skill: 'Python',
          category: 'Languages',
          correct: passed ? 2 : 1,
          total: 2,
          score_percent: passed ? 100 : 50,
          passed,
          eligible_for_evidence: passed,
        },
      ],
      passed_skills: passed ? ['Python'] : [],
      started_at: '2026-01-01T00:00:00Z',
      completed_at: '2026-01-01T00:05:00Z',
    },
    results: [
      {
        question_id: 'py-1',
        skill: 'Python',
        correct: true,
        chosen_index: 0,
        correct_index: 0,
        explanation: '`def` introduces a function definition.',
      },
    ],
    suggested_skills: suggested,
    explanation: 'Deterministic score from your answers.',
    disclaimer: 'A quiz result is not a certification.',
  }
}

function renderPage() {
  return render(
    <MemoryRouter>
      <AssessmentsPage />
    </MemoryRouter>
  )
}

async function startAndAnswer(user) {
  await screen.findByTestId('assessment-catalogue')
  await user.click(screen.getByRole('button', { name: 'Start assessment' }))
  const q1 = await screen.findByTestId('question-py-1')
  await user.click(within(q1).getByLabelText('def'))
  await user.click(screen.getByRole('button', { name: 'Submit answers' }))
}

beforeEach(() => {
  vi.clearAllMocks()
  assessmentAPI.list.mockResolvedValue({ data: CATALOG })
  assessmentAPI.history.mockResolvedValue({ data: [] })
})

describe('AssessmentsPage', () => {
  it('renders the curated catalogue from the API', async () => {
    renderPage()

    expect(await screen.findByTestId('assessment-catalogue')).toBeInTheDocument()
    const card = screen.getByTestId('assessment-python-fundamentals')
    expect(within(card).getByText('Python Fundamentals')).toBeInTheDocument()
    expect(within(card).getByText(/2 questions/)).toBeInTheDocument()
    expect(within(card).getByText(/skills: Python/)).toBeInTheDocument()
  })

  it('shows the questions without exposing correct answers', async () => {
    const user = userEvent.setup()
    assessmentAPI.start.mockResolvedValue({
      data: {
        attempt: { ...resultBody().attempt, status: 'in_progress', score_percent: null, passed: null },
        questions: QUESTIONS,
      },
    })

    renderPage()
    await user.click(await screen.findByRole('button', { name: 'Start assessment' }))

    expect(assessmentAPI.start).toHaveBeenCalledWith('python-fundamentals')
    const runner = await screen.findByTestId('assessment-runner')
    expect(within(runner).getByText(/Which keyword defines a function\?/)).toBeInTheDocument()
    expect(within(runner).getByText(/Which type is immutable\?/)).toBeInTheDocument()
    // Nothing from the answer key is rendered.
    expect(runner.textContent).not.toMatch(/correct_index/)
  })

  it('submits the chosen answers and renders the graded result', async () => {
    const user = userEvent.setup()
    assessmentAPI.start.mockResolvedValue({ data: { attempt: resultBody().attempt, questions: QUESTIONS } })
    assessmentAPI.submit.mockResolvedValue({ data: resultBody() })

    renderPage()
    await startAndAnswer(user)

    expect(assessmentAPI.submit).toHaveBeenCalledWith(11, [
      { question_id: 'py-1', chosen_index: 0 },
    ])

    const result = await screen.findByTestId('assessment-result')
    expect(within(result).getByText('100%')).toBeInTheDocument()
    expect(within(result).getByText('Passed')).toBeInTheDocument()
    expect(within(result).getByText(/✓ Python — 100%/)).toBeInTheDocument()
  })

  it('only writes profile evidence when the student confirms', async () => {
    const user = userEvent.setup()
    assessmentAPI.start.mockResolvedValue({ data: { attempt: resultBody().attempt, questions: QUESTIONS } })
    assessmentAPI.submit.mockResolvedValue({ data: resultBody() })
    assessmentAPI.confirmSkills.mockResolvedValue({
      data: { added: ['Python'], already_present: [], skills: [], message: 'Added Python to your profile.' },
    })

    renderPage()
    await startAndAnswer(user)

    // Merely grading must never write to the profile.
    expect(assessmentAPI.confirmSkills).not.toHaveBeenCalled()

    const result = await screen.findByTestId('assessment-result')
    await user.click(within(result).getByRole('button', { name: /Add 1 skill to my profile/ }))

    expect(assessmentAPI.confirmSkills).toHaveBeenCalledWith(11, ['Python'])
    expect(await screen.findByText(/Added Python to your profile/)).toBeInTheDocument()
  })

  it('lets the student deselect a suggested skill before confirming', async () => {
    const user = userEvent.setup()
    assessmentAPI.start.mockResolvedValue({ data: { attempt: resultBody().attempt, questions: QUESTIONS } })
    assessmentAPI.submit.mockResolvedValue({ data: resultBody() })

    renderPage()
    await startAndAnswer(user)

    const result = await screen.findByTestId('assessment-result')
    await user.click(within(result).getByRole('checkbox', { name: 'Python' }))

    expect(within(result).getByRole('button', { name: /Add 0 skills/ })).toBeDisabled()
  })

  it('offers nothing to add when no skill reached the threshold', async () => {
    const user = userEvent.setup()
    assessmentAPI.start.mockResolvedValue({ data: { attempt: resultBody().attempt, questions: QUESTIONS } })
    assessmentAPI.submit.mockResolvedValue({ data: resultBody({ passed: false, suggested: [] }) })

    renderPage()
    await startAndAnswer(user)

    const result = await screen.findByTestId('assessment-result')
    expect(within(result).getByText('Not passed')).toBeInTheDocument()
    expect(within(result).queryByRole('button', { name: /to my profile/ })).not.toBeInTheDocument()
    expect(within(result).getByText(/No skill reached the evidence threshold/)).toBeInTheDocument()
  })

  it('lists previous attempts from the API', async () => {
    assessmentAPI.history.mockResolvedValue({
      data: [
        {
          id: 9,
          assessment_name: 'Python Fundamentals',
          status: 'completed',
          score_percent: 80,
          passed: true,
          passed_skills: ['Python'],
        },
      ],
    })

    renderPage()

    const history = await screen.findByTestId('assessment-history')
    expect(within(history).getByText('Python Fundamentals')).toBeInTheDocument()
    expect(within(history).getByText(/80%/)).toBeInTheDocument()
    expect(within(history).getByText(/evidenced: Python/)).toBeInTheDocument()
  })
})
