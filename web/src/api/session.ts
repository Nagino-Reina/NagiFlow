/**
 * api/session.ts
 *
 * Holds the opaque session token (docs/05 §2). Stored in localStorage for the SPA;
 * sent as `Authorization: Bearer <token>`. The backend only stores its hash.
 */

const STORAGE_KEY = 'nf.token'

let token: string | null = localStorage.getItem(STORAGE_KEY)

export function getToken (): string | null {
  return token
}

export function setToken (value: string | null): void {
  token = value
  if (value) {
    localStorage.setItem(STORAGE_KEY, value)
  } else {
    localStorage.removeItem(STORAGE_KEY)
  }
}
