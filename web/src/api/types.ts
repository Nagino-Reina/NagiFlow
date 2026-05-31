/**
 * api/types.ts
 *
 * Shared API types — minimal P0 subset mirroring the backend schemas (docs/05 §2).
 * Broader types are generated from OpenAPI later (docs/03 §3.4, docs/05 §7).
 */

export type PrincipalKind = 'guest' | 'user'

/** GET /auth/me (backend `MeResponse`). */
export interface Principal {
  user_id: string
  kind: PrincipalKind
  is_admin: boolean
  username?: string | null
  display_name?: string | null
}

/** POST /auth/guest | /auth/login (backend `SessionResponse`). */
export interface SessionResponse {
  token: string
  user_id: string
  kind: PrincipalKind
  expires_at: string
}

/** POST /auth/register — creates the account; does not start a session. */
export interface RegisterResponse {
  id: string
  username: string
}

/** The API error envelope (docs/05 §3). */
export interface ErrorEnvelope {
  error: {
    code: string
    message: string
    details?: Record<string, unknown>
    correlation_id?: string
  }
}
