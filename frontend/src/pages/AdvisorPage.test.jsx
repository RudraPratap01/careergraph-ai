/**
 * AdvisorPage tests — Phase 7 UI.
 *
 * The API is mocked. These tests verify the page shows the deterministic
 * context, renders source-attributed answers, distinguishes LLM from local
 * fallback mode, and handles loading/error/general-question states without
 * pretending an LLM was used.
 */

import { beforeEach, describe, expect, it, vi } from 'vitest'
import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'

vi.mock('../services/api', () => ({
  careerAPI: {
    getGapAnalysis: vi.fn(),
  },
  roadmapAPI: {
    getCurrent: vi.fn(),
  },
  intelligenceAPI: {
    status: vi.fn(),
    ask: vi.fn(),
  },
  formatApiError: (_error, fallback) => fallback,
}))

import AdvisorPage from './AdvisorPage'
import { careerAPI, intelligenceAPI, roadmapAPI } from '../services/api'

const GAP = {
  occupation_key: 'backend-developer',
  occupation_name: 'Backend Developer',
  occupation_category: 'Software Engineering',
  readiness_score: 25,
  readiness_band: 'Emerging',
  matched_count: 1,
  required_count: 4,
  matched_skills: [{ name: 'Python' }],
  missing_skills: [{ name: 'Docker' }, { name: 'REST APIs' }],
  optional_skills: [],
  explanation: 'Deterministic explanation.',
  disclaimer: 'Not a probability of employment.',
}

const ROADMAP = {
  id: 4,
  occupation_key: 'backend-developer',
  occupation_name: 'Backend Developer',
  progress: { percent_complete: 0, completed_steps: 0, total_steps: 2 },
  steps: [
    { skill: 'Docker', position: 1, status: 'pending' },
    { skill: 'REST APIs', position: 2, status: 'pending' },
  ],
  next_action: 'Start with Docker',
}

const STATUS = {
  enabled: true,
  retrieval: 'lexical_bm25',
  llm_configured: false,
  provider: 'local',
  model: null,
  knowledge: { document_count: 94, chunk_count: 102, source: 'curated', retrieval: 'lexical_bm25' },
  limitations: ['Lexical retrieval is not semantic search.'],
  privacy_note: 'No LLM key is configured, so no external AI request is made.',
  disclaimer: 'Educational guidance, not a hiring probability.',
}

const ANSWER = {
  answer:
    'Start with the highest-importance missing skill and follow the prerequisite-aware roadmap order [S1]. Confirm the evidence before relying on it.',
  mode: 'grounded_extractive',
  retrieval: 'lexical_bm25',
  llm_configured: false,
  llm_used: false,
  provider: 'local',
  model: null,
  sources: [
    {
      id: 'S1',
      document_id: 'guidance:learning-loop',
      title: 'A practical learning loop',
      source: 'curated://guidance/learning-loop',
      source_label: 'CareerGraph curated guidance - A practical learning loop',
      kind: 'career-guide',
      score: 4.2,
      snippet: 'Review the current gap and pick one high-importance missing skill.',
    },
  ],
  context: {
    occupation_key: 'backend-developer',
    occupation_name: 'Backend Developer',
    readiness_score: 25,
    readiness_band: 'Emerging',
    matched_count: 1,
    required_count: 4,
    known_skills: ['Python'],
    missing_skills: ['Docker', 'REST APIs'],
    roadmap_steps: ['Docker', 'REST APIs'],
    graph_backend: 'memory',
  },
  notice: 'No LLM key is configured; this answer is generated locally from the retrieved sources.',
  limitations: [
    'Retrieval is lexical BM25 over a small curated corpus, not semantic embedding search.',
    'The advisor may explain the deterministic readiness and roadmap but never changes them.',
  ],
  privacy_note:
    'No LLM key is configured, so no external AI request is made. Resume files, resume text, email, names, account IDs and tokens are not used by this endpoint.',
  disclaimer: 'Readiness is a deterministic metric, not a probability of being hired.',
  request_id: 'test-request-id',
}

function renderPage() {
  return render(
    <MemoryRouter>
      <AdvisorPage />
    </MemoryRouter>,
  )
}

beforeEach(() => {
  vi.clearAllMocks()
  careerAPI.getGapAnalysis.mockResolvedValue({ data: GAP })
  roadmapAPI.getCurrent.mockResolvedValue({ data: ROADMAP })
  intelligenceAPI.status.mockResolvedValue({ data: STATUS })
  intelligenceAPI.ask.mockResolvedValue({ data: ANSWER })
})

describe('AdvisorPage', () => {
  it('shows the deterministic context, offline mode and source-attributed answer', async () => {
    const user = userEvent.setup()
    renderPage()

    expect(await screen.findByText('Backend Developer')).toBeInTheDocument()
    expect(screen.getByText('25% · Emerging')).toBeInTheDocument()
    expect(screen.getByText('Offline · no LLM key')).toBeInTheDocument()
    expect(screen.getByText('1 matched · 2 missing')).toBeInTheDocument()
    expect(screen.getByText('Docker')).toBeInTheDocument()

    const textarea = screen.getByLabelText(/your question/i)
    await user.type(textarea, 'What should I learn first?')
    await user.click(screen.getByRole('button', { name: /ask advisor/i }))

    expect(intelligenceAPI.ask).toHaveBeenCalledWith(
      'What should I learn first?',
      'backend-developer',
    )
    const answer = await screen.findByTestId('advisor-answer')
    expect(within(answer).getByText(/Start with the highest-importance/)).toBeInTheDocument()
    expect(within(answer).getByText('Local grounded answer')).toBeInTheDocument()
    expect(within(answer).getByText('25%')).toBeInTheDocument()
    expect(within(answer).getByText('A practical learning loop')).toBeInTheDocument()
    expect(within(answer).getByText('S1')).toBeInTheDocument()
    expect(within(answer).getAllByText(/No LLM key is configured/).length).toBeGreaterThan(0)
    expect(within(answer).getByText(/Resume files, resume text, email/i)).toBeInTheDocument()
  })

  it('fills a suggested question and reports a validation error for an empty submit', async () => {
    const user = userEvent.setup()
    renderPage()

    const suggestion = await screen.findByRole('button', {
      name: /how can i close my biggest skill gap/i,
    })
    await user.click(suggestion)
    expect(screen.getByLabelText(/your question/i)).toHaveValue(
      'How can I close my biggest skill gap?',
    )

    await user.clear(screen.getByLabelText(/your question/i))
    await user.click(screen.getByRole('button', { name: /ask advisor/i }))
    expect(screen.getByRole('alert')).toHaveTextContent(/at least 3 characters/i)
    expect(intelligenceAPI.ask).not.toHaveBeenCalled()
  })

  it('shows a loading state and keeps the submit button disabled while waiting', async () => {
    const user = userEvent.setup()
    let resolveAnswer
    intelligenceAPI.ask.mockReturnValueOnce(
      new Promise((resolve) => {
        resolveAnswer = resolve
      }),
    )
    renderPage()

    await screen.findByText('Backend Developer')
    await user.type(screen.getByLabelText(/your question/i), 'What next?')
    await user.click(screen.getByRole('button', { name: /ask advisor/i }))

    expect(screen.getByRole('button', { name: /thinking/i })).toBeDisabled()
    expect(screen.getByRole('status')).toHaveTextContent(/Retrieving curated sources/i)

    resolveAnswer({ data: ANSWER })
    expect(await screen.findByTestId('advisor-answer')).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /thinking/i })).not.toBeInTheDocument()
  })

  it('shows a retryable error without clearing the question', async () => {
    const user = userEvent.setup()
    intelligenceAPI.ask.mockRejectedValueOnce(new Error('Provider unavailable'))
    renderPage()

    await screen.findByText('Backend Developer')
    await user.type(screen.getByLabelText(/your question/i), 'What should I learn?')
    await user.click(screen.getByRole('button', { name: /ask advisor/i }))

    expect(await screen.findByRole('alert')).toHaveTextContent(/could not answer just now/i)
    expect(screen.getByLabelText(/your question/i)).toHaveValue('What should I learn?')
    expect(screen.queryByTestId('advisor-answer')).not.toBeInTheDocument()
  })

  it('still supports general questions when no target context is available', async () => {
    const user = userEvent.setup()
    careerAPI.getGapAnalysis.mockRejectedValueOnce(new Error('No target role'))
    roadmapAPI.getCurrent.mockRejectedValueOnce(new Error('No roadmap'))
    renderPage()

    expect(await screen.findByText(/No target role or gap analysis is available yet/)).toBeInTheDocument()
    await user.type(screen.getByLabelText(/your question/i), 'How does readiness work?')
    await user.click(screen.getByRole('button', { name: /ask advisor/i }))

    expect(intelligenceAPI.ask).toHaveBeenCalledWith('How does readiness work?', undefined)
  })

  it('labels a validated LLM answer as such and keeps its sources visible', async () => {
    const user = userEvent.setup()
    const llmAnswer = {
      ...ANSWER,
      mode: 'llm',
      llm_configured: true,
      llm_used: true,
      provider: 'openrouter',
      model: 'test/model',
      notice: null,
      privacy_note:
        'An LLM key is configured. The question, canonical skill names and retrieved excerpts may be sent to OpenRouter. Resume files and email are never included.',
    }
    intelligenceAPI.status.mockResolvedValueOnce({
      data: { ...STATUS, llm_configured: true, provider: 'openrouter', model: 'test/model' },
    })
    intelligenceAPI.ask.mockResolvedValueOnce({ data: llmAnswer })
    renderPage()

    expect(await screen.findByText('LLM explanations enabled')).toBeInTheDocument()
    await user.type(screen.getByLabelText(/your question/i), 'What next?')
    await user.click(screen.getByRole('button', { name: /ask advisor/i }))

    const answer = await screen.findByTestId('advisor-answer')
    expect(within(answer).getByText('LLM explanation · citations checked')).toBeInTheDocument()
    expect(within(answer).getByText(/Resume files and email are never included/)).toBeInTheDocument()
    expect(within(answer).getByText('A practical learning loop')).toBeInTheDocument()
  })
})
