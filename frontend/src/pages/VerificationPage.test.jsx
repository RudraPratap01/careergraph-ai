/**
 * VerificationPage tests — Phase 6 UI.
 *
 * All API calls and the auth role are mocked. These tests pin the two trust
 * levels the page must never blur: GitHub data is real evidence-backed data that
 * the student confirms, while a LinkedIn link is always labelled unverified.
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
  verificationAPI: {
    getStatus: vi.fn(),
    verifyGithub: vi.fn(),
    getGithub: vi.fn(),
    disconnectGithub: vi.fn(),
    confirmSkills: vi.fn(),
    saveLinkedin: vi.fn(),
    getLinkedin: vi.fn(),
  },
  profileAPI: {
    getMeProfile: vi.fn(),
  },
  formatApiError: (_e, fallback) => fallback,
}))

import VerificationPage from './VerificationPage'
import { verificationAPI, profileAPI } from '../services/api'

function githubPayload(overrides = {}) {
  return {
    account: {
      username: 'octocat',
      name: 'The Octocat',
      avatar_url: null,
      profile_url: 'https://github.com/octocat',
      bio: 'GitHub mascot',
      public_repos: 8,
      followers: 120,
      following: 5,
      account_created_at: '2011-01-25T18:44:36Z',
      account_age_days: 5000,
    },
    languages: [{ name: 'Python', count: 2 }],
    skills: [
      {
        name: 'Python',
        category: 'Languages',
        confidence: 0.8,
        repo_count: 2,
        repos: ['api', 'ml'],
        stars: 16,
        sources: ['language'],
        proficiency: 'advanced',
        evidence:
          'Python appears as a primary language in 2 non-forked repositories (api, ml); 16 stars across those repositories.',
      },
      {
        name: 'Docker',
        category: 'Cloud & DevOps',
        confidence: 0.6,
        repo_count: 1,
        repos: ['api'],
        stars: 0,
        sources: ['topic'],
        proficiency: 'beginner',
        evidence:
          'Docker appears as a repository topic in 1 non-forked repository (api); 0 stars across those repositories.',
      },
    ],
    repos_analyzed: 5,
    repos_truncated: false,
    forks_excluded: 1,
    total_stars: 24,
    target_role: 'Backend Developer',
    relevant_to_target: ['Python'],
    explanation:
      'Fetched 5 public repositories from github.com/octocat (forks excluded) and matched 2 skills from their primary languages and topics.',
    disclaimer: 'Detected skills are inferred from repository metadata.',
    verified_at: '2026-10-21T00:00:00Z',
    source: 'github',
    ...overrides,
  }
}

const LINKEDIN = {
  linkedin_url: 'https://www.linkedin.com/in/jane-doe',
  verified: false,
  note:
    "LinkedIn does not provide a public API for reading a member's profile, so this link is self-declared and not verified.",
}

function renderPage() {
  return render(
    <MemoryRouter>
      <VerificationPage />
    </MemoryRouter>
  )
}

beforeEach(() => {
  vi.clearAllMocks()
  auth.role = 'student'
  verificationAPI.getStatus.mockResolvedValue({ data: { github: null, linkedin: null } })
  profileAPI.getMeProfile.mockResolvedValue({ data: { student_profile: { skills: [] } } })
})

describe('VerificationPage', () => {
  it('shows both trust levels with nothing linked yet', async () => {
    renderPage()

    const github = await screen.findByTestId('github-panel')
    const linkedin = screen.getByTestId('linkedin-panel')

    expect(within(github).getByText('Not linked')).toBeInTheDocument()
    expect(within(github).getByRole('button', { name: 'Verify GitHub' })).toBeInTheDocument()
    expect(within(linkedin).getByText('Not added')).toBeInTheDocument()
    expect(within(linkedin).getByText(/self-declared/)).toBeInTheDocument()
  })

  it('verifies a GitHub account and shows evidence-backed skills', async () => {
    const user = userEvent.setup()
    verificationAPI.verifyGithub.mockResolvedValue({ data: githubPayload() })

    renderPage()
    await screen.findByTestId('github-panel')
    await user.type(screen.getByLabelText('GitHub username'), 'octocat')
    await user.click(screen.getByRole('button', { name: 'Verify GitHub' }))

    expect(verificationAPI.verifyGithub).toHaveBeenCalledWith('octocat')

    const account = await screen.findByTestId('github-account')
    expect(within(account).getByText('The Octocat')).toBeInTheDocument()
    expect(within(account).getByText('@octocat ↗')).toBeInTheDocument()
    expect(within(screen.getByTestId('github-panel')).getByText('✓ Account verified')).toBeInTheDocument()
    expect(within(account).getByText(/Fetched 5 public repositories from github.com\/octocat/)).toBeInTheDocument()
    expect(within(account).getByText(/Also required for your target role/)).toBeInTheDocument()

    const python = screen.getByTestId('github-skill-Python')
    expect(within(python).getByText('80% confidence')).toBeInTheDocument()
    expect(within(python).getByText(/primary language in 2 non-forked repositories/)).toBeInTheDocument()
  })

  it('confirms only the skills the student selected', async () => {
    const user = userEvent.setup()
    verificationAPI.verifyGithub.mockResolvedValue({ data: githubPayload() })
    verificationAPI.confirmSkills.mockResolvedValue({
      data: {
        added: ['Docker'],
        upgraded: [],
        already_present: [],
        skills: [],
        message: 'GitHub skills updated: 1 added.',
      },
    })

    renderPage()
    await screen.findByTestId('github-panel')
    await user.type(screen.getByLabelText('GitHub username'), 'octocat')
    await user.click(screen.getByRole('button', { name: 'Verify GitHub' }))

    const docker = await screen.findByTestId('github-skill-Docker')
    await user.click(within(docker).getByRole('checkbox'))
    await user.click(screen.getByRole('button', { name: 'Add 1 skill from GitHub' }))

    expect(verificationAPI.confirmSkills).toHaveBeenCalledWith(['Docker'])
    expect(await screen.findByText('GitHub skills updated: 1 added.')).toBeInTheDocument()
    // The profile is reloaded so the "On your profile" markers stay accurate.
    expect(profileAPI.getMeProfile).toHaveBeenCalledTimes(2)
  })

  it('marks skills that are already on the profile', async () => {
    verificationAPI.getStatus.mockResolvedValue({
      data: { github: githubPayload(), linkedin: null },
    })
    profileAPI.getMeProfile.mockResolvedValue({
      data: {
        student_profile: {
          skills: [{ name: 'Python', level: 'advanced', source: 'github' }],
        },
      },
    })

    renderPage()

    const python = await screen.findByTestId('github-skill-Python')
    expect(within(python).getByText('On your profile')).toBeInTheDocument()
    expect(within(python).getByRole('checkbox')).toBeDisabled()
    expect(within(python).getByRole('checkbox')).toBeChecked()
  })

  it('allows a self-reported skill to be upgraded to GitHub evidence', async () => {
    const user = userEvent.setup()
    verificationAPI.getStatus.mockResolvedValue({
      data: { github: githubPayload(), linkedin: null },
    })
    profileAPI.getMeProfile.mockResolvedValue({
      data: {
        student_profile: {
          skills: [{ name: 'Python', level: 'advanced', source: 'self' }],
        },
      },
    })
    verificationAPI.confirmSkills.mockResolvedValue({
      data: {
        added: [],
        upgraded: ['Python'],
        already_present: [],
        skills: [],
        message: 'GitHub skills updated: 1 upgraded to GitHub evidence.',
      },
    })

    renderPage()

    const python = await screen.findByTestId('github-skill-Python')
    expect(within(python).getByText('On profile as self — can upgrade')).toBeInTheDocument()

    await user.click(within(python).getByRole('checkbox'))
    await user.click(screen.getByRole('button', { name: 'Add 1 skill from GitHub' }))

    expect(verificationAPI.confirmSkills).toHaveBeenCalledWith(['Python'])
  })

  it('labels the LinkedIn link as unverified after saving it', async () => {
    const user = userEvent.setup()
    verificationAPI.saveLinkedin.mockResolvedValue({ data: LINKEDIN })

    renderPage()
    await screen.findByTestId('github-panel')
    await user.type(
      screen.getByLabelText('LinkedIn profile URL'),
      'https://www.linkedin.com/in/jane-doe'
    )
    await user.click(screen.getByRole('button', { name: 'Save link' }))

    expect(verificationAPI.saveLinkedin).toHaveBeenCalledWith(
      'https://www.linkedin.com/in/jane-doe'
    )

    expect(await screen.findByTestId('linkedin-unverified')).toHaveTextContent(
      'Unverified — self-declared'
    )
    const status = screen.getByTestId('linkedin-status')
    expect(within(status).getByText(/linkedin.com\/in\/jane-doe/)).toBeInTheDocument()
    expect(within(status).getByText(/does not provide a public API/)).toBeInTheDocument()
  })

  it('unlinks GitHub and explains that confirmed skills are kept', async () => {
    const user = userEvent.setup()
    verificationAPI.getStatus.mockResolvedValue({
      data: { github: githubPayload(), linkedin: null },
    })
    verificationAPI.disconnectGithub.mockResolvedValue({
      data: {
        disconnected: true,
        message:
          'GitHub account unlinked. Skills you confirmed from GitHub remain on your profile, but are now marked as self-reported.',
      },
    })

    renderPage()

    const github = await screen.findByTestId('github-panel')
    await user.click(within(github).getByRole('button', { name: 'Unlink GitHub' }))

    expect(verificationAPI.disconnectGithub).toHaveBeenCalled()
    expect(await screen.findByText(/GitHub account unlinked/)).toBeInTheDocument()
    expect(within(github).getByText('Not linked')).toBeInTheDocument()
    expect(within(github).queryByTestId('github-account')).not.toBeInTheDocument()
  })

  it('shows the API error when verification fails', async () => {
    const user = userEvent.setup()
    verificationAPI.verifyGithub.mockRejectedValue(new Error('boom'))

    renderPage()
    await screen.findByTestId('github-panel')
    await user.type(screen.getByLabelText('GitHub username'), 'nobody')
    await user.click(screen.getByRole('button', { name: 'Verify GitHub' }))

    expect(
      await screen.findByText('Could not verify that GitHub account.')
    ).toBeInTheDocument()
  })

  it('tells alumni that verification is part of the student workflow', async () => {
    auth.role = 'alumni'
    renderPage()

    expect(await screen.findByTestId('verification-student-only')).toBeInTheDocument()
    expect(verificationAPI.getStatus).not.toHaveBeenCalled()
  })
})
