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
// Handles 401 (session expired) globally.
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('cg_token')
      localStorage.removeItem('cg_user')
      window.location.href = '/login'
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

// ─── Health ──────────────────────────────────────────────────────────────────
export const healthAPI = {
  check: () => api.get('/health'),
}

export default api
