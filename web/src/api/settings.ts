/**
 * api/settings.ts
 *
 * Runtime application settings (docs/05 §4.7). P1 exposes the global roleplay prompt; the
 * response carries both the effective value and the system default (for a reset affordance).
 */

import { http } from './http'

export interface RoleplayPrompt {
  roleplay_prompt: string
  default: string
}

export const settingsApi = {
  getRoleplayPrompt: () => http.get<RoleplayPrompt>('/settings/roleplay-prompt'),
  setRoleplayPrompt: (value: string) =>
    http.put<RoleplayPrompt>('/settings/roleplay-prompt', { value }),
  resetRoleplayPrompt: () => http.delete<RoleplayPrompt>('/settings/roleplay-prompt'),
}
