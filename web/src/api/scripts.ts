/**
 * api/scripts.ts
 *
 * Script authoring endpoints (docs/05 §4.2, docs/07): script CRUD + duplicate + validate,
 * and per-line create / update / delete / reorder.
 */

import type {
  Script,
  ScriptCreate,
  ScriptLine,
  ScriptLineInput,
  ScriptUpdate,
  ValidationIssue,
} from './types'
import { http } from './http'
import { getToken } from './session'

const BASE = '/api/v1'

export const scriptsApi = {
  list: () => http.get<Script[]>('/scripts'),
  get: (id: string) => http.get<Script>(`/scripts/${id}`),
  create: (body: ScriptCreate) => http.post<Script>('/scripts', body),
  update: (id: string, body: ScriptUpdate) => http.patch<Script>(`/scripts/${id}`, body),
  archive: (id: string) => http.delete<void>(`/scripts/${id}`),
  duplicate: (id: string) => http.post<Script>(`/scripts/${id}:duplicate`),
  validate: (id: string) => http.get<{ issues: ValidationIssue[] }>(`/scripts/${id}:validate`),

  lines: (id: string) => http.get<ScriptLine[]>(`/scripts/${id}/lines`),
  addLine: (id: string, body: ScriptLineInput) =>
    http.post<ScriptLine>(`/scripts/${id}/lines`, body),
  updateLine: (id: string, lineId: string, body: ScriptLineInput) =>
    http.patch<ScriptLine>(`/scripts/${id}/lines/${lineId}`, body),
  deleteLine: (id: string, lineId: string) =>
    http.delete<void>(`/scripts/${id}/lines/${lineId}`),
  reorder: (id: string, lineIds: string[]) =>
    http.post<ScriptLine[]>(`/scripts/${id}/lines:reorder`, { line_ids: lineIds }),

  /** Synthesize one line with its speaker's voice; returns a playable object URL. */
  async previewLine (id: string, lineId: string): Promise<string> {
    const token = getToken()
    const res = await fetch(`${BASE}/scripts/${id}/lines/${lineId}:preview`, {
      method: 'POST',
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    })
    if (!res.ok) {
      throw new Error(`line preview failed (${res.status})`)
    }
    return URL.createObjectURL(await res.blob())
  },
}
