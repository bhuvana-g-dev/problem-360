import { apiFetch } from './api.js'

const post = (path) => apiFetch(path, { method: 'POST' })
export const listGroups = (locality) => apiFetch(`/api/groups${locality ? `?locality=${encodeURIComponent(locality)}` : ''}`)
export const joinGroup = (id) => post(`/api/groups/${id}/join`)
export const leaveGroup = (id) => post(`/api/groups/${id}/leave`)
export const listEvents = (locality) => apiFetch(`/api/events${locality ? `?locality=${encodeURIComponent(locality)}` : ''}`)
export const registerEvent = (id) => post(`/api/events/${id}/register`)
export const unregisterEvent = (id) => post(`/api/events/${id}/unregister`)
export const listUpdates = () => apiFetch('/api/updates')
export const trending = (locality) => apiFetch(`/api/trending${locality ? `?locality=${encodeURIComponent(locality)}` : ''}`)
