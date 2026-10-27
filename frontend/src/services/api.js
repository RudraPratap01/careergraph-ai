/**
 * API service layer — all HTTP calls go through this module.
 *
 * Why a service layer?
 *   1. The base URL is configured in one place.
 *   2. The JWT token is automatically attached to every request.
 *   3. If the API structure changes, only this file needs updating.
 *   4. Errors are handled consistently.
 */

import axios from 'axios'

/**
 * Safely normalizes FastAPI error responses (string, dictionary, or 422 array of {loc, msg})
 * into a user-friendly string so React never crashes on {type, loc, msg, input, ctx}.
 */
export function formatApiError(err, fallback = 'An unexpected error occurred.') {
  const detail = err.response?.data?.detail
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail)) {
    return detail
      .map((d) => {
        const field = Array.isArray(d.loc) ? d.loc[d.loc.length - 1] : ''
        const fieldPrefix = field && field !== 'body' ? `${field}: ` : ''
        return `${fieldPrefix}${d.msg || d.message || JSON.stringify(d)}`
      })
      .join(', ')
  }
  if (detail && typeof detail === 'object') {
    return detail.msg || detail.message || JSON.stringify(detail)
  }
  return err.message || fallback
}

const api = axios.create({
  baseURL: '/api',  // Vite proxy rewrites /api → http://localhost:8000
  headers: { 'Content-Type': 'application/json' },
})


// ─── Request interceptor ─────────────────────────────────────────────────────
// Automatically attaches the JWT token to every outgoing request.
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('cg_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// ─── Response interceptor ────────────────────────────────────────────────────
// Handles 401 (session expired) globally for protected requests.
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      const url = error.config?.url || ''
      // Do not clear credentials or force reload if the user is attempting to log in or register
      if (!url.includes('/auth/login') && !url.includes('/auth/register')) {
        localStorage.removeItem('cg_token')
        localStorage.removeItem('cg_user')
        if (typeof window !== 'undefined' && window.location.pathname !== '/login') {
          window.location.href = '/login'
        }
      }
    }
    return Promise.reject(error)
  }
)

// ─── Auth endpoints (Phase 1) ─────────────────────────────────────────────────
export const authAPI = {
  register: (data) => api.post('/auth/register', data),
  login: (data) => api.post('/auth/login', data),
  me: () => api.get('/auth/me'),
}

// ─── Profile endpoints (Phase 2) ──────────────────────────────────────────────
export const profileAPI = {
  getMeProfile: () => api.get('/profile/me'),
  updateStudentProfile: (data) => api.put('/profile/student', data),
  updateAlumniProfile: (data) => api.put('/profile/alumni', data),
  getPublicProfile: (userId) => api.get(`/profile/${userId}`),
  getAlumniMentors: (expertise) =>
    api.get('/alumni', { params: expertise ? { expertise } : {} }),
}

// ─── Resume Intelligence endpoints (Phase 3) ─────────────────────────────────
export const resumeAPI = {
  uploadResume: (formData) =>
    api.post('/resume/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }),
  getLatestResume: () => api.get('/resume/latest'),
  confirmSkills: (data) => api.post('/resume/confirm-skills', data),
}

// ─── Career Intelligence endpoints (Phase 4) ─────────────────────────────────
export const careerAPI = {
  listOccupations: () => api.get('/career/occupations'),
  getOccupation: (key) => api.get(`/career/occupations/${encodeURIComponent(key)}`),
  getGapAnalysis: (occupation) =>
    api.get('/career/gap-analysis', { params: occupation ? { occupation } : {} }),
}

// ─── Skill Graph endpoints (Phase 5A) ────────────────────────────────────────
export const graphAPI = {
  getStats: () => api.get('/graph/stats'),
  getDependencies: (skill, maxDepth) =>
    api.get(`/graph/skills/${encodeURIComponent(skill)}`, {
      params: maxDepth ? { max_depth: maxDepth } : {},
    }),
}

// ─── Learning Roadmap endpoints (Phase 5B) ───────────────────────────────────
export const roadmapAPI = {
  generate: (occupation, regenerate = true) =>
    api.post('/roadmap/generate', { occupation: occupation || null, regenerate }),
  getCurrent: () => api.get('/roadmap'),
  getById: (roadmapId) => api.get(`/roadmap/${roadmapId}`),
  getExplanations: (roadmapId) => api.get(`/roadmap/${roadmapId}/explanations`),
  updateStep: (roadmapId, skill, state) =>
    api.post(`/roadmap/${roadmapId}/steps`, { skill, state }),
  refresh: (occupation) =>
    api.post('/roadmap/refresh', null, { params: occupation ? { occupation } : {} }),
}

// ─── Skill Assessments (Phase 8) ─────────────────────────────────────────────
export const assessmentAPI = {
  list: () => api.get('/assessments'),
  get: (key) => api.get(`/assessments/${encodeURIComponent(key)}`),
  start: (key) => api.post(`/assessments/${encodeURIComponent(key)}/start`),
  submit: (attemptId, answers) =>
    api.post(`/assessments/attempts/${attemptId}/submit`, { answers }),
  confirmSkills: (attemptId, skills) =>
    api.post(`/assessments/attempts/${attemptId}/confirm-skills`, { skills }),
  history: () => api.get('/assessments/attempts'),
}

// ─── Alumni Matching & Mentorship (Phase 8) ──────────────────────────────────
export const mentorshipAPI = {
  getMatches: () => api.get('/mentorship/matches'),
  requestMentorship: (alumniUserId, message) =>
    api.post('/mentorship/requests', { alumni_user_id: alumniUserId, message: message || null }),
  listRequests: () => api.get('/mentorship/requests'),
  accept: (requestId) => api.post(`/mentorship/requests/${requestId}/accept`),
  decline: (requestId) => api.post(`/mentorship/requests/${requestId}/decline`),
  cancel: (requestId) => api.post(`/mentorship/requests/${requestId}/cancel`),
}

// ─── GitHub Verification & LinkedIn link (Phase 6) ───────────────────────────
export const verificationAPI = {
  getStatus: () => api.get('/verification/status'),
  verifyGithub: (username) => api.post('/verification/github', { username }),
  getGithub: () => api.get('/verification/github'),
  disconnectGithub: () => api.delete('/verification/github'),
  confirmSkills: (skills) => api.post('/verification/github/confirm-skills', { skills }),
  saveLinkedin: (url) => api.post('/verification/linkedin', { url }),
  getLinkedin: () => api.get('/verification/linkedin'),
}

// ─── Grounded career intelligence (Phase 7) ──────────────────────────────────
export const intelligenceAPI = {
  status: () => api.get('/intelligence/status'),
  ask: (question, occupation) =>
    api.post('/intelligence/ask', { question, occupation: occupation || null }),
}

// ─── Health ──────────────────────────────────────────────────────────────────
export const healthAPI = {
  check: () => api.get('/health'),
}

export default api
