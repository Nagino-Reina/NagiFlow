/**
 * api/auth.ts
 *
 * Auth endpoints (docs/05 §2). Session-based: guest auto-issued, user login upgrades
 * capabilities. Tokens are opaque; the server stores only their hash. Registration
 * creates the account but does not start a session (the store logs in afterwards).
 */

import { http } from './http'
import type { Principal, RegisterResponse, SessionResponse } from './types'

export interface LoginBody {
  username: string
  password: string
}

export interface RegisterBody {
  username: string
  password: string
  display_name?: string
}

export const authApi = {
  guest: () => http.post<SessionResponse>('/auth/guest'),
  register: (body: RegisterBody) => http.post<RegisterResponse>('/auth/register', body),
  login: (body: LoginBody) => http.post<SessionResponse>('/auth/login', body),
  logout: () => http.post<{ ok: boolean }>('/auth/logout'),
  logoutAll: () => http.post<{ ok: boolean }>('/auth/logout-all'),
  me: () => http.get<Principal>('/auth/me'),
}
