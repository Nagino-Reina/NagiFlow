/**
 * api/index.ts
 * One barrel export for all API service modules.
 */

import client from './client'

// ── Auth ──────────────────────────────────────────────────────────────────
export const authApi = {
  register: (data)        => client.post('/auth/register', data),
  login:    (data)        => client.post('/auth/login', data),
  refresh:  (token)       => client.post('/auth/refresh', { refresh_token: token }),
  me:       ()            => client.get('/auth/me'),
}

// ── Users ─────────────────────────────────────────────────────────────────
export const usersApi = {
  list:           ()           => client.get('/users'),
  updateMe:       (data)       => client.patch('/users/me', data),
  changePassword: (data)       => client.post('/users/me/password', data),
  deactivate:     (id)         => client.patch(`/users/${id}/deactivate`),
  setRole:        (id, role)   => client.patch(`/users/${id}/role`, null, { params: { role } }),
}

// ── Characters ────────────────────────────────────────────────────────────
export const charactersApi = {
  list:             (params)         => client.get('/characters', { params }),
  get:              (id)             => client.get(`/characters/${id}`),
  create:           (data)           => client.post('/characters', data),
  update:           (id, data)       => client.patch(`/characters/${id}`, data),
  delete:           (id)             => client.delete(`/characters/${id}`),
  uploadAvatar:     (id, file)       => _upload(`/characters/${id}/avatar`, file),
  uploadVoice:      (id, file)       => _upload(`/characters/${id}/voice-sample`, file),
  uploadModel:      (id, file, type) => _upload(`/characters/${id}/model`, file, { model_type: type }),
  listSkills:       (id)             => client.get(`/characters/${id}/skills`),
  assignSkill:      (id, data)       => client.post(`/characters/${id}/skills`, data),
  removeSkill:      (id, skillId)    => client.delete(`/characters/${id}/skills/${skillId}`),
}

// ── Conversations ─────────────────────────────────────────────────────────
export const conversationsApi = {
  list:   (params) => client.get('/conversations', { params }),
  get:    (id)     => client.get(`/conversations/${id}`),
  create: (data)   => client.post('/conversations', data),
  delete: (id)     => client.delete(`/conversations/${id}`),
  chat:   (charId, data) => client.post(`/conversations/characters/${charId}/chat`, data),
  tts:    (charId, text) => client.post(`/conversations/characters/${charId}/tts`, null, { params: { text } }),
}

// ── Memory ────────────────────────────────────────────────────────────────
export const memoryApi = {
  list:    (charId, params) => client.get(`/characters/${charId}/memories`, { params }),
  create:  (charId, data)   => client.post(`/characters/${charId}/memories`, data),
  update:  (charId, id, d)  => client.patch(`/characters/${charId}/memories/${id}`, d),
  delete:  (charId, id)     => client.delete(`/characters/${charId}/memories/${id}`),
  clear:   (charId)         => client.delete(`/characters/${charId}/memories`),
  search:  (charId, data)   => client.post(`/characters/${charId}/memories/search`, data),
}

// ── Knowledge ─────────────────────────────────────────────────────────────
export const knowledgeApi = {
  list:   (params) => client.get('/knowledge', { params }),
  get:    (id)     => client.get(`/knowledge/${id}`),
  create: (data)   => client.post('/knowledge', data),
  upload: (title, file, charId) => {
    const form = new FormData()
    form.append('file', file)
    const params = { title }
    if (charId) params.character_id = charId
    return client.post('/knowledge/upload', form, {
      params,
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },
  delete: (id)   => client.delete(`/knowledge/${id}`),
  search: (data) => client.post('/knowledge/search', data),
}

// ── Skills ────────────────────────────────────────────────────────────────
export const skillsApi = {
  list:   ()   => client.get('/skills'),
  get:    (id) => client.get(`/skills/${id}`),
  toggle: (id) => client.patch(`/skills/${id}/toggle`),
}

// ── Scripts ───────────────────────────────────────────────────────────────
export const scriptsApi = {
  list:            ()                     => client.get('/scripts'),
  create:          (data)                 => client.post('/scripts', data),
  get:             (id)                   => client.get(`/scripts/${id}`),
  update:          (id, data)             => client.patch(`/scripts/${id}`, data),
  delete:          (id)                   => client.delete(`/scripts/${id}`),
  exportZip:       (id)                   => client.get(`/scripts/${id}/export`, { responseType: 'blob' }),
  synthesizeAll:   (id)                   => client.post(`/scripts/${id}/synthesize_all`),
  createScene:     (id, data)             => client.post(`/scripts/${id}/scenes`, data),
  updateScene:     (id, sid, data)        => client.patch(`/scripts/${id}/scenes/${sid}`, data),
  deleteScene:     (id, sid)              => client.delete(`/scripts/${id}/scenes/${sid}`),
  createLine:      (id, sid, data)        => client.post(`/scripts/${id}/scenes/${sid}/lines`, data),
  updateLine:      (id, sid, lid, data)   => client.patch(`/scripts/${id}/scenes/${sid}/lines/${lid}`, data),
  deleteLine:      (id, sid, lid)         => client.delete(`/scripts/${id}/scenes/${sid}/lines/${lid}`),
  synthesizeLine:  (id, sid, lid)         => client.post(`/scripts/${id}/scenes/${sid}/lines/${lid}/synthesize`),
}

// ── Training ─────────────────────────────────────────────────────────────
export const trainingApi = {
  listDatasets:    ()              => client.get('/training/datasets'),
  createDataset:   (data)          => client.post('/training/datasets', data),
  getDataset:      (id)            => client.get(`/training/datasets/${id}`),
  updateDataset:   (id, data)      => client.patch(`/training/datasets/${id}`, data),
  deleteDataset:   (id)            => client.delete(`/training/datasets/${id}`),
  exportDataset:   (id)            => client.get(`/training/datasets/${id}/export`, { responseType: 'blob' }),
  addItem:         (id, form)      => client.post(`/training/datasets/${id}/items`, form, { headers: { 'Content-Type': 'multipart/form-data' } }),
  generateItem:    (id, form)      => client.post(`/training/datasets/${id}/items/generate`, form, { headers: { 'Content-Type': 'multipart/form-data' } }),
  updateItem:      (id, iid, data) => client.patch(`/training/datasets/${id}/items/${iid}`, data),
  deleteItem:      (id, iid)       => client.delete(`/training/datasets/${id}/items/${iid}`),
}

// ── Providers ─────────────────────────────────────────────────────────────
export const providersApi = {
  list:   ()           => client.get('/providers'),
  health: (type, name) => client.get(`/providers/${type}/health`, { params: name ? { name } : {} }),
}

// ── Health ────────────────────────────────────────────────────────────────
export const healthApi = {
  ping:   () => client.get('/health'),
  system: () => client.get('/health/system'),
}

// ── Helpers ───────────────────────────────────────────────────────────────
function _upload(url, file, extraParams = {}) {
  const form = new FormData()
  form.append('file', file)
  return client.post(url, form, {
    params: extraParams,
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}