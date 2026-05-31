/**
 * api/http.ts
 *
 * Typed REST client (docs/03 §3.4, docs/05). Attaches the session token, sends/receives
 * JSON, and normalizes the error envelope (docs/05 §3) into a thrown `ApiError` carrying
 * the stable `code` + `correlation_id`. In dev, `/api` is proxied to the backend (vite).
 */

import { getToken } from './session'
import type { ErrorEnvelope } from './types'

const BASE = '/api/v1'

/** Stable, typed error carrying the envelope `code` so UI can map to `error.<code>`. */
export class ApiError extends Error {
  constructor (
    public readonly code: string,
    message: string,
    public readonly status: number,
    public readonly details?: Record<string, unknown>,
    public readonly correlationId?: string,
  ) {
    super(message)
    this.name = 'ApiError'
  }
}

interface RequestOptions {
  body?: unknown
  headers?: Record<string, string>
  signal?: AbortSignal
}

async function request<T> (method: string, path: string, opts: RequestOptions = {}): Promise<T> {
  const headers: Record<string, string> = { Accept: 'application/json', ...opts.headers }
  const token = getToken()
  if (token) headers.Authorization = `Bearer ${token}`

  let body: BodyInit | undefined
  if (opts.body !== undefined) {
    headers['Content-Type'] = 'application/json'
    body = JSON.stringify(opts.body)
  }

  let res: Response
  try {
    res = await fetch(`${BASE}${path}`, { method, headers, body, signal: opts.signal })
  } catch (cause) {
    throw new ApiError('network.error', 'Network request failed.', 0, undefined, undefined)
  }

  if (res.status === 204) return undefined as T

  const payload = await res.json().catch(() => null)

  if (!res.ok) {
    const env = payload as ErrorEnvelope | null
    const err = env?.error
    throw new ApiError(
      err?.code ?? 'internal.error',
      err?.message ?? res.statusText,
      res.status,
      err?.details,
      err?.correlation_id,
    )
  }

  return payload as T
}

export const http = {
  get: <T>(path: string, opts?: RequestOptions) => request<T>('GET', path, opts),
  post: <T>(path: string, body?: unknown, opts?: RequestOptions) =>
    request<T>('POST', path, { ...opts, body }),
  patch: <T>(path: string, body?: unknown, opts?: RequestOptions) =>
    request<T>('PATCH', path, { ...opts, body }),
  delete: <T>(path: string, opts?: RequestOptions) => request<T>('DELETE', path, opts),
}
