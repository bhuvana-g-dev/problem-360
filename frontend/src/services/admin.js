import { apiFetch } from './api.js'

export const reviewQueue = (state = 'pending') => apiFetch(`/api/admin/reviews?state=${state}`)
export const reviewStats = () => apiFetch('/api/admin/reviews/stats')
export const decideReview = (id, decision, note = '') => apiFetch(`/api/admin/reviews/${id}`, { method: 'POST', body: { decision, note } })
export const setReportStatus = (id, status, note = '') => apiFetch(`/api/admin/reports/${id}/status`, { method: 'PATCH', body: { status, note } })
export const adminOrganizations = (status) => apiFetch(`/api/admin/organizations${status ? `?status=${status}` : ''}`)
export const setVerification = (id, status, note = '') => apiFetch(`/api/admin/organizations/${id}/verification`, { method: 'PATCH', body: { status, note } })
