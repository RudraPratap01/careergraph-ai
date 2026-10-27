/**
 * ResumePage tests — review list construction and profile-preserving sync.
 *
 * The resume confirmation endpoint treats the submitted list as the complete
 * profile skill list. These tests lock in the UI behaviour that existing
 * non-evidenced profile skills are carried into the review and sent back with
 * their self-reported provenance, rather than being silently deleted.
 */

import { it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'

vi.mock('../services/api', () => ({
  resumeAPI: {
    getLatestResume: vi.fn(),
    uploadResume: vi.fn(),
    confirmSkills: vi.fn(),
  },
  profileAPI: {
    getMeProfile: vi.fn(),
  },
  formatApiError: (_err, fallback) => fallback,
}))

import ResumePage from './ResumePage'
import { resumeAPI, profileAPI } from '../services/api'

const LATEST_RESUME = {
  id: 7,
  filename: 'qa-resume.txt',
  file_size_bytes: 2048,
  created_at: '2026-10-26T00:00:00Z',
  status: 'parsed',
  raw_text: 'Python and FastAPI experience.',
  extracted_skills: [
    {
      name: 'Python',
      normalized_name: 'Python',
      category: 'Programming language',
      confidence: 0.95,
      evidence: 'Built a REST API with Python and FastAPI.',
      proficiency: 'intermediate',
    },
  ],
}

beforeEach(() => {
  vi.clearAllMocks()
  profileAPI.getMeProfile.mockResolvedValue({
    data: {
      student_profile: {
        skills: [{ name: 'SQL', level: 'beginner', source: 'self' }],
      },
    },
  })
  resumeAPI.getLatestResume.mockResolvedValue({ data: LATEST_RESUME })
  resumeAPI.confirmSkills.mockResolvedValue({
    data: { total_confirmed_skills: 2, synced_to_profile: true, skills: [] },
  })
})

it('keeps an existing profile skill in the review and preserves its source', async () => {
  const user = userEvent.setup()
  render(<ResumePage />)

  await screen.findByRole('heading', { name: /Review skills before syncing \(2\)/i })
  expect(screen.getByText('SQL')).toBeInTheDocument()
  expect(screen.getByText('Kept from profile')).toBeInTheDocument()
  expect(screen.getByText('95% confidence')).toBeInTheDocument()

  await user.click(screen.getByRole('button', { name: /Confirm & sync to profile/i }))

  await waitFor(() => expect(resumeAPI.confirmSkills).toHaveBeenCalledTimes(1))
  expect(resumeAPI.confirmSkills).toHaveBeenCalledWith({
    resume_id: 7,
    skills: [
      expect.objectContaining({ name: 'Python', level: 'intermediate', source: 'resume' }),
      expect.objectContaining({ name: 'SQL', level: 'beginner', source: 'self' }),
    ],
  })
  expect(await screen.findByText(/2 skills synced to your profile/i)).toBeInTheDocument()
})

it('disables syncing when existing profile skills could not be loaded', async () => {
  profileAPI.getMeProfile.mockRejectedValue(new Error('profile endpoint unavailable'))
  render(<ResumePage />)

  expect(
    await screen.findByText(/couldn't load your existing profile skills/i)
  ).toBeInTheDocument()
  expect(screen.getByRole('button', { name: /Confirm & sync to profile/i })).toBeDisabled()
  expect(resumeAPI.confirmSkills).not.toHaveBeenCalled()
})
